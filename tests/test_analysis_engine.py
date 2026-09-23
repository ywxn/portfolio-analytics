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


def test_analysis_engine_returns_highest_group_for_top_question(monkeypatch):
    monkeypatch.setattr(
        "portfolio_analytics.llm.generate_analysis_plan",
        lambda question, columns, metadata: {
            "dimensions": ["state"],
            "metric": "portfolio_value",
            "aggregation": "sum",
            "pivot_index": [],
            "pivot_columns": [],
            "limit": 1,
            "filters": {},
        },
    )
    data = pd.DataFrame(
        {
            "state": ["Andhra Pradesh", "Telangana", "Telangana"],
            "portfolio_value": [349, 900, 652],
        }
    )

    result, _ = AnalysisEngine().run(data, "What is the top state by value?")

    assert result.to_dict("records") == [
        {"state": "Telangana", "portfolio_value": 1552}
    ]
