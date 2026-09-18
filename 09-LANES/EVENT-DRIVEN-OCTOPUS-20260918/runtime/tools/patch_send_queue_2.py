#!/usr/bin/env python3
"""Patch send_queue.py (second anchor) — EVENT-DRIVEN-OCTOPUS 2026-09-18."""
import pathlib
import py_compile
import shutil
import time

p = pathlib.Path("/home/ari/ofn/state/revenue-drive/send_queue.py")
ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
orig = p.read_text(encoding="utf-8")

OLD = '    with SENTLOG.open("a", encoding="utf-8") as f:\n        f.write(json.dumps(rec, sort_keys=True) + "\\n")\n'
NEW = OLD + (
    '    try:  # EVENT-DRIVEN-OCTOPUS 2026-09-18: packet_sent/packet_failed\n'
    '        import sys as _es; _es.path.insert(0, "/home/ari/ofn/tools"); import octopus_events as _oe\n'
    '        _oe.emit("packet_sent" if p in sent_ids else "packet_failed", p,\n'
    '                 {"payload_sha16": h, "outcome": rec["outcome"], "src": "send_queue"})\n'
    '    except Exception:\n'
    '        pass\n'
)

n = orig.count(OLD)
print("anchor count:", n)
assert n == 1, "anchor not unique/found"
bak = p.with_name(p.name + ".pre-eventbus-" + ts)
shutil.copy2(str(p), str(bak))
p.write_text(orig.replace(OLD, NEW, 1), encoding="utf-8", newline="\n")
py_compile.compile(str(p), doraise=True)
print("PATCHED send_queue.py (preimage %s)" % bak.name)
