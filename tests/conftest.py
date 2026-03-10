from __future__ import annotations

from dotenv import load_dotenv
import pytest

# Support .env for local development
load_dotenv()


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup("docs")
    group.addoption(
        "--run-doc-examples",
        action="store_true",
        help="Execute doc code examples (requires network access and API keys).",
    )
