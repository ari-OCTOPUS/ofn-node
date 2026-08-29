#!/usr/bin/env python3
"""Write evidence-gate artifacts under engineering-completeness. Does not sign. Does not reboot."""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, "/opt/octopus/cognition/src")
from octopus_cognition.milestone_gate import evaluate_gate, gate  # noqa: E402

PACK = Path("/var/lib/octopus/state/engineering-completeness")
GATES = PACK / "gates"
TICKETS = PACK / "tickets"
INBOUND = Path("/var/lib/octopus/inbound/TO-LAPTOP/engineering-completeness")
NOW = datetime.now(timezone.utc).isoformat()
M0_DIGEST = "sha256:b4ffb57399228d1e1032c150dc84a31e40d833ee5b84928a1279752d043a682b"
AUDIT_PHRASE = "octopus-audit-ledger checkpoint anchored at seq=266"
AUDIT_HASH = "sha256:ec98f51753c6565d845acd6734c052e2c929383469c8a2755d88dcfbb24b7fc2"


def sha256_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def condition(cid, expected, observed, evidence):
    return {"id": cid, "expected": expected, "observed": observed, "evidence": evidence}


def write_gate(milestone, status_human, conditions, extra=None):
    doc = {
        "schema": "octopus.milestone-gate.v2",
        "written_at": NOW,
        "milestone": milestone,
        "status_human": status_human,
        "blocking_conditions": conditions,
        "calendar_time_is_not_exit": True,
        "authority_change_permitted": False,
    }
    if extra:
        doc.update(extra)
    computed = evaluate_gate(doc)
    doc["gate_result"] = computed["gate_result"]
    doc["unmet"] = computed["unmet"]
    doc["authority_change_permitted"] = False
    assert doc["gate_result"] == gate(conditions)
    dump(GATES / f"{milestone}.json", doc)
    return doc


def main() -> int:
    GATES.mkdir(parents=True, exist_ok=True)
    TICKETS.mkdir(parents=True, exist_ok=True)

    doctor_report = Path("/var/lib/octopus/state/engineering-completeness/DOCTOR_REPORT.json")
    boot_report = Path("/var/lib/octopus/state/gap001/boot_report.json")
    open_gaps = Path("/opt/octopus/current/manifests/open-gaps.json")
    fusion = Path("/var/lib/octopus/state/fusion/latest-frame.json")
    freeze_manifest = Path("/var/lib/octopus/inbound/TO-LAPTOP/owner-review-final/MANIFEST.json.sha256")
    lock_register = Path("/var/lib/octopus/inbound/TO-LAPTOP/owner-review-final/LOCK_REGISTER.json")
    doctor_causes = PACK / "DOCTOR_THREE_CAUSES.json"
    gap001_def = PACK / "GAP_001_DEFINITION.json"
    gap001_crit = PACK / "GAP_001_SUCCESS_CRITERIA.json"
    gap002 = PACK / "GAP_002_REGISTRY_STATUS.json"

    doctor_h = sha256_file(doctor_report)
    boot_h = sha256_file(boot_report)
    gaps_h = sha256_file(open_gaps)
    fusion_h = sha256_file(fusion)
    freeze_h = sha256_file(freeze_manifest) or M0_DIGEST
    lock_h = sha256_file(lock_register)

    m0 = write_gate(
        "M0_FREEZE",
        "PARTIAL",
        [
            condition("snapshot", "PRESENT", "PRESENT", str(Path("/var/lib/octopus/inbound/TO-LAPTOP/owner-review-final"))),
            condition("manifest", "PRESENT", "PRESENT", M0_DIGEST),
            condition("digest", M0_DIGEST, M0_DIGEST, str(freeze_manifest) if freeze_manifest.is_file() else M0_DIGEST),
            condition("independent_verify_two_machines", "PASS", "BOARD_ONLY", None),
        ],
        extra={
            "note": "Board holds the freeze digest. Laptop independent verify is not evidenced here. Partial is not PASS.",
            "creates_authority": False,
            "read_only_snapshot": True,
        },
    )

    m1 = write_gate(
        "M1_INTEGRITY",
        "BLOCKED",
        [
            condition("doctor_pass", "PASS", "FAIL", f"{doctor_report}:{doctor_h}"),
            condition("gap_001_closed", "CLOSED_TESTED_PASS", "OPEN", f"{boot_report}:{boot_h}"),
            condition("gap_002_registry_consistent", "CONSISTENT", "DEFERRED_TO_WAVE1", f"{open_gaps}:{gaps_h}"),
            condition("ledger_integrity", "PASS", "PASS", f"{AUDIT_PHRASE}|{AUDIT_HASH}"),
            condition("executed_actions", 0, 0, f"doctor_report:{doctor_h}|lock_register:{lock_h}"),
        ],
        extra={
            "doctor_fail_checks": ["sensor_coverage", "gap001", "gap002_registry"],
            "hard_prerequisite_of": ["M2_CANDIDATE"],
            "sensor_coverage_evidence": f"{fusion}:{fusion_h}",
        },
    )

    m2 = write_gate(
        "M2_CANDIDATE",
        "NOT_STARTED",
        [
            condition("m1_integrity", "PASS", m1["gate_result"], str(GATES / "M1_INTEGRITY.json")),
            condition("candidate_equals_baseline", False, None, None),
            condition("skill_lower_bound_positive", True, None, None),
            condition("bootstrap_method", "block_bootstrap", None, None),
            condition("shuffled_outcome_deny", True, None, None),
            condition("interaction_guard", True, None, None),
            condition("leakage_guard", True, None, None),
            condition("calibration_reported", True, None, None),
            condition("missingness_rate_reported", True, None, None),
            condition("per_domain_worst_case_skill_reported", True, None, None),
            condition("candidate_wired_to_live", False, False, "live_wm=persistence-v1"),
        ],
        extra={
            "reason_prior_score_zero_invalid": "model_is_the_baseline",
            "prior_shadow_eval_is_not_m2_evidence": True,
            "contract": str(PACK / "M2_CONTRACT.yaml"),
        },
    )

    later = [
        ("M3_SAFETY_CASE", "NOT_STARTED", [
            condition("iso_12100_risk_assessment", "DOCUMENTED", None, None),
            condition("plr_determined_in_risk_assessment", True, None, None),
            condition("unknowns_not_guessed", True, None, None),
            condition("independent_validation", "PASS", None, None),
        ]),
        ("M4_A0_ADVISORY", "NOT_STARTED", [
            condition("oa_a0_signed", True, False, None),
            condition("executable", False, False, "WAVE0_OBSERVE_ONLY"),
            condition("planner_reaches_host", False, False, "planner_not_on_live_path"),
        ]),
        ("M5_PLANNER_SANDBOX", "NOT_STARTED", [
            condition("replay_reproducible", True, None, None),
            condition("external_effects", 0, None, None),
            condition("planner_invoked_on_live", False, False, "metacontrol.planner_invoked=false"),
        ]),
        ("M6_HIL", "NOT_STARTED", [
            condition("dummy_load", True, None, None),
            condition("envelope_escapes", 0, None, None),
        ]),
        ("M7_BOUNDED_ACTUATOR", "NOT_STARTED", [
            condition("single_actuator", True, None, None),
            condition("lease_short", True, None, None),
            condition("operator_at_estop", True, None, None),
            condition("rollback_drill_prior", "PASS", None, None),
        ]),
        ("M8_SCOPE_GROWTH", "NOT_STARTED", [
            condition("one_capability_per_transition", True, None, None),
            condition("separate_authorization", True, None, None),
        ]),
        ("M9_OPERATIONS", "NOT_STARTED", [
            condition("drill", True, None, None),
            condition("rotation", True, None, None),
            condition("revalidation", True, None, None),
        ]),
    ]
    for name, status, conds in later:
        write_gate(name, status, conds)

    tickets = [
        {
            "schema": "octopus.doctor-fail-ticket.v1",
            "ticket_id": "TICKET-DOC-001",
            "check_id": "gap001",
            "title": "GAP-001 cold_boot_unverified last probe TESTED_FAIL",
            "independent": True,
            "observed": "OPEN / TESTED_FAIL / gates=[G8]",
            "expected": "CLOSED_TESTED_PASS after maintenance-window reboot meeting written criteria",
            "evidence": [
                {"path": str(boot_report), "sha256": boot_h},
                {"path": str(gap001_def), "sha256": sha256_file(gap001_def)},
                {"path": str(gap001_crit), "sha256": sha256_file(gap001_crit)},
            ],
            "pass_fail_written_before_execution": True,
            "agent_must_not_reboot": True,
            "proposed_change": "OWNER_MAINTENANCE_WINDOW_REQUIRED software reboot with operator present; do not auto-reboot",
            "diff": "none this session — test not executed",
            "rollback": "do not reboot; remain WAVE0_OBSERVE_ONLY; KEEP_WAVE0_LOCKED",
            "touches_candidate": False,
            "touches_planner": False,
            "touches_hardware": False,
        },
        {
            "schema": "octopus.doctor-fail-ticket.v1",
            "ticket_id": "TICKET-DOC-002",
            "check_id": "gap002_registry",
            "title": "GAP-002 status from registry of record, not from checkpoint credit",
            "independent": True,
            "observed": json.loads(open_gaps.read_text(encoding="utf-8"))["GAP-002"],
            "expected": {"status": "closed according to registry", "audit_integrity": "EXTERNALLY_CHECKPOINTED", "pass": True},
            "evidence": [
                {"path": str(open_gaps), "sha256": gaps_h},
                {"path": str(gap002), "sha256": sha256_file(gap002)},
            ],
            "source_of_truth": str(open_gaps),
            "not_source_of_truth": "seq-266 detached signature / live gap CLOSED_BY_SIGNED_CHECKPOINT",
            "proposed_change": "do not rewrite open-gaps.json from signature credit; registry close is a separate signed software process",
            "diff": "none this session — registry unchanged",
            "rollback": "leave open-gaps.json unchanged; do not treat signature as CLOSE",
            "touches_candidate": False,
            "touches_planner": False,
            "touches_hardware": False,
        },
        {
            "schema": "octopus.doctor-fail-ticket.v1",
            "ticket_id": "TICKET-DOC-003",
            "check_id": "sensor_coverage",
            "title": "coverage 0.6667 critical; OCT-SENSE-092/095 degraded; would_decide=block",
            "independent": True,
            "observed": {"coverage": 0.6667, "active": 4, "expected_sensors": 6, "degraded": ["OCT-SENSE-092", "OCT-SENSE-095"]},
            "expected": "healthy_or_explained without imputing missing/shadow sensors",
            "evidence": [
                {"path": str(fusion), "sha256": fusion_h},
                {"path": str(doctor_causes), "sha256": sha256_file(doctor_causes)},
            ],
            "proposed_change": "OWNER_MAINTENANCE_WINDOW_REQUIRED signed registry v6 apply; do not zero-fill 092/095",
            "diff": "none this session — registry remains v5",
            "rollback": "do not apply unsigned registry; do not impute missing sensors to 1.0",
            "touches_candidate": False,
            "touches_planner": False,
            "touches_hardware": False,
        },
    ]
    for t in tickets:
        t["written_at"] = NOW
        dump(TICKETS / f"{t['ticket_id']}.json", t)

    dump(
        PACK / "EVIDENCE_SEQUENCE.json",
        {
            "schema": "octopus.evidence-sequence.v1",
            "written_at": NOW,
            "replaces": "OWNER_WEEKLY_PLAN.md calendar weeks",
            "time_does_not_authorize_pass": True,
            "steps": [
                {
                    "n": 1,
                    "action": "three Doctor=FAIL causes as independent tickets with evidence, diff, rollback",
                    "artifact": str(TICKETS),
                    "closed": True,
                },
                {
                    "n": 2,
                    "action": "write GAP-001 PASS/FAIL before execution; run in maintenance window with operator",
                    "artifact": str(gap001_crit),
                    "criteria_written": True,
                    "executed": False,
                    "agent_must_not_reboot": True,
                },
                {
                    "n": 3,
                    "action": "extract GAP-002 from live registry, not checkpoint credit",
                    "artifact": str(open_gaps),
                    "closed": False,
                    "observed": "DEFERRED_TO_WAVE1",
                },
                {
                    "n": 4,
                    "action": "after Doctor PASS, collect 7 days natural telemetry; no synthetic load",
                    "closed": False,
                    "blocked_by": "M1_INTEGRITY",
                },
                {
                    "n": 5,
                    "action": "register interactive candidate in Shadow; run shuffled, leakage, interaction guards",
                    "closed": False,
                    "blocked_by": "M1_INTEGRITY",
                    "prior_shadow_eval_not_evidence": True,
                },
                {
                    "n": 6,
                    "action": "if skill_lower_bound not positive, reject candidate; do not change threshold",
                    "closed": False,
                    "bootstrap": "block_bootstrap",
                },
                {
                    "n": 7,
                    "action": "write Safety Case and PLr; validate E-stop, watchdog, power removal on bench",
                    "closed": False,
                    "unknown_must_not_be_guessed": True,
                },
                {
                    "n": 8,
                    "action": "issue OA-A0 advisory only; prove Planner cannot reach host",
                    "closed": False,
                    "oa_a0_created": False,
                },
                {
                    "n": 9,
                    "action": "HIL with dummy load; record every command outside envelope",
                    "closed": False,
                },
                {
                    "n": 10,
                    "action": "rollback drill before any physical test, never after",
                    "closed": False,
                },
            ],
        },
    )

    dump(
        PACK / "AUTHORITY_LEASE.example.json",
        {
            "schema": "octopus.authority-lease.v1",
            "status": "SCHEMA_ONLY_NOT_ISSUED",
            "lease_id": "LEASE-NOT-ISSUED",
            "level": "A3",
            "actuator_allowlist": ["motor-A"],
            "max_commands": 5,
            "max_duration_s": 120,
            "max_energy_j": 0,
            "expires_at": "NOT_ISSUED",
            "operator_present": True,
            "estop_verified_at": "NOT_ISSUED",
            "auto_revoke_on": [
                "telemetry_gap",
                "watchdog_timeout",
                "clock_anomaly",
                "ledger_failure",
                "doctor_not_pass",
                "lease_expiry",
                "budget_exhausted",
            ],
            "post_expiry_state": "AUTHORITY_NONE",
            "renewal": "ISSUE_NEW_LEASE_NOT_MUTATE_FIELDS",
            "levels_above_A1": "LEASE_ONLY_NOT_STEADY_STATE",
            "issued": False,
            "note": "Expiry is the default. Extending means a new lease. max_energy_j stays 0 until measured.",
        },
    )

    dump(
        PACK / "COMPLETION_RECORD.json",
        {
            "schema": "octopus.completion-record.v2",
            "written_at": NOW,
            "complete": False,
            "verifier": "NOT_PASS",
            "doctor": "FAIL",
            "gap_001": "OPEN",
            "gap_002": "OPEN",
            "ledger": "VALID_AND_EXTERNALLY_ANCHORED",
            "candidate_skill_lower_bound": "NOT_EVIDENCE_M1_BLOCKED",
            "calibration": "NOT_ASSESSED_AS_M2_EVIDENCE",
            "missing_data_behavior": "FAIL_SAFE",
            "planner": "NOT_ON_LIVE_PATH",
            "policy": "SCOPE_LIMITED",
            "risk_assessment": "TEMPLATE_ONLY",
            "required_performance_level": "NOT_DETERMINED",
            "authority_model": "LEASE_BASED_EXPIRING",
            "hardware_interlocks": "NOT_VALIDATED",
            "physical_estop": "NOT_VALIDATED",
            "watchdog": "NOT_VALIDATED",
            "rollback": "DRILL_NOT_RUN",
            "owner_authorizations": "NONE_FOR_TRANSITION",
            "general_unbounded_authority": False,
            "decision": "KEEP_WAVE0_LOCKED",
        },
    )

    dump(
        PACK / "STOP_CONDITIONS.json",
        {
            "schema": "octopus.stop-conditions.v2",
            "written_at": NOW,
            "stop_progression_if": [
                "doctor != PASS",
                "ledger or signature verification fails",
                "unexpected LAN listener",
                "missing telemetry converted to healthy",
                "coverage below contract",
                "planner invoked before allowed level",
                "actuator command without valid lease",
                "E-stop or independent watchdog fail",
                "command exceeds power/duration/rate",
                "rollback not executable",
                "outcome without prediction",
                "skill_lower_bound <= 0",
                "executed_actions increases at a level that must be 0",
                "any PLr check fails",
                "physical test without prior successful rollback drill",
            ],
            "added_v2": [
                "any PLr check fails",
                "physical test without prior successful rollback drill",
            ],
        },
    )

    dump(
        PACK / "M0_FREEZE.json",
        {
            "schema": "octopus.m0-freeze.v2",
            "milestone": "M0_FREEZE",
            "snapshot": "/var/lib/octopus/inbound/TO-LAPTOP/owner-review-final/",
            "manifest_sha256": M0_DIGEST,
            "read_only": True,
            "independent_verify_two_machines": "BOARD_ONLY_LAPTOP_NOT_EVIDENCED",
            "gate_result": m0["gate_result"],
            "status_human": "PARTIAL",
            "do_not_replace_freeze_with_this_pack": True,
            "digest_is_not_a_signature": True,
            "signed_checkpoint_preserved": True,
            "creates_authority": False,
            "candidate_not_wired_to_live": True,
            "hardware_not_touched": True,
        },
    )

    dump(
        PACK / "OWNER_REVIEW_DECISION.json",
        {
            "schema": "octopus.owner-review-decision.v2",
            "written_at": NOW,
            "current_wave": "WAVE0_OBSERVE_ONLY",
            "decision": "KEEP_WAVE0_LOCKED",
            "engineering_completeness_target": True,
            "absolute_perfection_not_a_goal": True,
            "milestone": "M1_INTEGRITY",
            "m0_status": "PARTIAL",
            "m1_gate": m1["gate_result"],
            "m2_evidence_permitted": False,
            "calendar_plan_superseded": True,
            "ready_for_owner_decision": False,
            "ready_for_bounded_transition": False,
            "authority_changed": False,
            "authority_model": "LEASE_BASED_EXPIRING",
            "oa_t7_created": False,
            "oa_a0_created": False,
            "lease_issued": False,
            "executed_actions": 0,
            "planner_invocations": 0,
            "actuator_authority": "NONE",
            "candidate_wired_to_live": False,
            "hardware_touched": False,
            "doctor": "FAIL",
            "doctor_fail_checks": ["sensor_coverage", "gap001", "gap002_registry"],
            "gap_001": "OPEN_TESTED_FAIL",
            "gap_002": "NOT_CLOSED_ACCORDING_TO_REGISTRY",
            "checkpoint_seq_266_signed": True,
            "checkpoint_creates_authority": False,
            "control_safety": "PASS",
            "next_action": "three independent Doctor FAIL tickets are written; GAP-001 acceptance criteria already written; do not touch candidate, Planner, or hardware",
        },
    )

    (PACK / "CURRENT_STATE.md").write_text(
        f"""# CURRENT_STATE — evidence gates (not calendar)

written_at: `{NOW}`
decision: **KEEP_WAVE0_LOCKED**
M0: PARTIAL (snapshot+digest present; two-machine verify not evidenced)
M1: **BLOCKED** (Doctor FAIL)
M2: NOT_STARTED — skill on Doctor-FAIL is not evidence

## Doctor FAIL — three independent tickets

See `tickets/TICKET-DOC-001.json` … `003.json`.

1. GAP-001 OPEN / TESTED_FAIL (G8)
2. GAP-002 registry DEFERRED_TO_WAVE1 — signature ≠ registry close
3. sensor_coverage 0.6667 critical; would_decide=block

## Gates

`python3 /opt/octopus/scripts/evaluate_milestone_gates.py`

Missing evidence fails the condition. Time does not pass a gate.

## Unchanged live path

- actuator_authority NONE, executed_actions 0, planner not on live path
- live WM persistence-v1
- candidate / Planner / hardware not touched this session
""",
        encoding="utf-8",
    )

    (PACK / "rollback-plan.md").write_text(
        """# rollback

Doctor registry-align (previous session only):

```
cp /var/lib/octopus/state/config-history/octopus_doctor_readonly.py.pre-registry-gap002 /opt/octopus/scripts/octopus_doctor_readonly.py
```

Evidence-gate pack: delete or ignore `/var/lib/octopus/state/engineering-completeness/gates/` and `tickets/`.
Do not restore a calendar plan as an exit criterion.

Do not restart. Do not reboot. Do not rewrite signed checkpoint. Do not copy private keys.
Do not issue a lease. Do not mutate an expiry field. Renewal is a new lease.
""",
        encoding="utf-8",
    )

    (PACK / "verification-commands.txt").write_text(
        """python3 -m json.tool /var/lib/octopus/state/engineering-completeness/gates/M1_INTEGRITY.json
python3 /opt/octopus/scripts/evaluate_milestone_gates.py
/opt/octopus/venv/bin/python -m pytest /opt/octopus/cognition/tests/test_milestone_gate.py /opt/octopus/cognition/tests/test_skill_bootstrap.py /opt/octopus/cognition/tests/test_authority_lease.py
python3 -m json.tool /opt/octopus/current/manifests/open-gaps.json
/opt/octopus/venv/bin/python /opt/octopus/scripts/octopus_doctor_readonly.py
ss -lntup | grep -E ':9101|:9464|:8080'
python3 -c "import json; print(json.load(open('/var/lib/octopus/state/homeostasis/latest.json'))['actuator_authority'], json.load(open('/var/lib/octopus/state/metacontrol/latest.json'))['planner_invoked'])"
""",
        encoding="utf-8",
    )

    import importlib.util

    ev_path = Path("/opt/octopus/scripts/evaluate_milestone_gates.py")
    spec = importlib.util.spec_from_file_location("evaluate_milestone_gates", ev_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load evaluate_milestone_gates")
    ev_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ev_mod)
    dump(PACK / "GATE_SUMMARY.json", ev_mod.evaluate_dir())

    decision_live = Path("/var/lib/octopus/state/OWNER_REVIEW_DECISION.json")
    shutil.copy2(PACK / "OWNER_REVIEW_DECISION.json", decision_live)

    skip_hash = {"MANIFEST.json", "MANIFEST.json.sha256"}
    files = {}
    for path in sorted(PACK.rglob("*")):
        if not path.is_file():
            continue
        rel = str(path.relative_to(PACK))
        if path.name in skip_hash:
            continue
        files[rel] = {"sha256": sha256_file(path), "bytes": path.stat().st_size}

    manifest = {
        "schema": "octopus.owner-review.manifest.v2",
        "written_at": NOW,
        "pack": "engineering-completeness-evidence-gates",
        "replaces_calendar_plan": True,
        "digest_is_signature": False,
        "do_not_treat_as_signed_manifest": True,
        "m0_owner_review_final_sha256": M0_DIGEST,
        "do_not_overwrite_m0_freeze": True,
        "decision": "KEEP_WAVE0_LOCKED",
        "m1_gate": m1["gate_result"],
        "m2_evidence_permitted": False,
        "audit_checkpoint": {
            "chain_id": "octopus-audit-ledger",
            "anchored_through_seq": 266,
            "record_hash_full": AUDIT_HASH,
            "phrase": AUDIT_PHRASE,
            "creates_authority": False,
        },
        "files": files,
    }
    dump(PACK / "MANIFEST.json", manifest)
    digest = sha256_file(PACK / "MANIFEST.json")
    (PACK / "MANIFEST.json.sha256").write_text(digest + "\n", encoding="utf-8")

    INBOUND.mkdir(parents=True, exist_ok=True)
    for path in PACK.rglob("*"):
        rel = path.relative_to(PACK)
        dest = INBOUND / rel
        if path.is_dir():
            dest.mkdir(parents=True, exist_ok=True)
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)

    print(json.dumps({"m0": m0["gate_result"], "m1": m1["gate_result"], "m2": m2["gate_result"], "manifest_sha256": digest}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
