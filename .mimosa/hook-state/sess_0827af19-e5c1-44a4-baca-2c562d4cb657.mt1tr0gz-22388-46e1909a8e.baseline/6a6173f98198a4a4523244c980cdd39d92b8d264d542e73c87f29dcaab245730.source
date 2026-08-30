"""Advisory judge. D6=BETWEEN_RUN_VARIANCE so never confirmatory. executable=false."""
from __future__ import annotations

import re
from typing import Any

D6 = "BETWEEN_RUN_VARIANCE"
GAP_001 = "OPEN"
_ACTION = re.compile(
    r"\b(actuator|wire_live|restart_organism|deploy|schtasks|crontab|"
    r"send_telegram|external_action\s*=\s*true|executable\s*=\s*true)\b",
    re.I,
)


def count_executable_true(obj: Any) -> int:
    n = 0
    if isinstance(obj, dict):
        if obj.get("executable") is True:
            n += 1
        for v in obj.values():
            n += count_executable_true(v)
    elif isinstance(obj, list):
        for v in obj:
            n += count_executable_true(v)
    return n


def advisory(*, pipeline: dict[str, Any], rendered: dict[str, Any] | None = None,
             model_text: str = "") -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    exec_n = count_executable_true(pipeline) + count_executable_true(rendered or {})
    checks.append({"id": "executable_false", "pass": exec_n == 0, "n": exec_n})
    gates = pipeline.get("gate_decisions") or []
    modes = {g.get("domain"): g.get("mode") for g in gates}
    jr = next((g for g in gates if g.get("domain") == "judge_reliability"), None)
    checks.append({
        "id": "judge_capped_advisory",
        "pass": bool(jr) and jr.get("mode") in ("ADVISORY", "BLOCK", "SHADOW") and jr.get("executable") is False,
        "mode": (jr or {}).get("mode"),
    })
    checks.append({"id": "d6_between_run_variance", "pass": True, "value": D6})
    checks.append({"id": "gap_001_open", "pass": True, "value": GAP_001})
    forbidden = bool(_ACTION.search(model_text or ""))
    checks.append({"id": "no_actuator_verbs_in_model_text", "pass": not forbidden})
    evidence = []
    if rendered:
        evidence = list(rendered.get("evidence_ids") or [])
    checks.append({"id": "evidence_ids_attached", "pass": bool(evidence), "n": len(evidence)})
    ok = all(c["pass"] for c in checks if c["id"] != "evidence_ids_attached")
    # missing evidence is a finding, not a license to execute
    return {
        "schema": "full-loop-judge.v1",
        "verdict": "ADVISORY_PROPOSAL_ONLY",
        "d6": D6,
        "gap_001": GAP_001,
        "executable": False,
        "external_action": False,
        "confirmatory": False,
        "skill_modes": modes,
        "checks": checks,
        "ok": ok,
        "reasons": [
            "D6=BETWEEN_RUN_VARIANCE → judge is advisory, not confirmatory",
            "Metacontrol fail-closed: executable remains false",
            f"executable_true_count={exec_n}",
        ],
    }
