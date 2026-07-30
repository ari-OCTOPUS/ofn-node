#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_tg_leg_tasks — مدلِ Task ِ گروهِ پاها (رأیِ مالک ۲۰۲۶-۰۷-۳۰ شب).

    هر پیام = یک کار · کارتِ زندهٔ ویرایش‌شونده · ۴ دکمه · ۴ وضعیت ·
    رسیدِ با شاهد · BLOCKED به‌جای سکوت · صفر اثرِ بیرونی از گروه
"""
import sys
from pathlib import Path

import harness

ENV = harness.setup("tg-leg-tasks")

_OPS = Path(__file__).resolve().parent.parent
_TC = str(_OPS / "telegram_center")
if _TC not in sys.path:
    sys.path.insert(0, _TC)

import leg_tasks as lt  # noqa: E402

NOW = 1_785_400_000.0


def _fresh(leg="lead"):
    try:
        lt._path(leg).unlink()
    except OSError:
        pass


# ── چرخهٔ عمر: چهار وضعیت، نه بیشتر ─────────────────────────────────────────
def t_a_message_becomes_a_queued_task_with_an_id():
    _fresh()
    t = lt.add("lead", "این لینک را بررسی کن", now=NOW)
    assert t and t["state"] == lt.QUEUED and t["id"] == "TASK-1", t
    t2 = lt.add("lead", "این فایل را به صف اضافه کن", now=NOW + 1)
    assert t2["id"] == "TASK-2", t2


def t_the_lifecycle_walks_queued_working_done():
    _fresh()
    t = lt.add("lead", "بررسی کن", now=NOW)
    w = lt.set_state("lead", t["id"], lt.WORKING, now=NOW + 1)
    assert w["state"] == lt.WORKING
    d = lt.set_state("lead", t["id"], lt.DONE, result="مناسب است",
                     evidence="سایتِ رسمی + منبعِ دوم", now=NOW + 2)
    assert d["state"] == lt.DONE and d["result"] == "مناسب است"


def t_an_invalid_state_is_rejected_not_invented():
    """«فقط چهار وضعیت — پیچیده‌اش نکن.» وضعیتِ پنجم ساختاراً رد می‌شود."""
    _fresh()
    t = lt.add("lead", "کاری", now=NOW)
    assert lt.set_state("lead", t["id"], "PAUSED") is None
    assert lt.set_state("lead", t["id"], "CANCELLED") is None
    fresh = lt.queue("lead")[0]
    assert fresh["state"] == lt.QUEUED, "گذارِ نامعتبر state را دست زد"


def t_cancel_is_done_with_a_result_not_a_fifth_state():
    _fresh()
    t = lt.add("lead", "کاری", now=NOW)
    c = lt.cancel("lead", t["id"], now=NOW + 1)
    assert c["state"] == lt.DONE and c["result"] == "لغو شد", c


def t_questions_are_not_turned_into_tasks():
    """سؤال همان لحظه جواب می‌گیرد (مسیرِ چت) — کارت‌سازی برایش مزاحمت است."""
    for q in ("الان چه کار می‌کنی؟", "چرا متوقف شدی؟", "چه خبر",
              "آیا تمام شد؟"):
        assert lt.is_question(q), q
    for c in ("این لینک را بررسی کن", "ادامه بده", "این مورد را رد کن",
              "پنج نتیجه بهتر را نشان بده"):
        assert not lt.is_question(c), c


# ── موتور: BLOCKED به‌جای سکوت، رسیدِ صادق ──────────────────────────────────
def t_the_engine_claims_only_working_tasks_started_by_the_owner():
    """هیچ کاری بدونِ تپِ «شروع» ِ مالک اجرا نمی‌شود — QUEUED قابلِ claim نیست."""
    _fresh()
    lt.add("lead", "کارِ صف‌شده", now=NOW)
    assert lt.claim_next("lead") is None, "QUEUED نباید claim شود"
    t = lt.queue("lead")[0]
    lt.set_state("lead", t["id"], lt.WORKING)
    got = lt.claim_next("lead")
    assert got and got["id"] == t["id"]


def t_an_i_dont_know_answer_becomes_blocked_with_the_question():
    state, q = lt.judge_engine_answer("برای این لینک اطلاعاتِ کافی ندارم")
    assert state == lt.BLOCKED and q, (state, q)
    state2, _ = lt.judge_engine_answer("لید مناسب است؛ سایتِ رسمی دارد")
    assert state2 == lt.DONE
    state3, q3 = lt.judge_engine_answer("")
    assert state3 == lt.BLOCKED, "جوابِ خالی نباید DONE شود"


def t_the_receipt_never_fabricates_confidence_and_tells_the_truth_about_cost():
    """اعتماد بدونِ سنجه = «—»؛ خرج/ارسالِ بیرونی حقیقتِ ساختاریِ مسیرند."""
    _fresh()
    t = lt.add("lead", "بررسی", now=NOW)
    d = lt.set_state("lead", t["id"], lt.DONE, result="مناسب",
                     evidence="شاهدِ الف")
    r = lt.receipt_text(d)
    assert "اعتماد: —" in r, r
    assert "خرج: صفر" in r and "ارسال بیرونی: انجام نشد" in r, r
    assert "٪" not in r, "درصدِ جعلی در رسید"


def t_blocked_gets_a_question_card_instead_of_silence():
    _fresh()
    t = lt.add("lead", "بررسیِ عکس", now=NOW)
    b = lt.set_state("lead", t["id"], lt.BLOCKED,
                     question="عکسِ کامل‌تر یا آدرسِ پروژه")
    txt = lt.blocked_text(b)
    assert "اطلاعات کافی ندارم" in txt and "عکسِ کامل‌تر" in txt, txt
    kb = lt.blocked_keyboard("lead", b)
    labels = [btn["text"] for row in kb for btn in row]
    assert any("ادامه" in x for x in labels) and any("لغو" in x for x in labels)


# ── کارت و دکمه‌ها ──────────────────────────────────────────────────────────
def t_the_card_has_the_agreed_fields_and_exactly_four_buttons():
    _fresh()
    lt.add("lead", "بررسی ۲۰ لید سیدنی", now=NOW)
    body = lt.card_text("lead", paused=False, now=NOW + 60)
    for field in ("وضعیت:", "کار فعلی:", "پیشرفت:", "نتیجه معتبر:", "مانع:",
                  "آخرین فعالیت:"):
        assert field in body, (field, body)
    kb = lt.card_keyboard("lead")
    n = sum(len(row) for row in kb)
    assert n == 4, f"{n} دکمه — قرارداد دقیقاً ۴ است"
    for row in kb:
        for b in row:
            assert len(b["callback_data"].encode()) <= 64
            assert b["callback_data"].startswith("tk:")


def t_a_paused_leg_shows_paused_on_the_card():
    _fresh()
    body = lt.card_text("lead", paused=True, now=NOW)
    assert "متوقف" in body, body


def t_persian_digits_on_the_card_no_bare_latin_counters():
    """درسِ bidi: عددِ لاتین وسطِ سطرِ فارسی جابه‌جا رندر می‌شود."""
    _fresh()
    for i in range(3):
        t = lt.add("lead", f"کارِ {i}", now=NOW + i)
        lt.set_state("lead", t["id"], lt.DONE, result="اوکی", now=NOW + 10 + i)
    body = lt.card_text("lead", paused=False, now=NOW + 60)
    import re
    bare = re.findall(r"پیشرفت: [0-9]|در صف: [0-9]", body)
    assert not bare, (bare, body)


# ── سیم: مرکز واقعاً وصل است (AST نه grep) ──────────────────────────────────
def t_the_center_wires_all_three_seams():
    import ast
    src = (_OPS / "telegram_center" / "center.py").read_text("utf-8")
    tree = ast.parse(src)
    calls = {getattr(n.func, "attr", None)
             for n in ast.walk(tree) if isinstance(n, ast.Call)}
    assert "_drive_leg_engine" in calls, "موتور در beat صدا نمی‌خورد"
    assert "_handle_tasks_callback" in calls, "دکمه‌های tk dispatch نمی‌شوند"
    assert "_refresh_leg_card" in calls, "کارتِ زنده هرگز تازه نمی‌شود"
    # و intake: پیامِ leg_scoped به add می‌رسد
    assert "add" in {getattr(n.func, "attr", None) for n in ast.walk(tree)
                     if isinstance(n, ast.Call)
                     and getattr(getattr(n.func, "value", None), "id", None)
                     in ("_lt", "leg_tasks")}, "پیامِ پا به Task تبدیل نمی‌شود"


def t_every_tk_button_the_module_emits_is_dispatched_in_the_center():
    """درسِ tr/iv — دکمهٔ بی‌handler = کارتِ مرده."""
    src = (_OPS / "telegram_center" / "center.py").read_text("utf-8")
    assert 'verb == "tk"' in src, "tk در روترِ مرکز نیست"
    ops = set()
    for kb in (lt.card_keyboard("lead"),
               lt.intake_keyboard("lead", {"id": "TASK-1"}),
               lt.blocked_keyboard("lead", {"id": "TASK-1"})):
        for row in kb:
            for b in row:
                ops.add(b["callback_data"].split(":")[1])
    handler = src.split("def _handle_tasks_callback")[1][:3000]
    for op in ops:
        assert f'op == "{op}"' in handler, f"tk:{op} ساخته می‌شود ولی شاخه ندارد"


def t_the_engine_has_no_external_effectors():
    """از گروه هیچ اثرِ بیرونی ممکن نیست — ماژول نه شبکه دارد نه ارسال."""
    import ast
    tree = ast.parse(Path(lt.__file__).read_text("utf-8"))
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
    for bad in ("send", "send_text", "post", "sendMessage", "urlopen"):
        assert bad not in called, f"leg_tasks خودش می‌فرستد: {bad}"


def t_state_stays_inside_the_isolated_tree():
    live = str(harness.REAL_VAULT / "_ops" / "state").lower()
    assert not str(lt._path("lead")).lower().startswith(live), lt._path("lead")


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_tg_leg_tasks: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
