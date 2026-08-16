#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""capability_token.py -- Short-lived, scoped capability tokens (EQUIP G7).

A capability token grants a specific agent permission to perform a specific
action on a specific resource for a limited duration, bound to a task.

Design principles:
  - Least privilege: token grants exactly one action on one resource
  - Task-bound: token is associated with a task_id
  - Time-bounded: token has expiry (default 5 min, max 1 hour)
  - Replay-resistant: each token has a unique nonce
  - Confused-deputy resistant: token binds agent_id to on_behalf_of
  - HMAC-signed: tamper-evident (same pattern as owner_gate.py)
  - Idempotent: same token can be verified multiple times (until consumed)

Token structure:
  {
    "schema": "capability-token.v1",
    "token_id": "<uuid>",
    "agent_id": "<who>",
    "on_behalf_of": "<principal, optional>",
    "task_id": "<bound task>",
    "action": "<tool/action name>",
    "resource": "<resource pattern or path>",
    "scope": "read" | "write" | "propose",
    "expires_at": <unix timestamp>,
    "issued_at": <unix timestamp>,
    "nonce": "<random hex>",
    "sig": "<HMAC-SHA256 hex>"
  }

$0 | stdlib-only | no network | no external writes.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import re
import time
import uuid

SCHEMA = "capability-token.v1"

KEY_ENV = "OCTOPUS_CAPABILITY_TOKEN_HMAC"
_HEX32 = re.compile(r"[0-9a-f]{32}")

DEFAULT_TTL_S = 300.0       # 5 minutes
MAX_TTL_S = 3600.0          # 1 hour maximum

VALID_SCOPES = ("read", "write", "propose")


def _key() -> bytes | None:
    """Get HMAC key from environment. None if missing or too short."""
    k = str(os.environ.get(KEY_ENV, "") or "").strip()
    return k.encode("utf-8") if len(k) >= 16 else None


def _sign(fields: dict[str, str]) -> str | None:
    """HMAC-SHA256 sign sorted field values. Returns None if no key."""
    k = _key()
    if k is None:
        return None
    blob = "|".join(f"{n}={fields.get(n)}" for n in sorted(fields))
    return hmac.new(k, blob.encode("utf-8"), hashlib.sha256).hexdigest()[:32]


def issue(
    agent_id: str,
    action: str,
    resource: str,
    scope: str = "read",
    task_id: str = "",
    on_behalf_of: str | None = None,
    ttl_s: float = DEFAULT_TTL_S,
    now: float | None = None,
) -> dict:
    """Issue a capability token.

    Returns a token dict or {"ok": False, "reason": "..."}.

    Args:
        agent_id: Who receives the token
        action: What action is permitted (e.g., "read_file_slice")
        resource: What resource pattern is permitted (e.g., "path:/notes/**")
        scope: read, write, or propose
        task_id: Task this token is bound to
        on_behalf_of: Principal the agent acts on behalf of
        ttl_s: Time-to-live in seconds (clamped to MAX_TTL_S)
        now: Current time (for testing)
    """
    if not agent_id or not isinstance(agent_id, str):
        return {"ok": False, "reason": "agent_id required"}
    if not action or not isinstance(action, str):
        return {"ok": False, "reason": "action required"}
    if not resource or not isinstance(resource, str):
        return {"ok": False, "reason": "resource required"}
    if scope not in VALID_SCOPES:
        return {"ok": False, "reason": f"scope must be one of {VALID_SCOPES}"}

    # Clamp TTL
    ttl_s = max(1.0, min(float(ttl_s), MAX_TTL_S))

    _now = now if now is not None else time.time()
    expires_at = _now + ttl_s
    token_id = uuid.uuid4().hex[:16]
    nonce = uuid.uuid4().hex[:16]

    # Build fields for signing
    fields = {
        "agent_id": agent_id,
        "on_behalf_of": str(on_behalf_of or ""),
        "task_id": str(task_id or ""),
        "action": action,
        "resource": resource,
        "scope": scope,
        "expires_at": f"{expires_at:.6f}",
        "nonce": nonce,
    }
    sig = _sign(fields)
    if sig is None:
        return {"ok": False, "reason": "no-signing-key"}

    return {"ok": True, "token": {
        "schema": SCHEMA,
        "token_id": token_id,
        "agent_id": agent_id,
        "on_behalf_of": on_behalf_of,
        "task_id": task_id,
        "action": action,
        "resource": resource,
        "scope": scope,
        "expires_at": expires_at,
        "issued_at": _now,
        "nonce": nonce,
        "sig": sig,
    }}


def verify(
    token: dict,
    *,
    agent_id: str | None = None,
    action: str | None = None,
    resource: str | None = None,
    task_id: str | None = None,
    now: float | None = None,
    used_nonces: set[str] | None = None,
) -> dict:
    """Verify a capability token.

    Returns {"ok": True/False, "reason": "..."}.

    Verification order (cheapest first):
      1. Structure check (schema, required fields)
      2. Signature format check
      3. Agent binding (if agent_id provided, must match)
      4. Action binding (if action provided, must match)
      5. Resource matching (if resource provided, must be contained in token resource)
      6. Task binding (if task_id provided, must match)
      7. Expiry check
      8. Replay check (nonce in used_nonces)
      9. HMAC signature verification

    Args:
        token: The token dict to verify
        agent_id: Verify token is for this specific agent (confused-deputy defense)
        action: Verify token grants this specific action
        resource: Verify resource is within token's resource scope
        task_id: Verify token is bound to this task
        now: Current time (for testing)
        used_nonces: Set of already-consumed nonces (for replay prevention)
    """
    if not isinstance(token, dict):
        return {"ok": False, "reason": "token must be dict"}
    if token.get("schema") != SCHEMA:
        return {"ok": False, "reason": "bad-schema"}

    # Required fields
    for fld in ("agent_id", "action", "resource", "scope",
                "expires_at", "nonce", "sig"):
        if not token.get(fld):
            return {"ok": False, "reason": f"missing-{fld}"}

    if token.get("scope") not in VALID_SCOPES:
        return {"ok": False, "reason": f"invalid-scope:{token.get('scope')}"}

    # Signature format check
    sig = token.get("sig")
    if not isinstance(sig, str) or not _HEX32.fullmatch(sig):
        return {"ok": False, "reason": "bad-signature-format"}

    # Agent binding (confused-deputy defense)
    if agent_id is not None:
        if str(token.get("agent_id")) != str(agent_id):
            return {"ok": False, "reason": "agent-mismatch"}

    # Action binding
    if action is not None:
        if str(token.get("action")) != str(action):
            return {"ok": False, "reason": "action-mismatch"}

    # Resource matching: token resource is a pattern, requested resource must match
    if resource is not None:
        token_resource = str(token.get("resource", ""))
        if not _resource_match(resource, token_resource):
            return {"ok": False, "reason": "resource-mismatch"}

    # Task binding
    if task_id is not None:
        if str(token.get("task_id") or "") != str(task_id):
            return {"ok": False, "reason": "task-mismatch"}

    # Expiry
    try:
        exp = float(token.get("expires_at"))
    except (TypeError, ValueError):
        return {"ok": False, "reason": "bad-expiry"}
    _now = now if now is not None else time.time()
    if _now > exp:
        return {"ok": False, "reason": "expired"}

    # Replay check (optional -- caller manages nonce store)
    if used_nonces is not None:
        nonce = str(token.get("nonce") or "")
        if nonce in used_nonces:
            return {"ok": False, "reason": "replayed"}

    # HMAC verification
    fields = {
        "agent_id": str(token["agent_id"]),
        "on_behalf_of": str(token.get("on_behalf_of") or ""),
        "task_id": str(token.get("task_id") or ""),
        "action": str(token["action"]),
        "resource": str(token["resource"]),
        "scope": str(token["scope"]),
        "expires_at": f"{exp:.6f}",
        "nonce": str(token["nonce"]),
    }
    expected = _sign(fields)
    if expected is None:
        return {"ok": False, "reason": "no-signing-key"}
    if not hmac.compare_digest(sig, expected):
        return {"ok": False, "reason": "bad-signature"}

    return {"ok": True, "reason": "valid"}


def consume_nonce(token: dict, used_nonces: set[str]) -> None:
    """Mark a token's nonce as consumed. Caller must persist this set."""
    nonce = str((token or {}).get("nonce") or "")
    if nonce:
        used_nonces.add(nonce)


def _resource_match(requested: str, granted_pattern: str) -> bool:
    """Check if requested resource matches the granted pattern.

    Patterns:
      - "path:/notes/**" matches any path starting with /notes/
      - "action:propose_action" matches exact action name
      - "tool:*" matches any tool
      - Exact string match as fallback

    This is a simple prefix/wildcard matcher, not a full glob engine.
    """
    req = str(requested).strip()
    pat = str(granted_pattern).strip()

    # Exact match
    if req == pat:
        return True

    # Wildcard
    if pat.endswith("/**"):
        prefix = pat[:-3]
        return req.startswith(prefix) or req.startswith(prefix.lstrip("path:"))
    if pat.endswith("/*"):
        prefix = pat[:-2]
        return req.startswith(prefix) or req.startswith(prefix.lstrip("path:"))
    if pat == "*":
        return True

    # Prefix match with prefix indicator
    if ":" in pat:
        kind, val = pat.split(":", 1)
        if kind == "path":
            return req.startswith(val) or req.startswith("/" + val.lstrip("/"))
        if kind == "tool":
            return val == "*" or req == val or req.endswith(":" + val)

    # Fallback: prefix
    return req.startswith(pat)
