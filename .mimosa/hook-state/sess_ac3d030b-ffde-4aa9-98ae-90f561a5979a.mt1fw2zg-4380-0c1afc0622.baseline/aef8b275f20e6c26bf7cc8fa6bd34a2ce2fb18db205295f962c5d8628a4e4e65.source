#!/usr/bin/env python3
"""Pure contracts for the non-owning unified control link."""
from __future__ import annotations

import hashlib
import json
import re

SCHEMA = "unified-control.v1"
SNAPSHOT_SCHEMA = "unified-control.snapshot.v1"
COMPASS_SCHEMA = "unified-control.compass.v1"
LINK_SCHEMA = "unified-control.link.v1"
ACTION_REQUEST_SCHEMA = "action-request.v1"

AUTHORITY = ("AUTHORITATIVE", "ADVISORY_SHADOW", "STALE", "MISSING", "BLOCKED")
STAGES = ("direction", "goal", "prereg", "mission", "action", "receipt", "verdict", "memory")


def canonical(v) -> str:
    return json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def sha(v, n: int = 32) -> str:
    return hashlib.sha256(canonical(v).encode("utf-8")).hexdigest()[:n]


def stable_id(prefix: str, *parts) -> str:
    p = re.sub(r"[^a-z0-9_-]", "-", str(prefix).lower()).strip("-") or "id"
    return f"{p}:{sha(list(parts), 20)}"


def authority(value: str) -> str:
    return value if value in AUTHORITY else "BLOCKED"


def new_link(*, trace_id: str, stage: str, ref: str, status: str,
             authority_level: str, evidence=None, reason: str = "") -> dict:
    if stage not in STAGES:
        stage, status, reason = "action", "BLOCKED", f"unknown-stage|{reason}"
    return {
        "schema": LINK_SCHEMA,
        "trace_id": str(trace_id),
        "stage": stage,
        "ref": str(ref),
        "status": str(status),
        "authority": authority(authority_level),
        "evidence": list(evidence or []),
        "reason": str(reason),
    }


def validate_action_request(req) -> dict:
    errors = []
    if not isinstance(req, dict):
        return {"ok": False, "errors": ["not-a-dict"]}
    required = ("schema", "action_id", "prereg_id", "source_component", "intent",
                "action_type", "target", "expected_effect", "allowed_scope",
                "external_effect", "estimated_cost", "rollback", "falsifier")
    for k in required:
        if k not in req:
            errors.append(f"missing:{k}")
    if req.get("schema") != ACTION_REQUEST_SCHEMA:
        errors.append("bad-schema")
    if not re.fullmatch(r"[A-Za-z0-9._:-]{4,80}", str(req.get("action_id") or "")):
        errors.append("bad-action-id")
    if not isinstance(req.get("external_effect"), bool):
        errors.append("bad-external-effect")
    if isinstance(req.get("estimated_cost"), bool) or not isinstance(
            req.get("estimated_cost"), (int, float)):
        errors.append("bad-cost")
    if not isinstance(req.get("allowed_scope"), list) or not req.get("allowed_scope"):
        errors.append("bad-scope")
    return {"ok": not errors, "errors": errors}
