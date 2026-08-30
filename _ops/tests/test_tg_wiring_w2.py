"""test_tg_wiring_w2 — سیم‌کشیِ سریالِ موج ۲ (منشورِ TG-UI ۲۰۲۶-۰۷-۳۱).

پنج لِین به مرکزِ واقعی وصل شدند و این فایل **خودِ سیم** را می‌سنجد، نه
ماژول‌ها را (هر ماژول suite ِ خودش را دارد):

  D  capture ِ یک‌ژسته در handle_update — با درزِ عمدیِ رأی ۱۹ (چتِ آزاد
     زنده می‌ماند: نوتِ سادهٔ kind=note هرگز capture نمی‌شود).
  E  reminders + brief سوارِ Center.beat + دکمه‌های rm:done/rm:snz.
  F  دکمهٔ Mini App در کیبوردِ خانه — فقط URL ِ تازهٔ https.
  H  weekly_review ِ شنبه + تحویلِ بودجهٔ سؤال و جوابِ ریپلای.
  و رسیدِ بوتِ ضدِ فراموشی (PID + نسخه) در ensure_setup.

همه با Center ِ واقعی + FakeClient (الگوی test_tg_center) — صفر شبکه؛
فلگ‌ها با os.environ داخلِ هر سنجه و با try/finally برمی‌گردند.
"""
import json
import os
import shutil
import sys
import types
from datetime import datetime
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))

import harness
ENV = harness.setup("tg-wiring-w2")

sys.path.insert(0, str(_HERE.parent / "telegram_center"))

import opslib   # noqa: E402
import center   # noqa: E402

CFG_PATH = opslib.STATE_DIR / "telegram" / "center-config.json"
RAW_DIR = Path(ENV["ORG_ROOT"]) / "10 - Telegram processing" / "Raw"
OWNER = 777


class FakeClient:
    """الگوی test_tg_center + owner_chat_id (گیتِ سطح/رسیدها لازمش دارند)."""

    def __init__(self, wired=True, owner_id=OWNER):
        self._is_wired = wired
        self.owner_id = owner_id
        self.owner_chat_id = owner_id
        self.calls: list = []
        self._next_mid = 100

    def wired(self):
        return self._is_wired

    def send(self, text, *, topic_id=None, keyboard=None, chat_id=None,
             pin=False, stream=None):
        self.calls.append(("send", {"text": text, "topic_id": topic_id,
                                    "keyboard": keyboard, "chat_id": chat_id,
                                    "pin": pin}))
        self._next_mid += 1
        return self._next_mid

    def edit(self, message_id, text, keyboard=None, chat_id=None):
        self.calls.append(("edit", {"message_id": message_id, "text": text}))
        return True

    def pin_message(self, message_id, chat_id=None):
        return True

    def create_topic(self, name, chat_id=None):
        self._next_mid += 1
        return self._next_mid

    def set_commands(self, commands, scope=None):
        return True

    def delete_commands(self, scope=None):
        return True

    def answer_callback(self, callback_id, text=""):
        self.calls.append(("answer", {"id": callback_id, "text": text}))
        return True

    def is_owner(self, update):
        frm = ((update.get("message") or {}).get("from")
               or (update.get("callback_query") or {}).get("from") or {})
        return frm.get("id") == self.owner_id

    def named(self, kind):
        return [c for k, c in self.calls if k == kind]


def _render():
    m = types.SimpleNamespace()
    m.collect_feeds = lambda *a, **k: {}
    m.render_status = lambda feeds: "STATUS"
    m.render_leg_digest = lambda leg, data: ""
    return m


class Clock:
    def __init__(self, t):
        self.t = float(t)

    def __call__(self):
        return self.t


def _reset():
    shutil.rmtree(opslib.STATE_DIR / "telegram", ignore_errors=True)
    shutil.rmtree(opslib.STATE_DIR / "reminders", ignore_errors=True)
    shutil.rmtree(RAW_DIR, ignore_errors=True)


def _dm_msg(mid, text=None, **extra):
    m = {"message_id": mid, "from": {"id": OWNER},
         "chat": {"id": OWNER, "type": "private"}}
    if text is not None:
        m["text"] = text
    m.update(extra)
    return {"update_id": mid, "message": m}


def _flag(name, val="1"):
    os.environ[name] = val


def _unflag(*names):
    for n in names:
        os.environ.pop(n, None)


# ── لِین D: capture ─────────────────────────────────────────────────────────
def t_d1_a_media_dm_is_captured_acked_and_never_falls_to_the_console():
    _reset()
    fc = FakeClient()
    c = center.Center(client=fc, clock=Clock(1000.0), render_mod=_render())
    _flag("OCTOPUS_TG_CAPTURE")
    try:
        r = c.handle_update(_dm_msg(501, caption="نمای کار",
                                    photo=[{"file_id": "PH1"}]))
    finally:
        _unflag("OCTOPUS_TG_CAPTURE")
    assert r is not None and r.get("kind") == "capture", f"capture نشد: {r}"
    sends = fc.named("send")
    assert len(sends) == 1, f"غیر از ack چیز دیگری رفت (fallthrough؟): {sends}"
    assert "ثبت شد" in sends[0]["text"], sends[0]["text"]
    notes = list(RAW_DIR.rglob("*.md"))
    assert notes, "هیچ نوتی در vault نوشته نشد"
    body = notes[0].read_text("utf-8")
    assert "message_id: 501" in body and f"chat_id: {OWNER}" in body, body


def t_d2_plain_chat_text_is_not_captured_and_reaches_the_ask_path():
    _reset()
    fc = FakeClient()
    c = center.Center(client=fc, clock=Clock(1000.0), render_mod=_render())
    _flag("OCTOPUS_TG_CAPTURE")
    try:
        r = c.handle_update(_dm_msg(502, text="سلام، حالت چطوره؟"))
    finally:
        _unflag("OCTOPUS_TG_CAPTURE")
    assert r is not None and r.get("kind") != "capture", \
        f"چتِ آزاد capture شد — رأی ۱۹ شکست: {r}"
    assert not list(RAW_DIR.rglob("*.md")), \
        "چتِ آزاد در vault نوشته شد — درزِ عمدی سوراخ است"
    assert fc.named("send"), "به مسیرِ گفتگو نرسید — هیچ جوابی نرفت"


def t_d3_sabt_prefix_expense_is_captured_and_dedup_is_idempotent():
    _reset()
    fc = FakeClient()
    c = center.Center(client=fc, clock=Clock(1000.0), render_mod=_render())
    _flag("OCTOPUS_TG_CAPTURE")
    try:
        r1 = c.handle_update(_dm_msg(503, text="ثبت: خرید رنگ ۵۰ دلار"))
        r2 = c.handle_update(_dm_msg(503, text="ثبت: خرید رنگ ۵۰ دلار"))
    finally:
        _unflag("OCTOPUS_TG_CAPTURE")
    assert r1 and r1.get("capture_kind") == "expense" \
        and r1.get("routed") == "expense-line", f"هزینه نشد: {r1}"
    assert any("هزینه" in s["text"] for s in fc.named("send")), \
        "ack ِ هزینه نرفت"
    assert r2 and r2.get("dup") is True, f"تکراری دوباره ثبت شد: {r2}"
    notes = list(RAW_DIR.rglob("*.md"))
    assert len(notes) == 1, f"idempotency شکست — {len(notes)} فایل"


def t_d4_group_system_mirror_rooms_never_capture_even_with_the_flag_on():
    """بازبینی ۰۷-۳۱ (BLOCKER 1): اتاق‌های system/mirror ِ گروه هم
    core_conversation طبقه‌بندی می‌شوند — ولی پیامشان هرگز نباید بایگانی شود؛
    مسیرِ آینه/ask ادامه می‌یابد. بدونِ گیتِ سطح، «ثبت:» در اتاقِ آینه یک
    نوتِ vault می‌ساخت."""
    _reset()
    GROUP = -100999
    CFG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CFG_PATH.write_text(json.dumps(
        {"chat_id": GROUP, "topics": {"system": 77, "mirror": 78}},
        ensure_ascii=False), "utf-8")
    fc = FakeClient()
    c = center.Center(client=fc, clock=Clock(1000.0), render_mod=_render())
    _flag("OCTOPUS_TG_CAPTURE")
    try:
        for thread in (77, 78):
            r = c.handle_update({"update_id": 700 + thread, "message": {
                "message_id": 700 + thread, "from": {"id": OWNER},
                "chat": {"id": GROUP, "type": "supergroup"},
                "message_thread_id": thread,
                "text": "ثبت: خرید رنگ ۵۰ دلار"}})
            assert not (isinstance(r, dict) and r.get("kind") == "capture"), \
                f"اتاقِ گروه (thread={thread}) capture شد: {r}"
    finally:
        _unflag("OCTOPUS_TG_CAPTURE")
    assert not list(RAW_DIR.rglob("*.md")), \
        "پیامِ اتاقِ گروه در vault بایگانی شد — گیتِ سطح سوراخ است"


def t_d5_a_vault_question_reaches_ask_vault_never_capture():
    """بازبینی ۰۷-۳۱ (BLOCKER 4): «از والت بپرس دربارهٔ ماینینگ چی دارم؟» —
    طبقه‌بندِ capture آن را task می‌بیند («بپرس») و بدونِ گیتِ vault-intent
    بایگانی‌اش می‌کرد؛ باید به ask_vault برسد."""
    _reset()
    import leg_tasks as _lt
    # دو شکل: با ؟ (که گیتِ سؤال هم می‌گیرد) و **بدونِ ؟** — دومی فقط با
    # گیتِ vault-intent نجات می‌یابد (وگرنه «بپرس» → task → بایگانی)؛ جهشِ
    # حذفِ گیتِ vault با شکلِ اول زنده می‌مانْد (گیتِ ج پوششش می‌داد).
    for mid, q in ((801, "از والت بپرس دربارهٔ ماینینگ چی دارم؟"),
                   (805, "از والت بپرس دربارهٔ ماینینگ")):
        assert center.Center._vault_intent(q) is True, ("پیش‌فرضِ تست", q)
    assert not (_lt.is_question("از والت بپرس دربارهٔ ماینینگ")
                or "از والت بپرس دربارهٔ ماینینگ".endswith(("؟", "?"))), \
        "پیش‌فرضِ تست: شکلِ دوم نباید سؤالِ نحوی باشد"
    fc = FakeClient()
    c = center.Center(client=fc, clock=Clock(1000.0), render_mod=_render())
    _flag("OCTOPUS_TG_CAPTURE")
    _flag("OCTOPUS_TG_ASK_VAULT")
    try:
        for mid, q in ((801, "از والت بپرس دربارهٔ ماینینگ چی دارم؟"),
                       (805, "از والت بپرس دربارهٔ ماینینگ")):
            r = c.handle_update(_dm_msg(mid, text=q))
            assert not (isinstance(r, dict) and r.get("kind") == "capture"), \
                f"سؤالِ vault بایگانی شد ({q!r}): {r}"
    finally:
        _unflag("OCTOPUS_TG_CAPTURE", "OCTOPUS_TG_ASK_VAULT")
    assert not list(RAW_DIR.rglob("*.md")), \
        "سؤالِ vault در Raw نوشته شد — به‌جای ask_vault به بایگانی رفت"


def t_d6_questions_belong_to_the_chat_brain_but_sabt_still_captures():
    """بازبینی ۰۷-۳۱ (BLOCKER 4): سؤال (is_question یا ؟) هرگز capture نمی‌شود
    — مگر پیشوندِ صریحِ «ثبت:» که همیشه capture است (استثنای مصوب)."""
    _reset()
    fc = FakeClient()
    c = center.Center(client=fc, clock=Clock(1000.0), render_mod=_render())
    _flag("OCTOPUS_TG_CAPTURE")
    try:
        # «چطور …» = is_question ِ leg_tasks؛ طبقه‌بند آن را lead می‌دید
        r1 = c.handle_update(_dm_msg(802, text="چطور لید بیشتر بگیرم"))
        # علامتِ ؟ ِ صریح روی متنی که طبقه‌بند task می‌دید
        r2 = c.handle_update(_dm_msg(803, text="باید مدارک بیمه را ببرم؟"))
        assert not (isinstance(r1, dict) and r1.get("kind") == "capture"), r1
        assert not (isinstance(r2, dict) and r2.get("kind") == "capture"), r2
        assert not list(RAW_DIR.rglob("*.md")), "سؤال در vault بایگانی شد"
        # استثنای صریح: «ثبت:» حتی روی جملهٔ سؤالی capture می‌شود
        r3 = c.handle_update(_dm_msg(804, text="ثبت: باید مدارک بیمه را ببرم؟"))
        assert r3 and r3.get("kind") == "capture", f"«ثبت:» دیگر capture نمی‌شود: {r3}"
        assert list(RAW_DIR.rglob("*.md")), "نوتِ «ثبت:» نوشته نشد"
    finally:
        _unflag("OCTOPUS_TG_CAPTURE")


# ── لِین E: یادآورها ────────────────────────────────────────────────────────
def t_e1_reminder_beat_delivers_due_reminder_with_rm_buttons():
    _reset()
    import reminders as rm
    now = datetime(2026, 7, 31, 8, 0).timestamp()
    it = rm.add("زنگ بزن به علی", due_ts=now - 60, scope="dm", now=now - 3600)
    assert it, "add شکست"
    fc = FakeClient()
    c = center.Center(client=fc, clock=Clock(now), render_mod=_render())
    _flag("OCTOPUS_TG_REMINDERS")
    try:
        c.beat()
    finally:
        _unflag("OCTOPUS_TG_REMINDERS")
    fired = [s for s in fc.named("send") if "یادآوری" in s["text"]]
    assert fired, "یادآوریِ سررسیده تحویل نشد"
    cds = [b.get("callback_data") for row in (fired[0]["keyboard"] or [])
           for b in row]
    assert any(str(cd).startswith("rm:done:") for cd in cds) \
        and any(str(cd).startswith("rm:snz:") for cd in cds), \
        f"دکمه‌های rm روی کارت نیستند: {cds}"


def t_e2_rm_done_tap_marks_done_answers_and_edits_the_card():
    _reset()
    import reminders as rm
    now = datetime(2026, 7, 31, 8, 0).timestamp()
    it = rm.add("زنگ بزن به علی", due_ts=now + 3600, scope="dm", now=now)
    rid = it["id"]
    fc = FakeClient()
    c = center.Center(client=fc, clock=Clock(now), render_mod=_render())
    _flag("OCTOPUS_TG_REMINDERS")
    try:
        r = c.handle_update({"update_id": 9, "callback_query": {
            "id": "cbq9", "from": {"id": OWNER}, "data": f"rm:done:{rid}",
            "message": {"message_id": 61,
                        "chat": {"id": OWNER, "type": "private"}}}})
        # دبل‌تاپ: بارِ دوم هم پاسخ می‌گیرد و state خراب نمی‌شود
        r2 = c.handle_update({"update_id": 10, "callback_query": {
            "id": "cbq10", "from": {"id": OWNER}, "data": f"rm:done:{rid}",
            "message": {"message_id": 61,
                        "chat": {"id": OWNER, "type": "private"}}}})
    finally:
        _unflag("OCTOPUS_TG_REMINDERS")
    assert r and r.get("kind") == "reminder" and r.get("ok"), r
    assert r2 and r2.get("kind") == "reminder", r2
    assert not [x for x in rm.list_open() if x["id"] == rid], \
        "بعد از done هنوز باز است"
    answers = fc.named("answer")
    assert answers and any("انجام شد" in a["text"] for a in answers), answers
    assert any(e["message_id"] == 61 for e in fc.named("edit")), \
        "کارتِ یادآوری به وضعِ نو ویرایش نشد"


# ── لِین E: بریف ────────────────────────────────────────────────────────────
def t_e3_morning_brief_fires_once_through_beat_and_persists_cursor():
    _reset()
    clk = Clock(datetime(2026, 7, 31, 7, 31).timestamp())
    fc = FakeClient()
    c = center.Center(client=fc, clock=clk, render_mod=_render())
    _flag("OCTOPUS_TG_BRIEF")
    try:
        c.beat()
        briefs = [s for s in fc.named("send") if "بریف صبح" in s["text"]]
        assert briefs, "بریفِ صبح در ۰۷:۳۱ شلیک نشد"
        cfg = json.loads(CFG_PATH.read_text("utf-8"))
        assert cfg.get("last_morning_day") == "2026-07-31", \
            f"cursor ِ بریف persist نشد: {cfg.get('last_morning_day')!r}"
        clk.t += 60.0
        c.beat()
        assert len([s for s in fc.named("send")
                    if "بریف صبح" in s["text"]]) == 1, \
            "بریف دوبار در یک روز رفت — persistence شکست"
    finally:
        _unflag("OCTOPUS_TG_BRIEF")


# ── لِین H: مرورِ هفتگی ─────────────────────────────────────────────────────
def t_h1_weekly_review_fires_saturday_morning_once():
    _reset()
    import weekly_review as wr
    now = datetime(2026, 8, 1, 9, 0).timestamp()          # شنبهٔ میلادی
    assert datetime.fromtimestamp(now).weekday() == 5
    clk = Clock(now)
    fc = FakeClient()
    c = center.Center(client=fc, clock=clk, render_mod=_render())
    _flag("OCTOPUS_TG_WEEKLY_REVIEW")
    try:
        c.beat()
        revs = [s for s in fc.named("send") if "مرور هفتگی" in s["text"]]
        assert revs, "مرورِ هفتگی شنبه صبح شلیک نشد"
        cfg = json.loads(CFG_PATH.read_text("utf-8"))
        assert cfg.get("last_weekly_review") == wr._week_key(now), \
            f"cursor ِ هفته persist نشد: {cfg.get('last_weekly_review')!r}"
        clk.t += 300.0
        c.beat()
        assert len([s for s in fc.named("send")
                    if "مرور هفتگی" in s["text"]]) == 1, \
            "مرور دوبار در یک هفته رفت"
    finally:
        _unflag("OCTOPUS_TG_WEEKLY_REVIEW")


# ── لِین H: بودجهٔ سؤال ─────────────────────────────────────────────────────
def t_h2_qbudget_question_is_delivered_once_and_reply_records_answer():
    _reset()
    import question_budget as qb
    now = datetime(2026, 7, 31, 10, 0).timestamp()
    qp = qb._path()
    qp.parent.mkdir(parents=True, exist_ok=True)
    qp.write_text(json.dumps({
        "week": qb._week_key(now), "used": 0, "seq": 1,
        "queue": [{"id": "Q-1", "q": "هدف روزانه چند لید باشد؟",
                   "context": "", "goal": "", "created": now,
                   "asked": False, "asked_ts": None,
                   "answer": None, "answered_ts": None}]},
        ensure_ascii=False), "utf-8")
    clk = Clock(now)
    fc = FakeClient()
    c = center.Center(client=fc, clock=clk, render_mod=_render())
    _flag("OCTOPUS_TG_QBUDGET")
    _flag("OCTOPUS_TG_CAPTURE")     # عمداً روشن: ریپلایِ جواب نباید capture شود
    try:
        c.beat()
        qs = [s for s in fc.named("send") if "سؤالِ اختاپوس" in s["text"]]
        assert qs and "Q-1" in qs[0]["text"], "سؤال تحویل نشد"
        assert qb.used(now) == 1, "mark_asked بعد از تحویل صدا نخورد"
        clk.t += 300.0
        c.beat()
        assert len([s for s in fc.named("send")
                    if "سؤالِ اختاپوس" in s["text"]]) == 1, \
            "سؤال دوباره تحویل شد — بودجه دوبار می‌سوزد"
        # جوابِ مالک = ریپلای به پیامِ سؤال (متنی که capture می‌توانست ببلعد)
        r = c.handle_update(_dm_msg(
            601, text="باید ۵ تا لید در روز بگیریم",
            reply_to_message={"message_id": 101,
                              "text": "❓ Q-1 — سؤالِ اختاپوس\n"
                                      "هدف روزانه چند لید باشد؟"}))
        assert r and r.get("kind") == "qbudget-answer" and r.get("recorded"), r
        d = json.loads(qp.read_text("utf-8"))
        assert d["queue"][0]["answer"] == "باید ۵ تا لید در روز بگیریم", d
    finally:
        _unflag("OCTOPUS_TG_QBUDGET", "OCTOPUS_TG_CAPTURE")


def t_h3_qbudget_without_owner_dm_skips_the_beat_never_leaks_to_group():
    """بازبینی ۰۷-۳۱ (wiring-4): owner_chat_id ِ غایب/falsy ⇒ این ضربان اصلاً
    ارسال نمی‌شود — chat_id=None به chat ِ پیش‌فرضِ client (گروه/General)
    می‌افتاد. بودجه هم نباید بسوزد (mark_asked فقط بعدِ تحویلِ واقعی)."""
    _reset()
    import question_budget as qb
    now = datetime(2026, 7, 31, 11, 0).timestamp()
    qp = qb._path()
    qp.parent.mkdir(parents=True, exist_ok=True)
    qp.write_text(json.dumps({
        "week": qb._week_key(now), "used": 0, "seq": 1,
        "queue": [{"id": "Q-9", "q": "سؤالِ بی‌مقصد؟", "context": "",
                   "goal": "", "created": now, "asked": False,
                   "asked_ts": None, "answer": None, "answered_ts": None}]},
        ensure_ascii=False), "utf-8")
    fc = FakeClient()
    fc.owner_chat_id = None            # DM ِ مالک در دسترس نیست
    c = center.Center(client=fc, clock=Clock(now), render_mod=_render())
    _flag("OCTOPUS_TG_QBUDGET")
    try:
        c.beat()
    finally:
        _unflag("OCTOPUS_TG_QBUDGET")
    assert not [s for s in fc.named("send") if "سؤالِ اختاپوس" in s["text"]], \
        "سؤال بدونِ DM ِ مالک ارسال شد — نشتِ General"
    assert qb.used(now) == 0, "بودجه بدونِ تحویلِ واقعی سوخت"


# ── لِین F: دکمهٔ Mini App ──────────────────────────────────────────────────
def t_f1_miniapp_button_only_appears_with_a_fresh_https_url_file():
    _reset()
    fc = FakeClient()
    c = center.Center(client=fc, clock=Clock(1000.0), render_mod=_render())

    def _btns():
        return [b for row in c._home_keyboard() for b in row]

    p = opslib.STATE_DIR / "telegram" / "miniapp-url.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    # فلگ خاموش ⇒ هرگز؛ فلگ روشن ولی بی‌فایل ⇒ هرگز
    assert not any("web_app" in b for b in _btns())
    _flag("OCTOPUS_TG_MINIAPP")
    try:
        assert not any("web_app" in b for b in _btns()), "بی‌فایل دکمه ساخت"
        # فایلِ تازهٔ https ⇒ دکمه
        p.write_text(json.dumps({"url": "https://x.trycloudflare.com",
                                 "started": 1, "pid": 1}), "utf-8")
        webs = [b for b in _btns() if "web_app" in b]
        assert webs and webs[0]["web_app"]["url"].startswith("https://"), \
            f"دکمهٔ داشبورد ساخته نشد: {webs}"
        web_url = webs[0]["web_app"]["url"]
        versioned = "?v=" in web_url or "&v=" in web_url
        assert versioned, "URL ریشهٔ WebView نسخه ندارد؛ Telegram می‌تواند HTML کهنه را باز کند"
        # url خالی (tunnel ایستاده) ⇒ بی‌دکمه
        p.write_text(json.dumps({"url": "", "started": 1, "pid": 1}), "utf-8")
        assert not any("web_app" in b for b in _btns()), "URL ِ مرده پیشنهاد شد"
        # http ِ ناامن ⇒ بی‌دکمه
        p.write_text(json.dumps({"url": "http://x.y", "pid": 1}), "utf-8")
        assert not any("web_app" in b for b in _btns()), "http پذیرفته شد"
        # فایلِ کهنه (>۲۴h) ⇒ بی‌دکمه
        p.write_text(json.dumps({"url": "https://x.trycloudflare.com"}),
                     "utf-8")
        import time as _t
        os.utime(p, (_t.time() - 90000, _t.time() - 90000))
        assert not any("web_app" in b for b in _btns()), "فایلِ کهنه پذیرفته شد"
    finally:
        _unflag("OCTOPUS_TG_MINIAPP")


# ── رسیدِ بوت ───────────────────────────────────────────────────────────────
def t_g1_boot_receipt_is_one_line_with_pid_and_version_once_per_process():
    _reset()
    fc = FakeClient()
    c = center.Center(client=fc, clock=Clock(1000.0), render_mod=_render())
    c.ensure_setup()
    rec = [s for s in fc.named("send") if "بیدار شدم" in s["text"]]
    assert rec, "رسیدِ بوت فرستاده نشد"
    txt = rec[0]["text"]
    # ۰۸-۰۴: خطِ دومِ شمارندهٔ ری‌استارتِ روزانه اضافه شد؛ رسید حالا دو خط
    # است — هر خط را جدا می‌سنجیم، نه کلِ متن را یک‌خطی.
    lines = txt.strip().split("\n")
    assert len(lines) == 2, f"رسید باید دقیقاً دو خط باشد: {txt!r}"
    assert str(os.getpid()) in lines[0], f"PID در خطِ اولِ رسید نیست: {txt!r}"
    assert "نسخه" in lines[0], f"نسخه در خطِ اولِ رسید نیست: {txt!r}"
    assert "ری‌استارتِ امروز" in lines[1], \
        f"شمارندهٔ ری‌استارت در خطِ دومِ رسید نیست: {txt!r}"
    # همان پروسه، بوتِ دوم ⇒ رسیدِ دوم نه (dedupe با pid در config)
    c.ensure_setup()
    assert len([s for s in fc.named("send")
                if "بیدار شدم" in s["text"]]) == 1, "رسیدِ بوت رگبار شد"
    # کلاینتِ بی‌owner (الگوی fakeهای قدیمی) ⇒ صفر رسید، صفر crash
    _reset()
    fc2 = FakeClient()
    del fc2.owner_chat_id
    c2 = center.Center(client=fc2, clock=Clock(1000.0), render_mod=_render())
    c2.ensure_setup()
    assert not [s for s in fc2.named("send") if "بیدار شدم" in s["text"]]


def _run():
    ok = fail = 0
    for name, fn in sorted(globals().items()):
        if not name.startswith("t_") or not callable(fn):
            continue
        try:
            fn()
            print(f"  ✅ {name}")
            ok += 1
        except AssertionError as e:
            print(f"  ❌ {name}: {e}")
            fail += 1
        except Exception as e:  # noqa: BLE001
            print(f"  ❌ {name}: {type(e).__name__}: {e}")
            fail += 1
    total = ok + fail
    mark = "✅" if fail == 0 else "❌"
    print(f"\n{mark} test_tg_wiring_w2: {ok}/{total}")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(_run())
