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
_DEFAULT_FAIL_CEILING = 8   # N شکستِ پیاپی → auto STOP-FUGU


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
    شکستِ I/O = fail-closed (deny)، هرگز crash کنندهٔ مسیرِ LLM."""
    path = _state_path()
    day = _today()
    try:
        import opslib  # type: ignore
        with opslib.LockedJson(path) as lj:
            st = Core.roll(lj.read() or {}, day)
            out = fn(st)
            lj.write(st)
            return out
    except ImportError:
        pass
    except Exception:  # noqa: BLE001 — قفل/opslib در دسترس نبود → مسیرِ سادهٔ زیر
        pass
    # fallback ساده (تست/تک‌پروسه): read → mutate → atomic replace
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
        if tier:
            st.setdefault("consecutive_failures_by_tier", {})[str(tier)] = 0
        return None
    _mutate(_fn)


def fail(tier: str = "") -> None:
    """شکستِ تماس → +۱ شکستِ پیاپی؛ در سقف → auto STOP-FUGU.

    ⚠️ حکمِ سقف عمداً روی شمارندهٔ **سراسری** ماند (بدونِ تغییرِ رفتار). دلیل: STOP-FUGU
    سراسری است، پس شلیکش از شکستِ یک tier، مغزِ *سالمِ* tierِ دیگر را هم می‌کشد — و
    شاهدِ زندهٔ ۲۰۲۶-۰۷-۲۵ همین بود (primary مرده، secondary سالم و پاسخ‌گو). پیامدش این
    است که در الگوی «primary می‌افتد → secondary جواب می‌دهد» سقف هرگز شلیک نمی‌کند؛
    این یک تصمیمِ طراحی است که رأیِ مالک لازم دارد (VQ-FUGU-002)، نه چیزی که ایجنت
    یک‌طرفه عوض کند. شمارندهٔ per-tier فقط آن را **دیدنی** می‌کند."""
    ceiling = _fail_ceiling()

    def _fn(st):
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
