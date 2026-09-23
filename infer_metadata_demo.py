from __future__ import annotations

import argparse
from typing import Any

import pandas as pd
import yaml

from portfolio_analytics.config import get_database_url, get_excel_path
from portfolio_analytics.database import get_engine, load_excel_engine
from portfolio_analytics.metadata_inference import infer_metadata
from portfolio_analytics.schema import get_schema


def load_current_portfolio() -> tuple[dict[str, pd.DataFrame], dict[str, dict[str, Any]]]:
    """Load every table and its database schema from the current portfolio."""
    database_url = get_database_url()
    engine = get_engine(database_url) if database_url else load_excel_engine(get_excel_path())
    try:
        schema = get_schema(engine)
        tables = {
            table_name: pd.read_sql_table(table_name, engine)
            for table_name in schema
        }
        return tables, schema
    finally:
        engine.dispose()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Infer YAML metadata from the currently configured portfolio."
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=5,
        help="Rows sampled from each table for LLM inference (default: 5).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    tables, schema = load_current_portfolio()
    metadata = infer_metadata(
        tables,
        sample_size=args.sample_size,
        schema=schema,
    )
    print(yaml.safe_dump(metadata, sort_keys=False, allow_unicode=False))


if __name__ == "__main__":
    main()
