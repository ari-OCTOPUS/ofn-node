#!/usr/bin/env python3
# ISOLATED PATCH ? skip-continue already_processed in candidate loop.
# NOT live. Do not copy to bin/ until PC GO.
# source_live_sha256=72e3b3a37592644ef368d70b6e383c296ea7e47023c781ddc4e42752cfddc9f8
"""Event-driven cognitive worker for board 180.

RECEIVE → PROCESS ONCE → FREEZE → REPLY_PENDING → TRANSMIT → ACK → INPUT_PROCESSED
Retry never re-runs the model. Frozen response bytes are immutable.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

MESH = Path(os.environ.get("OCTOMESH_ROOT", "/root/octopus-mesh"))
sys.path.insert(0, str(MESH / "bin"))

from octomesh_common import (  # noqa: E402
    parse_utc,
    utc_now,
    verify_checksum,
)
import octopus_model_adapter as model_adapter  # noqa: E402
import octopus_self_model as self_model  # noqa: E402
import octopus_reply_outbox as outbox  # noqa: E402

ALLOWED_TYPES = {"task", "proposal", "critique", "ping"}
CONTROL_TYPES = {"ack", "nack"}
SAFE_EXIT = {
    "ok", "idle", "dry-run-valid", "paused", "duplicate_blocked", "rejected",
    "reply_pending", "retry_wait", "overlap_blocked", "recovered_pending",
    "recovered_acked", "orphaned_response_missing", "circuit_open",
}


def pause_path(override: str | None = None) -> Path:
    if override:
        return Path(override)
    return MESH / "state/OWNER_PAUSE"


def pause_active(override: str | None = None) -> bool:
    return pause_path(override).is_file()


def processed_index() -> Path:
    return outbox.processed_index_path()


def already_processed(message_id: str, idempotency_key: str) -> bool:
    data = json.loads(processed_index().read_text(encoding="utf-8") or "{}")
    rec = data.get(message_id) or (data.get(idempotency_key) if idempotency_key else None)
    if not isinstance(rec, dict):
        return False
    return bool(rec.get("reply_acked")) or outbox.reply_acked(message_id)


def freeze_prediction(task: dict[str, Any], response: dict[str, Any]) -> str:
    dest = MESH / "state/cognition" / f"prediction-{task.get('message_id')}.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    blob = {
        "cycle_id": str(task.get("run_id") or task.get("message_id")),
        "task_id": task.get("message_id"),
        "agent": "180",
        "prior_confidence": response.get("confidence"),
        "falsifier_proposed": bool(response.get("falsifier")),
        "alternatives_listed": bool(response.get("alternatives")),
        "scope_claimed": response.get("scope"),
        "claim_type": response.get("claim_type"),
        "submitted_at": utc_now(),
        "frozen_artifact": response,
    }
    text = json.dumps(blob, ensure_ascii=False, sort_keys=True)
    dest.write_text(text + "\n", encoding="utf-8")
    os.chmod(dest, 0o600)
    sha = hashlib.sha256(text.encode()).hexdigest()
    (MESH / "state/cognition" / f"prediction-{task.get('message_id')}.sha256").write_text(
        sha + "\n", encoding="utf-8"
    )
    return sha


def validate_envelope(msg: dict[str, Any]) -> str | None:
    if not isinstance(msg, dict):
        return "not_object"
    if str(msg.get("message_type")) in CONTROL_TYPES:
        return "control_plane_not_cognitive"
    if str(msg.get("message_type")) not in ALLOWED_TYPES:
        return "role_incompatible_type"
    if msg.get("may_authorize") is True:
        return "may_authorize_true_rejected"
    if msg.get("may_authorize") not in (False, None):
        return "may_authorize_invalid"
    if not verify_checksum(msg):
        return "checksum_mismatch"
    try:
        if parse_utc(str(msg.get("expires_at"))) <= parse_utc(utc_now()):
            return "expired"
    except (ValueError, TypeError):
        return "expires_at_invalid"
    if msg.get("recipient_node") not in (None, "180"):
        return "wrong_recipient"
    return None


def required_fields_ok(response: dict[str, Any]) -> bool:
    for key in ("claim_type", "scope", "confidence", "evidence", "alternatives", "falsifier"):
        if key not in response:
            return False
    return True


def _result_from_pending(pending: dict[str, Any], model_called: bool) -> dict[str, Any]:
    st = str(pending.get("state") or "")
    status = "ok" if st in {"REPLY_ACKED", "INPUT_PROCESSED"} else "reply_pending"
    if st == "RETRY_WAIT":
        status = "retry_wait"
    return {
        "status": status,
        "reply_state": st,
        "message_id": pending.get("original_message_id"),
        "frozen_artifact_sha256": pending.get("frozen_prediction_sha256"),
        "response_sha256": pending.get("response_sha256"),
        "reply_idempotency_key": pending.get("reply_idempotency_key"),
        "reply_message_id": pending.get("reply_message_id"),
        "immutable_after_send": True,
        "executed_locally": False,
        "may_authorize": False,
        "model_called": model_called,
        "input_processed": st == "INPUT_PROCESSED",
    }


def handle_task(msg: dict[str, Any], *, call_model: bool, pause: str | None) -> dict[str, Any]:
    if pause_active(pause):
        return {"status": "paused", "reason": "OWNER_PAUSE", "model_called": False}
    mid = str(msg.get("message_id"))
    idem = str(msg.get("idempotency_key") or "")
    if already_processed(mid, idem):
        return {"status": "duplicate_blocked", "reason": "already_processed",
                "message_id": mid, "model_called": False}
    frozen = outbox.load_frozen_response(mid)
    err = validate_envelope(msg)
    if frozen is not None:
        # Freeze happened during PROCESS ONCE. Retry never re-runs the model.
        # Expired originals still retry the same frozen bytes unless the
        # envelope is otherwise invalid.
        if err and err != "expired":
            return {"status": "rejected", "reason": err, "model_called": False}
        sha = outbox.freeze_sha_file(mid) or outbox.response_sha256(frozen)
        pending = outbox.persist_pending(msg, frozen, sha)
        if err == "expired" and pending.get("state") not in {"REPLY_ACKED", "INPUT_PROCESSED"}:
            pending = dict(pending)
            pending["original_expired"] = True
        if not call_model:
            return _result_from_pending(pending, False)
        pending = outbox.transmit_pending(pending)
        out = _result_from_pending(pending, False)
        out["recovered"] = True
        if err == "expired" and pending.get("state") not in {"INPUT_PROCESSED", "REPLY_ACKED"}:
            if pending.get("state") == "OWNER_REVIEW":
                out["status"] = "owner_review"
        return out
    if err:
        return {"status": "rejected", "reason": err, "model_called": False}
    if not call_model:
        return {"status": "dry-run-valid", "message_id": mid, "model_called": False}
    if pause_active(pause):
        return {"status": "paused", "reason": "OWNER_PAUSE", "model_called": False}
    runtime = model_adapter.discover_runtime()
    response = model_adapter.complete_structured(msg, runtime)
    if not required_fields_ok(response):
        return {"status": "rejected", "reason": "response_schema_invalid", "model_called": True}
    sha = freeze_prediction(msg, response)
    pending = outbox.persist_pending(msg, response, sha)
    pending = outbox.transmit_pending(pending)
    out = _result_from_pending(pending, True)
    out["response"] = response
    return out


def load_json_file(path: Path) -> tuple[dict | None, str | None]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None, "malformed_json"
    except OSError as exc:
        return None, type(exc).__name__
    if not isinstance(data, dict):
        return None, "not_object"
    return data, None


def acquire_lock() -> Any:
    lock_path = MESH / "state/cognition/worker.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        os.close(fd)
        return None
    return fd


def recover_inbox_orphans() -> dict[str, Any] | None:
    inbox = MESH / "inbox"
    files = sorted(inbox.glob("*.json")) if inbox.is_dir() else []
    for path in files:
        data, err = load_json_file(path)
        if err or data is None:
            continue
        mid = str(data.get("message_id") or "")
        if not mid:
            continue
        if already_processed(mid, str(data.get("idempotency_key") or "")):
            continue
        frozen = outbox.load_frozen_response(mid)
        idx = json.loads(processed_index().read_text(encoding="utf-8") or "{}")
        listed = mid in idx
        if listed and frozen is None:
            return {"status": "orphaned_response_missing", "message_id": mid,
                    "model_called": False, "escalation": "138"}
        if frozen is not None:
            return handle_task(data, call_model=True, pause=None)
    reports = outbox.scan_orphans()
    for rep in reports:
        if rep.get("classification") == "ORPHANED_RESPONSE_MISSING":
            return {"status": "orphaned_response_missing",
                    "message_id": rep.get("original_message_id"),
                    "model_called": False, "escalation": "138"}
    return None


def run_once(args: argparse.Namespace) -> dict[str, Any]:
    if pause_active(args.pause_path):
        return {"status": "paused", "reason": "OWNER_PAUSE", "model_called": False}
    retried = outbox.retry_pending_this_activation()
    if retried:
        last = retried[-1]
        if last.get("state") in {"REPLY_ACKED", "INPUT_PROCESSED", "RETRY_WAIT", "REPLY_PENDING"}:
            out = _result_from_pending(last, False)
            out["retried"] = True
            if last.get("circuit_open"):
                out["status"] = "circuit_open"
            return out
    recovered = recover_inbox_orphans()
    if recovered is not None:
        return recovered
    if args.fixture:
        path = Path(args.fixture)
        data, err = load_json_file(path)
        if err:
            return {"status": "rejected", "reason": err, "model_called": False}
        assert data is not None
        return handle_task(data, call_model=not args.dry_run, pause=args.pause_path)
    inbox = MESH / "inbox"
    candidates = sorted(inbox.glob("*.json")) if inbox.is_dir() else []
    for path in candidates:
        data, err = load_json_file(path)
        if err == "malformed_json":
            return {"status": "rejected", "reason": "malformed_json", "model_called": False, "path": path.name}
        if err or data is None:
            continue
        if str(data.get("message_type")) in CONTROL_TYPES:
            continue
        err2 = validate_envelope(data)
        if err2:
            continue
        mid = str(data.get("message_id") or "")
        idem = str(data.get("idempotency_key") or "")
        if already_processed(mid, idem):
            continue
        return handle_task(data, call_model=not args.dry_run, pause=args.pause_path)
    return {"status": "idle", "reason": "no_event", "model_called": False}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--foreground", action="store_true")
    parser.add_argument("--fixture", default="")
    parser.add_argument("--pause-path", default="")
    parser.add_argument("--cycles", type=int, default=1)
    parser.add_argument("--sleep", type=float, default=0.0)
    parser.add_argument("--scan-orphans", action="store_true")
    args = parser.parse_args()
    MESH.joinpath("state/cognition").mkdir(parents=True, exist_ok=True)
    self_model.load_or_create()
    lockfd = acquire_lock()
    if lockfd is None:
        print(json.dumps({"status": "overlap_blocked", "reason": "flock", "model_called": False}))
        return 0
    try:
        if args.scan_orphans:
            print(json.dumps({"status": "ok", "orphans": outbox.scan_orphans()}, ensure_ascii=False))
            return 0
        if args.foreground and not args.once:
            last = None
            for i in range(max(1, args.cycles)):
                last = run_once(args)
                last["cycle"] = i + 1
                print(json.dumps(last, ensure_ascii=False))
                if args.sleep:
                    time.sleep(args.sleep)
            return 0 if last and last.get("status") in SAFE_EXIT else 1
        result = run_once(args)
        print(json.dumps(result, ensure_ascii=False))
        if result.get("status") in SAFE_EXIT:
            return 0
        if result.get("reason") in {"malformed_json", "expired", "checksum_mismatch", "already_processed"}:
            return 0
        return 1
    finally:
        try:
            fcntl.flock(lockfd, fcntl.LOCK_UN)
        except OSError:
            pass
        os.close(lockfd)


if __name__ == "__main__":
    raise SystemExit(main())
