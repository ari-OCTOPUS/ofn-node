#!/usr/bin/env python3
"""agent_bearer.py — owner-issued bearer token for the AgentGateway (M3.B v1).

Generalizes the existing HMAC token pattern (callback_token.py / human_append_guard.py)
to a NEW purpose: proving that the OWNER authorized a given peer AGI to connect.

Contract (bound inside the HMAC, so nothing can be extended/forged after mint):
    version | peer_id | expires_epoch
Token wire form:  v1.<peer_id>.<expires>.<sig>

Secret: env OCTOPUS_AGENT_OWNER_SECRET only. Never logged / persisted / echoed and this
module never *creates* the value (minting the secret is the owner's job — same discipline
as OCTOPUS_CB_SECRET). Constant-time compare (hmac.compare_digest). stdlib-only.

Two-factor design (defense-in-depth): the bearer proves OWNER-authorization; the per-peer
HMAC signature on the request body (see agent_gateway_http.py) proves PEER identity.
Neither alone is sufficient. Fail-closed everywhere: no secret / bad token / expired = deny.

NOTE: this module has NO effect-side. It cannot approve, merge, send, or write organism
state. It only answers a yes/no question about a token.
"""
from __future__ import annotations

import hmac
import hashlib
import os
import time

VERSION = "v1"
SECRET_ENV = "OCTOPUS_AGENT_OWNER_SECRET"
_SIG_LEN = 32  # hex chars of sha256


def _secret() -> bytes | None:
    s = os.environ.get(SECRET_ENV, "")
    s = s.strip() if isinstance(s, str) else ""
    return s.encode("utf-8") if s else None


def _sig(secret: bytes, peer_id: str, expires: str) -> str:
    msg = f"{VERSION}|{peer_id}|{expires}".encode("utf-8")
    return hmac.new(secret, msg, hashlib.sha256).hexdigest()[:_SIG_LEN]


def mint(peer_id: str, expires_epoch: int) -> str:
    """Owner-side mint. "" if no secret (fail-closed: never emit a token-less pass).

    peer_id must not contain '.' (delimiter). Owner runs this offline to hand a peer a
    time-boxed bearer; the organism never auto-mints peer authorizations."""
    sec = _secret()
    if not sec:
        return ""
    peer_id = str(peer_id)
    if not peer_id or "." in peer_id:
        return ""
    exp = str(int(expires_epoch))
    return f"{VERSION}.{peer_id}.{exp}.{_sig(sec, peer_id, exp)}"


def verify(token, peer_id: str, *, now: float | None = None) -> tuple[bool, str]:
    """(ok, reason). Fail-closed: missing token/secret, bad format, wrong peer, expired,
    or any HMAC mismatch → (False, reason). Enforces expiry HERE (unlike callback_token,
    which leaves now<=exp to the handler) so a stolen-but-expired bearer is inert."""
    if not token or not isinstance(token, str):
        return (False, "missing-token")
    sec = _secret()
    if not sec:
        return (False, "no-secret")            # fail-closed: nothing verifies
    parts = token.split(".")
    if len(parts) != 4 or parts[0] != VERSION:
        return (False, "bad-format")
    _, tok_peer, exp_s, sig = parts
    if tok_peer != str(peer_id):
        return (False, "peer-mismatch")
    try:
        exp = int(exp_s)
    except (TypeError, ValueError):
        return (False, "bad-exp")
    _now = float(now if now is not None else time.time())
    if _now > exp:
        return (False, "expired")
    expected = _sig(sec, tok_peer, exp_s)
    if not hmac.compare_digest(sig, expected):
        return (False, "bad-signature")
    return (True, "ok")
