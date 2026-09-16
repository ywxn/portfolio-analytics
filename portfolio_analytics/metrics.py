from __future__ import annotations

import pandas as pd


def percent_of_total(
    df: pd.DataFrame,
    value_column: str,
    group_by: str | list[str] | None = None,
    total_column: str | None = None,
) -> pd.DataFrame:
    """Return a percentage-of-total metric for each row or group."""
    if df.empty:
        return df.copy()

    total_value = float(df[value_column].sum()) if value_column in df.columns else 0.0
    if total_value == 0:
        data = df.copy()
        data[total_column or f"{value_column}_pct"] = 0.0
        return data

    result = df.copy()
    pct_name = total_column or f"{value_column}_pct"
    if group_by is None:
        result[pct_name] = (result[value_column] / total_value) * 100.0
        return result

    grouped = result.groupby(group_by, dropna=False)[value_column].transform("sum")
    result[pct_name] = (result[value_column] / grouped) * 100.0
    return result


def ratio(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return float(numerator) / float(denominator)


def difference(current: float, baseline: float) -> float:
    return float(current) - float(baseline)


def growth(baseline: float, current: float) -> float:
    if baseline == 0:
        return 0.0
    return (float(current) - float(baseline)) / float(baseline)


__all__ = ["percent_of_total", "ratio", "difference", "growth"]
