#!/usr/bin/env python3
"""Remediation after the dedupe-key switch re-sent 11 cards:
 - restore EXECUTED state for cards already resolved (prevents re-dispatch)
 - mark TEST card test:true
 - send the owner ONE short clarification naming the 5 valid cards
"""
import hashlib
import json
import pathlib
import sys
import time

RD = pathlib.Path("/home/ari/ofn/state/revenue-drive")
sys.path.insert(0, str(RD))
import owner_ask  # noqa: E402  (reuse the sanctioned sender)

NOW = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
reg = json.loads((RD / "owner-ask-registry.json").read_text(encoding="utf-8"))
cards = reg["cards"]

EXECUTED = {"5df55ba0": "2026-09-18T00:40:25Z", "6bb24fc1": "2026-09-18T00:41:07Z",
            "ff34ac53": "2026-09-18T00:41:07Z", "a1b2c3d4": "2026-09-18T00:45:18Z"}
for did, ts in EXECUTED.items():
    if did in cards:
        cards[did]["state"] = "EXECUTED"
        cards[did]["resolved_at"] = ts
if "a1b2c3d4" in cards:
    cards["a1b2c3d4"]["test"] = True
(RD / "owner-ask-registry.json").write_text(
    json.dumps(reg, indent=1, sort_keys=True) + "\n", encoding="utf-8")

open_ids = {d: c["id"] for d, c in cards.items() if c.get("state") == "PENDING"}
with (RD / "receipts.jsonl").open("a", encoding="utf-8") as fh:
    fh.write(json.dumps({"schema": "octopus.owner-ask.remediation.v1", "at": NOW,
                         "why": "dedupe-key switch re-sent 11 cards; states restored, "
                                "one clarification card sent",
                         "pending_cards": open_ids}, ensure_ascii=False,
                        sort_keys=True) + "\n")

txt = ("🔧 دیباگ انجام شد — اگر چند پیام تکراری دیدی، آن‌ها اثر باگ بودند و قابل نادیده‌گرفتن‌اند.\n"
       "فقط این ۵ دکمه معتبرند (بقیه را ببند):\n\n"
       "1️⃣ پول (۱۰ بستهٔ آماده) — کد %s → دکمهٔ «تأیید و ارسال ایمیل»\n"
       "2️⃣ زیمن — کد %s → یکی از گزینه‌ها\n"
       "3️⃣ کانال تقاضا — کد %s → یکی از گزینه‌ها\n"
       "4️⃣ تماس/DIDWW — کد %s → یکی از گزینه‌ها\n"
       "5️⃣ بستهٔ ۲۰ رأی معلق — کد %s → یکی از گزینه‌ها\n\n"
       "دکمه‌ها الان لحظه‌ای هستند (زیر ~۱ دقیقه پردازش می‌شوند).") % (
      "cc2566cb", "4d6f9cc9", "3c63766b", "fda29337", "1b41b3cf")
ok, detail = owner_ask.send_card(txt)
print("clarification sent:", ok, detail)
print("pending cards:", open_ids)
