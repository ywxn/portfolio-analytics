from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

import pandas as pd

from .analytics import SUPPORTED_AGGREGATIONS, analyze_dataframe
from . import llm


@dataclass
class AnalysisPlan:
    """Structured instructions produced by the LLM for dataframe analysis."""

    dimensions: list[str] = field(default_factory=list)
    metric: str | None = None
    aggregation: str = "sum"
    pivot_index: list[str] = field(default_factory=list)
    pivot_columns: list[str] = field(default_factory=list)
    limit: int | None = None
    filters: dict[str, Any] = field(default_factory=dict)


class AnalysisEngine:
    """Use an LLM to plan analysis, then execute it deterministically in pandas."""

    def __init__(self, metadata: Mapping[str, Any] | None = None) -> None:
        self.metadata = metadata or {}

    def plan(self, question: str, columns: list[str]) -> AnalysisPlan:
        raw_plan = llm.generate_analysis_plan(question, columns, str(self.metadata))
        plan = AnalysisPlan(
            dimensions=list(raw_plan.get("dimensions", [])),
            metric=raw_plan.get("metric"),
            aggregation=raw_plan.get("aggregation", "sum"),
            pivot_index=list(raw_plan.get("pivot_index", [])),
            pivot_columns=list(raw_plan.get("pivot_columns", [])),
            limit=raw_plan.get("limit"),
            filters=dict(raw_plan.get("filters", {})),
        )
        unknown = [
            column
            for column in [*plan.dimensions, plan.metric, *plan.pivot_index, *plan.pivot_columns]
            if column and column not in columns
        ]
        if unknown:
            raise ValueError(f"Analysis plan references unavailable columns: {', '.join(unknown)}")
        if plan.aggregation not in SUPPORTED_AGGREGATIONS:
            raise ValueError(f"Unsupported aggregation: {plan.aggregation}")
        return plan

    def run(self, df: pd.DataFrame, question: str) -> tuple[pd.DataFrame, AnalysisPlan]:
        plan = self.plan(question, [str(column) for column in df.columns])
        selected = df.copy()
        for column, expected in plan.filters.items():
            if column not in selected.columns:
                raise ValueError(f"Filter references unavailable column: {column}")
            if isinstance(expected, list):
                selected = selected[selected[column].isin(expected)]
            else:
                selected = selected[selected[column] == expected]
        return analyze_dataframe(
            selected,
            dimensions=plan.dimensions,
            metric=plan.metric,
            aggregation=plan.aggregation,
            pivot_index=plan.pivot_index,
            pivot_columns=plan.pivot_columns,
            limit=plan.limit,
        ), plan


__all__ = ["AnalysisEngine", "AnalysisPlan"]