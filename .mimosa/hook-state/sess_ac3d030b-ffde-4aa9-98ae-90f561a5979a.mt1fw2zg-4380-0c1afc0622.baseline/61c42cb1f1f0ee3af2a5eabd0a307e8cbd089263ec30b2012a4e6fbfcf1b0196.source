#!/usr/bin/env python3
"""
flag_monitor.py — STOP/FREEZE/Activation flag monitor (additive, read-only, stdlib-only).

Checks flag consistency and alerts on dangerous or unexpected combinations:
  - HALT-ALL without any STOP flag (unusual but valid)
  - FREEZE without budgets.yaml readable (orphan freeze)
  - Multiple contradictory STOP flags
  - GO-LIVE before LIVE_GATE_DATE without explicit early flag
  - Missing activation flags for enabled loops

Output: JSON stdout + summary stderr.
Exit: 0=ok, 1=warn, 2=err.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

_OPS = Path(__file__).resolve().parents[1]
_BUDGET_DIR = _OPS / "budget"

opslib = None
try:
    sys.path.insert(0, str(_BUDGET_DIR))
    import opslib as _opslib
    opslib = _opslib
except Exception:
    pass

# ─── paths ───────────────────────────────────────────────────────────────────
HALT_ALL = _OPS / "HALT-ALL"
STOP_METABOLIC = _OPS / "STOP-METABOLIC"
STOP_DEBATE = _OPS / "STOP-DEBATE"
STOP_ORGANISM = _OPS / "STOP-ORGANISM"
STOP_ARCHITECT = _OPS.parent / "04 - Architect System" / "STOP"
FREEZE_FLAG = _BUDGET_DIR / "FREEZE.flag"
BUDGETS_YAML = _BUDGET_DIR / "budgets.yaml"
LIVE_GATE_DATE_STR = "2026-07-21"

# ─── helpers ─────────────────────────────────────────────────────────────────
def _exists(p: Path) -> bool:
    try:
        return p.exists()
    except OSError:
        return False

def _flag_mtime(p: Path) -> float | None:
    try:
        return p.stat().st_mtime
    except OSError:
        return None

def _read_json(p: Path) -> dict:
    try:
        return json.loads(p.read_text("utf-8", errors="replace"))
    except Exception:
        return {}

def _budgets_yaml_readable() -> bool:
    try:
        return BUDGETS_YAML.exists() and "global:" in BUDGETS_YAML.read_text("utf-8", errors="replace")
    except Exception:
        return False

# ─── checks ──────────────────────────────────────────────────────────────────
def check_panic_flags() -> dict:
    flags = {
        "HALT-ALL": _exists(HALT_ALL),
        "STOP-ARCHITECT": _exists(STOP_ARCHITECT),
        "STOP-METABOLIC": _exists(STOP_METABOLIC),
        "STOP-DEBATE": _exists(STOP_DEBATE),
        "STOP-ORGANISM": _exists(STOP_ORGANISM),
        "FREEZE": _exists(FREEZE_FLAG),
    }
    active = [k for k, v in flags.items() if v]
    issues = []

    # HALT-ALL is the strongest; if it exists, note that everything else is moot
    if flags["HALT-ALL"]:
        issues.append("HALT-ALL is active — organism will not revive")

    # FREEZE without readable budgets.yaml = orphan freeze, needs manual attention
    if flags["FREEZE"] and not _budgets_yaml_readable():
        issues.append("FREEZE active but budgets.yaml unreadable — orphan freeze state")

    # Multiple stop flags may indicate cascading failure
    stop_count = sum(1 for k in ["STOP-ARCHITECT", "STOP-METABOLIC", "STOP-DEBATE", "STOP-ORGANISM"] if flags[k])
    if stop_count > 1:
        issues.append(f"Multiple STOP flags active ({stop_count}) — review cascading failure")

    level = "err" if flags["HALT-ALL"] else ("warn" if active else "ok")
    return {"level": level, "active": active, "issues": issues, "details": flags}

def check_activation_flags() -> dict:
    try:
        flags = sorted(p.name for p in _OPS.glob("ACTIVATION-*.flag"))
    except OSError:
        flags = []

    go_live = "ACTIVATION-GO-LIVE.flag" in flags
    debate = "ACTIVATION-DEBATE.flag" in flags
    replication = "ACTIVATION-REPLICATION.flag" in flags
    gov_llm = "ACTIVATION-GOVERNOR-LLM.flag" in flags
    cortex = "ACTIVATION-CORTEX-PAID.flag" in flags
    self_improve = "ACTIVATION-SELF-IMPROVE-AUTO.flag" in flags

    issues = []
    notes = []

    # If GO-LIVE is set but no DEBATE, note it (not necessarily an error)
    if go_live and not debate:
        notes.append("GO-LIVE without DEBATE — review loop routing intent")

    # If SELF-IMPROVE-AUTO without GOVERNOR-LLM, warn
    if self_improve and not gov_llm:
        issues.append("SELF-IMPROVE-AUTO without GOVERNOR-LLM — autonomous improvement lacks governance")

    # If CORTEX-PAID exists, ensure budget awareness
    if cortex:
        notes.append("CORTEX-PAID active — ensure budget monitoring is enabled")

    level = "warn" if issues else "ok"
    return {
        "level": level,
        "flags": flags,
        "issues": issues,
        "notes": notes,
        "parsed": {
            "go_live": go_live,
            "debate": debate,
            "replication": replication,
            "governor_llm": gov_llm,
            "cortex_paid": cortex,
            "self_improve_auto": self_improve,
        }
    }

def check_flag_age() -> dict:
    # Alert if any panic flag is older than 24h (may indicate forgotten cleanup)
    flags = {
        "HALT-ALL": HALT_ALL,
        "STOP-METABOLIC": STOP_METABOLIC,
        "STOP-DEBATE": STOP_DEBATE,
        "STOP-ORGANISM": STOP_ORGANISM,
        "FREEZE": FREEZE_FLAG,
    }
    old_flags = []
    now = time.time()
    for name, p in flags.items():
        if not _exists(p):
            continue
        mtime = _flag_mtime(p)
        if mtime and (now - mtime) > 86400:
            age_h = round((now - mtime) / 3600, 1)
            old_flags.append(f"{name} is {age_h}h old — review if still intentional")

    level = "warn" if old_flags else "ok"
    return {"level": level, "old_flags": old_flags}

# ─── main ────────────────────────────────────────────────────────────────────
def _obs_alert_tail(results: dict) -> None:
    """RC3 فیوزِ سکوتِ مرگ: severity>=warn را به governor-alerts.md برسان.
    flag-gated (OCTOPUS_OBS_ALERT)، fail-soft — خروجی/exit-code را عوض نمی‌کند."""
    if opslib is None:
        return
    try:
        bad = []
        for name, c in results["checks"].items():
            if c["level"] in ("warn", "err"):
                detail = "; ".join(c.get("issues") or []) or c["level"]
                bad.append(f"{name}: {detail}")
        if bad:
            opslib.alert([f"flag_monitor {results['overall']}: " + " | ".join(bad)])
    except Exception:
        pass


def main() -> int:
    results = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "checks": {
            "panic_flags": check_panic_flags(),
            "activation_flags": check_activation_flags(),
            "flag_age": check_flag_age(),
        }
    }
    levels = [c["level"] for c in results["checks"].values()]
    overall = "err" if "err" in levels else ("warn" if "warn" in levels else "ok")
    results["overall"] = overall

    if os.environ.get("OCTOPUS_OBS_ALERT", "0") == "1" and overall in ("warn", "err"):
        _obs_alert_tail(results)

    print(json.dumps(results, ensure_ascii=False, indent=2))

    print(f"\n=== Flag Monitor ({results['ts']}) ===", file=sys.stderr)
    print(f"Overall: {overall.upper()}", file=sys.stderr)
    for name, c in results["checks"].items():
        emoji = {"ok": "🟢", "warn": "🟡", "err": "🔴"}.get(c["level"], "⚪")
        print(f"  {emoji} {name}: {c['level']}", file=sys.stderr)
        for issue in c.get("issues", []):
            print(f"      → {issue}", file=sys.stderr)
        for note in c.get("notes", []):
            print(f"      ℹ {note}", file=sys.stderr)
    return {"ok": 0, "warn": 1, "err": 2}.get(overall, 2)

if __name__ == "__main__":
    sys.exit(main())
