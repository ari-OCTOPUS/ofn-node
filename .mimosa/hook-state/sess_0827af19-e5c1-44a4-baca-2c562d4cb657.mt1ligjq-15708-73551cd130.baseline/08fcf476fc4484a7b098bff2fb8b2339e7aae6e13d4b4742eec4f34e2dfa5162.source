#!/usr/bin/env python3
"""Durable, content-minimizing Telegram intent/outbox boundary.

The boundary is opt-in and never performs network I/O itself. Callers provide the
single transport attempt. An uncertain attempt is quarantined rather than retried.
"""
from __future__ import annotations

import contextlib
import contextvars
import hashlib
import json
import os
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

SCHEMA = "telegram-durable-loop/1"
FLAG = "OCTOPUS_TG_DURABLE_OUTBOX"
KILL_SWITCH = "OCTOPUS_TG_LOOP_KILL"

_ALLOWED = {
    "RECEIVED": {"AUTHENTICATED", "AUTH_REJECTED"},
    "AUTHENTICATED": {"INTENT_COMMITTED"},
    "INTENT_COMMITTED": {"DISPATCHED", "RESULT_COMMITTED", "CANCELLED", "DEAD_LETTERED"},
    "DISPATCHED": {"RESULT_COMMITTED", "NEEDS_RECONCILIATION", "CANCELLED", "DEAD_LETTERED"},
    "RESULT_COMMITTED": {"RESPONSE_QUEUED", "CLOSED", "DEAD_LETTERED"},
    "RESPONSE_QUEUED": {"RESPONSE_SENT", "DELIVERY_FAILED", "NEEDS_RECONCILIATION"},
    "RESPONSE_SENT": {"RESPONSE_CONFIRMED", "NEEDS_RECONCILIATION"},
    "RESPONSE_CONFIRMED": {"RESPONSE_QUEUED", "CLOSED"},
    "DELIVERY_FAILED": {"RESPONSE_QUEUED", "DEAD_LETTERED"},
    "NEEDS_RECONCILIATION": {"DEAD_LETTERED"},
    "AUTH_REJECTED": set(),
    "CLOSED": set(),
    "CANCELLED": set(),
    "DEAD_LETTERED": set(),
}
_TERMINAL = {"AUTH_REJECTED", "CLOSED", "CANCELLED", "DEAD_LETTERED"}
_CTX: contextvars.ContextVar["LoopContext | None"] = contextvars.ContextVar(
    "telegram_durable_loop_context", default=None
)


class InvalidTransition(RuntimeError):
    pass


@dataclass(frozen=True)
class LoopContext:
    event_id: str
    correlation_id: str
    task_id: str | None
    run_id: str
    state: str
    duplicate: bool = False
    resumed: bool = False


def enabled() -> bool:
    return str(os.environ.get(FLAG, "")).strip().lower() in {"1", "true", "yes", "on"}


def killed() -> bool:
    return str(os.environ.get(KILL_SWITCH, "")).strip().lower() in {"1", "true", "yes", "on"}


def _root() -> Path:
    configured = str(os.environ.get("OCTOPUS_STATE_DIR", "")).strip()
    base = Path(configured) if configured else Path(__file__).resolve().parents[1] / "state"
    return base / "telegram" / "loop"


def _event_path(event_id: str) -> Path:
    return _root() / "events" / event_id.replace(":", "_")


def _outbox_path(message_key: str) -> Path:
    return _root() / "outbox" / f"{message_key}.json"


def _metrics_path() -> Path:
    return _root() / "metrics.json"


def _now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def _hash(value: object) -> str:
    blob = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(blob.encode("utf-8", "replace")).hexdigest()


def _read(path: Path) -> dict:
    try:
        value = json.loads(path.read_text("utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def _atomic(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True), "utf-8")
    os.replace(tmp, path)


def _metric(name: str, amount: int = 1) -> None:
    path = _metrics_path()
    current = _read(path)
    current[name] = int(current.get(name) or 0) + int(amount)
    current["updated_at"] = _now()
    _atomic(path, current)


def metrics() -> dict:
    return _read(_metrics_path())


def _transition_row(old: str | None, new: str, *, outcome: str = "ok", error_code=None) -> dict:
    return {
        "transition": f"{old or 'NONE'}->{new}",
        "process": "telegram-center",
        "outcome": outcome,
        "error_code": error_code,
        "timestamp": _now(),
    }


def _context(row: dict, *, duplicate: bool = False, resumed: bool = False) -> LoopContext:
    return LoopContext(
        event_id=str(row.get("event_id") or ""),
        correlation_id=str(row.get("correlation_id") or ""),
        task_id=row.get("task_id"),
        run_id=str(row.get("run_id") or ""),
        state=str(row.get("state") or ""),
        duplicate=duplicate,
        resumed=resumed,
    )


def _normalize(update: dict) -> dict:
    uid = int(update.get("update_id"))
    msg = update.get("message") or update.get("edited_message") or {}
    cb = update.get("callback_query") or {}
    actor = msg.get("from") or cb.get("from") or {}
    chat = msg.get("chat") or (cb.get("message") or {}).get("chat") or {}
    payload_shape = {
        "update_id": uid,
        "message_id": msg.get("message_id") or (cb.get("message") or {}).get("message_id"),
        "date": msg.get("date") or (cb.get("message") or {}).get("date"),
        "actor_id": actor.get("id"),
        "chat_id": chat.get("id"),
        "callback_id": cb.get("id"),
        "text_hash": _hash(msg.get("text") or msg.get("caption") or cb.get("data") or ""),
    }
    event_id = f"tg:{uid}"
    seed = _hash({"event_id": event_id, "payload": payload_shape})
    return {
        "schema_version": 2,
        "schema": SCHEMA,
        "source": "telegram",
        "event_id": event_id,
        "update_id": uid,
        "correlation_id": f"corr_{seed[:24]}",
        "task_id": f"task_{seed[24:48]}",
        "run_id": f"run_{uuid.uuid4().hex}",
        "chat_id_hash": _hash(chat.get("id")) if chat.get("id") is not None else None,
        "actor_id_hash": _hash(actor.get("id")) if actor.get("id") is not None else None,
        "event_type": "callback" if cb else ("command" if str(msg.get("text") or "").startswith("/") else "message"),
        "idempotency_key": f"telegram:{uid}",
        "payload_hash": _hash(payload_shape),
        "received_at": _now(),
        "state": "RECEIVED",
        "transitions": [_transition_row(None, "RECEIVED")],
        "reply_receipt_id": None,
        "readback_verified": False,
        "error_code": None,
    }


def begin_update(update: dict, *, authorized: bool) -> LoopContext:
    normalized = _normalize(update)
    path = _event_path(normalized["event_id"])
    path = path.with_suffix(".json")
    existing = _read(path)
    if existing:
        state = str(existing.get("state") or "")
        if state == "INTENT_COMMITTED":
            _metric("telegram_intents_resumed_total")
            return _context(existing, resumed=True)
        if state == "DISPATCHED":
            existing = transition(
                normalized["event_id"], "NEEDS_RECONCILIATION",
                outcome="blocked", error_code="RESTART_AFTER_DISPATCH",
            )
        _metric("telegram_duplicates_suppressed_total")
        return _context(existing, duplicate=True)

    _metric("telegram_updates_received_total")
    if not authorized:
        normalized["task_id"] = None
        normalized["state"] = "AUTH_REJECTED"
        normalized["transitions"].append(_transition_row("RECEIVED", "AUTH_REJECTED", outcome="blocked"))
        normalized["closed_at"] = _now()
        _atomic(path, normalized)
        _metric("telegram_updates_rejected_total")
        return _context(normalized)

    normalized["state"] = "AUTHENTICATED"
    normalized["transitions"].append(_transition_row("RECEIVED", "AUTHENTICATED"))
    normalized["state"] = "INTENT_COMMITTED"
    normalized["intent_written_at"] = _now()
    normalized["transitions"].append(_transition_row("AUTHENTICATED", "INTENT_COMMITTED"))
    _atomic(path, normalized)
    _metric("telegram_updates_authorized_total")
    return _context(normalized)


def start_dispatch(event_id: str) -> dict:
    row = readback_event(event_id)
    if str(row.get("state") or "") == "INTENT_COMMITTED":
        return transition(event_id, "DISPATCHED", fields={"processing_started_at": _now()})
    return row


def readback_event(event_id: str) -> dict:
    return _read(_event_path(event_id).with_suffix(".json"))


def transition(event_id: str, new_state: str, *, outcome: str = "ok", error_code=None, fields=None) -> dict:
    path = _event_path(event_id).with_suffix(".json")
    row = _read(path)
    if not row:
        raise InvalidTransition(f"unknown event: {event_id}")
    old = str(row.get("state") or "")
    if new_state not in _ALLOWED.get(old, set()):
        raise InvalidTransition(f"{old}->{new_state}")
    row["state"] = new_state
    row.setdefault("transitions", []).append(
        _transition_row(old, new_state, outcome=outcome, error_code=error_code)
    )
    if fields:
        row.update(dict(fields))
    if new_state in _TERMINAL:
        row["closed_at"] = _now()
    _atomic(path, row)
    return row


def bind_context(context: LoopContext | None):
    return _CTX.set(context)


def clear_context() -> None:
    _CTX.set(None)


def current_context() -> LoopContext | None:
    return _CTX.get()


@contextlib.contextmanager
def bound(context: LoopContext | None):
    token = _CTX.set(context)
    try:
        yield context
    finally:
        _CTX.reset(token)


def _message_key(context: LoopContext, *, text: str, chat_id, topic_id, stream: str) -> str:
    return _hash({
        "task_id": context.task_id,
        "event_id": context.event_id,
        "chat": _hash(chat_id),
        "topic": topic_id,
        "stream": stream,
        "text": _hash(text),
    })[:40]


def deliver(*, text: str, chat_id, topic_id, stream: str, send_fn: Callable[[], dict | None]) -> dict:
    context = current_context()
    if not enabled() or context is None or context.duplicate and not context.task_id:
        return {"managed": False, "ok": False, "state": "UNMANAGED", "message_id": None}
    if killed():
        _metric("telegram_dispatch_blocked_total")
        return {"managed": True, "ok": False, "state": "BLOCKED", "message_id": None}
    if context.state == "AUTH_REJECTED" or not context.task_id:
        return {"managed": True, "ok": False, "state": "AUTH_REJECTED", "message_id": None}

    key = _message_key(context, text=text, chat_id=chat_id, topic_id=topic_id, stream=stream)
    path = _outbox_path(key)
    existing = _read(path)
    if existing:
        state = str(existing.get("state") or "")
        if state == "CONFIRMED":
            return {"managed": True, "ok": True, "state": state,
                    "message_id": existing.get("message_id"), "message_key": key, "replayed": True}
        if state in {"SENDING", "NEEDS_RECONCILIATION"}:
            if state == "SENDING":
                existing["state"] = "NEEDS_RECONCILIATION"
                existing["error_code"] = "RESTART_AFTER_SEND_ATTEMPT"
                existing["updated_at"] = _now()
                _atomic(path, existing)
            return {"managed": True, "ok": False, "state": "NEEDS_RECONCILIATION",
                    "message_id": None, "message_key": key}

    event = readback_event(context.event_id)
    state = str(event.get("state") or "")
    if state in {"INTENT_COMMITTED", "DISPATCHED"}:
        transition(context.event_id, "RESULT_COMMITTED", fields={"result_hash": _hash(text)})
        state = "RESULT_COMMITTED"
    if state == "RESULT_COMMITTED":
        queued = {
            "schema": "telegram-outbox/1",
            "message_key": key,
            "event_id": context.event_id,
            "correlation_id": context.correlation_id,
            "task_id": context.task_id,
            "run_id": context.run_id,
            "chat_id_hash": _hash(chat_id),
            "topic_id": topic_id,
            "stream": str(stream or "center"),
            "payload_hash": _hash(text),
            "state": "QUEUED",
            "attempts": 0,
            "created_at": _now(),
        }
        _atomic(path, queued)
        event = transition(context.event_id, "RESPONSE_QUEUED")
        receipt_ids = list(event.get("reply_receipt_ids") or [])
        if key not in receipt_ids:
            receipt_ids.append(key)
        event["reply_receipt_id"] = key
        event["reply_receipt_ids"] = receipt_ids
        _atomic(_event_path(context.event_id).with_suffix(".json"), event)
    elif state == "RESPONSE_CONFIRMED":
        queued = {
            "schema": "telegram-outbox/1",
            "message_key": key,
            "event_id": context.event_id,
            "correlation_id": context.correlation_id,
            "task_id": context.task_id,
            "run_id": context.run_id,
            "chat_id_hash": _hash(chat_id),
            "topic_id": topic_id,
            "stream": str(stream or "center"),
            "payload_hash": _hash(text),
            "state": "QUEUED",
            "attempts": 0,
            "created_at": _now(),
        }
        _atomic(path, queued)
        event = transition(context.event_id, "RESPONSE_QUEUED")
        receipt_ids = list(event.get("reply_receipt_ids") or [])
        if key not in receipt_ids:
            receipt_ids.append(key)
        event["reply_receipt_id"] = key
        event["reply_receipt_ids"] = receipt_ids
        event["readback_verified"] = False
        _atomic(_event_path(context.event_id).with_suffix(".json"), event)
    elif state not in {"RESPONSE_QUEUED", "RESPONSE_SENT", "CLOSED"}:
        return {"managed": True, "ok": False, "state": state, "message_id": None, "message_key": key}

    queued = _read(path)
    if not queued:
        return {"managed": True, "ok": False, "state": "OUTBOX_MISSING", "message_id": None}
    queued["state"] = "SENDING"
    queued["attempts"] = int(queued.get("attempts") or 0) + 1
    queued["attempted_at"] = _now()
    _atomic(path, queued)
    try:
        response = send_fn()
    except Exception as exc:
        queued["state"] = "NEEDS_RECONCILIATION"
        queued["error_code"] = type(exc).__name__
        queued["updated_at"] = _now()
        _atomic(path, queued)
        transition(context.event_id, "NEEDS_RECONCILIATION", outcome="error",
                   error_code="UNCERTAIN_SEND_OUTCOME")
        _metric("telegram_delivery_failures_total")
        return {"managed": True, "ok": False, "state": queued["state"],
                "message_id": None, "message_key": key}

    message_id = None
    if isinstance(response, dict) and response.get("ok"):
        result = response.get("result") or {}
        try:
            message_id = int(result.get("message_id"))
        except (TypeError, ValueError, AttributeError):
            message_id = None
    if message_id is None:
        queued["state"] = "NEEDS_RECONCILIATION"
        queued["error_code"] = "UNCERTAIN_SEND_OUTCOME"
        queued["updated_at"] = _now()
        _atomic(path, queued)
        transition(context.event_id, "NEEDS_RECONCILIATION", outcome="error",
                   error_code="UNCERTAIN_SEND_OUTCOME")
        _metric("telegram_delivery_failures_total")
        return {"managed": True, "ok": False, "state": queued["state"],
                "message_id": None, "message_key": key}

    transition(context.event_id, "RESPONSE_SENT")
    queued["state"] = "CONFIRMED"
    queued["message_id"] = message_id
    queued["confirmed_at"] = _now()
    _atomic(path, queued)
    transition(context.event_id, "RESPONSE_CONFIRMED", fields={"delivery_message_id": message_id})
    readback = _read(path)
    event = readback_event(context.event_id)
    verified = readback.get("state") == "CONFIRMED" and event.get("state") == "RESPONSE_CONFIRMED"
    event["readback_verified"] = bool(verified)
    event["readback_at"] = _now()
    _atomic(_event_path(context.event_id).with_suffix(".json"), event)
    _metric("telegram_responses_confirmed_total")
    return {"managed": True, "ok": bool(verified), "state": "CONFIRMED",
            "message_id": message_id, "message_key": key}


def commit_result(result: object) -> dict:
    context = current_context()
    if context is None:
        return {"state": "UNMANAGED"}
    row = readback_event(context.event_id)
    state = str(row.get("state") or "")
    if state in {"INTENT_COMMITTED", "DISPATCHED"}:
        row = transition(context.event_id, "RESULT_COMMITTED", fields={"result_hash": _hash(result)})
        state = str(row.get("state"))
    elif state in {"RESULT_COMMITTED", "RESPONSE_QUEUED", "RESPONSE_SENT", "RESPONSE_CONFIRMED"}:
        row["handler_result_hash"] = _hash(result)
        _atomic(_event_path(context.event_id).with_suffix(".json"), row)
    if state == "RESPONSE_CONFIRMED" and bool(row.get("readback_verified")):
        row = transition(context.event_id, "CLOSED")
    return row
