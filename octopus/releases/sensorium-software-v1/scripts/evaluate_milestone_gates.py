#!/usr/bin/env python3
"""Evaluate octopus.milestone-gate.v2 files. Missing evidence == unmet condition.

Calendar time does not pass a gate. M1 is a hard prerequisite of M2.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, "/opt/octopus/cognition/src")

from octopus_cognition.milestone_gate import (  # noqa: E402
    PREREQUISITES,
    apply_prerequisites,
    evaluate_gate,
)

GATES_DIR = Path("/var/lib/octopus/state/engineering-completeness/gates")


def load_gate(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def evaluate_dir(gates_dir: Path = GATES_DIR) -> dict[str, Any]:
    files = sorted(gates_dir.glob("M*.json"))
    computed: dict[str, dict[str, Any]] = {}
    for path in files:
        doc = load_gate(path)
        mid = str(doc.get("milestone"))
        ev = evaluate_gate(doc)
        computed[mid] = {
            "path": str(path),
            "status_human": doc.get("status_human"),
            "gate_result_declared": doc.get("gate_result"),
            "gate_result_computed": ev["gate_result"],
            "unmet": ev["unmet"],
            "authority_change_permitted": False,
            "prerequisite": PREREQUISITES.get(mid),
        }

    prereq_in = {mid: spec["gate_result_computed"] for mid, spec in computed.items()}
    prereq_out = apply_prerequisites(prereq_in)
    for mid, spec in computed.items():
        if prereq_out.get(mid) != spec["gate_result_computed"]:
            spec["gate_result_computed"] = prereq_out[mid]
            spec["blocked_by_prerequisite"] = spec["prerequisite"]
            spec["unmet"] = list(spec["unmet"]) + ["prerequisite_unmet"]

    overall = "PASS" if all(v["gate_result_computed"] == "PASS" for v in computed.values()) else "BLOCKED"
    m1 = computed.get("M1_INTEGRITY", {}).get("gate_result_computed", "BLOCKED")
    return {
        "schema": "octopus.milestone-gate.summary.v2",
        "overall": overall,
        "m1_integrity": m1,
        "m2_evidence_permitted": m1 == "PASS",
        "authority_change_permitted": False,
        "decision": "KEEP_WAVE0_LOCKED",
        "calendar_does_not_pass_gates": True,
        "missing_evidence_is_fail": True,
        "milestones": computed,
    }


def main() -> int:
    out = evaluate_dir()
    print(json.dumps(out, indent=2, ensure_ascii=False))
    summary_path = GATES_DIR.parent / "GATE_SUMMARY.json"
    if GATES_DIR.is_dir():
        summary_path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return 0 if out.get("overall") == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
