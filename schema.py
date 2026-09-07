from __future__ import annotations

from typing import Any

from sqlalchemy import inspect


def get_schema(engine) -> dict[str, dict[str, Any]]:
    """Retrieve table names, columns, and foreign keys from a SQLAlchemy engine."""
    # TODO: Expand schema discovery with column data types, primary keys, and
    # normalized relationship details for reliable LLM prompts and validation.
    inspector = inspect(engine)
    schema: dict[str, dict[str, Any]] = {}
    for table in inspector.get_table_names():
        schema[table] = {
            "columns": [column["name"] for column in inspector.get_columns(table)],
            "foreign_keys": inspector.get_foreign_keys(table),
        }
    return schema
