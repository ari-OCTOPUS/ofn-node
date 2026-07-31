#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_paid_timeout_chain.py — زنجیرهٔ مرگِ مغزِ پولی، هر سه حلقه قفل.

یافتهٔ ۲۵ جولای از `state/paid-calls.jsonl` (۳۰ فراخوان، ۱۵ شکست، **تنها نوعِ خطا
`TimeoutError`** — صفر ۴۰۱، صفر ۵xx):

    max_tokens=1200 در گاورنر  →  ≥۳۴s لازم  →  سقفِ سوکتِ سراسریِ ۲۰s  →  timeoutِ محلی
      →  fugu_quota آن را «شکستِ فروشنده» می‌شمارد  →  FUGU_FAIL_CEILING  →  STOP-FUGU
        →  مغزِ ۲۰۰ دلاری خاموش تا دستِ انسان

سه حلقه، سه فیکس، و این تست هر سه را در **هر دو** حالتِ فلگ قفل می‌کند:
  T1–T4  سقفِ سوکت از اندازهٔ درخواست مشتق می‌شود و به بودجهٔ askِ بیرونی کران دارد
  T5–T7  timeoutِ محلی از شکستِ فروشنده تفکیک می‌شود (و kill-switch را نمی‌شلیکد)
  T8     درخواستِ گاورنر در سقفِ مشتق‌شده جا می‌شود — با حاشیهٔ عددی

hermetic: هیچ شبکه، هیچ کلید، هیچ فایلِ زندهٔ state. `fugu_quota` به tmp نشانه می‌رود.
"""
from __future__ import annotations

import importlib
import json
import os
import socket
import sys
import tempfile
import urllib.error
from pathlib import Path

_HERE = Path(__file__).resolve().parent

# ⚠️ این فایل در سربرگش می‌گوید «هیچ فایلِ زندهٔ state» — ولی تا ۲۰۲۶-۰۷-۲۷
# `OPS_DIR`/`ORG_ROOT` را ست نمی‌کرد، پس `opslib.STATE_DIR` به درختِ **زنده**
# اشاره می‌کرد. تنها دلیلی که کسی نفهمید این بود که هیچ مسیرِ زیرِ آزمون تا آن
# روز چیزی در state نمی‌نوشت؛ لحظه‌ای که یکی نوشت، ۹۸ ردیفِ آزمایشی در stateِ
# واقعی نشست.
#
# ادعای hermetic بودن باید **اجرا** شود، نه فقط نوشته — و قبل از هر importی که
# مسیر را می‌خواند.
_ISO = Path(tempfile.mkdtemp(prefix="paid-timeout-"))
os.environ["ORG_ROOT"] = str(_ISO)
os.environ["OPS_DIR"] = str(_ISO / "_ops")
(_ISO / "_ops" / "state").mkdir(parents=True, exist_ok=True)

for _p in (str(_HERE.parent / "debate"), str(_HERE.parent / "budget"),
           str(_HERE.parent / "cortex"), str(_HERE.parent)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

FAILURES: list[str] = []
CHECKS = 0

# نرخِ مشاهده‌شدهٔ زنده — مرجعِ عددیِ همهٔ ادعاهای این فایل
OBS_A_MS, OBS_B_MS = 3811.0, 25.2      # ms ≈ A + B×out_tokens


def ck(cond, msg):
    global CHECKS
    CHECKS += 1
    if not cond:
        FAILURES.append(msg)


def need_s(max_tokens: int) -> float:
    return (OBS_A_MS + OBS_B_MS * max_tokens) / 1000.0


def _env(**kw):
    """env را ست/پاک می‌کند و مقادیرِ قبلی را برمی‌گرداند."""
    old = {}
    for k, v in kw.items():
        old[k] = os.environ.get(k)
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = str(v)
    return old


def _restore(old):
    for k, v in old.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v


# ── T1 · سازگاریِ عقب‌رو: بی max_tokens، رفتارِ قبلی بایت‌به‌بایت ─────────────
def t1_backward_compatible():
    import client
    old = _env(PAID_HTTP_TIMEOUT_S=None, PAID_ASK_BUDGET_S=None)
    try:
        ck(client._http_timeout() == 45.0, "T1: پیش‌فرضِ بی‌آرگومان باید ۴۵ باشد")
        _env(PAID_HTTP_TIMEOUT_S=20)
        ck(client._http_timeout() == 20.0, "T1: سقفِ صریحِ ۲۰ باید محترم باشد")
        _env(PAID_HTTP_TIMEOUT_S=999)          # بیرونِ بازه → پیش‌فرض
        ck(client._http_timeout() == 45.0, "T1: مقدارِ بیرونِ بازه باید به ۴۵ برگردد")
        _env(PAID_HTTP_TIMEOUT_S="نامعتبر")
        ck(client._http_timeout() == 45.0, "T1: مقدارِ غیرعددی باید به ۴۵ برگردد")
    finally:
        _restore(old)


# ── T2 · سقف از اندازهٔ درخواست مشتق می‌شود ───────────────────────────────────
def t2_derived_from_request():
    import client
    old = _env(PAID_HTTP_TIMEOUT_S=20, PAID_ASK_BUDGET_S=90)
    try:
        # همان فراخوانِ ناممکنِ تاریخی: ۱۲۰۰ توکن زیرِ سقفِ ۲۰ ثانیه
        t = client._http_timeout("orchestr", 1200)
        ck(t > need_s(1200),
           f"T2: ۱۲۰۰ توکن ({need_s(1200):.1f}s لازم) باید سقفِ بزرگ‌تر بگیرد، گرفت {t:.1f}s")
        ck(t > 20.0, f"T2: سقفِ مشتق‌شده باید از ۲۰ِ صریح بیشتر شود، شد {t:.1f}s")
        # و درخواستِ کوچک هرگز سقف را **پایین** نمی‌آورد
        ck(client._http_timeout("glm", 50) >= 20.0,
           "T2: درخواستِ کوچک نباید سقف را از مقدارِ صریح پایین‌تر ببرد")
        # یکنوایی: درخواستِ بزرگ‌تر ⇒ سقفِ ≥
        seq = [client._http_timeout("orchestr", m) for m in (100, 400, 800, 1600)]
        ck(all(seq[i] <= seq[i + 1] for i in range(len(seq) - 1)),
           f"T2: سقف باید یکنوا صعودی باشد، شد {seq}")
    finally:
        _restore(old)


# ── T3 · کرانِ بالا: سقفِ درونی هرگز بودجهٔ askِ بیرونی را نمی‌خورد ────────────
def t3_bounded_by_ask_budget():
    import client
    old = _env(PAID_HTTP_TIMEOUT_S=45, PAID_ASK_BUDGET_S=90)
    try:
        for mt in (2048, 4096, 100000):
            t = client._http_timeout("orchestr", mt)
            ck(t <= 90 * 0.6 + 1e-9,
               f"T3: max_tokens={mt} سقف {t:.1f}s گرفت — بیشتر از ۶۰٪ بودجهٔ ask")
            ck(t < 90.0, f"T3: سقفِ درونی ({t:.1f}s) باید کمتر از ۹۰ِ بیرونی باشد")
        # بودجهٔ ask کوچک‌تر ⇒ کرانِ کوچک‌تر
        _env(PAID_ASK_BUDGET_S=30)
        ck(client._http_timeout("orchestr", 4096) <= 30 * 0.6 + 1e-9,
           "T3: با ASK_BUDGET=30 کران باید ۱۸ شود")
        # همیشه در بازهٔ مطلق
        for mt in (0, 1, 100000):
            t = client._http_timeout("orchestr", mt)
            ck(1.0 <= t <= 300.0, f"T3: سقف {t} بیرونِ بازهٔ [1,300]")
    finally:
        _restore(old)


# ── T4 · سقفِ per-role صریح ──────────────────────────────────────────────────
def t4_per_role_override():
    import client
    old = _env(PAID_HTTP_TIMEOUT_S=20, PAID_ASK_BUDGET_S=90,
               PAID_HTTP_TIMEOUT_S_ORCHESTR=None, PAID_HTTP_TIMEOUT_S_GLM=None)
    try:
        _env(PAID_HTTP_TIMEOUT_S_ORCHESTR=50)
        ck(client._http_timeout("orchestr") == 50.0,
           "T4: overrideِ per-role اعمال نشد")
        ck(client._http_timeout("glm") == 20.0,
           "T4: roleِ دیگر نباید از overrideِ orchestr اثر بگیرد")
        ck(client._http_timeout("ORCHESTR") == 50.0, "T4: نام باید case-insensitive باشد")
        ck(client._http_timeout(None) == 20.0, "T4: role=None باید سراسری بگیرد")
        _env(PAID_HTTP_TIMEOUT_S_ORCHESTR=9999)     # بیرونِ بازه → نادیده
        ck(client._http_timeout("orchestr") == 20.0,
           "T4: overrideِ بیرونِ بازه باید نادیده گرفته شود")
    finally:
        _restore(old)


# ── T5 · طبقه‌بندی: timeoutِ محلی در برابر پاسخِ فروشنده ─────────────────────
def t5_timeout_classification():
    import fugu_quota as fq
    local = [TimeoutError("timed out"), socket.timeout("timed out"),
             urllib.error.URLError(TimeoutError("timed out")),
             urllib.error.URLError("connection timed out")]
    for e in local:
        ck(fq.is_local_timeout(e) is True,
           f"T5: {type(e).__name__} باید timeoutِ محلی شناخته شود")
    provider = [urllib.error.HTTPError("u", 401, "Unauthorized", {}, None),
                urllib.error.HTTPError("u", 500, "Server Error", {}, None),
                ValueError("bad json"), OSError("connection refused"),
                RuntimeError("PriceNotLocked"), None]
    for e in provider:
        ck(fq.is_local_timeout(e) is False,
           f"T5: {type(e).__name__ if e else 'None'} نباید timeoutِ محلی شناخته شود")


# ── T6/T7 · معافیت از kill-switch، فقط با فلگ ───────────────────────────────
def _fq_isolated():
    """fugu_quota با stateِ موقت — فایلِ زنده هرگز لمس نمی‌شود."""
    d = Path(tempfile.mkdtemp(prefix="fq-"))
    import fugu_quota as fq
    fq = importlib.reload(fq)
    fq._state_path = lambda: d / "fugu-quota.json"        # type: ignore[assignment]
    stops: list[str] = []
    fq._write_stop = lambda why: stops.append(why)         # type: ignore[assignment]
    return fq, stops, d


def _state(fq):
    try:
        return json.loads(fq._state_path().read_text("utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def t6_flag_off_preserves_kill():
    old = _env(OCTOPUS_FUGU_TIMEOUT_NOT_PROVIDER_FAIL=None, FUGU_FAIL_CEILING=3)
    try:
        fq, stops, _ = _fq_isolated()
        for _ in range(3):
            fq.fail("primary", error=TimeoutError("timed out"))
        ck(len(stops) == 1, f"T6: با فلگِ خاموش باید در سقف STOP بنویسد، نوشت {len(stops)}")
        st = _state(fq)
        ck(st.get("consecutive_failures") == 3,
           f"T6: شمارندهٔ شکست باید ۳ باشد، شد {st.get('consecutive_failures')}")
        # طبقه‌بندی حتی با فلگِ خاموش ثبت می‌شود (دیدنی‌شدن)
        ck(st.get("consecutive_timeouts") == 3,
           f"T6: consecutive_timeouts باید ۳ ثبت شود، شد {st.get('consecutive_timeouts')}")
        ck(st.get("last_error_was_local_timeout") is True,
           "T6: طبقهٔ آخرین خطا ثبت نشد")
        # و بدونِ error، رفتارِ قدیمیِ کامل
        fq2, stops2, _ = _fq_isolated()
        for _ in range(3):
            fq2.fail("primary")
        ck(len(stops2) == 1, "T6: فراخوانِ بی‌error باید رفتارِ قبلی را داشته باشد")
        ck(_state(fq2).get("consecutive_timeouts", 0) == 0,
           "T6: خطای نامعلوم نباید timeout شمرده شود")
    finally:
        _restore(old)


def t7_flag_on_exempts_timeout_only():
    old = _env(OCTOPUS_FUGU_TIMEOUT_NOT_PROVIDER_FAIL="1", FUGU_FAIL_CEILING=3)
    try:
        fq, stops, _ = _fq_isolated()
        for _ in range(10):                    # ۱۰ timeoutِ محلی
            fq.fail("primary", error=TimeoutError("timed out"))
        ck(len(stops) == 0,
           f"T7: timeoutِ محلی نباید STOP بنویسد، نوشت {len(stops)}")
        st = _state(fq)
        ck(st.get("consecutive_failures", 0) == 0,
           f"T7: شکستِ فروشنده نباید شمرده شود، شد {st.get('consecutive_failures')}")
        ck(st.get("consecutive_timeouts") == 10,
           f"T7: timeoutها باید جدا شمرده شوند، شد {st.get('consecutive_timeouts')}")
        ck(st.get("timeouts_total") == 10, "T7: مجموعِ timeout ثبت نشد")

        # ولی خطای واقعیِ فروشنده همچنان می‌کشد — معافیت فقط برای timeout است
        fq2, stops2, _ = _fq_isolated()
        for _ in range(3):
            fq2.fail("primary", error=urllib.error.HTTPError("u", 500, "x", {}, None))
        ck(len(stops2) == 1,
           f"T7: خطای ۵۰۰ فروشنده باید در سقف STOP بنویسد، نوشت {len(stops2)}")

        # مخلوط: دو timeout + یک ۵۰۰ ⇒ فقط ۵۰۰ شمرده می‌شود (زیرِ سقف)
        fq3, stops3, _ = _fq_isolated()
        fq3.fail("primary", error=TimeoutError("t"))
        fq3.fail("primary", error=TimeoutError("t"))
        fq3.fail("primary", error=urllib.error.HTTPError("u", 502, "x", {}, None))
        ck(len(stops3) == 0, "T7: یک شکستِ واقعی زیرِ سقفِ ۳ نباید STOP بزند")
        ck(_state(fq3).get("consecutive_failures") == 1,
           f"T7: باید فقط ۱ شکستِ فروشنده بشمارد، شد {_state(fq3).get('consecutive_failures')}")

        # موفقیت هر دو رشته را می‌شکند
        fq4, _s, _ = _fq_isolated()
        fq4.fail("primary", error=TimeoutError("t"))
        fq4.ok("primary")
        st4 = _state(fq4)
        ck(st4.get("consecutive_timeouts") == 0, "T7: موفقیت باید رشتهٔ timeout را بشکند")
        ck(st4.get("consecutive_failures") == 0, "T7: موفقیت باید شمارندهٔ شکست را صفر کند")
    finally:
        _restore(old)


# ── T8 · درخواستِ گاورنر با حاشیهٔ عددی در سقف جا می‌شود ────────────────────
def t8_governor_request_fits():
    import client
    import governor_epoch as ge
    # ۲۰۲۶-۰۷-۲۷ — این تست `mt == 600` را پین کرده بود. بعد اندازه‌گیریِ زنده نشان
    # داد ۶۰۰ خروجی را **می‌بُرَد** و گاورنر فقط با ۲۰۰۰ parse می‌شود. پس عددِ پین‌شده
    # کهنه شد — ولی چیزی که تست واقعاً محافظت می‌کرد کهنه نشد: «هر سقفی که گاورنر
    # انتخاب کند، ساعتِ سوکت باید با حاشیه جا بدهد.» عدد برداشته شد، ناوردی ماند —
    # حالا این گارد **مستقل از سقف** همان کلاسِ باگ را می‌گیرد.
    # `PAID_ASK_BUDGET_S` هم دیگر پین نمی‌شود چون مسیرِ واقعیِ حل، جدولِ per-role است
    # (`_ask_budget`) و ستِ صریحِ سراسری آن را دور می‌زد — یعنی تست چیزی را می‌سنجید
    # که در استقرار وجود ندارد.
    old = _env(OCTOPUS_GOVERNOR_MAX_TOKENS=None, PAID_ASK_BUDGET_S=None)
    try:
        ge = importlib.reload(ge)
        mt = ge._gov_max_tokens()
        ck(64 <= mt <= 4096, f"T8: سقفِ گاورنر خارج از بازهٔ امن: {mt}")
        # در هر دو رژیمِ سقفِ زنده جا می‌شود، با حاشیهٔ ≥۲×
        for cap in (20, 45):
            _env(PAID_HTTP_TIMEOUT_S=cap)
            t = client._http_timeout("orchestr", mt)
            ck(t > need_s(mt),
               f"T8: سقفِ زندهٔ {cap}s — لازم {need_s(mt):.1f}s ولی مجاز {t:.1f}s")
            ck(t / need_s(mt) >= 2.0,
               f"T8: حاشیه با سقفِ {cap}s فقط {t / need_s(mt):.2f}× است (<۲×)")
        # و مقدارِ تاریخیِ ۱۲۰۰ زیرِ سقفِ ۲۰ ثانیه‌ای ناممکن بود — رگرسیون‌گیر
        _env(PAID_HTTP_TIMEOUT_S=20)
        ck(need_s(1200) > 20.0,
           "T8: مرجعِ عددیِ یافته عوض شد (۱۲۰۰ توکن باید >۲۰s لازم داشته باشد)")
        # env قابلِ تنظیم، با بازهٔ امن
        _dflt = ge.GOV_MAX_TOKENS_DEFAULT
        for v, want in ((1200, 1200), (64, 64), (4096, 4096),
                        (10, _dflt), (99999, _dflt), ("x", _dflt)):
            _env(OCTOPUS_GOVERNOR_MAX_TOKENS=v)
            ge = importlib.reload(ge)
            ck(ge._gov_max_tokens() == want,
               f"T8: env={v!r} باید {want} بدهد، داد {ge._gov_max_tokens()}")
    finally:
        _restore(old)
        importlib.reload(ge)


def main() -> int:
    for fn in (t1_backward_compatible, t2_derived_from_request, t3_bounded_by_ask_budget,
               t4_per_role_override, t5_timeout_classification, t6_flag_off_preserves_kill,
               t7_flag_on_exempts_timeout_only, t8_governor_request_fits):
        try:
            fn()
        except Exception as e:  # noqa: BLE001
            FAILURES.append(f"{fn.__name__}: EXCEPTION {type(e).__name__}: {e}")
    for k in ("PAID_HTTP_TIMEOUT_S", "PAID_HTTP_TIMEOUT_S_ORCHESTR", "PAID_HTTP_TIMEOUT_S_GLM",
              "PAID_ASK_BUDGET_S", "OCTOPUS_FUGU_TIMEOUT_NOT_PROVIDER_FAIL",
              "OCTOPUS_GOVERNOR_MAX_TOKENS", "FUGU_FAIL_CEILING"):
        os.environ.pop(k, None)
    if FAILURES:
        print(f"FAIL {len(FAILURES)}/{CHECKS} — paid timeout chain")
        for f in FAILURES:
            print("  ✗", f)
        return 1
    print(f"PASS {CHECKS}/{CHECKS} — زنجیرهٔ مرگِ مغزِ پولی در هر سه حلقه قفل شد")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
