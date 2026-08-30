#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_tg_weekly_review — مرورِ هفتگیِ شنبه صبح (رأی ۱۲ + §۹، W4 لِین H).

    due فقط شنبهٔ بعد از ۰۸:۰۰ و یک بار در هفته · غیابِ صادقانه («داده‌ای
    نیست»، صفر عددسازی) · لیدهای تحویل‌شده از قیفِ واقعی · پیشنهادِ تنزلِ
    طبقه روی نرخِ تأیید >۹۰٪ · beat پشتِ فلگِ خاموش
"""
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import harness

ENV = harness.setup("tg-weekly-review")

_OPS = Path(__file__).resolve().parent.parent
_TC = str(_OPS / "telegram_center")
if _TC not in sys.path:
    sys.path.insert(0, _TC)
_OUT = str(_OPS / "outcomes")
if _OUT not in sys.path:
    sys.path.insert(0, _OUT)

import weekly_review as wr  # noqa: E402
import leg_tasks as lt  # noqa: E402

STATE = Path(ENV["OCTOPUS_STATE_DIR"])

# 2026-08-01 شنبه است (07-31 جمعه). ساعت‌ها محلی.
SAT_0830 = datetime(2026, 8, 1, 8, 30).timestamp()
SAT_0759 = datetime(2026, 8, 1, 7, 59).timestamp()
SUN_0900 = datetime(2026, 8, 2, 9, 0).timestamp()
NEXT_SAT = datetime(2026, 8, 8, 8, 30).timestamp()


def _clean():
    for leg in wr.BUSINESS_LEGS:
        try:
            lt._path(leg).unlink()
        except OSError:
            pass
    for sub in ("telegram/approvals", "outcomes", "reminders"):
        d = STATE / sub
        if d.is_dir():
            for p in d.glob("*"):
                try:
                    p.unlink()
                except OSError:
                    pass


def _leg_block(text: str, leg: str) -> str:
    lines = text.splitlines()
    i = next(k for k, ln in enumerate(lines)
             if ln.startswith(wr.DISPLAY[leg]))
    block = []
    for ln in lines[i:]:
        if not ln.strip() and block:
            break
        block.append(ln)
    return "\n".join(block)


# ── due-logic ──────────────────────────────────────────────────────────────
def t_due_only_saturday_after_8_and_once_per_week():
    state = {}
    assert not wr.is_due(now=SAT_0759, state=state), "قبل از ۸ نباید due باشد"
    assert wr.is_due(now=SAT_0830, state=state)
    state[wr.CURSOR_KEY] = wr._week_key(SAT_0830)
    assert not wr.is_due(now=SAT_0830 + 3600, state=state), \
        "همان شنبه دوباره due شد"
    assert not wr.is_due(now=SUN_0900, state=state), "یکشنبه due شد"
    assert wr.is_due(now=NEXT_SAT, state=state), "شنبهٔ بعد باید دوباره due باشد"


# ── غیابِ صادقانه ──────────────────────────────────────────────────────────
def t_empty_stores_say_no_data_and_never_fabricate_numbers():
    _clean()
    txt = wr.review_text(now=SAT_0830, cfg={})
    assert wr.NO_DATA in txt, txt
    for leg in wr.BUSINESS_LEGS:
        block = _leg_block(txt, leg)
        assert not re.search(r"[0-9]", block), (leg, block)
        fa_digits = re.findall(r"[۰-۹]", block)
        assert not fa_digits, f"عدد برای پای بی‌داده جعل شد: {leg}: {block}"
        assert wr.NO_DATA in block, (leg, block)
    assert "کم‌صدا" in _leg_block(txt, "ziman"), "مارکرِ کم‌صدای زیمان نیست"


def t_leg_activity_shows_up_with_persian_digits_and_next_step():
    _clean()
    t1 = lt.add("lead", "بررسی ۲۰ لید بروکر", now=SAT_0830 - 7200)
    lt.set_state("lead", t1["id"], lt.DONE, result="۵ لید خوب",
                 now=SAT_0830 - 3600)
    lt.add("lead", "پیگیریِ مشتریِ چتسوود", now=SAT_0830 - 1800)
    txt = wr.review_text(now=SAT_0830, cfg={})
    block = _leg_block(txt, "lead")
    assert "چه شد" in block and "۱ کار تمام شد" in block, block
    assert "چه بعد: پیگیریِ مشتریِ چتسوود" in block, block
    assert not re.search(r"[0-9]", block), "عددِ لاتین وسطِ سطرِ فارسی"
    # پای فعال ولی بی‌پول: سطرِ پول هم باید صادقانه «داده‌ای نیست» بگوید —
    # جهشِ ۰۷-۳۱ نشان داد فقط چکِ پاهای خالی این سطر را نمی‌پاید.
    assert f"پول: {wr.NO_DATA}" in block, block


# ── قیف: خواننده و نویسنده با هم ───────────────────────────────────────────
def t_delivered_leads_and_paid_come_from_the_real_funnel_writer():
    _clean()
    import funnel_store as fs
    store = fs.FunnelStore(STATE / "outcomes" / "funnel.db")
    occurred = datetime.fromtimestamp(SAT_0830 - 3600,
                                      timezone.utc).isoformat()
    old = datetime.fromtimestamp(SAT_0830 - 9 * 86400,
                                 timezone.utc).isoformat()
    for i, (lid, et, at) in enumerate((
            ("L-1", "proposal.routed", occurred),
            ("L-2", "proposal.routed", occurred),
            ("L-1", "invoice.paid", occurred),
            ("L-9", "proposal.routed", old))):     # بیرونِ پنجرهٔ هفته
        store.record({"lead_id": lid, "event_type": et, "occurred_at": at,
                      "source_component": "test", "causation_id": str(i)})
    store.close()
    txt = wr.review_text(now=SAT_0830, cfg={})
    assert "لیدهای تحویل‌شده: ۲" in txt, txt
    assert "۱ فاکتورِ paid" in _leg_block(txt, "lead"), _leg_block(txt, "lead")


# ── نرخِ تأیید و پیشنهادِ تنزل (§۹) ────────────────────────────────────────
def _write_approvals(kind: str, ok_n: int, no_n: int, *, ts: str):
    adir = STATE / "telegram" / "approvals"
    adir.mkdir(parents=True, exist_ok=True)
    for i in range(ok_n + no_n):
        v = "ok" if i < ok_n else "no"
        (adir / f"{kind}-{i}.json").write_text(json.dumps(
            {"id": f"{kind}-{i}", "verdict": v, "ts": ts, "type": kind},
            ensure_ascii=False), "utf-8")


def t_over_90_percent_approval_suggests_a_tier_demotion():
    _clean()
    ts = datetime.fromtimestamp(SAT_0830 - 86400).isoformat()
    _write_approvals("lead-card", 19, 1, ts=ts)      # ٪۹۵
    _write_approvals("money-card", 2, 2, ts=ts)      # ٪۵۰
    txt = wr.review_text(now=SAT_0830, cfg={})
    assert "نرخ تأیید کارت‌ها:" in txt, txt
    assert "lead-card" in txt and "٪۹۵" in txt, txt
    assert "یک طبقه پایین بیاور" in txt, txt
    sug = [ln for ln in txt.splitlines() if "یک طبقه پایین بیاور" in ln]
    assert len(sug) == 1 and "lead-card" in sug[0], sug
    assert "money-card" not in sug[0]


def t_no_suggestion_below_the_threshold_or_sample_floor():
    _clean()
    ts = datetime.fromtimestamp(SAT_0830 - 86400).isoformat()
    _write_approvals("tiny-card", 2, 0, ts=ts)       # ٪۱۰۰ ولی n=2 < کف
    _write_approvals("meh-card", 8, 2, ts=ts)        # ٪۸۰
    txt = wr.review_text(now=SAT_0830, cfg={})
    assert "یک طبقه پایین بیاور" not in txt, txt


def t_stale_approvals_outside_the_week_are_ignored():
    _clean()
    old = datetime.fromtimestamp(SAT_0830 - 9 * 86400).isoformat()
    _write_approvals("old-card", 10, 0, ts=old)
    txt = wr.review_text(now=SAT_0830, cfg={})
    assert "old-card" not in txt, txt


# ── هزینه‌های ثبت‌شدهٔ مالک (بازبینی ۰۷-۳۱، BLOCKER 2) ─────────────────────
def t_expenses_section_reads_the_real_capture_writer_and_is_honest_when_empty():
    """round-trip از مسیرِ تولیدی: capture (نویسنده) سطرِ هزینه را در نوتِ Raw
    می‌نویسد؛ weekly_review (خواننده) همان را در بخشِ «هزینه‌های ثبت‌شدهٔ
    هفته» می‌آورد. خالی ⇒ «هیچ هزینه‌ای ثبت نشده» — عددسازی ممنوع."""
    _clean()
    import shutil as _sh
    import capture as cap
    raw_dir = Path(ENV["ORG_ROOT"]) / "10 - Telegram processing" / "Raw"
    _sh.rmtree(raw_dir, ignore_errors=True)
    # (الف) غیابِ صادقانه
    txt0 = wr.review_text(now=SAT_0830, cfg={})
    assert "هزینه‌های ثبت‌شدهٔ هفته" in txt0, txt0
    assert "هیچ هزینه‌ای ثبت نشده" in txt0, txt0
    # (ب) نویسندهٔ واقعی: capture ِ یک هزینه در همین هفته
    kr = cap.classify("هزینه خرید رنگ ۴۵ دلار")
    filed = cap.file_to_vault(kr, "هزینه خرید رنگ ۴۵ دلار",
                              msg_meta={"message_id": 9101, "chat_id": 777},
                              now=SAT_0830 - 3600)
    r = cap.route(kr, filed["path"], now=SAT_0830 - 3600)
    assert r["routed"] == "expense-line", r
    # (ج) هزینهٔ بیرونِ پنجرهٔ هفته — نباید شمرده شود
    old_day = datetime.fromtimestamp(SAT_0830 - 9 * 86400).strftime("%Y-%m-%d")
    with Path(filed["path"]).open("a", encoding="utf-8") as f:
        f.write(f"- {old_day} هزینه: هزینهٔ کهنهٔ خارج از هفته\n")
    txt = wr.review_text(now=SAT_0830, cfg={})
    assert "۱ هزینه ثبت شده" in txt, txt
    assert "خرید رنگ" in txt, txt
    assert "هزینهٔ کهنهٔ خارج از هفته" not in txt, txt
    assert "هیچ هزینه‌ای ثبت نشده" not in txt, txt


def t_octopus_llm_spend_is_labeled_as_its_own_money_not_the_owners():
    """بازبینی ۰۷-۳۱ (BLOCKER 2c): عددِ telemetry خرجِ LLM ِ خودِ ارگانیسم است
    — برچسبِ قبلی («جمع Accounting») آن را پولِ بیزنسِ مالک جا می‌زد."""
    txt = wr.review_text(now=SAT_0830, cfg={})
    assert "خرجِ خودِ اختاپوس (LLM)" in txt, txt
    assert "جمع Accounting" not in txt, "برچسبِ گمراه‌کنندهٔ قدیمی هنوز هست"


# ── یادآوری‌های fired ِ هفته (بازبینی ۰۷-۳۱، BLOCKER 3) ────────────────────
def t_reminders_fired_count_reads_the_real_store_shape_and_the_real_clock():
    """seed از مسیرِ تولیدی: reminders.add + شلیکِ واقعیِ beat با ساعتِ
    تزریقی. شکلِ واقعیِ store یعنی {"seq","items":[...]} — نسخهٔ قبلی
    (rows=[d]) کلِ store را یک ردیف می‌شمرد و همیشه ۰/غلط می‌داد."""
    _clean()
    import reminders as rmod
    old_beat = SAT_0830 - 9 * 86400          # هفتهٔ پیش (بیرونِ پنجره)
    new_beat = SAT_0830 - 3600               # همین هفته
    assert rmod.add("پیگیریِ کهنه", due_ts=old_beat - 60, now=old_beat - 120)
    assert rmod.add("زنگ بزن به مشتری", due_ts=new_beat - 60, now=new_beat - 120)
    n_old = rmod.beat(now=old_beat, send_dm_fn=lambda t, rid: 1,
                      send_leg_fn=lambda leg, t: 1)
    n_new = rmod.beat(now=new_beat, send_dm_fn=lambda t, rid: 1,
                      send_leg_fn=lambda leg, t: 1)
    assert n_old == 1 and n_new == 1, (n_old, n_new)
    # خوانندهٔ واقعی: فقط شلیکِ داخلِ پنجرهٔ هفته
    assert wr._reminders_fired_week(SAT_0830) == 1, \
        wr._reminders_fired_week(SAT_0830)
    txt = wr.review_text(now=SAT_0830, cfg={})
    assert "یادآوری‌ها: ۱ شلیک" in txt, txt


# ── کیفیتِ یادآوری (§۹): شلیک ≠ مفید ───────────────────────────────────────
def t_reminder_quality_splits_fired_into_done_snoozed_and_open():
    """سه سرنوشتِ متفاوت از **همان** store ِ واقعی: انجام‌شده / بعداً /
    بی‌پاسخ. شمارِ لختِ fired این سه را یکی می‌کرد و «مفید» را نمی‌سنجید."""
    _clean()
    import reminders as rmod
    t0 = SAT_0830 - 3600          # ۰۷:۳۰ — بیرونِ پنجرهٔ سکوتِ ۲۳–۷ (رأی ۸)
    ids = []
    for label in ("انجامش می‌دهم", "بعداً می‌رسم", "هیچ جوابی ندادم"):
        it = rmod.add(label, due_ts=t0 - 60, now=t0 - 120)
        ids.append(it["id"])
    assert rmod.beat(now=t0, send_dm_fn=lambda t, rid: 1,
                     send_leg_fn=lambda leg, t: 1) == 3
    rmod.done(ids[0])                       # ✅ انجام شد
    rmod.snooze(ids[1], 1800, now=t0)       # ⏰ بعداً
    q = wr._reminder_quality(SAT_0830)
    assert q == {"fired": 3, "done": 1, "snoozed": 1, "open": 1}, q
    txt = wr.review_text(now=SAT_0830, cfg={})
    assert ("یادآوری‌ها: ۳ شلیک · ۱ انجام‌شده · ۱ بعداً · ۱ بی‌پاسخ "
            "(وضعِ فعلی)") in txt, txt


def t_reminder_quality_is_honestly_absent_without_a_store():
    _clean()
    import shutil as _sh
    _sh.rmtree(STATE / "reminders", ignore_errors=True)
    assert wr._reminder_quality(SAT_0830) is None
    txt = wr.review_text(now=SAT_0830, cfg={})
    assert f"· یادآوری‌ها: {wr.NO_DATA}" in txt, txt


# ── ساعتِ آزادشدهٔ مالک (§۹) — تخمینِ برچسب‌دار، هرگز عددِ لخت ─────────────
def t_hours_freed_shows_its_formula_and_counts_only_engine_work():
    """سه جزءِ سنجش‌پذیر با هم: کارِ بی‌دخالتِ مالک (کارِ حل‌شده با «➕
    اطلاعات مالک» بیرون می‌ماند) + یادآوریِ انجام‌شده + ثبتِ خودکارِ capture."""
    _clean()
    import capture as cap
    import reminders as rmod
    # (الف) دو کارِ تمام‌شده — یکی با دخالتِ مالک ⇒ فقط یکی می‌شمارد
    a = lt.add("mining", "گزارشِ نرخ هش", now=SAT_0830 - 5 * 3600)
    lt.set_state("mining", a["id"], lt.DONE, result="ساخته شد",
                 now=SAT_0830 - 4 * 3600)
    b = lt.add("crypto", "خلاصهٔ بازار", now=SAT_0830 - 5 * 3600)
    lt.set_state("crypto", b["id"], lt.BLOCKED, question="کدام جفت‌ارز؟",
                 now=SAT_0830 - 4.5 * 3600)
    lt.resolve_blocked("crypto", b["id"], "BTC و ETH", now=SAT_0830 - 4 * 3600)
    lt.set_state("crypto", b["id"], lt.DONE, result="خلاصه آماده شد",
                 now=SAT_0830 - 3 * 3600)
    assert wr._engine_tasks_week(SAT_0830) == 1, wr._engine_tasks_week(SAT_0830)
    # (ب) یک یادآوریِ انجام‌شده
    it = rmod.add("زنگ به مشتری", due_ts=SAT_0830 - 2400,
                  now=SAT_0830 - 2500)
    # ۰۸:۰۰ — بیرونِ پنجرهٔ سکوتِ ۲۳–۷، وگرنه beat عمداً شلیک نمی‌کند
    assert rmod.beat(now=SAT_0830 - 1800, send_dm_fn=lambda t, rid: 1,
                     send_leg_fn=lambda leg, t: 1) == 1
    rmod.done(it["id"])
    # (ج) یک ثبتِ خودکار از **نویسندهٔ واقعی**
    kr = cap.classify("ایده: کاتالوگ قاب‌های جدید")
    cap.file_to_vault(kr, "ایده: کاتالوگ قاب‌های جدید",
                      msg_meta={"message_id": 5511, "chat_id": 42},
                      now=SAT_0830 - 3600)
    assert wr._captures_filed_week(None, SAT_0830) >= 1

    hf = wr.hours_freed(SAT_0830)
    assert hf["tasks"] == 1 and hf["reminders_done"] == 1, hf
    assert hf["minutes"] == (1 * wr.MIN_PER_TASK + 1 * wr.MIN_PER_REMINDER
                             + hf["captures"] * wr.MIN_PER_CAPTURE), hf
    txt = wr.review_text(now=SAT_0830, cfg={})
    assert "ساعتِ آزادشدهٔ تو (تخمین)" in txt, txt
    line = [ln for ln in txt.splitlines() if "فرمول:" in ln]
    assert len(line) == 1, txt
    # فرمول باید هر سه ضریب را نشان بدهد — عددِ لختِ بی‌فرمول ممنوع
    for tok in ("کارِ بی‌دخالتِ تو", "یادآوریِ انجام‌شده", "ثبتِ خودکار",
                "دقیقه"):
        assert tok in line[0], (tok, line[0])
    assert "۱۰د" in line[0] and "۲د" in line[0] and "۳د" in line[0], line[0]


def t_hours_freed_disappears_when_no_component_has_data():
    """غیابِ صادقانه: نه عدد، نه فرمول — فقط «داده‌ای نیست».

    دو حالتِ متفاوت که هر دو باید ساکت بمانند (درسِ «جهشِ سبز = خطِ نادیده»:
    نسخهٔ اولِ این تست فقط حالتِ الف را داشت، و چون همان‌جا زودتر برمی‌گشت،
    جهشِ `minutes <= 0` زنده ماند):
      الف) هیچ store ای وجود ندارد           ⇒ همهٔ اجزا None
      ب) storeها هستند ولی خالی‌اند          ⇒ اجزا صفرِ واقعی‌اند
    حالتِ (ب) همان جایی است که «صفرِ سنجیده» نباید به «~۰ ساعت آزاد شد»
    ترجمه شود — صفر ساعت آزاد نشده، پس خطِ تخمین حرفی برای گفتن ندارد."""
    _clean()
    import shutil as _sh
    raw = Path(ENV["ORG_ROOT"]) / "10 - Telegram processing" / "Raw"
    _sh.rmtree(raw, ignore_errors=True)
    _sh.rmtree(STATE / "reminders", ignore_errors=True)
    # (الف) هیچ منبعی روی دیسک نیست
    assert wr._engine_tasks_week(SAT_0830) is None
    assert wr._captures_filed_week(None, SAT_0830) is None
    assert wr._reminder_quality(SAT_0830) is None
    assert wr.hours_freed(SAT_0830) is None
    txt = wr.review_text(now=SAT_0830, cfg={})
    assert f"· ساعتِ آزادشدهٔ تو: {wr.NO_DATA}" in txt, txt
    assert "تخمین" not in txt and "فرمول" not in txt, txt

    # (ب) storeها هستند و همه صفرند — نه None
    import reminders as rmod
    raw.mkdir(parents=True, exist_ok=True)
    t = lt.add("mining", "کارِ هنوز در صف", now=SAT_0830 - 3600)
    assert t and lt._path("mining").exists()
    rmod.load_config()                   # پوشهٔ reminders را می‌سازد
    assert wr._engine_tasks_week(SAT_0830) == 0
    assert wr._captures_filed_week(None, SAT_0830) == 0
    assert wr._reminder_quality(SAT_0830) == {"fired": 0, "done": 0,
                                              "snoozed": 0, "open": 0}
    assert wr.hours_freed(SAT_0830) is None, wr.hours_freed(SAT_0830)
    txt = wr.review_text(now=SAT_0830, cfg={})
    assert f"· ساعتِ آزادشدهٔ تو: {wr.NO_DATA}" in txt, txt
    assert "فرمول" not in txt, txt


# ── beat: فلگ، ارسالِ یک‌باره، cursor فقط بعدِ ارسالِ موفق ─────────────────
def t_beat_is_silent_with_the_flag_off():
    _clean()
    os.environ.pop(wr.FLAG, None)
    sent = []
    state = {}
    assert wr.beat(now=SAT_0830, cfg={}, send_dm_fn=lambda t: sent.append(t)
                   or 123, state=state) is False
    assert sent == [] and wr.CURSOR_KEY not in state


def t_beat_fires_once_per_saturday_and_again_next_week():
    _clean()
    os.environ[wr.FLAG] = "1"
    try:
        sent = []
        state = {}
        assert wr.beat(now=SAT_0830, cfg={},
                       send_dm_fn=lambda t: sent.append(t) or 123,
                       state=state) is True
        assert len(sent) == 1 and "مرور هفتگی" in sent[0]
        assert state[wr.CURSOR_KEY] == wr._week_key(SAT_0830)
        assert wr.beat(now=SAT_0830 + 3600, cfg={},
                       send_dm_fn=lambda t: sent.append(t) or 123,
                       state=state) is False
        assert wr.beat(now=SUN_0900, cfg={},
                       send_dm_fn=lambda t: sent.append(t) or 123,
                       state=state) is False
        assert len(sent) == 1, "بیش از یک بار در هفته فرستاد"
        assert wr.beat(now=NEXT_SAT, cfg={},
                       send_dm_fn=lambda t: sent.append(t) or 123,
                       state=state) is True
        assert len(sent) == 2
    finally:
        os.environ.pop(wr.FLAG, None)


def t_cursor_never_advances_on_a_failed_send():
    _clean()
    os.environ[wr.FLAG] = "1"
    try:
        state = {}
        assert wr.beat(now=SAT_0830, cfg={},
                       send_dm_fn=lambda t: None, state=state) is False
        assert wr.CURSOR_KEY not in state, "ارسالِ ناموفق cursor را جلو برد"

        def boom(t):
            raise RuntimeError("network down")
        assert wr.beat(now=SAT_0830, cfg={}, send_dm_fn=boom,
                       state=state) is False
        assert wr.CURSOR_KEY not in state
    finally:
        os.environ.pop(wr.FLAG, None)


# ── مرزها ──────────────────────────────────────────────────────────────────
def t_the_module_itself_never_sends_or_writes_state():
    import ast
    tree = ast.parse(Path(wr.__file__).read_text("utf-8"))
    imported = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            imported.update(a.name.split(".")[0] for a in n.names)
        elif isinstance(n, ast.ImportFrom) and n.module:
            imported.add(n.module.split(".")[0])
    assert not (imported & {"requests", "urllib", "socket", "http",
                            "subprocess"}), imported
    called = {getattr(n.func, "attr", None) or getattr(n.func, "id", None)
              for n in ast.walk(tree) if isinstance(n, ast.Call)}
    for bad in ("send", "send_text", "post", "sendMessage", "urlopen",
                "write_text", "os.replace"):
        assert bad not in called, f"weekly_review اثرِ ناخواسته دارد: {bad}"


def t_data_paths_stay_inside_the_isolated_tree():
    live = str(harness.REAL_VAULT / "_ops" / "state").lower()
    assert not str(wr._state_dir()).lower().startswith(live), wr._state_dir()


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_tg_weekly_review: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
