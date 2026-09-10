"""Sales field records, status enum, and validators (never invent values)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from .schema import FIELD_NAMES, OWNER_REQUIRED_FIELDS


class FieldStatus(str, Enum):
    GROUNDED_OWNER_CONFIRMED = "GROUNDED_OWNER_CONFIRMED"
    GROUNDED_FROM_CATALOG = "GROUNDED_FROM_CATALOG"
    OWNER_REQUIRED = "OWNER_REQUIRED"
    INVALID = "INVALID"
    CONFLICT = "CONFLICT"
    NOT_APPLICABLE = "NOT_APPLICABLE"


def _utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class FieldRecord:
    field_name: str
    value: Any = None
    unit: Optional[str] = None
    currency: Optional[str] = None
    status: str = FieldStatus.OWNER_REQUIRED.value
    source: Optional[str] = None
    source_reference: Optional[str] = None
    owner_confirmed: bool = False
    confirmed_at: Optional[str] = None
    confidence: Optional[float] = None
    validation_errors: list = field(default_factory=list)
    updated_at: Optional[str] = None
    note: Optional[str] = None
    owner_answer: Optional[str] = None

    def to_dict(self) -> dict:
        d = asdict(self)
        out = {}
        for k, v in d.items():
            if k == "value":
                out[k] = v
            elif v is None:
                continue
            elif k == "validation_errors" and not v:
                continue
            else:
                out[k] = v
        # Compatibility alias used in prior cycle artifacts
        out["field"] = self.field_name
        return out

    @classmethod
    def from_dict(cls, data: dict) -> "FieldRecord":
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        kwargs = {k: v for k, v in data.items() if k in known}
        if "field" in data and "field_name" not in kwargs:
            kwargs["field_name"] = data["field"]
        return cls(**kwargs)


def validate_price_aud(value: Any, *, unit: Optional[str] = None, currency: Optional[str] = None, **_kwargs: Any) -> list[str]:
    errors: list[str] = []
    if value is None:
        return errors
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        errors.append("price_aud_must_be_number")
        return errors
    if value < 0:
        errors.append("price_aud_negative_rejected")
    cur = (currency or unit or "AUD").upper()
    if cur not in {"AUD", "AU$", "A$"}:
        errors.append("price_aud_currency_must_be_aud")
    return errors


def validate_stock_qty(value: Any, **_kwargs: Any) -> list[str]:
    errors: list[str] = []
    if value is None:
        return errors
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        errors.append("stock_qty_must_be_number")
        return errors
    if isinstance(value, float) and not value.is_integer():
        errors.append("stock_qty_fractional_rejected")
    if value < 0:
        errors.append("stock_qty_negative_rejected")
    return errors


def validate_delivery_options(value: Any, **_kwargs: Any) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, (str, list, dict)):
        return ["delivery_options_invalid_type"]
    return []


def validate_lead_time(value: Any, **_kwargs: Any) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, (str, dict, int, float)):
        return ["lead_time_invalid_type"]
    return []


def validate_sku(value: Any, **_kwargs: Any) -> list[str]:
    if value is None:
        return ["sku_missing"]
    if isinstance(value, dict):
        ids = value.get("product_ids") or value.get("ids")
        if not ids:
            return ["sku_product_ids_empty"]
        return []
    if isinstance(value, str) and value.strip():
        return []
    if isinstance(value, list) and value:
        return []
    return ["sku_invalid"]


def validate_weight_g(value: Any, *, unit: Optional[str] = None, **_kwargs: Any) -> list[str]:
    errors: list[str] = []
    if value is None:
        return errors
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return ["weight_g_must_be_number"]
    if value < 0:
        errors.append("weight_g_negative_rejected")
    u = (unit or "g").lower()
    if u not in {"g", "gram", "grams", "kg"}:
        errors.append("weight_g_unit_invalid")
    return errors


def validate_dimensions(value: Any, *, unit: Optional[str] = None, **_kwargs: Any) -> list[str]:
    errors: list[str] = []
    if value is None:
        return errors
    dim_unit = unit
    if isinstance(value, dict):
        dim_unit = dim_unit or value.get("unit")
        if not dim_unit:
            errors.append("dimensions_unit_required")
    elif isinstance(value, str):
        if unit is None and not any(tok in value.lower() for tok in ("cm", "mm", "m", "in")):
            errors.append("dimensions_unit_required")
    else:
        if not unit:
            errors.append("dimensions_unit_required")
    return errors


def validate_components_cost(value: Any, **_kwargs: Any) -> list[str]:
    errors: list[str] = []
    if value is None:
        return errors
    if isinstance(value, bool) or not isinstance(value, (int, float, dict)):
        return ["components_cost_invalid_type"]
    if isinstance(value, (int, float)) and value < 0:
        errors.append("components_cost_negative_rejected")
    return errors


def validate_license_clearance(
    value: Any,
    *,
    evidence: Any = None,
    owner_confirmed: bool = False,
    **_kwargs: Any,
) -> list[str]:
    errors: list[str] = []
    if value is None and evidence is None:
        return errors
    has_evidence = bool(evidence) or (
        isinstance(value, dict) and value.get("evidence")
    )
    if owner_confirmed and not has_evidence:
        # Allow scan-only dict without formal evidence to remain OWNER_REQUIRED path
        # but reject final confirm without evidence
        errors.append("license_clearance_evidence_required_for_final_confirm")
    return errors


VALIDATORS = {
    "price_aud": validate_price_aud,
    "stock_qty": validate_stock_qty,
    "delivery_options": validate_delivery_options,
    "lead_time": validate_lead_time,
    "sku": validate_sku,
    "weight_g": validate_weight_g,
    "dimensions": validate_dimensions,
    "components_cost": validate_components_cost,
    "license_clearance": validate_license_clearance,
}


def validate_field(field_name: str, value: Any, **kwargs: Any) -> list[str]:
    if field_name not in VALIDATORS:
        return [f"unknown_field:{field_name}"]
    return VALIDATORS[field_name](value, **kwargs)


def apply_validation(record: FieldRecord) -> FieldRecord:
    """Validate and update status. Null stays OWNER_REQUIRED; never invent values."""
    kwargs = {
        "unit": record.unit,
        "currency": record.currency,
        "owner_confirmed": record.owner_confirmed,
        "evidence": None,
    }
    if isinstance(record.value, dict):
        kwargs["evidence"] = record.value.get("evidence") or record.source_reference
    errors = validate_field(record.field_name, record.value, **kwargs)
    record.validation_errors = list(errors)
    record.updated_at = record.updated_at or _utcnow()
    if errors:
        if record.value is not None or record.field_name == "sku":
            record.status = FieldStatus.INVALID.value
        return record
    if record.value is None and record.field_name in OWNER_REQUIRED_FIELDS:
        record.status = FieldStatus.OWNER_REQUIRED.value
        return record
    return record


def owner_required_null(field_name: str, source: str = "ABSENT") -> FieldRecord:
    return apply_validation(
        FieldRecord(
            field_name=field_name,
            value=None,
            status=FieldStatus.OWNER_REQUIRED.value,
            source=source,
            updated_at=_utcnow(),
        )
    )


def preserve_sku_owner_confirmed(prior_sku_row: dict) -> FieldRecord:
    """Preserve GROUNDED_OWNER_CONFIRMED YES_USE_PRODUCT_ID from prior cycle."""
    payload = dict(prior_sku_row)
    if "field_name" not in payload:
        payload["field_name"] = payload.get("field", "sku")
    rec = FieldRecord.from_dict(payload)
    rec.field_name = "sku"
    rec.status = FieldStatus.GROUNDED_OWNER_CONFIRMED.value
    rec.owner_confirmed = True
    if not rec.owner_answer:
        rec.owner_answer = prior_sku_row.get("owner_answer") or "YES_USE_PRODUCT_ID"
    if not rec.confirmed_at:
        rec.confirmed_at = prior_sku_row.get("owner_answered_at") or prior_sku_row.get("confirmed_at")
    if not rec.note:
        rec.note = prior_sku_row.get("note")
    rec.updated_at = _utcnow()
    return apply_validation(rec)


def build_cycle4_sales_fields(prior_sell_fields: list[dict]) -> list[FieldRecord]:
    by_name = {}
    for row in prior_sell_fields:
        name = row.get("field") or row.get("field_name")
        if name:
            by_name[name] = row
    out: list[FieldRecord] = []
    for name in FIELD_NAMES:
        if name == "sku":
            if "sku" not in by_name:
                raise ValueError("sku_missing_from_prior")
            out.append(preserve_sku_owner_confirmed(by_name["sku"]))
            continue
        prior = by_name.get(name, {})
        out.append(
            owner_required_null(
                name,
                source=prior.get("source") or "ABSENT; awaiting owner input",
            )
        )
    return out
