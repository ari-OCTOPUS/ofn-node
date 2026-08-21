#!/usr/bin/env python3
"""Bio-cognitive laboratory core — schemas and append-only registries.

Operational JSONL lives under _ops/state/lab/ and is not Git-tracked. Only
schemas, fixtures, sealed manifests and verifier reports are committed.
Experiment Cards are validated before any execution: no card may run without
question/H1/H0/falsifier/baseline/control/metric/denominator/sample plan/stop
conditions/budget/rollback/kill switch/negative-result policy/preregistration.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
import uuid
from pathlib import Path

_OPS = Path(__file__).resolve().parent.parent

REQUIRED_CARD_FIELDS = (
    "experiment_id", "loop_id", "question", "hypothesis", "null_hypothesis",
    "falsifier", "metrics", "denominator", "controls", "sample_plan",
    "stop_conditions", "budgets", "rollback", "kill_switch",
    "negative_outcome_policy", "execution_mode", "result", "preregistered_at",
    "code_head", "fixture_hash", "telegram_surface", "miniapp_route",
)
# Fields excluded from the preregistration hash: they may change only via an
# explicit amendment after the fact.
_MUTABLE_AFTER_PREREG = {"result", "evidence_refs", "verifier", "updated_at"}

_EXECUTION_MODES = {"STATIC", "FIXTURE_ONLY", "UNIT_FIXTURE", "INTEGRATION_FIXTURE",
                    "FAULT_INJECTION", "SHADOW", "CANARY_PROPOSED",
                    "CANARY_OWNER_APPROVED", "VERIFIED"}
_RESULTS = {"PENDING", "SUPPORTED", "REFUTED", "NO_EFFECT", "REGRESSED",
            "INCONCLUSIVE", "INSUFFICIENT_SAMPLE", "ENVIRONMENT_FAILURE",
            "BLOCKED_BY_POLICY"}


def _state_dir() -> Path:
    base = str(os.environ.get("OCTOPUS_STATE_DIR", "") or "").strip()
    root = Path(base) if base else (_OPS / "state")
    return root / "lab"


def _ledger(name: str) -> Path:
    return _state_dir() / f"{name}-REGISTRY.jsonl"


def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def validate_experiment_card(card: dict) -> list[str]:
    """Return missing/invalid field errors; empty list means the card may run."""
    errors = []
    if not isinstance(card, dict):
        return ["card must be an object"]
    for field in REQUIRED_CARD_FIELDS:
        value = card.get(field)
        if value in (None, "", [], {}):
            errors.append(f"missing-{field}")
    mode = str(card.get("execution_mode") or "")
    if mode and mode not in _EXECUTION_MODES:
        errors.append(f"invalid-execution-mode-{mode}")
    result = str(card.get("result") or "")
    if result and result not in _RESULTS:
        errors.append(f"invalid-result-{result}")
    if not str(card.get("falsifier") or "").strip():
        errors.append("falsifier-empty")
    if not str(card.get("null_hypothesis") or "").strip():
        errors.append("null-hypothesis-empty")
    return errors


def preregister_hash(card: dict) -> str:
    """Canonical SHA-256 over preregistered fields only (mutable fields dropped)."""
    canonical = {k: v for k, v in sorted(card.items())
                 if k not in _MUTABLE_AFTER_PREREG}
    blob = json.dumps(canonical, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def register_experiment(card: dict, *, preregistered_hash: str | None = None) -> dict:
    errors = validate_experiment_card(card)
    if errors:
        return {"ok": False, "errors": errors}
    if "experiment_id" not in card:
        card["experiment_id"] = f"exp_{uuid.uuid4().hex[:12]}"
    if not card.get("preregistered_at"):
        card["preregistered_at"] = _now_iso()
    phash = preregistered_hash or preregister_hash(card)
    row = {"schema": "lab-experiment-card/1",
           "preregistration_hash": phash,
           "registered_at": _now_iso(),
           "card": card}
    path = _ledger("EXPERIMENT")
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return {"ok": True, "experiment_id": card["experiment_id"],
            "preregistration_hash": phash}


def append_record(ledger: str, record: dict) -> dict:
    """Append-only writer for observation/evidence/falsification/replication/
    negative/decision records. Every record must carry experiment_id + ts."""
    if not record.get("experiment_id") or not record.get("ts"):
        return {"ok": False, "errors": ["experiment_id-and-ts-required"]}
    path = _ledger(ledger)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return {"ok": True}


def seed_owner_experiments() -> dict:
    """Preregister the owner-specified experiment set (fixture/shadow scope)."""
    now = _now_iso()
    head = "2325ffce7b8408cb0c007c6089a4b7fe1f717b5a"
    base = {
        "loop_id": "LOOP-LAB-SECURITY", "metrics": ["pass/fail"],
        "denominator": "fixture executions", "controls": ["isolated state"],
        "sample_plan": {"min_runs": 1, "fixture_only": True},
        "stop_conditions": ["any forbidden side effect"],
        "budgets": {"max_runs": 3, "timeout_s": 180},
        "rollback": "no production path touched; fixture temp state",
        "kill_switch": "OCTOPUS_STATE_DIR isolation; stop on first red",
        "negative_outcome_policy": "retain and report; never hide",
        "preregistered_at": now, "code_head": head,
        "fixture_hash": "fixture-suite-test_security_c1_c4",
        "telegram_surface": "STATUS", "miniapp_route": "/lab/experiments/<id>",
        "execution_mode": "FIXTURE_ONLY", "result": "PENDING",
    }
    experiments = [
        ("EXP-SEC-001", "Does auth_date 300/-30 reject the previously accepted 3600/-60 window?",
         "301s and -31s are rejected", "301s or -31s accepted", "boundary_test_fails", "FIXTURE_ONLY"),
        ("EXP-SEC-002", "Does a one-time nonce block replay of the same approval inside TTL?",
         "second consume returns 409 REPLAY_REJECTED", "second consume succeeds", "replay_accepted", "FIXTURE_ONLY"),
        ("EXP-SEC-003", "Do concurrent approvals produce exactly one effect?",
         "8 consumers yield 1 winner", "winner_count != 1", "duplicate_winner", "FIXTURE_ONLY"),
        ("EXP-SEC-004", "Is retry_after=75 preserved and never retried early?",
         "zero transport calls before 75s", "early call at 30s", "early_retry", "FIXTURE_ONLY"),
        ("EXP-SEC-005", "Does retry_not_before survive restart?",
         "restart keeps the prohibition", "restart forgets", "early_send_after_restart", "FIXTURE_ONLY"),
        ("EXP-TG-001", "Is one-byte-tampered initData rejected with 403 empty and zero dispatch?",
         "tamper -> 403, empty, no upstream call", "dispatch>0", "dispatch_happened", "FIXTURE_ONLY"),
        ("EXP-TG-002", "Does restart avoid resending confirmed outbox items?",
         "confirmed items never resend", "resend occurs", "duplicate_effect", "FIXTURE_ONLY"),
        ("EXP-TG-003", "Do webhook and polling ever ingest the same update twice?",
         "single ingestion authority", "dual ingestion", "task_count>1", "CANARY_PROPOSED"),
        ("EXP-TG-004", "Do 42 scanner findings coalesce to one digest?",
         "42 -> 1 with count/first/last", "digest_count!=1", "spam_digest", "FIXTURE_ONLY"),
        ("EXP-TG-005", "Is an invalid webhook secret rejected with empty 403 and zero dispatch?",
         "403 empty, zero dispatch", "dispatch>0", "secret_bypass", "CANARY_PROPOSED"),
        ("EXP-TG-006", "Is a duplicate update deduped durably before 200?",
         "one task, 200 after dedupe", "task_count>1", "duplicate_task", "CANARY_PROPOSED"),
        ("EXP-MEM-001", "Does read-only memory retrieval leave the DB hash unchanged?",
         "before/after hash equal", "hash differs", "mutation", "FIXTURE_ONLY"),
        ("EXP-MEM-002", "Can task A retrieve task B's private context?",
         "zero cross-task leak", "leak>0", "cross_task_leak", "FIXTURE_ONLY"),
        ("EXP-HUB-001", "Does memory-lane failure leave the cortex response intact?",
         "cortex replies despite memory failure", "cortex dead", "lane_cascade", "FIXTURE_ONLY"),
        ("EXP-HUB-002", "Does auth failure stop all lanes?",
         "zero lanes dispatch", "any lane runs", "auth_bypass", "FIXTURE_ONLY"),
        ("EXP-HUB-003", "Does MCP without allowlist/budget stay propose-only?",
         "no external effect", "effect runs", "mcp_effect", "FIXTURE_ONLY"),
        ("EXP-LAB-001", "Do failed experiments remain visible and searchable?",
         "negative result retained", "removed", "evidence_loss", "FIXTURE_ONLY"),
        ("EXP-LAB-002", "Are registered/executed/skipped/unexecuted counts separate?",
         "counts reconcile independently", "merged", "count_conflation", "FIXTURE_ONLY"),
        ("EXP-DOC-001", "Are code_audited_head/document/provenance commits distinct?",
         "three distinct SHAs", "same SHA", "provenance_collapse", "FIXTURE_ONLY"),
        ("EXP-DOCTOR-001", "Does a stuck mission timeout and quarantine without pipeline deadlock?",
         "timeout -> quarantine, pipeline alive", "deadlock", "pipeline_stall", "FIXTURE_ONLY"),
        ("EXP-C15-001", "Do write-ahead intent crash boundaries recover via DLQ?",
         "no lost/duplicate task", "loss or duplicate", "intent_loss", "FIXTURE_ONLY"),
        ("EXP-C19-001", "Does capability verification require a non-empty attributable receipt?",
         "empty receipt -> not verified", "empty counts", "empty_receipt_pass", "FIXTURE_ONLY"),
        ("EXP-C21-001", "Does every Doctor diagnosis reach closure or explicit escalation?",
         "closed or escalated", "dangling", "dangling_diagnosis", "FIXTURE_ONLY"),
        ("EXP-C23-001", "Does the owner capability matrix reflect fresh runtime evidence?",
         "fresh evidence only", "stale matrix", "stale_matrix", "FIXTURE_ONLY"),
    ]
    results = {"ok": 0, "errors": []}
    for eid, question, hypothesis, null_hypothesis, falsifier, mode in experiments:
        card = dict(base)
        card.update({"experiment_id": eid, "question": question,
                     "hypothesis": hypothesis, "null_hypothesis": null_hypothesis,
                     "falsifier": falsifier, "execution_mode": mode})
        out = register_experiment(card)
        if out.get("ok"):
            results["ok"] += 1
        else:
            results["errors"].append((eid, out.get("errors")))
    return results


def conclude_experiment(experiment_id: str, *, result: str,
                        evidence_refs: list | None = None,
                        ts: str | None = None, note: str = "") -> dict:
    """Append-only conclusion. Does not rewrite the preregistration card.

    ``result`` must be in the closed result set. CANARY_PROPOSED cards may be
    concluded INCONCLUSIVE until an owner live gate; they must not be marked
    SUPPORTED from fixture evidence alone.
    """
    eid = str(experiment_id or "").strip()
    if not eid:
        return {"ok": False, "errors": ["experiment_id-required"]}
    if result not in _RESULTS:
        return {"ok": False, "errors": [f"invalid-result-{result}"]}
    rec = {
        "experiment_id": eid,
        "ts": ts or _now_iso(),
        "kind": "conclusion",
        "result": result,
        "evidence_refs": list(evidence_refs or []),
        "note": str(note or ""),
    }
    return append_record("DECISION", rec)


def latest_conclusions(path: Path | None = None) -> dict[str, dict]:
    """Last DECISION conclusion per experiment_id (append-only view)."""
    ledger = path or _ledger("DECISION")
    last: dict[str, dict] = {}
    if not ledger.is_file():
        return last
    for line in ledger.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if not isinstance(row, dict) or row.get("kind") != "conclusion":
            continue
        eid = str(row.get("experiment_id") or "")
        if eid:
            last[eid] = row
    return last
