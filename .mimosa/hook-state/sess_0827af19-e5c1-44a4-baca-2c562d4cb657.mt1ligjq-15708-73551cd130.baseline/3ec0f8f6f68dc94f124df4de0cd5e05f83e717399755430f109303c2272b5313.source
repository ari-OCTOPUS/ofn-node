#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_tg_brief — بریفِ صبح/جمع‌بندیِ شب (لِین E؛ منشور رأی‌های ۵ و ۱۱).

    دقیقاً ≤۳ خطِ کار · لینکِ تاپیک t.me/c با ریاضیِ ‎-100‎ درست ·
    ایزولهٔ bidi دورِ لینک · یک‌بار-در-روز با cursor ِ تزریقی · صفر ارسال
"""
import os
import sys
from datetime import datetime
from pathlib import Path

import harness

ENV = harness.setup("tg-brief")

_OPS = Path(__file__).resolve().parent.parent
_TC = str(_OPS / "telegram_center")
if _TC not in sys.path:
    sys.path.insert(0, _TC)

import brief  # noqa: E402
import leg_tasks as lt  # noqa: E402
import reminders as rm  # noqa: E402

NOW = datetime(2026, 8, 5, 7, 40).timestamp()
CFG = {"chat_id": -1001234567890, "topics": {"lead": 7, "ziman": 9},
       "display_names": {"lead": "نقاشی", "ziman": "زیمان"}}

_TASK_ICONS = ("🚧", "⏳", "⏰", "▫")


def _fresh():
    for leg in ("lead", "ziman"):
        try:
            lt._path(leg).unlink()
        except OSError:
            pass
    for p in (rm._file(), rm._cfg_file()):
        try:
            p.unlink()
        except OSError:
            pass


def _task_lines(txt: str) -> list:
    return [l for l in txt.splitlines() if l.startswith(_TASK_ICONS)]


# ── لینکِ تاپیک ────────────────────────────────────────────────────────────
def t_topic_link_strips_the_minus_100_prefix():
    assert brief.topic_link(-1001234567890, 42) == \
        "https://t.me/c/1234567890/42"
    assert brief.topic_link("-1001234567890", 7) == \
        "https://t.me/c/1234567890/7"
    assert brief.topic_link(-987654, 3) == "https://t.me/c/987654/3"
    assert brief.topic_link(555, 1) == "https://t.me/c/555/1"


# ── بریفِ صبح ──────────────────────────────────────────────────────────────
def t_morning_brief_has_at_most_three_task_lines_blocked_first():
    _fresh()
    t1 = lt.add("lead", "لید سیدنی را بررسی کن", now=NOW - 3600)
    lt.set_state("lead", t1["id"], lt.BLOCKED, question="بودجه چند؟",
                 now=NOW - 1800)
    t2 = lt.add("lead", "پیش‌نویس پیام", now=NOW - 3000)
    lt.set_state("lead", t2["id"], lt.WORKING, now=NOW - 1000)
    for i in range(4):
        lt.add("lead", f"کارِ صف {i}", now=NOW - 900 + i)
    lt.add("ziman", "عکس محصول جدید", now=NOW - 500)

    txt = brief.morning_text(now=NOW, cfg=CFG, reminders_mod=rm)
    assert "بریف صبح" in txt, txt
    lines = _task_lines(txt)
    assert len(lines) == 3, (len(lines), txt)
    assert lines[0].startswith("🚧") and "بودجه" in lines[0], \
        "BLOCKED باید خطِ اول باشد"
    assert lines[1].startswith("⏳"), "WORKING باید بعد از BLOCKED باشد"


def t_morning_brief_links_every_nonempty_business_topic():
    _fresh()
    lt.add("lead", "کارِ نقاشی", now=NOW - 100)
    lt.add("ziman", "کارِ زیمان", now=NOW - 90)
    txt = brief.morning_text(now=NOW, cfg=CFG, reminders_mod=rm)
    assert "t.me/c/1234567890/7" in txt, txt      # ریاضیِ -100 درست
    assert "t.me/c/1234567890/9" in txt, txt
    assert "-100" not in txt, "پیشوندِ -100 نباید در لینک بماند"
    assert "نقاشی" in txt and "زیمان" in txt


def t_morning_brief_isolates_ltr_links_with_bidi_marks():
    """قاعدهٔ UX ۹ منشور: U+2066…U+2069 دورِ هر تکهٔ LTR."""
    _fresh()
    lt.add("lead", "کاری", now=NOW - 100)
    txt = brief.morning_text(now=NOW, cfg=CFG, reminders_mod=rm)
    assert "⁦https://t.me/c/1234567890/7⁩" in txt, \
        "لینک داخلِ ایزولهٔ bidi نیست"


def t_morning_brief_counts_open_reminders_in_persian_digits():
    _fresh()
    due, cleaned = rm.parse_when("فردا ساعت ۹ زنگ به تامین‌کننده", now=NOW)
    rm.add(cleaned, due_ts=due, now=NOW)
    txt = brief.morning_text(now=NOW, cfg=CFG, reminders_mod=rm)
    assert "یادآوری‌های باز: ۱" in txt, txt


def t_todays_due_reminder_is_a_candidate_task_line():
    _fresh()
    rm.add("قرارِ دندان‌پزشکی", due_ts=NOW + 3600, now=NOW)   # امروز
    txt = brief.morning_text(now=NOW, cfg=CFG, reminders_mod=rm)
    assert any(l.startswith("⏰") and "دندان" in l
               for l in _task_lines(txt)), txt


def t_empty_vault_gives_a_short_graceful_brief():
    _fresh()
    txt = brief.morning_text(now=NOW, cfg=CFG, reminders_mod=rm)
    assert "بریف صبح" in txt and "t.me" not in txt, txt
    assert len(txt) < 400, "بریفِ خالی باید کوتاه باشد (بدونِ شلوغی)"
    assert "یادآوری‌های باز: ۰" in txt


# ── جمع‌بندیِ شب ───────────────────────────────────────────────────────────
def t_evening_text_reports_done_blocked_and_tomorrow():
    _fresh()
    a = lt.add("lead", "کار الف", now=NOW - 4000)
    lt.set_state("lead", a["id"], lt.DONE, result="انجام شد", now=NOW - 100)
    b = lt.add("lead", "کار ب", now=NOW - 3900)
    lt.set_state("lead", b["id"], lt.BLOCKED, question="آدرس؟", now=NOW - 200)
    lt.add("ziman", "کار فردا", now=NOW - 300)
    txt = brief.evening_text(now=NOW, cfg=CFG)
    assert "جمع‌بندی شب" in txt, txt
    assert "انجام شد" in txt and "آدرس" in txt and "کار فردا" in txt, txt


def t_evening_text_is_honest_when_nothing_finished():
    _fresh()
    txt = brief.evening_text(now=NOW, cfg=CFG)
    assert "تمام نشد" in txt, txt


# ── ضربان: یک‌بار در روز ───────────────────────────────────────────────────
def t_beat_fires_each_brief_once_per_day():
    _fresh()
    sent, state = [], {}
    early = datetime(2026, 8, 5, 6, 0).timestamp()
    assert brief.beat(now=early, cfg=CFG,
                      send_dm_fn=lambda t: sent.append(t),
                      state=state) is None, "قبل از brief_hour نباید بفرستد"

    m = datetime(2026, 8, 5, 7, 40).timestamp()
    out = brief.beat(now=m, cfg=CFG, send_dm_fn=lambda t: sent.append(t),
                     state=state)
    assert out and "بریف صبح" in out and len(sent) == 1
    assert brief.beat(now=m + 600, cfg=CFG,
                      send_dm_fn=lambda t: sent.append(t),
                      state=state) is None, "صبحِ دوم در همان روز"

    e = datetime(2026, 8, 5, 21, 40).timestamp()
    out2 = brief.beat(now=e, cfg=CFG, send_dm_fn=lambda t: sent.append(t),
                      state=state)
    assert out2 and "جمع‌بندی شب" in out2 and len(sent) == 2
    assert brief.beat(now=e + 600, cfg=CFG,
                      send_dm_fn=lambda t: sent.append(t),
                      state=state) is None, "شبِ دوم در همان روز"

    m2 = datetime(2026, 8, 6, 7, 40).timestamp()
    out3 = brief.beat(now=m2, cfg=CFG, send_dm_fn=lambda t: sent.append(t),
                      state=state)
    assert out3 and "بریف صبح" in out3 and len(sent) == 3, "روزِ نو نچرخید"


# ── انضباط ─────────────────────────────────────────────────────────────────
def t_flag_is_default_off():
    os.environ.pop("OCTOPUS_TG_BRIEF", None)
    assert not brief.enabled()


def t_the_module_has_no_external_effectors():
    import ast
    tree = ast.parse(Path(brief.__file__).read_text("utf-8"))
    imported = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            imported.update(a.name.split(".")[0] for a in n.names)
        elif isinstance(n, ast.ImportFrom) and n.module:
            imported.add(n.module.split(".")[0])
    assert not (imported & {"requests", "urllib", "socket", "http",
                            "subprocess"}), imported


def t_state_stays_inside_the_isolated_tree():
    live = str(harness.REAL_VAULT / "_ops" / "state").lower()
    assert not str(lt._path("lead")).lower().startswith(live)
    assert not str(rm._file()).lower().startswith(live)


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items())
              if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_tg_brief: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
