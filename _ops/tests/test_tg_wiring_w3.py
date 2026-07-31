"""test_tg_wiring_w3 — سیم‌کشیِ سریالِ موج ۳ (شش لِینِ ۲۰۲۶-۰۸-۰۱).

این فایل **خودِ سیم** را می‌سنجد، نه ماژول‌ها را (هر ماژول suite ِ خودش را دارد):

  V  ویس: دانلودر از خودِ مرکز به capture می‌رسد و با موتورِ fake یک نوتِ
     ساختاریافته از هوکِ واقعیِ مرکز درمی‌آید.
  N  بودجهٔ اعلان (منشور §۳): سرریزِ قطع‌کننده → digest + اعلامِ صادقانه؛
     جریانِ محیطی هرگز بودجه نمی‌خورد؛ ارسالِ شکست‌خورده refund می‌شود و
     mark_asked فقط بعدِ تحویلِ واقعی.
  Q  تولیدِ سؤال در beat + تحویلِ همان-ضربان.
  L  یادگیرِ پنجرهٔ سکوت حداکثر روزی یک‌بار؛ رأیِ دستیِ مالک همیشه برنده.
  P  خطِ نبضِ tg_send_log در پالسِ ساعتی — با داده هست، بی‌داده نیست.
  M  گزینهٔ ② پنل به هندلرِ واقعی (owner_menu.handle_panel_choice) می‌رسد؛
     خطا عیناً نشان داده می‌شود.
  G  کارتِ دوره‌ایِ پای template-نما با guard_send بلاک می‌شود (با رسیدِ
     held)، رخدادِ واقعی رد می‌شود.
  D  امیترِ decision_gate: فلگ‌خاموش صفر اثر؛ فلگ‌روشن کارت با دکمه‌های
     handled؛ نشانگر فقط بعدِ تحویل جلو می‌رود.

همه با Center ِ واقعی + FakeClient (الگوی test_tg_center) — صفر شبکه؛
فلگ‌ها با os.environ داخلِ هر سنجه و با try/finally برمی‌گردند.
"""
import json
import os
import shutil
import sys
import time
import types
from datetime import datetime
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))

import harness
ENV = harness.setup("tg-wiring-w3")

sys.path.insert(0, str(_HERE.parent / "telegram_center"))

import opslib   # noqa: E402
import center   # noqa: E402

CFG_PATH = opslib.STATE_DIR / "telegram" / "center-config.json"
RAW_DIR = Path(ENV["ORG_ROOT"]) / "10 - Telegram processing" / "Raw"
OWNER = 777


class FakeClient:
    """الگوی test_tg_wiring_w2 + fetch_file (ویس) + شکستِ قابلِ‌تزریقِ send."""

    def __init__(self, wired=True, owner_id=OWNER, send_fails=False):
        self._is_wired = wired
        self.owner_id = owner_id
        self.owner_chat_id = owner_id
        self.send_fails = send_fails
        self.calls: list = []
        self.fetched: list = []
        self._next_mid = 100

    def wired(self):
        return self._is_wired

    def send(self, text, *, topic_id=None, keyboard=None, chat_id=None,
             pin=False, stream=None):
        self.calls.append(("send", {"text": text, "topic_id": topic_id,
                                    "keyboard": keyboard, "chat_id": chat_id,
                                    "pin": pin, "stream": stream}))
        if self.send_fails:
            return None
        self._next_mid += 1
        return self._next_mid

    def edit(self, message_id, text, keyboard=None, chat_id=None):
        self.calls.append(("edit", {"message_id": message_id, "text": text,
                                    "keyboard": keyboard}))
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

    def fetch_file(self, file_id, dest):
        self.fetched.append((file_id, dest))
        Path(dest).write_bytes(b"OggS-fake-voice")
        return True

    def is_owner(self, update):
        frm = ((update.get("message") or {}).get("from")
               or (update.get("callback_query") or {}).get("from") or {})
        return frm.get("id") == self.owner_id

    def named(self, kind):
        return [c for k, c in self.calls if k == kind]


def _render(with_digests=False):
    m = types.SimpleNamespace()
    m.collect_feeds = lambda *a, **k: {}
    m.render_status = lambda feeds: "STATUS"
    if with_digests:
        m.LEGS = {"lead": {}, "ziman": {}, "mining": {}}
        m.render_leg_digest = lambda leg, data: f"digest:{leg} — ۳ رخدادِ تازه"
    else:
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
    shutil.rmtree(opslib.STATE_DIR / "decisions", ignore_errors=True)
    shutil.rmtree(RAW_DIR, ignore_errors=True)
    try:
        (opslib.STATE_DIR / "tg-send-log.jsonl").unlink()
    except OSError:
        pass


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


def _nb_state(day_ts, used=0, deferred=0, announced=None):
    """state ِ بودجهٔ اعلان را مستقیم بنویس (قطعی‌سازیِ سناریو)."""
    import notify_budget as nb
    p = nb._path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({
        "day": nb._day_key(day_ts), "used": used, "exempt_used": 0,
        "deferred": deferred, "by_kind": {}, "announced_day": announced,
        "history": {}}, ensure_ascii=False), "utf-8")
    return nb


# ── V: ویس از هوکِ واقعیِ مرکز ──────────────────────────────────────────────
def t_v1_voice_dep_reaches_capture_and_a_fake_backend_yields_a_note():
    """دانلودر = خودِ client ِ مرکز (fetch_file)؛ موتورِ fake ⇒ نوتِ
    ساختاریافته با متنِ ویس، از handle_update ِ واقعی — نه از ماژولِ تنها."""
    _reset()
    import transcribe as tr
    fc = FakeClient()
    c = center.Center(client=fc, clock=Clock(1000.0), render_mod=_render())
    orig_avail, orig_tr = tr.available, tr.transcribe
    tr.available = lambda: (True, "fake-engine")
    tr.transcribe = lambda p, lang="fa", duration_s=None: {
        "ok": True, "text": "فردا با علی تماس بگیر", "engine": "fake-engine",
        "secs": 0.2}
    _flag("OCTOPUS_TG_CAPTURE")
    _flag("OCTOPUS_TG_VOICE_TRANSCRIBE")
    try:
        r = c.handle_update(_dm_msg(9101, voice={"file_id": "VOICE-1",
                                                 "duration": 4}))
    finally:
        _unflag("OCTOPUS_TG_CAPTURE", "OCTOPUS_TG_VOICE_TRANSCRIBE")
        tr.available, tr.transcribe = orig_avail, orig_tr
    assert r is not None and r.get("kind") == "capture", f"capture نشد: {r}"
    assert fc.fetched and fc.fetched[0][0] == "VOICE-1", \
        "دانلودر از client ِ مرکز صدا نخورد — dep وصل نیست"
    notes = list(RAW_DIR.rglob("*.md"))
    assert notes, "هیچ نوتی نوشته نشد"
    body = notes[0].read_text("utf-8")
    assert "فردا با علی تماس بگیر" in body and "متنِ ویس" in body, \
        f"نوتِ ساختاریافته نیست: {body[:200]}"
    acks = [s for s in fc.named("send") if "ویس متن شد" in s["text"]]
    assert acks, "ack ِ «ویس متن شد» نرفت"


def t_v2_flag_off_voice_stays_a_raw_note_with_an_honest_reason():
    """فلگ خاموش ⇒ رفتارِ دیروز: نوتِ خام + ack ای که چرا را می‌گوید؛
    دانلودر هرگز صدا نمی‌خورد (پاریتهٔ flag-off ِ همین سیم)."""
    _reset()
    fc = FakeClient()
    c = center.Center(client=fc, clock=Clock(1000.0), render_mod=_render())
    _flag("OCTOPUS_TG_CAPTURE")
    try:
        r = c.handle_update(_dm_msg(9102, voice={"file_id": "VOICE-2",
                                                 "duration": 4}))
    finally:
        _unflag("OCTOPUS_TG_CAPTURE")
    assert r is not None and r.get("kind") == "capture", r
    assert not fc.fetched, "فلگ خاموش ولی دانلود اجرا شد — پاریته شکست"
    acks = [s for s in fc.named("send") if "ویس ثبت شد" in s["text"]]
    assert acks and "متن‌سازی" in acks[0]["text"], \
        f"ack ِ صادقِ فلگ-خاموش نیست: {[s['text'] for s in fc.named('send')]}"


# ── N: بودجهٔ اعلان ─────────────────────────────────────────────────────────
def t_n1_an_interrupting_send_beyond_the_cap_goes_to_digest_and_announces():
    """سقف پر (۵/۵) ⇒ یادآوریِ ششم DM نمی‌شود، در بافرِ digest ِ hold_policy
    می‌نشیند، fired جلو می‌رود (تحویلِ digestی = تحویل)، و اعلامِ صادقانهٔ
    سرریز یک‌بار به DM می‌رود."""
    _reset()
    import reminders as rm
    import hold_policy as hp
    now = datetime(2026, 8, 1, 10, 0).timestamp()
    nb = _nb_state(now, used=5)
    rm.add("زنگ بزن به مامان", due_ts=now - 60, scope="dm", now=now - 3600)
    fc = FakeClient()
    c = center.Center(client=fc, clock=Clock(now), render_mod=_render())
    _flag("OCTOPUS_TG_REMINDERS")
    try:
        c.beat()
    finally:
        _unflag("OCTOPUS_TG_REMINDERS")
    texts = [s["text"] for s in fc.named("send")]
    assert not any("زنگ بزن به مامان" in t for t in texts), \
        f"یادآوریِ ماورای سقف باز هم DM شد: {texts}"
    buf = hp._buffer_path()
    assert buf.exists(), "بافرِ digest اصلاً نوشته نشد — سرریز گم شد"
    rows = [json.loads(ln) for ln in
            buf.read_text("utf-8").splitlines() if ln.strip()]
    assert any(r.get("stream") == "notify:reminder"
               and "زنگ بزن به مامان" in r.get("head", "") for r in rows), \
        f"سرریز در بافرِ hold_policy ننشست: {rows}"
    assert any("سقفِ اعلانِ امروز پر شد" in t for t in texts), \
        f"اعلامِ صادقانهٔ سرریز نرفت: {texts}"
    d = json.loads(nb._path().read_text("utf-8"))
    assert d["used"] == 5 and d["deferred"] == 1, d
    it = rm._load()["items"][0]
    assert it.get("fired") is True, \
        "تحویلِ digestی fired نکرد — ضربانِ بعد دوباره defer می‌شود (تکرار)"


def t_n2_ambient_streams_edit_digest_pulse_never_consume_budget():
    """یک beat ِ کامل با edit ِ status + دایجستِ ۳ پا + کارتِ پا ⇒ مصرفِ
    بودجهٔ قطع‌کننده باید صفر بماند (جریانِ محیطی هرگز شمرده نمی‌شود)."""
    _reset()
    now = datetime(2026, 8, 1, 11, 0).timestamp()
    nb = _nb_state(now, used=0)
    fc = FakeClient()
    c = center.Center(client=fc, clock=Clock(now),
                      render_mod=_render(with_digests=True))
    c.ensure_setup()
    fc.calls.clear()
    out = c.beat()
    assert out["digests"] >= 1, f"پیش‌فرضِ تست: دایجستی نرفت: {out}"
    assert fc.named("edit"), "پیش‌فرضِ تست: حتی edit ِ status هم نرفت"
    d = json.loads(nb._path().read_text("utf-8"))
    assert d["used"] == 0 and d["deferred"] == 0, \
        f"جریانِ محیطی بودجه خورد: {d}"


def t_n3_failed_question_send_is_refunded_and_never_marked_asked():
    """client ای که send اش None می‌دهد: سؤال asked نمی‌شود (ضربانِ بعد
    دوباره می‌کوشد) و واحدِ سوختهٔ بودجه refund می‌شود."""
    _reset()
    import question_budget as qb
    now = datetime(2026, 8, 1, 12, 0).timestamp()
    nb = _nb_state(now, used=0)
    qp = qb._path()
    qp.parent.mkdir(parents=True, exist_ok=True)
    qp.write_text(json.dumps({
        "week": qb._week_key(now), "used": 0, "seq": 1,
        "queue": [{"id": "Q-7", "q": "سؤالِ بی‌بخت؟", "context": "",
                   "goal": "", "created": now, "asked": False,
                   "asked_ts": None, "answer": None, "answered_ts": None}]},
        ensure_ascii=False), "utf-8")
    fc = FakeClient(send_fails=True)
    c = center.Center(client=fc, clock=Clock(now), render_mod=_render())
    _flag("OCTOPUS_TG_QBUDGET")
    try:
        c.beat()
    finally:
        _unflag("OCTOPUS_TG_QBUDGET")
    assert any("سؤالِ اختاپوس" in s["text"] for s in fc.named("send")), \
        "پیش‌فرضِ تست: اصلاً تلاشِ ارسال نشد"
    assert qb.used(now) == 0, "ارسالِ شکست‌خورده asked شد — بودجهٔ سؤال سوخت"
    d = json.loads(nb._path().read_text("utf-8"))
    assert d["used"] == 0, f"واحدِ سوخته refund نشد: {d}"


# ── Q: تولیدِ سؤال + تحویلِ همان-ضربان ─────────────────────────────────────
def t_q1_producers_submit_in_beat_and_the_same_beat_delivers_and_marks():
    """artifact ِ واقعی (flags-loaded + ماژولِ موجودِ خلعِ‌سلاح) ⇒ scan در
    beat ثبت می‌کند و **همان** ضربان تحویل می‌دهد و mark_asked می‌خورد —
    ترتیبِ scan-قبل-از-تحویل (قرارداد ASKS بند ۲)."""
    _reset()
    import question_budget as qb
    import question_producers as qp
    now = time.time()
    _nb_state(now, used=0)
    state = qp._state_dir()
    state.mkdir(parents=True, exist_ok=True)
    (state / "flags-loaded-center.json").write_text(
        json.dumps({"flags": {"OCTOPUS_TG_SEND_LOG": "1"}}), "utf-8")
    # هیچ‌کدام از فلگ‌های جدولِ منشور نباید در env روشن باشد وگرنه producer
    # چیزی برای پرسیدن ندارد (try/finally ِ تست‌های دیگر پاکشان کرده).
    fc = FakeClient()
    c = center.Center(client=fc, clock=Clock(now), render_mod=_render())
    _flag("OCTOPUS_TG_QBUDGET")
    try:
        c.beat()
    finally:
        _unflag("OCTOPUS_TG_QBUDGET")
    sent = [s for s in fc.named("send") if "سؤالِ اختاپوس" in s["text"]]
    assert sent, "سؤالِ تولیدشده در همان ضربان تحویل نشد"
    assert "خاموش" in sent[0]["text"], \
        f"سؤالِ producer ِ خلعِ‌سلاح نیست: {sent[0]['text'][:120]}"
    assert qb.used(now) == 1, "mark_asked بعدِ تحویل نخورد"
    keys = qp.asked_keys(now)
    assert any(k.startswith("disarm:") for k in keys), \
        f"دفترِ dedup ِ producer خالی است: {keys}"


# ── L: یادگیرِ پنجرهٔ سکوت ─────────────────────────────────────────────────
def t_l1_the_quiet_learner_runs_at_most_once_a_day_through_beat():
    _reset()
    import reminders as rm
    now = datetime(2026, 8, 1, 9, 0).timestamp()
    calls = []
    orig = rm.adapt_quiet

    def counting(now2=None):
        calls.append(now2)
        return orig(now2)

    rm.adapt_quiet = counting
    fc = FakeClient()
    clk = Clock(now)
    c = center.Center(client=fc, clock=clk, render_mod=_render())
    _flag("OCTOPUS_TG_REMINDERS")
    try:
        c.beat()
        clk.t += 300.0
        c.beat()
        clk.t += 300.0
        c.beat()
    finally:
        _unflag("OCTOPUS_TG_REMINDERS")
        rm.adapt_quiet = orig
    assert len(calls) == 1, \
        f"یادگیر باید روزی یک‌بار بدود، {len(calls)} بار دوید"
    assert rm.load_config().get("quiet_learned_day") == "2026-08-01", \
        "مهرِ روزِ یادگیری ننشست — فردا دوباره طوفانِ I/O"


def t_l2_the_owners_manual_quiet_window_always_wins():
    _reset()
    import reminders as rm
    now = datetime(2026, 8, 1, 9, 30).timestamp()
    cfgp = rm._cfg_file()
    cfgp.parent.mkdir(parents=True, exist_ok=True)
    cfgp.write_text(json.dumps({"quiet_from": 22, "quiet_to": 6,
                                "quiet_manual": True}), "utf-8")
    v = rm.adapt_quiet(now)
    assert v.get("applied") is False and v.get("manual") is True, v
    assert float(v.get("confidence", 1.0)) == 0.0, \
        "قفلِ دستی باید اطمینان را صفر اعلام کند"
    d = json.loads(cfgp.read_text("utf-8"))
    assert d["quiet_from"] == 22 and d["quiet_to"] == 6, \
        f"پنجرهٔ دستیِ مالک دست خورد: {d}"


# ── P: خطِ نبض در پالسِ ساعتی ──────────────────────────────────────────────
def t_p1_pulse_line_appears_with_data_and_is_absent_without():
    _reset()
    import tg_send_log as tsl
    fc = FakeClient()
    c = center.Center(client=fc, clock=Clock(time.time()),
                      render_mod=_render())
    _flag("OCTOPUS_TG_SEND_LOG")
    try:
        txt0 = c._home_pulse_text()
        assert "📨" not in txt0, f"بی‌داده خطِ نبض آمد: {txt0!r}"
        for i in range(4):
            tsl.record(chat_id=1, topic_id=None, text=f"row-{i}",
                       stream="center-pulse", ok=True, surface="dm")
        txt1 = c._home_pulse_text()
        assert "📨" in txt1, f"با داده خطِ نبض نیامد: {txt1!r}"
    finally:
        _unflag("OCTOPUS_TG_SEND_LOG")


# ── M: گزینهٔ ② پنل ────────────────────────────────────────────────────────
def t_m1_panel_option_two_prompts_then_the_next_text_builds_a_real_mission():
    _reset()
    fc = FakeClient()
    c = center.Center(client=fc, clock=Clock(1000.0), render_mod=_render())
    _flag("OCTOPUS_WIRE_MENU_V2")
    try:
        r1 = c.handle_update({"update_id": 21, "callback_query": {
            "id": "cbm1", "from": {"id": OWNER}, "data": "m:mission",
            "message": {"message_id": 50,
                        "chat": {"id": OWNER, "type": "private"}}}})
        assert r1 and r1.get("panel") == "mission-prompt", r1
        assert getattr(c, "_awaiting_mission", False) is True, \
            "پرچمِ انتظارِ متن ست نشد"
        edits = fc.named("edit")
        assert edits and "مأموریت جدید" in edits[-1]["text"], \
            f"prompt ِ گزینهٔ ② روی همان پیام ننشست: {edits}"
        assert fc.named("answer"), "answer_callback نرفت — spinner ِ ابدی"
        r2 = c.handle_update(_dm_msg(22, text="گزارشِ هفتگیِ وضعیت را آماده کن"))
        assert r2 and r2.get("kind") == "panel-mission" \
            and r2.get("panel_kind") == "mission", r2
        assert r2.get("mission"), "هیچ mission_id ای برنگشت — به هندلرِ واقعی نرسید"
        sends = [s for s in fc.named("send") if s["text"].startswith("②")]
        assert sends, "کارتِ نتیجهٔ ② فرستاده نشد"
        assert getattr(c, "_awaiting_mission", True) is False, \
            "پرچمِ انتظار مصرف نشد"
    finally:
        _unflag("OCTOPUS_WIRE_MENU_V2")


def t_m2_a_panel_error_is_shown_verbatim_never_swallowed():
    """A3: kind == "error" باید عیناً به مالک برسد — می‌گوید چیزی ثبت نشد."""
    _reset()
    import owner_menu as om
    fc = FakeClient()
    c = center.Center(client=fc, clock=Clock(1000.0), render_mod=_render())
    orig = om.handle_new_mission

    def boom(*a, **k):
        raise RuntimeError("simulated")

    om.handle_new_mission = boom
    _flag("OCTOPUS_WIRE_MENU_V2")
    try:
        c._awaiting_mission = True
        r = c.handle_update(_dm_msg(23, text="مأموریتی که می‌ترکد"))
    finally:
        _unflag("OCTOPUS_WIRE_MENU_V2")
        om.handle_new_mission = orig
    assert r and r.get("panel_kind") == "error", r
    assert any("نشد" in s["text"] for s in fc.named("send")), \
        "خطای پنل بلعیده شد — مالک هیچ نفهمید"


# ── G: گاردِ صفر-template روی کارتِ دوره‌ایِ پا ─────────────────────────────
def t_g1_a_template_leg_card_is_blocked_with_a_held_receipt_a_real_one_passes():
    _reset()
    import leg_tasks as lt
    fc = FakeClient()
    c = center.Center(client=fc, clock=Clock(1000.0), render_mod=_render())
    c.ensure_setup()
    fc.calls.clear()
    orig = lt.card_text
    lt.card_text = lambda leg, paused=False, kpi=None: "TODO: {{fill me}}"
    _flag("OCTOPUS_TG_SEND_LOG")
    try:
        c._refresh_leg_card("lead")
        assert not fc.named("send") and not fc.named("edit"), \
            f"کارتِ template-نما بیرون رفت: {fc.calls}"
        log = (opslib.STATE_DIR / "tg-send-log.jsonl")
        rows = [json.loads(ln) for ln in
                log.read_text("utf-8").splitlines() if ln.strip()] \
            if log.exists() else []
        held = [r for r in rows if r.get("state") == "held"
                and r.get("stream") == "leg-card-lead"]
        assert held, f"بلاکِ بی‌صدا — هیچ رسیدِ held ای ثبت نشد: {rows}"
        # رخدادِ واقعی از همان مسیر رد می‌شود
        lt.card_text = orig
        c._refresh_leg_card("lead")
        assert fc.named("send") or fc.named("edit"), \
            "کارتِ واقعی هم بلاک شد — گارد کور است"
    finally:
        _unflag("OCTOPUS_TG_SEND_LOG")
        lt.card_text = orig


# ── D: امیترِ decision_gate ────────────────────────────────────────────────
def _dg_row(now, tid, executor="owner_required"):
    return {"schema": "decision-record.v1", "trace_id": tid,
            "action": "lead.followup", "executor": executor,
            "evidence_score": 0.4, "threshold": 0.51, "risk_class": 3,
            "reasons": [], "destruction_risk": False,
            "ts": datetime.fromtimestamp(now - 120).isoformat()}


def t_dg1_flag_off_emits_nothing_flag_on_emits_a_handled_card_and_advances():
    _reset()
    import decision_gate as dg
    now = time.time()
    _nb_state(now, used=0)
    dg.LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with dg.LEDGER.open("w", encoding="utf-8") as f:
        f.write(json.dumps(_dg_row(now, "trace-w3-0001")) + "\n")
    fc = FakeClient()
    c = center.Center(client=fc, clock=Clock(now), render_mod=_render())
    c.beat()                                          # فلگ خاموش
    assert not [s for s in fc.named("send") if "⚖️" in s["text"]], \
        "فلگ خاموش ولی کارتِ decision_gate رفت — پاریته شکست"
    assert "dg_cursor" not in json.loads(CFG_PATH.read_text("utf-8")) \
        if CFG_PATH.exists() else True
    _flag("OCTOPUS_WIRE_DECISION_GATE")
    try:
        out = c.beat()
    finally:
        _unflag("OCTOPUS_WIRE_DECISION_GATE")
    cards = [s for s in fc.named("send") if "⚖️" in s["text"]]
    assert cards, "فلگ روشن ولی کارتی نرفت"
    cds = [str(b.get("callback_data") or "") for row in
           (cards[0]["keyboard"] or []) for b in row]
    assert any(cd.startswith("ok:") for cd in cds) \
        and any(cd.startswith("dg:e:") for cd in cds), \
        f"دکمه‌های کارت با هندلرهای مرکز نمی‌خوانند: {cds}"
    cfg = json.loads(CFG_PATH.read_text("utf-8"))
    assert float(cfg.get("dg_cursor") or 0) > 0, \
        "نشانگر بعدِ تحویل جلو نرفت"
    assert out["decisions"] >= 1, out
    # ضربانِ بعد: همان کارت دوباره نمی‌رود (since=cursor)
    fc.calls.clear()
    _flag("OCTOPUS_WIRE_DECISION_GATE")
    try:
        c.beat()
    finally:
        _unflag("OCTOPUS_WIRE_DECISION_GATE")
    assert not [s for s in fc.named("send") if "⚖️" in s["text"]], \
        "کارتِ تحویل‌شده دوباره رفت — نشانگر بی‌اثر است"


def t_dg2_a_failed_card_send_never_advances_the_cursor():
    _reset()
    import decision_gate as dg
    now = time.time()
    _nb_state(now, used=0)
    dg.LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with dg.LEDGER.open("w", encoding="utf-8") as f:
        f.write(json.dumps(_dg_row(now, "trace-w3-0002")) + "\n")
    fc = FakeClient(send_fails=True)
    c = center.Center(client=fc, clock=Clock(now), render_mod=_render())
    _flag("OCTOPUS_WIRE_DECISION_GATE")
    try:
        c.beat()
    finally:
        _unflag("OCTOPUS_WIRE_DECISION_GATE")
    cfg = json.loads(CFG_PATH.read_text("utf-8")) if CFG_PATH.exists() else {}
    assert float(cfg.get("dg_cursor") or 0) == 0.0, \
        f"ارسال شکست ولی نشانگر جلو رفت — کارت برای همیشه گم شد: {cfg}"


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
    print(f"\n{mark} test_tg_wiring_w3: {ok}/{total}")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(_run())
