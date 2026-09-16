#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""telegram_pep_shadow — DA-4-P1: PEP سایه روی مرز ارسال تلگرام (PHASE02 STEP1).

«کوچک‌ترین پچ مؤثر» به روایت قاضی (نقض INV-4: دو کلاینت تلگرام/دو PolicyGate).
این ماژول **سایه** است: هیچ مسیر زنده‌ای را نمی‌بندد؛ فقط هر ارسالِ ردشده از
گلوگاه را در برابر قراردادِ lease می‌سنجد و حکمِ «اگر enforce بود» را ثبت
می‌کند. فعال‌سازی = رأی مالک (پیش‌نویس ADR: 02-DECISIONS/DECISION-ARTIFACTS).

قرارداد lease (هم‌خانوادهٔ councils/pep_shadow، DA-4):
  · متصل به hashِ دقیقِ (action, params) — نه رشتهٔ آزاد
  · تک‌مصرف (nonce) · انقضای کوتاه · kill توزیع‌شده (لیست ابطالِ محلی)
  · deny-by-default در حالتِ enforce؛ سایه = فقط گزارش

نقشهٔ مرز (سطح A، 2026-08-16 ~05:1x):
  بات مرکز:  telegram_center/tg_api.py::TelegramBot._call_post  (تنها POST)
  بات پول:   budget/approval_channel.py::http_post (ساختار داخلی خودش)
  دکتر:      بدون ارسال مستقیم — relay از center (doctor_link)
  ارسال قانونی امروز بدون lease: همه — به همین دلیل سایه می‌سنجیم، نه می‌بندیم.
"""
from __future__ import annotations

import contextvars
import hashlib
import json
import os
import time
from contextlib import contextmanager
from pathlib import Path

from octopus_v3.lease import CapabilityLease, LeaseStore

STATE = Path(os.environ.get("OCTOPUS_STATE_DIR",
                            Path(__file__).resolve().parent.parent / "state"))
LOG = STATE / "telegram-pep-shadow.jsonl"
_TTL_S = 30.0
ENFORCE_FLAG = "OCTOPUS_TG_PEP_ENFORCE"
KILL_FLAG = "OCTOPUS_TG_PEP_KILL"
KEY_ENV = "OCTOPUS_TG_PEP_HMAC"
_TRUTHY = ("1", "true", "yes", "on")
_ACTIVE_REAL_LEASE: contextvars.ContextVar[CapabilityLease | None] = (
    contextvars.ContextVar("octopus_tg_pep_lease", default=None)
)
_REAL_STORE: LeaseStore | None = None
_REAL_KEY_FINGERPRINT = ""
_REAL_REVOKED: set[str] = set()


def params_sha(action: str, params: dict) -> str:
    blob = json.dumps([action, params], ensure_ascii=False,
                      sort_keys=True, default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:24]


class Lease:
    """اجارهٔ تک‌مصرف متصل به عمل — ساخت/امضا در آینده با رأی مالک."""
    __slots__ = ("lease_id", "action", "sha", "nonce", "expires_at", "consumed")

    def __init__(self, action: str, params: dict, ttl_s: float = _TTL_S):
        self.lease_id = f"tg-{hashlib.sha256(os.urandom(8)).hexdigest()[:8]}"
        self.action = action
        self.sha = params_sha(action, params)
        self.nonce = os.urandom(8).hex()
        self.expires_at = time.monotonic() + ttl_s
        self.consumed = False


class PepState:
    """ریجستریِ leaseها + ابطال — در سایه فقط برای سنجش، نه اجرا."""

    def __init__(self):
        self.leases: dict[str, Lease] = {}
        self.revoked: set[str] = set()

    def evaluate(self, action: str, params: dict, lease: Lease | None) -> dict:
        """حکم enforce-اگر-بود. هیچ اثری ندارد — خروجی = گزارش."""
        if lease is None:
            v, why = "deny", "no-lease (deny-by-default)"
        elif lease.lease_id in self.revoked:
            v, why = "deny", "revoked (distributed kill)"
        elif lease.consumed:
            v, why = "deny", "replay (single-use)"
        elif time.monotonic() > lease.expires_at:
            v, why = "deny", "expired"
        elif lease.sha != params_sha(action, params):
            v, why = "deny", "hash-mismatch (action/params drifted)"
        else:
            v, why = "allow", "lease-valid"
            lease.consumed = True
        return {"verdict": v, "reason": why,
                "lease": lease.lease_id if lease else None}


def enforce_on() -> bool:
    """Real enforcement is owner-gated and default-off."""
    return str(os.environ.get(ENFORCE_FLAG, "") or "").strip().lower() in _TRUTHY


def _real_store() -> LeaseStore | None:
    """Lazy HMAC authority. Missing/short key means issuance is fail-closed."""
    global _REAL_STORE, _REAL_KEY_FINGERPRINT
    raw = str(os.environ.get(KEY_ENV, "") or "")
    if len(raw) < 16:
        return None
    key = raw.encode("utf-8")
    fingerprint = hashlib.sha256(key).hexdigest()
    if _REAL_STORE is None or fingerprint != _REAL_KEY_FINGERPRINT:
        _REAL_STORE = LeaseStore(key)
        _REAL_KEY_FINGERPRINT = fingerprint
        _REAL_REVOKED.clear()
    return _REAL_STORE


def _bound_params(action: str, params: dict) -> dict:
    return {"action": str(action), "params": params if isinstance(params, dict) else {}}


def issue_real_lease(action: str, params: dict, *, ttl_s: float = _TTL_S,
                     now: float | None = None) -> CapabilityLease | None:
    """Mint one HMAC-signed, exact-action lease; no key means no lease."""
    store = _real_store()
    if store is None or not action or not isinstance(params, dict):
        return None
    try:
        ttl = min(_TTL_S, max(0.001, float(ttl_s)))
        return store.issue(
            capability=f"telegram:{action}",
            cost_cap_cents=0,
            max_calls=1,
            network_allow=("api.telegram.org",),
            ttl_s=ttl,
            bound_params=_bound_params(action, params),
            now=now,
        )
    except Exception:  # noqa: BLE001 — issuance must fail closed
        return None


def revoke_real_lease(lease_id: str) -> bool:
    """Local distributed-kill entry; unknown IDs are still safely deny-listed."""
    lid = str(lease_id or "").strip()
    if not lid:
        return False
    _REAL_REVOKED.add(lid)
    return True


@contextmanager
def use_real_lease(lease: CapabilityLease | None):
    """Bind a lease to exactly the current execution context."""
    token = _ACTIVE_REAL_LEASE.set(lease)
    try:
        yield lease
    finally:
        _ACTIVE_REAL_LEASE.reset(token)


def evaluate_real(action: str, params: dict, lease: CapabilityLease | None = None,
                  *, now: float | None = None) -> dict:
    """Consume a real lease atomically in its issuing process; every gap denies."""
    bound = lease if lease is not None else _ACTIVE_REAL_LEASE.get()
    if str(os.environ.get(KILL_FLAG, "") or "").strip().lower() in _TRUTHY:
        return {"verdict": "deny", "reason": "lease-kill-active", "lease": None}
    if bound is None:
        return {"verdict": "deny", "reason": "no-lease (deny-by-default)",
                "lease": None}
    lid = str(getattr(bound, "lease_id", "") or "")
    if lid in _REAL_REVOKED:
        return {"verdict": "deny", "reason": "revoked (distributed kill)",
                "lease": lid or None}
    store = _real_store()
    if store is None:
        return {"verdict": "deny", "reason": "lease-key-unavailable",
                "lease": lid or None}
    try:
        store.consume(
            bound,
            params=_bound_params(action, params),
            cost_cents=0,
            now=now,
        )
        return {"verdict": "allow", "reason": "lease-valid",
                "lease": lid or None}
    except Exception as exc:  # noqa: BLE001 — exact reason, never token/signature
        why = str(exc).strip().lower()
        if "expired" in why:
            reason = "expired"
        elif "burned" in why or "call cap" in why:
            reason = "replay (single-use)"
        elif "params hash" in why:
            reason = "hash-mismatch (action/params drifted)"
        elif "hmac" in why:
            reason = "bad-signature"
        elif "unknown lease" in why:
            reason = "unknown-lease"
        else:
            reason = f"lease-error:{type(exc).__name__}"
        return {"verdict": "deny", "reason": reason, "lease": lid or None}


def _record(sender: str, action: str, params: dict, mode: str, result: dict) -> None:
    """Content-free receipt: no body, signature, nonce, token, or chat ID."""
    try:
        rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
               "sender": str(sender)[:60], "action": str(action)[:40],
               "params_sha": params_sha(action, params),
               "mode": str(mode), **result}
        STATE.mkdir(parents=True, exist_ok=True)
        log = STATE / "telegram-pep-shadow.jsonl"
        with open(log, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:  # noqa: BLE001 — receipt never changes the verdict
        pass


def observe(sender: str, action: str, params: dict,
            lease: Lease | None = None, state: PepState | None = None) -> dict:
    """ناظرِ سایه — fail-soft؛ هرگز مسیرِ ارسال را نگه نمی‌دارد."""
    try:
        st = state or _SHARED
        r = st.evaluate(action, params, lease)
        _record(sender, action, params, "shadow", r)
        return r
    except Exception:  # noqa: BLE001 — سایه هرگز مرز را نمی‌کشد
        return {"verdict": "shadow-error", "reason": "observer failed"}


_SHARED = PepState()


def hook(sender: str, action: str, params: dict) -> dict:
    """Shared boundary: shadow by default; real deny-by-default when owner enables it."""
    enforcing = enforce_on()
    if not enforcing:
        r = observe(sender, action, params)
        return {**r, "enforced": False}
    try:
        r = evaluate_real(action, params)
    except Exception:  # noqa: BLE001 — enforcement errors deny, never authorize
        r = {"verdict": "deny", "reason": "pep-evaluation-error", "lease": None}
    _record(sender, action, params, "enforce", r)
    return {**r, "enforced": True}
