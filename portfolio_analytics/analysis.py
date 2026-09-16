from __future__ import annotations

from typing import Any, Mapping

import pandas as pd

from .config import load_metadata
from .database import execute_query, get_engine, load_excel_engine
from .llm import generate_sql
from .schema import get_schema
from .validator import validate_sql


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
    if df.empty:
        return df

    lowered = question.lower()
    if "pivot" in lowered or "by" in lowered or "group" in lowered:
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
    if not question or not question.strip():
        raise ValueError("A natural-language question is required.")

    engine = (
        load_excel_engine(excel_path)
        if excel_path or not database_url
        else get_engine(database_url)
    )

    resolved_schema = get_schema(engine) if schema is None else schema
    resolved_schema = resolved_schema or {}
    resolved_metadata = metadata or load_metadata()

    schema_text = _serialize_schema(resolved_schema)
    metadata_text = _serialize_metadata(resolved_metadata)
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
    return blog_query(
        question,
        schema=schema,
        metadata=metadata,
        database_url=database_url,
        excel_path=excel_path,
    )["data"]


__all__ = ["blog_query", "run_pipeline"]
