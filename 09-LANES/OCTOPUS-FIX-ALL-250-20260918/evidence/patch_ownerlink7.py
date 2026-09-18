#!/usr/bin/env python3
"""OWNER-LINK v7: a typed approval may carry the option number:
'تأیید 6a251799 2' == tap on option 2. Without this, text approvals of
option cards recorded no choice (ambiguous vote)."""
import hashlib
import json
import pathlib
import shutil
import time

TS = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
RD = pathlib.Path("/home/ari/ofn/state/revenue-drive")
RP = RD / "owner_reply.py"


def sha(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


shutil.copy2(RP, str(RP) + ".pre-ownerlink7-" + TS)
h0 = sha(RP)
s = RP.read_text(encoding="utf-8")

old = ('                if did in raw.lower() and str(card.get("state")) == "PENDING":\n'
       '                    target = next((it for it in items\n'
       '                                   if str(it.get("id")) == str(card["id"])),\n'
       '                                  {"id": card["id"], "packets": card.get("packets") or []})\n'
       '                    used_registry = True\n'
       '                    break')
new = ('                if did in raw.lower() and str(card.get("state")) == "PENDING":\n'
       '                    target = next((it for it in items\n'
       '                                   if str(it.get("id")) == str(card["id"])),\n'
       '                                  {"id": card["id"], "packets": card.get("packets") or []})\n'
       '                    used_registry = True\n'
       '                    # OWNER-LINK v7: the typed reply may name the option number.\n'
       '                    _tail = raw.lower().replace(did, " ")\n'
       '                    _m = re.search(r"(?<![0-9a-f])([1-9])(?![0-9a-f])", _tail)\n'
       '                    if _m and kind == "APPROVE":\n'
       '                        option_chosen = _m.group(1)\n'
       '                    break')
assert s.count(old) == 1, "v7 anchor=%d" % s.count(old)
s = s.replace(old, new)
RP.write_text(s, encoding="utf-8", newline="\n")
print("v7 applied", h0[:16], "->", sha(RP)[:16])
json.dump({"schema": "octopus.fix-receipt.v1", "id": "OWNERLINK7-" + TS,
           "at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "node": "138",
           "file": str(RP), "preimage": str(RP) + ".pre-ownerlink7-" + TS,
           "sha_before": h0, "sha_after": sha(RP),
           "what": "typed approval can carry the option number (exact callback equivalence)",
           "rollback": "cp <preimage> <file>"},
          open(RD / "receipts.jsonl", "a", encoding="utf-8"), ensure_ascii=False)
print("receipt appended")
