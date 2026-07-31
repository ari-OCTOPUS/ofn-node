#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_tg_capture — ‏Capture ِ یک‌ژسته (منشور رأی ۹–۱۰، لِین D).

    طبقه‌بندِ $0 · بایگانیِ قانونِ‌اساسی‌پسند · dedup ِ idempotent ·
    مسیریابیِ تزریقی · ویسِ صادق · ack ِ یک‌خطی · فلگ default-off
"""
import os
import re
import sys
from pathlib import Path
from types import SimpleNamespace

import harness

ENV = harness.setup("tg-capture")

_OPS = Path(__file__).resolve().parent.parent
_TC = str(_OPS / "telegram_center")
if _TC not in sys.path:
    sys.path.insert(0, _TC)

import capture  # noqa: E402

NOW = 1_785_400_000.0
RAW_DIR = Path(ENV["ORG_ROOT"]) / "10 - Telegram processing" / "Raw"


def _meta(mid, chat=777, **kw):
    return {"message_id": mid, "chat_id": chat, **kw}


def _msg(text, mid, chat=777, **extra):
    return {"message_id": mid, "chat": {"id": chat}, "text": text, **extra}


def _front(path):
    txt = Path(path).read_text("utf-8")
    m = re.match(r"^---\n(.*?)\n---", txt, re.S)
    assert m, f"فرانت‌متر ندارد: {txt[:120]}"
    fm = {}
    for line in m.group(1).splitlines():
        km = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*):\s*(.*)$", line)
        if km:
            fm[km.group(1)] = km.group(2).strip()
    return fm


def _raw_count():
    return len(list(RAW_DIR.glob("*.md"))) if RAW_DIR.exists() else 0


# ── طبقه‌بندی ───────────────────────────────────────────────────────────────
SAMPLES = [
    ("هزینه خرید رنگ ۴۵ دلار", "expense"),
    ("پول دادم بابت اجاره کارگاه", "expense"),
    ("پرداخت قبض برق انجام شد", "expense"),
    ("لید جدید از گامتری رسید", "lead"),
    ("مشتری جدید برای نقاشی 0412345678", "lead"),
    ("مشتری زنگ زد دنبال قیمت بود", "lead"),
    ("ایده: بات معرفی آثار برای گالری", "idea"),
    ("یه ایده دارم برای زیمان", "idea"),
    ("یادم بنداز فردا ساعت ۹ زنگ بزنم", "task"),
    ("سایت زیمان را بررسی کن", "task"),
    ("باید مدارک بیمه را ببرم", "task"),
    ("امروز هوا در سیدنی عالی بود", "note"),
    ("گزارش روز چیز خاصی نداشت", "note"),
]


def t_a_classification_table_covers_all_five_kinds():
    for text, want in SAMPLES:
        got = capture.classify(text)
        assert got["kind"] == want, (text, want, got)
    assert {w for _, w in SAMPLES} == set(capture.KINDS), \
        "جدولِ نمونه‌ها هر ۵ نوع را نمی‌پوشاند"


def t_b_lead_lands_on_the_painting_leg_and_tasks_detect_their_leg():
    lead = capture.classify("مشتری جدید برای نقاشی 0412345678")
    assert lead["leg"] == "lead", lead
    assert lead.get("phone"), "شمارهٔ تلفن گم شد"
    task = capture.classify("سایت زیمان را بررسی کن")
    assert task["leg"] == "ziman", task
    # لیدِ بی‌نامِ پا هم به 🎨نقاشی می‌رود (منشور §۵: لید فقط تاپیکِ نقاشی)
    bare = capture.classify("مشتری زنگ زد دنبال قیمت بود")
    assert bare["leg"] == "lead", bare


def t_c_when_is_extracted_from_natural_persian():
    got = capture.classify("یادم بنداز فردا ساعت ۹ زنگ بزنم")
    assert got["when"] and "فردا" in got["when"], got
    none = capture.classify("گزارش روز چیز خاصی نداشت")
    assert none["kind"] == "note", none


def t_d_llm_refinement_only_runs_behind_its_flag():
    calls = []

    def spy_ask(task, prompt):
        calls.append(task)
        return '{"kind": "lead", "leg": "lead", "summary": "x"}'

    os.environ.pop(capture.FLAG_CAPTURE_LLM, None)
    got = capture.classify("گزارش روز چیز خاصی نداشت", ask_fn=spy_ask)
    assert got["kind"] == "note" and not calls, "فلگ خاموش ولی LLM صدا خورد"
    os.environ[capture.FLAG_CAPTURE_LLM] = "1"
    try:
        got2 = capture.classify("گزارش روز چیز خاصی نداشت", ask_fn=spy_ask)
        assert calls == ["tg_capture"] and got2["kind"] == "lead", (calls, got2)
    finally:
        os.environ.pop(capture.FLAG_CAPTURE_LLM, None)


# ── بایگانی: نام §۵، فرانت‌متر §۶، dedup §۹ ────────────────────────────────
def t_e_filename_follows_the_machine_capture_pattern():
    kr = capture.classify("سایت زیمان را بررسی کن")
    got = capture.file_to_vault(kr, "سایت زیمان را بررسی کن",
                                msg_meta=_meta(120), now=NOW)
    p = Path(got["path"])
    assert p.parent == RAW_DIR, p
    assert re.match(r"^\d{4}-\d{2}-\d{2} \d{4} .+\.md$", p.name), p.name
    assert " - Copy" not in p.name and "(1)" not in p.name


def t_f_frontmatter_has_the_six_core_keys_and_legal_status():
    kr = capture.classify("مشتری جدید برای نقاشی 0412345678")
    got = capture.file_to_vault(kr, "مشتری جدید برای نقاشی 0412345678",
                                msg_meta=_meta(130), now=NOW)
    fm = _front(got["path"])
    for key in ("type", "project", "status", "tags", "created", "updated"):
        assert key in fm, (key, fm)
    assert fm["type"] == "telegram-log", fm
    assert fm["status"] in ("idea", "active", "paused", "done", "archived"), fm
    assert fm["tags"].startswith("["), fm
    assert re.match(r"^\d{4}-\d{2}-\d{2}$", fm["created"]), fm
    assert fm["message_id"] == "130" and fm["chat_id"] == "777", fm
    assert "Lead-نقاشی" in fm["project"], "لید به شناسنامهٔ نقاشی لینک نیست"


def t_g_duplicate_message_id_in_same_chat_is_skipped():
    kr = capture.classify("لید جدید از گامتری رسید")
    before = _raw_count()
    first = capture.file_to_vault(kr, "لید جدید از گامتری رسید",
                                  msg_meta=_meta(101), now=NOW)
    assert not first["dup"]
    second = capture.file_to_vault(kr, "لید جدید از گامتری رسید",
                                   msg_meta=_meta(101), now=NOW + 60)
    assert second["dup"] and "تکراری" in second["ack"], second
    assert second["path"] == first["path"], "dedup مسیرِ نوتِ قبلی را نداد"
    assert _raw_count() == before + 1, "پیامِ تکراری فایلِ دوم ساخت"


def t_h_dedup_is_scoped_to_the_chat_id():
    kr = capture.classify("لید جدید از گامتری رسید")
    got = capture.file_to_vault(kr, "لید جدید از گامتری رسید",
                                msg_meta=_meta(101, chat=888), now=NOW + 120)
    assert not got["dup"], "همان message_id در چتِ دیگر تکراری نیست (§۹)"


# ── مسیریابی: درختِ تصمیم با callbackهای تزریقی ────────────────────────────
def t_i_business_task_goes_to_the_legs_task_queue():
    kr = capture.classify("سایت زیمان را بررسی کن")
    filed = capture.file_to_vault(kr, "سایت زیمان را بررسی کن",
                                  msg_meta=_meta(201), now=NOW)
    calls = []
    fake = SimpleNamespace(add=lambda leg, text, now=None:
                           calls.append((leg, text)) or {"id": "TASK-9"})
    r = capture.route(kr, filed["path"], leg_tasks_mod=fake, now=NOW)
    assert r["routed"] == "leg-task", r
    assert calls and calls[0][0] == "ziman", calls
    assert "زیمان" in r["ack"], r


def t_j_personal_task_becomes_a_reminder_when_the_engine_exists():
    kr = capture.classify("یادم بنداز فردا ساعت ۹ زنگ بزنم")
    assert kr["leg"] is None, kr
    filed = capture.file_to_vault(kr, "یادم بنداز فردا ساعت ۹ زنگ بزنم",
                                  msg_meta=_meta(202), now=NOW)
    rem = []
    r = capture.route(kr, filed["path"],
                      reminder_add_fn=lambda t, w: rem.append((t, w)), now=NOW)
    assert r["routed"] == "reminder", r
    assert rem and rem[0][1] and "فردا" in rem[0][1], rem
    assert "یادآوری" in r["ack"], r


def t_k_personal_task_without_an_engine_stays_in_raw_as_idea():
    kr = capture.classify("باید مدارک بیمه را ببرم")
    filed = capture.file_to_vault(kr, "باید مدارک بیمه را ببرم",
                                  msg_meta=_meta(203), now=NOW)
    r = capture.route(kr, filed["path"], now=NOW)
    assert r["routed"] == "raw-idea", r
    assert _front(filed["path"])["status"] == "idea", \
        "نوتِ بی‌موتور باید status: idea بگیرد (§۴e)"


def t_l_lead_is_submitted_with_the_consented_manual_channel():
    kr = capture.classify("مشتری جدید برای نقاشی 0412345678")
    filed = capture.file_to_vault(kr, "مشتری جدید برای نقاشی 0412345678",
                                  msg_meta=_meta(204), now=NOW)
    got = []
    r = capture.route(kr, filed["path"], lead_submit_fn=got.append, now=NOW)
    assert r["routed"] == "lead-inbox", r
    assert got and got[0]["channel"] == "telegram_manual", got
    assert got[0]["phone"], "تلفنِ لید به صف نرسید"
    assert got[0]["source_note"] == filed["path"], got


def t_m_expense_appends_a_dated_line_item_to_the_raw_note():
    kr = capture.classify("هزینه خرید رنگ ۴۵ دلار")
    filed = capture.file_to_vault(kr, "هزینه خرید رنگ ۴۵ دلار",
                                  msg_meta=_meta(205), now=NOW)
    r = capture.route(kr, filed["path"], now=NOW)
    assert r["routed"] == "expense-line", r
    body = Path(filed["path"]).read_text("utf-8")
    assert re.search(r"^- \d{4}-\d{2}-\d{2} هزینه: ", body, re.M), \
        "سطرِ هزینهٔ تاریخ‌دار append نشد"


# ── handle: ورودیِ سیم‌کشی، ویسِ صادق، فلگ ─────────────────────────────────
def t_n_voice_is_captured_honestly_without_a_fake_transcript():
    os.environ[capture.FLAG_CAPTURE] = "1"
    try:
        r = capture.handle({"message_id": 301, "chat": {"id": 777},
                            "voice": {"file_id": "AF123xyz", "duration": 17}},
                           deps={"now": NOW})
    finally:
        os.environ.pop(capture.FLAG_CAPTURE, None)
    assert r["handled"], r
    assert "متن‌سازی هنوز نصب نیست" in r["ack"], r
    body = Path(r["path"]).read_text("utf-8")
    assert "file_id: AF123xyz" in body and "duration: 17" in body, body
    assert "[voice]" in body, body
    assert "(بدون متن)" in body, "به‌جای متنِ صادقانه چیزی جعل شده"


def t_o_handle_files_routes_and_acks_in_one_gesture():
    os.environ[capture.FLAG_CAPTURE] = "1"
    calls = []
    fake = SimpleNamespace(add=lambda leg, text, now=None:
                           calls.append(leg) or {"id": "TASK-1"})
    try:
        r = capture.handle(_msg("سایت زیمان را بررسی کن", 401),
                           deps={"now": NOW, "leg_tasks_mod": fake})
        again = capture.handle(_msg("سایت زیمان را بررسی کن", 401),
                               deps={"now": NOW + 5, "leg_tasks_mod": fake})
    finally:
        os.environ.pop(capture.FLAG_CAPTURE, None)
    assert r["kind"] == "task" and r["routed"] == "leg-task", r
    assert calls == ["ziman"], calls
    assert again.get("dup") and "تکراری" in again["ack"], again
    assert calls == ["ziman"], "پیامِ تکراری دوباره Task ساخت — idempotent نیست"


def t_p_acks_are_one_line_short_and_persian_digit():
    os.environ[capture.FLAG_CAPTURE] = "1"
    acks = []
    try:
        for i, text in enumerate(("هزینه خرید رنگ ۴۵ دلار",
                                  "ایده: بات معرفی آثار برای گالری",
                                  "امروز هوا در سیدنی عالی بود")):
            acks.append(capture.handle(_msg(text, 501 + i),
                                       deps={"now": NOW})["ack"])
    finally:
        os.environ.pop(capture.FLAG_CAPTURE, None)
    for a in acks:
        assert a and "\n" not in a, a
        assert len(a) <= 120, (len(a), a)
        assert "ثبت شد" in a, a


def t_q_flag_off_means_capture_never_touches_anything():
    os.environ.pop(capture.FLAG_CAPTURE, None)
    before = _raw_count()
    r = capture.handle(_msg("سایت زیمان را بررسی کن", 601), deps={"now": NOW})
    assert r["handled"] is False and r["ack"] == "", r
    assert _raw_count() == before, "فلگِ خاموش ولی فایل نوشته شد"


def t_r_capture_writes_only_inside_the_isolated_vault():
    kr = capture.classify("امروز هوا در سیدنی عالی بود")
    got = capture.file_to_vault(kr, "امروز هوا در سیدنی عالی بود",
                                msg_meta=_meta(701), now=NOW)
    p = str(Path(got["path"]).resolve()).lower()
    assert p.startswith(str(Path(ENV["ORG_ROOT"]).resolve()).lower()), p
    live = str((harness.REAL_VAULT / "10 - Telegram processing").resolve()).lower()
    assert not p.startswith(live), f"نوشتن روی درختِ زنده: {p}"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_tg_capture: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
