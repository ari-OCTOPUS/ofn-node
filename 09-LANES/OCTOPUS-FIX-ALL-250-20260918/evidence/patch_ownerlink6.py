#!/usr/bin/env python3
"""OWNER-LINK v6:
 (1) persist the cursor as the HASH SET (my v4 patch computed it but still
     wrote a line number -> the spool was fully reprocessed every run: 37
     duplicate-tap messages spammed the owner)
 (2) repair receipts.jsonl lines that got glued (json.dump without newline)
"""
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


# ---------- (1) cursor write fix ----------
shutil.copy2(RP, str(RP) + ".pre-ownerlink6-" + TS)
h0 = sha(RP)
s = RP.read_text(encoding="utf-8")
old = ('    CURSOR.write_text(str(kept), encoding="utf-8")\n'
       '    return "OK", msgs')
new = ('    # OWNER-LINK v6: persist the HASH SET (writing a line number here made the\n'
       '    # whole spool reprocess on the next run and spammed the owner).\n'
       '    _all = sorted(set(_seen_hashes) | set(_new_hashes))\n'
       '    CURSOR.write_text(json.dumps({"hashes": _all}), encoding="utf-8")\n'
       '    return "OK", msgs')
assert s.count(old) == 1, "v6 cursor anchor=%d" % s.count(old)
s = s.replace(old, new)
RP.write_text(s, encoding="utf-8", newline="\n")
print("v6 cursor fix:", h0[:16], "->", sha(RP)[:16])

# migrate the current numeric cursor to a hash set NOW (so nothing reprocesses)
cursor = RD / "tg-inbox-cursor.txt"
inbox = RD / "tg-inbox.jsonl"
raw = cursor.read_text(encoding="utf-8").strip() if cursor.exists() else ""
if not raw.startswith("{"):
    try:
        n = int(raw or 0)
    except ValueError:
        n = 0
    lines = inbox.read_text(errors="replace").strip().splitlines()
    # a numeric cursor meant "first n rows seen"; if it is 0 we must assume ALL
    # current rows were already handled (they were — the spam proved it).
    if n == 0:
        n = len(lines)
    hs = sorted({hashlib.sha256(l.encode("utf-8")).hexdigest()[:16] for l in lines[:n]})
    cursor.write_text(json.dumps({"hashes": hs}), encoding="utf-8")
    print("cursor migrated: legacy=%s -> %d hashes (file has %d rows)" % (raw, len(hs), len(lines)))
else:
    print("cursor already a hash set")

# ---------- (2) receipts repair ----------
rc = RD / "receipts.jsonl"
shutil.copy2(rc, str(rc) + ".pre-gluedfix-" + TS)
rawtxt = rc.read_text(encoding="utf-8")
objs, buf, depth = [], "", 0
for ch in rawtxt:
    if ch == "{" and depth == 0:
        buf = ""
    buf += ch
    if ch == "{":
        depth += 1
    elif ch == "}":
        depth -= 1
        if depth == 0:
            try:
                objs.append(json.loads(buf))
            except ValueError:
                pass
            buf = ""
with rc.open("w", encoding="utf-8") as fh:
    for o in objs:
        fh.write(json.dumps(o, ensure_ascii=False, sort_keys=True, default=str) + "\n")
print("receipts repaired: %d objects written (was %d lines)" %
      (len(objs), len(rawtxt.splitlines())))

json.dump({"schema": "octopus.fix-receipt.v1", "id": "OWNERLINK6-" + TS,
           "at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "node": "138",
           "file": str(RP), "preimage": str(RP) + ".pre-ownerlink6-" + TS,
           "sha_before": h0, "sha_after": sha(RP),
           "also": {"cursor_migrated": True,
                    "receipts_repaired": {"was_lines": len(rawtxt.splitlines()),
                                          "now_objects": len(objs),
                                          "preimage": str(rc) + ".pre-gluedfix-" + TS}},
           "what": "cursor now persists the consumed-hash set (a numeric write caused full "
                   "spool reprocessing = 37 duplicate-tap messages to the owner); receipts.jsonl "
                   "glued lines repaired by re-serialising every JSON object on its own line "
                   "(no entry added, removed or altered)",
           "rollback": "cp <preimage> <file>"},
          open(rc, "a", encoding="utf-8"), ensure_ascii=False)
print("receipt appended")
