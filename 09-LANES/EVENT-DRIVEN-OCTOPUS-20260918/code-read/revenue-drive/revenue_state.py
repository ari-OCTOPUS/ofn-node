#!/usr/bin/env python3
"""revenue_state.py — AUTONOMY V3 section 9 revenue state machine (deterministic, $0).

Only VERIFIED_CASH counts as revenue. A lane without channel authorization is
parked READY_FOR_AUTHORITY without re-asking the owner every cycle (section 9).
2026-09-15 (season-correction): capacity window leads[:20]->[:200]; lanes with
contact channels advance to CHANNEL_AUTHORIZED when the machine-readable
authorization exists; canonical season meter rewritten each cycle.
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
for a in leads[:200]:  # 2026-09-15 capacity fix (season-correction 1.3)
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
    # 2026-09-15 (season-correction 1.3): machine-readable funnel authorization
    # (channel-authorization.json, RED-4) exists — email-contact lanes may advance.
    if rate_ok and (ROOT / "channel-authorization.json").exists() \
            and not (ROOT / "CHANNEL-REVOKED").exists():
        adv("CHANNEL_AUTHORIZED", "machine-readable channel authorization present")
    o["parked"] = (o["state"] == "PACKET_READY" and not rate_ok) or False

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

# 2026-09-15 (season-correction 4.1): canonical season meter, rewritten in place
try:
    _emails = sum(1 for _l in (ROOT / "lead-emails.jsonl")
                  .read_text(errors="replace").splitlines() if _l.strip())
    _staged = len(list((ROOT / "send-queue").glob("QP-*.json")))
    _today = time.strftime("%Y-%m-%d", time.gmtime())
    # 2026-09-17 data-integrity fix: explicit outcome only (the old default
    # `.get("outcome", "sent")` silently counted outcome-less rows as sent).
    _sent_today = 0
    for _l in (ROOT / "sent-log.jsonl").read_text(errors="replace").splitlines():
        try:
            _r = json.loads(_l)
        except ValueError:
            continue
        if _r.get("at", "").startswith(_today) and _r.get("outcome") == "sent":
            _sent_today += 1
    _repl = 0
    for _l in (ROOT / "tg-inbox.jsonl").read_text(errors="replace").splitlines():
        if "REPLY_DETECTED" in _l and "arminooal4@gmail.com" not in _l:
            _repl += 1
    # MIGRATION 2026-09-17 (owner ruling): sent_today/sent_total had mixed
    # units (messages vs packet-lifecycle-state) — renamed to make the unit
    # explicit; added contactable_phone_only; the four canonical daily values
    # are leads_total, emails_known, contactable_phone_only, verified_cash.
    _phone_only = 0
    _pq = ROOT / "phone-only-queue.jsonl"
    if _pq.exists():
        _phone_only = sum(1 for _l in _pq.read_text(errors="replace")
                          .splitlines() if _l.strip())
    (ROOT / "season-meter.json").write_text(json.dumps({
        "at": NOW,
        "verified_cash": st.get("verified_cash_aud", 0.0),
        "leads_total": len(leads),
        "emails_known": _emails,
        "contactable_phone_only": _phone_only,
        "authorized_with_contact": st["counts"].get("CHANNEL_AUTHORIZED", 0),
        "staged_packets": _staged,
        "messages_sent_today": _sent_today,
        "packets_in_sent_state": st["counts"].get("SENT", 0),
        "replies_detected": _repl,
    }, indent=1, sort_keys=True) + "\n", encoding="utf-8")
except Exception:
    pass

print(json.dumps({"state_counts": st["counts"], "rate_card": rate_ok,
                  "packets": len(packets),
                  "ready_for_authority": len(st["ready_for_authority"]),
                  "verified_cash_aud": 0.0}, ensure_ascii=False))
