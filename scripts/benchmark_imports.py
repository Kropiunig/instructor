"""Benchmark Python import cost in fresh subprocesses.

This is intended for import-regression checks like issue #2205, where the
important signal is the startup cost of `import instructor` relative to other
modules in the same environment.
"""

from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import sys
from dataclasses import dataclass


DEFAULT_MODULES = ["sys", "openai", "google.genai", "instructor"]

CHILD_SCRIPT = """
import importlib
import json
import resource
import sys
import time

module_name = sys.argv[1]
start = time.perf_counter()
importlib.import_module(module_name)
elapsed = time.perf_counter() - start
rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
rss_bytes = rss if sys.platform == "darwin" else rss * 1024
print(
    json.dumps(
        {
            "module": module_name,
            "seconds": elapsed,
            "module_count": len(sys.modules),
            "rss_bytes": rss_bytes,
        }
    )
)
""".strip()


@dataclass(frozen=True)
class Sample:
    seconds: float
    module_count: int
    rss_bytes: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "modules",
        nargs="*",
        default=DEFAULT_MODULES,
        help="Modules to benchmark. Defaults to the modules discussed in issue #2205.",
    )
    parser.add_argument(
        "--repeat",
        type=int,
        default=3,
        help="How many fresh subprocess runs to execute per module.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of a text table.",
    )
    return parser.parse_args()


def run_sample(module: str) -> Sample:
    result = subprocess.run(
        [sys.executable, "-c", CHILD_SCRIPT, module],
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(result.stdout)
    return Sample(
        seconds=float(payload["seconds"]),
        module_count=int(payload["module_count"]),
        rss_bytes=int(payload["rss_bytes"]),
    )


def mean(values: list[float]) -> float:
    return statistics.fmean(values)


def summarize_module(module: str, repeat: int) -> dict[str, float | int | str]:
    samples = [run_sample(module) for _ in range(repeat)]
    seconds = [sample.seconds for sample in samples]
    modules = [sample.module_count for sample in samples]
    rss_bytes = [sample.rss_bytes for sample in samples]
    return {
        "module": module,
        "runs": repeat,
        "seconds_avg": mean(seconds),
        "seconds_min": min(seconds),
        "seconds_max": max(seconds),
        "module_count_avg": round(mean(modules)),
        "module_count_min": min(modules),
        "module_count_max": max(modules),
        "rss_mb_avg": mean(rss_bytes) / (1024 * 1024),
        "rss_mb_min": min(rss_bytes) / (1024 * 1024),
        "rss_mb_max": max(rss_bytes) / (1024 * 1024),
    }


def print_table(rows: list[dict[str, float | int | str]]) -> None:
    headers = [
        "module",
        "runs",
        "seconds_avg",
        "module_count_avg",
        "rss_mb_avg",
        "seconds_range",
        "module_range",
        "rss_mb_range",
    ]
    display_rows: list[dict[str, str]] = []
    for row in rows:
        display_rows.append(
            {
                "module": str(row["module"]),
                "runs": str(row["runs"]),
                "seconds_avg": f"{row['seconds_avg']:.4f}",
                "module_count_avg": str(row["module_count_avg"]),
                "rss_mb_avg": f"{row['rss_mb_avg']:.2f}",
                "seconds_range": (f"{row['seconds_min']:.4f}-{row['seconds_max']:.4f}"),
                "module_range": (
                    f"{row['module_count_min']}-{row['module_count_max']}"
                ),
                "rss_mb_range": f"{row['rss_mb_min']:.2f}-{row['rss_mb_max']:.2f}",
            }
        )

    widths = {
        header: max(len(header), *(len(row[header]) for row in display_rows))
        for header in headers
    }
    print("  ".join(header.ljust(widths[header]) for header in headers))
    print("  ".join("-" * widths[header] for header in headers))
    for row in display_rows:
        print("  ".join(row[header].ljust(widths[header]) for header in headers))


def main() -> None:
    args = parse_args()
    rows = [summarize_module(module, args.repeat) for module in args.modules]
    rows.sort(key=lambda row: float(row["rss_mb_avg"]), reverse=True)

    if args.json:
        print(json.dumps(rows, indent=2))
        return

    print_table(rows)


if __name__ == "__main__":
    main()
