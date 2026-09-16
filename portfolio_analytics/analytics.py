from __future__ import annotations

import pandas as pd
from typing import Literal


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
    aggfunc: Literal[
        "sum", "prod", "mean", "median", "min", "max", "count", "std", "var", "size"
    ] = "sum",
) -> pd.DataFrame:
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
    if isinstance(by, str):
        by = [by]
    return df.groupby(by, dropna=False)[metric].agg(aggfunc).reset_index()


def top_n(df: pd.DataFrame, column: str, n: int = 10) -> pd.DataFrame:
    return df.nlargest(n, column).copy()


def bottom_n(df: pd.DataFrame, column: str, n: int = 10) -> pd.DataFrame:
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
    missing = [column for column in [*dimensions, metric] if column and column not in df.columns]
    if missing:
        raise ValueError(f"Analysis columns are not present in the selected data: {', '.join(missing)}")
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
                aggfunc=aggregation,
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
