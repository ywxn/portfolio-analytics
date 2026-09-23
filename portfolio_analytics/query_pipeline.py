from __future__ import annotations

from typing import Any, Callable, Mapping

import pandas as pd

from .config import load_metadata
from .database import execute_query, get_engine, load_excel_engine
from .llm import generate_sql
from .query_context import finalize_query_output, serialize_metadata, serialize_schema
from .schema import get_schema
from .validator import validate_sql


def execute_query_pipeline(
    question: str,
    schema: Mapping[str, Any] | None = None,
    metadata: Mapping[str, Any] | None = None,
    database_url: str | None = None,
    excel_path: str | None = None,
    sql_generator: Callable[[str, str, str], str] | None = None,
) -> dict[str, Any]:
    """Generate, validate, and execute one natural-language database query."""
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

    sql = (sql_generator or generate_sql)(
        question,
        serialize_schema(resolved_schema),
        serialize_metadata(resolved_metadata, question, resolved_schema),
    )
    validate_sql(sql)

    data = execute_query(sql, engine)
    return {"sql": sql, "data": finalize_query_output(data, question)}


def run_pipeline(
    question: str,
    schema: Mapping[str, Any] | None = None,
    metadata: Mapping[str, Any] | None = None,
    database_url: str | None = None,
    excel_path: str | None = None,
    sql_generator: Callable[[str, str, str], str] | None = None,
) -> pd.DataFrame:
    """Run the query pipeline and return only its dataframe result."""
    return execute_query_pipeline(
        question,
        schema=schema,
        metadata=metadata,
        database_url=database_url,
        excel_path=excel_path,
        sql_generator=sql_generator,
    )["data"]


__all__ = ["execute_query_pipeline", "run_pipeline"]