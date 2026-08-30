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


# ── ویس → نوتِ ساختاریافته (منشور رأی ۹) ────────────────────────────────────
# صفر شبکه، صفر موتور: دانلودر و موتور تزریق می‌شوند. مسیرِ زیرِ آزمون همان
# مسیرِ تولیدی است (capture._voice_transcribe)، نه یک نسخهٔ موازی.
_VOICE_MSG_ID = [900]


def _voice_msg(**voice):
    _VOICE_MSG_ID[0] += 1
    v = {"file_id": "AF-voice-1", "duration": 12}
    v.update(voice)
    return {"message_id": _VOICE_MSG_ID[0], "chat": {"id": 777}, "voice": v}


class _Dl:
    """دانلودرِ جعلی: فایلِ صوت را واقعاً می‌سازد تا حذفش قابلِ‌سنجش باشد."""

    def __init__(self, ok=True):
        self.ok = ok
        self.paths = []

    def __call__(self, file_id, dest):
        self.paths.append(dest)
        if not self.ok:
            return False
        Path(dest).write_bytes(b"OggS-fake")
        return True


def _tr_ok(text, engine="faster-whisper", secs=1.5):
    def _fn(path, lang="fa", duration_s=None):
        return {"ok": True, "text": text, "engine": engine, "secs": secs,
                "reason": ""}
    return _fn


def _voice_deps(dl, tr_fn, *, avail=True, **extra):
    d = {"now": NOW, "download_fn": dl, "transcribe_fn": tr_fn,
         "transcribe_available": lambda: (avail, "faster-whisper"
                                          if avail else "no-backend")}
    d.update(extra)
    return d


def _run_voice(deps, msg=None, flag=True):
    os.environ[capture.FLAG_CAPTURE] = "1"
    if flag:
        os.environ[capture.FLAG_VOICE] = "1"
    else:
        os.environ.pop(capture.FLAG_VOICE, None)
    try:
        return capture.handle(msg or _voice_msg(), deps=deps)
    finally:
        os.environ.pop(capture.FLAG_CAPTURE, None)
        os.environ.pop(capture.FLAG_VOICE, None)


def t_s_voice_becomes_a_structured_note_not_a_raw_transcript():
    """رأی ۹: عنوان از اولین بندِ معنادار · خطِ خلاصه · متنِ کامل زیرِ سرتیتر."""
    dl = _Dl()
    text = ("فردا ساعت ۹ باید به گالری زیمان زنگ بزنم. "
            "قرار بود قیمت قاب را بگویند")
    r = _run_voice(_voice_deps(dl, _tr_ok(text)))
    assert r["handled"] and r.get("transcript") is True, r
    body = Path(r["path"]).read_text("utf-8")
    assert body.startswith("---"), body[:40]
    assert "# فردا ساعت ۹ باید به گالری زیمان زنگ بزنم" in body, body
    assert "**خلاصه:**" in body, body
    assert "## متنِ ویس" in body, body
    assert text in body, "متنِ کامل زیرِ سرتیترِ transcript نیست"
    # خطِ خلاصه واقعاً ساختار دارد (نوع/پا/زمان/طول/موتور)
    line = [l for l in body.splitlines() if l.startswith("**خلاصه:**")][0]
    for token in ("نوع:", "پا:", "زمان:", "طول:", "موتور:"):
        assert token in line, (token, line)


def t_t_voice_frontmatter_keeps_file_id_duration_and_adds_transcript_keys():
    dl = _Dl()
    r = _run_voice(_voice_deps(dl, _tr_ok("یادم بنداز فردا رنگ بخرم")),
                   msg=_voice_msg(file_id="AF-front", duration=41))
    fm = _front(r["path"])
    assert fm["file_id"] == "AF-front" and fm["duration"] == "41", fm
    assert fm["transcribed_by"] == "faster-whisper", fm
    assert fm["transcript_secs"] == "1.5", fm
    for key in ("type", "project", "status", "tags", "created", "updated"):
        assert key in fm, (key, fm)


def t_u_transcript_is_classified_and_routed_exactly_like_text():
    """ویس هم کار/لید/هزینه می‌شود — همان درختِ تصمیمِ متن (§۴)."""
    dl = _Dl()
    calls = []
    fake = SimpleNamespace(add=lambda leg, text, now=None:
                           calls.append((leg, text)) or {"id": "T-1"})
    r = _run_voice(_voice_deps(dl, _tr_ok("سایت زیمان را بررسی کن"),
                               leg_tasks_mod=fake))
    assert r["kind"] == "task" and r["routed"] == "leg-task", r
    assert calls and calls[0][0] == "ziman", calls
    assert "ویس متن شد" in r["ack"] and "زیمان" in r["ack"], r

    leads = []
    r2 = _run_voice(_voice_deps(_Dl(),
                                _tr_ok("مشتری جدید برای نقاشی 0412345678"),
                                lead_submit_fn=leads.append))
    assert r2["kind"] == "lead" and r2["routed"] == "lead-inbox", r2
    assert leads and leads[0]["channel"] == "telegram_manual", leads
    assert leads[0]["phone"], "تلفنِ لیدِ ویس گم شد"

    r3 = _run_voice(_voice_deps(_Dl(), _tr_ok("هزینه خرید رنگ ۴۵ دلار")))
    assert r3["kind"] == "expense" and r3["routed"] == "expense-line", r3


def t_v_the_audio_file_never_survives_and_never_touches_the_vault():
    """صوت در temp دانلود می‌شود و بعدِ متن‌سازی پاک — نه در vault، نه در temp."""
    dl = _Dl()
    seen = {}

    def tr_fn(path, lang="fa", duration_s=None):
        seen["path"] = path
        seen["exists_during"] = Path(path).exists()
        seen["lang"] = lang
        seen["duration_s"] = duration_s
        return {"ok": True, "text": "سلام آرمین", "engine": "faster-whisper",
                "secs": 0.4, "reason": ""}

    before = _raw_count()
    r = _run_voice(_voice_deps(dl, tr_fn), msg=_voice_msg(duration=33))
    assert r.get("transcript") is True, r
    assert seen["exists_during"] is True, "موتور فایلِ صوت را ندید"
    assert seen["lang"] == "fa" and seen["duration_s"] == 33, seen
    assert not Path(seen["path"]).exists(), "فایلِ صوت پاک نشد"
    assert not Path(seen["path"]).parent.exists(), "دایرکتوریِ موقت جا ماند"
    vault = str(Path(ENV["ORG_ROOT"]).resolve()).lower()
    assert not str(Path(seen["path"]).resolve()).lower().startswith(vault), \
        "صوت داخلِ vault دانلود شد"
    assert _raw_count() == before + 1, "دقیقاً یک نوت باید ساخته شود"
    assert not list(RAW_DIR.glob("*.oga")), "باینری داخلِ vault ماند"


def t_w_every_failure_branch_is_honest_and_says_why():
    """no-backend / download-failed / too-long / موتورِ منفجر — همه با دلیل.

    نوتِ صادقِ file_id/duration نوشته می‌شود، ولی **هیچ transcript ای** نه."""
    cases = [
        # (deps, دلیلِ منتظره، تکه‌ای از ack)
        (_voice_deps(_Dl(), _tr_ok("x"), avail=False), "no-backend",
         "موتورِ متن‌سازی نصب نیست"),
        (_voice_deps(_Dl(ok=False), _tr_ok("x")), "download-failed",
         "دانلودِ ویس نشد"),
        (_voice_deps(_Dl(), lambda p, lang="fa", duration_s=None:
                     {"ok": False, "text": "", "engine": "faster-whisper",
                      "secs": 0.0, "reason": "too-long"}), "too-long",
         "بلندتر از سقف"),
        (_voice_deps(_Dl(), lambda p, lang="fa", duration_s=None:
                     {"ok": True, "text": "   ", "engine": "faster-whisper",
                      "secs": 0.1, "reason": ""}), "empty-transcript",
         "چیزی شنیده نشد"),
        ({"now": NOW}, "no-downloader", "دانلودر غایب"),
    ]
    for deps, reason, ack_bit in cases:
        r = _run_voice(deps)
        assert r["handled"] and r.get("transcript") is False, (reason, r)
        assert r["reason"] == reason, (reason, r)
        assert ack_bit in r["ack"], (reason, r["ack"])
        assert "ویس ثبت شد" in r["ack"], r["ack"]
        body = Path(r["path"]).read_text("utf-8")
        assert "## متنِ ویس" not in body, (reason, "سرتیترِ transcript بی‌متن!")
        assert "(بدون متن)" in body, (reason, body)
        assert f"- متن‌سازی: ناموفق ({reason})" in body, (reason, body)
        assert "transcribed_by" not in _front(r["path"]), \
            (reason, "کلیدِ متن‌سازی روی نوتِ بی‌متن نشست")


def t_x_a_failed_backend_can_never_smuggle_text_into_the_vault():
    """گاردِ ضدِ جعل (دندان‌دار): آداپترِ بدقلق ok=False می‌دهد **ولی متن هم**.

    این دقیقاً همان حالتی است که یک روز پیش می‌آید (کتابخانه‌ای که در شکست
    متنِ نیم‌کاره برمی‌گرداند). آن متن هرگز نباید به نوت برسد.
    جهش (`if not res.get("ok"):` → `if False:`) این تست را قرمز می‌کند."""
    fake_text = "این جملهٔ کاملاً ساختگی است"

    def liar(path, lang="fa", duration_s=None):
        return {"ok": False, "text": fake_text, "engine": "faster-whisper",
                "secs": 0.2, "reason": "no-backend"}

    r = _run_voice(_voice_deps(_Dl(), liar))
    assert r.get("transcript") is False and r["reason"] == "no-backend", r
    body = Path(r["path"]).read_text("utf-8")
    assert fake_text not in body, "متنِ جعلیِ یک شکست وارد vault شد"
    assert fake_text not in r["ack"], r["ack"]
    assert "(بدون متن)" in body, body


def t_x2_voice_flag_off_keeps_yesterdays_behaviour_byte_for_byte():
    """فلگِ خاموش ⇒ نه دانلود، نه موتور، و همان ack ِ دیروز."""
    dl = _Dl()
    called = []
    r = _run_voice(_voice_deps(dl, lambda *a, **k: called.append(1) or {}),
                   flag=False)
    assert r["ack"].endswith("متن‌سازی هنوز نصب نیست"), r["ack"]
    assert dl.paths == [] and called == [], "فلگ خاموش ولی کار انجام شد"
    body = Path(r["path"]).read_text("utf-8")
    assert "متن‌سازی: ناموفق" not in body, "نوتِ flag-off نباید عوض شود"
    assert "[voice]" in body and "(بدون متن)" in body, body


def t_x4_voice_language_is_persian_by_default_and_overridable():
    """پیش‌فرض `fa` (زبانِ مالک)؛ env/deps می‌تواند `auto` کند."""
    seen = []

    def spy(path, lang="fa", duration_s=None):
        seen.append(lang)
        return {"ok": True, "text": "سلام", "engine": "e", "secs": 0.1,
                "reason": ""}

    _run_voice(_voice_deps(_Dl(), spy))
    os.environ["OCTOPUS_WHISPER_LANG"] = "auto"
    try:
        _run_voice(_voice_deps(_Dl(), spy))
    finally:
        os.environ.pop("OCTOPUS_WHISPER_LANG", None)
    _run_voice(_voice_deps(_Dl(), spy, voice_lang="en"))
    assert seen == ["fa", "auto", "en"], seen


def t_x3_voice_dedup_still_holds_after_transcription():
    """§۹ idempotent: همان message_id دوباره ⇒ نوتِ دوم نه، مسیریابیِ دوم نه."""
    msg = _voice_msg(file_id="AF-dup")
    calls = []
    fake = SimpleNamespace(add=lambda leg, text, now=None:
                           calls.append(leg) or {"id": "T-2"})
    first = _run_voice(_voice_deps(_Dl(), _tr_ok("سایت زیمان را بررسی کن"),
                                   leg_tasks_mod=fake), msg=msg)
    before = _raw_count()
    again = _run_voice(_voice_deps(_Dl(), _tr_ok("سایت زیمان را بررسی کن"),
                                   leg_tasks_mod=fake), msg=msg)
    assert first["routed"] == "leg-task" and calls == ["ziman"], (first, calls)
    assert again.get("dup") and "تکراری" in again["ack"], again
    assert _raw_count() == before, "ویسِ تکراری نوتِ دوم ساخت"
    assert calls == ["ziman"], "ویسِ تکراری دوباره Task ساخت"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_tg_capture: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
