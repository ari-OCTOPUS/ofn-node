"""Authentication primitives. Pure verification — no sockets, no clock.

Two mechanisms, for the two shells the partners use.

**Init-data verification** for the messaging-app shell. The client hands the
server a signed blob describing who launched the app. The signature is an
HMAC keyed on the bot token, so only someone holding that token could have
produced it. Getting the key derivation backwards is the classic bug here —
the secret is `HMAC(key="WebAppData", msg=bot_token)`, not the reverse — so
it is written once, here, and never re-implemented at a call site.

**Session tokens** for everything after the first request. Re-validating the
same static init-data blob on every call is what makes replay cheap: the blob
does not change, so an attacker who captures one can use it until it ages
out. Instead we validate once, then issue a short-lived token bound to the
tenant and the user.

Three properties this module refuses to compromise on:

  * Every comparison is constant-time. A timing oracle on an HMAC is a slow
    but complete break.
  * Freshness is mandatory and short. The default window is minutes, not the
    hour that libraries commonly default to, because init data never refreshes
    on its own — a long window is a long replay window.
  * Nothing here trusts a field the client could have written. The unsigned
    convenience copy of the user object that clients also send is not read by
    any function in this file.
"""

from __future__ import annotations

import hashlib
import hmac
import re
from dataclasses import dataclass
from typing import Mapping

# Init data is only good for a few minutes. It is issued once when the app
# opens and is never refreshed, so this is a replay window, not a session
# length — the session token below is what carries the user forward.
DEFAULT_MAX_AGE_S = 600

SESSION_TTL_S = 3600

_SAFE = re.compile(r"^[A-Za-z0-9_\-]{1,64}$")


class AuthError(Exception):
    """Verification failed. Deliberately carries no detail about *which*
    check failed when returned to a client — an attacker learning that the
    signature was fine but the timestamp was stale is a free oracle.

    `reason` is for the operator, not the caller. It never reaches a
    response body; it exists so that "login does not work" can be answered
    from the journal instead of guessed at. Every value is a fixed word from
    the set below — never a user id, a name, or any part of the blob.
    """

    def __init__(self, message: str, reason: str = "") -> None:
        super().__init__(message)
        self.reason = reason or message


@dataclass(frozen=True)
class VerifiedUser:
    user_id: str
    username: str
    auth_date: int
    raw_fields: Mapping[str, str]


def _parse_qs(raw: str) -> dict[str, str]:
    """Minimal query-string parse. Percent-decoding is left to the adapter —
    the signature covers the decoded values, so decoding must happen before
    this function, and doing it twice would corrupt the check string."""
    out: dict[str, str] = {}
    for pair in raw.split("&"):
        if not pair:
            continue
        key, sep, value = pair.partition("=")
        if not sep:
            raise AuthError("malformed init data")
        out[key] = value
    return out


def data_check_string(fields: Mapping[str, str]) -> str:
    """Canonical string the signature is computed over.

    Both `hash` and `signature` are excluded: `hash` is the value being
    checked, and `signature` belongs to a separate third-party verification
    scheme whose presence must not change this computation.
    """
    items = sorted((k, v) for k, v in fields.items()
                   if k not in ("hash", "signature"))
    return "\n".join(f"{k}={v}" for k, v in items)


def verify_init_data(
    fields: Mapping[str, str],
    bot_token: str,
    *,
    now_epoch_s: int,
    max_age_s: int = DEFAULT_MAX_AGE_S,
) -> VerifiedUser:
    """Verify a launch blob and return the user it attests to.

    Raises `AuthError` on any failure. There is no "partially valid" return
    value, because every caller of this function is about to make an
    authorisation decision.
    """
    if not bot_token:
        raise AuthError("verification unavailable", "no_bot_token")

    received = fields.get("hash", "")
    if not received:
        raise AuthError("invalid credentials", "no_hash")

    secret = hmac.new(b"WebAppData", bot_token.encode("utf-8"),
                      hashlib.sha256).digest()
    expected = hmac.new(secret, data_check_string(fields).encode("utf-8"),
                        hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, received):
        # The single most common cause is the token in the config not being
        # the token of the bot the button was configured on — a rotation
        # that landed in one place and not the other.
        raise AuthError("invalid credentials", "signature_mismatch")

    try:
        auth_date = int(fields.get("auth_date", ""))
    except ValueError:
        raise AuthError("invalid credentials", "bad_auth_date") from None

    age = now_epoch_s - auth_date
    if age > max_age_s:
        raise AuthError("invalid credentials", "blob_too_old")
    if age < -60:
        # Issued in the future by more than clock skew allows. On a board with
        # no battery-backed clock this is as likely to be our fault as theirs,
        # but accepting it would let a forged future timestamp live forever.
        raise AuthError("invalid credentials", "clock_skew")

    user_id, username = _extract_user(fields.get("user", ""))
    return VerifiedUser(user_id=user_id, username=username,
                        auth_date=auth_date, raw_fields=dict(fields))


def _extract_user(blob: str) -> tuple[str, str]:
    """Pull id and username out of the signed user object.

    Read with a regex rather than a JSON parser on purpose: this value is
    inside the signed payload, so it is trustworthy, but it arrives as a
    string and we want exactly two scalar fields from it. Parsing the whole
    object would invite a caller to start reading other fields from a shape
    we do not control.
    """
    if not blob:
        raise AuthError("invalid credentials")
    m_id = re.search(r'"id"\s*:\s*(\d+)', blob)
    if not m_id:
        raise AuthError("invalid credentials")
    m_name = re.search(r'"username"\s*:\s*"([^"]*)"', blob)
    return m_id.group(1), (m_name.group(1) if m_name else "")


def parse_and_verify(
    raw_decoded: str,
    bot_token: str,
    *,
    now_epoch_s: int,
    max_age_s: int = DEFAULT_MAX_AGE_S,
) -> VerifiedUser:
    """Convenience wrapper over `_parse_qs` + `verify_init_data`."""
    return verify_init_data(_parse_qs(raw_decoded), bot_token,
                            now_epoch_s=now_epoch_s, max_age_s=max_age_s)


# ── session tokens ───────────────────────────────────────────────────────
@dataclass(frozen=True)
class Session:
    tenant: str
    user_id: str
    issued_at: int
    expires_at: int


def issue_session(tenant: str, user_id: str, secret: str, *,
                  now_epoch_s: int, ttl_s: int = SESSION_TTL_S) -> str:
    """Mint a signed, self-contained session token.

    The tenant is inside the signature, so a token minted for one leg cannot
    be presented to another — a partner's token is useless against a sibling
    business even if the transport leaks it.
    """
    if not _SAFE.match(tenant) or not _SAFE.match(user_id):
        raise AuthError("invalid session subject")
    if not secret:
        raise AuthError("session signing unavailable")
    exp = now_epoch_s + ttl_s
    body = f"{tenant}.{user_id}.{now_epoch_s}.{exp}"
    sig = hmac.new(secret.encode("utf-8"), body.encode("utf-8"),
                   hashlib.sha256).hexdigest()[:32]
    return f"{body}.{sig}"


def verify_session(token: str, secret: str, *, now_epoch_s: int) -> Session:
    """Validate a session token. Raises `AuthError` on anything unexpected."""
    if not secret:
        raise AuthError("session verification unavailable")
    parts = token.split(".")
    if len(parts) != 5:
        raise AuthError("invalid session")
    tenant, user_id, issued, exp, sig = parts
    body = f"{tenant}.{user_id}.{issued}.{exp}"
    expected = hmac.new(secret.encode("utf-8"), body.encode("utf-8"),
                        hashlib.sha256).hexdigest()[:32]
    if not hmac.compare_digest(expected, sig):
        raise AuthError("invalid session")
    try:
        issued_i, exp_i = int(issued), int(exp)
    except ValueError:
        raise AuthError("invalid session") from None
    if now_epoch_s >= exp_i:
        raise AuthError("session expired")
    return Session(tenant=tenant, user_id=user_id,
                   issued_at=issued_i, expires_at=exp_i)


class ReplayGuard:
    """Rejects an init-data blob that has already been accepted.

    The signature stays valid for the whole freshness window, so without this
    a captured blob can be replayed repeatedly inside it. Entries are pruned
    by age; the guard therefore stays small without needing a background job.
    """

    def __init__(self, window_s: int = DEFAULT_MAX_AGE_S) -> None:
        self._seen: dict[str, int] = {}
        self._window = window_s

    def check_and_remember(self, digest: str, now_epoch_s: int) -> None:
        self._prune(now_epoch_s)
        if digest in self._seen:
            raise AuthError("invalid credentials")
        self._seen[digest] = now_epoch_s

    def _prune(self, now_epoch_s: int) -> None:
        cutoff = now_epoch_s - self._window
        for key in [k for k, t in self._seen.items() if t < cutoff]:
            del self._seen[key]

    def __len__(self) -> int:
        return len(self._seen)
