from __future__ import annotations

from typing import Any, Mapping

import pandas as pd

from config import load_metadata
from database import execute_query, get_engine, load_excel_engine
from llm import generate_sql
from schema import get_schema
from validator import validate_sql


def _serialize_schema(schema: Mapping[str, Any] | None) -> str:
    if not schema:
        return ""

    lines: list[str] = []
    for table_name, table_schema in schema.items():
        if isinstance(table_schema, Mapping):
            columns = table_schema.get("columns", [])
            foreign_keys = table_schema.get("foreign_keys", [])
        else:
            columns = []
            foreign_keys = []

        lines.append(f"Table: {table_name}")
        lines.append(f"  Columns: {', '.join(columns)}")
        if foreign_keys:
            lines.append(f"  Foreign keys: {foreign_keys}")
    return "\n".join(lines)


def _serialize_metadata(metadata: Mapping[str, Any] | None) -> str:
    if not metadata:
        return ""
    if isinstance(metadata, str):
        return metadata
    return str(metadata)


def _finalize_output(df: pd.DataFrame, question: str) -> pd.DataFrame:
    # TODO: Replace the row-limit heuristic with an analytical engine for
    # aggregations, pivots, multidimensional breakdowns, ranking, top/bottom N,
    # percentages, ratios, differences, growth, and subtotals.
    if df.empty:
        return df

    lowered = question.lower()
    if "pivot" in lowered:
        if len(df.columns) >= 2 and df.shape[0] > 0:
            return df.copy()
    if "by" in lowered or "group" in lowered:
        return df.copy()
    if "total" in lowered or "sum" in lowered or "avg" in lowered:
        return df.copy()
    return df.head(20).copy()


def blog_query(
    question: str,
    schema: Mapping[str, Any] | None = None,
    metadata: Mapping[str, Any] | None = None,
    database_url: str | None = None,
    excel_path: str | None = None,
) -> dict[str, Any]:
    """Generate SQL and execute it, returning both the generated SQL and the output dataframe."""
    # TODO: Add bounded SQL error-correction retries; every retry must be
    # revalidated before execution and must return a useful typed error.
    # TODO: Accept caller-owned query context/follow-ups and return structured
    # dimensions, metric, intent, and execution metadata alongside the data.
    if not question or not question.strip():
        raise ValueError("A natural-language question is required.")

    engine = (
        load_excel_engine(excel_path)
        if excel_path or not database_url
        else get_engine(database_url)
    )
    if schema is None:
        schema = get_schema(engine)
    schema = schema or {}
    metadata = metadata or load_metadata()

    schema_text = _serialize_schema(schema)
    metadata_text = _serialize_metadata(metadata)
    sql = generate_sql(question, schema_text, metadata_text)
    validate_sql(sql)

    df = execute_query(sql, engine)
    return {"sql": sql, "data": _finalize_output(df, question)}


def run_pipeline(
    question: str,
    schema: Mapping[str, Any] | None = None,
    metadata: Mapping[str, Any] | None = None,
    database_url: str | None = None,
    excel_path: str | None = None,
) -> pd.DataFrame:
    """Run the full NLP-to-SQL-to-output flow and return the dataframe."""
    # TODO: Expose a stable public analyzer/query interface instead of keeping
    # integration behavior coupled to this internal pipeline function.
    return blog_query(
        question,
        schema=schema,
        metadata=metadata,
        database_url=database_url,
        excel_path=excel_path,
    )["data"]


if __name__ == "__main__":
    sample_question = "What is the total value by portfolio name?"
    sample_schema = {
        "portfolio": {
            "columns": ["portfolio_id", "portfolio_name", "market_value"],
            "foreign_keys": [],
        }
    }
    sample_metadata = {"table_descriptions": {"portfolio": "One row per portfolio"}}
    outcome = blog_query(sample_question, sample_schema, sample_metadata)
    print(outcome["sql"])
    print(outcome["data"])
