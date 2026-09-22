import pytest

from validator import validate_sql


def test_validate_sql_allows_select_with_union_and_cte():
    assert validate_sql("WITH totals AS (SELECT 1 AS id) SELECT * FROM totals") is True
    assert validate_sql("SELECT * FROM portfolio UNION SELECT * FROM portfolio") is True


def test_validate_sql_rejects_mutation_and_non_select_statements():
    with pytest.raises(ValueError):
        validate_sql("DELETE FROM portfolio")
    with pytest.raises(ValueError):
        validate_sql("DROP TABLE portfolio")
    with pytest.raises(ValueError):
        validate_sql("ALTER TABLE portfolio ADD COLUMN extra TEXT")


def test_validate_sql_rejects_multiple_statements_when_any_is_destructive():
    with pytest.raises(ValueError):
        validate_sql("SELECT * FROM portfolio; DROP TABLE portfolio")


def test_validate_sql_accepts_read_only_ctes_and_unions():
    assert (
        validate_sql(
            "WITH totals AS (SELECT market_value FROM portfolio) SELECT * FROM totals UNION SELECT * FROM totals"
        )
        is True
    )
