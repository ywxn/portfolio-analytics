from __future__ import annotations

from typing import Any, Literal, cast

import pandas as pd

Aggregation = Literal[
    "sum", "prod", "mean", "median", "min", "max", "count", "std", "var", "size"
]

SUPPORTED_AGGREGATIONS = {
    "sum", "prod", "mean", "median", "min", "max", "count", "std", "var", "size"
}


def aggregate_dataframe(df: pd.DataFrame, by: str | list[str] | None = None, metric: str | None = None, aggfunc: str = "sum") -> pd.DataFrame:
    if metric is None:
        raise ValueError("A metric column is required for aggregation.")
    if metric not in df.columns:
        raise ValueError(f"Unknown metric column: {metric}")
    if by is None:
        return pd.DataFrame({metric: [df[metric].agg(aggfunc)]})
    group_columns = [by] if isinstance(by, str) else list(by)
    unknown = [column for column in group_columns if column not in df.columns]
    if unknown:
        raise ValueError(f"Unknown group columns: {', '.join(unknown)}")
    return df.groupby(group_columns, dropna=False, sort=False)[metric].agg(aggfunc).reset_index()


def sort_dataframe(df: pd.DataFrame, column: str, ascending: bool = False) -> pd.DataFrame:
    if column not in df.columns:
        raise ValueError(f"Unknown sort column: {column}")
    return df.sort_values(by=column, ascending=ascending).reset_index(drop=True)


def limit_dataframe(df: pd.DataFrame, rows: int = 10) -> pd.DataFrame:
    if rows < 1:
        raise ValueError("Row limit must be at least 1.")
    return df.head(rows).copy()


def pivot(df: pd.DataFrame, index: str | list[str] | None = None, columns: str | list[str] | None = None, values: str | list[str] | None = None, aggfunc: Aggregation = "sum") -> pd.DataFrame:
    if df.empty:
        return df.copy()
    return df.pivot_table(index=index, columns=columns, values=values, aggfunc=aggfunc, observed=False)


def summarize_by(df: pd.DataFrame, by: str | list[str], metric: str, aggfunc: str = "sum") -> pd.DataFrame:
    group_columns = [by] if isinstance(by, str) else by
    return df.groupby(group_columns, dropna=False)[metric].agg(aggfunc).reset_index()


def top_n(df: pd.DataFrame, column: str, n: int = 10) -> pd.DataFrame:
    return df.nlargest(n, column).copy()


def bottom_n(df: pd.DataFrame, column: str, n: int = 10) -> pd.DataFrame:
    return df.nsmallest(n, column).copy()


def analyze_dataframe(df: pd.DataFrame, dimensions: list[str] | None = None, metric: str | None = None, aggregation: str = "sum", pivot_index: list[str] | None = None, pivot_columns: list[str] | None = None, limit: int | None = None, sort_by: str | None = None, ascending: bool = True) -> pd.DataFrame:
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
            result = pivot(result, index=pivot_index or dimensions, columns=pivot_columns, values=metric, aggfunc=cast(Aggregation, aggregation)).reset_index()
        else:
            result = summarize_by(result, dimensions, metric, aggregation)
    elif dimensions and aggregation == "size":
        result = df.groupby(dimensions, dropna=False).size().reset_index(name="count")
    elif metric and aggregation != "size":
        result = pd.DataFrame({metric: [result[metric].agg(aggregation)]})
    if limit is not None and limit > 0:
        if sort_by is not None:
            if sort_by not in result.columns:
                raise ValueError(f"Unknown sort column: {sort_by}")
            result = result.sort_values(by=sort_by, ascending=ascending, kind="stable")
        result = result.head(limit)
    return result


__all__ = ["SUPPORTED_AGGREGATIONS", "aggregate_dataframe", "sort_dataframe", "limit_dataframe", "pivot", "summarize_by", "top_n", "bottom_n", "analyze_dataframe"]