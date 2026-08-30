#!/usr/bin/env python3
"""
budget_monitor.py — Budget drift & divergence monitor (additive, read-only, stdlib-only).

Monitors:
  1. Per-organ spent vs cap_monthly (from budgets.yaml via organ_gate.status).
  2. Global monthly cap vs billed (from budget_gate state if available).
  3. Telemetry vs billed divergence (if telemetry.py readable).
  4. Spike detection: organ daily spend rate vs spike_pct threshold.
  5. Organ gate log tail for recent denials.

Output: JSON to stdout + summary to stderr.
Exit: 0=ok, 1=warn, 2=err.

Respects:
  I1: read-only, no ledger writes.
  I2: observes budget_gate, never enforces.
  I3: divergence reported, not auto-FREEZE.
  I6: thresholds from budgets.yaml.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

_OPS = Path(__file__).resolve().parents[1]
_BUDGET_DIR = _OPS / "budget"
_STATE_DIR = _OPS / "state"

opslib = None
try:
    sys.path.insert(0, str(_BUDGET_DIR))
    import opslib as _opslib
    opslib = _opslib
except Exception:
    pass

BUDGETS_YAML = _BUDGET_DIR / "budgets.yaml"
ORGAN_LOG = _BUDGET_DIR / "organ-gate-log.jsonl"
BUDGET_STATE = _BUDGET_DIR / "budget-state.json"

# ─── helpers ─────────────────────────────────────────────────────────────────
def _read_json(p: Path) -> dict:
    try:
        return json.loads(p.read_text("utf-8", errors="replace"))
    except Exception:
        return {}

def _budgets_yaml_dict() -> dict:
    try:
        import yaml
        return yaml.safe_load(BUDGETS_YAML.read_text("utf-8", errors="replace")) or {}
    except Exception:
        return {}

def _read_organ_log_tail(n: int = 20) -> list[dict]:
    try:
        with open(ORGAN_LOG, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        records = []
        for line in lines[-n:]:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except Exception:
                continue
        return records
    except Exception:
        return []

def _get_spike_pct(budgets: dict) -> float:
    try:
        return float(budgets.get("global", {}).get("spike_pct", 25))
    except Exception:
        return 25.0

def _get_cap_monthly(budgets: dict) -> float:
    try:
        return float(budgets.get("global", {}).get("cap_monthly", 30))
    except Exception:
        return 30.0

# ─── checks ──────────────────────────────────────────────────────────────────
def check_organ_spending() -> dict:
    try:
        sys.path.insert(0, str(_BUDGET_DIR))
        import organ_gate
        st = organ_gate.status()
    except Exception as e:
        return {"level": "warn", "reason": f"organ_gate.status unavailable: {e}"}

    organs = st.get("organs", {})
    if not organs:
        return {"level": "warn", "reason": "no organ data in status"}

    budgets = _budgets_yaml_dict()
    spike_pct = _get_spike_pct(budgets)
    global_cap = _get_cap_monthly(budgets)
    fx = st.get("fx_aud_per_usd", 1.5)

    issues = []
    organ_rows = []
    total_month_aud = 0.0

    for name, data in organs.items():
        cap = data.get("cap_monthly_aud", 0)
        spent_month = data.get("spent_month_aud", 0)
        spent_today_usd = data.get("spent_today_usd", 0)
        total_month_aud += spent_month

        row = {"organ": name, "cap_aud": cap, "spent_month_aud": spent_month, "spent_today_usd": spent_today_usd}

        if cap > 0 and spent_month > cap:
            issues.append(f"{name}: monthly {spent_month:.4f} AUD > cap {cap:.2f}")
            row["level"] = "err"
        else:
            # Spike: daily spend > spike_pct% of monthly cap in a single day (rough proxy)
            # Convert today's USD to AUD for comparison
            today_aud = spent_today_usd * fx
            if cap > 0 and today_aud > (cap * spike_pct / 100.0):
                issues.append(f"{name}: daily spike {today_aud:.4f} AUD > {spike_pct}% of cap")
                row["level"] = "warn"
            else:
                row["level"] = "ok"
        organ_rows.append(row)

    if total_month_aud > global_cap:
        issues.append(f"GLOBAL: total {total_month_aud:.4f} AUD > cap {global_cap:.2f}")

    level = "err" if any("monthly" in i for i in issues) else ("warn" if issues else "ok")
    return {"level": level, "issues": issues, "organs": organ_rows, "total_month_aud": round(total_month_aud, 6)}

def check_telemetry_divergence() -> dict:
    # Best-effort: if telemetry.py can be imported, compare its aggregate vs organ_state
    try:
        sys.path.insert(0, str(_BUDGET_DIR))
        import telemetry
        # telemetry module doesn't expose a simple "get totals" function; we approximate
        # by trying to read from its data sources.
    except Exception:
        return {"level": "ok", "reason": "telemetry.py not available for divergence check"}

    # Read genome ledger METRIC entries for current month (best effort)
    ledger_path = _OPS.parent / "07 - Knowledge" / "genome-system" / "ledger" / "ledger.jsonl"
    month_prefix = time.strftime("%Y-%m")
    genome_total_usd = 0.0
    try:
        with open(ledger_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                    if rec.get("type") == "METRIC" and month_prefix in rec.get("ts", ""):
                        payload = rec.get("payload", {})
                        cost = payload.get("llm_cost_usd", 0)
                        if cost:
                            genome_total_usd += float(cost)
                except Exception:
                    continue
    except Exception:
        pass

    # Read organ-state for ARCHITECT_SYS as proxy for comparison
    organ_state = _read_json(_BUDGET_DIR / "organ-state.json")
    organs = organ_state.get("organs", {})
    arch_month_usd = 0.0
    for name, st in organs.items():
        arch_month_usd += st.get("spent_month_musd", 0) / 1_000_000.0

    # Divergence: if genome ledger exists and differs significantly from organ_state
    if genome_total_usd > 0 and arch_month_usd > 0:
        diff = abs(genome_total_usd - arch_month_usd)
        ratio = diff / max(arch_month_usd, genome_total_usd, 1e-9)
        if ratio > 0.20:
            return {"level": "warn", "reason": f"telemetry divergence {ratio:.1%} (genome {genome_total_usd:.4f} vs organ {arch_month_usd:.4f} USD)"}

    return {"level": "ok", "genome_total_usd": round(genome_total_usd, 6), "organ_total_usd": round(arch_month_usd, 6)}

def check_recent_denials() -> dict:
    tail = _read_organ_log_tail(30)
    denials = [r for r in tail if not r.get("allow", True)]
    if not denials:
        return {"level": "ok", "recent_denials": 0}
    reasons = {}
    for d in denials:
        r = d.get("reason", "unknown")
        reasons[r] = reasons.get(r, 0) + 1
    level = "warn" if len(denials) > 5 else "ok"
    return {"level": level, "recent_denials": len(denials), "denial_reasons": reasons}

# ─── main ────────────────────────────────────────────────────────────────────
def main() -> int:
    results = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "checks": {
            "organ_spending": check_organ_spending(),
            "telemetry_divergence": check_telemetry_divergence(),
            "recent_denials": check_recent_denials(),
        }
    }
    levels = [c["level"] for c in results["checks"].values()]
    overall = "err" if "err" in levels else ("warn" if "warn" in levels else "ok")
    results["overall"] = overall

    print(json.dumps(results, ensure_ascii=False, indent=2))

    print(f"\n=== Budget Monitor ({results['ts']}) ===", file=sys.stderr)
    print(f"Overall: {overall.upper()}", file=sys.stderr)
    for name, c in results["checks"].items():
        emoji = {"ok": "🟢", "warn": "🟡", "err": "🔴"}.get(c["level"], "⚪")
        print(f"  {emoji} {name}: {c['level']}", file=sys.stderr)
        if c.get("reason"):
            print(f"      → {c['reason']}", file=sys.stderr)
        if c.get("issues"):
            for issue in c["issues"]:
                print(f"      → {issue}", file=sys.stderr)
    return {"ok": 0, "warn": 1, "err": 2}.get(overall, 2)

if __name__ == "__main__":
    sys.exit(main())
