from __future__ import annotations

import os
import re

from anthropic import Anthropic

from config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL


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

    # Remove Markdown code fences if the model ignores the SQL-only instruction.
    match = re.fullmatch(
        r"```(?:sql|postgresql)?\s*(.*?)\s*```",
        sql,
        flags=re.IGNORECASE | re.DOTALL,
    )

    if match:
        sql = match.group(1).strip()

    # Remove a trailing semicolon only if desired by downstream tooling.
    # Keeping it is valid PostgreSQL, so leave it intact.

    return sql


def generate_sql(question: str, schema: str, metadata: str) -> str:
    """Generate a read-only PostgreSQL SELECT query from a natural-language question.

    Anthropic is required for SQL generation. SQL safety and validity are
    enforced separately by the application's SQL validator.
    """
    cleaned_question = (question or "").strip()

    if not cleaned_question:
        raise ValueError("A question is required to generate SQL.")

    if not schema or not schema.strip():
        raise ValueError("Schema information is required to generate SQL.")

    api_key = ANTHROPIC_API_KEY or os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY is required for SQL generation."
        )

    try:
        client = Anthropic(api_key=api_key)

        response = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": (
                        "<schema>\n"
                        f"{schema.strip()}\n"
                        "</schema>\n\n"
                        "<metadata>\n"
                        f"{(metadata or '').strip()}\n"
                        "</metadata>\n\n"
                        "<question>\n"
                        f"{cleaned_question}\n"
                        "</question>\n\n"
                        "Return exactly one PostgreSQL SELECT statement."
                    ),
                }
            ],
        )

    except Exception as error:
        raise RuntimeError(
            f"Anthropic SQL generation failed: {error}"
        ) from error

    parts: list[str] = []

    for block in getattr(response, "content", []) or []:
        text = getattr(block, "text", None)

        if text:
            parts.append(text)

    sql = _clean_sql("".join(parts))

    if not sql:
        raise RuntimeError("Anthropic returned an empty SQL query.")

    return sql