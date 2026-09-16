from __future__ import annotations

import pandas as pd

from database import execute_query as _execute_query


def execute_query(sql: str, engine=None) -> pd.DataFrame:
    if not sql or not sql.strip():
        raise ValueError("No SQL query provided.")
    return _execute_query(sql, engine)


__all__ = ["execute_query"]
