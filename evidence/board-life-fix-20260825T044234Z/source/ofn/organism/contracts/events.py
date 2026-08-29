
import hashlib, json, time
from typing import Any

SCHEMA_VERSION = 1
EVENT_QUEUE_MAXSIZE = 512

def canonical(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

def event_hash(payload: dict) -> str:
    return hashlib.sha256(canonical(payload)).hexdigest()

def validate_event(ev: dict) -> dict:
    if not isinstance(ev, dict):
        raise ValueError("invalid_quality:not_object")
    if ev.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"unknown_schema_version:{ev.get('schema_version')}")
    required = ("event_id", "event_type", "priority", "payload", "created_at")
    missing = [k for k in required if k not in ev]
    if missing:
        raise ValueError("invalid_quality:missing:" + ",".join(missing))
    pr = ev["priority"]
    if not isinstance(pr, int) or pr < 0 or pr > 99:
        raise ValueError("invalid_quality:priority")
    if not isinstance(ev["event_id"], str) or not ev["event_id"]:
        raise ValueError("invalid_quality:event_id")
    body = {k: ev[k] for k in ("event_id","event_type","priority","payload","created_at","schema_version")}
    h = event_hash(body)
    if ev.get("hash") and ev["hash"] != h:
        raise ValueError("invalid_quality:hash_mismatch")
    ev = dict(ev)
    ev["hash"] = h
    return ev

def make_event(event_type: str, payload: dict, priority: int = 50, event_id: str | None = None) -> dict:
    ev = {
        "schema_version": SCHEMA_VERSION,
        "event_id": event_id or hashlib.sha256(f"{time.time_ns()}:{event_type}".encode()).hexdigest()[:32],
        "event_type": event_type,
        "priority": priority,
        "payload": payload,
        "created_at": time.time(),
    }
    ev["hash"] = event_hash({k: ev[k] for k in ("event_id","event_type","priority","payload","created_at","schema_version")})
    return ev
