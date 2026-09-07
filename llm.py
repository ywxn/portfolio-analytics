from __future__ import annotations

import os

from openai import OpenAI

from config import OPENAI_API_KEY, OPENAI_MODEL


def generate_sql(question: str, schema: str, metadata: str) -> str:
    """Generate a read-only SELECT SQL query from a natural-language question.

    The MVP requires OpenAI. There is deliberately no local SQL fallback because
    generating SQL without the configured model would hide configuration failures.
    """
    # TODO: Add intent extraction, previous-query context, configurable
    # temperature/token limits, and a correction prompt that includes errors.
    cleaned_question = (question or "").strip()
    if not cleaned_question:
        raise ValueError("A question is required to generate SQL.")

    api_key = OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is required for SQL generation.")

    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            temperature=0,
            messages=[
                {
                    "role": "system",
                    "content": "You are a SQL generator for portfolio analytics. Return only one valid PostgreSQL SELECT statement. Never use INSERT, UPDATE, DELETE, CREATE, DROP, ALTER, TRUNCATE, or other data-modifying statements. Use only tables and columns in the supplied schema. Support filters, aggregates, grouping, joins, sorting, LIMIT, and derived metrics when requested.",
                },
                {
                    "role": "user",
                    "content": f"Schema:\n{schema}\n\nMetadata:\n{metadata}\n\nQuestion:\n{cleaned_question}\n\nReturn SQL only.",
                },
            ],
        )
    except Exception as error:
        raise RuntimeError(f"OpenAI SQL generation failed: {error}") from error

    sql = (response.choices[0].message.content or "").strip()
    if sql.startswith("```"):
        sql = sql.strip("`").removeprefix("sql").strip()
    if not sql:
        raise RuntimeError("OpenAI returned an empty SQL query.")
    return sql
