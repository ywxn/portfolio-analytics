from sqlalchemy import create_engine, text

from portfolio_analytics.schema import format_schema_for_prompt, get_schema


def test_get_schema_discovers_primary_keys_and_types():
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        connection.execute(
            text(
                "CREATE TABLE portfolio (id INTEGER PRIMARY KEY, portfolio_name TEXT, market_value REAL)"
            )
        )
        connection.execute(
            text(
                "CREATE TABLE holdings (id INTEGER PRIMARY KEY, portfolio_id INTEGER, market_value REAL, FOREIGN KEY (portfolio_id) REFERENCES portfolio(id))"
            )
        )

    schema = get_schema(engine)
    assert "portfolio" in schema
    assert schema["portfolio"]["columns"] == ["id", "portfolio_name", "market_value"]
    assert schema["portfolio"]["primary_keys"] == ["id"]
    assert schema["portfolio"]["column_types"]["market_value"] in {"REAL", "FLOAT"}
    assert schema["holdings"]["foreign_keys"]

    prompt_text = format_schema_for_prompt(schema)
    assert "Table: portfolio" in prompt_text
    assert "Primary keys: id" in prompt_text
