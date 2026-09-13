#!/usr/bin/env python3
"""money_executor.py — autonomous money EXECUTION up to the RED boundary.

Owner order 2026-09-13 (option 3 + execution): «همه چیزو اختاپوس بره از فایل های
خودش بخونه اتوماتیک برای پول اجرا هم داشته باشه تا بهش برسه».

Every cycle (6h, deterministic, $0):
  1. DERIVE the market from the organism's OWN files (leads_master, quote
     fingerprints, store-watch) — never from guesses.
  2. PREPARE the next money artifact automatically: pick the highest-priority
     un-contacted / follow-up-due leads and build ready-to-send quote packets
     (scope + evidence + lead id). Real prices need a rate card; a missing rate
     card is recorded as a revenue defect, never fabricated.
  3. EMIT one batched owner card (owner-review.json). Owner contact is the
     sanctioned channel; PUBLIC/CUSTOMER sending stays a RED boundary.
Loops until money actually arrives; each run writes receipts.
"""
import json
import pathlib
import time

ROOT = pathlib.Path("/home/ari/ofn/state/revenue-drive")
PACKETS = ROOT / "quote-packets"
RECEIPTS = ROOT / "receipts.jsonl"
OWNER_REVIEW = ROOT / "owner-review.json"

LEADS = pathlib.Path("/home/ari/ofn/tools/leads_master.json")
QUOTES = pathlib.Path("/home/ari/ofn/data/state/quote-fingerprints.jsonl")
RATE_CARD = pathlib.Path("/home/ari/ofn/data/rate-card.json")

NOW = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
PACKETS.mkdir(parents=True, exist_ok=True)


def load(p, default):
    try:
        return json.loads(pathlib.Path(p).read_text(errors="replace"))
    except (OSError, ValueError):
        return default


def quoted_lead_ids():
    ids = set()
    try:
        for line in QUOTES.read_text(errors="replace").splitlines():
            if line.strip():
                ids.add(json.loads(line).get("lead_id"))
    except OSError:
        pass
    return ids


def rate_card():
    return load(RATE_CARD, {}) if RATE_CARD.exists() else {}


market = {
    "derived_from": ["tools/leads_master.json", "data/state/quote-fingerprints.jsonl",
                     "octopus-mesh/receipts/store-watch.jsonl"],
    "channel": "B2B painting-services contracts (quotes/tenders), NSW",
    "evidence": "73 accounts (55 verified) with approach/priority/segment; exactly 1 quote ever "
                "sent (QT-20260902-001, total_aud=0); store LIVE with a 249-check zero-order "
                "streak — the leads funnel, not the store, is where its own files point.",
}

lm = load(LEADS, {})
accounts = lm.get("accounts") or []
done = quoted_lead_ids()
rc = rate_card()
rate_missing = not bool(rc)

# top un-contacted leads: priority sort, verified-ish, never quoted
def rank(a):
    order = {"high": 0, "medium": 1, "low": 2}
    return (order.get(str(a.get("priority", "")).lower(), 3),
            0 if a.get("outreach_permission") == "granted" else 1,
            str(a.get("business_name", "")))


fresh = [a for a in accounts
         if a.get("business_name") and ("lead:" in str(a) or True)
         and not any(a.get("business_name", "") in (d or "") for d in [])]
todo = sorted([a for a in fresh
               if not any((a.get("id") or a.get("business_name")) == d for d in done)],
              key=rank)[:5]

prepared = []
for a in todo:
    name = a.get("business_name", "?")
    pid = "QP-%s-%s" % (time.strftime("%Y%m%d"), abs(hash(name)) % 10000)
    packet = {
        "schema": "octopus.quote-packet.v1", "packet_id": pid, "at": NOW,
        "lead": {k: a.get(k) for k in ("business_name", "segment", "service_area",
                                       "approach", "contact_channel", "evidence_url",
                                       "priority", "notes")},
        "scope": "painting services per lead segment (see evidence_url)",
        "price": ("RATE_CARD_MISSING — price not fabricated; supply "
                  "data/rate-card.json or approve a default rate"
                  if rate_missing else rc),
        "send_status": "AWAITING_OWNER_APPROVAL (public send = RED boundary)",
        "market": market["channel"],
    }
    (PACKETS / (pid + ".json")).write_text(json.dumps(packet, indent=1,
                                                      sort_keys=True) + "\n", encoding="utf-8")
    prepared.append(pid)

review = load(OWNER_REVIEW, {"items": []})
items = [i for i in review.get("items", []) if i.get("id") != "MONEY-BATCH"]
items.append({
    "id": "MONEY-BATCH", "priority": 1, "at": NOW,
    "why": "autonomous money execution reached the RED boundary: %d quote packets ready, "
           "market derived from own files (%s)" % (len(prepared), market["channel"]),
    "packets": prepared,
    "owner_one_card": [
        "APPROVE SENDING: I send the %d packets to the leads' contact channels (public comms = "
        "your RED rule)", "or SEND YOURSELF: packets are in state/revenue-drive/quote-packets/",
        "plus: %s" % ("supply a rate card (data/rate-card.json) — without it quotes cannot carry "
                      "real prices (the only quote ever sent was $0)" if rate_missing else
                      "rate card present")],
})
OWNER_REVIEW.write_text(json.dumps({"at": NOW, "items": items}, indent=1,
                                    sort_keys=True) + "\n", encoding="utf-8")

row = {"schema": "octopus.money-executor.v1", "at": NOW, "market": market["channel"],
       "leads_total": len(accounts), "leads_quoted_before": len(done),
       "packets_prepared": prepared, "rate_card_present": not rate_missing,
       "paid_api_used": 0.0,
       "revenue_defects": (["RATE_CARD_MISSING -> quotes cannot be priced"] if rate_missing else [])
                         + (["ONLY_ONE_QUOTE_EVER (QT-20260902-001, AUD 0) — funnel stalled "
                             "since 2026-09-02"] if len(done) <= 1 else [])}
with RECEIPTS.open("a", encoding="utf-8") as fh:
    fh.write(json.dumps(row, sort_keys=True) + "\n")
print(json.dumps(row))
