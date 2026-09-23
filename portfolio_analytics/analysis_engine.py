from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, cast

import pandas as pd

from .dataframe_operations import SUPPORTED_AGGREGATIONS, analyze_dataframe
from . import llm
from .metadata_catalog import format_metadata_for_prompt


@dataclass
class AnalysisPlan:
    """Structured instructions produced by the LLM for dataframe analysis."""

    dimensions: list[str] = field(default_factory=list)
    metric: str | None = None
    aggregation: str = "sum"
    pivot_index: list[str] = field(default_factory=list)
    pivot_columns: list[str] = field(default_factory=list)
    limit: int | None = None
    sort_by: str | None = None
    ascending: bool = True
    filters: dict[str, Any] = field(default_factory=dict)


class AnalysisEngine:
    """Use an LLM to plan analysis, then execute it deterministically in pandas."""

    def __init__(self, metadata: Mapping[str, Any] | None = None) -> None:
        self.metadata = metadata or {}

    def plan(self, question: str, columns: list[str]) -> AnalysisPlan:
        metadata_text = format_metadata_for_prompt(self.metadata, question)
        raw_plan = llm.generate_analysis_plan(question, columns, metadata_text)
        plan = AnalysisPlan(
            dimensions=list(cast(list[str], raw_plan.get("dimensions", []))),
            metric=cast(str | None, raw_plan.get("metric")),
            aggregation=cast(str, raw_plan.get("aggregation", "sum")),
            pivot_index=list(cast(list[str], raw_plan.get("pivot_index", []))),
            pivot_columns=list(cast(list[str], raw_plan.get("pivot_columns", []))),
            limit=cast(int | None, raw_plan.get("limit")),
            sort_by=cast(str | None, raw_plan.get("sort_by")),
            ascending=bool(raw_plan.get("ascending", True)),
            filters=dict(cast(dict[str, Any], raw_plan.get("filters", {}))),
        )
        unknown = [
            column
            for column in [
                *plan.dimensions,
                plan.metric,
                *plan.pivot_index,
                *plan.pivot_columns,
                plan.sort_by,
            ]
            if column and column not in columns
        ]
        if unknown:
            raise ValueError(
                f"Analysis plan references unavailable columns: {', '.join(unknown)}"
            )
        if plan.aggregation not in SUPPORTED_AGGREGATIONS:
            raise ValueError(f"Unsupported aggregation: {plan.aggregation}")
        return plan


    # TODO: Allow LLM-generated Python code if built-in functions are insufficient
    def run(self, df: pd.DataFrame, question: str) -> tuple[pd.DataFrame, AnalysisPlan]:
        plan = self.plan(question, [str(column) for column in df.columns])
        sort_by = plan.sort_by
        ascending = plan.ascending
        if sort_by is None and plan.limit and plan.metric and plan.dimensions:
            question_lower = question.lower()
            if any(term in question_lower for term in ("top", "highest", "largest", "most")):
                sort_by, ascending = plan.metric, False
            elif any(term in question_lower for term in ("bottom", "lowest", "smallest", "least")):
                sort_by, ascending = plan.metric, True
        selected = df.copy()
        for column, expected in plan.filters.items():
            if column not in selected.columns:
                raise ValueError(f"Filter references unavailable column: {column}")
            if isinstance(expected, list):
                selected = selected[selected[column].isin(expected)]
            else:
                selected = selected[selected[column] == expected]
        return (
            analyze_dataframe(
                selected,
                dimensions=plan.dimensions,
                metric=plan.metric,
                aggregation=plan.aggregation,
                pivot_index=plan.pivot_index,
                pivot_columns=plan.pivot_columns,
                limit=plan.limit,
                sort_by=sort_by,
                ascending=ascending,
            ),
            plan,
        )


__all__ = ["AnalysisEngine", "AnalysisPlan"]
