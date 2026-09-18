#!/usr/bin/env python3
"""lead_enrich.py — the octopus enriches lead emails from the web BY ITSELF.

Owner order 2026-09-13: «مطمین شو اختاپوس خودش همه اینارو انجام میده اتوماتیک
براساس سیزنمون». 33 of 73 painting leads carry an email; the rest are phone-only.
This tool visits each lead's own website, extracts a mailto/email, and records it —
so the revenue loop keeps flowing with no owner involvement.

Bounded: max N leads per cycle (cursor persisted), 12s per site, no paid API.
"""
import json
import pathlib
import re
import sys
import time

sys.path.insert(0, "/home/ari/ofn/state/revenue-drive")
import web_lookup as W  # noqa: E402

ROOT = pathlib.Path("/home/ari/ofn/state/revenue-drive")
LEADS = pathlib.Path("/home/ari/ofn/tools/leads_master.json")
FOUND = ROOT / "lead-emails.jsonl"
CURSOR = ROOT / "lead-enrich-cursor.txt"
RECEIPTS = ROOT / "receipts.jsonl"
MAX_PER_CYCLE = 8
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
BAD = ("example.", "sentry", "wixpress", "@2x", ".png", ".jpg", "domain.com")


def receipt(kind, **kw):
    with RECEIPTS.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(dict(schema="octopus.lead-enrich.v1",
                                 at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                                 kind=kind, **kw), sort_keys=True,
                            ensure_ascii=False) + "\n")


leads = json.loads(LEADS.read_text(errors="replace")).get("accounts", [])
have = set()
if FOUND.exists():
    for line in FOUND.read_text(errors="replace").splitlines():
        try:
            have.add(json.loads(line)["business_name"])
        except (ValueError, KeyError):
            pass

todo = []
for a in leads:
    name = a.get("business_name")
    if not name or name in have:
        continue
    blob = " ".join(str(a.get(k) or "") for k in ("contact_channel", "notes", "website"))
    if "@" in blob:
        continue                      # already emailable
    site = str(a.get("website") or "").strip()
    if site.startswith(("http://", "https://")):
        todo.append((name, site, a.get("suburb")))

start = int(CURSOR.read_text().strip() or 0) if CURSOR.exists() else 0
# 2026-09-17 fix: a cursor past the end of todo made every later cycle a silent
# no-op (attempted:0/remaining:0). Clamp it and rescan from the top; the `have`
# set keeps re-processing idempotent.
if todo and start >= len(todo):
    start = 0
batch = todo[start:start + MAX_PER_CYCLE]
found, missed = [], []
for name, site, suburb in batch:
    r = W.fetch(site)
    if not r["ok"]:
        missed.append({"business_name": name, "reason": "site_unreachable"})
        continue
    text = r["text"]
    cands = [e for e in EMAIL.findall(text)
             if not any(b in e.lower() for b in BAD)]
    cands += [e for e in EMAIL.findall(text.replace("mailto:", " "))]
    pick = None
    if cands:
        # prefer an address on the lead's own domain
        dom = re.sub(r"^www\.", "", re.sub(r"^https?://", "", site).split("/")[0])
        same = [c for c in cands if dom.split(".")[0] in c.lower()]
        pick = (same or cands)[0]
    if pick:
        found.append({"business_name": name, "email": pick, "suburb": suburb,
                      "source": site, "strategy": r["strategy"],
                      "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
        with FOUND.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(found[-1], sort_keys=True, ensure_ascii=False) + "\n")
    else:
        missed.append({"business_name": name, "reason": "no_email_on_site"})

CURSOR.write_text(str(start + len(batch)), encoding="utf-8")
receipt("ENRICH_CYCLE", attempted=len(batch), emails_found=len(found),
        missed=len(missed), remaining_after_cursor=max(0, len(todo) - (start + len(batch))))
print(json.dumps({"attempted": len(batch), "emails_found": len(found),
                  "missed": len(missed),
                  "remaining": max(0, len(todo) - (start + len(batch)))},
                 ensure_ascii=False))
