from __future__ import annotations

import time
from typing import Any, Mapping

import pandas as pd

from . import llm as llm_module
from .analysis_engine import AnalysisEngine, AnalysisPlan
from .config import load_metadata
from .database import execute_query, get_engine, load_excel_engine
from .results import AnalysisResult
from .schema import get_schema
from .validator import validate_sql


def _infer_dimensions(question: str) -> list[str]:
    lowered = question.lower()
    dimensions: list[str] = []
    if "sector" in lowered:
        dimensions.append("sector")
    if "geography" in lowered or "region" in lowered:
        dimensions.append("geography")
    if "portfolio" in lowered:
        dimensions.append("portfolio_name")
    if "issuer" in lowered or "company" in lowered:
        dimensions.append("issuer")
    return dimensions


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


def _serialize_schema(schema: Mapping[str, Any] | None) -> str:
    if not schema:
        return ""

    lines: list[str] = []
    for table_name, table_schema in schema.items():
        if isinstance(table_schema, Mapping):
            columns = table_schema.get("columns", [])
            foreign_keys = table_schema.get("foreign_keys", [])
        else:
            columns = []
            foreign_keys = []

        lines.append(f"Table: {table_name}")
        lines.append(f"  Columns: {', '.join(columns)}")
        if foreign_keys:
            lines.append(f"  Foreign keys: {foreign_keys}")
    return "\n".join(lines)


def _serialize_metadata(metadata: Mapping[str, Any] | None) -> str:
    if not metadata:
        return ""
    if isinstance(metadata, str):
        return metadata
    return str(metadata)


def _finalize_output(df: pd.DataFrame, question: str) -> pd.DataFrame:
    if df.empty:
        return df

    lowered = question.lower()
    if "pivot" in lowered:
        return df.copy()
    if "by" in lowered or "group" in lowered:
        return df.copy()
    if "total" in lowered or "sum" in lowered or "avg" in lowered:
        return df.copy()
    return df.head(20).copy()


class PortfolioAnalyzer:
    """Public orchestration entry point for the portfolio analytics backend."""

    def __init__(
        self,
        database_url: str | None = None,
        excel_path: str | None = None,
        schema: Mapping[str, Any] | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        self.database_url = database_url
        self.excel_path = excel_path
        self.schema = schema
        self.metadata = metadata or load_metadata()

    def query(
        self,
        question: str,
        schema: Mapping[str, Any] | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> AnalysisResult:
        if not question or not question.strip():
            raise ValueError("A natural-language question is required.")

        started = time.perf_counter()
        engine = (
            load_excel_engine(self.excel_path)
            if self.excel_path or not self.database_url
            else get_engine(self.database_url)
        )

        resolved_schema = schema or self.schema or get_schema(engine)
        resolved_schema = resolved_schema or {}
        resolved_metadata = metadata or self.metadata or load_metadata()

        sql = llm_module.generate_sql(
            question,
            _serialize_schema(resolved_schema),
            _serialize_metadata(resolved_metadata),
        )
        validate_sql(sql)

        df = execute_query(sql, engine)
        result = _finalize_output(df, question)
        dimensions = _infer_dimensions(question)
        metrics = _infer_metrics(question)
        return AnalysisResult(
            question=question,
            sql=sql,
            data=result,
            dimensions=dimensions,
            metrics=metrics,
            execution_time=time.perf_counter() - started,
            warnings=[],
            error=None,
        )

    def run(self, question: str, **kwargs: Any) -> AnalysisResult:
        return self.query(question, **kwargs)

    def select_data(
        self,
        table: str,
        columns: list[str] | None = None,
        filters: Mapping[str, Any] | None = None,
    ) -> pd.DataFrame:
        """Select a read-only slice of one database table for further analysis."""
        engine = (
            load_excel_engine(self.excel_path)
            if self.excel_path or not self.database_url
            else get_engine(self.database_url)
        )
        available_schema = get_schema(engine)
        table_schema = available_schema.get(table)
        if not table_schema:
            raise ValueError(f"Unknown table: {table}")

        available_columns = list(table_schema.get("columns", []))
        selected_columns = columns or available_columns
        unknown_columns = [
            column for column in selected_columns if column not in available_columns
        ]
        if unknown_columns:
            raise ValueError(
                f"Unknown columns for {table}: {', '.join(unknown_columns)}"
            )

        quoted_table = '"' + table.replace('"', '""') + '"'
        quoted_columns = ", ".join(
            '"' + column.replace('"', '""') + '"' for column in selected_columns
        )
        params: dict[str, Any] = {}
        predicates: list[str] = []
        for index, (column, value) in enumerate((filters or {}).items()):
            if column not in available_columns:
                raise ValueError(f"Unknown filter column for {table}: {column}")
            parameter = f"filter_{index}"
            predicates.append(
                f'"{column.replace(chr(34), chr(34) * 2)}" = :{parameter}'
            )
            params[parameter] = value

        sql = f"SELECT {quoted_columns} FROM {quoted_table}"
        if predicates:
            sql += " WHERE " + " AND ".join(predicates)

        from sqlalchemy import text

        with engine.connect() as connection:
            result = connection.execute(text(sql), params)
            rows = result.fetchall()
            result_columns = list(result.keys())
        return pd.DataFrame(rows, columns=result_columns)

    def list_tables(self) -> dict[str, list[str]]:
        """Return selectable table names and their columns for CLI discovery."""
        engine = (
            load_excel_engine(self.excel_path)
            if self.excel_path or not self.database_url
            else get_engine(self.database_url)
        )
        return {
            table: list(table_schema.get("columns", []))
            for table, table_schema in get_schema(engine).items()
        }

    def analyze(
        self,
        question: str,
        data: pd.DataFrame,
    ) -> tuple[pd.DataFrame, AnalysisPlan]:
        """Use the LLM to plan analysis over an already selected dataframe."""
        engine = AnalysisEngine(metadata=self.metadata)
        return engine.run(data, question)
