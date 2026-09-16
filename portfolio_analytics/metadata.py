from __future__ import annotations

from typing import Any

from config import load_metadata as _load_metadata


def load_metadata(path: str | None = None) -> dict[str, Any]:
    return _load_metadata(path)


def get_metric(metadata: dict[str, Any], name: str) -> dict[str, Any] | None:
    if not isinstance(metadata, dict):
        return None
    metrics = metadata.get("metrics", {})
    if isinstance(metrics, dict):
        return metrics.get(name)
    return None


def get_dimension(metadata: dict[str, Any], name: str) -> dict[str, Any] | None:
    if not isinstance(metadata, dict):
        return None
    dimensions = metadata.get("dimensions", {})
    if isinstance(dimensions, dict):
        return dimensions.get(name)
    return None


def get_synonyms(metadata: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(metadata, dict):
        return {}
    synonyms = metadata.get("synonyms", {})
    return synonyms if isinstance(synonyms, dict) else {}


__all__ = ["load_metadata", "get_metric", "get_dimension", "get_synonyms"]
