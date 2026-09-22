import pandas as pd

from portfolio_analytics import AnalysisEngine


def test_analysis_engine_supports_multidimensional_breakdown(monkeypatch):
    monkeypatch.setattr(
        "portfolio_analytics.llm.generate_analysis_plan",
        lambda question, columns, metadata: {
            "dimensions": ["sector", "geography"],
            "metric": "market_value",
            "aggregation": "sum",
            "pivot_index": [],
            "pivot_columns": [],
            "limit": None,
            "filters": {},
        },
    )
    data = pd.DataFrame(
        {
            "sector": ["Technology", "Technology", "Finance"],
            "geography": ["US", "EU", "US"],
            "market_value": [100, 50, 200],
        }
    )

    result, plan = AnalysisEngine().run(
        data, "Show market value by sector and geography"
    )

    assert plan.dimensions == ["sector", "geography"]
    assert result["market_value"].sum() == 350


def test_analysis_engine_supports_pivot(monkeypatch):
    monkeypatch.setattr(
        "portfolio_analytics.llm.generate_analysis_plan",
        lambda question, columns, metadata: {
            "dimensions": ["sector", "geography"],
            "metric": "market_value",
            "aggregation": "sum",
            "pivot_index": ["sector"],
            "pivot_columns": ["geography"],
            "limit": None,
            "filters": {},
        },
    )
    data = pd.DataFrame(
        {
            "sector": ["Technology", "Technology"],
            "geography": ["US", "EU"],
            "market_value": [100, 50],
        }
    )

    result, _ = AnalysisEngine().run(data, "Pivot market value by sector and geography")

    assert "US" in result.columns
    assert "EU" in result.columns
