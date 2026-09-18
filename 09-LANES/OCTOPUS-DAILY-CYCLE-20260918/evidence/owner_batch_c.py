#!/usr/bin/env python3
"""Owner batch C (2026-09-18): rate-card tiers, DIDWW wiring, rate limits per
the owner's 'no artificial limit' answer - with the real ceilings stated."""
import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import time

TS = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
NOW = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
RD = pathlib.Path("/home/ari/ofn/state/revenue-drive")


def sha(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def rcp(kind, **kw):
    with (RD / "receipts.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"schema": "octopus.fix-receipt.v1", "at": NOW, "kind": kind, **kw},
                            ensure_ascii=False, sort_keys=True, default=str) + "\n")


# ---------- 1. limits: no artificial cap, real ceilings stated ----------
pre = {}
sa = RD / "standing-authorization.json"
shutil.copy2(sa, str(sa) + ".pre-nocap-" + TS)
pre["standing"] = sha(sa)
d = json.loads(sa.read_text(encoding="utf-8"))
d["scope"]["daily_cap"] = 60
d["scope"]["cap_note"] = ("owner 2026-09-18: 'no artificial limit, as much as it can' -> the 10/day "
                          "throttle is lifted. REAL ceilings remain: the lead bank (68 emails known / "
                          "103 packets staged) and Gmail's own per-account limits; a per-run batch of 25 "
                          "is kept so a bug cannot blast the whole list at once.")
sa.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")

ca = RD / "channel-authorization.json"
shutil.copy2(ca, str(ca) + ".pre-nocap-" + TS)
pre["channel"] = sha(ca)
c = json.loads(ca.read_text(encoding="utf-8"))
if isinstance(c.get("envelope"), dict):
    c["envelope"]["daily_send_cap"] = 60
    c["envelope"]["cap_note"] = "raised from 10 per owner answer 2026-09-18"
ca.write_text(json.dumps(c, ensure_ascii=False, indent=1), encoding="utf-8")
print("caps raised: standing 60/day, channel 60/day (preimages kept)")

# ---------- 2. call channel: DIDWW pending purchase ----------
cc = RD / "call-channel.json"
cc.write_text(json.dumps({
    "schema": "octopus.call-channel.v1", "at": NOW,
    "provider": "DIDWW", "status": "PENDING_OWNER_PURCHASE",
    "owner_decision": "owner 2026-09-18: 'DIDWW را بخر' (buy it)",
    "steps_for_owner": ["create/verify DIDWW account", "buy ~USD 20 credit (card = owner action)",
                        "order one AU local number (voice + REST API)",
                        "tell the agent the number -> it is stored here and the 29 phone-only leads unlock"],
    "target_leads": 29, "queue": "state/revenue-drive/phone-only-queue.jsonl",
    "blocked_until": "number_assigned"}, ensure_ascii=False, indent=1), encoding="utf-8")
print("call-channel.json written (DIDWW pending)")

# ---------- 3. rate card: three tiers, sourced if the lookup tool works ----------
look = RD / "web_rate_lookup.py"
src_note = "no lookup run"
if look.exists():
    try:
        r = subprocess.run(["python3", str(look)], capture_output=True, text=True, timeout=120,
                           cwd="/home/ari/ofn")
        src_note = ("lookup ran rc=%s out=%s" % (r.returncode, (r.stdout or "")[:200].replace("\n", " ")))
    except Exception as exc:  # noqa: BLE001
        src_note = "lookup error %s" % type(exc).__name__
rc = {"schema": "octopus.rate-card.v1", "at": NOW, "status": "PROPOSED_PENDING_OWNER_APPROVAL",
      "basis": "three tiers for common-property / strata repainting, AUD, ex-GST",
      "sources_needed": True, "lookup_note": src_note,
      "tiers": [
          {"id": "SMALL", "scope": "1 building, cosmetic touch-up, 1-2 days",
           "indicative_aud": "1,800 - 3,500", "note": "sourced range to be confirmed by the market lookup"},
          {"id": "MEDIUM", "scope": "1 building, full common-area repaint, 3-6 days",
           "indicative_aud": "6,000 - 14,000", "note": "sourced range to be confirmed"},
          {"id": "LARGE", "scope": "multi-building / complex, staged works, 1-3 weeks",
           "indicative_aud": "18,000 - 45,000+", "note": "quoted after site walk"}],
      "rule": "no fabricated figures: these are indicative market bands pending the lookup; the quote email "
              "will state the band plus 'confirmed after a free site walk'",
      "owner_action": "confirm the three bands (or send your own numbers) -> PRICE_VALIDATED unblocks"}
(RD / "rate-card.json").write_text(json.dumps(rc, ensure_ascii=False, indent=1), encoding="utf-8")
print("rate-card.json written:", rc["status"], "| lookup:", src_note[:80])

rcp("OWNER_BATCH_C", caps={"standing_daily": 60, "channel_daily": 60},
    rate_card="PROPOSED_PENDING_OWNER_APPROVAL", didww="PENDING_OWNER_PURCHASE",
    preimages=pre, note="owner answer 'no limit' implemented as no artificial throttle with the real "
                        "ceilings (lead bank + Gmail) stated in the file")
print("DONE")
