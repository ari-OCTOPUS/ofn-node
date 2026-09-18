#!/usr/bin/env python3
"""Patch send_queue.py: explicit per-run batch cap 25 (owner guard) — EVENT-DRIVEN-OCTOPUS."""
import pathlib
import py_compile
import shutil
import time

p = pathlib.Path("/home/ari/ofn/state/revenue-drive/send_queue.py")
ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
orig = p.read_text(encoding="utf-8")

OLD_C = 'NOW = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())\n'
NEW_C = OLD_C + (
    '# EVENT-DRIVEN-OCTOPUS 2026-09-18: owner guard "batch of 25 per run" made explicit —\n'
    '# the daily cap stays 60 (channel-authorization); a bug can no longer blast the list\n'
    '# in one event-triggered run.\n'
    'MAX_PER_RUN = 25\n'
)
OLD_P = ('pkts = [p.stem for p in sorted(QUEUE.glob("QP-*.json"))\n'
         '        if p.stem not in already and p.stem not in terminal_now][:room]\n')
NEW_P = ('pkts = [p.stem for p in sorted(QUEUE.glob("QP-*.json"))\n'
         '        if p.stem not in already and p.stem not in terminal_now][:min(room, MAX_PER_RUN)]\n')

assert orig.count(OLD_C) == 1, "const anchor %d" % orig.count(OLD_C)
assert orig.count(OLD_P) == 1, "slice anchor %d" % orig.count(OLD_P)
new = orig.replace(OLD_C, NEW_C, 1).replace(OLD_P, NEW_P, 1)
bak = p.with_name(p.name + ".pre-batchcap-" + ts)
shutil.copy2(str(p), str(bak))
p.write_text(new, encoding="utf-8", newline="\n")
py_compile.compile(str(p), doraise=True)
print("PATCHED send_queue.py batch-cap (preimage %s)" % bak.name)
