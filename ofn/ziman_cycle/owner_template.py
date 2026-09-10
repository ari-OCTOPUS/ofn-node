"""Machine + human owner input templates for the eight OWNER_REQUIRED fields."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .schema import OWNER_REQUIRED_FIELDS, SALES_FIELDS_SCHEMA


def _utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def machine_template(draft_id: str, cycle: str = "4") -> dict[str, Any]:
    fields = {}
    for name in OWNER_REQUIRED_FIELDS:
        fields[name] = {
            "value": None,
            "status": "OWNER_REQUIRED",
            "unit": None,
            "currency": "AUD" if name in {"price_aud", "components_cost"} else None,
            "evidence": None,
            "owner_notes": None,
        }
    return {
        "schema": SALES_FIELDS_SCHEMA,
        "kind": "owner_input_template",
        "cycle": cycle,
        "draft_id": draft_id,
        "created_at": _utcnow(),
        "fields": fields,
        "instructions": {
            "null_means": "OWNER_REQUIRED",
            "do_not_invent": True,
            "sku_policy": "YES_USE_PRODUCT_ID already GROUNDED_OWNER_CONFIRMED — do not reopen unless conflict",
        },
    }


def human_markdown(draft_id: str, cycle: str = "4", prior_sku_note: str = "YES_USE_PRODUCT_ID") -> str:
    lines = [
        f"# Ziman Owner Input Form — CYCLE-{cycle}",
        "",
        f"- Draft ID: `{draft_id}`",
        f"- Generated (UTC): `{_utcnow()}`",
        f"- SKU status (locked): GROUNDED_OWNER_CONFIRMED (`{prior_sku_note}`)",
        "- Verdict target after fill: still internal; publish remains false",
        "",
        "## Fields requiring owner input",
        "",
        "| Field | Value | Unit/Currency | Notes / Evidence |",
        "|---|---|---|---|",
    ]
    hints = {
        "price_aud": "AUD number only; never invent",
        "stock_qty": "non-negative integer",
        "delivery_options": "list or description",
        "lead_time": "e.g. days / business days",
        "weight_g": "grams (unit required)",
        "dimensions": "include unit (cm/mm)",
        "components_cost": "AUD COGS if known",
        "license_clearance": "formal clearance evidence required for final confirm",
    }
    for name in OWNER_REQUIRED_FIELDS:
        lines.append(f"| `{name}` | _null / OWNER_REQUIRED_ |  | {hints.get(name, '')} |")
    lines.extend(
        [
            "",
            "## Rules",
            "",
            "1. Leave null if unknown — status stays OWNER_REQUIRED.",
            "2. Do not invent commercial sell values.",
            "3. Negative price / fractional stock will be rejected by validators.",
            "4. License final confirm requires evidence artifact reference.",
            "5. External publish remains HOLD / false until owner review complete.",
            "",
        ]
    )
    return "\n".join(lines)
