#!/usr/bin/env python3
"""circuit_breaker.py — Circuit breaker per-target برای تماس‌های بیرونی (M1-M2).

خط‌قرمزهای سخت:
  • fail-closed: circuit باز = هرگز تماس نمی‌زند (fast-fail).
  • state اتمیک (LockedJson) — چندپارگی بین فرایندها محال.
  • اعداد از budgets.yaml (I6)؛ نبود = default با tag EST (همان الگوی opslib.fx).
  • stdlib-only؛ $0 offline؛ propose-only.
"""
from __future__ import annotations

import json
import sys
from enum import Enum
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
import opslib  # noqa: E402

STATE_PATH = opslib.STATE_DIR / "circuit-state.json"


class State(Enum):
    CLOSED = "closed"       # عادی — تماس مجاز
    OPEN = "open"           # fail-fast — صفر تماس
    HALF_OPEN = "half_open" # یک تماس آزمایشی مجاز


def _cfg() -> dict:
    """پیکربندی از budgets.yaml → resilience.circuit_breaker. نبود = default."""
    try:
        b = opslib.load_budgets()
    except Exception:  # noqa: BLE001
        b = {}
    r = (b.get("resilience") or {}).get("circuit_breaker") or {}
    return {
        "failure_threshold": int(r.get("failure_threshold", 5)),
        "cooldown_seconds": float(r.get("cooldown_seconds", 60)),
        "half_open_max": int(r.get("half_open_max", 3)),
        "success_to_close": int(r.get("success_to_close", 2)),
        # ۲۰۲۶-۰۸-۰۹ (VQ-FUGU-002، رأیِ مالک): شاهدِ زندهٔ همان روز — cooldownِ
        # ثابتِ ۶۰s برایِ یک خرابیِ چندساعته یعنی probe هر ۶۰-۹۰s برایِ ۲۲+
        # ساعت، هر probe یک attemptِ روزانهٔ fugu_quota را می‌سوزاند. بک‌آفِ
        # تصاعدی: هر چرخهٔ پیاپیِ OPEN (نه فقط اولین‌بار) cooldownِ مؤثر را
        # دوبرابر می‌کند تا سقف — closeِ واقعی (نه فقط یک نیمه‌باز موفق) صفرش
        # می‌کند. خرابیِ گذرا هنوز در همان ۶۰s اول جواب می‌دهد؛ فقط خرابیِ
        # پایدار آرام می‌شود.
        "max_cooldown_seconds": float(r.get("max_cooldown_seconds", 3600)),
        # پنجرهٔ نرخ‌محور: نقطه‌کورِ شمارندهٔ پیاپی — providerِ پوسته‌پوسته
        # (۱ موفقیت از هر ۱۰) هرگز به threshold ِ پیاپی نمی‌رسد چون هر موفقیت
        # fail_count را صفر می‌کند. این پنجره مستقل از پیاپی‌بودن قضاوت می‌کند.
        "window_size": int(r.get("window_size", 20)),
        "window_min_samples": int(r.get("window_min_samples", 10)),
        "window_fail_rate": float(r.get("window_fail_rate", 0.7)),
        "tag": "FACT(budgets.yaml)" if r else "EST(default)",
    }


def _load_state() -> dict:
    with opslib.LockedJson(STATE_PATH) as lj:
        return lj.read()


def _save_state(state: dict) -> None:
    with opslib.LockedJson(STATE_PATH) as lj:
        lj.write(state)


def _target_entry(state: dict, target: str) -> dict:
    t = state.setdefault("targets", {}).setdefault(target, {})
    t.setdefault("state", State.CLOSED.value)
    t.setdefault("fail_count", 0)
    t.setdefault("success_count", 0)
    t.setdefault("last_fail_ts", None)
    t.setdefault("last_ok_ts", None)
    t.setdefault("opened_at_ts", None)
    t.setdefault("half_open_attempts", 0)
    # ۲۰۲۶-۰۸-۰۹ (VQ-FUGU-002): consecutive_opens = چندبار پیاپی این target
    # بدونِ یک closeِ واقعی دوباره OPEN شده — پایهٔ بک‌آفِ تصاعدی. فقط با
    # closeِ کامل صفر می‌شود، نه با هر موفقیتِ تکی.
    t.setdefault("consecutive_opens", 0)
    # recent_outcomes = آخرین window_size نتیجه (True=ok/False=fail)، پایهٔ
    # تریگرِ نرخ‌محور. لیستِ ساده کافی است — پنجره «آخرین N call» است نه
    # «آخرین N دقیقه».
    t.setdefault("recent_outcomes", [])
    return t


def _effective_cooldown(t: dict, cfg: dict) -> float:
    """cooldownِ مؤثر با بک‌آفِ تصاعدی: base × 2^(consecutive_opens-1)، سقف‌دار.

    چرخهٔ اول (consecutive_opens=1) = همان cooldownِ پایه، بدونِ ضریب — خرابیِ
    گذرا نباید کندتر از قبل جواب بدهد. فقط چرخهٔ دوم به بعد رشد می‌کند."""
    base = cfg["cooldown_seconds"]
    n = int(t.get("consecutive_opens", 0) or 0)
    return min(base * (2.0 ** max(n - 1, 0)), cfg["max_cooldown_seconds"])


def _record_outcome(t: dict, ok: bool, window_size: int) -> None:
    hist = t.setdefault("recent_outcomes", [])
    hist.append(bool(ok))
    if len(hist) > window_size:
        del hist[: len(hist) - window_size]


def _window_says_open(t: dict, cfg: dict) -> bool:
    """نرخ‌محور: ≥window_fail_rate شکست با حداقلِ window_min_samples نمونه."""
    hist = t.get("recent_outcomes") or []
    n = len(hist)
    if n < cfg["window_min_samples"]:
        return False
    fails = sum(1 for ok in hist if not ok)
    return (fails / n) >= cfg["window_fail_rate"]


def check(target: str) -> dict:
    """بررسی circuit برای target. خروجی: {allow: bool, state: str, reason: str}.
    allow=False → فراخوان‌کننده باید فوراً fail-soft کند (صفر شبکه)."""
    cfg = _cfg()
    state = _load_state()
    t = _target_entry(state, target)
    st = State(t["state"])

    if st is State.OPEN:
        opened = t.get("opened_at_ts")
        cooldown = _effective_cooldown(t, cfg)
        if opened is not None:  # نه `if opened:` — ۰.۰ falsy است ولی timestamp معتبر
            import time as _time
            elapsed = _time.time() - opened
            if elapsed >= cooldown:
                t["state"] = State.HALF_OPEN.value
                t["half_open_attempts"] = 0
                _save_state(state)
                return {"allow": True, "state": State.HALF_OPEN.value,
                        "reason": f"cooldown elapsed ({int(elapsed)}s) → half_open"}
        return {"allow": False, "state": State.OPEN.value,
                "reason": f"circuit open (cooldown {int(cooldown)}s, "
                          f"backoff x{2 ** int(t.get('consecutive_opens', 0) or 0)})"}

    if st is State.HALF_OPEN:
        if t.get("half_open_attempts", 0) >= cfg["half_open_max"]:
            return {"allow": False, "state": State.HALF_OPEN.value,
                    "reason": f"half_open max attempts ({cfg['half_open_max']}) reached"}
        return {"allow": True, "state": State.HALF_OPEN.value,
                "reason": "half_open (one probe allowed)"}

    return {"allow": True, "state": State.CLOSED.value, "reason": "circuit closed"}


def record_success(target: str) -> dict:
    """ثبت موفقیت. اگر در half_open به success_to_close رسید → closed."""
    cfg = _cfg()
    state = _load_state()
    t = _target_entry(state, target)
    t["last_ok_ts"] = opslib.now_iso()
    t["fail_count"] = 0
    _record_outcome(t, True, cfg["window_size"])

    st = State(t["state"])
    just_closed = False
    if st is State.HALF_OPEN:
        t["success_count"] = t.get("success_count", 0) + 1
        t["half_open_attempts"] = t.get("half_open_attempts", 0) + 1
        if t["success_count"] >= cfg["success_to_close"]:
            t["state"] = State.CLOSED.value
            t["success_count"] = 0
            t["half_open_attempts"] = 0
            t["opened_at_ts"] = None
            # ۲۰۲۶-۰۸-۰۹ (VQ-FUGU-002): فقط closeِ **واقعی** (نه هر probeِ تکی)
            # پلهٔ بک‌آف را صفر می‌کند — تا وقتی providerِ واقعاً سالم نشده،
            # چرخهٔ بعدیِ OPEN از همان سطحِ بک‌آفِ فعلی ادامه می‌دهد، نه از صفر.
            t["consecutive_opens"] = 0
            just_closed = True
    _save_state(state)
    if just_closed:
        # ۲۰۲۶-۰۸-۰۹: هشدارِ ریکاوری — درسِ امروز فقط «چرا trip نکرد» نبود؛
        # صداکننده هم هرگز نمی‌فهمید کِی برگشته بود. dedup ِ خودِ opslib.alert
        # این را از هشدارِ OPEن مشابه جدا نگه می‌دارد (متنِ متفاوت = امضایِ متفاوت).
        try:
            opslib.alert([f"circuit RECOVERED for {target} — closed after "
                          f"{cfg['success_to_close']} consecutive successes"])
        except Exception:  # noqa: BLE001
            pass
    return {"state": t["state"], "target": target}


def record_failure(target: str, reason: str = "") -> dict:
    """ثبت شکست. اگر threshold رد شد یا پنجرهٔ نرخ‌محور مسموم بود → OPEN."""
    cfg = _cfg()
    state = _load_state()
    t = _target_entry(state, target)
    t["last_fail_ts"] = opslib.now_iso()
    t["fail_count"] = t.get("fail_count", 0) + 1
    _record_outcome(t, False, cfg["window_size"])

    st = State(t["state"])
    trip_reason = ""
    if st is State.HALF_OPEN:
        t["half_open_attempts"] = t.get("half_open_attempts", 0) + 1
        # شکست در half_open → فوراً باز
        t["state"] = State.OPEN.value
        t["opened_at_ts"] = __import__("time").time()
        trip_reason = "half-open probe failed"
    elif t["fail_count"] >= cfg["failure_threshold"]:
        t["state"] = State.OPEN.value
        t["opened_at_ts"] = __import__("time").time()
        trip_reason = f"consecutive>={cfg['failure_threshold']}"
    elif st is State.CLOSED and _window_says_open(t, cfg):
        # ۲۰۲۶-۰۸-۰۹ (VQ-FUGU-002): providerِ پوسته‌پوسته — هرگز به threshold ِ
        # پیاپی نمی‌رسد چون هر موفقیتِ پراکنده fail_count را صفر می‌کند، ولی
        # نرخِ واقعی همچنان بد است. این تنها راهِ trip بدونِ پیاپی‌بودن است.
        hist = t.get("recent_outcomes") or []
        n_fail = sum(1 for ok in hist if not ok)
        t["state"] = State.OPEN.value
        t["opened_at_ts"] = __import__("time").time()
        trip_reason = f"error-rate {n_fail}/{len(hist)} >= {cfg['window_fail_rate']:.0%}"

    just_opened = t["state"] == State.OPEN.value and st is not State.OPEN
    if just_opened:
        t["consecutive_opens"] = int(t.get("consecutive_opens", 0) or 0) + 1

    _save_state(state)

    if just_opened:
        # ۲۰۲۶-۰۸-۰۹: fail_countِ خامِ همیشه‌رونده حذف شد — با هر شکست عدد فرق
        # می‌کرد، پس امضایِ dedup ِ opslib.alert هرگز یکی نمی‌شد و ۲۲ ساعت
        # می‌توانست ۲۲ خطِ «یکتا»ی جدا بنویسد. consecutive_opens فقط یک‌بار در
        # هر چرخهٔ OPEN عوض می‌شود، پس شکست‌های پیاپیِ همان چرخه واقعاً دیجوپ
        # می‌شوند؛ فقط ورودِ چرخهٔ **بعدی** (بک‌آفِ بلندتر) خطِ نو می‌سازد —
        # همان چیزی که مالک خواست: نه سکوت، نه اسپم.
        cooldown = _effective_cooldown(t, cfg)
        opslib.alert([f"circuit OPEN for {target} — {trip_reason} "
                      f"(backoff level {t['consecutive_opens']}, next retry in "
                      f"~{int(cooldown)}s) {reason}".strip()])

    return {"state": t["state"], "target": target, "fail_count": t["fail_count"]}


def status(target: str | None = None) -> dict:
    """snapshot وضعیت circuit breaker(ها)."""
    state = _load_state()
    cfg = _cfg()
    targets = state.get("targets", {})
    if target:
        t = targets.get(target, {})
        return {"target": target, **t, "config": cfg}
    return {"targets": targets, "config": cfg, "ts": opslib.now_iso()}


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        print(json.dumps(status(sys.argv[1]), ensure_ascii=False, indent=2))
    else:
        print(json.dumps(status(), ensure_ascii=False, indent=2))
