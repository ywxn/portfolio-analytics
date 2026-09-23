from __future__ import annotations

import time
from typing import Any, Mapping

import pandas as pd
from sqlalchemy import text

from . import llm as llm_module
from .analysis_engine import AnalysisEngine, AnalysisPlan
from .config import load_metadata
from .database import execute_query, get_engine, load_excel_engine
from .query_context import finalize_query_output, serialize_metadata, serialize_schema
from .results import AnalysisResult
from .schema import get_schema
from .validator import validate_sql


def _infer_dimensions(question: str) -> list[str]:
    lowered = question.lower()
    return [
        column
        for term, column in (
            ("sector", "sector"),
            ("geography", "geography"),
            ("region", "geography"),
            ("portfolio", "portfolio_name"),
            ("issuer", "issuer"),
            ("company", "issuer"),
        )
        if term in lowered
    ]


def _infer_metrics(question: str) -> list[str]:
    lowered = question.lower()
    metrics: list[str] = []
    if any(token in lowered for token in ("total", "sum", "overall")):
        metrics.append("market_value")
    if "average" in lowered or "avg" in lowered:
        metrics.append("average_ytm")
    if "count" in lowered or "number" in lowered:
        metrics.append("total_holdings")
    return metrics


class PortfolioAnalyzer:
    """Public orchestration entry point for the portfolio analytics backend."""

    def __init__(self, database_url: str | None = None, excel_path: str | None = None, schema: Mapping[str, Any] | None = None, metadata: Mapping[str, Any] | None = None) -> None:
        self.database_url = database_url
        self.excel_path = excel_path
        self.schema = schema
        self.metadata = metadata or load_metadata()

    def _engine(self):
        return load_excel_engine(self.excel_path) if self.excel_path or not self.database_url else get_engine(self.database_url)

    def query(self, question: str, schema: Mapping[str, Any] | None = None, metadata: Mapping[str, Any] | None = None) -> AnalysisResult:
        if not question or not question.strip():
            raise ValueError("A natural-language question is required.")
        started = time.perf_counter()
        engine = self._engine()
        resolved_schema = schema or self.schema or get_schema(engine) or {}
        resolved_metadata = metadata or self.metadata or load_metadata()
        sql = llm_module.generate_sql(question, serialize_schema(resolved_schema), serialize_metadata(resolved_metadata, question, resolved_schema))
        validate_sql(sql)
        data = finalize_query_output(execute_query(sql, engine), question)
        return AnalysisResult(question=question, sql=sql, data=data, dimensions=_infer_dimensions(question), metrics=_infer_metrics(question), execution_time=time.perf_counter() - started, warnings=[], error=None)

    def run(self, question: str, **kwargs: Any) -> AnalysisResult:
        return self.query(question, **kwargs)

    def select_data(self, table: str, columns: list[str] | None = None, filters: Mapping[str, Any] | None = None) -> pd.DataFrame:
        engine = self._engine()
        table_schema = get_schema(engine).get(table)
        if not table_schema:
            raise ValueError(f"Unknown table: {table}")
        available_columns = list(table_schema.get("columns", []))
        selected_columns = columns or available_columns
        unknown_columns = [column for column in selected_columns if column not in available_columns]
        if unknown_columns:
            raise ValueError(f"Unknown columns for {table}: {', '.join(unknown_columns)}")
        quoted_table = '"' + table.replace('"', '""') + '"'
        quoted_columns = ", ".join('"' + column.replace('"', '""') + '"' for column in selected_columns)
        params: dict[str, Any] = {}
        predicates: list[str] = []
        for index, (column, value) in enumerate((filters or {}).items()):
            if column not in available_columns:
                raise ValueError(f"Unknown filter column for {table}: {column}")
            parameter = f"filter_{index}"
            predicates.append(f'"{column.replace(chr(34), chr(34) * 2)}" = :{parameter}')
            params[parameter] = value
        sql = f"SELECT {quoted_columns} FROM {quoted_table}"
        if predicates:
            sql += " WHERE " + " AND ".join(predicates)
        with engine.connect() as connection:
            result = connection.execute(text(sql), params)
            rows = result.fetchall()
            result_columns = list(result.keys())
        return pd.DataFrame(rows, columns=result_columns)

    def list_tables(self) -> dict[str, list[str]]:
        return {table: list(table_schema.get("columns", [])) for table, table_schema in get_schema(self._engine()).items()}

    def analyze(self, question: str, data: pd.DataFrame) -> tuple[pd.DataFrame, AnalysisPlan]:
        return AnalysisEngine(metadata=self.metadata).run(data, question)


__all__ = ["PortfolioAnalyzer"]