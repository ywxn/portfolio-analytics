"""Reusable dataframe aggregation helpers for portfolio analytics questions."""

# TODO: Add more sophisticated aggregation functions and validation logic.
#       Additionally, adding support for LLM generated Python code, though for this
#       we'll need to expand the planning stage.

from __future__ import annotations

import pandas as pd
from typing import Literal, cast

Aggregation = Literal[
    "sum", "prod", "mean", "median", "min", "max", "count", "std", "var", "size"
]

SUPPORTED_AGGREGATIONS = {
    "sum",
    "prod",
    "mean",
    "median",
    "min",
    "max",
    "count",
    "std",
    "var",
    "size",
}


def pivot(
    df: pd.DataFrame,
    index: str | list[str] | None = None,
    columns: str | list[str] | None = None,
    values: str | list[str] | None = None,
    aggfunc: Aggregation = "sum",
) -> pd.DataFrame:
    """Pivot a dataframe using pandas' table-style aggregation semantics."""
    if df.empty:
        return df.copy()
    return df.pivot_table(
        index=index,
        columns=columns,
        values=values,
        aggfunc=aggfunc,
        observed=False,
    )


def summarize_by(
    df: pd.DataFrame,
    by: str | list[str],
    metric: str,
    aggfunc: str = "sum",
) -> pd.DataFrame:
    """Group rows by a dimension and aggregate a single metric for each group."""
    if isinstance(by, str):
        by = [by]
    return df.groupby(by, dropna=False)[metric].agg(aggfunc).reset_index()


def top_n(df: pd.DataFrame, column: str, n: int = 10) -> pd.DataFrame:
    """Return the largest n rows for a metric column without mutating the input."""
    return df.nlargest(n, column).copy()


def bottom_n(df: pd.DataFrame, column: str, n: int = 10) -> pd.DataFrame:
    """Return the smallest n rows for a metric column without mutating the input."""
    return df.nsmallest(n, column).copy()


def analyze_dataframe(
    df: pd.DataFrame,
    dimensions: list[str] | None = None,
    metric: str | None = None,
    aggregation: str = "sum",
    pivot_index: list[str] | None = None,
    pivot_columns: list[str] | None = None,
    limit: int | None = None,
) -> pd.DataFrame:
    """Apply a validated dynamic analysis plan to a selected dataframe."""
    if df.empty:
        return df.copy()

    dimensions = dimensions or []
    missing = [
        column
        for column in [*dimensions, metric]
        if column and column not in df.columns
    ]
    if missing:
        raise ValueError(
            f"Analysis columns are not present in the selected data: {', '.join(missing)}"
        )
    if aggregation not in SUPPORTED_AGGREGATIONS:
        raise ValueError(f"Unsupported aggregation: {aggregation}")

    result = df.copy()
    if dimensions and metric:
        if pivot_index or pivot_columns:
            result = pivot(
                result,
                index=pivot_index or dimensions,
                columns=pivot_columns,
                values=metric,
                aggfunc=cast(Aggregation, aggregation),
            ).reset_index()
        else:
            result = summarize_by(result, dimensions, metric, aggregation)
    elif dimensions and aggregation == "size":
        result = df.groupby(dimensions, dropna=False).size().reset_index(name="count")
    elif metric and aggregation != "size":
        result = pd.DataFrame({metric: [result[metric].agg(aggregation)]})

    if limit is not None and limit > 0:
        result = result.head(limit)
    return result


__all__ = [
    "SUPPORTED_AGGREGATIONS",
    "pivot",
    "summarize_by",
    "top_n",
    "bottom_n",
    "analyze_dataframe",
]
