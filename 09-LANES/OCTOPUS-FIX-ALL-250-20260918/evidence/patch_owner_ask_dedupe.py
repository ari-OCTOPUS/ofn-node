#!/usr/bin/env python3
"""Fix owner_ask dedupe key: hourly key silently dropped a genuinely-new card
sent in the same hour. Replace with content-addressed key (id + why + packets +
options) so: regenerated identical cards stay suppressed, changed cards send."""
import hashlib
import json
import shutil
import time

TS = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
AP = "state/revenue-drive/owner_ask.py"


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


shutil.copy2(AP, AP + ".pre-whyslow250-dedup-" + TS)
h0 = sha(AP)
s = open(AP, encoding="utf-8").read()

old = '        key = "%s@%s" % (iid, str(it.get("at", ""))[:13])'
new = ('        # content-addressed dedupe (WHY-SLOW-250 debug 2026-09-18): the old\n'
       '        # hourly key silently dropped a genuinely-new card sent in the same\n'
       '        # hour; identical regenerated cards still stay suppressed.\n'
       '        _ck = policy_hash(json.dumps([iid, str(it.get("why", "")),\n'
       '                                      [str(p) for p in (it.get("packets") or [])],\n'
       '                                      [str(o) for o in (it.get("owner_one_card") or [])]],\n'
       '                                     sort_keys=True, ensure_ascii=False))\n'
       '        key = "%s@%s" % (iid, _ck)')
assert s.count(old) == 1, "key anchor count=%d" % s.count(old)
s = s.replace(old, new)
open(AP, "w", encoding="utf-8", newline="\n").write(s)
print("dedupe-key patch applied", h0[:16], "->", sha(AP)[:16])
rec = {"schema": "octopus.fix-receipt.v1", "id": "WHYSLOW250-DEDUP-" + TS,
       "at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "node": "138",
       "lane": "OCTOPUS-FIX-ALL-250-20260918/debug-owner-reply",
       "file": AP, "preimage": AP + ".pre-whyslow250-dedup-" + TS,
       "sha_before": h0, "sha_after": sha(AP),
       "what": "content-addressed send-dedupe key (was hourly-granular and dropped new cards)",
       "rollback": "cp <preimage> <file>"}
json.dump(rec, open("state/receipts/WHYSLOW250-DEDUP-%s.json" % TS, "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("receipt written")
