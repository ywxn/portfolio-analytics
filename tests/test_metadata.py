from portfolio_analytics.metadata_catalog import format_metadata_for_prompt


def test_format_metadata_for_prompt_keeps_one_table_detailed():
    metadata = {
        "tables": {
            "portfolio": {
                "description": "Bond portfolio holdings",
                "columns": ["issuer", "ytm", "purchase_value"],
                "dimensions": {"issuer": {"description": "Bond issuer"}},
                "metrics": {
                    "ytm": {"description": "Yield to maturity"},
                    "purchase_value": {"description": "Purchase amount"},
                },
                "synonyms": {"yield": "ytm"},
            },
            "unrelated": {
                "description": "Unrelated data",
                "columns": ["id"],
                "dimensions": {"region": {"description": "Region"}},
                "metrics": {"count": {"description": "Count"}},
            },
        }
    }

    prompt_metadata = format_metadata_for_prompt(
        metadata, "What is the average yield?", ["portfolio", "unrelated"]
    )

    assert '"ytm"' in prompt_metadata
    assert '"available_metrics"' in prompt_metadata
    assert '"metrics":{"count"' not in prompt_metadata


def test_format_metadata_for_prompt_respects_budget():
    metadata = {
        "tables": {
            "portfolio": {
                "description": "A very long description " * 100,
                "columns": ["issuer", "ytm"],
                "dimensions": {"issuer": {"description": "Issuer " * 100}},
                "metrics": {"ytm": {"description": "Yield " * 100}},
                "synonyms": {"yield": "ytm"},
            }
        }
    }

    prompt_metadata = format_metadata_for_prompt(metadata, "yield", max_chars=150)

    assert len(prompt_metadata) <= 150