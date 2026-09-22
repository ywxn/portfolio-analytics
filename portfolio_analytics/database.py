"""Database access helpers for both configured databases and Excel-backed demos."""

from __future__ import annotations

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from .config import DEFAULT_DATABASE_URL, get_excel_path
from .validator import validate_sql

# TODO: Expand database access capabilities, making this tool database-agnostic.
def get_engine(database_url: str | None = None) -> Engine:
    """Create a database engine for the configured database or Excel-derived SQLite database."""
    url = database_url or DEFAULT_DATABASE_URL
    if not url:
        raise ValueError(
            "Set PORTFOLIO_EXCEL_PATH or PORTFOLIO_DB_URL before running a query."
        )
    return create_engine(url, future=True)


def load_excel_engine(excel_path: str | None = None) -> Engine:
    """Load every workbook sheet into an in-memory SQLite SQL database."""
    # The project supports workbook-based demos as a portable fallback. Each sheet
    # is normalized into a SQL table so downstream code can query it with the same
    # schema-driven interface used for a real database.
    path = excel_path or get_excel_path()
    if not path:
        raise ValueError("An Excel workbook path is required.")

    workbook = pd.ExcelFile(path)
    if not workbook.sheet_names:
        raise ValueError(f"Excel workbook contains no sheets: {path}")

    engine = create_engine("sqlite:///:memory:", future=True)
    portfolio_frames: list[pd.DataFrame] = []
    for sheet_name in workbook.sheet_names:
        # Sheet names are converted into SQL-safe identifiers so they can be used
        # as table names without collision or quoting issues in SQLite.
        table_name = str(sheet_name).strip().lower().replace(" ", "_")
        frame = pd.read_excel(workbook, sheet_name=sheet_name)
        frame.columns = [
            str(column).strip().lower().replace(" ", "_") for column in frame.columns
        ]
        if frame.empty and len(frame.columns) == 0:
            continue
        frame.to_sql(table_name, engine, index=False, if_exists="replace")
        portfolio_frame = frame.copy()
        if "portfolio_name" not in portfolio_frame.columns:
            portfolio_frame.insert(0, "portfolio_name", str(sheet_name).strip())
        portfolio_frames.append(portfolio_frame)

    if portfolio_frames:
        # The workbook may contain several portfolio sheets; this aggregate table
        # gives the rest of the app a single, consistent table for cross-portfolio
        # questions while preserving per-sheet context in the source tables.
        pd.concat(portfolio_frames, ignore_index=True, sort=False).to_sql(
            "portfolio", engine, index=False, if_exists="replace"
        )
    return engine


def execute_query(sql: str, engine: Engine | None = None) -> pd.DataFrame:
    """Execute a validated SELECT query and return a pandas DataFrame."""
    if not sql or not sql.strip():
        raise ValueError("No SQL query provided.")

    validate_sql(sql)

    engine = engine or get_engine()
    try:
        with engine.connect() as connection:
            result = connection.execute(text(sql))
            rows = result.fetchall()
            columns = list(result.keys())
    except Exception as exc:  # pragma: no cover - translation path
        raise RuntimeError(f"Database execution failed: {exc}") from exc

    if not rows:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(rows, columns=columns)


__all__ = ["get_engine", "load_excel_engine", "execute_query"]
