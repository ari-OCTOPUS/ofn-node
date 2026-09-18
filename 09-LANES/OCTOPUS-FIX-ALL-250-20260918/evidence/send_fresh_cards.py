#!/usr/bin/env python3
"""WHY-SLOW-250: supersede stale cards, send fresh unambiguous cards."""
import hashlib
import json
import pathlib
import subprocess
import time

RD = pathlib.Path("/home/ari/ofn/state/revenue-drive")
NOW = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

reg = json.loads((RD / "owner-ask-registry.json").read_text(encoding="utf-8"))
cards = reg["cards"]

# 1. supersede stale/unresolved cards (so nothing double-fires later)
pkt = []
for did in ("d3c0fdea", "2d90365e"):
    c = cards.get(did) or {}
    for p in (c.get("packets") or []):
        if p not in pkt:
            pkt.append(p)
for did in ("d3c0fdea", "2d90365e", "b3417ba8"):
    c = cards.get(did)
    if c and c.get("state") == "PENDING":
        c["state"] = "SUPERSEDED"
        c["resolved_at"] = NOW
        c["superseded_by"] = "MONEY-BATCH-FRESH" if did != "b3417ba8" else "WHYSLOW-ZIMAN-HOLD2"
(RD / "owner-ask-registry.json").write_text(
    json.dumps(reg, indent=1, sort_keys=True) + "\n", encoding="utf-8")
with (RD / "receipts.jsonl").open("a", encoding="utf-8") as fh:
    fh.write(json.dumps({"schema": "octopus.owner-ask.supersede.v1", "at": NOW,
                         "cards": ["d3c0fdea", "2d90365e", "b3417ba8"],
                         "why": "stale/ambiguous cards replaced by fresh unambiguous cards "
                                "(WHY-SLOW-250 debug 2026-09-18)"}, sort_keys=True) + "\n")
print("superseded 3 cards; union packets:", len(pkt), pkt)

# 2. fresh items
rv = json.loads((RD / "owner-review.json").read_text(encoding="utf-8"))
have = {str(i.get("id")) for i in rv.get("items", [])}
new = [
    {"id": "MONEY-BATCH", "at": NOW, "priority": 1, "packets": pkt,
     "why": ("کارت تازه و نهایی — جای دو کارت قدیمی MONEY-BATCH را گرفت. "
             "%d بستهٔ قیمت آماده است؛ تأیید = ارسال همین حالا از ایمیل. "
             "این آخرین سؤال قبل از اولین درآمد است."),
     "owner_one_card": []},
    {"id": "WHYSLOW-ZIMAN-HOLD2", "at": NOW, "priority": 1,
     "why": ("✅ تأییدت رسید. حالا فقط گزینه را بزن (زیمن):"),
     "owner_one_card": ["hold برداشته شود — ارسال محدود به ایمیل‌های موجود زیمن",
                        "hold بماند، دست نزن",
                        "اول ۳ ایمیل نمونه را ببینم"]},
    {"id": "WHYSLOW-DEMAND-OPT", "at": NOW, "priority": 1,
     "why": "✅ تأییدت رسید. کدام کانال تقاضا؟ (دکمهٔ گزینه را بزن):",
     "owner_one_card": ["کانال ارگانیک را خودم می‌سازم — بدون هزینه",
                        "بودجهٔ تبلیغ را تصویب می‌کنم (نیاز به تأیید هزینه)",
                        "بازار/کانال را نام می‌برم"]},
    {"id": "WHYSLOW-CALL-OPT", "at": NOW, "priority": 1,
     "why": "✅ تأییدت رسید. دربارهٔ ۲۹ سرنخ تلفنی کدام؟ (دکمهٔ گزینه را بزن):",
     "owner_one_card": ["DIDWW را بخرم (~۲۰ دلار، کارت خودم)",
                        "شمارهٔ خودم را به‌عنوان شمارهٔ کاری می‌دهم",
                        "فعلاً نه"]},
    {"id": "WHYSLOW-VOTE-OPT", "at": NOW, "priority": 1,
     "why": "✅ تأییدت رسید. بستهٔ ۲۰ رأی معلق چطور بسته شود؟ (دکمهٔ گزینه را بزن):",
     "owner_one_card": ["همه با پیش‌فرض محافظه‌کارانه بسته شود",
                        "۲۰ کارت جدا بفرست تا تک‌تک تصمیم بگیرم",
                        "فعلاً دست نزن"]},
]
rv["items"] = [i for i in rv.get("items", []) if str(i.get("id")) not in
               {"MONEY-BATCH", "WHYSLOW-ZIMAN-HOLD2", "WHYSLOW-DEMAND-OPT",
                "WHYSLOW-CALL-OPT", "WHYSLOW-VOTE-OPT"}] + new
rv["at"] = NOW
(RD / "owner-review.json").write_text(json.dumps(rv, ensure_ascii=False, indent=1),
                                      encoding="utf-8")
print("review items now:", [i.get("id") for i in rv["items"]])

# 3. send
r = subprocess.run(["python3", "state/revenue-drive/owner_ask.py"],
                   capture_output=True, text=True, cwd="/home/ari/ofn")
print("owner_ask rc:", r.returncode)
print((r.stdout or "").strip()[:700])
print((r.stderr or "").strip()[:200])
