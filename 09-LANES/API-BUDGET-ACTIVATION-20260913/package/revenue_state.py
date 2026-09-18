#!/usr/bin/env python3
"""revenue_state.py — AUTONOMY V3 section 9 revenue state machine (deterministic, $0).

Only VERIFIED_CASH counts as revenue. A lane without channel authorization is
parked READY_FOR_AUTHORITY without re-asking the owner every cycle (section 9).
"""
import json
import pathlib
import time

ROOT = pathlib.Path("/home/ari/ofn/state/revenue-drive")
STATE = ROOT / "revenue-state.json"
RECEIPTS = ROOT / "receipts.jsonl"
LEADS = pathlib.Path("/home/ari/ofn/tools/leads_master.json")
RATE_CARD = pathlib.Path("/home/ari/ofn/data/rate-card.json")
PACKETS = ROOT / "quote-packets"

NOW = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
ORDER = ["OPPORTUNITY_FOUND", "PACKET_READY", "PRICE_VALIDATED", "CHANNEL_AUTHORIZED",
         "SENT", "DELIVERED", "REPLIED", "QUOTE_ACCEPTED", "INVOICED",
         "PAYMENT_PENDING", "VERIFIED_CASH", "RECONCILED"]


def load(p, d):
    try:
        return json.loads(pathlib.Path(p).read_text(errors="replace"))
    except (OSError, ValueError):
        return d


st = load(STATE, {"schema": "octopus.revenue-state.v1", "opportunities": {},
                  "verified_cash_aud": 0.0})
opps = st["opportunities"]
rate_ok = RATE_CARD.exists()
packets = sorted(p.name for p in PACKETS.glob("QP-*.json")) if PACKETS.exists() else []

leads = load(LEADS, {}).get("accounts", [])
for a in leads[:20]:
    name = a.get("business_name")
    if not name:
        continue
    o = opps.setdefault(name, {"lead": name, "state": "OPPORTUNITY_FOUND",
                               "evidence": a.get("evidence_url") or a.get("source"),
                               "history": []})
    def adv(to, why):
        if ORDER.index(to) > ORDER.index(o["state"]):
            o["history"].append({"at": NOW, "from": o["state"], "to": to, "why": why})
            o["state"] = to
    if packets:
        adv("PACKET_READY", "quote packet prepared (%d available)" % len(packets))
    if rate_ok:
        adv("PRICE_VALIDATED", "valid rate card present")
    # CHANNEL_AUTHORIZED requires a machine-readable authorization (V3 RED-4):
    # the email channel is retired, so lanes park instead of spamming the owner.
    o["parked"] = (o["state"] == "PRICE_VALIDATED" and not rate_ok) or \
                  (o["state"] == "PACKET_READY" and not rate_ok) or \
                  (o["state"] == "PRICE_VALIDATED")

st["at"] = NOW
st["policy"] = "AUTONOMY_V3"
st["verified_cash_aud"] = 0.0
st["counts"] = {}
for o in opps.values():
    st["counts"][o["state"]] = st["counts"].get(o["state"], 0) + 1
st["ready_for_authority"] = sorted(k for k, v in opps.items() if v.get("parked"))
st["note"] = ("packets are NOT revenue; only VERIFIED_CASH counts; parked lanes do "
              "not re-ask the owner every cycle (V3 section 9)")
STATE.write_text(json.dumps(st, indent=1, sort_keys=True, ensure_ascii=False) + "\n",
                 encoding="utf-8")
with RECEIPTS.open("a", encoding="utf-8") as fh:
    fh.write(json.dumps({"schema": "octopus.revenue-state.receipt", "at": NOW,
                         "counts": st["counts"], "rate_card": rate_ok,
                         "packets": len(packets),
                         "ready_for_authority": len(st["ready_for_authority"]),
                         "verified_cash_aud": 0.0}, sort_keys=True,
                        ensure_ascii=False) + "\n")
print(json.dumps({"state_counts": st["counts"], "rate_card": rate_ok,
                  "packets": len(packets),
                  "ready_for_authority": len(st["ready_for_authority"]),
                  "verified_cash_aud": 0.0}, ensure_ascii=False))
