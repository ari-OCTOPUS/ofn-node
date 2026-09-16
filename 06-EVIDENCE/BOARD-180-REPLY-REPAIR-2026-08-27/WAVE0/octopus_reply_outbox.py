#!/usr/bin/env python3
"""Durable reply outbox and retry state machine for board 180.

INPUT_PROCESSED only after REPLY_ACKED. Frozen response bytes are immutable.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import uuid
from pathlib import Path
from typing import Any, Callable

_UUID = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)

from octomesh_common import (
    atomic_write,
    audit_append,
    canonical,
    compute_checksum,
    load_json,
    parse_utc,
    utc_now,
)

STATES = (
    "CLAIMED",
    "PROCESSING",
    "RESPONSE_FROZEN",
    "REPLY_PENDING",
    "REPLY_TRANSMITTING",
    "REPLY_ACKED",
    "INPUT_PROCESSED",
    "RETRY_WAIT",
    "FAILED_TERMINAL",
    "OWNER_REVIEW",
    "ORPHANED_REPLY_PENDING",
    "ORPHANED_RESPONSE_MISSING",
)

TransmitFn = Callable[[dict[str, Any]], dict[str, Any]]


def mesh_root() -> Path:
    return Path(os.environ.get("OCTOMESH_ROOT", "/root/octopus-mesh"))


def replies_dir() -> Path:
    p = mesh_root() / "state" / "replies"
    for sub in ("pending", "acked", "meta", "circuit"):
        (p / sub).mkdir(parents=True, exist_ok=True)
        os.chmod(p / sub, 0o700)
    os.chmod(p, 0o700)
    return p


def prediction_path(message_id: str) -> Path:
    return mesh_root() / "state" / "cognition" / f"prediction-{message_id}.json"


def processed_index_path() -> Path:
    p = mesh_root() / "state" / "cognition" / "processed_ids.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    if not p.exists():
        p.write_text("{}\n", encoding="utf-8")
        os.chmod(p, 0o600)
    return p


def response_bytes(response: dict[str, Any]) -> bytes:
    return canonical(response).encode("utf-8")


def response_sha256(response: dict[str, Any]) -> str:
    return hashlib.sha256(response_bytes(response)).hexdigest()


def reply_idempotency_key(original_message_id: str, resp_sha: str) -> str:
    return f"reply:{original_message_id}:{resp_sha}"


def pending_path(idem_key: str) -> Path:
    name = hashlib.sha256(idem_key.encode("utf-8")).hexdigest() + ".json"
    return replies_dir() / "pending" / name


def acked_path(idem_key: str) -> Path:
    name = hashlib.sha256(idem_key.encode("utf-8")).hexdigest() + ".json"
    return replies_dir() / "acked" / name


def meta_path(original_message_id: str) -> Path:
    return replies_dir() / "meta" / f"{original_message_id}.json"


def fsync_dir(path: Path) -> None:
    fd = os.open(str(path), os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def write_atomic_bytes(dest: Path, data: bytes) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(f".{dest.name}.{os.getpid()}.{uuid.uuid4().hex[:8]}.tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        os.write(fd, data)
        os.fsync(fd)
    finally:
        os.close(fd)
    os.replace(tmp, dest)
    fsync_dir(dest.parent)


def load_meta(original_message_id: str) -> dict[str, Any] | None:
    p = meta_path(original_message_id)
    if not p.is_file():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def save_meta(meta: dict[str, Any]) -> None:
    write_atomic_bytes(meta_path(str(meta["original_message_id"])),
                       (json.dumps(meta, ensure_ascii=False, indent=2) + "\n").encode())


def reply_acked(original_message_id: str) -> bool:
    meta = load_meta(original_message_id)
    if meta and meta.get("state") in {"REPLY_ACKED", "INPUT_PROCESSED"}:
        return True
    return acked_path_exists(original_message_id)


def acked_path_exists(original_message_id: str) -> bool:
    meta = load_meta(original_message_id)
    if not meta:
        return False
    key = meta.get("reply_idempotency_key")
    return bool(key) and acked_path(str(key)).is_file()


def load_frozen_response(message_id: str) -> dict[str, Any] | None:
    p = prediction_path(message_id)
    if not p.is_file():
        return None
    try:
        blob = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    art = blob.get("frozen_artifact") if isinstance(blob, dict) else None
    return art if isinstance(art, dict) else None


def freeze_sha_file(message_id: str) -> str | None:
    p = mesh_root() / "state" / "cognition" / f"prediction-{message_id}.sha256"
    if not p.is_file():
        return None
    return p.read_text(encoding="utf-8").strip() or None


def build_reply_envelope(original: dict[str, Any], response: dict[str, Any],
                         resp_sha: str) -> dict[str, Any]:
    idem = reply_idempotency_key(str(original.get("message_id")), resp_sha)
    reply_id = str(uuid.uuid5(uuid.NAMESPACE_URL, idem))
    now = utc_now()
    try:
        from datetime import timedelta
        expires = (parse_utc(now) + timedelta(seconds=3600)).isoformat().replace("+00:00", "Z")
    except Exception:
        expires = now
    nodes = load_json(mesh_root() / "config" / "nodes.json")["nodes"]
    sender_role = str(nodes.get("180", {}).get("role") or "quality-brain")
    msg = {
        "envelope_version": 1,
        "message_id": reply_id,
        "run_id": str(original.get("run_id") or original.get("message_id")),
        "sender_node": "180",
        "recipient_node": "138",
        "sender_role": sender_role,
        "message_type": "result",
        "scope": "mesh",
        "claim_type": "observation",
        "created_at": now,
        "expires_at": expires,
        "correlation_id": str(original.get("message_id")),
        "idempotency_key": idem,
        "requires_ack": True,
        "may_authorize": False,
        "payload": {
            "response": dict(response),
            "in_reply_to": str(original.get("message_id")),
            "response_sha256": resp_sha,
        },
        "evidence": [],
        "checksum": "",
    }
    msg["checksum"] = compute_checksum(msg)
    return msg


def persist_pending(original: dict[str, Any], response: dict[str, Any],
                    frozen_sha: str) -> dict[str, Any]:
    resp_sha = response_sha256(response)
    idem = reply_idempotency_key(str(original.get("message_id")), resp_sha)
    existing = load_meta(str(original.get("message_id")))
    if existing and existing.get("response_sha256") == resp_sha and existing.get("wire"):
        # immutable replay of the same artifact
        if existing.get("state") not in {"REPLY_ACKED", "INPUT_PROCESSED"}:
            existing["state"] = "REPLY_PENDING"
            save_meta(existing)
        return existing
    if existing and existing.get("response_sha256") and existing.get("response_sha256") != resp_sha:
        raise ValueError("frozen_response_immutable_mismatch")
    wire = build_reply_envelope(original, response, resp_sha)
    rec = {
        "state": "REPLY_PENDING",
        "original_message_id": str(original.get("message_id")),
        "original_idempotency_key": str(original.get("idempotency_key") or ""),
        "correlation_id": str(original.get("correlation_id") or original.get("message_id")),
        "reply_message_id": wire["message_id"],
        "reply_idempotency_key": idem,
        "response_sha256": resp_sha,
        "frozen_prediction_sha256": frozen_sha,
        "sender_node": "180",
        "recipient_node": "138",
        "may_authorize": False,
        "retry_count": 0,
        "activation_attempts": 0,
        "created_at": utc_now(),
        "wire": wire,
        "requires_ack": True,
        "inject_send_failure_once": bool((original.get("payload") or {}).get("inject_send_failure_once")),
        "inject_send_failure_consumed": False,
    }
    blob = (json.dumps(rec, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    write_atomic_bytes(pending_path(idem), blob)
    save_meta(rec)
    audit_append(mesh_root() / "audit", {
        "ts": utc_now(),
        "message_id": rec["original_message_id"],
        "run_id": original.get("run_id"),
        "sender": "180",
        "recipient": "138",
        "type": "result",
        "status": "response_frozen",
        "reason": "response_frozen",
        "checksum": rec["response_sha256"][:16],
    })
    rec["state"] = "REPLY_PENDING"
    save_meta(rec)
    return rec


def circuit_path() -> Path:
    return replies_dir() / "circuit" / "transport.json"


def circuit_open() -> bool:
    p = circuit_path()
    if not p.is_file():
        return False
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    until = str(data.get("open_until") or "")
    if not until:
        return False
    try:
        return parse_utc(until) > parse_utc(utc_now())
    except (ValueError, TypeError):
        return False


def circuit_record(success: bool) -> None:
    p = circuit_path()
    data = {"failures": 0, "open_until": ""}
    if p.is_file():
        try:
            data.update(json.loads(p.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError):
            pass
    if success:
        data["failures"] = 0
        data["open_until"] = ""
    else:
        data["failures"] = int(data.get("failures") or 0) + 1
        if data["failures"] >= 3:
            from datetime import timedelta
            data["open_until"] = (parse_utc(utc_now()) + timedelta(seconds=60)).isoformat().replace("+00:00", "Z")
    write_atomic_bytes(p, (json.dumps(data, indent=2) + "\n").encode())


TRANSMIT_HOOK = os.environ.get("OCTOMESH_REPLY_TRANSMIT") or ""
TRANSMIT_CALLS = 0



def default_transmit(wire: dict[str, Any]) -> dict[str, Any]:
    hook = os.environ.get("OCTOMESH_REPLY_TRANSMIT") or TRANSMIT_HOOK or ""
    if hook == "fail":
        return {"returncode": 1, "remote_stdout": "", "remote_stderr_prefix": "injected_fail"}
    if hook == "ack":
        return {"returncode": 0,
                "remote_stdout": json.dumps({"status": "ack", "message_id": wire["message_id"]}),
                "remote_stderr_prefix": ""}
    if hook == "duplicate":
        return {"returncode": 0,
                "remote_stdout": json.dumps({"status": "duplicate", "message_id": wire["message_id"]}),
                "remote_stderr_prefix": ""}
    if hook == "timeout":
        return {"returncode": 1, "remote_stdout": "", "remote_stderr_prefix": "timeout"}
    nodes = load_json(mesh_root() / "config" / "nodes.json")["nodes"]
    from octomesh_send import transmit
    return transmit(wire, nodes, mesh_root() / "config" / "nodes.json")


def parse_verdict(result: dict[str, Any]) -> str:
    out = str(result.get("remote_stdout") or "").strip()
    try:
        verdict = json.loads(out) if out else {}
    except json.JSONDecodeError:
        verdict = {}
    rc = result.get("returncode")
    try:
        rc_i = int(rc)
    except (TypeError, ValueError):
        rc_i = 1
    if rc_i == 0 and str(verdict.get("status")) in ("ack", "duplicate"):
        return str(verdict.get("status"))
    return "retryable"


def mark_input_processed(original_message_id: str, original_idem: str, artifact_sha: str) -> None:
    path = processed_index_path()
    data = json.loads(path.read_text(encoding="utf-8") or "{}")
    prev = data.get(original_message_id) if isinstance(data.get(original_message_id), dict) else {}
    # Additive: do not rewrite prior ts/hash evidence.
    if "ts" not in prev:
        prev["ts"] = utc_now()
    if artifact_sha and not prev.get("artifact_sha256"):
        prev["artifact_sha256"] = artifact_sha
    prev["immutable"] = True
    prev["reply_acked"] = True
    prev["reply_acked_at"] = utc_now()
    data[original_message_id] = prev
    if original_idem:
        idem_prev = data.get(original_idem) if isinstance(data.get(original_idem), dict) else {}
        if "ts" not in idem_prev:
            idem_prev["ts"] = prev.get("ts") or utc_now()
        if artifact_sha and not idem_prev.get("artifact_sha256"):
            idem_prev["artifact_sha256"] = prev.get("artifact_sha256") or artifact_sha
        idem_prev["immutable"] = True
        idem_prev["reply_acked"] = True
        idem_prev["reply_acked_at"] = prev["reply_acked_at"]
        data[original_idem] = idem_prev
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def on_acked(rec: dict[str, Any], verdict: str) -> dict[str, Any]:
    rec = dict(rec)
    rec["state"] = "REPLY_ACKED"
    rec["ack_status"] = verdict
    rec["acked_at"] = utc_now()
    blob = (json.dumps(rec, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    dest = acked_path(str(rec["reply_idempotency_key"]))
    src = pending_path(str(rec["reply_idempotency_key"]))
    write_atomic_bytes(dest, blob)
    if src.is_file():
        src.unlink()
        fsync_dir(src.parent)
    save_meta(rec)
    audit_append(mesh_root() / "audit", {
        "ts": utc_now(),
        "message_id": rec["original_message_id"],
        "run_id": rec.get("correlation_id"),
        "sender": "180",
        "recipient": "138",
        "type": "result",
        "status": "reply_acked",
        "reason": "reply_acked",
        "checksum": str(rec.get("response_sha256") or "")[:16],
    })
    mark_input_processed(str(rec["original_message_id"]),
                         str(rec.get("original_idempotency_key") or ""),
                         str(rec.get("frozen_prediction_sha256") or rec.get("response_sha256")))
    rec["state"] = "INPUT_PROCESSED"
    save_meta(rec)
    audit_append(mesh_root() / "audit", {
        "ts": utc_now(),
        "message_id": rec["original_message_id"],
        "run_id": rec.get("correlation_id"),
        "sender": "180",
        "recipient": "138",
        "type": "result",
        "status": "processed",
        "reason": "input_processed_after_reply_ack",
        "checksum": str(rec.get("response_sha256") or "")[:16],
    })
    circuit_record(True)
    return rec


def _ack_check_hook() -> str | None:
    hook = os.environ.get("OCTOMESH_REPLY_TRANSMIT") or TRANSMIT_HOOK or ""
    if hook in ("ack", "duplicate"):
        return hook
    return None


def transmit_pending(rec: dict[str, Any], transmit_fn: TransmitFn | None = None) -> dict[str, Any]:
    global TRANSMIT_CALLS
    if rec.get("state") in {"REPLY_ACKED", "INPUT_PROCESSED"}:
        return rec
    if circuit_open():
        rec = dict(rec)
        rec["state"] = "RETRY_WAIT"
        rec["circuit_open"] = True
        save_meta(rec)
        return rec
    rec = dict(rec)
    if rec.get("inject_send_failure_once") and not rec.get("inject_send_failure_consumed"):
        # isolated hook: first transmit fails for real, freeze stays, no fn(wire)
        rec["inject_send_failure_consumed"] = True
        rec["state"] = "RETRY_WAIT"
        rec["last_error"] = "injected_send_failure_once"
        rec["retry_count"] = int(rec.get("retry_count") or 0) + 1
        save_meta(rec)
        if rec.get("reply_idempotency_key"):
            write_atomic_bytes(pending_path(str(rec["reply_idempotency_key"])),
                               (json.dumps(rec, ensure_ascii=False, indent=2) + "\n").encode())
        return rec
    if rec.get("transmit_handed"):
        # bytes already left the node; never call fn(wire) again
        hook = _ack_check_hook()
        if hook:
            return on_acked(rec, hook)
        last = rec.get("last_transmit_result")
        if isinstance(last, dict):
            verdict = parse_verdict(last)
            if verdict in ("ack", "duplicate"):
                return on_acked(rec, verdict)
        rec["state"] = "RETRY_WAIT"
        rec["last_error"] = rec.get("last_error") or "handed_awaiting_ack"
        save_meta(rec)
        return rec
    rec["state"] = "REPLY_TRANSMITTING"
    save_meta(rec)
    fn = transmit_fn or default_transmit
    try:
        TRANSMIT_CALLS = int(TRANSMIT_CALLS) + 1
        rec["transmit_calls"] = int(rec.get("transmit_calls") or 0) + 1
        result = fn(rec["wire"])
    except Exception as exc:
        rec["state"] = "RETRY_WAIT"
        rec["last_error"] = type(exc).__name__
        rec["retry_count"] = int(rec.get("retry_count") or 0) + 1
        save_meta(rec)
        if rec.get("reply_idempotency_key"):
            write_atomic_bytes(pending_path(str(rec["reply_idempotency_key"])),
                               (json.dumps(rec, ensure_ascii=False, indent=2) + "\n").encode())
        circuit_record(False)
        return rec
    # fn returned: latch BEFORE on_acked so kill-after-send is 1->1
    rec["transmit_handed"] = True
    rec["transmit_handed_at"] = utc_now()
    rec["last_transmit_result"] = result
    save_meta(rec)
    if rec.get("reply_idempotency_key"):
        write_atomic_bytes(pending_path(str(rec["reply_idempotency_key"])),
                           (json.dumps(rec, ensure_ascii=False, indent=2) + "\n").encode())
    verdict = parse_verdict(result)
    if verdict in ("ack", "duplicate"):
        return on_acked(rec, verdict)
    rec["state"] = "RETRY_WAIT"
    rec["last_error"] = str(result.get("remote_stderr_prefix") or "retryable")
    rec["retry_count"] = int(rec.get("retry_count") or 0) + 1
    save_meta(rec)
    write_atomic_bytes(pending_path(str(rec["reply_idempotency_key"])),
                       (json.dumps(rec, ensure_ascii=False, indent=2) + "\n").encode())
    circuit_record(False)
    return rec


def backoff_seconds() -> tuple[int, int]:
    if os.environ.get("OCTOMESH_REPLY_BACKOFF") == "0":
        return (0, 0)
    return (5, 15)


def retry_pending_this_activation(transmit_fn: TransmitFn | None = None,
                                  max_attempts: int = 2) -> list[dict[str, Any]]:
    out = []
    waits = backoff_seconds()
    pending_root = replies_dir() / "pending"
    files = sorted(pending_root.glob("*.json")) if pending_root.is_dir() else []
    for p in files:
        if p.name.endswith(".moved"):
            continue
        try:
            rec = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if rec.get("state") in {"REPLY_ACKED", "INPUT_PROCESSED"}:
            continue
        attempts = 0
        while attempts < max_attempts and rec.get("state") not in {"REPLY_ACKED", "INPUT_PROCESSED"}:
            rec = transmit_pending(rec, transmit_fn)
            attempts += 1
            rec["activation_attempts"] = int(rec.get("activation_attempts") or 0) + 1
            save_meta(rec)
            if rec.get("state") in {"REPLY_ACKED", "INPUT_PROCESSED"}:
                if p.is_file():
                    p.unlink()
                    fsync_dir(p.parent)
                break
            write_atomic_bytes(p, (json.dumps(rec, ensure_ascii=False, indent=2) + "\n").encode())
            if rec.get("circuit_open"):
                break
            import time
            delay = waits[0] if attempts == 1 else waits[1]
            if delay:
                time.sleep(delay)
        out.append(rec)
    return out


def find_receiver_receipt(original_message_id: str) -> dict[str, Any] | None:
    root = mesh_root() / "receipts"
    if not root.is_dir():
        return None
    paths = list(root.glob("*.json"))
    control = root / "control"
    if control.is_dir():
        paths.extend(control.glob("*.json"))
    for p in paths:
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(data, dict):
            continue
        status = str(data.get("status") or "")
        if status not in {"ack", "duplicate"}:
            continue
        payload = data.get("payload") if isinstance(data.get("payload"), dict) else {}
        in_reply = str(payload.get("in_reply_to") or data.get("in_reply_to")
                       or data.get("correlation_id") or "")
        if in_reply == original_message_id:
            return data
    return None


def scan_orphans() -> list[dict[str, Any]]:
    """Find processed_ids entries that required a reply but have no reply_acked."""
    idx = processed_index_path()
    data = json.loads(idx.read_text(encoding="utf-8") or "{}")
    reports = []
    seen = set()
    for key, rec in data.items():
        if not isinstance(rec, dict):
            continue
        mid = str(key)
        if not _UUID.match(mid):
            continue
        if mid in seen:
            continue
        if rec.get("reply_acked") is True or reply_acked(mid):
            continue
        seen.add(mid)
        frozen = load_frozen_response(mid)
        meta = load_meta(mid)
        receipt = find_receiver_receipt(mid)
        if receipt:
            reports.append({
                "original_message_id": mid,
                "classification": "RECEIVER_RECEIPT_LOCAL_REPAIR",
                "has_frozen": bool(frozen),
                "has_receiver_receipt": True,
            })
        elif frozen and not (meta and meta.get("state") in {"REPLY_ACKED", "INPUT_PROCESSED"}):
            reports.append({
                "original_message_id": mid,
                "classification": "ORPHANED_REPLY_PENDING",
                "has_frozen": True,
                "has_receiver_receipt": False,
            })
        elif not frozen:
            reports.append({
                "original_message_id": mid,
                "classification": "ORPHANED_RESPONSE_MISSING",
                "has_frozen": False,
            })
    return reports


def recover_orphan(original: dict[str, Any], transmit_fn: TransmitFn | None = None) -> dict[str, Any]:
    mid = str(original.get("message_id"))
    if reply_acked(mid):
        return {"status": "already_acked", "message_id": mid, "model_called": False}
    receipt = find_receiver_receipt(mid)
    if receipt:
        frozen = load_frozen_response(mid)
        sha = freeze_sha_file(mid) or (response_sha256(frozen) if frozen else "")
        rec = load_meta(mid) or {
            "original_message_id": mid,
            "original_idempotency_key": str(original.get("idempotency_key") or ""),
            "reply_idempotency_key": reply_idempotency_key(mid, sha) if sha else f"reply:{mid}:unknown",
            "response_sha256": sha,
            "frozen_prediction_sha256": sha,
            "correlation_id": str(original.get("correlation_id") or mid),
        }
        rec["receiver_receipt"] = {"status": receipt.get("status")}
        on_acked(rec, str(receipt.get("status") or "ack"))
        return {"status": "already_acked", "message_id": mid, "model_called": False,
                "local_repair": True, "resend": False}
    frozen = load_frozen_response(mid)
    if frozen is None:
        rec = {
            "state": "ORPHANED_RESPONSE_MISSING",
            "original_message_id": mid,
            "escalation": "138",
            "model_rerun": False,
        }
        save_meta(rec)
        return {"status": "orphaned_response_missing", "message_id": mid, "model_called": False}
    sha = freeze_sha_file(mid) or response_sha256(frozen)
    pending = persist_pending(original, frozen, sha)
    pending = transmit_pending(pending, transmit_fn)
    return {
        "status": "recovered_pending" if pending.get("state") not in {"INPUT_PROCESSED", "REPLY_ACKED"} else "recovered_acked",
        "message_id": mid,
        "reply_state": pending.get("state"),
        "response_sha256": pending.get("response_sha256"),
        "model_called": False,
        "reply_idempotency_key": pending.get("reply_idempotency_key"),
    }
