"""Utilities for introspecting database schema into prompt-friendly metadata."""

from __future__ import annotations

from typing import Any, Mapping

from sqlalchemy import inspect


def get_schema(engine) -> dict[str, dict[str, Any]]:
    """Retrieve table names, columns, primary keys, data types, and foreign keys."""
    inspector = inspect(engine)
    schema: dict[str, dict[str, Any]] = {}
    for table in inspector.get_table_names():
        columns = inspector.get_columns(table)
        schema[table] = {
            "columns": [column["name"] for column in columns],
            "column_types": {column["name"]: str(column["type"]) for column in columns},
            "primary_keys": inspector.get_pk_constraint(table).get(
                "constrained_columns", []
            ),
            "foreign_keys": inspector.get_foreign_keys(table),
        }
    return schema


def format_schema_for_prompt(schema: Mapping[str, Any] | None) -> str:
    """Flatten schema metadata into a compact string for LLM prompts."""
    if not schema:
        return ""

    lines: list[str] = []
    for table_name, table_schema in schema.items():
        if not isinstance(table_schema, Mapping):
            continue
        columns = table_schema.get("columns", [])
        column_types = table_schema.get("column_types", {})
        primary_keys = table_schema.get("primary_keys", [])
        foreign_keys = table_schema.get("foreign_keys", [])

        lines.append(f"Table: {table_name}")
        if columns:
            column_lines: list[str] = []
            for column_name in columns:
                type_name = column_types.get(column_name, "UNKNOWN")
                column_lines.append(f"{column_name}: {type_name}")
            lines.append("  Columns: " + ", ".join(column_lines))
        if primary_keys:
            lines.append(f"  Primary keys: {', '.join(primary_keys)}")
        if foreign_keys:
            lines.append(f"  Foreign keys: {foreign_keys}")
    return "\n".join(lines)


__all__ = ["get_schema", "format_schema_for_prompt"]
