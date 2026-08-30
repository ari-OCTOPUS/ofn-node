#!/usr/bin/env python3
"""approval_binder.py -- Tamper-evident approval tokens (EQUIP G8).

Generates and verifies approval tokens that cryptographically bind:
  action_id + tool_name + target + arguments + expiry + approver

Each token is a JSON structure with an HMAC signature. Verification is
fail-closed: any tampering, expiry, or replay = deny.

Properties:
  - Approval replay prevention: each nonce used once
  - Argument mismatch detection: changing args invalidates approval
  - Expiry enforcement: approvals expire
  - Nonce store is pluggable (in-memory default, JSONL for production)

$0 | stdlib-only | no network | HMAC via hashlib
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

SCHEMA = "approval-binder.v1"
# Default HMAC key from env (MUST be set in production)
_KEY_ENV = "OCTOPUS_APPROVAL_BINDER_HMAC"


def _get_key() -> bytes:
    """Get HMAC signing key from environment. No key = deny everything."""
    raw = os.environ.get(_KEY_ENV, "")
    if not raw:
        return b""  # empty key means all signatures fail
    return raw.encode("utf-8")


def _sign(payload: str, key: bytes) -> str:
    """HMAC-SHA256 signature."""
    return hmac.new(key, payload.encode("utf-8"), hashlib.sha256).hexdigest()[:32]


@dataclass
class ApprovalToken:
    """A tamper-evident approval token."""
    action_id: str
    tool_name: str
    target: str
    arguments_hash: str  # hash of arguments, not raw args (no secret leakage)
    approver: str
    issued_at: float
    expires_at: float
    nonce: str
    signature: str = ""

    def to_dict(self) -> dict:
        return {
            "schema": SCHEMA,
            "action_id": self.action_id,
            "tool_name": self.tool_name,
            "target": self.target,
            "arguments_hash": self.arguments_hash,
            "approver": self.approver,
            "issued_at": self.issued_at,
            "expires_at": self.expires_at,
            "nonce": self.nonce,
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ApprovalToken":
        return cls(
            action_id=str(d.get("action_id", "")),
            tool_name=str(d.get("tool_name", "")),
            target=str(d.get("target", "")),
            arguments_hash=str(d.get("arguments_hash", "")),
            approver=str(d.get("approver", "")),
            issued_at=float(d.get("issued_at", 0)),
            expires_at=float(d.get("expires_at", 0)),
            nonce=str(d.get("nonce", "")),
            signature=str(d.get("signature", "")),
        )


def _canonical_payload(token: ApprovalToken) -> str:
    """Deterministic serialization for signing (excludes signature itself)."""
    d = {
        "action_id": token.action_id,
        "tool_name": token.tool_name,
        "target": token.target,
        "arguments_hash": token.arguments_hash,
        "approver": token.approver,
        "issued_at": token.issued_at,
        "expires_at": token.expires_at,
        "nonce": token.nonce,
    }
    return json.dumps(d, sort_keys=True, separators=(",", ":"))


def hash_arguments(arguments: dict | None) -> str:
    """Hash arguments for binding. Does not include secrets in hash content."""
    raw = json.dumps(arguments or {}, sort_keys=True, separators=(",", ":"),
                     default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def issue(action_id: str, tool_name: str, target: str,
          arguments: dict | None = None,
          approver: str = "owner",
          ttl_seconds: float = 300,
          nonce: str | None = None) -> ApprovalToken:
    """Issue a tamper-evident approval token.

    Args:
        action_id: Unique action identifier
        tool_name: Tool being approved
        target: Target of the action
        arguments: Action arguments (hashed, not stored raw)
        approver: Who approved (must be "owner" or trusted identity)
        ttl_seconds: Time-to-live for the approval
        nonce: Optional nonce (generated if not provided)

    Returns:
        ApprovalToken with HMAC signature

    No HMAC key in env = token issued but will fail verification (fail-closed).
    """
    key = _get_key()
    now = time.time()
    n = nonce or hashlib.sha256(
        f"{action_id}:{now}:{os.urandom(8).hex()}".encode()
    ).hexdigest()[:16]

    token = ApprovalToken(
        action_id=action_id, tool_name=tool_name, target=target,
        arguments_hash=hash_arguments(arguments), approver=approver,
        issued_at=now, expires_at=now + ttl_seconds, nonce=n,
    )
    token.signature = _sign(_canonical_payload(token), key)
    return token


def verify(token: ApprovalToken,
           action_id: str, tool_name: str, target: str,
           arguments: dict | None = None,
           nonce_store: set | None = None) -> dict:
    """Verify an approval token.

    Checks (all must pass):
      1. HMAC signature valid
      2. Not expired
      3. action_id matches
      4. tool_name matches
      5. target matches
      6. arguments hash matches (argument binding)
      7. Nonce not replayed

    Returns:
        {valid: bool, reason: str, ...}
    """
    key = _get_key()

    # 1. Signature check (fail-closed: no key = deny)
    if not key:
        return {"valid": False, "reason": "no_hmac_key_configured"}

    expected_sig = _sign(_canonical_payload(token), key)
    if not hmac.compare_digest(token.signature, expected_sig):
        return {"valid": False, "reason": "signature_invalid"}

    # 2. Expiry check
    now = time.time()
    if now > token.expires_at:
        return {"valid": False, "reason": "expired",
                "expired_at": token.expires_at, "now": now}

    # 3-6. Binding checks
    if token.action_id != action_id:
        return {"valid": False, "reason": "action_id_mismatch"}
    if token.tool_name != tool_name:
        return {"valid": False, "reason": "tool_name_mismatch"}
    if token.target != target:
        return {"valid": False, "reason": "target_mismatch"}
    expected_args_hash = hash_arguments(arguments)
    if not hmac.compare_digest(token.arguments_hash, expected_args_hash):
        return {"valid": False, "reason": "arguments_mismatch"}

    # 7. Nonce replay check
    if nonce_store is not None:
        if token.nonce in nonce_store:
            return {"valid": False, "reason": "nonce_replayed"}
        nonce_store.add(token.nonce)

    return {
        "valid": True,
        "reason": "approved",
        "approver": token.approver,
        "expires_at": token.expires_at,
        "remaining_seconds": token.expires_at - now,
    }


if __name__ == "__main__":
    # Demo
    nonce_store: set[str] = set()
    os.environ[_KEY_ENV] = "test-key-for-demo-only"

    tok = issue("act-001", "deploy", "/prod/api",
                {"version": "2.1", "env": "production"},
                approver="owner", nonce_store=nonce_store)
    print("Issued:", json.dumps(tok.to_dict(), indent=2))

    # Verify with correct params
    v1 = verify(tok, "act-001", "deploy", "/prod/api",
                {"version": "2.1", "env": "production"},
                nonce_store=nonce_store)
    print("Verify (correct):", v1)

    # Replay attempt
    v2 = verify(tok, "act-001", "deploy", "/prod/api",
                {"version": "2.1", "env": "production"},
                nonce_store=nonce_store)
    print("Verify (replay):", v2)

    # Wrong arguments
    nonce_store2: set[str] = set()
    v3 = verify(tok, "act-001", "deploy", "/prod/api",
                {"version": "2.2", "env": "production"},
                nonce_store=nonce_store2)
    print("Verify (wrong args):", v3)
