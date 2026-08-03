#!/usr/bin/env python3
"""test_token_meter.py — متر توکن روی پنجرهٔ غلتان (رأیِ مالک ۰۸-۰۴).

چرا این ماژول ساخته شد (ممیزیِ ۰۸-۰۳): هیچ متری در ریپو توکن را به‌عنوانِ بودجه
نمی‌شمرد. `fugu_quota` درخواست می‌شمارد؛ `subscription=max` باعث می‌شود
`est_worst_case`/`complete` صفر بدهند پس `organ_gate`/`budget_gate` صفر جمع
می‌زنند؛ و تنها منبعِ توکنِ واقعی (`paid-calls.jsonl`) صفر خوانندهٔ تجمیعی داشت.

سنجه‌های این فایل عمداً روی سه چیز تمرکز دارند که در این ریپو بارها شکسته‌اند:
  · **پنجرهٔ غلتان** (نه تقویمی) — سهمیهٔ فروشنده غلتان است.
  · **ساعتِ محلی در برابر UTC** — `opslib.now_iso()` محلیِ بی‌منطقه می‌نویسد؛
    خواندنش به‌عنوانِ UTC همان باگی است که یک‌بار ده ساعت از هر روز را کور کرد.
  · **«نمی‌دانم» ≠ «صفر»** — ذخیرهٔ غایب نباید شبیهِ مصرفِ صفر رندر شود.
"""
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import harness  # noqa: E402

ENV = harness.setup("token-meter")
_OPS = harness.SELF_OPS
if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))

import token_meter as tm  # noqa: E402

NOW = datetime(2026, 8, 4, 12, 0, 0, tzinfo=timezone.utc)


def _write(rows, name="paid-calls.jsonl"):
    d = Path(ENV["ops"]) / "state"
    d.mkdir(parents=True, exist_ok=True)
    p = d / name
    p.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n",
                 encoding="utf-8")
    return str(d)


def _row(hours_ago, ti=1000, to=200, ok=True, task=None):
    ts = (NOW - timedelta(hours=hours_ago)).isoformat()
    r = {"ts": ts, "tier": "primary", "role": "orchestr", "ok": ok,
         "tokens_in": ti, "tokens_out": to}
    if task is not None:
        r["task"] = task
    return r


def t_a_a_missing_store_is_unknown_not_zero():
    """تفکیکِ حیاتی: ذخیرهٔ غایب «نمی‌دانم» است، نه «مصرفِ صفر»."""
    sd = str(Path(ENV["ops"]) / "state" / "nonexistent-dir")
    w = tm.read_window(now=NOW, state_dir=sd)
    assert w["readable"] is False, w
    assert w["calls"] == 0
    s = tm.status(now=NOW, state_dir=sd)
    assert s["readable"] is False, "متر نباید صفرِ تمیز نشان دهد"


def t_b_the_window_really_rolls_it_is_not_calendar():
    """قلبِ رفع: سهمیهٔ فروشنده غلتان است. ردیفِ خارج از پنجره نباید شمرده شود."""
    sd = _write([_row(1), _row(2), _row(200)])     # ۲۰۰ ساعت پیش = بیرون از ۱۶۸
    w = tm.read_window(window_h=168, now=NOW, state_dir=sd)
    assert w["calls"] == 2, ("پنجره غلتان نیست", w["calls"])
    w2 = tm.read_window(window_h=300, now=NOW, state_dir=sd)
    assert w2["calls"] == 3, w2["calls"]


def t_c_a_naive_timestamp_is_read_as_local_not_utc():
    """`opslib.now_iso()` محلیِ بی‌منطقه می‌نویسد. اگر خواننده UTC فرضش کند،
    ردیف‌ها به‌اندازهٔ اختلافِ منطقه جابه‌جا می‌شوند — همان باگِ ده‌ساعته."""
    local_now = NOW.astimezone()
    naive = local_now.replace(tzinfo=None).isoformat()
    parsed = tm._parse_ts(naive)
    assert parsed is not None
    assert abs((parsed - NOW).total_seconds()) < 90, (
        "مهرِ بی‌منطقه محلی خوانده نشد", parsed, NOW)


def t_d_failed_calls_burn_no_tokens():
    sd = _write([_row(1, ok=True), _row(1, ok=False, ti=9999, to=9999)])
    w = tm.read_window(now=NOW, state_dir=sd)
    assert w["failed"] == 1 and w["calls"] == 2, w
    assert w["visible_total"] == 1200, ("شکست نباید توکن بسوزاند", w)


def t_e_the_multiplier_is_applied_but_the_raw_number_survives():
    """اگر ضریب غلط بود، عددِ خام باید دست‌نخورده بماند."""
    sd = _write([_row(1, ti=1000, to=0)])
    prev = os.environ.get(tm.MULTIPLIER_ENV)
    os.environ[tm.MULTIPLIER_ENV] = "2.6"
    try:
        s = tm.status(now=NOW, state_dir=sd)
        assert s["visible_tokens"] == 1000, s
        assert s["effective_tokens"] == 2600, s
        assert s["multiplier_verified"] is False, "ضریب تخمین است، نه مشاهده"
    finally:
        if prev is None:
            os.environ.pop(tm.MULTIPLIER_ENV, None)
        else:
            os.environ[tm.MULTIPLIER_ENV] = prev


def t_f_the_budget_is_a_percentage_so_a_capacity_fix_self_corrects():
    """رأیِ مالک: «۴۰٪ روی ظرفیتِ *واقعی* اعمال می‌شود نه عددِ تخمینی».
    پس نصف‌کردنِ تخمینِ ظرفیت باید بودجه را هم نصف کند — بدونِ هیچ ویرایشِ دیگری."""
    sd = _write([_row(1)])
    prev_cap = os.environ.get(tm.CAPACITY_ENV)
    prev_share = os.environ.get(tm.SHARE_ENV)
    os.environ[tm.SHARE_ENV] = "40"
    try:
        os.environ[tm.CAPACITY_ENV] = "100000000"
        big = tm.status(now=NOW, state_dir=sd)["budget_tokens"]
        os.environ[tm.CAPACITY_ENV] = "50000000"
        small = tm.status(now=NOW, state_dir=sd)["budget_tokens"]
        assert big == 40_000_000 and small == 20_000_000, (big, small)
    finally:
        for k, v in ((tm.CAPACITY_ENV, prev_cap), (tm.SHARE_ENV, prev_share)):
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def t_g_capacity_is_never_claimed_as_verified():
    """ظرفیتِ واقعی بدونِ خوردن به سقف قابلِ مشاهده نیست — متر نباید ادعایش کند."""
    sd = _write([_row(1)])
    s = tm.status(now=NOW, state_dir=sd)
    assert s["capacity_verified"] is False
    assert "تخمین" in s["note"]


def t_h_legs_are_split_by_task_and_unattributed_is_visible():
    """تخصیصِ سه‌گانه فقط با فیلدِ `task` ممکن است. ردیفِ بی‌آن باید **دیده** شود،
    نه اینکه بی‌صدا در یک پا جمع شود."""
    sd = _write([_row(1, task="ziman"), _row(1, task="lead"),
                 _row(1, task="research"), _row(1)])      # آخری بی‌task
    w = tm.read_window(now=NOW, state_dir=sd)
    assert w["by_leg"]["ziman"]["calls"] == 1, w["by_leg"]
    assert w["by_leg"]["lead"]["calls"] == 1, w["by_leg"]
    assert w["by_leg"]["studio"]["calls"] == 1, w["by_leg"]   # research→studio
    assert w["unattributed_calls"] == 1, w
    s = tm.status(now=NOW, state_dir=sd)
    assert s["attribution_complete"] is False


def t_i_a_torn_line_does_not_kill_the_meter():
    sd = _write([_row(1)])
    p = Path(sd) / "paid-calls.jsonl"
    p.write_text(p.read_text("utf-8") + '{"ts": "broken\n', encoding="utf-8")
    w = tm.read_window(now=NOW, state_dir=sd)
    assert w["readable"] is True and w["calls"] == 1, w


def t_j_the_module_writes_nothing():
    src = Path(tm.__file__).read_text("utf-8")
    for bad in ("write_text", "write_bytes", "append_jsonl", "os.replace"):
        assert bad not in src, f"مسیرِ نوشتن در مترِ فقط‌خواندنی: {bad}"


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("t_") and callable(v)]
    passed, failed = 0, []
    for t in tests:
        try:
            t()
            passed += 1
            print(f"  OK  {t.__name__}")
        except Exception as e:  # noqa: BLE001
            failed.append(t.__name__)
            print(f"  FAIL {t.__name__}: {e!r}")
    print(f"\ntest_token_meter: {passed}/{len(tests)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
