from __future__ import annotations

from typing import Any

from portfolio_analytics import PortfolioAnalyzer


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


def _run_query(analyzer: PortfolioAnalyzer) -> None:
    question = _prompt_required("Natural-language question: ")
    result = analyzer.query(question)
    print("\nGenerated SQL:")
    print(result.sql)
    print("\nResults:")
    print(result.data.to_string(index=False))

    while True:
        analyze_results = input(
            "\nRun analysis on these results? [y/N]: "
        ).strip().lower()
        if analyze_results in {"y", "yes"}:
            break
        if analyze_results in {"n", "no"}:
            return
        print("Please enter y, yes, n, or no.")

    analysis_question = input(
        "Analysis question (press Enter to reuse the original question): "
    ).strip() or question
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

    raw_columns = input(
        "Columns (comma-separated, or press Enter for all): "
    ).strip()
    columns = [column.strip() for column in raw_columns.split(",") if column.strip()]
    filters = _prompt_filters()
    selected = analyzer.select_data(table, columns=columns or None, filters=filters)

    print("\nSelected data preview:")
    print(selected.head(10).to_string(index=False))
    question = _prompt_required("Analysis question: ")
    analyzed, plan = analyzer.analyze(question, selected)

    print("\nAnalysis plan:")
    print(plan)
    print("\nAnalysis result:")
    print(analyzed.to_string(index=False))


def main() -> None:
    analyzer = PortfolioAnalyzer()
    print("Portfolio Analytics Demo")
    print("Workbook path is controlled by PORTFOLIO_EXCEL_PATH.")

    while True:
        print("\nChoose an operation:")
        print("  1. Ask a natural-language question, then optionally analyze the results")
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
