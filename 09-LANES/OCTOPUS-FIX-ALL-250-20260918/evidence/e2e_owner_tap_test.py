#!/usr/bin/env python3
"""WHY-SLOW-250 E2E test: option tap -> recorded; duplicate tap -> ignored.
Self-addressed: we inject spool rows (the sanctioned test pattern) instead of
asking the owner to tap. Cleans nothing destructive; card is marked test."""
import json
import pathlib
import subprocess
import time

RD = pathlib.Path("/home/ari/ofn/state/revenue-drive")
DID = "a1b2c3d4"
CHAT = "6150431610"
NOW = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

# 1. registry entry (test card, PENDING, 3 options)
reg = json.loads((RD / "owner-ask-registry.json").read_text(encoding="utf-8"))
reg["cards"][DID] = {"id": "TEST-DEBUG-OPT", "at": NOW, "card_sent_at": NOW,
                     "packets": [], "channel": None, "state": "PENDING",
                     "sent_ok": True, "test": True}
(RD / "owner-ask-registry.json").write_text(
    json.dumps(reg, indent=1, sort_keys=True) + "\n", encoding="utf-8")

# 2. review item so _dispatch_card can resolve it
rv = json.loads((RD / "owner-review.json").read_text(encoding="utf-8"))
rv["items"] = [i for i in rv.get("items", []) if str(i.get("id")) != "TEST-DEBUG-OPT"]
rv["items"].append({"id": "TEST-DEBUG-OPT", "at": NOW,
                    "why": "کارت تست دیباگ (خودآدرس) — گزینه/تپ تکراری",
                    "owner_one_card": ["گزینهٔ یک", "گزینهٔ دو", "گزینهٔ سه"]})
(RD / "owner-review.json").write_text(json.dumps(rv, ensure_ascii=False, indent=1),
                                      encoding="utf-8")

# 3. inject two taps: option 2, then a duplicate plain go (must be ignored)
with (RD / "tg-inbox.jsonl").open("a", encoding="utf-8") as fh:
    fh.write(json.dumps({"chat": CHAT, "text": "opt:%s:2" % DID, "at": NOW,
                         "lane": "MONEY", "route_reason": "callback_query",
                         "kind": "callback"}, ensure_ascii=False) + "\n")
    fh.write(json.dumps({"chat": CHAT, "text": "go:%s" % DID,
                         "at": NOW, "lane": "MONEY",
                         "route_reason": "callback_query", "kind": "callback"},
                        ensure_ascii=False) + "\n")

r = subprocess.run(["python3", "state/revenue-drive/owner_reply.py"],
                   capture_output=True, text=True, cwd="/home/ari/ofn")
print("run:", r.returncode, (r.stdout or "").strip()[:200], (r.stderr or "").strip()[:200])

# 4. verify
dec = [json.loads(l) for l in (RD / "owner-decisions.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()][-3:]
print("last decisions:")
for d in dec:
    print("  ", d.get("at"), d.get("decision"), "id=", d.get("decision_id"), "opt=", d.get("option"), d.get("text", "")[:40])
rec = [json.loads(l) for l in (RD / "receipts.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
kinds = [x.get("kind") for x in rec][-8:]
print("last receipt kinds:", kinds)
reg2 = json.loads((RD / "owner-ask-registry.json").read_text(encoding="utf-8"))
print("test card state:", reg2["cards"][DID].get("state"))
