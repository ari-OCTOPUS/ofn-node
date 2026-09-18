#!/usr/bin/env python3
"""money_executor: emit draft_ready per NEW packet (EVENT-DRIVEN-OCTOPUS 2026-09-18).

The preparer is the natural source of the `draft_ready` domain event: a new packet
file appeared. It only fires for genuinely new ids (deterministic sha id, so a repeat
run for the same lead is idempotent and silent).
"""
import pathlib
import py_compile
import shutil
import time

p = pathlib.Path("/home/ari/ofn/state/revenue-drive/money_executor.py")
ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
s = p.read_text(encoding="utf-8")

OLD = '    (PACKETS / (pid + ".json")).write_text(json.dumps(packet, indent=1,\n                                                      sort_keys=True) + "\\n", encoding="utf-8")\n    prepared.append(pid)\n'
NEW = ('    _pf = PACKETS / (pid + ".json")\n'
       '    _is_new = not _pf.exists()\n'
       '    _pf.write_text(json.dumps(packet, indent=1,\n'
       '                              sort_keys=True) + "\\n", encoding="utf-8")\n'
       '    prepared.append(pid)\n'
       '    if _is_new:\n'
       '        try:  # EVENT-DRIVEN-OCTOPUS 2026-09-18: a new draft is ready -> send chain\n'
       '            import sys as _es; _es.path.insert(0, "/home/ari/ofn/tools")\n'
       '            import octopus_events as _oe\n'
       '            _oe.emit("draft_ready", pid,\n'
       '                     {"lead": packet["lead"].get("business_name", ""), "src": "money_executor"})\n'
       '        except Exception:\n'
       '            pass\n')

print("anchor count:", s.count(OLD))
assert s.count(OLD) == 1
bak = p.with_name(p.name + ".pre-draftemit-" + ts)
shutil.copy2(str(p), str(bak))
p.write_text(s.replace(OLD, NEW, 1), encoding="utf-8", newline="\n")
py_compile.compile(str(p), doraise=True)
print("PATCHED money_executor draft_ready emit (preimage %s)" % bak.name)
