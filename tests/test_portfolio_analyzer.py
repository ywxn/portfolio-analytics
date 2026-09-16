import pandas as pd

from portfolio_analytics import PortfolioAnalyzer


def test_portfolio_analyzer_query_returns_structure(tmp_path, monkeypatch):
    workbook_path = tmp_path / "portfolio.xlsx"
    with pd.ExcelWriter(workbook_path, engine="openpyxl") as writer:
        pd.DataFrame(
            {
                "portfolio_name": ["Alpha", "Beta"],
                "market_value": [120000.0, 95000.0],
            }
        ).to_excel(writer, sheet_name="Portfolio", index=False)

    monkeypatch.setattr(
        "portfolio_analytics.llm.generate_sql",
        lambda question, schema, metadata: "SELECT portfolio_name, market_value FROM portfolio ORDER BY market_value DESC",
    )

    analyzer = PortfolioAnalyzer(excel_path=str(workbook_path))
    result = analyzer.query("Show portfolio values")

    assert result.sql.startswith("SELECT")
    assert result.data is not None
    assert "portfolio_name" in result.data.columns
    assert result.question == "Show portfolio values"
