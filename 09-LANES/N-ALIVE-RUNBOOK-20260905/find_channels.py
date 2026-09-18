#!/usr/bin/env python3
"""Rank named Octopus surfaces. Propose-only. No network. No secrets."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

LANE = Path(__file__).resolve().parent
VAULT = LANE.parents[1]
CATALOG = LANE / "CATALOG.json"
OUT = LANE / "CHANNEL-RANK.json"

BOARD = VAULT / "06-EVIDENCE" / "OCTOPUS-OWNER-BOARD-2026-08-24"
RECEIPTS = {
    "tg-channel-traffic": VAULT
    / "06-EVIDENCE"
    / "TRAFFIC1-2026-09-05"
    / "TRAFFIC1-SEND1-RECEIPT.json",
    "studio-tg-post1": BOARD / "STUDIO-POST1-RECEIPT.json",
    "tg-owner-card": VAULT
    / "06-EVIDENCE"
    / "IGN1-2026-09-05"
    / "IGN1-CLOSEOUT-RECEIPT.json",
    "of-novasolesau": BOARD / "profiles" / "ONLYFANS-CONNECT.md",
    "x-novasolmate": BOARD / "profiles" / "SOCIAL-HANDLES.md",
    "feetfinder-novasolesau": BOARD / "profiles" / "SOCIAL-HANDLES.md",
    "ig-novasoles-tbd": BOARD / "profiles" / "SOCIAL-HANDLES.md",
    "fb-novasoles-tbd": BOARD / "profiles" / "SOCIAL-HANDLES.md",
    "ziman-storefront": BOARD / "CHECKOUT-1-README-20260905.md",
    "ziman-checkout-1": BOARD / "CHECKOUT-1-README-20260905.md",
    "paint-leads-pool": VAULT
    / "06-EVIDENCE"
    / "OCTOPUS-OWNER-BOARD-2026-08-24"
    / "GOV-V8-REVENUE-IGNITION-2026-09-05.md",
}

# LAYER4 is another lane. Read-only cite for mesh health, not a rewrite.
LAYER4 = (
    VAULT
    / "09-LANES"
    / "U-WHY-NOT-LIVE-20260905"
    / "LAYER4-CHANNEL-SELECTION.json"
)

SCORE = {
    "leg-ziman-http": 100,
    "ziman-storefront": 95,
    "tg-channel-traffic": 90,
    "studio-tg-post1": 85,
    "of-novasolesau": 80,
    "x-novasolmate": 75,
    "leg-studio-http": 70,
    "tg-owner-card": 40,
    "leg-lead-http": 35,
    "paint-leads-pool": 30,
    "paint-ch-telegram": 25,
    "ziman-checkout-1": 20,
    "paint-ch-website": 15,
    "paint-ch-google": 12,
    "feetfinder-novasolesau": 10,
    "paint-ch-instagram": 8,
    "paint-ch-facebook": 8,
    "ig-novasoles-tbd": 5,
    "fb-novasoles-tbd": 5,
    "paint-ch-tiktok": 4,
    "paint-ch-email": 3,
    "leg-owner-http": 0,
    "mesh-bridge": 0,
}

NOT_CUSTOMER = {
    "leg-owner-http",
    "mesh-bridge",
    "tg-owner-card",
    "ziman-checkout-1",
}

BLOCKED_CONTACT = {
    "leg-lead-http": "blocked_outreach_permission_unknown",
    "paint-leads-pool": "blocked_outreach_permission_unknown",
    "of-novasolesau": "feeder_surfaces_only_no_of_api",
    "feetfinder-novasolesau": "kyc_blocked",
    "ig-novasoles-tbd": "handle_tbd",
    "fb-novasoles-tbd": "handle_tbd",
    "paint-ch-email": "auto_email_closed",
    "paint-ch-website": "form_not_built",
    "paint-ch-google": "planned_no_consumer",
    "paint-ch-instagram": "planned_no_consumer",
    "paint-ch-facebook": "planned_no_consumer",
    "paint-ch-tiktok": "planned_no_consumer",
    "paint-ch-telegram": "connected_outbound_disabled",
}


def _exists(p: Path) -> bool:
    return p.is_file()


def _layer4_ok(port: int) -> str:
    if not _exists(LAYER4):
        return "unverified"
    try:
        data = json.loads(LAYER4.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return "unverified"
    hz = data.get("healthz_via_tunnel_this_session") or {}
    row = hz.get(str(port)) or {}
    if row.get("http") == 200 and row.get("ok") is True:
        return "healthz_200_layer4_2026-09-05"
    return "not_green_in_layer4"


def main() -> int:
    cat = json.loads(CATALOG.read_text(encoding="utf-8"))
    ranked = []
    for surf in cat["surfaces"]:
        sid = surf["id"]
        rec = RECEIPTS.get(sid)
        receipt_ok = bool(rec and _exists(rec))
        health = "n/a"
        if surf.get("class") == "mesh" and surf.get("port"):
            health = _layer4_ok(int(surf["port"]))
        if sid in NOT_CUSTOMER:
            contact = "not_a_customer_channel"
        else:
            contact = BLOCKED_CONTACT.get(sid, "propose_only")
        ranked.append({
            "id": sid,
            "leg": surf.get("leg"),
            "class": surf.get("class"),
            "feeds": surf.get("feeds") or [],
            "score": SCORE.get(sid, 0),
            "receipt_on_disk": receipt_ok,
            "receipt_path": str(rec) if rec else None,
            "mesh_health": health,
            "customer_job": surf.get("customer_job"),
            "find_mode": surf.get("find_mode"),
            "contact": contact,
        })
    ranked.sort(key=lambda r: (-r["score"], r["id"]))
    blocked = {
        "not_a_customer_channel",
        "kyc_blocked",
        "blocked_outreach_permission_unknown",
        "handle_tbd",
        "auto_email_closed",
        "form_not_built",
        "planned_no_consumer",
        "feeder_surfaces_only_no_of_api",
    }
    destinations = {"of-novasolesau"}
    customer_now = [
        r["id"] for r in ranked
        if r["score"] >= 70
        and r["contact"] not in blocked
        and r["id"] not in destinations
    ]
    of_feeders = [
        r["id"] for r in ranked
        if "onlyfans" in r["feeds"]
        and r["id"] not in destinations
        and r["contact"] == "propose_only"
    ]
    out = {
        "schema": "octopus.channel-rank.v1",
        "ts_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "network": False,
        "send": False,
        "flags_touched": False,
        "catalog_sha256": hashlib.sha256(CATALOG.read_bytes()).hexdigest(),
        "contradictions_open": cat.get("contradictions_open") or [],
        "rank": ranked,
        "customer_find_now": customer_now,
        "of_feeders_now": of_feeders,
        "leg_feeders_now": {
            "ziman": [r["id"] for r in ranked if "ziman" in r["feeds"] and r["score"] >= 70],
            "painting": [r["id"] for r in ranked if "painting" in r["feeds"] and r["contact"] == "propose_only"],
            "studio": [r["id"] for r in ranked if "studio" in r["feeds"] and r["score"] >= 70],
        },
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
