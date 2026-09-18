#!/usr/bin/env python3
"""Patch send_queue.py (first anchor: draft_ready on staging) — EVENT-DRIVEN-OCTOPUS."""
import pathlib
import py_compile
import shutil
import time

p = pathlib.Path("/home/ari/ofn/state/revenue-drive/send_queue.py")
ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
orig = p.read_text(encoding="utf-8")

OLD = '    rcpt("PACKET_STAGED", packets=staged, count=len(staged), why="email-bearing packets staged for authorised send")\n'
NEW = OLD + (
    '    try:  # EVENT-DRIVEN-OCTOPUS 2026-09-18: draft_ready per staged packet\n'
    '        import sys as _es; _es.path.insert(0, "/home/ari/ofn/tools"); import octopus_events as _oe\n'
    '        for _p in staged:\n'
    '            _oe.emit("draft_ready", _p, {"src": "send_queue.stage"})\n'
    '    except Exception:\n'
    '        pass\n'
)
n = orig.count(OLD)
print("anchor count:", n)
assert n == 1, "anchor not unique/found"
bak = p.with_name(p.name + ".pre-eventbus2-" + ts)
shutil.copy2(str(p), str(bak))
p.write_text(orig.replace(OLD, NEW, 1), encoding="utf-8", newline="\n")
py_compile.compile(str(p), doraise=True)
print("PATCHED send_queue.py draft_ready (preimage %s)" % bak.name)
