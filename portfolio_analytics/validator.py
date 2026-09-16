from __future__ import annotations

import sqlglot
from sqlglot import expressions as exp


def validate_sql(sql: str) -> bool:
    """Validate that SQL is syntactically valid and read-only."""
    if not sql or not sql.strip():
        raise ValueError("SQL is empty.")

    try:
        statements = sqlglot.parse(sql.strip())
    except sqlglot.ParseError as exc:
        raise ValueError(f"Invalid SQL syntax: {exc}") from exc

    if not statements:
        raise ValueError("SQL contains no statements.")

    forbidden = (
        exp.Insert,
        exp.Update,
        exp.Delete,
        exp.Merge,
        exp.Create,
        exp.Drop,
        exp.Alter,
        exp.Grant,
        exp.Revoke,
    )
    for name in ("Truncate", "Call", "Execute"):
        cls = getattr(exp, name, None)
        if cls is not None:
            forbidden = forbidden + (cls,)

    for statement in statements:
        if not isinstance(statement, (exp.Select, exp.Union, exp.With, exp.Subquery)):
            raise ValueError(f"Unsupported SQL statement type: {type(statement).__name__}")
        for node in statement.walk():
            if isinstance(node, forbidden):
                raise ValueError(f"Forbidden SQL operation detected: {type(node).__name__}")

    return True


__all__ = ["validate_sql"]
