#!/usr/bin/env python3
"""U-WORK v1 acceptance test — 4 cases:
T1 internal_green write_file      -> auto-executed (file + receipt + preimage)
T2 red_external proposal          -> NOT executed; card item with action spec
T3 owner tap on that card         -> executed via generic executor
T4 disallowed type + path escape  -> ACTION_NOT_ALLOWED / PATH_OUTSIDE_ALLOWED_ROOTS
"""
import json
import pathlib
import subprocess
import sys
import time

ROOT = pathlib.Path("/home/ari/ofn")
RD = ROOT / "state/revenue-drive"
sys.path.insert(0, str(RD))
import proposal_intake  # noqa: E402

NOW = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
print("== T1 inner-green write_file ==")
r1 = proposal_intake.submit({
    "title": "ثبت فایل نمای وضعیت U-WORK",
    "why": "تست خودآدرس: نوشتن فایل داخلی برگشت‌پذیر",
    "action": {"type": "write_file",
               "args": {"path": "state/revenue-drive/uwork-probe.txt",
                        "content": "U-WORK probe %s\n" % NOW}},
    "risk": "internal_green", "reversible": True, "source": "acceptance-test"})
print(json.dumps(r1, ensure_ascii=False)[:400])
p = RD / "uwork-probe.txt"
print("probe file exists:", p.exists(), "| content ok:", "U-WORK probe" in p.read_text())

print("\n== T2 red boundary -> card, not executed ==")
r2 = proposal_intake.submit({
    "title": "نصب ابزار X روی نود ۱۸۰",
    "why": "تست خودآدرس: اثر بیرونی/مرز سرخ باید کارت مالک بگیرد",
    "action": {"type": "install_package", "args": {"pkg": "x", "host": "180"}},
    "risk": "red_external", "reversible": False, "source": "acceptance-test"})
print(json.dumps(r2, ensure_ascii=False)[:400])

print("\n== T4 refusals ==")
r4a = proposal_intake.submit({
    "title": "نوع ناشناخته", "why": "تست allowlist",
    "action": {"type": "teleport", "args": {}}, "risk": "internal_green"})
print("disallowed:", json.dumps(r4a, ensure_ascii=False)[:260])
r4b = proposal_intake.submit({
    "title": "فرار از مسیر", "why": "تست path escape",
    "action": {"type": "write_file", "args": {"path": "/etc/passwd", "content": "x"}},
    "risk": "internal_green"})
print("escape:", json.dumps(r4b, ensure_ascii=False)[:260])

print("\n== T3 owner tap executes the red-boundary card (simulated tap) ==")
pid = r2["id"]
rv = json.loads((RD / "owner-review.json").read_text(encoding="utf-8"))
it = next(i for i in rv["items"] if str(i.get("id")) == pid)
print("card carries action:", json.dumps(it.get("action"), ensure_ascii=False)[:120])
# simulate approval through the real dispatcher
sys.path.insert(0, str(RD))
import owner_reply  # noqa: E402
acted, note = owner_reply._dispatch_card(it, "APPROVE", "tap", None)
print("dispatch result:", json.dumps(acted, ensure_ascii=False)[:300])
print("note:", note)

print("\n== receipts tail ==")
rows = [json.loads(l) for l in (RD / "receipts.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
for r in rows[-6:]:
    print("  ", r.get("at"), r.get("kind"), str(r.get("type") or r.get("id") or "")[:30],
          str(r.get("reason") or r.get("ok") or "")[:30])
