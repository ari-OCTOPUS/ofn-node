#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_tg_acceptance_journey — سفرِ پذیرشِ بدونِ ناظر (لِینِ سفر، ۲۰۲۶-۰۷-۳۱).

    ترتیب و idempotency (دو تیک در یک پنجره = یک ارسال) · شاهدِ غایب = PENDING
    نه PASS · تشخیصِ نوتِ capture ِ کاشته‌شده · تشخیصِ شلیکِ یادآوری ·
    TIMEOUT بعد از ۳ تلاش · گزارشِ نهایی همهٔ فازها را دارد · stateِ خراب
    fail-soft · شکستِ ارسال هرگز مکان‌نما را جلو نمی‌برد · ناوردیِ AST:
    نه importِ center، نه poll_updates.

ساعت و کلاینت هر دو تزریق‌شده‌اند — صفر شبکه، صفر ساعتِ واقعی.
"""
import ast
import json
import sys
import time
from pathlib import Path

import harness

ENV = harness.setup("tg-acceptance-journey")

_OPS = Path(__file__).resolve().parent.parent
_TC = str(_OPS / "telegram_center")
if _TC not in sys.path:
    sys.path.insert(0, _TC)

import acceptance_journey as aj  # noqa: E402

NOW = time.mktime((2026, 7, 31, 10, 0, 0, 0, 0, -1))
SRC = Path(aj.__file__).resolve()


# ─── دوبل‌ها ────────────────────────────────────────────────────────────────
class FakeClient:
    """کلاینتِ ساختگی با **همان** امضای TgClient.send (فیکی که تابعِ واقعی را
    دور بزند = پوششِ کاذب؛ پس امضا عیناً کپی شده)."""

    def __init__(self, *, fail=False, owner=111, center=-1004475788460):
        self.owner_chat_id = owner
        self.center_chat_id = center
        self.sent = []
        self.fail = fail

    def send(self, text, *, topic_id=None, keyboard=None, chat_id=None,
             pin=False, stream="center"):
        if self.fail:
            return None
        self.sent.append({"text": text, "chat_id": chat_id, "topic_id": topic_id,
                          "stream": stream})
        return 1000 + len(self.sent)


class Clock:
    def __init__(self, t=NOW):
        self.t = float(t)

    def __call__(self):
        return self.t

    def advance(self, s):
        self.t += float(s)
        return self.t


def _journey(clock=None, client=None, **kw):
    root = Path(ENV["ops"]) / "state"
    j = aj.Journey(client=client if client is not None else FakeClient(),
                   clock=clock or Clock(),
                   state_path=root / "telegram" / "acceptance-journey.json",
                   org_root=Path(ENV["root"]), **kw)
    return j


def _fresh(j):
    """ایزولهٔ کامل بینِ تست‌ها. درسِ «هر مسیرِ تحتِ آزمون را ایزوله کن»:
    پاک‌کردنِ فقط state کافی نیست — یک ردیفِ tg-send-log ِ جامانده از تستِ
    قبلی، تستِ «شاهد نیست» را الکی سبز می‌کند."""
    for p in (j.state_path, j.send_log_path, j.reminders_path, j.qbudget_path,
              j.miniapp_hits_path, j.lead_tasks_path):
        try:
            p.unlink()
        except OSError:
            pass
    try:
        for f in j.raw_dir.glob("*.md"):
            f.unlink()
    except OSError:
        pass


def _center_config(j, **extra):
    cfg = {"chat_id": -1004475788460, "topics": {"lead": 22},
           "last_pulse": j.now(), "home_message_id": 1, "guide_message_id": 2}
    cfg.update(extra)
    j.center_config_path.parent.mkdir(parents=True, exist_ok=True)
    j.center_config_path.write_text(json.dumps(cfg, ensure_ascii=False), "utf-8")


def _plant_send_row(j, **row):
    base = {"ts": j.now(), "chat": 111, "topic": None, "stream": "center",
            "sha": "deadbeef", "chars": 10, "ok": True, "state": "sent",
            "bot_role": "outer", "surface": "dm"}
    base.update(row)
    j.send_log_path.parent.mkdir(parents=True, exist_ok=True)
    with j.send_log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(base, ensure_ascii=False) + "\n")


def _seed_to(j, key, *, prompt_ts=None, meta=None):
    """سفر را مستقیم روی یک فاز بنشان (state فایلِ سادهٔ JSON است)."""
    st = j.load_state()
    st["started_at"] = st.get("started_at") or j.now()
    idx = [i for i, p in enumerate(aj._PHASES) if p["key"] == key][0]
    st["phase_idx"] = idx
    for p in aj._PHASES[:idx]:
        rec = j._rec(st, p["key"])
        rec["prompt_sent_ts"] = j.now() - 10_000
        rec["verdict"] = aj.VERDICT_PASS
        rec["evidence"] = ["(کاشته‌شده در تست)"]
    rec = j._rec(st, key)
    rec["prompt_sent_ts"] = prompt_ts
    if meta:
        rec["meta"].update(meta)
    j.save_state(st)
    return st


# ─── ترتیب و idempotency ───────────────────────────────────────────────────
def t_first_tick_sends_the_kickoff_and_records_state():
    c, cl = Clock(), FakeClient()
    j = _journey(c, cl)
    _fresh(j)
    _center_config(j)
    out = j.tick()
    assert len(cl.sent) == 1, cl.sent
    assert "سفرِ آزمونِ خودکار" in cl.sent[0]["text"]
    assert cl.sent[0]["stream"] == aj.STREAM, "رسیدِ خودمان باید برچسبِ journey بگیرد"
    st = j.load_state()
    assert st["phases"]["P0"]["prompt_sent_ts"] is not None
    assert st["started_at"] is not None
    assert out["sends"] == 1


def t_two_ticks_in_the_same_window_send_only_once():
    """قلبِ idempotency: فازی که منتظرِ مالک است، هرچقدر تیک بخورد سکوت می‌کند."""
    c, cl = Clock(), FakeClient()
    j = _journey(c, cl)
    _fresh(j)
    _center_config(j)
    _seed_to(j, "P1", prompt_ts=None)
    j.tick()
    assert len(cl.sent) == 1, cl.sent          # درخواستِ P1 یک‌بار رفت
    for _ in range(3):
        c.advance(60)                          # همان پنجره، بی‌شاهد
        j.tick()
        assert len(cl.sent) == 1, cl.sent


def t_phases_advance_in_declared_order():
    c, cl = Clock(), FakeClient()
    j = _journey(c, cl)
    _fresh(j)
    _center_config(j)
    j.tick()                                       # P0 immediate → پایانی
    st = j.load_state()
    assert st["phases"]["P0"]["verdict"] in (aj.VERDICT_PASS, aj.VERDICT_DEGRADED), \
        st["phases"]["P0"]
    assert st["phase_idx"] == 1, st["phase_idx"]
    assert len(cl.sent) == 1, "سقفِ یک درخواست در هر تیک"
    c.advance(900)
    j.tick()                                       # حالا نوبتِ درخواستِ P1
    st = j.load_state()
    assert st["phases"]["P1"]["prompt_sent_ts"] is not None, st["phases"]["P1"]
    assert len(cl.sent) == 2


def t_p0_is_terminal_even_when_the_environment_is_incomplete():
    """محیطِ ناقص نباید کلِ سفر را همان اولِ کار قفل کند — DEGRADED، نه PENDING."""
    c, cl = Clock(), FakeClient()
    j = _journey(c, cl)
    _fresh(j)
    _center_config(j)               # نه ORGANISM-STATE، نه فلگ‌ها ⇒ ناقص
    j.tick()
    rec = j.load_state()["phases"]["P0"]
    assert rec["verdict"] == aj.VERDICT_DEGRADED, rec
    assert any("فلگ" in e for e in rec["evidence"]), rec["evidence"]
    assert j.load_state()["phase_idx"] == 1


# ─── صداقت: شاهدِ غایب = PENDING، نه PASS ──────────────────────────────────
def t_missing_evidence_is_pending_never_pass():
    c, cl = Clock(), FakeClient()
    j = _journey(c, cl)
    _fresh(j)
    _center_config(j)
    _seed_to(j, "P1", prompt_ts=c.t)
    c.advance(aj.DEFAULT_WINDOW_S + 60)            # پنجره بست، هیچ ردیفی نکاشتیم
    j.tick()
    rec = j.load_state()["phases"]["P1"]
    assert rec["verdict"] == aj.VERDICT_PENDING, rec
    assert rec["attempts"] == 1, rec
    assert j.load_state()["phase_idx"] == 1, "مکان‌نما نباید جلو رفته باشد"


def t_our_own_send_row_is_never_counted_as_the_owners_reply():
    c, cl = Clock(), FakeClient()
    j = _journey(c, cl)
    _fresh(j)
    _center_config(j)
    _seed_to(j, "P1", prompt_ts=c.t)
    _plant_send_row(j, ts=c.t + 5, stream=aj.STREAM)   # ردیفِ خودِ سفر
    c.advance(aj.DEFAULT_WINDOW_S + 60)
    j.tick()
    assert j.load_state()["phases"]["P1"]["verdict"] == aj.VERDICT_PENDING


def t_a_foreign_dm_row_passes_free_chat():
    c, cl = Clock(), FakeClient()
    j = _journey(c, cl)
    _fresh(j)
    _center_config(j)
    _seed_to(j, "P1", prompt_ts=c.t)
    _plant_send_row(j, ts=c.t + 30, stream="center", sha="abc123")
    c.advance(600)
    j.tick()
    st = j.load_state()
    assert st["phases"]["P1"]["verdict"] == aj.VERDICT_PASS, st["phases"]["P1"]
    assert any("tg-send-log" in e for e in st["phases"]["P1"]["evidence"])


# ─── capture ───────────────────────────────────────────────────────────────
def _plant_raw_note(j, name, body="", *, mid=42, chat=111, extra_fm=()):
    j.raw_dir.mkdir(parents=True, exist_ok=True)
    fm = ["---", "type: telegram-log", 'project: ""', "status: active",
          "tags: [telegram]", "created: 2026-07-31", "updated: 2026-07-31",
          f"message_id: {mid}", f"chat_id: {chat}"]
    fm += list(extra_fm)
    fm.append("---")
    p = j.raw_dir / name
    p.write_text("\n".join(fm) + "\n\n" + body + "\n", "utf-8")
    return p


def t_capture_evidence_is_detected_from_a_planted_raw_note():
    c, cl = Clock(), FakeClient()
    j = _journey(c, cl)
    _fresh(j)
    _center_config(j)
    _seed_to(j, "P2", prompt_ts=c.t)
    p = _plant_raw_note(j, "2026-07-31 1005 خرید رنگ.md", "ثبت: خرید رنگ ۵۰ دلار")
    c.advance(300)
    j.tick()
    rec = j.load_state()["phases"]["P2"]
    assert rec["verdict"] == aj.VERDICT_PASS, rec
    assert any(p.name in e for e in rec["evidence"]), rec["evidence"]


def t_a_note_without_message_id_frontmatter_is_not_evidence():
    c, cl = Clock(), FakeClient()
    j = _journey(c, cl)
    _fresh(j)
    _center_config(j)
    _seed_to(j, "P2", prompt_ts=c.t)
    j.raw_dir.mkdir(parents=True, exist_ok=True)
    (j.raw_dir / "2026-07-31 1005 بی-فرانت‌متر.md").write_text("سلام\n", "utf-8")
    c.advance(300)
    j.tick()
    assert j.load_state()["phases"]["P2"]["verdict"] == aj.VERDICT_PENDING


def t_media_capture_needs_a_media_marker():
    c, cl = Clock(), FakeClient()
    j = _journey(c, cl)
    _fresh(j)
    _center_config(j)
    _seed_to(j, "P3", prompt_ts=c.t)
    _plant_raw_note(j, "2026-07-31 1010 متنِ ساده.md", "فقط متن")
    c.advance(300)
    j.tick()
    assert j.load_state()["phases"]["P3"]["verdict"] == aj.VERDICT_PENDING
    _plant_raw_note(j, "2026-07-31 1011 ویس.md",
                    "- منبع: تلگرام · chat_id: 111 · message_id: 43 · [voice]",
                    mid=43, extra_fm=("file_id: AwACAgQ",))
    c.advance(300)
    j.tick()
    rec = j.load_state()["phases"]["P3"]
    assert rec["verdict"] == aj.VERDICT_PASS, rec
    assert any("file_id" in e for e in rec["evidence"]), rec["evidence"]


# ─── یادآوری ───────────────────────────────────────────────────────────────
def _plant_reminders(j, items):
    j.reminders_path.parent.mkdir(parents=True, exist_ok=True)
    j.reminders_path.write_text(
        json.dumps({"seq": len(items), "items": items}, ensure_ascii=False), "utf-8")


def t_reminder_creation_is_detected_from_a_planted_store():
    c, cl = Clock(), FakeClient()
    j = _journey(c, cl)
    _fresh(j)
    _center_config(j)
    _seed_to(j, "P4A", prompt_ts=c.t)
    _plant_reminders(j, [{"id": "RM-9", "text": "آب بخورم", "due": c.t + 900,
                          "scope": "dm", "leg": None, "created": c.t + 60,
                          "done": False, "fired": False}])
    c.advance(300)
    j.tick()
    st = j.load_state()
    assert st["phases"]["P4A"]["verdict"] == aj.VERDICT_PASS, st["phases"]["P4A"]
    assert st["phases"]["P4A"]["meta"]["reminder_id"] == "RM-9"


def t_reminder_fired_detection_needs_both_fired_ts_and_a_dm_row():
    c, cl = Clock(), FakeClient()
    j = _journey(c, cl)
    _fresh(j)
    _center_config(j)
    _seed_to(j, "P4B", prompt_ts=c.t, meta={})
    st = j.load_state()
    j._rec(st, "P4A")["meta"]["reminder_id"] = "RM-9"
    j.save_state(st)
    # ۱) شلیک‌نشده ⇒ PENDING
    _plant_reminders(j, [{"id": "RM-9", "text": "آب", "due": c.t + 900,
                          "created": c.t, "done": False, "fired": False}])
    c.advance(aj.DEFAULT_WINDOW_S + 60)
    j.tick()
    assert j.load_state()["phases"]["P4B"]["verdict"] == aj.VERDICT_PENDING
    # ۲) fired + fired_ts ولی بدونِ ردیفِ DM ⇒ هنوز PENDING (تحویل اثبات نشده)
    fired_at = c.t + 900
    _plant_reminders(j, [{"id": "RM-9", "text": "آب", "due": c.t + 900,
                          "created": c.t, "done": False, "fired": True,
                          "fired_ts": fired_at}])
    c.advance(1200)
    j.tick()
    rec = j.load_state()["phases"]["P4B"]
    assert rec["verdict"] == aj.VERDICT_PENDING, rec
    assert any("شلیک ثبت شد" in e for e in rec["evidence"]), rec["evidence"]
    # ۳) با ردیفِ DM ِ نزدیک ⇒ PASS
    _plant_send_row(j, ts=fired_at + 2, stream="center", sha="rm9")
    j.tick()
    assert j.load_state()["phases"]["P4B"]["verdict"] == aj.VERDICT_PASS


# ─── TIMEOUT ───────────────────────────────────────────────────────────────
def t_three_windows_without_evidence_become_timeout_then_advance():
    c, cl = Clock(), FakeClient()
    j = _journey(c, cl)
    _fresh(j)
    _center_config(j)
    _seed_to(j, "P1", prompt_ts=c.t)
    for i in range(aj.MAX_ATTEMPTS):
        c.advance(aj.DEFAULT_WINDOW_S + 60)
        j.tick()
        st = j.load_state()
        if i < aj.MAX_ATTEMPTS - 1:
            assert st["phases"]["P1"]["verdict"] == aj.VERDICT_PENDING, (i, st)
    st = j.load_state()
    assert st["phases"]["P1"]["verdict"] == aj.VERDICT_TIMEOUT, st["phases"]["P1"]
    assert st["phase_idx"] > 1, "بعد از TIMEOUT باید جلو برود"
    assert st["phases"]["P1"]["verdict"] != aj.VERDICT_PASS


# ─── شکستِ ارسال ───────────────────────────────────────────────────────────
def t_a_send_failure_never_advances_the_cursor():
    c = Clock()
    cl = FakeClient(fail=True)
    j = _journey(c, cl)
    _fresh(j)
    _center_config(j)
    for _ in range(6):
        c.advance(aj.DEFAULT_WINDOW_S + 60)
        j.tick()
    st = j.load_state()
    assert st["phase_idx"] == 0, st["phase_idx"]
    assert st["phases"]["P0"]["verdict"] == aj.VERDICT_PENDING
    assert st["phases"]["P0"]["prompt_sent_ts"] is None, "ارسالِ ناموفق نباید مهرِ زمان بگذارد"
    assert st["done"] is False


def t_an_undeliverable_final_report_still_lands_in_the_vault_and_stops():
    """تلگرام در دسترس نیست: گزارش نمی‌رود، ولی سکوتِ ابدی هم جواب نیست."""
    c = Clock()
    cl = FakeClient(fail=True)
    j = _journey(c, cl, task_name="OctopusJourneyTestTaskDoesNotExist")
    _fresh(j)
    _center_config(j)
    _seed_to(j, "P12", prompt_ts=None)
    for _ in range(aj.MAX_ATTEMPTS):
        c.advance(900)
        j.tick()
    st = j.load_state()
    assert st["done"] is True, st
    assert st["phases"]["P12"]["verdict"] == aj.VERDICT_TIMEOUT
    note = st["phases"]["P12"]["meta"].get("note")
    assert note and Path(note).exists(), st["phases"]["P12"]


# ─── گزارشِ نهایی ──────────────────────────────────────────────────────────
def t_final_report_names_every_phase_and_is_telegram_safe():
    c, cl = Clock(), FakeClient()
    j = _journey(c, cl)
    _fresh(j)
    _center_config(j)
    st = _seed_to(j, "P12", prompt_ts=None)
    report = j.compose_report(j.load_state())
    for ph in aj._PHASES:
        if ph["key"] == aj._FINAL_KEY:
            continue
        assert ph["key"] in report, ph["key"]
        assert ph["title"] in report, ph["title"]
    assert len(report) <= 4096, len(report)
    assert "کارنامهٔ سفرِ پذیرش" in report
    assert "OCTOPUS_WIRE_LEAD_OUTBOUND" in report, "نیازِ مالک باید در گزارش باشد"


def t_the_final_phase_sends_writes_a_vault_note_and_marks_done():
    c, cl = Clock(), FakeClient()
    j = _journey(c, cl, task_name="OctopusJourneyTestTaskDoesNotExist")
    _fresh(j)
    _center_config(j)
    _seed_to(j, "P12", prompt_ts=None)
    j.tick()
    st = j.load_state()
    assert st["done"] is True, st
    assert cl.sent and "کارنامهٔ سفرِ پذیرش" in cl.sent[-1]["text"]
    note = st["phases"]["P12"]["meta"].get("note")
    assert note, st["phases"]["P12"]
    txt = Path(note).read_text("utf-8")
    for key in ("type:", "project:", "status:", "tags:", "created:", "updated:",
                "created_by: agent"):
        assert key in txt, key
    assert "<b>" not in txt, "نوتِ والت نباید HTML داشته باشد"
    assert str(Path(ENV["root"])) in note, note
    # حذفِ تسکِ ناموجود باید صادقانه گزارش شود، نه crash
    assert st["phases"]["P12"]["meta"]["schtask"]["ok"] in (True, False)


def t_a_done_journey_is_inert():
    c, cl = Clock(), FakeClient()
    j = _journey(c, cl, task_name="OctopusJourneyTestTaskDoesNotExist")
    _fresh(j)
    _center_config(j)
    _seed_to(j, "P12", prompt_ts=None)
    j.tick()
    n = len(cl.sent)
    c.advance(10_000)
    out = j.tick()
    assert len(cl.sent) == n, "سفرِ تمام‌شده دیگر هیچ نمی‌فرستد"
    assert out["done"] is True


def t_the_global_deadline_jumps_straight_to_the_report():
    c, cl = Clock(), FakeClient()
    j = _journey(c, cl, deadline_s=3600,
                 task_name="OctopusJourneyTestTaskDoesNotExist")
    _fresh(j)
    _center_config(j)
    j.tick()                                   # P0
    c.advance(60)
    j.tick()                                   # درخواستِ P1 رفت
    assert j.load_state()["phases"]["P1"]["prompt_sent_ts"] is not None
    c.advance(4000)                            # از سقفِ کلِ سفر گذشت
    j.tick()
    st = j.load_state()
    assert st["done"] is True, (st["done"], st["phase_idx"])
    assert st["phases"]["P1"]["verdict"] == aj.VERDICT_TIMEOUT, st["phases"]["P1"]
    assert st["phases"]["P9"]["verdict"] == aj.VERDICT_NOT_RUN, \
        "فازی که نوبتش نرسید باید NOT-RUN باشد نه TIMEOUT"
    assert st["phases"]["P11"]["verdict"] == aj.VERDICT_NOT_DUE, \
        "شبی که نرسیده باید SCHEDULED-NOT-DUE باشد نه TIMEOUT"
    assert cl.sent and "کارنامهٔ سفرِ پذیرش" in cl.sent[-1]["text"]


# ─── مقاومت ────────────────────────────────────────────────────────────────
def t_a_corrupt_state_file_is_survived_not_fatal():
    c, cl = Clock(), FakeClient()
    j = _journey(c, cl)
    _fresh(j)
    _center_config(j)
    j.state_path.parent.mkdir(parents=True, exist_ok=True)
    j.state_path.write_text("{این JSON نیست", "utf-8")
    st = j.load_state()
    assert st["phase_idx"] == 0 and st["phases"] == {}
    out = j.tick()                     # نباید استثنا بدهد
    assert out["sends"] == 1
    assert j.load_state()["phases"]["P0"]["prompt_sent_ts"] is not None


def t_a_phase_exception_does_not_kill_the_tick():
    c, cl = Clock(), FakeClient()
    j = _journey(c, cl)
    _fresh(j)
    _center_config(j)
    _seed_to(j, "P1", prompt_ts=c.t)
    orig = aj.Journey._verify_p1

    def boom(self, st, rec):
        raise RuntimeError("انفجارِ عمدی")
    aj.Journey._verify_p1 = boom
    try:
        c.advance(aj.DEFAULT_WINDOW_S + 60)
        out = j.tick()
    finally:
        aj.Journey._verify_p1 = orig
    rec = j.load_state()["phases"]["P1"]
    assert rec["verdict"] == aj.VERDICT_PENDING, rec
    assert any("RuntimeError" in e for e in rec["errors"]), rec["errors"]
    assert isinstance(out, dict)


def t_state_stays_inside_the_isolated_tree():
    j = _journey()
    live = str(harness.REAL_VAULT / "_ops" / "state").lower()
    for p in (j.state_path, j.send_log_path, j.reminders_path, j.qbudget_path,
              j.miniapp_hits_path, j.outcomes_db_path, j.lead_tasks_path):
        assert not str(p).lower().startswith(live), p
    assert not str(j.raw_dir).lower().startswith(str(harness.REAL_VAULT).lower())


# ─── قرارداد با دروازهٔ مینی‌اپ (نویسنده و خواننده را با هم بسنج) ──────────
def t_the_gateway_writes_exactly_the_hit_line_the_journey_reads():
    """درسِ «خواننده و نویسنده را با هم بسنج»: شکلِ ردیف را از مسیرِ
    **تولیدیِ** خودِ دروازه می‌گیریم، نه از یک fixture ِ دست‌ساز."""
    import miniapp_gateway as mg

    c, cl = Clock(), FakeClient()
    j = _journey(c, cl)
    _fresh(j)
    _center_config(j)
    assert mg._hits_path() == j.miniapp_hits_path, (mg._hits_path(),
                                                    j.miniapp_hits_path)
    _seed_to(j, "P9", prompt_ts=c.t, meta={"url_present": True})
    st, body, ctype = mg.handle("GET", "/miniapp?x=1", {},
                                fetch_fn=lambda p: (200, b"<html></body>",
                                                    "text/html"))
    assert st == 200, st
    rows = [json.loads(x) for x in
            j.miniapp_hits_path.read_text("utf-8").splitlines() if x.strip()]
    assert rows and rows[-1]["path"] == "/miniapp", rows
    assert rows[-1]["ok"] is True and rows[-1]["authed"] is False
    assert set(rows[-1]) == {"ts", "path", "ok", "authed"}, \
        "ردیف نباید هیچ فیلدِ هویتی داشته باشد"
    c.advance(300)
    j.tick()
    rec = j.load_state()["phases"]["P9"]
    assert rec["verdict"] == aj.VERDICT_PASS, rec
    assert any("درخواست سرو کرد" in e for e in rec["evidence"]), rec["evidence"]


def t_an_unauthenticated_api_hit_is_logged_as_not_authed():
    import miniapp_gateway as mg

    c = Clock()
    j = _journey(c)
    _fresh(j)
    st, _b, _c = mg.handle("GET", "/api/miniapp", {},
                           fetch_fn=lambda p: (200, b"{}", "application/json"))
    assert st == 403, st
    rows = [json.loads(x) for x in
            j.miniapp_hits_path.read_text("utf-8").splitlines() if x.strip()]
    assert rows[-1] == {**rows[-1], "path": "/api/miniapp", "ok": False,
                        "authed": False}, rows[-1]


# ─── ناوردی‌های ساختاری (AST روی منبعِ خودش) ───────────────────────────────
def _tree():
    return ast.parse(SRC.read_text("utf-8"))


def t_the_module_never_imports_center():
    imported = set()
    for n in ast.walk(_tree()):
        if isinstance(n, ast.Import):
            imported.update(a.name.split(".")[0] for a in n.names)
        elif isinstance(n, ast.ImportFrom) and n.module:
            imported.add(n.module.split(".")[0])
    assert "center" not in imported, imported
    assert "approval_channel" not in imported, imported
    assert not (imported & {"organism", "live_loop", "wiring"}), imported


def t_the_module_never_polls_telegram():
    """poller دومی روی همان توکن = 409 و دزدیدنِ پیامِ مالک."""
    src = SRC.read_text("utf-8")
    called = {getattr(n.func, "attr", None) or getattr(n.func, "id", None)
              for n in ast.walk(_tree()) if isinstance(n, ast.Call)}
    for bad in ("poll_updates", "poll_once", "get_updates", "getUpdates"):
        assert bad not in called, f"سفر خودش poll می‌کند: {bad}"
        assert bad not in src.replace("poll_updates`", ""), bad


def t_only_send_is_used_on_the_client():
    """تنها فعلِ تلگرامیِ مجاز `send` است (نه edit/pin/delete/answer)."""
    src = SRC.read_text("utf-8")
    for bad in ("cl.edit(", "client.edit(", "cl.pin_message(", "cl.delete",
                "answer_callback"):
        assert bad not in src, bad


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_tg_acceptance_journey: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
