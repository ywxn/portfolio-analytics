from __future__ import annotations

import os
import re

from anthropic import Anthropic

from portfolio_analytics.config import ANTHROPIC_API_KEY as _ANTHROPIC_API_KEY
from portfolio_analytics.config import ANTHROPIC_MODEL as _ANTHROPIC_MODEL
from portfolio_analytics.prompts import SQL_GENERATION_PROMPT

ANTHROPIC_API_KEY = _ANTHROPIC_API_KEY
ANTHROPIC_MODEL = _ANTHROPIC_MODEL

SYSTEM_PROMPT = """
You are a SQL generation engine for a portfolio analytics application.

Your task is to convert a user's natural-language analytical question into
exactly one valid PostgreSQL SELECT statement.
""".strip()


def _clean_sql(text: str) -> str:
    sql = text.strip()
    match = re.fullmatch(r"```(?:sql|postgresql)?\s*(.*?)\s*```", sql, flags=re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(1).strip()
    return sql


def generate_sql(question: str, schema: str, metadata: str) -> str:
    cleaned_question = (question or "").strip()
    if not cleaned_question:
        raise ValueError("A question is required to generate SQL.")
    if not schema or not schema.strip():
        raise ValueError("Schema information is required to generate SQL.")

    api_key = ANTHROPIC_API_KEY or os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is required for SQL generation.")

    prompt_text = SQL_GENERATION_PROMPT.format(
        schema=schema.strip(),
        metadata=(metadata or "").strip(),
        question=cleaned_question,
    )

    try:
        client = Anthropic(api_key=api_key)
        response = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt_text}],
        )
    except Exception as error:
        raise RuntimeError(f"Anthropic SQL generation failed: {error}") from error

    parts: list[str] = []
    for block in getattr(response, "content", []) or []:
        if text := getattr(block, "text", None):
            parts.append(text)

    sql = _clean_sql("".join(parts))
    if not sql:
        raise RuntimeError("Anthropic returned an empty SQL query.")
    return sql


__all__ = ["generate_sql", "SYSTEM_PROMPT", "ANTHROPIC_API_KEY", "ANTHROPIC_MODEL"]
