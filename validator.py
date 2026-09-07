from __future__ import annotations

import sqlglot
from sqlglot import expressions as exp


def validate_sql(sql: str) -> bool:
    """Validate that SQL is syntactically valid and read-only."""

    # TODO: Require SELECT/UNION roots, validate referenced tables and columns
    # against discovered schema, and explicitly test CTE/subquery behavior.

    if not sql or not sql.strip():
        raise ValueError("SQL is empty.")

    try:
        statements = sqlglot.parse(sql.strip())
    except sqlglot.ParseError as e:
        raise ValueError(f"Invalid SQL syntax: {e}") from e

    if not statements:
        raise ValueError("SQL contains no statements.")

    # Operations that can modify data or database/schema state.
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

    for statement in statements:
        assert statement is not None
        for node in statement.walk():
            if isinstance(node, forbidden):
                raise ValueError(
                    f"Forbidden SQL operation detected: " f"{type(node).__name__}"
                )

    return True
