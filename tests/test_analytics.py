import pandas as pd

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

    result = pivot(df, index="sector", columns="geography", values="market_value", aggfunc="sum")
    assert "US" in result.columns
    assert "Technology" in result.index
