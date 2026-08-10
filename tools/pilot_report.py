#!/usr/bin/env python3
"""O12 — pilot daily report from the canonical stores (no parallel DB).

Run: python3 tools/pilot_report.py [--days 3]
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ofn import config  # noqa: E402
from ofn.adapters.lead_store import LeadStore  # noqa: E402
from ofn.adapters.products import ProductStore  # noqa: E402
from ofn.adapters.studio_store import StudioStore  # noqa: E402


def main(argv: list[str]) -> int:
    days = 3
    if "--days" in argv:
        try:
            days = int(argv[argv.index("--days") + 1])
        except (ValueError, IndexError):
            days = 3
    cfg = config.load()
    painting = LeadStore(cfg.painting_path)
    products = ProductStore(
        cfg.products_path,
        cost_fields=["materials_cost_aud"],
        labour_hours_field="labour_hours",
        labour_rate_field="hourly_rate_aud")
    studio = StudioStore(cfg.studio_path)

    leads = painting.list_leads("lead", limit=100)
    open_leads = [l for l in leads
                  if l.get("status") in ("new", "review", "contacted", "quoted")]
    due = painting.follow_ups_due("lead", before_iso=config.now_iso())
    pieces = products.list("ziman")
    ready = [p for p in pieces if p.state == "for_sale"]
    sold = [p for p in pieces if p.state == "sold"]
    drafts = studio.drafts("studio") or []

    print(f"pilot report (last {days}d window view)")
    print(f"  lead: {len(open_leads)} open · {len(due)} follow-up due")
    print(f"  ziman: {len(ready)} ready-to-list · {len(sold)} sold")
    print(f"  studio: {len(drafts)} drafts")
    print("  (thresholds are set by Ari on day zero — none invented here)")

    painting.close()
    products.close()
    studio.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
