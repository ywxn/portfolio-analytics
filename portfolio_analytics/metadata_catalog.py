from __future__ import annotations

import json
import re
from typing import Any, Mapping

from .config import DEFAULT_METADATA_MAX_CHARS, load_metadata


def get_metric(metadata: dict[str, Any], name: str) -> dict[str, Any] | None:
    if not isinstance(metadata, dict):
        return None
    metrics = metadata.get("metrics", {})
    return metrics.get(name) if isinstance(metrics, dict) else None


def get_dimension(metadata: dict[str, Any], name: str) -> dict[str, Any] | None:
    if not isinstance(metadata, dict):
        return None
    dimensions = metadata.get("dimensions", {})
    return dimensions.get(name) if isinstance(dimensions, dict) else None


def get_synonyms(metadata: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(metadata, dict):
        return {}
    synonyms = metadata.get("synonyms", {})
    return synonyms if isinstance(synonyms, dict) else {}


def format_metadata_for_prompt(
    metadata: Mapping[str, Any] | str | None,
    question: str = "",
    table_names: list[str] | None = None,
    max_chars: int = DEFAULT_METADATA_MAX_CHARS,
) -> str:
    if not metadata:
        return ""
    if isinstance(metadata, str):
        return metadata
    if not isinstance(metadata, Mapping):
        return ""
    metadata = dict(metadata)
    tables = metadata.get("tables")
    if not isinstance(tables, dict):
        return json.dumps(metadata, separators=(",", ":"), ensure_ascii=True)

    allowed_tables = set(table_names or tables)
    available = [name for name in tables if name in allowed_tables] or list(tables)
    terms = set(re.findall(r"[a-z0-9]+", question.lower())) - {
        "a", "an", "and", "by", "for", "from", "give", "is", "of", "show", "the", "to", "what"
    }

    def score(name: str, table: dict[str, Any]) -> int:
        searchable = " ".join([
            name.replace("_", " "),
            str(table.get("description", "")),
            " ".join(str(key) for key in table.get("metrics", {})),
            " ".join(str(key) for key in table.get("dimensions", {})),
        ]).lower()
        return len(terms & set(re.findall(r"[a-z0-9]+", searchable)))

    ranked = sorted(
        ((name, tables[name]) for name in available if isinstance(tables[name], dict)),
        key=lambda item: score(item[0], item[1]),
        reverse=True,
    )
    detailed_names = {name for name, table in ranked[:1] if score(name, table) > 0}
    if len(available) == 1:
        detailed_names = set(available)

    def relevant_entries(entries: Any) -> dict[str, Any]:
        if not isinstance(entries, dict):
            return {}
        matched = {
            key: value
            for key, value in entries.items()
            if not terms or terms & set(re.findall(r"[a-z0-9]+", f"{key} {value}".lower()))
        }
        return matched or entries

    compact_tables: dict[str, Any] = {}
    for name, table in ranked:
        compact: dict[str, Any] = {
            "description": table.get("description", ""),
            "available_columns": table.get("columns", []),
        }
        if name in detailed_names:
            compact.update({
                "dimensions": relevant_entries(table.get("dimensions")),
                "metrics": relevant_entries(table.get("metrics")),
                "synonyms": relevant_entries(table.get("synonyms")),
            })
        else:
            compact["available_metrics"] = list(table.get("metrics", {}))
            compact["available_dimensions"] = list(table.get("dimensions", {}))
        compact_tables[name] = compact

    payload = {"tables": compact_tables}
    serialized = json.dumps(payload, separators=(",", ":"), ensure_ascii=True)
    if len(serialized) <= max_chars:
        return serialized
    for table in compact_tables.values():
        table.pop("synonyms", None)
        for field_name in ("dimensions", "metrics"):
            entries = table.get(field_name, {})
            if isinstance(entries, dict):
                table[field_name] = {key: value.get("column", key) if isinstance(value, dict) else value for key, value in entries.items()}
    serialized = json.dumps(payload, separators=(",", ":"), ensure_ascii=True)
    if len(serialized) <= max_chars:
        return serialized
    for table in compact_tables.values():
        table.pop("description", None)
        table.pop("available_columns", None)
    serialized = json.dumps(payload, separators=(",", ":"), ensure_ascii=True)
    if len(serialized) <= max_chars:
        return serialized
    for table in compact_tables.values():
        for field_name in ("dimensions", "metrics", "available_metrics", "available_dimensions"):
            values = table.get(field_name)
            if isinstance(values, dict):
                table[field_name] = list(values)
    serialized = json.dumps(payload, separators=(",", ":"), ensure_ascii=True)
    return serialized if len(serialized) <= max_chars else json.dumps({"tables": {name: {} for name in compact_tables}}, separators=(",", ":"))


__all__ = ["load_metadata", "get_metric", "get_dimension", "get_synonyms", "format_metadata_for_prompt"]