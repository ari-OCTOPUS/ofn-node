#!/usr/bin/env python3
"""discover_models.py — write config/discovered-models.json from official model lists.

Metadata only. Writes model ids and tier resolution. Never touches credentials.
"""
import json
import pathlib
import sys

sys.path.insert(0, "/home/ari/ofn/state/api-budget")
import providers  # noqa: E402

OUT = pathlib.Path("/home/ari/ofn/state/api-budget/config/discovered-models.json")

# tier -> ordered name fragments to prefer when the configured name is absent
PREFERENCE = {
    "deepseek": {"economy": ["flash"], "standard": ["flash"],
                 "strong": ["pro"], "reasoning": ["pro"], "frontier": ["pro"]},
}


def pick(pid, tier, ids, configured):
    frags = (PREFERENCE.get(pid) or {}).get(tier) or []
    for frag in frags:
        cands = [i for i in ids if frag in i.lower()]
        if cands:
            return sorted(cands)[-1]
    return configured


record = {}
for pid in providers.provider_ids():
    if not providers.enabled(pid):
        continue
    if not providers.REGISTRY[pid]["paid"]:
        base = providers.env().get("LOCAL_LLAMACPP_BASE_URL", "")
        record[pid] = {
            "kind": "local", "ids": [],
            "base_override": "http://192.168.0.180:8081",
            "base_note": ("env declares 127.0.0.1 which only resolves on node 180; "
                          "from 138 the local rung is reachable at 192.168.0.180:8081 "
                          "(health 200 verified)"),
            "configured_base": base,
            "tiers": {},
        }
        continue
    r = providers.list_models(pid)
    ids = r.get("ids") or []
    cfg = providers.models(pid)
    tiers, changed = {}, {}
    for tier, name in cfg.items():
        if not name:
            continue
        if ids and name not in ids:
            new = pick(pid, tier, ids, name)
            tiers[tier] = new
            changed[tier] = {"configured": name, "resolved": new}
        else:
            tiers[tier] = name
    record[pid] = {
        "kind": "paid", "ok": bool(r.get("ok")), "http_status": r.get("http_status"),
        "error": r.get("error"), "count": r.get("count"),
        "ids": ids, "tiers": tiers, "tier_changes": changed,
    }
    print("%-12s ok=%s count=%s tier_changes=%s"
          % (pid, r.get("ok"), r.get("count"), changed or "none"))

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(record, indent=1, sort_keys=True) + "\n", encoding="utf-8")
print("wrote:", OUT)
