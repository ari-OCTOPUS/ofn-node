"""Schema version constants for Ziman sales fields and cycle outcomes."""

from __future__ import annotations

SALES_FIELDS_SCHEMA = "ziman_sales_fields.v1"
OUTCOME_SCHEMA = "ziman_internal_cycle_outcome.v1"
SCHEMA_VERSION = SALES_FIELDS_SCHEMA

KNOWN_SCHEMAS = frozenset({SALES_FIELDS_SCHEMA, OUTCOME_SCHEMA})

FIELD_NAMES = (
    "price_aud",
    "stock_qty",
    "delivery_options",
    "lead_time",
    "sku",
    "weight_g",
    "dimensions",
    "components_cost",
    "license_clearance",
)

OWNER_REQUIRED_FIELDS = (
    "price_aud",
    "stock_qty",
    "delivery_options",
    "lead_time",
    "weight_g",
    "dimensions",
    "components_cost",
    "license_clearance",
)


def migrate_schema(doc: dict) -> dict:
    """Load/migrate known schemas; unknown schema raises."""
    if not isinstance(doc, dict):
        raise ValueError("schema_doc_not_object")
    schema = doc.get("schema") or doc.get("schema_version")
    if schema is None:
        raise ValueError("schema_missing")
    if schema in KNOWN_SCHEMAS:
        return doc
    if str(schema).startswith("ziman_internal_cycle_outcome"):
        out = dict(doc)
        out["schema"] = OUTCOME_SCHEMA
        return out
    if str(schema).startswith("ziman_sales_fields"):
        out = dict(doc)
        out["schema"] = SALES_FIELDS_SCHEMA
        return out
    raise ValueError(f"unknown_schema:{schema}")
