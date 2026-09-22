from portfolio_analytics import PortfolioAnalyzer

if __name__ == "__main__":
    analyzer = PortfolioAnalyzer()
    result = analyzer.query("What is the total market value by sector?")
    print(result.sql)
    print(result.data.head())
