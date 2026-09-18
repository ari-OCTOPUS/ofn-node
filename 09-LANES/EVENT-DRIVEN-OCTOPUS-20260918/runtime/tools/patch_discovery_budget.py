#!/usr/bin/env python3
"""Patch discovery_runner.py: idle-trigger budget guard (same daily budget as the 02:40Z timer).

EVENT-DRIVEN-OCTOPUS 2026-09-18 (Phase 4). The runner stays byte-identical in what it
does; it now refuses to harvest more often than MIN_INTERVAL_S unless the lead bank is
actually stale/empty. Receipted either way (never a silent no-op).
"""
import pathlib
import py_compile
import shutil
import time

p = pathlib.Path("/home/ari/ofn/state/revenue-drive/discovery_runner.py")
ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
orig = p.read_text(encoding="utf-8")

OLD = 'def main():\n    if (RD / "SEND-PAUSED").exists():\n        rcp("DISCOVERY_SKIPPED", why="paused"); return\n'
NEW = (
    'MIN_INTERVAL_S = 4 * 3600  # idle-triggered discovery keeps the same daily budget as the old 02:40Z timer\n'
    'STALE_LEADS = 40           # below this many email-ready leads the bank counts as stale -> harvest now\n'
    '\n'
    '\n'
    'def _last_harvest_age():\n'
    '    try:\n'
    '        n = 0\n'
    '        for line in (RD / "receipts.jsonl").read_text(errors="replace").splitlines():\n'
    '            if \'"DISCOVERY_HARVEST"\' in line:\n'
    '                n = line\n'
    '        if not n:\n'
    '            return None\n'
    '        import json as _j, datetime as _dt\n'
    '        at = _j.loads(n).get("at", "")\n'
    '        t = _dt.datetime.strptime(at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=_dt.timezone.utc)\n'
    '        return (time.time() - t.timestamp())\n'
    '    except Exception:\n'
    '        return None\n'
    '\n'
    '\n'
    'def _emails_ready():\n'
    '    try:\n'
    '        return sum(1 for _ in (RD / "lead-emails.jsonl").open(encoding="utf-8"))\n'
    '    except Exception:\n'
    '        return 0\n'
    '\n'
    '\n'
    'def main():\n'
    '    if (RD / "SEND-PAUSED").exists():\n'
    '        rcp("DISCOVERY_SKIPPED", why="paused"); return\n'
    '    _age = _last_harvest_age()\n'
    '    if _age is not None and _age < MIN_INTERVAL_S and _emails_ready() >= STALE_LEADS:\n'
    '        rcp("DISCOVERY_SKIPPED_FRESH", age_s=int(_age), emails_ready=_emails_ready(),\n'
    '            min_interval_s=MIN_INTERVAL_S)\n'
    '        print(json.dumps({"skipped": "fresh", "age_s": int(_age)}))\n'
    '        return\n'
    '    rcp("DISCOVERY_TRIGGERED", idle_age_s=None if _age is None else int(_age),\n'
    '        emails_ready=_emails_ready(), src="idle-beat")\n'
)
assert orig.count(OLD) == 1, "anchor %d" % orig.count(OLD)
new = orig.replace(OLD, NEW, 1)
bak = p.with_name(p.name + ".pre-budget-" + ts)
shutil.copy2(str(p), str(bak))
p.write_text(new, encoding="utf-8", newline="\n")
py_compile.compile(str(p), doraise=True)
print("PATCHED discovery_runner.py budget guard (preimage %s)" % bak.name)
