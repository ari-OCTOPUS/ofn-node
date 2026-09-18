#!/usr/bin/env python3
"""OWNER-LINK v3: option cards must NOT offer a generic approve button
(it produced ambiguous taps: owner tapped go:<did> instead of an option).
Also re-asks the CALL decision (his tap was option-less)."""
import hashlib
import json
import pathlib
import shutil
import subprocess
import sys
import time

ROOT = pathlib.Path("/home/ari/ofn")
RD = ROOT / "state/revenue-drive"
AP = RD / "owner_ask.py"
NOW = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def sha(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


shutil.copy2(AP, str(AP) + ".pre-ownerlink3-" + time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()))
h0 = sha(AP)
s = AP.read_text(encoding="utf-8")
old = ('    rows.append([{"text": go_label, "callback_data": go_data},\n'
       '                 {"text": "⛔ رد", "callback_data": "no:%s" % did},\n'
       '                 {"text": "⏸ بعداً", "callback_data": "later:%s" % did}])\n'
       '    return rows')
new = ('    if len(options) > 1:\n'
       '        # OWNER-LINK v3: no generic approve when options exist — the generic\n'
       '        # button produced option-less taps (ambiguous votes, 2026-09-18).\n'
       '        rows.append([{"text": "⛔ رد", "callback_data": "no:%s" % did},\n'
       '                     {"text": "⏸ بعداً", "callback_data": "later:%s" % did}])\n'
       '    else:\n'
       '        rows.append([{"text": go_label, "callback_data": go_data},\n'
       '                     {"text": "⛔ رد", "callback_data": "no:%s" % did},\n'
       '                     {"text": "⏸ بعداً", "callback_data": "later:%s" % did}])\n'
       '    return rows')
assert s.count(old) == 1, "anchor=%d" % s.count(old)
s = s.replace(old, new)
AP.write_text(s, encoding="utf-8", newline="\n")
print("v3 patched", h0[:16], "->", sha(AP)[:16])
json.dump({"schema": "octopus.fix-receipt.v1", "id": "OWNERLINK3-" + time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()),
           "at_utc": NOW, "node": "138", "file": str(AP),
           "sha_before": h0, "sha_after": sha(AP),
           "what": "option cards no longer render a generic approve button (ambiguous taps)",
           "rollback": "cp <preimage> <file>"},
          open(RD / ("receipts.jsonl"), "a", encoding="utf-8"),
          ensure_ascii=False)

# fresh option-only card for the CALL decision (his earlier tap had no option)
rv = json.loads((RD / "owner-review.json").read_text(encoding="utf-8"))
rv["items"] = [i for i in rv.get("items", []) if str(i.get("id")) != "WHYSLOW-CALL-OPT2"]
rv["items"].append({"id": "WHYSLOW-CALL-OPT2", "at": NOW, "priority": 1,
                    "why": "📞 تأییدت رسید ولی «کدام گزینه» مشخص نشد. فقط یکی را بزن:",
                    "owner_one_card": ["DIDWW را می‌خرم (~۲۰ دلار، کارت خودم)",
                                       "شمارهٔ خودم را به‌عنوان شمارهٔ کاری می‌دهم",
                                       "فعلاً نه"]})
(RD / "owner-review.json").write_text(json.dumps(rv, ensure_ascii=False, indent=1),
                                      encoding="utf-8")
r = subprocess.run(["python3", "state/revenue-drive/owner_ask.py"],
                   capture_output=True, text=True, cwd=str(ROOT))
print("send:", (r.stdout or "").strip()[:300])
