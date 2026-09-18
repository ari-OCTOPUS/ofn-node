#!/usr/bin/env python3
"""Fix send_queue.py crash: receipts may carry a BOOLEAN "sent" (e.g. OWNER_BATCH_* rows).

EVENT-DRIVEN-OCTOPUS 2026-09-18. Found live: the 06:54:05Z receipt
{"kind":"OWNER_BATCH_20260918B","sent":true, ...} made every later send_queue run
die with `TypeError: 'bool' object is not iterable` at the `already` scan — i.e. the
whole send cycle was blocked since 06:54Z (the owner's 12:00Z wave would have failed
too). Fix: only iterate when the field really is a collection.
"""
import pathlib
import py_compile
import shutil
import time

p = pathlib.Path("/home/ari/ofn/state/revenue-drive/send_queue.py")
ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
orig = p.read_text(encoding="utf-8")

OLD = '        for pk in (r.get("sent") or []):\n            already.add(pk)\n'
NEW = ('        _sent = r.get("sent")\n'
       '        if isinstance(_sent, (list, dict, set, tuple)):  # bool rows exist (OWNER_BATCH_*)\n'
       '            for pk in _sent:\n'
       '                already.add(pk)\n')
assert orig.count(OLD) == 1, "anchor %d" % orig.count(OLD)
bak = p.with_name(p.name + ".pre-sentboolfix-" + ts)
shutil.copy2(str(p), str(bak))
p.write_text(orig.replace(OLD, NEW, 1), encoding="utf-8", newline="\n")
py_compile.compile(str(p), doraise=True)
print("FIXED send_queue.py bool-sent crash (preimage %s)" % bak.name)
