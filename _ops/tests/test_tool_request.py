#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_tool_request — کانالِ «چه ابزاری ندارم» (رأیِ مالک ۲۰۲۶-۰۷-۳۰).

این کانال یکی از سه سنجهٔ خودآگاهی در آزمونِ ۷ روزه است، پس گاردش باید همان
چیزی را بسنجد که آزمون به آن تکیه می‌کند:

  ۱) **ضدِ سکوت** — درخواست حتی وقتی تحویل نمی‌شود (سهمیه/سکوت/فلگِ خاموش)
     باید در دفتر بنشیند. اگر ثبت هم گیت داشت، «نپرسید» و «پرسید ولی نرسید» یک
     سکوتِ یکسان می‌ساختند و کارتِ نمرهٔ آزمون کور می‌شد.
  ۲) **دقت ماشین‌خوان** — «درخواستِ دقیق» نباید قضاوتِ دستی باشد؛ چهار میدانِ
     need/why/cost/alternative سنجیده می‌شوند و `missing` صریح برمی‌گردد.
  ۳) **اسلات قبل از تماس** — `scan` پولِ مغز را می‌دهد، پس گیتِ سهمیه باید
     *قبل* از تماس بخورد، نه بعدش.
  ۴) **سهمیه فقط با تحویل می‌سوزد** — نسخهٔ اول با فلگِ خاموش هم `_take` می‌کرد،
     یعنی یک دورهٔ خاموشی بی‌صدا سهمیهٔ روز را خالی می‌کرد.

ساعت‌ها **صریح** اند نه offset: نسخهٔ اولِ پروب با `T14 + 40000` تصادفاً به ۰۱:۰۶
بامداد می‌افتاد و در ساعتِ سکوت قرمز می‌شد — همان «تستِ روز سبز، شب قرمز».
"""
import datetime as dt
import importlib
import inspect
import json
import sys

import harness

ENV = harness.setup("tool-request")          # env قبل از import ِ opslib — ترتیب مهم است

import opslib          # noqa: E402
import tool_request as tr  # noqa: E402

_TODAY = dt.date.today()


def _at(h, m=0):
    return dt.datetime.combine(_TODAY, dt.time(h, m)).timestamp()


def _on():
    import os
    os.environ["OCTOPUS_WIRE_TOOL_REQUEST"] = "1"


def _off():
    import os
    os.environ["OCTOPUS_WIRE_TOOL_REQUEST"] = "0"


def _fresh():
    """دفتر و سهمیه را صفر کن تا بندها به هم وابسته نباشند."""
    for p in (tr.LEDGER, tr.STATE):
        try:
            p.unlink()
        except OSError:
            pass
    _on()


_FULL = dict(need="دسترسیِ خواندنیِ API ِ PocketSmith",
             why="آشتیِ تراکنش‌ها زمین مانده و بی‌آن درآمد تأیید نمی‌شود",
             cost="۰ دلار، ~۲۰ دقیقه راه‌اندازی",
             alternative="ورودِ دستیِ CSV — کندتر و مستعدِ خطای تایپی")


# ── ایزولاسیون ──────────────────────────────────────────────────────────────
def t_state_is_isolated_from_the_live_tree():
    """اگر این بند بشکند بقیه بی‌معنی‌اند: دفتر نباید درختِ زنده باشد."""
    assert str(ENV["ops"]) in str(tr.LEDGER), tr.LEDGER
    assert r"F:\backup\_ops\state" not in str(tr.LEDGER), tr.LEDGER


# ── ۱) ضدِ سکوت ─────────────────────────────────────────────────────────────
def t_a_complete_request_is_precise_and_deliverable():
    _fresh()
    r = tr.request(**_FULL, blocking=True, cycle="c1", now=_at(14))
    assert r["precise"] is True, r["missing"]
    assert r["missing"] == []
    assert r["delivered"] is True, r["throttle_reason"]
    assert r["throttled"] is False
    assert r["emitted_ts"] is not None
    assert r["status"] == "pending"


def t_a_throttled_request_is_still_written_to_the_ledger():
    """قلبِ قاعدهٔ ضدِ سکوت. تحویل گیت دارد؛ ثبت هرگز."""
    _fresh()
    tr.request(**_FULL, now=_at(14))                       # سهمیه را می‌گیرد
    r = tr.request(need="دسترسیِ نوشتنی به تقویم",
                   why="برای زمان‌بندیِ پیگیریِ لیدها لازم است",
                   cost="۰ دلار", alternative="یادداشتِ دستی در vault",
                   now=_at(14, 1))                          # یک دقیقه بعد
    assert r["delivered"] is False
    assert r["throttled"] is True
    assert r["throttle_reason"] == "too-soon", r["throttle_reason"]
    rows = [x for x in tr._rows() if x.get("request_id") == r["request_id"]]
    assert len(rows) == 1, f"درخواستِ throttle‌شده ثبت نشد: {len(rows)} ردیف"
    assert r["request_id"] in {p["request_id"] for p in tr.pending()}, \
        "throttle‌شده از صفِ باز گم شد"


def t_quiet_hours_defer_delivery_but_never_the_record():
    _fresh()
    orig = tr._quiet_now
    tr._quiet_now = lambda now=None: True
    try:
        r = tr.request(**_FULL, now=_at(3))
    finally:
        tr._quiet_now = orig
    assert r["delivered"] is False
    assert r["throttle_reason"] == "quiet-hours"
    assert any(x.get("request_id") == r["request_id"] for x in tr._rows())


def t_a_dark_flag_records_the_request_and_does_not_burn_quota():
    """دو ادعا در یک بند، چون هر دو یک ریشه دارند: فلگِ خاموش ≠ نبودِ نیاز.

    نسخهٔ اول `_take` را قبل از دیدنِ فلگ صدا می‌زد، پس یک دورهٔ خاموشی سهمیهٔ
    روز را بی‌صدا می‌خورد و اولین درخواستِ واقعیِ بعد از روشن‌شدن `daily-cap`
    می‌گرفت."""
    _fresh()
    before = tr._load().get("used")
    _off()
    try:
        r = tr.request(**_FULL, now=_at(15, 30))
    finally:
        _on()
    assert r["delivered"] is False
    assert r["throttle_reason"] == "flag-off"
    assert any(x.get("request_id") == r["request_id"] for x in tr._rows()), \
        "با فلگِ خاموش درخواست گم شد — «نپرسید» از «کانال بسته بود» جدا نمی‌شود"
    assert tr._load().get("used") == before, "فلگِ خاموش سهمیه را سوزاند"
    assert r["precise"] is True, "دقت باید مستقل از فلگ محاسبه شود"


# ── ۲) دقتِ ماشین‌خوان ──────────────────────────────────────────────────────
def t_an_incomplete_request_names_exactly_what_is_missing():
    _fresh()
    r = tr.request(need="یه چیزی برای ایمیل", why="لازمه", now=_at(14))
    assert r["precise"] is False
    assert set(r["missing"]) == {"why", "cost", "alternative"}, r["missing"]
    assert r["delivered"] is True, "قضاوتِ ناقص‌بودن کارِ مالک است، نه سانسورِ ما"


# ── ۳) رأیِ مالک ────────────────────────────────────────────────────────────
def t_later_is_not_a_verdict():
    _fresh()
    r = tr.request(**_FULL, now=_at(14))
    out = tr.answer(r["request_id"], "later", now=_at(14, 10))
    assert out["ok"] is True and out["status"] == "pending"
    assert r["request_id"] in {p["request_id"] for p in tr.pending()}, \
        "«بعداً» درخواست را بست — همان باگِ anti-double-tap"


def t_wait_time_is_measured_and_verdicts_key_on_the_decision():
    _fresh()
    r = tr.request(**_FULL, now=_at(14))
    rid = r["request_id"]
    a = tr.answer(rid, "granted", now=_at(14, 30))
    assert a["wait_s"] == 1800.0, a["wait_s"]
    assert rid not in {p["request_id"] for p in tr.pending()}
    again = tr.answer(rid, "granted", now=_at(14, 33))
    assert again.get("idempotent") is True, "همان رأی دو بار رویدادِ نو نوشت"
    changed = tr.answer(rid, "denied", now=_at(14, 36))
    assert changed.get("idempotent") is not True and changed["status"] == "denied", \
        "مالک حق دارد نظرش را عوض کند — idempotency روی تصمیم است نه روی تپ"


def t_bad_verdicts_and_unknown_ids_are_refused():
    _fresh()
    r = tr.request(**_FULL, now=_at(14))
    assert tr.answer("deadbeef0000", "granted")["reason"] == "unknown-request"
    assert tr.answer(r["request_id"], "maybe")["reason"] == "bad-verdict"


# ── ۴) اسلات قبل از تماس ────────────────────────────────────────────────────
def _ask_ok(calls):
    def _f(*a, **k):
        calls.append(1)
        return {"ok": True, "model": "fake", "text": json.dumps(
            {"لازم_دارم": "دسترسیِ خواندنی به صندوقِ ایمیل",
             "چرا": "لیدهای ورودی از ایمیل می‌آیند و الان کورم",
             "هزینه": "۰ دلار، ~۱۰ دقیقه",
             "جایگزین": "چکِ دستیِ روزانه — کند و فراموش‌شدنی",
             "بازدارنده": True, "ارزشش_را_ندارد": False}, ensure_ascii=False)}
    return _f


def t_scan_does_not_pay_the_brain_when_the_quota_is_closed():
    """هزینه‌دار است، پس گیت باید *قبل* از تماس بخورد."""
    import os
    _fresh()
    os.environ["OCTOPUS_TOOL_REQUEST_CAP_PER_DAY"] = "1"
    try:
        tr.request(**_FULL, now=_at(14))                  # سهمیهٔ ۱ تمام شد
        calls = []
        out = tr.scan(ask_fn=_ask_ok(calls), now=_at(16), cycle="c3")
        assert out["reason"] == "daily-cap", out
        assert calls == [], f"مغز در سقف صدا زده شد — {len(calls)} تماس"
        assert any(x.get("note") == "scan-skipped" for x in tr._rows()), \
            "ردشدنِ اسکن ثبت نشد — «چیزی لازم نبود» با «نپرسیدم» یکی می‌شود"
    finally:
        os.environ.pop("OCTOPUS_TOOL_REQUEST_CAP_PER_DAY", None)


def t_scan_builds_a_precise_request_when_the_brain_names_a_need():
    _fresh()
    calls = []
    out = tr.scan(ask_fn=_ask_ok(calls), now=_at(16), cycle="c3")
    assert calls == [1], f"{len(calls)} تماس"
    assert out.get("ok") is True, out
    assert out.get("precise") is True, out.get("missing")
    assert out.get("source") == "scan"
    assert out.get("blocking") is True
    assert out.get("model") == "fake"


def t_scan_is_fail_soft_and_self_declines_without_inventing_requests():
    _fresh()
    n = lambda: len([x for x in tr._rows() if x.get("schema") == tr.SCHEMA])  # noqa: E731
    before = n()
    assert tr.scan(ask_fn=lambda *a, **k: {
        "ok": True, "text": '{"ارزشش_را_ندارد":true}'},
        now=_at(14))["reason"] == "self-declined"
    assert n() == before, "خودانصرافی یک درخواستِ الکی ساخت"

    assert tr.scan(ask_fn=lambda *a, **k: {"ok": True, "text": "من JSON نیستم"},
                   now=_at(15))["reason"] == "bad-format"

    def _boom(*a, **k):
        raise RuntimeError("مغز افتاد")
    assert tr.scan(ask_fn=_boom, now=_at(16))["reason"].startswith("ask-exception"), \
        "خطای مغز از fail-soft بیرون زد"


# ── ۵) قراردادهای سطح ──────────────────────────────────────────────────────
def t_the_card_is_zero_arg_so_the_registry_discovers_it():
    """`capability_registry` فقط `card()` ِ بی‌آرگومان را خودکار پیدا می‌کند —
    وگرنه این قابلیت ساخته می‌شود و از تلگرام نامرئی می‌ماند."""
    sig = inspect.signature(tr.card)
    assert all(p.default is not inspect.Parameter.empty or
               p.kind in (p.VAR_POSITIONAL, p.VAR_KEYWORD)
               for p in sig.parameters.values()), str(sig)
    assert isinstance(getattr(tr, "CARD_TITLE", None), str)


def t_cards_surface_throttling_and_incompleteness():
    _fresh()
    tr.request(**_FULL, now=_at(14))
    thr = tr.request(need="دسترسیِ نوشتنی به تقویم", why="برای زمان‌بندیِ پیگیری",
                     cost="۰", alternative="دستی", now=_at(14, 1))
    body, _ = tr.card()
    assert "throttle" in body, "کارت throttle‌شده را پنهان کرد"
    inc = tr.request(need="یه چیزی", why="لازمه", now=_at(17))
    assert "رد شد" in tr.card_for(inc)[0]
    assert "tr:y:" in json.dumps(tr.card_for(thr)[1])


def t_a_present_but_short_field_is_not_called_empty():
    """۲۰۲۶-۰۸-۰۶ زنده: کارت «هزینه: AU$10/ماه» را نشان می‌داد و بلافاصله زیرش
    می‌گفت «میدان‌های خالی: cost» — چون _precision زیرِ ۱۲ حرف را missing
    می‌شمارد، نه فقط رشتهٔ خالی. طراحیِ آستانه دست‌نخورده می‌ماند (کوتاه هنوز
    missing است)، ولی برچسب دیگر نباید ادعا کند مقدار نیست وقتی همان‌جا نشانش
    می‌دهد."""
    _fresh()
    r = tr.request(need="دسترسیِ Shell پایدار POSIX در sandbox پروژه",
                    why="بدون این نمی‌توانم تست‌ها را با اطمینان اجرا کنم",
                    cost="AU$10/ماه", alternative="", now=_at(14))
    assert "cost" in r["missing"], r["missing"]        # هنوز کوتاه‌تر از آستانه -- عمدی
    body, _ = tr.card_for(r)
    assert "AU$10" in body, "مقدارِ هزینه باید در کارت دیده شود"
    assert "میدان‌های خالی: " not in body, \
        "برچسبِ قدیمی می‌گفت خالی حتی وقتی مقدار در همان کارت دیده می‌شد"
    assert "کوتاه" in body, "برچسبِ نو باید علتِ واقعی (کوتاهیِ زیرِ آستانه) را بگوید"


def t_every_button_fits_the_telegram_64_byte_cap():
    """رد شدن از ۶۴ بایت = تلگرام کلِ پیام را ۴۰۰ می‌کند و کارت بی‌ردّ گم می‌شود."""
    _fresh()
    r = tr.request(**_FULL, now=_at(14))
    for row in tr.card_for(r)[1] + tr.card()[1]:
        for b in row:
            assert len(b["callback_data"].encode()) <= 64, b


def t_a_repeated_skip_reason_is_not_repeated_in_the_ledger():
    """ضدِ نویز — بدونِ گم‌کردنِ قاعدهٔ ضدِ سکوت (اندازه‌گیریِ زندهٔ ۲۰۲۶-۰۷-۳۰).

    `organism` هر تیک (~۴۳s) `scan` را صدا می‌زند و ۹۹٪ اوقات `too-soon`
    می‌گیرد؛ نسخهٔ اول برای هر کدام یک ردیف می‌نوشت ⇒ ۷ روز ≈ ۱۴٬۰۰۰ ردیفِ
    یکسان که دفترِ درخواست‌های واقعی را غرق می‌کرد. **اولین** ردِ هر دلیل
    همچنان نوشته می‌شود، فقط تکرارش نه."""
    _fresh()
    tr.request(**_FULL, now=_at(14))            # سهمیه را می‌سوزاند → too-soon
    n0 = len(tr._rows())
    tr.scan(ask_fn=lambda *a, **k: {"ok": False}, now=_at(14, 1))
    n1 = len(tr._rows())
    assert n1 == n0 + 1, "اولین ردِ 'too-soon' باید ثبت شود"
    for i in range(2, 6):                       # چهار تیکِ بعدی، همان دلیل
        tr.scan(ask_fn=lambda *a, **k: {"ok": False}, now=_at(14, i))
    assert len(tr._rows()) == n1, "دلیلِ یکسانِ پیاپی تکرار شد"
    last = tr._rows()[-1]
    assert last["reason"] == "too-soon" and last["note"] == "scan-skipped", last


def t_a_different_skip_reason_is_always_recorded():
    """`too-soon` → `quiet-hours` خبر است، نه تکرار — نباید بلعیده شود."""
    _fresh()
    tr.request(**_FULL, now=_at(14))
    tr.scan(ask_fn=lambda *a, **k: {"ok": False}, now=_at(14, 1))
    n1 = len(tr._rows())
    tr.scan(ask_fn=lambda *a, **k: {"ok": False}, now=_at(3))   # ساعتِ سکوت
    rows = tr._rows()
    assert len(rows) == n1 + 1, "دلیلِ متفاوت ثبت نشد"
    assert rows[-1]["reason"] == "quiet-hours", rows[-1]


def t_the_ledger_survives_a_reload():
    """حالتِ درون‌حافظه اثبات نیست — بعد از reload باید از دیسک بازخوانی شود."""
    _fresh()
    tr.request(**_FULL, now=_at(14))
    tr.request(need="دسترسیِ نوشتنی به تقویم", why="برای زمان‌بندیِ پیگیری",
               cost="۰", alternative="دستی", now=_at(14, 1))
    again = importlib.reload(tr)
    assert len(again.pending()) == 2, len(again.pending())


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_tool_request: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
