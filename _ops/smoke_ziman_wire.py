#!/usr/bin/env python3
"""smoke_ziman_wire.py — بررسی سریع اتصال پای زیمان (بدون شبکه)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

_OPS = Path(__file__).resolve().parent
sys.path.insert(0, str(_OPS))
sys.path.insert(0, str(_OPS / "budget"))
sys.path.insert(0, str(_OPS / "legs"))

os.environ.setdefault("OCTOPUS_WIRE_ZIMAN", "1")

import wiring  # noqa: E402
from ziman_leg import ZimanLeg  # noqa: E402


def main() -> int:
    leg = wiring.make_ziman_leg()
    if leg is None:
        # flag may be off if explicitly 0; force construct
        leg = ZimanLeg(organ_table={"ZIMAN": {"floor": 1}}, capacity_ceiling=30)
        print("wiring returned None (flag?) — constructed direct ZimanLeg")
    else:
        print("wiring.make_ziman_leg →", type(leg).__name__, "money_link=", leg.money_link)

    snap = leg.status_snapshot()
    print("status:", {k: snap[k] for k in (
        "leg_id", "organ", "money_link", "capacity_ceiling_per_week",
        "drafts_count", "autonomy") if k in snap})
    print("digest:\n", leg.telegram_digest())
    g = leg.campaign_check(100)
    print("D4 over-ceiling approved?", g["approved"], "—", g["reason"][:80])
    p = leg.draft_content(product_family="C3")
    print("proposal kind=", p.kind, "publish=", p.payload.get("publish"))
    bio = wiring.ziman_beat(leg, beat=0)
    if bio:
        b = bio.get("biology") or {}
        print("biology:", {
            "schema": b.get("schema"),
            "nerves": (b.get("nerves") or {}).get("connected"),
            "doctor": (b.get("doctor") or {}).get("connected"),
            "heart_write": b.get("ziman_can_write_heart"),
            "outward_execution": b.get("outward_execution"),
        })
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
