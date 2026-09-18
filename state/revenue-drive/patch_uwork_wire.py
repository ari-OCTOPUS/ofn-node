#!/usr/bin/env python3
"""Wire owner_reply._dispatch_card to the generic action executor (U-WORK v1)."""
import hashlib
import json
import shutil
import time

TS = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
RP = "state/revenue-drive/owner_reply.py"


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


shutil.copy2(RP, RP + ".pre-uwork-" + TS)
h0 = sha(RP)
s = open(RP, encoding="utf-8").read()
old = ('    if kind == "REJECT":\n'
       '        return {"action": "rejected-by-owner"}, "رد شد — هیچ اقدامی انجام نشد."\n')
new = ('    if kind == "REJECT":\n'
       '        return {"action": "rejected-by-owner"}, "رد شد — هیچ اقدامی انجام نشد."\n'
       '    if kind == "APPROVE" and it.get("action"):\n'
       '        # U-WORK v1: unforeseen work. The card carries an action spec; the\n'
       '        # generic executor runs it (allowlist + preimage + receipt + rollback)\n'
       '        # and refuses anything outside the allowlist or beyond the red boundary.\n'
       '        import action_executor\n'
       '        _res = action_executor.execute(it.get("action") or {}, via="owner_card",\n'
       '                                       card_id=iid,\n'
       '                                       risk=str(it.get("risk") or "internal_green"))\n'
       '        return _res, (_res.get("note") or "اجرا شد.")\n')
assert s.count(old) == 1, "anchor count=%d" % s.count(old)
s = s.replace(old, new)
open(RP, "w", encoding="utf-8", newline="\n").write(s)
print("wired", h0[:16], "->", sha(RP)[:16])
json.dump({"schema": "octopus.fix-receipt.v1", "id": "UWORK-WIRE-" + TS,
           "at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "node": "138",
           "file": RP, "preimage": RP + ".pre-uwork-" + TS, "sha_before": h0,
           "sha_after": sha(RP),
           "what": "cards carrying an `action` spec now execute via action_executor "
                   "(allowlist/red-boundary/preimage/receipt/rollback); previously such "
                   "approvals were record-only (approved-no-typed-tool)",
           "rollback": "cp <preimage> <file>"},
          open("state/receipts/UWORK-WIRE-%s.json" % TS, "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("receipt written")
