#!/usr/bin/env python3
"""human_append_guard.py — رفعِ E16: امضای «human-append» تا is_human=1 جعل‌ناپذیر شود.

مسئله (E16): ledgerِ ژنومِ فریز، mortal age_tick را روی *هر* append با is_human=True
جلو می‌برد. هر مسیرِ کدِ ارگانیسم می‌تواند is_human=True پاس کند و یک verdictِ «انسانی»
جعل کند. چون ژنوم فریز است، گارد این‌جا در لایهٔ ارگانیسم و روی گلوگاهِ نوشتنِ
`unified_bus.publish` می‌نشیند — نه در ژنوم.

طراحی (additive · fail-safe · backward-compatible · stdlib-only):
  * فقط approval_channel رازِ مشترک را دارد و می‌تواند token را `mint` کند.
  * token به approval_id + event_type + انقضا bind می‌شود؛ HMAC-SHA256.
  * `authorize()` می‌گوید آیا این is_human-append مجاز است.
  * approval_id یک‌بارمصرف است → محافظتِ replay درونِ پروسه.
  * اگر راز پیکربندی نشده باشد → گارد DISABLED (passthrough) تا پیش از وصلِ
    approval_channel چیزی نشکند؛ فقط یک alertِ مشورتی یک‌بار می‌زند.

هرگز به ledgerِ ژنوم دست نمی‌زند. فقط stdlib: hmac, time.
تست: `_ops/tests/test_human_append_guard.py` (standalone، بدونِ pytest).
"""
from __future__ import annotations

import hmac
import time
from typing import Callable, Optional, Tuple

_ALG = "sha256"
_TOKEN_VERSION = "v1"
DEFAULT_TTL_S = 900  # ۱۵ دقیقه


class HumanAppendError(Exception):
    """خطای پیکربندی/عملیاتِ گارد (مثلِ mint وقتی راز نیست)."""


def _sig(secret: bytes, approval_id: str, event_type: str, exp: int) -> str:
    msg = f"{approval_id}|{event_type}|{exp}".encode("utf-8")
    return hmac.new(secret, msg, _ALG).hexdigest()


class HumanAppendGuard:
    """گاردِ human-append. approval_channel با راز می‌سازد؛ unified_bus بدونِ راز
    فقط authorize می‌کند (راز را لازم ندارد اگر همان instance به اشتراک گذاشته شود)."""

    def __init__(self, secret: Optional[bytes] = None, *,
                 ttl_s: int = DEFAULT_TTL_S,
                 clock: Callable[[], float] = time.time) -> None:
        self._secret = secret
        self._ttl = int(ttl_s)
        self._clock = clock
        self._used: set[str] = set()   # replay: approval_id یک‌بارمصرف
        self._warned = False

    @property
    def enabled(self) -> bool:
        return self._secret is not None

    # ── سمتِ approval_channel (mint) ────────────────────────────────────────
    def mint(self, approval_id: str, event_type: str, *,
             ttl_s: Optional[int] = None) -> str:
        if not self.enabled:
            raise HumanAppendError("guard disabled: no secret; cannot mint")
        if not approval_id or not event_type:
            raise HumanAppendError("approval_id and event_type required")
        if "." in approval_id:
            raise HumanAppendError("approval_id must not contain '.'")
        exp = int(self._clock()) + int(self._ttl if ttl_s is None else ttl_s)
        sig = _sig(self._secret, approval_id, event_type, exp)
        return f"{_TOKEN_VERSION}.{approval_id}.{exp}.{sig}"

    # ── سمتِ نوشتنِ ledger (authorize) ───────────────────────────────────────
    def authorize(self, event_type: str, is_human: bool, *,
                  token: Optional[str] = None,
                  approval_id: Optional[str] = None) -> Tuple[bool, str]:
        """(allow_human, reason) برمی‌گرداند.
        allow_human=False یعنی: caller باید is_human را به 0 downgrade کند."""
        if not is_human:
            return (False, "not-human-append")
        if not self.enabled:
            self._warned = True
            return (True, "guard-disabled-passthrough")
        if not token:
            return (False, "missing-token")
        ok, reason, tok_id = self._verify(token, event_type)
        if not ok:
            return (False, reason)
        if approval_id is not None and approval_id != tok_id:
            return (False, "approval-id-mismatch")
        if tok_id in self._used:
            return (False, "replay")
        self._used.add(tok_id)
        return (True, "ok")

    def _verify(self, token: str, event_type: str) -> Tuple[bool, str, Optional[str]]:
        parts = token.split(".")
        if len(parts) != 4 or parts[0] != _TOKEN_VERSION:
            return (False, "bad-format", None)
        _, approval_id, exp_s, sig = parts
        try:
            exp = int(exp_s)
        except ValueError:
            return (False, "bad-exp", None)
        if int(self._clock()) > exp:
            return (False, "expired", None)
        expected = _sig(self._secret, approval_id, event_type, exp)
        if not hmac.compare_digest(expected, sig):
            return (False, "bad-signature", None)
        return (True, "ok", approval_id)


# راحتیِ wiring: یک گاردِ ماژول-سطح که پیش‌فرض DISABLED است (backward-compat).
_default_guard = HumanAppendGuard(None)


def default_guard() -> HumanAppendGuard:
    return _default_guard


def configure(secret: bytes, *, ttl_s: int = DEFAULT_TTL_S) -> HumanAppendGuard:
    """approval_channel این را با رازِ واقعی (از store، هرگز hardcode) صدا می‌زند."""
    global _default_guard
    _default_guard = HumanAppendGuard(secret, ttl_s=ttl_s)
    return _default_guard
