#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_tg_question_budget — بودجهٔ ۳۰ سؤال/هفته (رأی ۲۴، W4 لِین H).

    ۳۰ پرسیده، ۳۱م صف · rollover ِ هفتهٔ ISO صف را آزاد می‌کند ·
    حسابِ remaining · roundtrip ِ جواب · صفر ارسال از خودِ ماژول
"""
import sys
from pathlib import Path

import harness

ENV = harness.setup("tg-question-budget")

_OPS = Path(__file__).resolve().parent.parent
_TC = str(_OPS / "telegram_center")
if _TC not in sys.path:
    sys.path.insert(0, _TC)

import question_budget as qb  # noqa: E402

# سه‌شنبه 2026-07-28 10:00 محلی — وسطِ یک هفتهٔ ISO
from datetime import datetime  # noqa: E402

NOW = datetime(2026, 7, 28, 10, 0).timestamp()
NEXT_WEEK = NOW + 7 * 86400


def _fresh():
    try:
        qb._path().unlink()
    except OSError:
        pass


# ── سقفِ ۳۰ ────────────────────────────────────────────────────────────────
def t_thirty_questions_are_asked_then_the_31st_is_queued():
    _fresh()
    for i in range(30):
        r = qb.submit(f"سؤال {i}", now=NOW + i)
        assert r["status"] == "asked", (i, r)
    r31 = qb.submit("سؤالِ سی‌ویکم", now=NOW + 40)
    assert r31["status"] == "queued", r31
    assert r31["item"]["asked"] is False
    assert qb.remaining(NOW + 41) == 0


def t_remaining_math_counts_down_from_30():
    _fresh()
    assert qb.remaining(NOW) == 30
    qb.submit("اول", now=NOW)
    assert qb.remaining(NOW) == 29 and qb.used(NOW) == 1
    qb.submit("دوم", now=NOW + 1)
    assert qb.remaining(NOW) == 28


def t_an_empty_question_is_rejected_not_counted():
    _fresh()
    assert qb.submit("   ", now=NOW) is None
    assert qb.used(NOW) == 0


# ── rollover ِ هفته ────────────────────────────────────────────────────────
def t_next_week_frees_the_queue_head():
    _fresh()
    for i in range(30):
        qb.submit(f"سؤال {i}", now=NOW + i)
    q31 = qb.submit("سؤالِ صف‌شده", now=NOW + 40)
    assert q31["status"] == "queued"
    assert qb.pending(NOW + 41) is None, "با بودجهٔ صفر pending باید None باشد"
    # هفتهٔ بعد: بودجه تازه، صف‌شده سرِ صف
    assert qb.remaining(NEXT_WEEK) == 30
    head = qb.pending(NEXT_WEEK)
    assert head and head["id"] == q31["item"]["id"], head
    asked = qb.mark_asked(head["id"], now=NEXT_WEEK)
    assert asked and asked["asked"] is True
    assert qb.used(NEXT_WEEK) == 1 and qb.remaining(NEXT_WEEK) == 29
    assert qb.pending(NEXT_WEEK) is None, "صف خالی شد — pending باید None باشد"


def t_mark_asked_is_fail_closed_on_budget_and_idempotent():
    _fresh()
    for i in range(30):
        qb.submit(f"سؤال {i}", now=NOW + i)
    q31 = qb.submit("صف‌شده", now=NOW + 40)["item"]
    assert qb.mark_asked(q31["id"], now=NOW + 41) is None, \
        "تحویلِ بی‌بودجه نباید ثبت شود"
    ok = qb.mark_asked(q31["id"], now=NEXT_WEEK)
    assert ok is not None
    assert qb.mark_asked(q31["id"], now=NEXT_WEEK) is None, \
        "دبل-تاپ نباید دو بار بودجه بخورد"
    assert qb.used(NEXT_WEEK) == 1


# ── roundtrip ِ جواب ───────────────────────────────────────────────────────
def t_record_answer_roundtrip():
    _fresh()
    r = qb.submit("رنگِ مرجحِ مشتری‌های بروکر چیست؟",
                  context="برای پیش‌نویسِ لید", goal="لیدِ بهتر", now=NOW)
    qid = r["item"]["id"]
    got = qb.record_answer(qid, "سفید و طوسی", now=NOW + 100)
    assert got and got["answer"] == "سفید و طوسی" and got["answered_ts"]
    # از store ِ تازه هم بخوان (نه فقط خروجیِ همان call)
    fresh = qb._find(qb._load(NOW + 101), qid)
    assert fresh["answer"] == "سفید و طوسی"
    assert qb.record_answer("Q-999", "جواب", now=NOW) is None
    assert qb.record_answer(qid, "   ", now=NOW) is None


def t_question_text_and_callback_contract():
    _fresh()
    r = qb.submit("سؤالی برای هدفِ خودمون", goal="اهدافِ مشترک", now=NOW)
    item = r["item"]
    txt = qb.question_text(item)
    assert item["id"] in txt and "هدف:" in txt and "ریپلای" in txt
    cd = qb.answer_callback_data(item["id"])
    assert cd.startswith("qb:ans:") and len(cd.encode()) <= 64


# ── مرزها ──────────────────────────────────────────────────────────────────
def t_the_flag_defaults_off_and_module_never_sends():
    import os
    os.environ.pop(qb.FLAG, None)
    assert qb.enabled() is False, "فلگِ بودجه باید پیش‌فرض خاموش باشد"
    import ast
    tree = ast.parse(Path(qb.__file__).read_text("utf-8"))
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
        assert bad not in called, f"question_budget خودش می‌فرستد: {bad}"


def t_state_stays_inside_the_isolated_tree():
    live = str(harness.REAL_VAULT / "_ops" / "state").lower()
    assert not str(qb._path()).lower().startswith(live), qb._path()


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_tg_question_budget: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
