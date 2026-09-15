"""Catalog loaders (utf-8 / utf-8-sig) and product_id indexing."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional


class CatalogError(ValueError):
    pass


def load_catalog_bytes(path: str | Path) -> bytes:
    return Path(path).read_bytes()


def decode_catalog_text(raw: bytes) -> str:
    """Prefer utf-8-sig (strips BOM); fall back to utf-8."""
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return raw.decode("utf-8")


def load_catalog(path: str | Path) -> dict[str, Any]:
    raw = load_catalog_bytes(path)
    text = decode_catalog_text(raw)
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise CatalogError(f"malformed_catalog_json:{exc}") from exc
    if not isinstance(data, dict):
        raise CatalogError("catalog_root_not_object")
    if "products" not in data or not isinstance(data["products"], list):
        raise CatalogError("catalog_products_missing")
    return data


def index_by_product_id(catalog: dict[str, Any]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for item in catalog.get("products", []):
        if not isinstance(item, dict):
            continue
        pid = item.get("product_id")
        if not pid:
            continue
        index[str(pid)] = item
    return index


def filter_family(catalog: dict[str, Any], family: str = "F1_floral") -> list[dict[str, Any]]:
    return [
        p
        for p in catalog.get("products", [])
        if isinstance(p, dict) and p.get("family") == family
    ]


def find_product(catalog: dict[str, Any], product_id: str) -> Optional[dict[str, Any]]:
    return index_by_product_id(catalog).get(product_id)


def family_product_ids(catalog: dict[str, Any], family: str = "F1_floral") -> list[str]:
    return [p["product_id"] for p in filter_family(catalog, family) if p.get("product_id")]
