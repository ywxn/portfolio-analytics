from __future__ import annotations

from typing import Any, Mapping

import pandas as pd

from .metadata_catalog import format_metadata_for_prompt


def serialize_schema(schema: Mapping[str, Any] | None) -> str:
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


def serialize_metadata(
    metadata: Mapping[str, Any] | None,
    question: str = "",
    schema: Mapping[str, Any] | None = None,
) -> str:
    table_names = list(schema) if schema else None
    return format_metadata_for_prompt(metadata, question, table_names)


def finalize_query_output(df: pd.DataFrame, question: str) -> pd.DataFrame:
    if df.empty:
        return df

    lowered = question.lower()
    if any(term in lowered for term in ("pivot", "by", "group", "total", "sum", "avg")):
        return df.copy()
    return df.head(20).copy()


__all__ = ["serialize_schema", "serialize_metadata", "finalize_query_output"]