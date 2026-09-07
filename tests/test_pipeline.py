import pandas as pd
import pytest

from analysis import blog_query, run_pipeline
from llm import generate_sql
from validator import validate_sql


def test_validate_sql_allows_select_only():
    assert validate_sql("SELECT * FROM portfolio") is True


def test_validate_sql_rejects_mutation():
    with pytest.raises(ValueError):
        validate_sql("INSERT INTO portfolio VALUES (1, 'A')")

    # TODO: Add coverage for SELECT-only enforcement, joins, UNION/CTEs/subqueries,
    # unknown tables/columns, and SQL injection-shaped inputs.


def test_generate_sql_requires_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr("llm.OPENAI_API_KEY", None)
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        generate_sql("Show portfolio values", "Table: portfolio", "")

    # TODO: Mock successful generation and correction retries, including API errors,
    # invalid SQL, database failures, bounded retries, and clear error responses.


def test_run_pipeline_reads_excel_and_returns_sql_and_dataframe(tmp_path, monkeypatch):
    workbook_path = tmp_path / "portfolio.xlsx"
    with pd.ExcelWriter(workbook_path, engine="openpyxl") as writer:
        pd.DataFrame(
            {
                "portfolio_name": ["Alpha", "Beta"],
                "market_value": [120000.0, 95000.0],
            }
        ).to_excel(writer, sheet_name="Portfolio", index=False)

    monkeypatch.setattr(
        "analysis.generate_sql",
        lambda question, schema, metadata: "SELECT portfolio_name, market_value FROM portfolio ORDER BY market_value DESC",
    )

    result = blog_query(
        "Show portfolio values",
        metadata={"business_metrics": {"market_value": "Current value"}},
        excel_path=str(workbook_path),
    )

    assert result["sql"].startswith("SELECT")
    assert isinstance(result["data"], pd.DataFrame)
    assert result["data"]["portfolio_name"].tolist() == ["Alpha", "Beta"]


def test_run_pipeline_returns_dataframe_from_excel(tmp_path, monkeypatch):
    workbook_path = tmp_path / "portfolio.xlsx"
    with pd.ExcelWriter(workbook_path, engine="openpyxl") as writer:
        pd.DataFrame(
            {"portfolio_name": ["Alpha"], "market_value": [120000.0]}
        ).to_excel(writer, sheet_name="portfolio", index=False)

    monkeypatch.setattr(
        "analysis.generate_sql",
        lambda question, schema, metadata: "SELECT portfolio_name, market_value FROM portfolio",
    )
    question = "What is the total value by portfolio name?"
    result = run_pipeline(question, excel_path=str(workbook_path))
    assert isinstance(result, pd.DataFrame)
    assert not result.empty
    assert "portfolio_name" in result.columns


# TODO: Add focused aggregation, pivot, ranking, multidimensional, derived
# metric, empty-result, schema-discovery, and end-to-end regression tests.
