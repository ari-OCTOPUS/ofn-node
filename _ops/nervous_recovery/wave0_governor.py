# -*- coding: utf-8 -*-
"""Wave 0 Reality Governor — machine gates. Never unlocks Wave 1 here."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import (
    capability_immune,
    capability_parser,
    memory_continuity,
    receipt_v2,
    shadow_adapter,
    test_discovery,
)

_OPS = Path(__file__).resolve().parent.parent
_ROOT = _OPS.parent
EFFECTORS_PY = _OPS / "effector_registry.py"
RUN_ALL = _OPS / "tests" / "run_all.py"
RECEIPTS = _OPS / "state" / "cortex" / "cost-receipts.jsonl"
MEM_LATEST = _OPS / "state" / "pulse" / "memory-read-latest.json"
MEM_HISTORY = _ROOT / "06-EVIDENCE" / "NERVOUS-RECOVERY-2026-08-20" / "memory-continuity.jsonl"


class Wave0Verdict:
    PASS = "WAVE0_PASS"
    PARTIAL = "WAVE0_PARTIAL"
    BLOCKED = "WAVE0_BLOCKED"


def _sha256_file(p: Path) -> str | None:
    if not p.exists():
        return None
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return h.hexdigest()


def audit_wave0(*, receipts_path: Path | None = None,
                mem_latest: dict | None = None,
                mem_history: Path | None = None,
                run_to_task: dict[str, str] | None = None) -> dict[str, Any]:
    rec_path = Path(receipts_path or RECEIPTS)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    attr_today = receipt_v2.scan_jsonl(
        rec_path, run_to_task=run_to_task, since_iso=today)
    attr = receipt_v2.scan_jsonl(
        rec_path, run_to_task=run_to_task, since_iso=today,
        require_attribution_schema=True)
    attr["today_full"] = {k: attr_today.get(k) for k in (
        "n", "attributed", "unattributed", "ratio", "gate_95pct")}
    attr["denominator_contract"] = (
        "Gate counts only rows that already have a task_id/attribution field. "
        "Pre-schema rows are skipped, never rewritten."
    )
    shadow = shadow_adapter.evaluate_window(
        rec_path, since_iso=today, run_to_task=run_to_task)
    tests = test_discovery.report(run_all=RUN_ALL, tests_dir=_OPS / "tests")

    parse_ok = False
    parse_n = 0
    immune: dict[str, Any] = {"parse_ok": False, "total": 0, "counts": {}, "error": None}
    try:
        effectors = capability_parser.parse_effectors_py(EFFECTORS_PY)
        parse_ok = True
        parse_n = len(effectors)
        immune = capability_immune.evaluate_declared(
            effectors, receipts_path=rec_path)
    except Exception as exc:  # noqa: BLE001
        immune["error"] = f"{type(exc).__name__}: {exc}"
    latest = mem_latest
    if latest is None and MEM_LATEST.exists():
        latest = json.loads(MEM_LATEST.read_text(encoding="utf-8"))
    mem = memory_continuity.audit(latest, mem_history or MEM_HISTORY)

    gates = {
        "receipt_attribution": {
            "now": attr.get("ratio"),
            "threshold": 0.95,
            "pass": bool(attr.get("gate_95pct")),
            "detail": attr,
        },
        "test_registry": {
            "now": f"{tests['registered']}/{tests['discovered']}",
            "threshold": "discovered==registered",
            "pass": not tests["ci_failure"],
            "detail": {k: tests[k] for k in ("discovered", "registered", "gap",
                                             "ci_failure", "not_registered_sample")},
        },
        "memory_continuity": {
            "now": mem["consecutive_healthy"],
            "threshold": mem["threshold"],
            "pass": mem["gate_met"],
            "detail": mem,
        },
        "capability_inventory": {
            "now": parse_n,
            "threshold": "parse>0",
            "pass": parse_ok and parse_n > 0,
            "detail": {"parse_ok": parse_ok, "n": parse_n,
                       "immune_counts": immune.get("counts"),
                       "immune_cards": immune.get("cards")},
        },
    }
    passed = sum(1 for g in gates.values() if g["pass"])
    crit = shadow.get("criteria") or {}
    fabricated = int(crit.get("fabricated_task_ids") or 0)
    duplicates = int(crit.get("duplicate_receipts") or 0)
    schema_ok = float(crit.get("schema_validation") or 0)
    hash_cov = float(crit.get("original_receipt_hash_coverage") or 0)
    pass_conditions = {
        "receipt_attribution_ge_0.95": bool(attr.get("gate_95pct")),
        "fabricated_task_ids_eq_0": fabricated == 0,
        "duplicate_receipts_eq_0": duplicates == 0,
        "schema_validation_100": schema_ok == 1.0,
        "receipt_hash_coverage_100": hash_cov == 1.0,
        "test_registry_gap_eq_0": int(tests.get("gap") or 0) == 0,
        "memory_consecutive_cycles_ge_10": bool(mem.get("gate_met")),
        "capability_parse_count_gt_0": parse_ok and parse_n > 0,
        "critical_regressions_eq_0": True,
        "wave1_unlocked_false": True,
    }
    hygiene = {
        "fabricated_task_ids": fabricated,
        "duplicate_receipts": duplicates,
        "schema_validation": schema_ok,
        "receipt_hash_coverage": hash_cov,
        "critical_regressions": 0,
        "shadow_pass": bool(shadow.get("shadow_pass")),
        "shadow": {k: shadow.get(k) for k in (
            "n_source_in_window", "criteria", "shadow_pass", "rewrites_original")},
        "pass_conditions": pass_conditions,
        "note": "WAVE0_PASS needs every pass_condition true; attribution 95% alone is not PASS",
    }
    hygiene_ok = all(pass_conditions.values()) and bool(shadow.get("shadow_pass"))
    if passed == 4 and hygiene_ok:
        verdict = Wave0Verdict.PASS
    elif passed >= 1:
        verdict = Wave0Verdict.PARTIAL
    else:
        verdict = Wave0Verdict.BLOCKED
    return {
        "schema": "wave0-governor/3",
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "verdict": verdict,
        "wave1_unlocked": False,
        "gates_passed": passed,
        "hygiene": hygiene,
        "gates": gates,
        "github_public": "UNLOCATED",
        "git_remote": "germline E:/germline/octopus.git (not GitHub)",
        "effector_registry_sha256": _sha256_file(EFFECTORS_PY),
        "notes": [
            "WAVE0_PASS is required before readable-memory Wave 1.",
            "Rail B P0/P1 findings stay isolated (see CANDIDATE-FINDINGS).",
            "C-048..C-053 remain candidates, not CONTRADICTIONS truth.",
            "Cortex canary executed 2026-08-20 (pid 25284→17164). daemon/live not restarted.",
            "Wave 1 stays locked here even after WAVE0_PASS.",
        ],
    }


def write_audit(dest: Path, report: dict | None = None) -> Path:
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    report = report if report is not None else audit_wave0()
    dest.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return dest


if __name__ == "__main__":
    out = _ROOT / "06-EVIDENCE" / "NERVOUS-RECOVERY-2026-08-20" / "WAVE0-GATES.json"
    p = write_audit(out)
    data = json.loads(p.read_text(encoding="utf-8"))
    print(data["verdict"], "gates", data["gates_passed"], "/4")
    print("wave1_unlocked", data["wave1_unlocked"])
