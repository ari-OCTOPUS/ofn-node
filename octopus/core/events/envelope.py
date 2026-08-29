"""OCTOPUS core.events — shared typed envelope (I1, additive-only).

One canonical implementation for the fields every OCTOPUS subsystem already
agrees on: run/event/message identity, UTC timestamp, boot identity, evidence
references, content hash, chain hash, and the standing rule may_authorize=False.

This package is NEW code under /opt/octopus/core/. Nothing in the runtime
imports it yet (adapters arrive in I3). Zero behavior change by construction.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re

HEX64 = re.compile(r"^sha256:[0-9a-f]{64}$")
RUN_ID = re.compile(r"^run-[0-9]{8}T[0-9]{4,6}Z-[0-9a-f]{8}$")


def canonical(obj) -> str:
    """Canonical JSON: sorted keys, tight separators, unicode preserved."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def content_hash(obj) -> str:
    return "sha256:" + hashlib.sha256(canonical(obj).encode("utf-8")).hexdigest()


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def new_run_id() -> str:
    ts = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"run-{ts}-{os.urandom(4).hex()}"


def boot_id() -> str:
    try:
        return open("/proc/sys/kernel/random/boot_id").read().strip()
    except OSError:
        return "unknown"


REQUIRED_FIELDS = (
    "run_id", "ts_utc", "boot_id", "evidence_refs",
    "payload", "payload_hash", "prev_hash", "may_authorize",
)


def build_event(run_id: str, payload: dict, evidence_refs: list[str],
                prev_hash: str | None) -> dict:
    """Build a typed event envelope with the shared invariants baked in."""
    event = {
        "run_id": run_id,
        "ts_utc": utc_now(),
        "boot_id": boot_id(),
        "evidence_refs": list(evidence_refs),
        "payload": payload,
        "payload_hash": content_hash(payload),
        "prev_hash": prev_hash,
        "may_authorize": False,
    }
    errors = validate_event(event)
    if errors:
        raise ValueError(f"internal: built invalid event: {errors}")
    return event


def event_hash(event: dict) -> str:
    """Chain hash of an event (over its canonical form)."""
    return content_hash(event)


def validate_event(event) -> list[str]:
    """Deterministic field checks. Empty list = valid."""
    if not isinstance(event, dict):
        return ["E01 not an object"]
    errors = []
    for f in REQUIRED_FIELDS:
        if f not in event:
            errors.append(f"E02 missing field {f}")
    if errors:
        return errors
    if not RUN_ID.match(str(event.get("run_id", ""))):
        errors.append("E03 run_id malformed")
    if not isinstance(event.get("ts_utc"), str) or not event["ts_utc"].endswith("Z"):
        errors.append("E04 ts_utc must be UTC ISO-8601 ending in Z")
    if not str(event.get("boot_id") or ""):
        errors.append("E05 boot_id missing")
    if not isinstance(event.get("evidence_refs"), list):
        errors.append("E06 evidence_refs must be a list")
    if not isinstance(event.get("payload"), dict):
        errors.append("E07 payload must be an object")
    elif event.get("payload_hash") != content_hash(event["payload"]):
        errors.append("E08 payload_hash mismatch")
    ph = event.get("prev_hash")
    if ph is not None and (not isinstance(ph, str) or not HEX64.match(ph)):
        errors.append("E09 prev_hash not sha256-string or null")
    if event.get("may_authorize") is not False:
        errors.append("E10 may_authorize must be false")
    return errors


def verify_chain(events: list[dict]) -> tuple[bool, str]:
    """Verify seq of events: each prev_hash must equal hash of the previous."""
    prev = None
    for i, ev in enumerate(events):
        errors = validate_event(ev)
        if errors:
            return False, f"event {i}: {errors[0]}"
        if ev["prev_hash"] != prev:
            return False, f"event {i}: prev_hash does not chain"
        prev = event_hash(ev)
    return True, f"chain of {len(events)} events intact"
