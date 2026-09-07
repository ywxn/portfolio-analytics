from __future__ import annotations

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from config import DEFAULT_DATABASE_URL, get_excel_path


def get_engine(database_url: str | None = None) -> Engine:
    # TODO: Support the target production database type and configure a
    # read-only connection/user at the database layer.
    url = database_url or DEFAULT_DATABASE_URL
    if not url:
        raise ValueError(
            "Set PORTFOLIO_EXCEL_PATH or PORTFOLIO_DB_URL before running a query."
        )
    return create_engine(url, future=True)


def load_excel_engine(excel_path: str | None = None) -> Engine:
    """Load every workbook sheet into an in-memory SQLite SQL database."""
    path = excel_path or get_excel_path()
    if not path:
        raise ValueError("An Excel workbook path is required.")

    workbook = pd.ExcelFile(path)
    if not workbook.sheet_names:
        raise ValueError(f"Excel workbook contains no sheets: {path}")

    engine = create_engine("sqlite:///:memory:", future=True)
    for sheet_name in workbook.sheet_names:
        table_name = str(sheet_name).strip().lower().replace(" ", "_")
        frame = pd.read_excel(workbook, sheet_name=sheet_name)
        frame.columns = [
            str(column).strip().lower().replace(" ", "_") for column in frame.columns
        ]
        if frame.empty and len(frame.columns) == 0:
            continue
        frame.to_sql(table_name, engine, index=False, if_exists="replace")
    return engine


def execute_query(sql: str, engine: Engine | None = None) -> pd.DataFrame:
    """Execute a SELECT query and return a pandas DataFrame."""
    # TODO: Enforce validation before execution, add connection/execution
    # error translation, and apply read-only defense-in-depth safeguards.
    if not sql or not sql.strip():
        raise ValueError("No SQL query provided.")

    engine = engine or get_engine()
    with engine.connect() as connection:
        result = connection.execute(text(sql))
        rows = result.fetchall()
        columns = list(result.keys())

    if not rows:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(rows, columns=columns)
