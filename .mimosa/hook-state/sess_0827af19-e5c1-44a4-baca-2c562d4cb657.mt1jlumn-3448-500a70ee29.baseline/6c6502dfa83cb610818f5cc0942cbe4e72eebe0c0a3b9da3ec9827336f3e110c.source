# -*- coding: utf-8 -*-
"""Independent Wave 0 verifier.

Recomputes gates from live sources. Does not trust WAVE0-GATES.json alone.
Never sets wave1_unlocked.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import (
    canary_restart,
    capability_parser,
    memory_continuity,
    receipt_v2,
    shadow_adapter,
    test_discovery,
    wave0_governor,
)

_OPS = Path(__file__).resolve().parent.parent
_ROOT = _OPS.parent
EVID = _ROOT / "06-EVIDENCE" / "NERVOUS-RECOVERY-2026-08-20"


def _check(name: str, ok: bool, detail: Any) -> dict[str, Any]:
    return {"name": name, "ok": bool(ok), "detail": detail}


def verify(*, evid: Path | None = None) -> dict[str, Any]:
    evid = Path(evid or EVID)
    live = wave0_governor.audit_wave0()
    gates_path = evid / "WAVE0-GATES.json"
    candidate_path = evid / "WAVE0_PASS_CANDIDATE.json"
    written = None
    if gates_path.is_file():
        written = json.loads(gates_path.read_text(encoding="utf-8"))

    today = live["gates"]["receipt_attribution"]["detail"]
    tests = live["gates"]["test_registry"]["detail"]
    mem = live["gates"]["memory_continuity"]["detail"]
    hyg = live["hygiene"]
    crit = (hyg.get("shadow") or {}).get("criteria") or {}

    # Recompute the four gates from the same libraries, not from the JSON artifact.
    attr = receipt_v2.scan_jsonl(
        _OPS / "state" / "cortex" / "cost-receipts.jsonl",
        since_iso=__import__("datetime").datetime.now(
            __import__("datetime").timezone.utc).strftime("%Y-%m-%d"),
        require_attribution_schema=True)
    disc = test_discovery.report()
    latest = None
    latest_p = _OPS / "state" / "pulse" / "memory-read-latest.json"
    if latest_p.exists():
        latest = json.loads(latest_p.read_text(encoding="utf-8"))
    mem2 = memory_continuity.audit(latest, evid / "memory-continuity.jsonl")
    caps = capability_parser.parse_effectors_py(_OPS / "effector_registry.py")
    shadow = shadow_adapter.evaluate_window(
        _OPS / "state" / "cortex" / "cost-receipts.jsonl",
        since_iso=__import__("datetime").datetime.now(
            __import__("datetime").timezone.utc).strftime("%Y-%m-%d"))

    src = (_OPS / "nervous_recovery" / "wave0_governor.py").read_text(encoding="utf-8")
    checks = [
        _check("wave1_unlocked_live", live.get("wave1_unlocked") is False,
               live.get("wave1_unlocked")),
        _check("wave1_unlocked_source_literal",
               '"wave1_unlocked": False' in src, "governor source"),
        _check("canary_execute_false", canary_restart.EXECUTE is False,
               canary_restart.EXECUTE),
        _check("receipt_attribution_ge_0.95", bool(attr.get("gate_95pct")),
               attr.get("ratio")),
        _check("fabricated_task_ids_eq_0",
               int(shadow["criteria"]["fabricated_task_ids"]) == 0,
               shadow["criteria"]["fabricated_task_ids"]),
        _check("duplicate_receipts_eq_0",
               int(shadow["criteria"]["duplicate_receipts"]) == 0,
               shadow["criteria"]["duplicate_receipts"]),
        _check("schema_validation_100",
               float(shadow["criteria"]["schema_validation"]) == 1.0,
               shadow["criteria"]["schema_validation"]),
        _check("receipt_hash_coverage_100",
               float(shadow["criteria"]["original_receipt_hash_coverage"]) == 1.0,
               shadow["criteria"]["original_receipt_hash_coverage"]),
        _check("test_registry_gap_eq_0", disc["gap"] == 0, disc["gap"]),
        _check("memory_consecutive_cycles_ge_10", mem2["gate_met"],
               mem2["consecutive_healthy"]),
        _check("capability_parse_count_gt_0", len(caps) > 0, len(caps)),
        _check("critical_regressions_eq_0", hyg.get("critical_regressions") == 0,
               hyg.get("critical_regressions")),
        _check("shadow_pass", bool(shadow.get("shadow_pass")), shadow.get("shadow_pass")),
        _check("rewrites_original_false", shadow.get("rewrites_original") is False,
               shadow.get("rewrites_original")),
        _check("unique_cycle_identities",
               bool(mem2.get("unique_cycle_identities")),
               mem2.get("trailing_beats")),
    ]
    if written is not None:
        checks.append(_check(
            "artifact_matches_live_verdict",
            written.get("verdict") == live.get("verdict")
            and written.get("wave1_unlocked") is False,
            {"written": written.get("verdict"), "live": live.get("verdict")}))
        checks.append(_check(
            "artifact_gates_passed_match",
            written.get("gates_passed") == live.get("gates_passed"),
            {"written": written.get("gates_passed"), "live": live.get("gates_passed")}))
    candidate = None
    if candidate_path.is_file():
        candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
        checks.append(_check(
            "candidate_wave1_locked",
            candidate.get("wave1_unlocked") is False,
            candidate.get("wave1_unlocked")))
        checks.append(_check(
            "candidate_does_not_unlock_wave1",
            candidate.get("wave1_unlock") not in (True, "GRANTED"),
            candidate.get("wave1_unlock", "absent")))

    failed = [c["name"] for c in checks if not c["ok"]]
    confirmed = not failed and live.get("verdict") == wave0_governor.Wave0Verdict.PASS
    return {
        "schema": "wave0-verifier/1",
        "confirmed": confirmed,
        "live_verdict": live.get("verdict"),
        "wave1_unlocked": False,
        "failed_checks": failed,
        "checks": checks,
        "independent_recompute": {
            "attribution_ratio": attr.get("ratio"),
            "attribution_n": attr.get("n"),
            "test_gap": disc.get("gap"),
            "memory_streak": mem2.get("consecutive_healthy"),
            "capability_n": len(caps),
            "shadow_criteria": shadow.get("criteria"),
        },
        "written_gates_ts": (written or {}).get("ts"),
        "candidate_present": candidate is not None,
        "note": (
            "confirmed=true only if every PASS condition holds and wave1 stays locked. "
            "This verifier does not open Wave 1."
        ),
    }


def write_report(dest: Path | None = None) -> dict[str, Any]:
    evid = EVID
    dest = Path(dest or (evid / "WAVE0-VERIFIER.json"))
    rep = verify(evid=evid)
    dest.write_text(json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    return rep


if __name__ == "__main__":
    r = write_report()
    print("confirmed", r["confirmed"], "verdict", r["live_verdict"])
    print("failed", r["failed_checks"])
    print("wave1_unlocked", r["wave1_unlocked"])
