#!/usr/bin/env python3
"""OWNER-LINK v2 acceptance test (owner chat never touched; all sends stubbed):
 A. superseded-card tap forwards to the live replacement
 B. bare approval with several pending cards -> replies with the open list (stubbed)
 C. every allowed owner text message is mirrored into the MONEY spool (never drop)
Cleanup: test cards removed at the end.
"""
import json
import pathlib
import sys
import time

ROOT = pathlib.Path("/home/ari/ofn")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "state" / "revenue-drive"))
RD = ROOT / "state" / "revenue-drive"
NOW = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
CHAT = "6150431610"

import owner_reply as OR  # noqa: E402
from ofn.agents import glass_runner as GR  # noqa: E402

OR.send_owner_text = lambda t: True          # never message the real owner
RD_extra = {}

# ---------- data fix: replacement_did for the superseded cards ----------
reg = json.loads((RD / "owner-ask-registry.json").read_text(encoding="utf-8"))
REPL = {"d3c0fdea": "cc2566cb", "2d90365e": "cc2566cb", "b3417ba8": "4d6f9cc9",
        "ca187645": "3c63766b"}
for d, r in REPL.items():
    if d in reg["cards"]:
        reg["cards"][d]["replacement_did"] = r
# test pair
reg["cards"]["feed1234"] = {"id": "TEST-FWD", "at": NOW, "state": "SUPERSEDED",
                            "replacement_did": "beef5678", "test": True, "packets": []}
reg["cards"]["beef5678"] = {"id": "TEST-FWD-2", "at": NOW, "state": "PENDING",
                            "test": True, "packets": []}
(RD / "owner-ask-registry.json").write_text(json.dumps(reg, indent=1, sort_keys=True) + "\n",
                                            encoding="utf-8")
rv = json.loads((RD / "owner-review.json").read_text(encoding="utf-8"))
rv["items"] = [i for i in rv["items"] if str(i.get("id")) != "TEST-FWD-2"]
rv["items"].append({"id": "TEST-FWD-2", "at": NOW, "why": "تست فوروارد",
                    "owner_one_card": []})
(RD / "owner-review.json").write_text(json.dumps(rv, ensure_ascii=False, indent=1),
                                      encoding="utf-8")

print("== A: tap on superseded card forwards ==")
with (RD / "tg-inbox.jsonl").open("a", encoding="utf-8") as fh:
    fh.write(json.dumps({"chat": CHAT, "text": "go:feed1234", "at": NOW,
                         "lane": "MONEY", "route_reason": "callback_query",
                         "kind": "callback"}) + "\n")
OR.main()
reg2 = json.loads((RD / "owner-ask-registry.json").read_text(encoding="utf-8"))
print("  replacement card state:", reg2["cards"]["beef5678"].get("state"), "(expect EXECUTED)")
rec = [json.loads(l) for l in (RD / "receipts.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
print("  forwarding receipt:", [r.get("kind") for r in rec if r.get("kind") == "TAP_FORWARDED_TO_REPLACEMENT"])

print("== B: bare approval with several pending cards -> asks, no binding ==")
with (RD / "tg-inbox.jsonl").open("a", encoding="utf-8") as fh:
    fh.write(json.dumps({"chat": CHAT, "text": "تایید", "at": NOW,
                         "lane": "MONEY", "route_reason": "not_b3_shaped",
                         "kind": "message"}) + "\n")
OR.main()
rec = [json.loads(l) for l in (RD / "receipts.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
noid = [r for r in rec if r.get("kind") in ("OWNER_DECISION_NO_IDENTITY",
                                            "OWNER_DECISION_BOUND_SOLE_PENDING")]
print("  last identity receipt:", noid[-1].get("kind") if noid else None,
      "| open_cards:", (noid[-1].get("open_cards") if noid else None))

print("== C: owner text is mirrored into the MONEY spool (glass) ==")
before = (RD / "tg-inbox.jsonl").read_text(encoding="utf-8").count("\n")
upd = [{"update_id": 999000001,
        "message": {"chat": {"id": int(CHAT)}, "text": "تأیید cc2566cb"}}]
st = GR.process_updates(upd, "dummy-token")
after_rows = [json.loads(l) for l in (RD / "tg-inbox.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
mir = [r for r in after_rows if r.get("mirrored_from") or str(r.get("route_reason", "")).startswith("mirror:")]
print("  glass stats:", st)
print("  mirrored rows:", len(mir), "| last:", json.dumps(mir[-1], ensure_ascii=False)[:160] if mir else None)

print("== cleanup ==")
reg3 = json.loads((RD / "owner-ask-registry.json").read_text(encoding="utf-8"))
for d in ("feed1234", "beef5678"):
    reg3["cards"].pop(d, None)
(RD / "owner-ask-registry.json").write_text(json.dumps(reg3, indent=1, sort_keys=True) + "\n",
                                            encoding="utf-8")
rv = json.loads((RD / "owner-review.json").read_text(encoding="utf-8"))
rv["items"] = [i for i in rv["items"] if str(i.get("id")) != "TEST-FWD-2"]
(RD / "owner-review.json").write_text(json.dumps(rv, ensure_ascii=False, indent=1),
                                      encoding="utf-8")
# drop the two synthetic spool rows we appended (keep cursor consistent)
raw = (RD / "tg-inbox.jsonl").read_text(encoding="utf-8").splitlines()
keep = [l for l in raw if ("go:feed1234" not in l and '"text": "تایید"' not in l
                           and "999000001" not in l and "تأیید cc2566cb" not in l)]
(RD / "tg-inbox.jsonl").write_text("\n".join(keep) + "\n", encoding="utf-8")
print("  test cards/rows removed; spool rows now:", len(keep))
