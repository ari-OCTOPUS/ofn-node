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
  * اگر راز پیکربندی نشده باشد → پیش‌فرض DISABLED (passthrough) تا پیش از وصلِ
    approval_channel چیزی نشکند. با فلگِ مالک HH_HUMAN_GUARD_STRICT=1 همین شاخه
    default-deny می‌شود (fail-closed، Saltzer-Schroeder/CISA/NIST)؛ با
    HH_HUMAN_GUARD_SHADOW_ALERT=1 فقط would-deny را یک‌بار لاگ می‌کند بی‌آنکه رفتار
    عوض شود. (پیش‌فرضِ هر دو خاموش = byte-identical با رفتارِ امروز؛ رأی مالک «برو» 2026-07-11.)

هرگز به ledgerِ ژنوم دست نمی‌زند. import-time فقط stdlib (hmac/os/time)؛ opslib فقط
lazy/best-effort برای هشدارِ سایه (fail-soft). تست: `_ops/tests/test_human_append_guard.py`.
"""
from __future__ import annotations

import hmac
import os
import time
from typing import Callable, Optional, Tuple

_ALG = "sha256"
_TOKEN_VERSION = "v1"
DEFAULT_TTL_S = 900  # ۱۵ دقیقه

# فلگ‌های env (فقط مالک؛ پیش‌فرضِ خاموش = رفتارِ امروز، byte-identical).
_ENV_STRICT = "HH_HUMAN_GUARD_STRICT"          # روشن → بی‌سکرت DENY (default-deny)
_ENV_SHADOW = "HH_HUMAN_GUARD_SHADOW_ALERT"    # روشن → فقط هشدارِ would-deny، همان passthrough
_TRUTHY = {"1", "true", "yes", "on", "strict"}


def _env_truthy(name: str) -> bool:
    return str(os.environ.get(name, "")).strip().lower() in _TRUTHY


def _emit_shadow_alert(msg: str) -> None:
    """هشدارِ fail-soft و lazy — importِ opslib فقط در زمانِ فراخوان تا خاصیتِ
    stdlib-only در import-time نشکند (این ماژول باید بدونِ هستهٔ ارگانیسم هم import شود)."""
    try:
        import opslib  # lazy, best-effort
        opslib.alert([msg])
    except Exception:  # noqa: BLE001 — هشدار هرگز مسیرِ گارد را نمی‌کشد
        pass


class HumanAppendError(Exception):
    """خطای پیکربندی/عملیاتِ گارد (مثلِ mint وقتی راز نیست)."""


def _sig(secret: bytes, approval_id: str, event_type: str, exp: int) -> str:
    msg = f"{approval_id}|{event_type}|{exp}".encode("utf-8")
    return hmac.new(secret, msg, _ALG).hexdigest()


class HumanAppendGuard:
    """گاردِ human-append. approval_channel با راز می‌سازد؛ unified_bus بدونِ راز
    فقط authorize می‌کند (راز را لازم ندارد اگر همان instance به اشتراک گذاشته شود).

    strict/shadow_alert فقط شاخهٔ «بی‌سکرت» را می‌سازند؛ وقتی راز هست (enabled)،
    مسیرِ HMAC حاکم است و این دو هیچ اثری ندارند."""

    def __init__(self, secret: Optional[bytes] = None, *,
                 ttl_s: int = DEFAULT_TTL_S,
                 clock: Callable[[], float] = time.time,
                 strict: bool = False,
                 shadow_alert: bool = False) -> None:
        self._secret = secret
        self._ttl = int(ttl_s)
        self._clock = clock
        self._used: set[str] = set()   # replay: approval_id یک‌بارمصرف
        self._warned = False
        self._strict = bool(strict)            # بی‌سکرت → DENY (fail-closed)
        self._shadow_alert = bool(shadow_alert)  # بی‌سکرت → هشدار ولی passthrough

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
            # strict (رأی مالک، قابلِ‌فلیپ): بی‌سکرت = default-deny
            # (Saltzer-Schroeder / CISA SBD / NIST SA-8(23)). پیش‌فرض strict=False → رفتارِ امروز.
            if self._strict:
                return (False, "fail-closed-no-secret")
            if not self._warned:
                self._warned = True
                if self._shadow_alert:
                    _emit_shadow_alert(
                        "HumanAppendGuard unconfigured → passthrough "
                        "(would DENY under HH_HUMAN_GUARD_STRICT=1)")
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
# strict/shadow را از env می‌خواند تا مالک بتواند بدونِ تغییرِ کد فلیپ کند
# (پیش‌فرضِ هر دو خاموش = byte-identical با امروز).
_default_guard = HumanAppendGuard(None, strict=_env_truthy(_ENV_STRICT),
                                  shadow_alert=_env_truthy(_ENV_SHADOW))


def default_guard() -> HumanAppendGuard:
    return _default_guard


def guard_from_env(secret: Optional[bytes] = None, *,
                   ttl_s: int = DEFAULT_TTL_S) -> "HumanAppendGuard":
    """گاردی که strict/shadow را از env می‌خواند (پیش‌فرضِ هر دو خاموش = رفتارِ امروز).
    مسیرِ توصیه‌شدهٔ فلیپِ مالک: HH_HUMAN_GUARD_STRICT=1 (enforce) یا
    HH_HUMAN_GUARD_SHADOW_ALERT=1 (فقط مشاهده)."""
    return HumanAppendGuard(secret, ttl_s=ttl_s,
                            strict=_env_truthy(_ENV_STRICT),
                            shadow_alert=_env_truthy(_ENV_SHADOW))


def configure(secret: bytes, *, ttl_s: int = DEFAULT_TTL_S) -> HumanAppendGuard:
    """approval_channel این را با رازِ واقعی (از store، هرگز hardcode) صدا می‌زند."""
    global _default_guard
    _default_guard = HumanAppendGuard(secret, ttl_s=ttl_s)
    return _default_guard
