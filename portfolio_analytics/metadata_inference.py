from __future__ import annotations

import json
from typing import Any

import pandas as pd

from .llm import generate_metadata
from .schema import format_schema_for_prompt


def infer_metadata(
    data: pd.DataFrame | dict[str, pd.DataFrame],
    table_name: str = "data",
    sample_size: int = 20,
    schema: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Infer business metadata for one or more data tables."""
    if sample_size <= 0:
        raise ValueError("sample_size must be greater than zero.")
    tables = {table_name: data} if isinstance(data, pd.DataFrame) else data
    if not isinstance(tables, dict) or not tables:
        raise ValueError("data must be a DataFrame or a non-empty table mapping.")
    if schema is not None and not isinstance(schema, dict):
        raise TypeError("schema must be a table schema mapping.")

    schema_text = format_schema_for_prompt(schema)
    inferred_tables: dict[str, dict[str, Any]] = {}
    business_metrics: dict[str, Any] = {}
    for name, frame in tables.items():
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Every table must have a non-empty string name.")
        if not isinstance(frame, pd.DataFrame):
            raise TypeError(f"Table '{name}' must be a pandas DataFrame.")
        if frame.empty or len(frame.columns) == 0:
            raise ValueError(f"Table '{name}' must contain columns and at least one row.")
        columns = {str(column): str(dtype) for column, dtype in frame.dtypes.items()}
        arguments = (name, json.dumps(columns), frame.head(sample_size).to_json(orient="records", date_format="iso"))
        inferred = generate_metadata(*arguments, schema=schema_text) if schema_text else generate_metadata(*arguments)
        inferred.setdefault("columns", list(columns))
        inferred_tables[name] = inferred
        metrics = inferred.get("metrics", {})
        if isinstance(metrics, dict):
            business_metrics.update(metrics)

    result: dict[str, Any] = {"tables": inferred_tables}
    if business_metrics:
        result["business_metrics"] = business_metrics
    return result


__all__ = ["infer_metadata"]