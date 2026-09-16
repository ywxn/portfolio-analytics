from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd


@dataclass
class AnalysisResult:
    question: str
    sql: str
    data: pd.DataFrame
    dimensions: list[str] = field(default_factory=list)
    metrics: list[str] = field(default_factory=list)
    execution_time: float | None = None
    warnings: list[str] = field(default_factory=list)
    error: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "question": self.question,
            "sql": self.sql,
            "data": self.data,
            "dimensions": self.dimensions,
            "metrics": self.metrics,
            "execution_time": self.execution_time,
            "warnings": self.warnings,
            "error": self.error,
        }
