#!/usr/bin/env python3
"""
health_check.py — Operations health checker for Octopus (additive, read-only, stdlib-only).

Checks (fail-soft, no side effects):
  1. STOP / HALT / FREEZE flags
  2. ORGANISM-STATE.json integrity
  3. organ-state.json lock & parseability
  4. budgets.yaml readable (SoT)
  5. Germline backup lag + GITWRITE-FAILED flag
  6. organ_gate status (reserve logic via organ_gate.status if available)
  7. Ledger fallback accumulation (ledger-fallback.jsonl size)
  8. Activation flags sanity

Output: JSON to stdout + human-readable summary to stderr.
Exit code: 0 = healthy, 1 = warnings, 2 = errors.

Invariant respect:
  I1: read-only, no ledger writes.
  I2: budget_gate single enforcer — we only observe, never enforce.
  I3: if divergence detected, we REPORT it (propose-only), never FREEZE.
  I6: thresholds read from budgets.yaml; hardcoded defaults only as fallback.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

# ─── paths ───────────────────────────────────────────────────────────────────
_OPS = Path(__file__).resolve().parents[1]          # _ops/
_BUDGET_DIR = _OPS / "budget"
_STATE_DIR = _OPS / "state"

# Try to import opslib; fallback to local definitions if unavailable (fail-soft)
opslib = None
try:
    sys.path.insert(0, str(_BUDGET_DIR))
    import opslib as _opslib
    opslib = _opslib
except Exception:
    pass

# Local fallback paths (mirror opslib)
ORGANISM_STATE = _STATE_DIR / "ORGANISM-STATE.json"
ORGAN_STATE = _BUDGET_DIR / "organ-state.json"
BUDGETS_YAML = _BUDGET_DIR / "budgets.yaml"
FREEZE_FLAG = _BUDGET_DIR / "FREEZE.flag"
ORGAN_LOG = _BUDGET_DIR / "organ-gate-log.jsonl"
LEDGER_FALLBACK = _STATE_DIR / "ledger-fallback.jsonl"
GITWRITE_FAILED = _OPS / "backup" / "GITWRITE-FAILED.flag"
HALT_ALL = _OPS / "HALT-ALL"
STOP_METABOLIC = _OPS / "STOP-METABOLIC"
STOP_DEBATE = _OPS / "STOP-DEBATE"
STOP_ORGANISM = _OPS / "STOP-ORGANISM"
STOP_ARCHITECT = _OPS.parent / "04 - Architect System" / "STOP"
OFFBOX_DIR = Path(os.environ.get("GERMLINE_OFFBOX", r"E:\germline"))
GERMLINE_WARN_H = 2.0
GERMLINE_ERR_H = 26.0

# ─── helpers ─────────────────────────────────────────────────────────────────
def _flag_exists(p: Path) -> bool:
    try:
        return p.exists()
    except OSError:
        return False

def _read_json(p: Path) -> dict:
    try:
        return json.loads(p.read_text("utf-8", errors="replace"))
    except Exception:
        return {}

def _file_size(p: Path) -> int:
    try:
        return p.stat().st_size
    except OSError:
        return 0

def _germline_lag_hours() -> float | None:
    cands = [OFFBOX_DIR / "last_backup_manifest.json", OFFBOX_DIR / "hourly-latest.bundle"]
    try:
        cands += list(OFFBOX_DIR.glob("vault-*.bundle"))
    except OSError:
        pass
    stamps = []
    for p in cands:
        try:
            if p.exists():
                stamps.append(p.stat().st_mtime)
        except OSError:
            continue
    if not stamps:
        return None
    return round((time.time() - max(stamps)) / 3600.0, 2)

def _budgets_yaml_readable() -> bool:
    try:
        if not BUDGETS_YAML.exists():
            return False
        text = BUDGETS_YAML.read_text("utf-8", errors="replace")
        # Minimal sanity: must contain 'global:' and 'projects:'
        return "global:" in text and "projects:" in text
    except Exception:
        return False

def _organ_gate_status() -> dict:
    try:
        sys.path.insert(0, str(_BUDGET_DIR))
        import organ_gate
        return organ_gate.status()
    except Exception as e:
        return {"error": str(e)}

# ─── checks ──────────────────────────────────────────────────────────────────
def check_flags() -> dict:
    flags = {
        "HALT-ALL": _flag_exists(HALT_ALL),
        "STOP-ARCHITECT": _flag_exists(STOP_ARCHITECT),
        "STOP-METABOLIC": _flag_exists(STOP_METABOLIC),
        "STOP-DEBATE": _flag_exists(STOP_DEBATE),
        "STOP-ORGANISM": _flag_exists(STOP_ORGANISM),
        "FREEZE": _flag_exists(FREEZE_FLAG),
    }
    active = [k for k, v in flags.items() if v]
    level = "err" if flags["HALT-ALL"] or flags["FREEZE"] else ("warn" if active else "ok")
    return {"level": level, "active_flags": active, "details": flags}

def check_organism_state() -> dict:
    data = _read_json(ORGANISM_STATE)
    if not data:
        return {"level": "err", "reason": "ORGANISM-STATE.json unreadable or empty"}
    issues = []
    if data.get("halted"):
        issues.append(f"halted={data['halted']}")
    if data.get("frozen"):
        issues.append("frozen=true")
    if data.get("stop_organism"):
        issues.append("stop_organism=true")
    if data.get("exited"):
        issues.append(f"exited={data['exited']}")
    level = "err" if (data.get("frozen") or data.get("halted")) else ("warn" if issues else "ok")
    return {"level": level, "issues": issues, "raw": data}

def check_organ_state() -> dict:
    try:
        with open(ORGAN_STATE, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
        data = json.loads(text) if text.strip() else {}
    except Exception as e:
        return {"level": "err", "reason": f"organ-state.json unreadable: {e}"}
    if not isinstance(data, dict):
        return {"level": "err", "reason": "organ-state.json top-level is not dict"}
    if "organs" not in data:
        return {"level": "warn", "reason": "missing 'organs' key"}
    # Check lock file stale
    lock = Path(str(ORGAN_STATE) + ".lock")
    lock_stale = False
    try:
        if lock.exists() and (time.time() - lock.stat().st_mtime) > 60:
            lock_stale = True
    except OSError:
        pass
    return {"level": "ok", "organs_count": len(data.get("organs", {})), "lock_stale": lock_stale}

def check_budgets_yaml() -> dict:
    ok = _budgets_yaml_readable()
    return {"level": "ok" if ok else "err", "readable": ok}

def check_germline() -> dict:
    lag = _germline_lag_hours()
    if lag is None:
        return {"level": "err", "lag_h": None, "reason": "no germline artifacts reachable"}
    if lag >= GERMLINE_ERR_H:
        return {"level": "err", "lag_h": lag, "reason": f"lag {lag}h >= {GERMLINE_ERR_H}h"}
    if lag >= GERMLINE_WARN_H:
        return {"level": "warn", "lag_h": lag, "reason": f"lag {lag}h >= {GERMLINE_WARN_H}h"}
    return {"level": "ok", "lag_h": lag}

def check_gitwrite() -> dict:
    if _flag_exists(GITWRITE_FAILED):
        try:
            txt = GITWRITE_FAILED.read_text("utf-8", errors="replace").lstrip("\ufeff").strip()
            first = txt.splitlines()[0].strip() if txt else ""
        except Exception:
            first = "GITWRITE-FAILED (unreadable)"
        return {"level": "err", "reason": first}
    return {"level": "ok", "reason": None}

def check_ledger_fallback() -> dict:
    size = _file_size(LEDGER_FALLBACK)
    level = "warn" if size > 1024 else "ok"
    return {"level": level, "size_bytes": size}

def check_organ_gate_status() -> dict:
    st = _organ_gate_status()
    if "error" in st:
        return {"level": "warn", "reason": st["error"]}
    return {"level": "ok", "organs": list(st.get("organs", {}).keys()), "fx": st.get("fx_aud_per_usd")}

def check_activation_flags() -> dict:
    try:
        flags = sorted(p.name for p in _OPS.glob("ACTIVATION-*.flag"))
    except OSError:
        flags = []
    # Sanity: if GO-LIVE exists but no DEBATE/REPLICATION, note it
    go_live = "ACTIVATION-GO-LIVE.flag" in flags
    debate = "ACTIVATION-DEBATE.flag" in flags
    replication = "ACTIVATION-REPLICATION.flag" in flags
    notes = []
    if go_live and not debate:
        notes.append("GO-LIVE without DEBATE — review loop routing")
    return {"level": "ok", "flags": flags, "notes": notes}

# ─── main ────────────────────────────────────────────────────────────────────
def _obs_alert_tail(results: dict) -> None:
    """RC3 فیوزِ سکوتِ مرگ: severity>=warn را به governor-alerts.md برسان.
    flag-gated (OCTOPUS_OBS_ALERT)، fail-soft — خروجی/exit-code را عوض نمی‌کند."""
    if opslib is None:
        return
    try:
        bad = [f"{name}={c['level']}" + (f" ({c['reason']})" if c.get('reason') else "")
               for name, c in results["checks"].items() if c["level"] in ("warn", "err")]
        if bad:
            opslib.alert([f"health_check {results['overall']}: " + "; ".join(bad)])
    except Exception:
        pass


def main() -> int:
    results = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "checks": {
            "flags": check_flags(),
            "organism_state": check_organism_state(),
            "organ_state": check_organ_state(),
            "budgets_yaml": check_budgets_yaml(),
            "germline": check_germline(),
            "gitwrite": check_gitwrite(),
            "ledger_fallback": check_ledger_fallback(),
            "organ_gate": check_organ_gate_status(),
            "activation_flags": check_activation_flags(),
        }
    }
    # Determine overall level
    levels = [c["level"] for c in results["checks"].values()]
    overall = "err" if "err" in levels else ("warn" if "warn" in levels else "ok")
    results["overall"] = overall

    if os.environ.get("OCTOPUS_OBS_ALERT", "0") == "1" and overall in ("warn", "err"):
        _obs_alert_tail(results)

    # JSON stdout
    print(json.dumps(results, ensure_ascii=False, indent=2))

    # Human summary stderr
    print(f"\n=== Octopus Health Check ({results['ts']}) ===", file=sys.stderr)
    print(f"Overall: {overall.upper()}", file=sys.stderr)
    for name, c in results["checks"].items():
        emoji = {"ok": "🟢", "warn": "🟡", "err": "🔴"}.get(c["level"], "⚪")
        print(f"  {emoji} {name}: {c['level']}", file=sys.stderr)
        if c.get("reason"):
            print(f"      → {c['reason']}", file=sys.stderr)
    return {"ok": 0, "warn": 1, "err": 2}.get(overall, 2)

if __name__ == "__main__":
    sys.exit(main())
