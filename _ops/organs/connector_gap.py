# -*- coding: utf-8 -*-
"""CONNECTOR-GAP advisory organ beat (U02 close).

Gated by WIRING flags.connector_gap_hook.
Read-only load of CONNECTOR-GAP-REGISTRY via evidence_plane.connector_gap_loader.
Advisory only: never invents OAuth, never claims LIVE connectors, metrics_allowed=false.
U04 GA4/GSC/Ads OAuth remains WAITING_OWNER_OAUTH / owner HOLD.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

from .flags import enabled, load_wiring
from .paths import ORGANS_STATE, assert_not_telegram

HOOK_FLAG = "connector_gap_hook"


def _ensure_ops_path() -> Path:
    ops = Path(__file__).resolve().parent.parent
    if str(ops) not in sys.path:
        sys.path.insert(0, str(ops))
    return ops


def beat(*, emit: bool = True, state_root: Path | None = None) -> dict[str, Any]:
    """Advisory consumer for connector_gap_hook.

    Returns flag-off when disarmed. When armed: load registry, mark OAuth gaps,
    write advisory sidecar. Never enables metrics or LIVE connector claims.
    """
    if not enabled(HOOK_FLAG, False):
        return {
            "ok": False,
            "reason": "flag-off",
            "hook": HOOK_FLAG,
            "consumer_fired": False,
            "flag_drift": False,
            "live_connectors_claimed": False,
            "metrics_allowed": False,
        }

    _ensure_ops_path()
    from evidence_plane.connector_gap_loader import mark_oauth_gaps, load_registry

    wiring = load_wiring()
    hook_meta = ((wiring.get("hooks") or {}).get("connector_gap") or {})
    reg_path = hook_meta.get("registry")

    try:
        registry = load_registry(reg_path) if reg_path else load_registry()
        marked = mark_oauth_gaps(registry)
    except FileNotFoundError as e:
        return {
            "ok": False,
            "reason": "registry-missing",
            "error": str(e),
            "hook": HOOK_FLAG,
            "consumer_fired": True,
            "flag_drift": False,
            "live_connectors_claimed": False,
            "metrics_allowed": False,
        }

    oauth_gaps = marked.get("oauth_gaps") or []
    all_waiting = all(
        (g.get("status") == "WAITING_OWNER_OAUTH") or g.get("is_gap")
        for g in oauth_gaps
    )
    any_metrics = any(bool(g.get("metrics_allowed")) for g in oauth_gaps)

    out: dict[str, Any] = {
        "ok": True,
        "hook": HOOK_FLAG,
        "consumer": "organs.connector_gap.beat",
        "mode": "advisory",
        "consumer_fired": True,
        "flag_drift": False,
        "live_connectors_claimed": False,
        "metrics_allowed": False if not any_metrics else False,  # hard false
        "oauth_hold_u04": True,
        "all_oauth_gaps_waiting": all_waiting,
        "as_of_registry": marked.get("as_of_registry"),
        "loaded_from": marked.get("loaded_from"),
        "oauth_gaps": oauth_gaps,
        "hard_rules": marked.get("hard_rules") or [],
        "gap_ids": [g.get("gap_id") for g in oauth_gaps if g.get("gap_id")],
        "do_not": [
            "invent_oauth_credentials",
            "claim_LIVE_connectors",
            "enable_metrics_before_owner_oauth",
            "automate_GA4_GSC_Ads",
        ],
        "stamp_unix": time.time(),
        "module": hook_meta.get("module"),
        "enabled_flag": hook_meta.get("enabled_flag") or HOOK_FLAG,
    }
    # Force metrics_allowed false on nested gaps (defense in depth)
    for g in out["oauth_gaps"]:
        if isinstance(g, dict):
            g["metrics_allowed"] = False
            g["live_claimed"] = False

    if emit:
        root = Path(state_root) if state_root is not None else ORGANS_STATE
        root.mkdir(parents=True, exist_ok=True)
        path = root / "connector-gap-advisory.json"
        assert_not_telegram(path)
        path.write_text(json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        out["advisory_path"] = str(path)

    return out


if __name__ == "__main__":
    print(json.dumps(beat(), indent=2, default=str))
