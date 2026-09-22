from __future__ import annotations

import os

from portfolio_analytics.llm import (
    ANALYSIS_PLAN_PROMPT,
    SYSTEM_PROMPT,
    generate_analysis_plan,
    generate_sql as package_generate_sql,
)

ANTHROPIC_API_KEY = None
ANTHROPIC_MODEL = None


def generate_sql(question: str, schema: str, metadata: str) -> str:
    if not ANTHROPIC_API_KEY and not os.getenv("ANTHROPIC_API_KEY"):
        raise RuntimeError("ANTHROPIC_API_KEY is required for SQL generation.")
    return package_generate_sql(question, schema, metadata)

__all__ = [
    "generate_sql",
    "generate_analysis_plan",
    "SYSTEM_PROMPT",
    "ANALYSIS_PLAN_PROMPT",
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_MODEL",
]
