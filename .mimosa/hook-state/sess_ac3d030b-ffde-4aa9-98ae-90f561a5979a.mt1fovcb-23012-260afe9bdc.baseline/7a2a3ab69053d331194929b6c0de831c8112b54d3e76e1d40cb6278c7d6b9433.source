#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_circuit_breaker_backoff_window.py — VQ-FUGU-002 (رأیِ مالک، ۲۰۲۶-۰۸-۰۹).

شاهدِ زنده‌ای که این را لازم کرد: Fugu از ۲۰۲۶-۰۸-۰۸ ۱۸:۰۹ تا ۲۰۲۶-۰۸-۰۹ ~۱۷:۰۰
(۲۲+ ساعت) پیوسته شکست خورد. circuit_breaker از قبل per-target/half-open داشت
(test_cortex_circuit_breaker.py ثابتش می‌کند)، ولی cooldown ثابتِ ۶۰s یعنی هر
۶۰-۹۰ ثانیه یک probeِ واقعی — هر probe یک attemptِ روزانهٔ fugu_quota را سوزاند.

سه ادعای نو:
  ۱) بک‌آفِ تصاعدی: هر چرخهٔ OPEنِ پیاپی (بدونِ closeِ واقعیِ میانی) cooldown را
     دوبرابر می‌کند، سقف‌دار؛ فقط closeِ واقعی صفرش می‌کند.
  ۲) پنجرهٔ نرخ‌محور: providerِ پوسته‌پوسته (که هرگز به threshold ِ پیاپی
     نمی‌رسد چون موفقیت‌های پراکنده fail_count را صفر می‌کنند) با نرخِ بدِ
     پنجره trip می‌شود.
  ۳) alert: فقط روی گذارِ واقعیِ closed/half-open→open (نه هر شکست) و روی
     closeِ واقعی (ریکاوری) — نه سکوتِ ۲۲ساعته، نه اسپمِ هر-دقیقه.
"""
import sys
import time as _t
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("cb-backoff-window")
OPS = Path(__file__).resolve().parent.parent
for _p in (OPS / "budget", OPS / "cortex"):
    sys.path.insert(0, str(_p))

import opslib  # noqa: E402,F401
import circuit_breaker as cb  # noqa: E402

_CB_STATE = opslib.STATE_DIR / "circuit-state.json"
cb.STATE_PATH = _CB_STATE
# thresholds پیش‌فرضِ کد (harness بخشِ resilience ندارد): failure_threshold=5،
# cooldown_seconds=60، max_cooldown_seconds=3600، window_size=20،
# window_min_samples=10، window_fail_rate=0.7.


def _fresh_cb():
    if _CB_STATE.exists():
        _CB_STATE.unlink()


def _force_open_via_threshold(target: str, n: int = 5) -> None:
    for i in range(n):
        cb.check(target)
        cb.record_failure(target, f"fail #{i+1}")


def _age_open(target: str, seconds_ago: float) -> None:
    """opened_at_ts را به گذشته می‌برد — شبیه‌سازیِ گذشتِ cooldown بدونِ sleep."""
    st = cb._load_state()
    st["targets"][target]["opened_at_ts"] = _t.time() - seconds_ago
    cb._save_state(st)


# ═══ ۱) بک‌آفِ تصاعدی ═══════════════════════════════════════════════════════

def t1_second_open_cycle_needs_longer_cooldown():
    _fresh_cb()
    target = "orchestr"
    _force_open_via_threshold(target)  # چرخهٔ اول → OPEN، consecutive_opens=1
    assert cb.status(target).get("consecutive_opens") == 1

    _age_open(target, 65)  # از cooldown پایهٔ ۶۰s رد شده
    r = cb.check(target)
    assert r.get("allow") is True, "چرخهٔ اول: ۶۵s کافی برایِ half-open پایه‌ای بود"
    cb.record_failure(target, "half-open probe #1 failed")  # فوراً OPEN، consecutive_opens=2
    assert cb.status(target).get("consecutive_opens") == 2

    _age_open(target, 65)  # همان ۶۵s قدیمی — این‌بار باید کافی نباشد (بک‌آف=۱۲۰s)
    r2 = cb.check(target)
    assert r2.get("allow") is False, (
        f"چرخهٔ دوم: بک‌آف باید دستِ‌کم ۱۲۰s باشد، ۶۵s کافی نیست ولی allow شد ({r2})")

    _age_open(target, 125)  # حالا از cooldownِ دوبرابرشده (۱۲۰s) رد شده
    r3 = cb.check(target)
    assert r3.get("allow") is True, f"با ۱۲۵s (>۱۲۰s بک‌آفِ چرخهٔ دوم) باید allow شود ({r3})"


def t2_backoff_capped_at_max():
    _fresh_cb()
    target = "orchestr"
    _force_open_via_threshold(target)
    # ۱۰ چرخهٔ نیمه‌باز-شکست پیاپی → 2^10×60=61440s، باید به سقفِ ۳۶۰۰s ببرد
    for _ in range(10):
        st = cb._load_state()
        # عمداً نه ۰.۰ — falsy است، `if opened is not None` رد می‌شود ولی برایِ
        # خوانایی همان تلهٔ واقعی که در کدِ اصلی فیکس شد این‌جا هم دور زده شود.
        st["targets"][target]["opened_at_ts"] = 1.0  # کاملاً قدیمی، ولی truthy
        cb._save_state(st)
        cb.check(target)
        cb.record_failure(target, "half-open probe failed")
    cooldown = cb._effective_cooldown(cb.status(target), cb._cfg())
    assert cooldown == cb._cfg()["max_cooldown_seconds"], (
        f"بعدِ ۱۰+ چرخه، cooldown باید به سقف برسد (got {cooldown})")


def t3_real_close_resets_backoff_level():
    _fresh_cb()
    target = "orchestr"
    _force_open_via_threshold(target)
    _age_open(target, 65)
    cb.check(target)  # گذارِ واقعیِ OPEN→HALF_OPEN — بدونِ این، state هنوز open می‌ماند
    cb.record_failure(target, "half-open probe failed")  # consecutive_opens=2
    assert cb.status(target).get("consecutive_opens") == 2

    # حالا واقعاً ریکاوری کن: نیمه‌باز → دو موفقیت → closed
    _age_open(target, cb._cfg()["max_cooldown_seconds"] + 5)  # هر عددی برای رسیدنِ half-open کافی است
    cb.check(target)
    cb.record_success(target)
    cb.record_success(target)
    assert cb.status(target).get("state") == "closed"
    assert cb.status(target).get("consecutive_opens") == 0, "closeِ واقعی باید بک‌آف را صفر کند"

    # چرخهٔ بعدی باید دوباره از cooldownِ پایه (نه بک‌آفِ قدیمی) شروع شود
    _force_open_via_threshold(target)
    assert cb.status(target).get("consecutive_opens") == 1, "بعدِ closeِ واقعی، چرخهٔ نو از ۱ شروع می‌شود"


# ═══ ۲) پنجرهٔ نرخ‌محور ══════════════════════════════════════════════════════

def t4_flaky_provider_trips_via_window_not_consecutive():
    """۱ موفقیت از هر ۵ — fail_count پیاپی هرگز از ۴ رد نمی‌شود (threshold=5)،
    ولی نرخِ واقعی (~۸۰٪ شکست) باید بعدِ حداقلِ نمونه trip کند."""
    _fresh_cb()
    target = "glm"
    for i in range(20):
        cb.check(target)
        if i % 5 == 4:
            cb.record_success(target)
        else:
            cb.record_failure(target, f"flaky #{i+1}")
        st = cb.status(target)
        if st.get("state") == "open":
            break
    assert cb.status(target).get("state") == "open", (
        "providerِ پوسته‌پوسته (نرخِ بد) باید نهایتاً از مسیرِ پنجره trip کند")
    assert cb.status(target).get("fail_count") < 5, (
        "trip باید از مسیرِ پنجره بیاید، نه پیاپیِ خام (fail_count هرگز به ۵ نرسید)")


def t5_window_needs_minimum_samples_before_tripping():
    _fresh_cb()
    target = "glm"
    # ۳ شکست، ۱ موفقیت، ۳ شکست — کمتر از window_min_samples=10، نباید trip کند
    for ok in (False, False, False, True, False, False, False):
        cb.check(target)
        if ok:
            cb.record_success(target)
        else:
            cb.record_failure(target, "early")
    assert cb.status(target).get("state") == "closed", (
        "با کمتر از window_min_samples، پنجره نباید trip کند")


# ═══ ۳) alertها: فقط روی گذار، نه هر شکست/موفقیت ══════════════════════════════

def t6_repeated_failures_in_same_open_cycle_alert_once():
    _fresh_cb()
    calls = []
    _orig = opslib.alert
    opslib.alert = lambda items: calls.append(list(items))
    try:
        target = "orchestr"
        _force_open_via_threshold(target)  # ← باید دقیقاً یک alert (گذار closed→open)
        n_after_open = len(calls)
        assert n_after_open == 1, f"فقط یک alert روی گذارِ اول (got {n_after_open})"
        # حالا در همان چرخهٔ OPEN، چندبار دیگر هم fail را صدا بزن (بدونِ گذارِ state)
        cb.record_failure(target, "already open, still failing")
        cb.record_failure(target, "already open, still failing")
        assert len(calls) == n_after_open, (
            f"شکست‌هایِ داخلِ همان چرخهٔ OPEN نباید alertِ نو بسازند (got {len(calls)})")
    finally:
        opslib.alert = _orig


def t7_recovery_alert_fires_on_real_close():
    _fresh_cb()
    calls = []
    _orig = opslib.alert
    opslib.alert = lambda items: calls.append(list(items))
    try:
        target = "orchestr"
        _force_open_via_threshold(target)
        _age_open(target, 65)
        cb.check(target)
        cb.record_success(target)
        cb.record_success(target)  # success_to_close=2 → closed
        recovered = [c for c in calls if any("RECOVERED" in ln for ln in c)]
        assert recovered, f"باید یک alertِ RECOVERED بعدِ closeِ واقعی باشد ({calls})"
    finally:
        opslib.alert = _orig


if __name__ == "__main__":
    failed = harness.run([
        ("۱ چرخهٔ دومِ OPEN نیازِ cooldownِ بلندتر دارد", t1_second_open_cycle_needs_longer_cooldown),
        ("۲ بک‌آف سقف‌دار است", t2_backoff_capped_at_max),
        ("۳ closeِ واقعی بک‌آف را صفر می‌کند", t3_real_close_resets_backoff_level),
        ("۴ providerِ پوسته‌پوسته از مسیرِ پنجره trip می‌کند", t4_flaky_provider_trips_via_window_not_consecutive),
        ("۵ پنجره حداقلِ نمونه لازم دارد", t5_window_needs_minimum_samples_before_tripping),
        ("۶ شکست‌هایِ همان چرخه یک‌بار alert می‌شوند", t6_repeated_failures_in_same_open_cycle_alert_once),
        ("۷ alertِ ریکاوری روی closeِ واقعی", t7_recovery_alert_fires_on_real_close),
    ])
    sys.exit(1 if failed else 0)
