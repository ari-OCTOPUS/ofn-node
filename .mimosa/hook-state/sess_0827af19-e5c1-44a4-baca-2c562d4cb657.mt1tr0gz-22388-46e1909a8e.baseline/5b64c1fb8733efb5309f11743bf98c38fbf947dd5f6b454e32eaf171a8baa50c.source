#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""arm_gate.py — P5 defense-in-depth: fresh arm-token + two-key gate for
dangerous (paid / self-modification) capabilities.

Problem (2026-07-24 live audit + CONTAINMENT-PLAN P5): the ~12 ACTIVATION-*.flag
levers sit on disk, so a bare restart re-arms paid/self-mod paths — an "ambient
capability". That is the exact anti-pattern behind the July-2026 sandbox escapes:
capability present as an ambient property of the environment rather than a scoped,
freshly-authorized, time-limited exception.

arm_gate ADDS a strictly-tightening precondition (it never relaxes anything): a
dangerous capability opens only if, IN ADDITION to its ACTIVATION flag, a FRESH
owner arm-token exists (TTL-bounded) — and for the highest-risk self-modification
capabilities, TWO independent tokens (two-key). Presence of the flag alone is no
longer sufficient; a recent, deliberate owner arm action is required.

Fail-closed everywhere: unknown capability, missing/stale/future/unreadable token,
wrong-capability token, or (when an owner secret is configured) a bad HMAC -> DENY.
Callers enforce ONLY via guard() when enforced() is true, so wiring is byte-identical
when the owner has not opted in (OCTOPUS_REQUIRE_ARM unset).

This module NEVER writes an arm-token, NEVER touches a kill-switch or an ACTIVATION
flag, and can only make a capability HARDER to open, never easier. Tokens are
owner-authored (like LIVE-ENABLED.flag / ACTIVATION-*.flag, capability_gate.py:27).
stdlib-only, fail-soft.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
from pathlib import Path

# capability -> (ACTIVATION flag basename in _ops/, two_key required?)
DANGEROUS = {
    "cortex_paid":       ("ACTIVATION-CORTEX-PAID.flag",     False),
    "governor_llm":      ("ACTIVATION-GOVERNOR-LLM.flag",    False),
    "code_autonomy":     ("ACTIVATION-CODE-AUTONOMY.flag",   True),
    "self_improve_auto": ("ACTIVATION-SELF-IMPROVE-AUTO.flag", True),
    "replicate":         ("ACTIVATION-REPLICATION.flag",     True),
}

DEFAULT_TTL_S = 24 * 3600  # a stale arm expires; presence-on-disk is never enough


def enforced() -> bool:
    """Owner opt-in. When false, guard() passes through -> today's behavior byte-identical."""
    return os.environ.get("OCTOPUS_REQUIRE_ARM", "").strip().lower() in ("1", "true", "yes", "on")


def _read_token(p: Path):
    try:
        return json.loads(p.read_text("utf-8"))
    except Exception:  # noqa: BLE001 — unreadable/corrupt token = fail-closed upstream
        return None


def _token_fresh(tok: dict, now: float, ttl_s: int) -> bool:
    try:
        ts = float(tok.get("armed_at", 0))
    except Exception:  # noqa: BLE001
        return False
    age = now - ts
    return 0 <= age <= ttl_s  # armed-now (age 0) ok; future timestamp (age<0) rejected


def _hmac_ok(tok: dict, cap: str, secret: "str | None") -> bool:
    # No owner secret configured -> presence+freshness only (documented weaker mode).
    if not secret:
        return True
    mac = tok.get("hmac")
    if not mac:
        return False
    body = f"{cap}|{tok.get('armed_at')}|{tok.get('key', '')}".encode("utf-8")
    want = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    try:
        return hmac.compare_digest(str(mac), want)
    except Exception:  # noqa: BLE001
        return False


def _one_key_ok(cap: str, key_path: Path, now: float, ttl_s: int, secret) -> bool:
    if not key_path.exists():
        return False
    tok = _read_token(key_path)
    if not isinstance(tok, dict):
        return False
    if tok.get("capability") != cap:
        return False
    if not _token_fresh(tok, now, ttl_s):
        return False
    return _hmac_ok(tok, cap, secret)


def arm_open(capability: str, *, arm_dir=None, ops_dir=None, now: "float | None" = None,
             ttl_s: int = DEFAULT_TTL_S, secret: "str | None" = None) -> "tuple[bool, str]":
    """Fail-closed. (True,'open') only if the ACTIVATION flag AND a fresh arm-token
    (two tokens for two-key caps) are present and valid. Never raises."""
    try:
        if capability not in DANGEROUS:
            return False, f"unknown-dangerous-capability:{capability}"
        flag_name, two_key = DANGEROUS[capability]
        if ops_dir is None or arm_dir is None:
            import opslib  # noqa: WPS433 — live paths; tests inject ops_dir/arm_dir
            ops_dir = ops_dir or opslib.OPS
            arm_dir = arm_dir or (opslib.STATE_DIR / "arm")
        ops_dir = Path(ops_dir)
        arm_dir = Path(arm_dir)
        if secret is None:
            secret = os.environ.get("OCTOPUS_ARM_SECRET") or None
        now = time.time() if now is None else now

        if not (ops_dir / flag_name).exists():
            return False, f"activation-flag-absent:{flag_name}"
        if not _one_key_ok(capability, arm_dir / f"{capability}.arm.json", now, ttl_s, secret):
            return False, "arm-token-1 missing/stale/invalid (fail-closed)"
        if two_key and not _one_key_ok(
                capability, arm_dir / f"{capability}.arm2.json", now, ttl_s, secret):
            return False, "arm-token-2 (two-key) missing/stale/invalid (fail-closed)"
        return True, "open"
    except Exception as e:  # noqa: BLE001 — the gate must never crash a caller; deny on error
        return False, f"failsafe-deny:{type(e).__name__}"


def sensitive_enforced() -> bool:
    """P0 fix (2026-08-04, blindspot #30): even without full OCTOPUS_REQUIRE_ARM,
    the most dangerous capabilities (code_autonomy, self_improve_auto, replicate)
    should require a fresh arm-token. This is a STRICTLY-TIGHTENING gate — it never
    relaxes anything. When this flag is OFF (default), behavior is byte-identical.

    Rationale: arm_gate_enforcing:false in ORGANISM-STATE means guard() passes
    through for ALL capabilities. But code_autonomy (self-patching code) and
    self_improve_auto (autonomous self-improvement) are D5/D6 actions that
    should not pass through even when the owner has not opted into full arm
    enforcement. This closes that gap behind a separate, default-off flag."""
    return os.environ.get("OCTOPUS_ARM_SENSITIVE_DEFAULT", "").strip().lower() in ("1", "true", "yes", "on")


# Capabilities that require arm even without full OCTOPUS_REQUIRE_ARM
# (when OCTOPUS_ARM_SENSITIVE_DEFAULT=1). These are the highest-risk D5/D6 caps.
_ALWAYS_SENSITIVE = frozenset({"code_autonomy", "self_improve_auto", "replicate"})


def guard(capability: str, **kw) -> "tuple[bool, str]":
    """Caller helper. When enforced() -> require arm_open; else pass-through (byte-identical).

    P0 fix (2026-08-04): even when enforced() is False, if
    OCTOPUS_ARM_SENSITIVE_DEFAULT=1 and capability is in _ALWAYS_SENSITIVE,
    arm_open is still required. This prevents code_autonomy/self_improve from
    being ambient capabilities even when full arm enforcement is off.

    Wire as:  ok, why = arm_gate.guard('code_autonomy');  if not ok: <deny/skip>."""
    if not enforced():
        # Full arm enforcement is OFF. But check sensitive default.
        if sensitive_enforced() and capability in _ALWAYS_SENSITIVE:
            return arm_open(capability, **kw)
        return True, "arm-gate-not-enforced"
    return arm_open(capability, **kw)


def arm_status(*, arm_dir=None, ops_dir=None, now=None, ttl_s: int = DEFAULT_TTL_S,
               secret=None) -> dict:
    """Read-only owner report (for /status, panel): per-capability armed?/reason."""
    out = {"enforced": enforced(), "caps": {}}
    for cap in DANGEROUS:
        ok, why = arm_open(cap, arm_dir=arm_dir, ops_dir=ops_dir, now=now,
                           ttl_s=ttl_s, secret=secret)
        out["caps"][cap] = {"armed": ok, "reason": why}
    return out
