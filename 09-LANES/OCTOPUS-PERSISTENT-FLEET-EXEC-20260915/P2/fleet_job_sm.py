#!/usr/bin/env python3
"""P2 fleet job state machine — dry/bootstrap. 138 sole commander. No NATS enqueue."""
from __future__ import annotations

import hashlib
import json
import time
import uuid
from pathlib import Path

ROOT = Path("/home/ari/ofn/state/fleet-jobs")
LEDGER = ROOT / "fleet_jobs.jsonl"
INDEX = ROOT / "idempotency_index.json"
SCHEMA = ROOT / "schemas" / "fleet_job.v1.schema.json"

ALLOWED = {
    "QUEUED": {"LEASED", "EXPIRED", "REJECTED", "UNKNOWN"},
    "LEASED": {"RUNNING", "EXPIRED", "FAILED", "UNKNOWN"},
    "RUNNING": {"ACK_RESULT", "FAILED", "EXPIRED", "UNKNOWN"},
    "ACK_RESULT": {"PERSISTED", "UNKNOWN"},
    "PERSISTED": {"CLOSED", "UNKNOWN"},
    "FAILED": {"QUEUED", "EXPIRED", "UNKNOWN"},
    "CLOSED": set(),
    "EXPIRED": set(),
    "REJECTED": set(),
    "UNKNOWN": set(),
}

REGISTERED_WORKERS = {"100", "160", "193", "114", "180", "182", "138"}


def _utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _sha(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _load_index() -> dict:
    if INDEX.exists():
        return json.loads(INDEX.read_text())
    return {}


def _save_index(idx: dict) -> None:
    INDEX.parent.mkdir(parents=True, exist_ok=True)
    INDEX.write_text(json.dumps(idx, indent=2) + "\n")


def _append(job: dict) -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    with LEDGER.open("a", encoding="utf-8") as f:
        f.write(json.dumps(job, ensure_ascii=False) + "\n")


def create_job(*, job_type: str, input_obj: dict, worker_node_id: str, deadline: str,
               idempotency_key: str | None = None) -> dict:
    if worker_node_id not in REGISTERED_WORKERS:
        raise ValueError("REJECTED: worker not registered")
    key = idempotency_key or _sha({"type": job_type, "input": input_obj, "worker": worker_node_id})
    idx = _load_index()
    if key in idx:
        # idempotent: return existing job snapshot (no dup side effect)
        return {"ok": True, "idempotent_hit": True, "job_id": idx[key], "external_effects": 0}
    job = {
        "schema": "fleet_job.v1",
        "job_id": f"job-{uuid.uuid4().hex[:16]}",
        "idempotency_key": key,
        "type": job_type,
        "input_hash": _sha(input_obj),
        "worker_node_id": worker_node_id,
        "deadline": deadline,
        "lease_expiry": None,
        "state": "QUEUED",
        "attempt": 0,
        "ack_at": None,
        "result_hash": None,
        "receipt_id": None,
        "commander_node_id": "138",
        "customer_send": False,
        "external_effects": 0,
        "bus": "SHADOW_LOCAL_JSONL",
        "notes": "P2 dry bootstrap — not JetStream durable (0 consumers)",
    }
    if job_type.lower() in {"shell", "bash", "sh"}:
        job["state"] = "REJECTED"
        job["notes"] = "DENY shell-as-job_type"
        _append(job)
        return {"ok": False, "job": job}
    idx[key] = job["job_id"]
    _save_index(idx)
    _append(job)
    return {"ok": True, "idempotent_hit": False, "job": job, "external_effects": 0}


def transition(job: dict, to_state: str, **fields) -> dict:
    cur = job["state"]
    if to_state not in ALLOWED.get(cur, set()):
        raise ValueError(f"illegal transition {cur} -> {to_state}")
    job = dict(job)
    job["state"] = to_state
    job.update({k: v for k, v in fields.items() if v is not None})
    fields = {k: v for k, v in fields.items() if k not in {"bump_attempt", "retry"}}
    if to_state == "LEASED" and job.get("attempt", 0) == 0:
        job["attempt"] = 1
    _append(job)
    return job


def dry_happy_path(worker: str = "100") -> dict:
    """QUEUED→…→CLOSED with external_effects=0; ACK≠success until PERSISTED/CLOSED."""
    created = create_job(
        job_type="echo_capability_probe",
        input_obj={"probe": "p2-dry", "n": 1},
        worker_node_id=worker,
        deadline="2099-01-01T00:00:00Z",
        idempotency_key=f"p2-dry-happy-{worker}",
    )
    if created.get("idempotent_hit"):
        return created
    job = created["job"]
    job = transition(job, "LEASED", lease_expiry="2099-01-01T00:05:00Z", bump_attempt=True)
    job = transition(job, "RUNNING")
    # ACK_RESULT is not success yet
    result = {"ok": True, "output": "dry"}
    job = transition(job, "ACK_RESULT", ack_at=_utc(), result_hash=_sha(result))
    receipt_id = f"rcpt-{job['job_id']}"
    job = transition(job, "PERSISTED", receipt_id=receipt_id)
    job = transition(job, "CLOSED")
    return {"ok": True, "job": job, "external_effects": 0, "ack_is_not_success": True}


def mark_unknown(job: dict, reason: str) -> dict:
    return transition(job, "UNKNOWN", notes=reason)


def test_idempotency() -> None:
    a = create_job(
        job_type="echo_capability_probe",
        input_obj={"probe": "idem", "n": 1},
        worker_node_id="160",
        deadline="2099-01-01T00:00:00Z",
        idempotency_key="p2-test-idem-1",
    )
    b = create_job(
        job_type="echo_capability_probe",
        input_obj={"probe": "idem", "n": 1},
        worker_node_id="160",
        deadline="2099-01-01T00:00:00Z",
        idempotency_key="p2-test-idem-1",
    )
    assert a["ok"] and not a.get("idempotent_hit")
    assert b["ok"] and b.get("idempotent_hit") is True
    assert a["job"]["job_id"] == b["job_id"]
    assert a["job"]["external_effects"] == 0


def test_unknown() -> None:
    created = create_job(
        job_type="echo_capability_probe",
        input_obj={"probe": "unk"},
        worker_node_id="114",
        deadline="2099-01-01T00:00:00Z",
        idempotency_key="p2-test-unknown-1",
    )
    job = created["job"]
    job = transition(job, "LEASED", lease_expiry="2099-01-01T00:05:00Z")
    job = transition(job, "RUNNING")
    job = mark_unknown(job, "crash_without_durable_result")
    assert job["state"] == "UNKNOWN"
    # must not invent CLOSED/success
    try:
        transition(job, "CLOSED")
        raise AssertionError("UNKNOWN must not go to CLOSED")
    except ValueError:
        pass


def test_shell_denied() -> None:
    r = create_job(
        job_type="shell",
        input_obj={"cmd": "echo no"},
        worker_node_id="100",
        deadline="2099-01-01T00:00:00Z",
        idempotency_key="p2-test-shell-1",
    )
    assert r["ok"] is False and r["job"]["state"] == "REJECTED"


if __name__ == "__main__":
    import sys
    ROOT.mkdir(parents=True, exist_ok=True)
    (ROOT / "schemas").mkdir(parents=True, exist_ok=True)
    cmd = sys.argv[1] if len(sys.argv) > 1 else "selftest"
    if cmd == "selftest":
        test_idempotency()
        test_unknown()
        test_shell_denied()
        happy = dry_happy_path("100")
        assert happy["job"]["state"] == "CLOSED"
        assert happy["external_effects"] == 0
        print(json.dumps({"selftest": "PASS", "happy_job_id": happy["job"]["job_id"]}, indent=2))
    elif cmd == "dry-happy":
        print(json.dumps(dry_happy_path(sys.argv[2] if len(sys.argv) > 2 else "100"), indent=2))
    else:
        raise SystemExit(f"unknown cmd {cmd}")
