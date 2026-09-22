from __future__ import annotations

from typing import Any

import pandas as pd

from portfolio_analytics import PortfolioAnalyzer


def aggregate_dataframe(
    df: pd.DataFrame,
    by: str | list[str] | None = None,
    metric: str | None = None,
    aggfunc: str = "sum",
) -> pd.DataFrame:
    """Aggregate a dataframe by one or more grouping columns."""
    if metric is None:
        raise ValueError("A metric column is required for aggregation.")
    if metric not in df.columns:
        raise ValueError(f"Unknown metric column: {metric}")

    if by is None:
        return pd.DataFrame({metric: [df[metric].agg(aggfunc)]})

    group_columns = [by] if isinstance(by, str) else list(by)
    unknown = [column for column in group_columns if column not in df.columns]
    if unknown:
        raise ValueError(f"Unknown group columns: {', '.join(unknown)}")
    return (
        df.groupby(group_columns, dropna=False, sort=False)[metric]
        .agg(aggfunc)
        .reset_index()
    )


def sort_dataframe(
    df: pd.DataFrame, column: str, ascending: bool = False
) -> pd.DataFrame:
    """Sort a dataframe by a single column."""
    if column not in df.columns:
        raise ValueError(f"Unknown sort column: {column}")
    return df.sort_values(by=column, ascending=ascending).reset_index(drop=True)


def limit_dataframe(df: pd.DataFrame, rows: int = 10) -> pd.DataFrame:
    """Limit rows shown in the dataframe."""
    if rows < 1:
        raise ValueError("Row limit must be at least 1.")
    return df.head(rows).copy()


def _print_tables(analyzer: PortfolioAnalyzer) -> dict[str, list[str]]:
    tables = analyzer.list_tables()
    print("\nAvailable tables:")
    for table, columns in tables.items():
        print(f"  {table}: {', '.join(columns)}")
    return tables


def _prompt_required(message: str) -> str:
    while True:
        value = input(message).strip()
        if value:
            return value
        print("Please enter a value.")


def _prompt_filters() -> dict[str, Any]:
    filters: dict[str, Any] = {}
    print("Enter filters as COLUMN=VALUE, one per line. Press Enter when finished.")
    while True:
        expression = input("  Filter: ").strip()
        if not expression:
            return filters
        if "=" not in expression:
            print("Use COLUMN=VALUE syntax.")
            continue
        column, value = expression.split("=", 1)
        column = column.strip()
        value = value.strip()
        if not column or not value:
            print("Both the column and value are required.")
            continue
        filters[column] = value


def run_dataframe_operations(
    analyzer: PortfolioAnalyzer | None,
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Allow a user to chain dataframe transforms and optional AI analysis."""
    current = df.copy()
    while True:
        print("\nCurrent dataframe operations:")
        print("  1. Aggregate by column(s)")
        print("  2. Sort by column")
        print("  3. Limit displayed rows")
        print("  4. Run AI analysis on the current data")
        print("  5. Show current dataframe")
        print("  6. Done")
        choice = input("Choice: ").strip().lower()

        try:
            if choice == "1":
                group_input = input(
                    "Group by columns (comma-separated, or press Enter for no group): "
                ).strip()
                group_columns = [
                    column.strip()
                    for column in group_input.split(",")
                    if column.strip()
                ] or None
                metric = input("Metric column to aggregate: ").strip()
                aggfunc = input("Aggregation function [sum]: ").strip() or "sum"
                current = aggregate_dataframe(
                    current, by=group_columns, metric=metric, aggfunc=aggfunc
                )
                print("\nAggregated data:")
                print(current.to_string(index=False))
            elif choice == "2":
                column = input("Sort by column: ").strip()
                ascending = input("Ascending? [y/N]: ").strip().lower() in {"y", "yes"}
                current = sort_dataframe(current, column=column, ascending=ascending)
                print("\nSorted data:")
                print(current.to_string(index=False))
            elif choice == "3":
                rows = int(input("Maximum rows to show [10]: ").strip() or "10")
                current = limit_dataframe(current, rows=rows)
                print("\nLimited data:")
                print(current.to_string(index=False))
            elif choice == "4":
                if analyzer is None:
                    raise ValueError(
                        "AI analysis requires a PortfolioAnalyzer instance."
                    )
                question = input("Analysis question: ").strip()
                if not question:
                    raise ValueError("An analysis question is required.")
                analyzed, plan = analyzer.analyze(question, current)
                print("\nAnalysis plan:")
                print(plan)
                print("\nAnalysis result:")
                print(analyzed.to_string(index=False))
            elif choice == "5":
                print("\nCurrent data:")
                print(current.to_string(index=False))
            elif choice in {"6", "done", "d"}:
                return current
            else:
                print("Choose 1, 2, 3, 4, 5, or 6.")
        except (RuntimeError, ValueError, OSError, TypeError) as exc:
            print(f"\nError: {exc}")


def _run_query(analyzer: PortfolioAnalyzer) -> None:
    question = _prompt_required("Natural-language question: ")
    result = analyzer.query(question)
    print("\nGenerated SQL:")
    print(result.sql)
    print("\nResults:")
    print(result.data.to_string(index=False))

    while True:
        analyze_results = (
            input("\nApply dataframe operations to these results? [y/N]: ")
            .strip()
            .lower()
        )
        if analyze_results in {"y", "yes"}:
            result.data = run_dataframe_operations(analyzer, result.data)
            print("\nCurrent data after operations:")
            print(result.data.to_string(index=False))
            return
        if analyze_results in {"n", "no"}:
            break
        print("Please enter y, yes, n, or no.")

    while True:
        analyze_results = (
            input("\nRun AI analysis on these results? [y/N]: ").strip().lower()
        )
        if analyze_results in {"y", "yes"}:
            break
        if analyze_results in {"n", "no"}:
            return
        print("Please enter y, yes, n, or no.")

    analysis_question = (
        input(
            "Analysis question (press Enter to reuse the original question): "
        ).strip()
        or question
    )
    analyzed, plan = analyzer.analyze(analysis_question, result.data)
    print("\nAnalysis plan:")
    print(plan)
    print("\nAnalysis result:")
    print(analyzed.to_string(index=False))


def _run_analysis(analyzer: PortfolioAnalyzer) -> None:
    tables = _print_tables(analyzer)
    table = _prompt_required("Table: ")
    if table not in tables:
        raise ValueError(f"Unknown table: {table}")

    raw_columns = input("Columns (comma-separated, or press Enter for all): ").strip()
    columns = [column.strip() for column in raw_columns.split(",") if column.strip()]
    filters = _prompt_filters()
    selected = analyzer.select_data(table, columns=columns or None, filters=filters)

    print("\nSelected data preview:")
    print(selected.head(10).to_string(index=False))
    current = run_dataframe_operations(analyzer, selected)
    print("\nFinal current data:")
    print(current.to_string(index=False))


def main() -> None:
    analyzer = PortfolioAnalyzer()
    print("Portfolio Analytics Demo")
    print("Workbook path is controlled by PORTFOLIO_EXCEL_PATH.")

    while True:
        print("\nChoose an operation:")
        print(
            "  1. Ask a natural-language question, then optionally analyze the results"
        )
        print("  2. Select data and run multidimensional analysis")
        print("  3. List tables and columns")
        print("  q. Quit")
        choice = input("Choice: ").strip().lower()

        try:
            if choice == "1":
                _run_query(analyzer)
            elif choice == "2":
                _run_analysis(analyzer)
            elif choice == "3":
                _print_tables(analyzer)
            elif choice in {"q", "quit", "exit"}:
                print("Goodbye.")
                return
            else:
                print("Choose 1, 2, 3, or q.")
        except (RuntimeError, ValueError, OSError) as exc:
            print(f"\nError: {exc}")


if __name__ == "__main__":
    main()
