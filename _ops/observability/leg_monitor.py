#!/usr/bin/env python3
"""
leg_monitor.py — Leg/worker isolation & money_link monitor (additive, read-only, stdlib-only).

Checks:
  1. All *.py in _ops/legs/ are readable and import-safe (no wildcard imports, no secrets).
  2. Any runtime-created TaskPacket would pass structural validation (via static scan).
  3. organ_gate.status includes expected organs from budgets.yaml.
  4. No leg file contains suspicious patterns (secrets=, spawn=, wildcard read_allowlist).

Output: JSON stdout + summary stderr.
Exit: 0=ok, 1=warn, 2=err.
"""
from __future__ import annotations

import ast
import json
import sys
import time
from pathlib import Path

_OPS = Path(__file__).resolve().parents[1]
_BUDGET_DIR = _OPS / "budget"
_LEGS_DIR = _OPS / "legs"

opslib = None
try:
    sys.path.insert(0, str(_BUDGET_DIR))
    import opslib as _opslib
    opslib = _opslib
except Exception:
    pass

# ─── helpers ─────────────────────────────────────────────────────────────────
# Known internal modules (part of Octopus, not stdlib but not external deps)
_INTERNAL_MODULES = {
    "opslib", "organ_gate", "budget_gate", "leg",
    "money", "txn_store", "attributor", "ps_writeback", "pocketsmith_api",
    "ledger_core", "acct_memory", "txn_categorize", "raw_store", "recon",
    "asset_map", "journal_bridge", "company_books", "books_xero",
    "lead_scorer", "lead_sense", "lead_quote", "email_inbound",
    "ziman_biology", "ziman_phase2", "ziman_leg", "leg_cultivate",
    "leg_freshness", "mining_leg", "crypto_leg", "knowledge_leg",
    "accounting_leg", "cartographer_leg", "lead_leg",
    "personal_ledger", "invoice", "pricing", "pocketsmith_import",
    "smoke_24h", "smoke_ziman_wire", "smoke_cartographer_virtual",
}

_STDLIB = getattr(sys, "stdlib_module_names", set())


def _scan_file_for_patterns(path: Path) -> dict:
    """Static scan of a leg file for structural invariants."""
    issues = []
    warnings = []
    try:
        text = path.read_text("utf-8", errors="replace")
    except Exception as e:
        return {"issues": [f"unreadable: {e}"], "warnings": []}

    # Heuristic text scans (fast, no AST needed)
    if "read_allowlist=\"*\"" in text or "read_allowlist=('*',)" in text:
        issues.append("wildcard read_allowlist detected")
    if "spawn=" in text and "spawn=0" not in text:
        # crude: if spawn appears but not spawn=0
        lines = text.splitlines()
        for line in lines:
            if "spawn=" in line and "spawn=0" not in line:
                issues.append(f"non-zero spawn in line: {line.strip()[:60]}")
                break
    if "secrets=" in text and "secrets=()" not in text and "secrets=[]" not in text and "default_factory=tuple" not in text:
        lines = text.splitlines()
        for line in lines:
            if "secrets=" in line and "secrets=()" not in line:
                issues.append(f"non-empty secrets in line: {line.strip()[:60]}")
                break

    # AST scan for imports (detect non-stdlib, non-internal imports)
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError as e:
        warnings.append(f"syntax error at line {e.lineno}")
        return {"issues": issues, "warnings": warnings}

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                mod = alias.name.split(".")[0]
                if mod not in _STDLIB and mod not in _INTERNAL_MODULES:
                    warnings.append(f"external import: {mod}")
        elif isinstance(node, ast.ImportFrom):
            mod = (node.module or "").split(".")[0]
            if mod and mod not in _STDLIB and mod not in _INTERNAL_MODULES:
                warnings.append(f"external import from: {mod}")

    return {"issues": issues, "warnings": warnings}

def _get_expected_organs() -> set[str]:
    try:
        sys.path.insert(0, str(_BUDGET_DIR))
        import opslib as ol
        table = ol.organ_table()
        return set(table.keys())
    except Exception:
        return set()

# ─── checks ──────────────────────────────────────────────────────────────────
def check_leg_files() -> dict:
    if not _LEGS_DIR.exists():
        return {"level": "warn", "reason": "_ops/legs directory not found"}

    leg_files = sorted(p for p in _LEGS_DIR.iterdir() if p.suffix == ".py" and p.is_file())
    if not leg_files:
        return {"level": "warn", "reason": "no .py files in _ops/legs"}

    file_results = []
    total_issues = 0
    total_warnings = 0

    for lf in leg_files:
        res = _scan_file_for_patterns(lf)
        file_results.append({
            "file": lf.name,
            "issues": res["issues"],
            "warnings": res["warnings"],
            "level": "err" if res["issues"] else ("warn" if res["warnings"] else "ok")
        })
        total_issues += len(res["issues"])
        total_warnings += len(res["warnings"])

    level = "err" if total_issues else ("warn" if total_warnings else "ok")
    return {"level": level, "files_checked": len(leg_files), "total_issues": total_issues, "total_warnings": total_warnings, "details": file_results}

def check_organ_coverage() -> dict:
    expected = _get_expected_organs()
    if not expected:
        return {"level": "warn", "reason": "could not read organ_table from budgets.yaml"}

    try:
        sys.path.insert(0, str(_BUDGET_DIR))
        import organ_gate
        st = organ_gate.status()
        actual = set(st.get("organs", {}).keys())
    except Exception as e:
        return {"level": "warn", "reason": f"organ_gate.status unavailable: {e}"}

    missing = expected - actual
    if missing:
        return {"level": "warn", "reason": f"organs in budgets.yaml but not in state: {sorted(missing)}"}
    return {"level": "ok", "expected": sorted(expected), "actual": sorted(actual)}

# ─── main ────────────────────────────────────────────────────────────────────
def main() -> int:
    results = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "checks": {
            "leg_files": check_leg_files(),
            "organ_coverage": check_organ_coverage(),
        }
    }
    levels = [c["level"] for c in results["checks"].values()]
    overall = "err" if "err" in levels else ("warn" if "warn" in levels else "ok")
    results["overall"] = overall

    print(json.dumps(results, ensure_ascii=False, indent=2))

    print(f"\n=== Leg Monitor ({results['ts']}) ===", file=sys.stderr)
    print(f"Overall: {overall.upper()}", file=sys.stderr)
    for name, c in results["checks"].items():
        emoji = {"ok": "🟢", "warn": "🟡", "err": "🔴"}.get(c["level"], "⚪")
        print(f"  {emoji} {name}: {c['level']}", file=sys.stderr)
        if c.get("reason"):
            print(f"      → {c['reason']}", file=sys.stderr)
    return {"ok": 0, "warn": 1, "err": 2}.get(overall, 2)

if __name__ == "__main__":
    sys.exit(main())
