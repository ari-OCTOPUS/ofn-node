#!/usr/bin/env python3
"""O12 — seed pilot scenarios with NO real PII.

Creates five fake scenarios across the three businesses so a day-zero
walkthrough has something real to exercise. All names are fabricated;
nothing here touches partner or customer data.

Run: python3 tools/seed_pilot.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ofn import config  # noqa: E402
from ofn.adapters.lead_store import LeadStore  # noqa: E402
from ofn.adapters.products import ProductStore  # noqa: E402
from ofn.adapters.studio_store import StudioStore  # noqa: E402


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

    # 2 fake leads (fabricated names)
    painting.create_lead("lead", {
        "customer_name": "مشتری آزمایشی یک", "phone": "0411000001",
        "message": "برای اتاق پذیرایی رنگ می‌خواهم",
        "source": "pilot", "source_ref": "pilot-1",
    }, now_iso=now)
    painting.create_lead("lead", {
        "customer_name": "مشتری آزمایشی دو", "phone": "0411000002",
        "message": "نمای ساختمان", "source": "pilot", "source_ref": "pilot-2",
    }, now_iso=now)

    # 2 fake ziman pieces (one for_sale)
    products.create("ziman", "ZM", {
        "name": "گلدان آزمایشی", "materials_cost_aud": 12.0,
        "packaging_cost_aud": 2.0, "price_primary_aud": 48.0,
    }, now_iso=now)
    p2 = products.create("ziman", "ZM", {
        "name": "ظرف آزمایشی", "materials_cost_aud": 6.0,
        "packaging_cost_aud": 1.0, "price_primary_aud": 22.0,
    }, now_iso=now)
    products.update("ziman", p2.sku, {"state": "for_sale"}, now_iso=now)

    # 1 fake studio draft
    studio.add_draft("studio", "pilot-draft-1",
                     collection_id=None, caption="پست آزمایشی",
                     now_epoch_s=config.epoch_seconds())

    painting.close()
    products.close()
    studio.close()
    print("seeded: 2 leads, 2 ziman pieces (1 for_sale), 1 studio draft")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
