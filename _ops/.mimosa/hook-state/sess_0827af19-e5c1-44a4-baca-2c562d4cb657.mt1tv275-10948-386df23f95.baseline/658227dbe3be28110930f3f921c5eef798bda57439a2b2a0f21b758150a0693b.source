# -*- coding: utf-8 -*-
"""Wave 0 closeout: inventory + merge + candidate + independent verifier.

Never unlocks Wave 1. Never rewrites cost-receipts.jsonl.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from . import (
    artifact_merge,
    capability_immune,
    capability_parser,
    wave0_governor,
    wave0_verifier,
)

_OPS = Path(__file__).resolve().parent.parent
_ROOT = _OPS.parent
EVID = _ROOT / "06-EVIDENCE" / "NERVOUS-RECOVERY-2026-08-20"


def run() -> dict:
    evid = EVID
    evid.mkdir(parents=True, exist_ok=True)
    report = wave0_governor.audit_wave0()
    wave0_governor.write_audit(evid / "WAVE0-GATES.json", report)

    effectors = capability_parser.parse_effectors_py(_OPS / "effector_registry.py")
    inv = capability_immune.evaluate_declared(effectors)
    (evid / "CAPABILITY-INVENTORY.json").write_text(
        json.dumps(inv, ensure_ascii=False, indent=2), encoding="utf-8")

    merged = artifact_merge.merge_wave0()
    (evid / "LEDGER-MERGE.json").write_text(
        json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")

    out = {
        "schema": "wave0-closeout/1",
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "verdict": report["verdict"],
        "wave1_unlocked": False,
        "gates_passed": report["gates_passed"],
        "pass_conditions": report["hygiene"].get("pass_conditions"),
        "candidate_written": False,
        "verifier_confirmed": False,
        "final_pass_written": False,
    }

    if report["verdict"] == wave0_governor.Wave0Verdict.PASS and report["wave1_unlocked"] is False:
        candidate = {
            "schema": "wave0-pass-candidate/1",
            "ts": out["ts"],
            "status": "WAVE0_PASS_CANDIDATE",
            "wave1_unlocked": False,
            "wave1_unlock": "NOT_GRANTED",
            "gates_passed": report["gates_passed"],
            "pass_conditions": report["hygiene"].get("pass_conditions"),
            "hygiene": {
                k: report["hygiene"].get(k) for k in (
                    "fabricated_task_ids", "duplicate_receipts",
                    "schema_validation", "receipt_hash_coverage",
                    "critical_regressions", "shadow_pass",
                )
            },
            "note": "Candidate only. Independent verifier must confirm. Wave 1 stays locked.",
        }
        (evid / "WAVE0_PASS_CANDIDATE.json").write_text(
            json.dumps(candidate, ensure_ascii=False, indent=2), encoding="utf-8")
        out["candidate_written"] = True

    v = wave0_verifier.write_report(evid / "WAVE0-VERIFIER.json")
    out["verifier_confirmed"] = bool(v.get("confirmed"))
    out["verifier_failed"] = v.get("failed_checks")

    if out["candidate_written"] and out["verifier_confirmed"]:
        final = {
            "schema": "wave0-pass/1",
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "status": "WAVE0_PASS",
            "wave1_unlocked": False,
            "wave1_unlock": "NOT_GRANTED",
            "requires_owner_command_to_open_wave1": True,
            "verifier": "WAVE0-VERIFIER.json",
            "candidate": "WAVE0_PASS_CANDIDATE.json",
            "gates": report["gates_passed"],
        }
        (evid / "WAVE0_PASS.json").write_text(
            json.dumps(final, ensure_ascii=False, indent=2), encoding="utf-8")
        (evid / "WAVE0_PASS.md").write_text(
            "\n".join([
                "---",
                "type: evidence",
                "created: 2026-08-20",
                "updated: 2026-08-20",
                "tags: [octopus, wave0]",
                "---",
                "",
                "# WAVE0_PASS",
                "",
                "Independent verifier confirmed every Wave 0 PASS condition.",
                "`wave1_unlocked` remains **false**. Wave 1 needs a separate owner command.",
                "",
                f"- gates_passed: {report['gates_passed']}/4",
                f"- attribution (schema-present): {report['gates']['receipt_attribution']['now']}",
                f"- test registry: {report['gates']['test_registry']['now']}",
                f"- memory streak: {report['gates']['memory_continuity']['now']}",
                f"- capability parse: {report['gates']['capability_inventory']['now']}",
                "- C-048..C-053 remain candidates (not CONTRADICTIONS.md)",
                "",
            ]),
            encoding="utf-8",
        )
        out["final_pass_written"] = True
        out["verdict"] = "WAVE0_PASS"
    return out


if __name__ == "__main__":
    r = run()
    print(json.dumps(r, ensure_ascii=False, indent=2))
