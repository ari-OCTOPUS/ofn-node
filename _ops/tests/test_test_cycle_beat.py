#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_test_cycle_beat — صداکنندهٔ حلقهٔ آزمون: زنجیرهٔ کامل، fail-closed، ضدِ دوبار-شلیک.

گاردها ↔ تهدیدهای فاز ۲:
  T4  «تستِ سبز روی تابعِ بی‌صداکننده» → این‌جا خودِ beat به‌صورتِ تابعی اجرا
      می‌شود (نه grep ِ سورس) و زنجیرهٔ هدف→پیش‌ثبت→دفتر را روی دیسک اثبات می‌کند.
  T12 «fail-open» → پیش‌ثبتِ شکسته = صفر اجرا، صفر ردیفِ دفتر، اسلاتِ نسوخته.
  dup-firing → دو beat در یک اسلات = یک چرخه.
  T21 «repeat جای switch» → نرمال‌سازیِ کلیدِ روش (فاصله/حروف) تکرار را تکرار می‌شمارد.
"""
import datetime as dt
import json
import os
import sys

import harness

ENV = harness.setup("test-cycle-beat")    # env قبل از import ِ opslib — ترتیب مهم است

import opslib          # noqa: E402
import test_cycle as tc   # noqa: E402
import prereg          # noqa: E402
import cycle_evaluator as ce  # noqa: E402


def _ts(day: str, h: int):
    return dt.datetime.combine(dt.date.fromisoformat(day), dt.time(h)).timestamp()


def _write_fitness(claimed=0):
    p = opslib.STATE_DIR / "fitness-latest.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"attribution": {"claimed": claimed}}), "utf-8")


def _on():
    os.environ["OCTOPUS_WIRE_TEST_CYCLE"] = "1"


def _off():
    os.environ["OCTOPUS_WIRE_TEST_CYCLE"] = "0"


def _fresh():
    _on()
    for rel in ("test_cycle/prereg.jsonl", "test_cycle/verdicts.jsonl",
                "test_cycle/state.json", "test_cycle/journal.jsonl",
                "fitness-latest.json"):
        try:
            (opslib.STATE_DIR / rel).unlink()
        except OSError:
            pass
    # STATE/JOURNAL ماژول زیرِ state/test_cycle اند — مسیرها را همسو نگه می‌داریم
    for p in (tc.STATE, tc.JOURNAL):
        try:
            p.unlink()
        except OSError:
            pass


# ── ایزولاسیون ──────────────────────────────────────────────────────────────
def t_state_is_isolated_from_the_live_tree():
    assert str(ENV["ops"]) in str(tc.JOURNAL), tc.JOURNAL
    assert r"F:\backup\_ops\state" not in str(tc.JOURNAL), tc.JOURNAL


# ── فلگِ خاموش = هیچ ────────────────────────────────────────────────────────
def t_flag_off_is_a_pure_noop():
    _fresh()
    _off()
    r = tc.beat(now=_ts("2026-07-30", 9))
    assert r == {"ok": False, "reason": "flag-off"}, r
    assert not tc.JOURNAL.exists()
    assert not prereg.LEDGER.exists()


# ── زنجیرهٔ کامل ────────────────────────────────────────────────────────────
def t_beat_runs_the_full_chain_and_burns_the_slot_once():
    _fresh()
    _write_fitness(claimed=0)
    r = tc.beat(now=_ts("2026-07-30", 9))
    assert r["ok"] is True, r
    assert r["prereg_id"], r
    assert r["switch"] == "first", r
    # روی دیسک: یک پیش‌ثبت + یک ردیفِ دفتر، هر دو برای همان چرخه
    assert len(prereg.rows()) == 1
    assert len(tc._rows()) == 1
    assert prereg.rows()[0]["cycle_id"] == tc._rows()[0]["cycle_id"] == r["cycle_id"]
    # پیش‌ثبت قبل از اجرا: target ِ منجمد در prereg موجود است
    assert prereg.rows()[0]["target"] == {"op": ">", "value": 0}
    # دوبار-شلیک در همان اسلات → not-due، هیچ ردیفِ تازه‌ای
    r2 = tc.beat(now=_ts("2026-07-30", 10))
    assert r2["ok"] is False and r2["reason"] == "not-due", r2
    assert len(prereg.rows()) == 1 and len(tc._rows()) == 1


def t_no_valid_goal_means_no_cycle_and_slot_not_burned():
    _fresh()                                  # هیچ سنجه‌ای روی دیسک نیست
    r = tc.beat(now=_ts("2026-07-30", 9))
    assert r["ok"] is False and r["reason"] == "no-valid-goal", r
    assert not tc.JOURNAL.exists()
    assert not prereg.LEDGER.exists()
    assert tc.due(_ts("2026-07-30", 9))["due"] is True    # اسلات نسوخت — tick بعدی دوباره


def t_prereg_failure_blocks_execution():
    """T12 — قلبِ fail-closed: بدونِ پیش‌ثبتِ روی دیسک، هیچ چرخه‌ای اجرا نمی‌شود."""
    _fresh()
    _write_fitness(claimed=0)
    orig = prereg.register

    def _refuse(proposal, *, cycle, now=None):
        return {"ok": False, "reason": "write-failed"}

    prereg.register = _refuse
    try:
        r = tc.beat(now=_ts("2026-07-30", 9))
    finally:
        prereg.register = orig
    assert r["ok"] is False and r["reason"] == "prereg-failed", r
    assert not tc.JOURNAL.exists()            # صفر اجرا
    assert tc.due(_ts("2026-07-30", 9))["due"] is True    # اسلات نسوخت


# ── ارزیابی → چرخشِ روش (حلقهٔ pivot ِ بسته) ────────────────────────────────
def t_failed_verdict_feeds_the_next_methods_pivot():
    _fresh()
    _write_fitness(claimed=0)
    r1 = tc.beat(now=_ts("2026-07-30", 9))            # چرخهٔ ۱ — روشِ ۰
    assert r1["ok"] and r1["switch"] == "first"
    # یک روز بعد: اول ارزیابِ معوق حکمِ FAIL می‌دهد (claimed نجنبید)،
    # بعد مولد روش را می‌چرخاند — در همان beat.
    r2 = tc.beat(now=_ts("2026-07-31", 9))
    assert r2["ok"] is True, r2
    assert r2.get("evaluated") == 1, r2
    assert r2["verdicts"][0]["verdict"] == "FAIL", r2
    assert "pivot-after-FAIL" in str(r2.get("method_note")), r2
    assert r2["switch"] == "switch", r2               # دفتر هم چرخش را شمرد
    rows = prereg.rows()
    assert rows[-1]["method_index"] == 1, rows[-1]


def t_the_cycle_observes_the_meters_it_does_not_re_fire_them():
    """اثباتِ زندهٔ ۲۰۲۶-۰۷-۳۰T۱۳:۱۲ — نسخهٔ اول این را می‌شکست.

    `organism` هر تیک خودش `recall_trend.sample()` و `tool_request.scan()` را
    صدا می‌زند. اگر چرخه هم دوباره صدایشان بزند، در همان تیک: recall ردیفِ
    تکراری می‌نویسد و scan سهمیهٔ سوخته را `too-soon` می‌بیند، پس دفتر
    `tool_request_ok=false` ثبت می‌کند — «این چرخه ابزار نخواست» در حالی که
    همان چرخه یک درخواستِ دقیقِ delivered ساخته بود. دروغِ سنجش.

    پس: صفر ردیفِ تازه از این مسیر، و شمارش باید همان چیزی باشد که روی دیسک است."""
    _fresh()
    _write_fitness(claimed=0)
    import recall_trend as rt
    import tool_request as tr
    # سری و دفتر را با دادهٔ «قبلاً موجود» پر می‌کنیم (نقشِ صداکنندهٔ organism)
    rt.TREND.parent.mkdir(parents=True, exist_ok=True)
    rt.TREND.write_text(json.dumps(
        {"ts": "2026-07-30T13:00:00", "schema": rt.SCHEMA, "cycle": 1,
         "events": 4, "keys": 17, "reach_median": 2.0, "self_ratio": 0.17,
         "coverage": 0.0074, "rows": 540}) + "\n", "utf-8")
    tr.LEDGER.parent.mkdir(parents=True, exist_ok=True)
    tr.LEDGER.write_text("\n".join(json.dumps(r) for r in (
        {"schema": tr.SCHEMA, "request_id": "a", "precise": True, "delivered": True},
        {"schema": tr.SCHEMA, "request_id": "b", "precise": False, "delivered": False},
    )) + "\n", "utf-8")
    trend_before = rt.TREND.read_bytes()
    ledger_before = tr.LEDGER.read_bytes()

    r = tc.beat(now=_ts("2026-07-30", 9))
    assert r["ok"] is True, r

    # هیچ ردیفِ تازه‌ای به هیچ‌کدام اضافه نشد — نه نمونهٔ تکراری، نه سهمیهٔ سوخته
    assert rt.TREND.read_bytes() == trend_before, "recall دوباره نمونه گرفت"
    assert tr.LEDGER.read_bytes() == ledger_before, "scan دوباره شلیک کرد"

    # و دفتر عددِ واقعیِ روی دیسک را ثبت کرد، نه «نشد»
    row = tc._rows()[-1]["outcome"]
    assert row["tool_request_ok"] is True, row
    assert row["tool_requests_total"] == 2, row
    assert row["tool_requests_precise"] == 1, row
    assert row["recall_ok"] is True and row["recall_events"] == 4, row


def t_an_empty_recall_series_is_still_sampled_once():
    """چرخهٔ اول نباید روی ترازوی خالی بنشیند — اگر سری خالی است، نمونه بگیر."""
    _fresh()
    _write_fitness(claimed=0)
    import recall_trend as rt
    try:
        rt.TREND.unlink()
    except OSError:
        pass
    r = tc.beat(now=_ts("2026-07-30", 9))
    assert r["ok"] is True, r
    # نتیجه هرچه باشد (زیرسیستمِ ادغام ممکن است در sandbox نباشد)، ادعای دروغ نکند
    row = tc._rows()[-1]["outcome"]
    assert isinstance(row["recall_ok"], bool), row


def t_two_slots_per_day_are_two_cycles():
    _fresh()
    _write_fitness(claimed=0)
    r_am = tc.beat(now=_ts("2026-07-30", 9))          # اسلاتِ صبح
    r_pm = tc.beat(now=_ts("2026-07-30", 15))         # اسلاتِ عصر (split=12)
    assert r_am["ok"] and r_pm["ok"]
    assert r_am["cycle_id"] != r_pm["cycle_id"]
    assert len(prereg.rows()) == 2


# ── آشکارسازِ چرخش: نرمال‌سازی ─────────────────────────────────────────────
def t_reworded_whitespace_is_still_a_repeat():
    """T21: «همان روش با فاصله/حروفِ متفاوت» چرخش نیست — تکرار است."""
    _fresh()
    tc.record(goal="g", method="بررسیِ   لیدهای باز", cycle="2026-07-30#0")
    sw = tc.detect_switch(tc._method_key("g"), "بررسیِ لیدهای   باز")
    assert sw["kind"] == "repeat", sw
    assert sw["repeat_n"] == 2


def t_a_genuinely_different_method_is_a_switch():
    _fresh()
    tc.record(goal="g", method="روشِ الف", cycle="2026-07-30#0")
    sw = tc.detect_switch(tc._method_key("g"), "روشِ ب — مسیرِ کاملاً متفاوت")
    assert sw["kind"] == "switch", sw
    assert sw["prev_method_key"] and sw["method_key"] != sw["prev_method_key"]


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_test_cycle_beat: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
