from __future__ import annotations

import argparse
from typing import Any

from portfolio_analytics import PortfolioAnalyzer
from portfolio_analytics.config import validate_runtime_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a natural-language portfolio analytics query."
    )
    parser.add_argument(
        "question", nargs="*", help="The question to convert into SQL and execute."
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Select a data slice and run dynamic dataframe analysis.",
    )
    parser.add_argument(
        "--list-tables",
        action="store_true",
        help="List selectable tables and columns, then exit.",
    )
    parser.add_argument("--table", help="Table or workbook sheet to select from.")
    parser.add_argument(
        "--columns",
        help="Comma-separated columns to select; defaults to every column.",
    )
    parser.add_argument(
        "--where",
        action="append",
        default=[],
        metavar="COLUMN=VALUE",
        help="Filter the selected data. Repeat for multiple filters.",
    )
    return parser.parse_args()


def _parse_filters(raw_filters: list[str]) -> dict[str, Any]:
    filters: dict[str, Any] = {}
    for expression in raw_filters:
        if "=" not in expression:
            raise ValueError(f"Filter must use COLUMN=VALUE syntax: {expression}")
        column, value = expression.split("=", 1)
        column = column.strip()
        value = value.strip()
        if not column or not value:
            raise ValueError(
                f"Filter must include both a column and value: {expression}"
            )
        filters[column] = value
    return filters


def preview(analyzer: PortfolioAnalyzer, args: argparse.Namespace) -> None:
    if not args.table:
        raise ValueError("--table is required with --preview.")
    columns = (
        [column.strip() for column in args.columns.split(",") if column.strip()]
        if args.columns
        else None
    )
    filters = _parse_filters(args.where)
    selected = analyzer.select_data(args.table, columns=columns, filters=filters)
    question = " ".join(args.question).strip()
    if not question:
        raise ValueError("Provide an analysis question after the preview options.")

    analyzed, plan = analyzer.analyze(question, selected)
    print("Selected data:")
    print(selected.head(10).to_string(index=False))
    print("\nAnalysis plan:")
    print(plan)
    print("\nAnalysis result:")
    print(analyzed.to_string(index=False))


def main() -> None:
    args = parse_args()
    config = validate_runtime_config()
    analyzer = PortfolioAnalyzer()
    if args.list_tables:
        for table, columns in analyzer.list_tables().items():
            print(f"{table}: {', '.join(columns)}")
        return
    if args.preview:
        preview(analyzer, args)
        return

    question = " ".join(args.question).strip()
    if not question:
        question = "What is the total value by portfolio name?"

    result = analyzer.query(question)
    print("SQL:")
    print(result.sql)
    print("\nResults:")
    print(result.data.to_string(index=False))
    print(f"\nRuntime config: {config}")


if __name__ == "__main__":
    main()
