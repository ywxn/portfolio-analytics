from __future__ import annotations

import argparse

from analysis import blog_query
from config import load_metadata, validate_runtime_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a natural-language portfolio analytics query."
    )
    parser.add_argument(
        "question", nargs="*", help="The question to convert into SQL and execute."
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    question = " ".join(args.question).strip()
    if not question:
        question = "What is the total value by portfolio name?"

    config = validate_runtime_config()
    metadata = load_metadata()
    outcome = blog_query(question, metadata=metadata)
    print("SQL:")
    print(outcome["sql"])
    print("\nResults:")
    print(outcome["data"].to_string(index=False))
    print(f"\nRuntime config: {config}")


if __name__ == "__main__":
    main()
