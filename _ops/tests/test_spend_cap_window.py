#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A1 (۲۰۲۶-۰۸-۰۳) — پنجرهٔ استثنای سقفِ ماهانه باید **کد** باشد و خودش منقضی شود.

پیش از این، استثنای «US$200 تا ۰۸-۰۶» فقط در `_ops/GOALS-OCTOPUS.md` نوشته شده
بود و هیچ کدی نمی‌خواندش: `budget_gate._caps()` همان min(hard=30, yaml=30) را
می‌داد و `reserve()` روی AU$30 هالت می‌کرد. یعنی پنجره اثرِ واقعی نداشت و
انقضایش هم به یادآوریِ انسان وابسته بود.

این سوییت هر دو نیمه را قفل می‌کند:
  • تابعِ خالص با تاریخِ **تزریقی** (داخلِ پنجره / روزِ آخر / روزِ بعد + fail-closed)
  • **صداکنندهٔ تولیدیِ واقعی**: `_caps()` و خودِ `reserve()` — وگرنه «مسلح ولی
    بی‌مصرف» می‌شد، همان اشتباهی که این پنجره یک هفته گرفتارش بود.

ایزوله: `BUDGET_STATE`/`BUDGETS_YAML` **قبل از import** به پوشهٔ موقت پین
می‌شوند (درسِ «هر مسیرِ تحتِ آزمون را ایزوله کن» — یک مسیرِ جاافتاده یعنی
نوشتن روی دفترِ پولِ زنده). yaml ِ غایب عمدی است: `_caps()` را روی کفِ
هاردکدِ قطعی می‌نشاند (day 2 · month 30 · disaster 500 · fx 1.5).
"""
from __future__ import annotations

import datetime
import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path

_TMP = Path(tempfile.mkdtemp(prefix="spend-cap-"))
os.environ["BUDGET_STATE"] = str(_TMP / "budget-state.json")
os.environ["BUDGETS_YAML"] = str(_TMP / "budgets.yaml")      # عمداً غایب
os.environ.pop("OCTOPUS_SPEND_CAP_USD", None)
os.environ.pop("OCTOPUS_SPEND_CAP_UNTIL", None)

ROOT = Path(__file__).resolve().parents[2]
GATE = ROOT / "04 - Architect System" / "scripts" / "budget_gate.py"
_spec = importlib.util.spec_from_file_location("_bg_under_test", GATE)
bg = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bg)

BASE, FX, DISASTER = 30.0, 1.5, 500.0


def _win(usd=None, until=None):
    for key, val in ((bg.SPEND_CAP_USD_ENV, usd), (bg.SPEND_CAP_UNTIL_ENV, until)):
        if val is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = str(val)


def _cap(today=None):
    return bg.spend_cap_now(BASE, FX, DISASTER, today=today)


def _seed(spent_month_aud):
    """دفترِ پولِ موقت با ماه/روزِ جاری تا `_roll` صفرش نکند."""
    t = datetime.date.today().isoformat()
    bg.STATE.write_text(json.dumps({
        "date": t, "spent_today_usd": 0.0, "month": t[:7],
        "spent_month_aud": float(spent_month_aud), "halted": False}), "utf-8")


# ── تابعِ خالص: سه نقطهٔ پنجره ──────────────────────────────────────────────

def t_inside_the_window_the_owner_cap_applies():
    _win(200, "2026-08-13")
    r = _cap("2026-08-07")
    assert r["window_open"] and r["value_aud"] == 300.0, r


def t_the_last_day_of_the_window_is_still_open():
    _win(200, "2026-08-13")
    r = _cap("2026-08-13")
    assert r["window_open"] and r["value_aud"] == 300.0, r


def t_the_day_after_falls_back_to_the_base():
    _win(200, "2026-08-13")
    r = _cap("2026-08-14")
    assert r["value_aud"] == BASE and r.get("expired") and not r["window_open"], r


# ── fail-closed: هر ابهامی به پایهٔ سخت‌گیر برمی‌گردد ───────────────────────

def t_without_the_env_the_base_stands():
    _win(None, None)
    r = _cap("2026-08-07")
    assert r["value_aud"] == BASE and r["reason"] == "default", r


def t_an_exception_without_an_expiry_is_refused():
    """استثنای بی‌تاریخ = قاعدهٔ نو. رأیِ مالک تاریخ داشت، پس بی‌تاریخ رد است."""
    _win(200, None)
    r = _cap("2026-08-07")
    assert r["value_aud"] == BASE and r["reason"] == "no-expiry-declared", r


def t_a_typo_in_the_amount_does_not_open_the_cap():
    _win("۲۰۰ دلار", "2026-08-13")
    r = _cap("2026-08-07")
    assert r["value_aud"] == BASE and r["reason"] == "bad-value", r


def t_a_malformed_date_does_not_open_the_cap():
    _win(200, "13-08-2026")
    r = _cap("2026-08-07")
    assert r["value_aud"] == BASE and r["reason"] == "bad-date", r


def t_a_nonpositive_amount_is_refused():
    for bad in (0, -5):
        _win(bad, "2026-08-13")
        r = _cap("2026-08-07")
        assert r["value_aud"] == BASE and r["reason"] == "bad-value", (bad, r)


# ── ناوردایی‌های مرزی ──────────────────────────────────────────────────────

def t_the_window_never_lowers_the_base():
    """پنجره فقط بالابرنده است — نباید تصادفاً سقف را سخت‌تر کند."""
    _win(1, "2026-08-13")            # 1×1.5 = AU$1.5 < AU$30
    r = _cap("2026-08-07")
    assert r["value_aud"] == BASE, r


def t_the_window_never_crosses_the_disaster_line():
    _win(10_000, "2026-08-13")       # AU$15000 → باید به ۵۰۰ کلمپ شود
    r = _cap("2026-08-07")
    assert r["value_aud"] == DISASTER, r


# ── صداکنندهٔ تولیدیِ واقعی (سنجهٔ پذیرشِ پلن) ───────────────────────────────

def t_the_production_caller_reads_it():
    _win(200, "2026-12-31")          # پنجرهٔ باز نسبت به ساعتِ واقعیِ `_caps()`
    assert bg._caps()["month_aud"] == 300.0, bg._caps()
    _win(None, None)
    assert bg._caps()["month_aud"] == BASE, bg._caps()


def t_a_closed_window_leaves_the_caps_untouched():
    """رگرسیون: خاموش‌بودن باید رفتارِ قبلی را بایت‌به‌بایت نگه دارد."""
    _win(None, None)
    c = bg._caps()
    assert (c["day_aud"], c["month_aud"], c["disaster_aud"]) == (2.0, BASE, DISASTER), c
    assert c["month_window"]["window_open"] is False, c


def t_an_open_window_is_visible_in_the_report():
    """سقفِ بالارفته هرگز پنهان نیست — وگرنه همان «متن به‌جای کد» برعکس می‌شود."""
    _win(200, "2026-12-31")
    c = bg._caps()
    assert "owner-window" in c["src"], c["src"]
    assert c["month_window"]["reason"].startswith("owner-window:"), c["month_window"]


def t_the_money_gate_actually_spends_differently():
    """قوی‌ترین شاهد: همان درخواست، یک‌بار deny و یک‌بار allow — فقط به‌خاطر پنجره.
    ‏AU$29.9 خرج‌شده + est ِ US$1 (=AU$1.5): زیرِ سقفِ روزانه، بالای سقفِ ماهانهٔ پایه."""
    _win(None, None)
    _seed(29.9)
    denied = bg.reserve("probe", 1.0)
    assert denied["allow"] is False and denied["reason"] == "monthly-halt", denied

    _win(200, "2026-12-31")
    _seed(29.9)
    allowed = bg.reserve("probe", 1.0)
    assert allowed["allow"] is True, allowed


def t_the_daily_ceiling_still_binds_inside_the_window():
    """پنجره فقط سقفِ **ماهانه** را باز می‌کند؛ AU$2 روزانه سرِ جایش می‌ماند."""
    _win(200, "2026-12-31")
    _seed(0.0)
    r = bg.reserve("probe", 5.0)     # 5×1.5 = AU$7.5 > AU$2
    assert r["allow"] is False and r["reason"] == "daily", r


def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("t_")]
    failed = 0
    for fn in tests:
        try:
            _win(None, None)
            fn()
            print(f"  ✅ {fn.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"  ❌ {fn.__name__}: {e}", file=sys.stderr)
    _win(None, None)
    ok = len(tests) - failed
    print(f"{'✅' if not failed else '❌'} test_spend_cap_window: {ok}/{len(tests)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
