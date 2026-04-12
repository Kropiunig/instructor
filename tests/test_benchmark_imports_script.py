from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_benchmark_imports_script_emits_json() -> None:
    script = Path(__file__).resolve().parents[1] / "scripts" / "benchmark_imports.py"
    result = subprocess.run(
        [sys.executable, str(script), "--repeat", "1", "--json", "sys", "instructor"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert [row["module"] for row in payload] == ["instructor", "sys"]
    assert all("rss_mb_avg" in row for row in payload)
