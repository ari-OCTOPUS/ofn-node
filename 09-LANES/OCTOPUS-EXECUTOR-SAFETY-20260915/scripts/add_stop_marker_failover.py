#!/usr/bin/env python3
"""Add operator stop-marker support to provider_failover on node 138."""
from pathlib import Path

p = Path('/home/ari/ofn/state/api-budget/provider_failover.py')
t = p.read_text(encoding='utf-8')
anchor = """        entry = rec.get(pid) or {}
        if not (providers.enabled(pid) and providers.key_present(pid)):"""
new = """        entry = rec.get(pid) or {}
        # operator stop-marker: config/STOP-<PROVIDER> pins a cooldown without
        # editing the registry (for account-level chat-only quota walls where
        # the free models endpoint still answers 200, e.g. fugu).
        _stop = HEALTH_FILE.parent / ("STOP-" + pid.upper())
        if _stop.exists():
            entry.update({"status": "OPERATOR_STOPPED", "checked_at": _iso(),
                          "cooldown_until": _iso(_now() + 6 * 3600)})
            rec[pid] = entry
            continue
        if not (providers.enabled(pid) and providers.key_present(pid)):"""
if 'OPERATOR_STOPPED' in t:
    print('already patched')
else:
    assert t.count(anchor) == 1, t.count(anchor)
    p.write_text(t.replace(anchor, new), encoding='utf-8', newline='\n')
    print('marker support added')
