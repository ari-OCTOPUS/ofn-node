#!/usr/bin/env python3
"""fugu_quota.py — گاردِ «روزِ اول» فوگو: شمارندهٔ روزانهٔ attempt-counted + STOP-FUGU.

چرا شمارنده نه سقفِ دلاری؟ organ_gate با settle استِ رزرو را refund می‌کند
(organ_gate.py:121,127) و برای subscription:max هزینه ~۰ است → سقفِ نقدی
structurally inert است. تنها راندِ درستِ فوگو یک شمارندهٔ اختصاصیِ non-refunded است.

اصولِ ایمنی (رأی مالک 2026-07-24 «open now + harden parallel»):
  • attempt-counted: شمارنده *قبل از* تماسِ شبکه بالا می‌رود (reserve)، نه بعد از
    موفقیت — پس اندپوینتِ خراب/حلقه هم سهمیه را می‌سوزاند و cap زود می‌بندد
    (نه egressِ بی‌نهایت). این فیکسِ COST-1 است.
  • fail-closed: هر خطای گارد = deny = برگشت به مغزِ محلی. هرگز باز-به‌سمتِ‌پولی.
  • STOP-FUGU: فایلِ _ops/STOP-FUGU یا env OCTOPUS_FUGU_KILL → همه‌چیز محلی،
    ارگانیسم زنده می‌ماند و روی Ollama فکر می‌کند.
  • auto-trip: N شکستِ پیاپی (FUGU_FAIL_CEILING) → خودکار STOP-FUGU می‌نویسد
    (circuit-breakerِ سبکِ همیشه‌روشن؛ نسخهٔ کاملِ half-open = PR-B).
  • همیشه‌روشن هر وقت paid_gate باز است — پشتِ فلگِ جدا نیست (فیکسِ COST-5).

مصرف در model_router._ask_paid (پیرامونِ cli.complete):
    import fugu_quota
    q = fugu_quota.reserve(tier, organ)     # +1 قبل از تماس؛ deny → return None
    if not q["allow"]:
        organ_gate.release(...); return None
    try:
        out = cli.complete(...)
        fugu_quota.ok(tier)
    except Exception:
        fugu_quota.fail(tier)               # شمارنده قبلاً بالا رفته → شکست هم می‌سوزاند
        raise
"""
from __future__ import annotations

import datetime as _dt
import json
import os
from pathlib import Path

# ── config (env-only؛ خواندن هیچ‌چیز را روشن نمی‌کند) ─────────────────────────
_DEFAULT_CAP = 300          # سقفِ سراسریِ فراخوانیِ روزانه — پس از متری‌گیریِ واقعی کالیبره شود
# ۲۰۲۶-۰۸-۰۹ (VQ-FUGU-002، رأیِ مالک): از ۸ به ۱۰ — تقسیمِ نقشِ تازه با
# circuit_breaker.py. آن‌جا حالا per-tier + بک‌آفِ تصاعدی + پنجرهٔ نرخ‌محور دارد
# (تریپِ سریع و هوشمندِ per-provider). این‌جا فقط آخرین خط دفاع برایِ خاموشیِ
# **کاملِ** هر دو مغزِ پولی با هم است — عمداً کمی بالاتر از دو برابرِ
# failure_thresholdِ پیش‌فرضِ breaker (۵) تا breaker همیشه اول برسد.
_DEFAULT_FAIL_CEILING = 10   # N شکستِ پیاپیِ سراسری (هر دو tier) → auto STOP-FUGU


def _int_env(name: str, default: int, lo: int = 1) -> int:
    """خواندنِ int از env با fail-closed به default (هرگز «نامحدود»)."""
    try:
        v = int(str(os.environ.get(name, "")).strip())
        return v if v >= lo else default
    except Exception:  # noqa: BLE001
        return default


def _cap() -> int:
    return _int_env("FUGU_DAILY_CALL_CAP", _DEFAULT_CAP)


def _fail_ceiling() -> int:
    return _int_env("FUGU_FAIL_CEILING", _DEFAULT_FAIL_CEILING)


# ── base dir resolution (opslib.OPS در پروداکشن؛ override برای تست) ───────────
def _base() -> Path:
    ov = os.environ.get("FUGU_QUOTA_BASE")
    if ov:
        return Path(ov)
    try:
        import opslib  # type: ignore  # noqa: WPS433
        return Path(opslib.OPS)
    except Exception:  # noqa: BLE001 — خارج از ارگانیسم (تست): از مسیرِ ماژول حدس بزن
        return Path(__file__).resolve().parent.parent  # cortex/.. == _ops


def _state_path() -> Path:
    p = _base() / "state" / "fugu-quota.json"
    return p


def _stop_file() -> Path:
    return _base() / "STOP-FUGU"


def _today() -> str:
    try:
        import opslib  # type: ignore
        return opslib.today()
    except Exception:  # noqa: BLE001
        return _dt.date.today().isoformat()


# ── pure core (بدونِ I/O — کاملاً تست‌پذیر) ──────────────────────────────────
class Core:
    @staticmethod
    def blank(day: str) -> dict:
        # consecutive_failures = شمارندهٔ **سراسری** (رفتارِ تاریخی، دست‌نخورده).
        # by_tier = صداقتِ ۲۰۲۶-۰۷-۲۵: شاهدِ زنده نشان داد شمارندهٔ سراسری واقعیت را
        # پنهان می‌کند — Fugu سه‌از‌سه تایم‌اوت شد (۱۴:۱۵/۱۴:۳۵/۱۴:۵۵، هر سه ~۴۵s) ولی
        # consecutive_failures صفر بود، چون هر موفقیتِ GLM آن را ریست می‌کرد. پس یک tierِ
        # مرده نامرئی می‌ماند. این کلید فقط **گزارش** می‌دهد؛ هیچ تصمیمی روی آن سوار نیست.
        return {"day": day, "used_total": 0, "consecutive_failures": 0,
                "consecutive_failures_by_tier": {}, "used": {}, "denied": {}}

    @staticmethod
    def roll(state: dict, day: str) -> dict:
        """رولِ روزانه: روزِ نو = صفرِ کامل (شمارنده روزانه ریست می‌شود)."""
        if not isinstance(state, dict) or state.get("day") != day:
            return Core.blank(day)
        state.setdefault("used_total", 0)
        state.setdefault("consecutive_failures", 0)
        state.setdefault("consecutive_failures_by_tier", {})   # سازگارِ عقب: فایلِ قدیمی
        state.setdefault("used", {})
        state.setdefault("denied", {})
        return state

    @staticmethod
    def check(state: dict, cap: int) -> tuple[bool, str]:
        if state.get("used_total", 0) >= cap:
            return False, "daily-cap"
        return True, "ok"

    @staticmethod
    def count_attempt(state: dict, key: str) -> dict:
        """attempt-counted: قبل از تماس، بی‌قید و شرط بالا می‌رود."""
        state["used_total"] = state.get("used_total", 0) + 1
        state["used"][key] = state["used"].get(key, 0) + 1
        return state

    @staticmethod
    def count_denied(state: dict, reason: str) -> dict:
        state["denied"][reason] = state["denied"].get(reason, 0) + 1
        return state


# ── kill-switch (STOP-FUGU / env / organism halt) — fail-closed ──────────────
def killed() -> bool:
    """True = فوگو خاموش، برگرد به محلی. هر خطا = True (fail toward local)."""
    try:
        if _stop_file().exists():
            return True
        if str(os.environ.get("OCTOPUS_FUGU_KILL", "")).strip().lower() in (
                "1", "true", "yes", "on"):
            return True
        try:
            import opslib  # type: ignore
            if opslib.STOP_ORGANISM.exists() or opslib.halted():
                return True
        except Exception:  # noqa: BLE001
            pass
        return False
    except Exception:  # noqa: BLE001 — خطای ناشناخته = خاموش‌فرض (امن)
        return True


def _write_stop(reason: str) -> None:
    try:
        _stop_file().write_text(f"auto: {reason} @ {_today()}\n", encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass


# ── I/O-backed API (LockedJson در پروداکشن؛ fallbackِ سادهٔ اتمیک در تست) ─────
def _mutate(fn):
    """load→roll→fn(state)→persist. خروجیِ fn به فراخوان برمی‌گردد.
    شکستِ I/O = fail-closed (deny)، هرگز crash کنندهٔ مسیرِ LLM.

    VQ-FUGU-TOCTOU-001 (۲۰۲۶-۰۸-۰۷): قبلاً `except Exception: pass` هر خطای
    داخلِ بلوکِ LockedJson را هم می‌بلعید — شاملِ TimeoutError ِ واقعیِ قفلِ
    مشغول (opslib.LockedJson بعدِ ۵s تلاش raise می‌کند) و شکستِ نوشتنِ اتمیک
    (VQ-STATE-WRITE-001، دیده‌شده در پروداکشن). یعنی دقیقاً همان لحظه‌ای که
    پروسهٔ دیگری واقعاً روی این فایل کار می‌کرد، کد به fallbackِ بی‌قفل
    می‌افتاد — قراردادِ خودِ این تابع («شکستِ I/O = fail-closed») را نقض
    می‌کرد. حالا فقط نبودِ خودِ ماژول (import واقعاً نشد) به fallbackِ
    تک‌پروسه می‌افتد؛ هر خطای دیگر (قفلِ مشغول، شکستِ نوشتن، باگِ fn) طبقِ
    قراردادِ مستندشده fail-closed می‌شود (None، نه نوشتنِ بی‌قفل)."""
    path = _state_path()
    day = _today()
    try:
        import opslib  # type: ignore
    except ImportError:
        pass
    else:
        try:
            with opslib.LockedJson(path) as lj:
                st = Core.roll(lj.read() or {}, day)
                out = fn(st)
                lj.write(st)
                return out
        except Exception:  # noqa: BLE001 — قفل مشغول/شکستِ نوشتن: fail-closed، نه fallbackِ بی‌قفل
            return None
    # fallback ساده (تست/تک‌پروسه — فقط وقتی opslib اصلاً import نشد): read → mutate → atomic replace
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            st = json.loads(path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            st = {}
        st = Core.roll(st, day)
        out = fn(st)
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(st, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, path)
        return out
    except Exception:  # noqa: BLE001
        return None


def reserve(tier: str, organ: str = "ARCHITECT_SYS") -> dict:
    """قبل از هر تماسِ فوگو صدا زده می‌شود. attempt-counted + kill + cap.
    خروجی: {allow: bool, reason: str, used: int}."""
    if killed():
        _mutate(lambda st: Core.count_denied(st, "stop-fugu"))
        return {"allow": False, "reason": "stop-fugu", "used": -1}
    key = f"{tier}:{organ}"
    cap = _cap()

    def _fn(st):
        ok, why = Core.check(st, cap)
        if not ok:
            Core.count_denied(st, why)
            return {"allow": False, "reason": why, "used": st.get("used_total", 0)}
        Core.count_attempt(st, key)           # ← +1 قبل از تماس (attempt-counted)
        return {"allow": True, "reason": "ok", "used": st["used_total"]}

    out = _mutate(_fn)
    if out is None:                           # I/O شکست → fail-closed
        return {"allow": False, "reason": "quota-io-failclosed", "used": -1}
    return out


def ok(tier: str = "") -> None:
    """موفقیتِ تماس → ریستِ شمارندهٔ شکستِ پیاپی (سراسری = رفتارِ قبلی، و همان tier)."""
    def _fn(st):
        st["consecutive_failures"] = 0
        st["consecutive_timeouts"] = 0     # موفقیت رشتهٔ timeout را هم می‌شکند
        if tier:
            st.setdefault("consecutive_failures_by_tier", {})[str(tier)] = 0
        return None
    _mutate(_fn)


# ── timeoutِ محلی ≠ شکستِ فروشنده (یافتهٔ ۲۵ جولای، ۱۵/۱۵ شکست) ────────────────
# شاهد: در `state/paid-calls.jsonl` تنها نوعِ خطای کلِ لاگ `TimeoutError` بود — صفر ۴۰۱،
# صفر ۵xx، صفر connection-refused. هر ۱۵ شکست دقیقاً روی سقفِ سوکتِ **خودمان** مرد
# (۶ روی ۴۵s، ۹ روی ۲۰s). یعنی این شمارنده «ناسالم‌بودنِ فروشنده» را نمی‌سنجید؛
# کوتاه‌بودنِ ساعتِ خودمان را می‌سنجید — و بر همان مبنا مغزِ ۲۰۰ دلاری را خاموش می‌کرد.
# همان کلاسِ خطای `phi=300` و `σ=1`: معیاری که چیزی جز خودش را نمی‌سنجد.
#
# رفتار: طبقه‌بندی **همیشه** ثبت می‌شود (دیدنی‌شدن، بی‌تغییرِ رفتار)، ولی معافیت از
# kill-switch پشتِ فلگ و پیش‌فرض خاموش است — چون خاموش‌کردنِ یک گاردِ ایمنیِ پول
# رأیِ مالک است، نه تصمیمِ ایجنت.
TIMEOUT_EXEMPT_FLAG = "OCTOPUS_FUGU_TIMEOUT_NOT_PROVIDER_FAIL"
_TIMEOUT_MARKERS = ("timeout", "timed out", "timeouterror")


def _timeout_exempt() -> bool:
    return str(os.environ.get(TIMEOUT_EXEMPT_FLAG, "")).strip().lower() in ("1", "true", "yes", "on")


def is_local_timeout(error: object) -> bool:
    """آیا این خطا سقفِ سوکتِ خودمان است، نه پاسخِ فروشنده؟ محافظه‌کار: مبهم → False."""
    if error is None:
        return False
    if isinstance(error, TimeoutError):        # socket.timeout هم از 3.10 همین است
        return True
    try:
        name = type(error).__name__.lower()
        if "timeout" in name:
            return True
        blob = str(error).lower()
    except Exception:  # noqa: BLE001
        return False
    # URLError/OSErrorِ پوشاننده: فقط اگر صریحاً timeout بگوید. کدِ HTTP = پاسخِ فروشنده.
    if any(ch.isdigit() for ch in blob[:6]) and "http" in blob:
        return False
    return any(m in blob for m in _TIMEOUT_MARKERS)


def fail(tier: str = "", error: object = None) -> None:
    """شکستِ تماس → +۱ شکستِ پیاپی؛ در سقف → auto STOP-FUGU.

    `error` (اختیاری) استثنای واقعی است. با `TIMEOUT_EXEMPT_FLAG` روشن، timeoutِ محلی
    شمارندهٔ شکستِ فروشنده را بالا نمی‌برد و سقف را شلیک نمی‌کند — فقط در
    `consecutive_timeouts` ثبت می‌شود. بدونِ فلگ (یا بدونِ `error`) رفتار بایت‌به‌بایتِ قبلی.

    ✅ VQ-FUGU-002 پاسخ گرفت (رأیِ مالک، ۲۰۲۶-۰۸-۰۹): سقفِ این‌جا عمداً روی
    شمارندهٔ **سراسری** ماند، ولی نقشش عوض شد — دیگر «تنها خطِ دفاع» نیست،
    فقط **آشکارسازِ خاموشیِ کاملِ هر دو مغز** است. حفاظتِ per-tier
    (مثلِ شاهدِ ۲۰۲۶-۰۷-۲۵: primary مرده، secondary سالم) حالا کارِ
    `circuit_breaker.py` است — per-target، بک‌آفِ تصاعدی، و پنجرهٔ نرخ‌محور
    برایِ providerِ پوسته‌پوسته. سراسری‌ماندنِ این‌جا عمدی است: اگر یک روز
    circuit_breaker خودش خاموش/معیوب بود، STOP-FUGU همچنان یک backstop
    مستقل و ساده می‌ماند. شمارندهٔ per-tير همچنان فقط **دیدنی** است، این‌جا
    trip نمی‌کند."""
    ceiling = _fail_ceiling()
    _to = is_local_timeout(error)
    _exempt = _to and _timeout_exempt()

    def _fn(st):
        # طبقه‌بندی همیشه ثبت می‌شود — حتی با فلگِ خاموش — تا مالک عدد را ببیند.
        if _to:
            st["consecutive_timeouts"] = st.get("consecutive_timeouts", 0) + 1
            st["timeouts_total"] = st.get("timeouts_total", 0) + 1
        else:
            st["consecutive_timeouts"] = 0
        if error is not None:
            st["last_error_class"] = type(error).__name__
            st["last_error_was_local_timeout"] = bool(_to)
        if _exempt:
            return None                        # نه شمارشِ شکستِ فروشنده، نه شلیکِ سقف
        st["consecutive_failures"] = st.get("consecutive_failures", 0) + 1
        if tier:
            _bt = st.setdefault("consecutive_failures_by_tier", {})
            _bt[str(tier)] = _bt.get(str(tier), 0) + 1
        return st["consecutive_failures"]
    n = _mutate(_fn)
    if isinstance(n, int) and n >= ceiling:
        _write_stop(f"{n} consecutive Fugu failures (>= {ceiling})")


def status() -> dict:
    """گزارشِ فقط‌خواندنی برای cockpit/CLI."""
    day = _today()
    try:
        st = Core.roll(json.loads(_state_path().read_text(encoding="utf-8")), day)
    except Exception:  # noqa: BLE001
        st = Core.blank(day)
    return {
        "day": st.get("day"),
        "cap": _cap(),
        "used_total": st.get("used_total", 0),
        "remaining": max(0, _cap() - st.get("used_total", 0)),
        "consecutive_failures": st.get("consecutive_failures", 0),
        "consecutive_failures_by_tier": dict(st.get("consecutive_failures_by_tier") or {}),
        "fail_ceiling": _fail_ceiling(),
        "killed": killed(),
        "used": st.get("used", {}),
        "denied": st.get("denied", {}),
    }


if __name__ == "__main__":
    print(json.dumps(status(), ensure_ascii=False, indent=2))
