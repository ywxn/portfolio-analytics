from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

DEFAULT_DATABASE_URL = os.getenv("PORTFOLIO_DB_URL", "")
DEFAULT_EXCEL_PATH = os.getenv(
    "PORTFOLIO_EXCEL_PATH",
    str(Path(__file__).resolve().parents[1] / "portfolio.xlsx"),
)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")
DEFAULT_TEMPERATURE = float(os.getenv("PORTFOLIO_TEMPERATURE", "0.1"))
DEFAULT_MAX_TOKENS = int(os.getenv("PORTFOLIO_MAX_TOKENS", "2048"))
DEFAULT_MAX_RETRIES = int(os.getenv("PORTFOLIO_MAX_RETRIES", "3"))
PROJECT_ROOT = Path(__file__).resolve().parents[1]
METADATA_DIR = PROJECT_ROOT / "metadata"
LEGACY_METADATA_PATH = PROJECT_ROOT / "metadata.yaml"
METADATA_PATH = METADATA_DIR / "portfolio.yaml"


def load_metadata(path: str | Path | None = None) -> dict[str, Any]:
    candidate = Path(path) if path else METADATA_PATH
    if not candidate.exists() and LEGACY_METADATA_PATH.exists():
        candidate = LEGACY_METADATA_PATH
    if not candidate.exists():
        return {}

    with candidate.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}
    return payload if isinstance(payload, dict) else {}


def get_anthropic_api_key() -> str | None:
    return ANTHROPIC_API_KEY or os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENAI_API_KEY")


def get_database_url() -> str:
    return os.getenv("PORTFOLIO_DB_URL", DEFAULT_DATABASE_URL)


def get_excel_path() -> str:
    return os.getenv("PORTFOLIO_EXCEL_PATH", DEFAULT_EXCEL_PATH)


def validate_runtime_config() -> dict[str, Any]:
    return {
        "database_url": get_database_url(),
        "excel_path": get_excel_path(),
        "anthropic_api_key_configured": bool(get_anthropic_api_key()),
        "anthropic_model": ANTHROPIC_MODEL,
        "temperature": DEFAULT_TEMPERATURE,
        "max_tokens": DEFAULT_MAX_TOKENS,
        "max_retries": DEFAULT_MAX_RETRIES,
    }


__all__ = [
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_MODEL",
    "DEFAULT_DATABASE_URL",
    "DEFAULT_EXCEL_PATH",
    "DEFAULT_TEMPERATURE",
    "DEFAULT_MAX_TOKENS",
    "DEFAULT_MAX_RETRIES",
    "METADATA_PATH",
    "PROJECT_ROOT",
    "get_anthropic_api_key",
    "get_database_url",
    "get_excel_path",
    "load_metadata",
    "validate_runtime_config",
]
