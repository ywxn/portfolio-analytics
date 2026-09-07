from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

DEFAULT_DATABASE_URL = os.getenv("PORTFOLIO_DB_URL", "")
DEFAULT_EXCEL_PATH = os.getenv(
    "PORTFOLIO_EXCEL_PATH", str(Path(__file__).resolve().parent / "portfolio.xlsx")
)  # TODO: REMOVE THIS IS TEMPORARY FOR TESTING PHASE
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
# TODO: Add configurable temperature/token limits, database options, and a
# checked-in .env.example without placing credentials in source.
PROJECT_ROOT = Path(__file__).resolve().parent
METADATA_PATH = PROJECT_ROOT / "metadata.yaml"


def load_metadata(path: str | Path | None = None) -> dict[str, Any]:
    metadata_path = Path(path) if path else METADATA_PATH
    if not metadata_path.exists():
        return {}

    with metadata_path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}
    return payload if isinstance(payload, dict) else {}


def get_openai_api_key() -> str | None:
    return OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")


def get_database_url() -> str:
    return os.getenv("PORTFOLIO_DB_URL", DEFAULT_DATABASE_URL)


def get_excel_path() -> str:
    return os.getenv("PORTFOLIO_EXCEL_PATH", DEFAULT_EXCEL_PATH)


def validate_runtime_config() -> dict[str, Any]:
    return {
        "database_url": get_database_url(),
        "excel_path": get_excel_path(),
        "openai_api_key_configured": bool(get_openai_api_key()),
        "openai_model": OPENAI_MODEL,
    }
