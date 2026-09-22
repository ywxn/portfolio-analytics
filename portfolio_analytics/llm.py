from __future__ import annotations

import os
import re
import json

from anthropic import Anthropic

from .config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL, DEFAULT_MAX_TOKENS
from .prompts import SQL_GENERATION_PROMPT

SYSTEM_PROMPT = """
You are a SQL generation engine for a portfolio analytics application.

Your task is to convert a user's natural-language analytical question into
exactly one valid PostgreSQL SELECT statement.

STRICT REQUIREMENTS:

1. Return ONLY the SQL statement.
2. Do not return Markdown, code fences, explanations, comments, or prose.
3. The query must be read-only.
4. Never generate INSERT, UPDATE, DELETE, MERGE, CREATE, DROP, ALTER,
   TRUNCATE, GRANT, REVOKE, CALL, EXECUTE, or other data-modifying
   statements.
5. Use only tables and columns provided in the supplied schema and metadata.
6. Do not invent tables, columns, relationships, or values.
7. Use PostgreSQL syntax.
8. Use JOINs when the requested information requires data from multiple tables.
9. Use aggregations, GROUP BY, HAVING, ORDER BY, LIMIT, subqueries, CTEs,
   CASE expressions, and window functions when appropriate.
10. Support analytical operations including:
    - aggregations
    - multidimensional breakdowns
    - pivots/cross-tab style analysis
    - ranking
    - top/bottom N
    - percentages
    - ratios
    - differences
    - growth/change
    - subtotals
11. Prefer clear, conventional SQL over unnecessarily complicated queries.
12. Do not assume a column has a particular meaning unless the schema or
    metadata supports that interpretation.
13. If a calculation requires protection against division by zero, use
    NULLIF where appropriate.
14. Preserve meaningful column names with aliases when calculations would
    otherwise produce unclear output.
15. The final result must be a single SELECT statement.

The SQL will be validated separately by the application before execution.
Do not rely on this prompt as the application's security boundary.
""".strip()


def _clean_sql(text: str) -> str:
    """Clean common formatting artifacts from an LLM SQL response."""
    sql = text.strip()
    match = re.fullmatch(
        r"```(?:sql|postgresql)?\s*(.*?)\s*```",
        sql,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if match:
        sql = match.group(1).strip()
    return sql


def _parse_analysis_plan(text: str) -> dict[str, object]:
    """Parse JSON plans even when the model adds a JSON fence or short prose."""
    content = text.strip()
    fenced = re.fullmatch(
        r"```(?:json)?\s*(.*?)\s*```",
        content,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if fenced:
        content = fenced.group(1).strip()

    try:
        plan = json.loads(content)
    except json.JSONDecodeError:
        object_start = content.find("{")
        if object_start < 0:
            raise
        plan, _ = json.JSONDecoder().raw_decode(content[object_start:])

    if not isinstance(plan, dict):
        raise ValueError("Analysis plan must be a JSON object.")
    return plan


def generate_sql(question: str, schema: str, metadata: str) -> str:
    """Generate a read-only PostgreSQL SELECT query from a natural-language question."""
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
            max_tokens=DEFAULT_MAX_TOKENS,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt_text}],
        )
    except Exception as error:
        raise RuntimeError(f"Anthropic SQL generation failed: {error}") from error

    parts: list[str] = []
    for block in getattr(response, "content", []) or []:
        text = getattr(block, "text", None)
        if text:
            parts.append(text)

    sql = _clean_sql("".join(parts))
    if not sql:
        raise RuntimeError("Anthropic returned an empty SQL query.")
    return sql


ANALYSIS_PLAN_PROMPT = """
You are a portfolio analysis planner. Return only valid JSON with these keys:
dimensions (array of column names), metric (column name or null), aggregation
(sum, prod, mean, median, min, max, count, std, var, or size), pivot_index
(array), pivot_columns (array), limit (integer or null), and filters (object).
Use only the available columns. Use pivot_index and pivot_columns for pivot or
cross-tab questions. Use multiple dimensions for multi-dimensional breakdowns.

Available columns:
{columns}
Business metadata:
{metadata}
Question:
{question}
""".strip()


def generate_analysis_plan(question: str, columns: list[str], metadata: str = "") -> dict[str, object]:
    """Generate a JSON analysis plan through the Anthropic API."""
    if not question or not question.strip():
        raise ValueError("A question is required to plan an analysis.")
    if not columns:
        raise ValueError("At least one selected column is required for analysis.")

    api_key = ANTHROPIC_API_KEY or os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is required for analysis planning.")

    try:
        client = Anthropic(api_key=api_key)
        response = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=DEFAULT_MAX_TOKENS,
            system="Return only valid JSON for the requested analysis plan.",
            messages=[{"role": "user", "content": ANALYSIS_PLAN_PROMPT.format(
                columns=", ".join(columns), metadata=metadata, question=question
            )}],
        )
        content = "".join(getattr(block, "text", "") for block in getattr(response, "content", []) or [])
        return _parse_analysis_plan(content)
    except Exception as error:
        raise RuntimeError(f"Analysis planning failed: {error}") from error


__all__ = ["generate_sql", "generate_analysis_plan", "SYSTEM_PROMPT"]
