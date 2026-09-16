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
