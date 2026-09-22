import pandas as pd

from demo import (
    aggregate_dataframe,
    limit_dataframe,
    run_dataframe_operations,
    sort_dataframe,
)
from portfolio_analytics.analytics import pivot, summarize_by, top_n


def test_summarize_by_and_top_n():
    df = pd.DataFrame(
        {
            "sector": ["Technology", "Technology", "Finance"],
            "market_value": [120.0, 80.0, 200.0],
        }
    )

    summary = summarize_by(df, by="sector", metric="market_value", aggfunc="sum")
    assert summary["market_value"].sum() == 400.0

    top = top_n(df, column="market_value", n=1)
    assert top.iloc[0]["market_value"] == 200.0


def test_pivot_handles_multidimensional_result():
    df = pd.DataFrame(
        {
            "sector": ["Technology", "Technology", "Finance"],
            "geography": ["US", "EU", "US"],
            "market_value": [100.0, 50.0, 200.0],
        }
    )

    result = pivot(
        df, index="sector", columns="geography", values="market_value", aggfunc="sum"
    )
    assert "US" in result.columns
    assert "Technology" in result.index


def test_demo_dataframe_operations_can_be_chained():
    df = pd.DataFrame(
        {
            "sector": ["Technology", "Finance", "Technology"],
            "market_value": [120.0, 200.0, 80.0],
        }
    )

    aggregated = aggregate_dataframe(
        df, by="sector", metric="market_value", aggfunc="sum"
    )
    assert aggregated.to_dict("records") == [
        {"sector": "Technology", "market_value": 200.0},
        {"sector": "Finance", "market_value": 200.0},
    ]

    sorted_df = sort_dataframe(aggregated, column="market_value", ascending=False)
    assert sorted_df["market_value"].tolist() == [200.0, 200.0]

    limited = limit_dataframe(sorted_df, rows=1)
    assert len(limited) == 1
    assert limited.iloc[0]["market_value"] == 200.0


def test_run_dataframe_operations_supports_chained_menu_flow(monkeypatch):
    df = pd.DataFrame(
        {
            "sector": ["Technology", "Finance", "Technology"],
            "market_value": [120.0, 200.0, 80.0],
        }
    )
    user_inputs = iter(
        ["1", "sector", "market_value", "sum", "2", "market_value", "n", "3", "1", "6"]
    )
    monkeypatch.setattr("builtins.input", lambda prompt="": next(user_inputs))

    result = run_dataframe_operations(None, df)
    assert result["market_value"].tolist() == [200.0]
