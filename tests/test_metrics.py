import pandas as pd

from portfolio_analytics.metrics import difference, growth, percent_of_total, ratio


def test_percent_of_total_and_ratio():
    df = pd.DataFrame({"sector": ["A", "B"], "market_value": [100.0, 100.0]})
    pct = percent_of_total(df, value_column="market_value", group_by="sector")
    assert pct["market_value_pct"].sum() == 200.0
    assert ratio(100.0, 50.0) == 2.0


def test_difference_and_growth():
    assert difference(200.0, 100.0) == 100.0
    assert growth(100.0, 200.0) == 1.0
