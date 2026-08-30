#!/usr/bin/env python3
"""Seed the five PII-free day-zero scenarios idempotently.

Seed rows are operational walkthrough fixtures only. They never count toward
pilot success. Run: ``python3 tools/seed_pilot.py``.
"""

from __future__ import annotations

import inspect
import os
import sys
from typing import Any, Mapping

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ofn import config  # noqa: E402
from ofn.adapters.lead_store import LeadStore  # noqa: E402
from ofn.adapters.products import ProductStore  # noqa: E402
from ofn.adapters.studio_store import StudioStore  # noqa: E402


def _ensure_lead(store: LeadStore, source_ref: str, data: Mapping[str, object],
                 *, now_iso: str) -> None:
    existing = store.list_leads("lead", limit=100)
    if any(str(row.get("source_ref") or "") == source_ref for row in existing):
        return
    payload = dict(data)
    payload.update({"lead_id": f"seed-pilot-{source_ref}",
                    "source": "seed_pilot", "source_ref": source_ref})
    store.create_lead("lead", payload, now_iso=now_iso)


def _product_create_kwargs(store: ProductStore) -> dict[str, Any]:
    """Use provenance only when the concurrently evolving API accepts it."""
    parameters = inspect.signature(store.create).parameters
    provenance = {
        "environment": "seed",
        "source": "seed_pilot",
        "created_by": "seed_pilot",
    }
    kwargs = {key: value for key, value in provenance.items() if key in parameters}
    if "provenance" in parameters:
        kwargs["provenance"] = provenance
    return kwargs


def _ensure_product(store: ProductStore, name: str, fields: Mapping[str, Any],
                    *, for_sale: bool, now_iso: str) -> None:
    piece = next((item for item in store.list("ziman", include_archived=True)
                  if item.name == name), None)
    if piece is None:
        create_fields = dict(fields)
        create_fields["name"] = name
        piece = store.create("ziman", "ZM", create_fields, now_iso=now_iso,
                             **_product_create_kwargs(store))
    if for_sale and piece.state == "in_progress":
        store.update("ziman", piece.sku, {"state": "for_sale"}, now_iso=now_iso)


def main() -> int:
    cfg = config.load()
    now = config.now_iso()
    painting = LeadStore(cfg.painting_path)
    products = ProductStore(
        cfg.products_path,
        cost_fields=cfg.packs_dir and ["materials_cost_aud"],
        labour_hours_field="labour_hours",
        labour_rate_field="hourly_rate_aud")
    studio = StudioStore(cfg.studio_path)
    try:
        _ensure_lead(painting, "pilot-1", {
            "customer_name": "مشتری آزمایشی یک", "phone": "0411000001",
            "message": "برای اتاق پذیرایی رنگ می‌خواهم",
        }, now_iso=now)
        _ensure_lead(painting, "pilot-2", {
            "customer_name": "مشتری آزمایشی دو", "phone": "0411000002",
            "message": "نمای ساختمان",
        }, now_iso=now)

        _ensure_product(products, "گلدان آزمایشی", {
            "materials_cost_aud": 12.0,
            "packaging_cost_aud": 2.0,
            "price_primary_aud": 48.0,
        }, for_sale=False, now_iso=now)
        _ensure_product(products, "ظرف آزمایشی", {
            "materials_cost_aud": 6.0,
            "packaging_cost_aud": 1.0,
            "price_primary_aud": 22.0,
        }, for_sale=True, now_iso=now)

        if not any(draft.draft_id == "pilot-draft-1"
                   for draft in studio.drafts("studio")):
            studio.add_draft("studio", "pilot-draft-1",
                             collection_id=None, caption="پست آزمایشی",
                             now_epoch_s=config.epoch_seconds())
    finally:
        painting.close()
        products.close()
        studio.close()
    print("ensured: 2 seed leads, 2 seed ziman pieces (1 for_sale), "
          "1 seed studio draft")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
