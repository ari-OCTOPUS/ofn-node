#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_tg_acceptance_journey — سفرِ پذیرشِ بدونِ ناظر (لِینِ سفر، ۲۰۲۶-۰۷-۳۱).

    ترتیب و idempotency (دو تیک در یک پنجره = یک ارسال) · شاهدِ غایب = PENDING
    نه PASS · تشخیصِ نوتِ capture ِ کاشته‌شده · تشخیصِ شلیکِ یادآوری ·
    TIMEOUT بعد از ۳ تلاش · گزارشِ نهایی همهٔ فازها را دارد · stateِ خراب
    fail-soft · شکستِ ارسال هرگز مکان‌نما را جلو نمی‌برد · ناوردیِ AST:
    نه importِ center، نه poll_updates.

    و لایهٔ ۰۷-۳۱ عصر — **اثباتِ قابلیت**: هر فازِ وابسته به مالک خودش را روی
    ماژولِ تولیدیِ واقعی می‌سنجد؛ شاهدِ مالک نیامد ولی اثبات پاس شد ⇒
    CAPABILITY-OK؛ اثبات ترکید ⇒ BROKEN؛ فلگ خاموش ⇒ BLOCKED. و گاردِ
    آلودگی: اجرای همهٔ اثبات‌ها هیچ بایتی از state/vault ِ زنده را تکان نمی‌دهد.

ساعت و کلاینت و HTTP هر سه تزریق‌شده‌اند — صفر شبکه، صفر ساعتِ واقعی.
"""
import ast
import json
import os
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
import opslib  # noqa: E402

NOW = time.mktime((2026, 7, 31, 10, 0, 0, 0, 0, -1))
SRC = Path(aj.__file__).resolve()

# فلگ‌هایی که اثباتِ قابلیت به آن‌ها گیت است (در تولید از OCTOPUS-flags.cmd می‌آیند).
PROOF_FLAGS = {"OCTOPUS_TG_CAPTURE": "1", "OCTOPUS_TG_REMINDERS": "1",
               "OCTOPUS_TG_QBUDGET": "1"}


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


class FakeHttp:
    """HTTP ِ تزریقی — هیچ تستی هرگز به تونلِ واقعی نمی‌زند.

    پیش‌فرض همان قراردادِ سالمِ دروازه است: شِل ۲۰۰، APIِ بی‌initData ۴۰۳."""

    def __init__(self, shell=200, api=403, error=None):
        self.shell, self.api, self.error = shell, api, error
        self.calls = []

    def __call__(self, url, timeout=12.0):
        self.calls.append(url)
        code = self.api if "/api/miniapp" in str(url) else self.shell
        return {"status": code, "error": self.error}


class _Flags:
    """فلگ‌ها را برای مدتِ تست مسلح می‌کند و **دقیقاً** برمی‌گرداند."""

    def __init__(self, **kw):
        self.want = {k: str(v) for k, v in kw.items()}
        self.before = {}

    def __enter__(self):
        for k, v in self.want.items():
            self.before[k] = os.environ.get(k)
            os.environ[k] = v
        return self

    def __exit__(self, *_e):
        for k, v in self.before.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        return False


def _journey(clock=None, client=None, http_fn=None, **kw):
    root = Path(ENV["ops"]) / "state"
    j = aj.Journey(client=client if client is not None else FakeClient(),
                   clock=clock or Clock(),
                   state_path=root / "telegram" / "acceptance-journey.json",
                   org_root=Path(ENV["root"]),
                   http_fn=http_fn if http_fn is not None else FakeHttp(), **kw)
    return j


def _fresh(j):
    """ایزولهٔ کامل بینِ تست‌ها. درسِ «هر مسیرِ تحتِ آزمون را ایزوله کن»:
    پاک‌کردنِ فقط state کافی نیست — یک ردیفِ tg-send-log ِ جامانده از تستِ
    قبلی، تستِ «شاهد نیست» را الکی سبز می‌کند."""
    for p in (j.state_path, j.send_log_path, j.reminders_path, j.qbudget_path,
              j.miniapp_hits_path, j.lead_tasks_path, j.ask_brain_path,
              j.miniapp_url_path, j.outcomes_db_path,
              Path(str(j.outcomes_db_path) + "-wal"),
              Path(str(j.outcomes_db_path) + "-shm")):
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


def _seed_to(j, key, *, prompt_ts=None, meta=None, prompt_mid=500):
    """سفر را مستقیم روی یک فاز بنشان (state فایلِ سادهٔ JSON است).

    قاعدهٔ provenance ِ ۰۷-۳۱: فازهای capture لنگرِ message_id ِ درخواستِ
    خودمان را از our_sends می‌خوانند — پس seed هم همان رسید را می‌کارد
    (همان شکلی که `_send` ِ تولیدی می‌نویسد)."""
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
    if prompt_ts is not None and prompt_mid is not None:
        st.setdefault("our_sends", []).append(
            {"ts": prompt_ts, "chat": 111, "topic": None, "label": key,
             "message_id": int(prompt_mid), "chars": 10})
    if meta:
        rec["meta"].update(meta)
    j.save_state(st)
    return st


def _plant_askbrain_row(j, ts, *, topic="", ok=True):
    """ردِ مسیرِ پیامِ ورودی (ask-brain.jsonl) — همان شکلی که ask_brain._ledger
    می‌نویسد: ts ِ ISO + topic ("" یعنی DM/General)."""
    from datetime import datetime as _dt
    row = {"ts": _dt.fromtimestamp(float(ts)).isoformat(),
           "schema": "tg-ask-brain.v1", "ok": bool(ok), "topic": topic}
    j.ask_brain_path.parent.mkdir(parents=True, exist_ok=True)
    with j.ask_brain_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


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


def t_free_chat_needs_both_a_consumed_update_and_an_outer_reply():
    """قراردادِ سه-شاهدی (سختگیریِ ۰۷-۳۱ بعد از یک سبزِ کاذبِ واقعی + ممیزی):
    PASS فقط با (۱) cursor ِ outer جلو رفته، (۲) پاسخِ DM ِ خودِ باتِ outer،
    و (۳) ردِ مسیرِ **پیامِ متنی** در ask-brain — چون cursor با هر callback ی
    هم جلو می‌رود."""
    c, cl = Clock(), FakeClient()
    j = _journey(c, cl)
    _fresh(j)
    _center_config(j, last_offset=1000)
    _seed_to(j, "P1", prompt_ts=c.t, meta={"offset_at_prompt": 1000})
    _plant_send_row(j, ts=c.t + 30, stream="center", sha="abc123",
                    bot_role="outer")
    _plant_askbrain_row(j, c.t + 28)             # ردِ پیامِ متنیِ ورودی
    _center_config(j, last_offset=1007)          # آپدیت مصرف شد
    c.advance(600)
    j.tick()
    st = j.load_state()
    assert st["phases"]["P1"]["verdict"] == aj.VERDICT_PASS, st["phases"]["P1"]
    assert any("cursor" in e for e in st["phases"]["P1"]["evidence"])


def t_a_callback_tap_plus_a_periodic_card_is_not_a_conversation():
    """بازتولیدِ سناریوی ممیزی (P1 WEAK): مالک روی یک کارتِ کهنه ✅ می‌زند
    (callback ⇒ cursor جلو می‌رود) و کارتِ دوره‌ایِ مرکز هم در پنجره می‌نشیند
    — هیچ جمله‌ای نوشته نشده. نباید PASS شود؛ PARTIAL ِ صادق."""
    c, cl = Clock(), FakeClient()
    j = _journey(c, cl)
    _fresh(j)
    _center_config(j, last_offset=1000)
    _seed_to(j, "P1", prompt_ts=c.t, meta={"offset_at_prompt": 1000})
    _plant_send_row(j, ts=c.t + 30, stream="center", sha="hourly1",
                    bot_role="outer", chars=856)     # کارتِ دوره‌ای
    _center_config(j, last_offset=1001)              # فقط یک callback مصرف شد
    c.advance(600)
    j.tick()
    rec = j.load_state()["phases"]["P1"]
    assert rec["verdict"] != aj.VERDICT_PASS, rec
    assert rec["verdict"] == aj.VERDICT_PARTIAL, rec
    assert any("ask-brain" in e for e in rec["evidence"]), rec["evidence"]


def t_a_leg_engine_askbrain_row_is_not_a_message_anchor():
    """موتورِ پاها هم ask_brain صدا می‌زند ولی با topic=نامِ پا
    (center.py:1530) — نباید لنگرِ «پیامِ متنی» شمرده شود."""
    c, cl = Clock(), FakeClient()
    j = _journey(c, cl)
    _fresh(j)
    _center_config(j, last_offset=1000)
    _seed_to(j, "P1", prompt_ts=c.t, meta={"offset_at_prompt": 1000})
    _plant_send_row(j, ts=c.t + 30, stream="center", sha="abc999",
                    bot_role="outer")
    _plant_askbrain_row(j, c.t + 28, topic="lead")   # ردِ موتور، نه پیامِ مالک
    _center_config(j, last_offset=1007)
    c.advance(600)
    j.tick()
    rec = j.load_state()["phases"]["P1"]
    assert rec["verdict"] == aj.VERDICT_PARTIAL, rec


def t_a_spontaneous_organism_card_is_never_read_as_a_conversation():
    """بازتولیدِ دقیقِ سبزِ کاذبِ ۲۰۲۶-۰۷-۳۱ ۱۸:۰۰:۵۷ — ردیفِ DM ِ باتِ inner
    در حالی که هیچ آپدیتی مصرف نشده بود. باید PENDING بماند، نه PASS."""
    c, cl = Clock(), FakeClient()
    j = _journey(c, cl)
    _fresh(j)
    _center_config(j, last_offset=1000)
    _seed_to(j, "P1", prompt_ts=c.t, meta={"offset_at_prompt": 1000})
    _plant_send_row(j, ts=c.t + 30, stream=None, sha="c08279492294b840",
                    bot_role="inner", chars=421)
    c.advance(600)
    j.tick()
    st = j.load_state()
    assert st["phases"]["P1"]["verdict"] == aj.VERDICT_PENDING, st["phases"]["P1"]


def t_a_received_but_unanswered_message_is_partial_not_pass():
    """پیام رسید ولی جوابی نیامد: نه سبز، نه هیچ — PARTIAL ِ صادق."""
    c, cl = Clock(), FakeClient()
    j = _journey(c, cl)
    _fresh(j)
    _center_config(j, last_offset=1000)
    _seed_to(j, "P1", prompt_ts=c.t, meta={"offset_at_prompt": 1000})
    _center_config(j, last_offset=1003)
    c.advance(600)
    j.tick()
    st = j.load_state()
    assert st["phases"]["P1"]["verdict"] == aj.VERDICT_PARTIAL, st["phases"]["P1"]


# ─── capture ───────────────────────────────────────────────────────────────
def _plant_raw_note(j, name, body="", *, mid=900, chat=111, extra_fm=()):
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


def t_a_retouched_old_note_is_never_fresh_evidence():
    """بازتولیدِ دقیقِ ممیزی (P2 FALSE-PASS #1): نوتِ دیروز که همین الان
    بازنویسی شده — mtime نو، مهرِ نام کهنه. نباید شاهد شود."""
    c, cl = Clock(), FakeClient()
    j = _journey(c, cl)
    _fresh(j)
    _center_config(j)
    _seed_to(j, "P2", prompt_ts=c.t)
    # همین حالا نوشته می‌شود (mtime = الان) ولی مهرِ نام مالِ دیروز است
    _plant_raw_note(j, "2026-07-30 0900 خرید کهنه.md", "ثبت: قدیمی")
    c.advance(300)
    j.tick()
    rec = j.load_state()["phases"]["P2"]
    assert rec["verdict"] != aj.VERDICT_PASS, rec
    assert rec["verdict"] == aj.VERDICT_PENDING, rec


def t_a_note_from_a_message_before_our_prompt_is_not_evidence():
    """ممیزی P2 FALSE-PASS #2 (پنجرهٔ غلط): message_id ِ نوت کوچک‌تر از
    message_id ِ درخواستِ خودِ ماست ⇒ پیامش قبل از درخواست رفته."""
    c, cl = Clock(), FakeClient()
    j = _journey(c, cl)
    _fresh(j)
    _center_config(j)
    _seed_to(j, "P2", prompt_ts=c.t, prompt_mid=500)
    _plant_raw_note(j, "2026-07-31 1005 پیامِ قبلی.md", "ثبت: چیزی", mid=7)
    c.advance(300)
    j.tick()
    assert j.load_state()["phases"]["P2"]["verdict"] == aj.VERDICT_PENDING


def t_p2_never_eats_the_media_note_that_belongs_to_p3():
    """ممیزی P3 (دزدیِ شاهدِ خواهر): عکسِ زودرسِ مالک message_id/chat_id دارد
    و P2 ِ قدیمی آن را «متن» می‌خورد؛ حالا باید برای P3 بماند."""
    c, cl = Clock(), FakeClient()
    j = _journey(c, cl)
    _fresh(j)
    _center_config(j)
    _seed_to(j, "P2", prompt_ts=c.t)
    p = _plant_raw_note(j, "2026-07-31 1004 عکسِ دیوار.md",
                        "- منبع: تلگرام · chat_id: 111 · message_id: 901 · [photo]",
                        mid=901)
    c.advance(300)
    j.tick()
    st = j.load_state()
    assert st["phases"]["P2"]["verdict"] == aj.VERDICT_PENDING, st["phases"]["P2"]
    assert p.name not in json.dumps(st.get("consumed") or {}), \
        "نوتِ رسانه نباید توسطِ P2 مصرف شده باشد"


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
                    "- منبع: تلگرام · chat_id: 111 · message_id: 943 · [voice]",
                    mid=943, extra_fm=("file_id: AwACAgQ",))
    c.advance(300)
    j.tick()
    rec = j.load_state()["phases"]["P3"]
    assert rec["verdict"] == aj.VERDICT_PASS, rec
    assert any("file_id" in e for e in rec["evidence"]), rec["evidence"]


def t_a_pasted_photo_string_in_the_body_is_not_media():
    """ممیزی P3: «[photo]» ِ paste‌شده وسطِ متن رسانه نیست — فقط خطِ منبعِ
    خودِ producer («منبع: تلگرام · … · [photo]») یا file_id ِ فرانت‌متر."""
    c, cl = Clock(), FakeClient()
    j = _journey(c, cl)
    _fresh(j)
    _center_config(j)
    _seed_to(j, "P3", prompt_ts=c.t)
    _plant_raw_note(j, "2026-07-31 1012 لاگِ paste شده.md",
                    "این خطِ لاگ را کپی کردم: [photo] در فایلِ قدیمی", mid=944)
    c.advance(300)
    j.tick()
    assert j.load_state()["phases"]["P3"]["verdict"] == aj.VERDICT_PENDING


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


def t_an_agent_self_test_reminder_is_never_the_owners_tap():
    """بازتولیدِ RM-1 ِ زندهٔ ۰۷-۳۱ (ممیزی P4A FALSE-PASS): یک جلسهٔ ایجنت
    مستقیم در store یادآوریِ «خودآزمون» ساخت، due=+۲۴۰ — فقط ۶۰ ثانیه با
    PASS ِ کاذب فاصله داشت. حالا متنِ خودآزمونی و scope ِ غیرِ dm رد می‌شوند."""
    c, cl = Clock(), FakeClient()
    j = _journey(c, cl)
    _fresh(j)
    _center_config(j)
    _seed_to(j, "P4A", prompt_ts=c.t)
    _plant_reminders(j, [
        {"id": "RM-1",
         "text": "خودآزمونِ زنجیرهٔ یادآوری (سیستم خودش ساخت — کاری لازم نیست)",
         "due": c.t + 300, "scope": "dm", "leg": None, "created": c.t + 60,
         "done": False, "fired": False},
        {"id": "RM-2", "text": "یادآوریِ پا", "due": c.t + 900, "scope": "leg",
         "leg": "lead", "created": c.t + 61, "done": False, "fired": False}])
    c.advance(aj.DEFAULT_WINDOW_S + 60)
    j.tick()
    rec = j.load_state()["phases"]["P4A"]
    assert rec["verdict"] != aj.VERDICT_PASS, rec
    assert rec["meta"].get("reminder_id") is None, rec["meta"]


def t_a_real_half_hour_reminder_is_not_missed_by_the_window():
    """اصلاحِ ممیزی: «نیم ساعت دیگه» (۱۸۰۰ ثانیه) واقعی است و باید در پنجرهٔ
    ۲–۹۰ دقیقه بگنجد — سخت‌گیریِ کور که مالکِ واقعی را رد کند خودش دروغ است."""
    c, cl = Clock(), FakeClient()
    j = _journey(c, cl)
    _fresh(j)
    _center_config(j)
    _seed_to(j, "P4A", prompt_ts=c.t)
    _plant_reminders(j, [{"id": "RM-9", "text": "زنگ به مشتری", "due": c.t + 1860,
                          "scope": "dm", "leg": None, "created": c.t + 60,
                          "done": False, "fired": False}])
    c.advance(300)
    j.tick()
    assert j.load_state()["phases"]["P4A"]["verdict"] == aj.VERDICT_PASS


def t_reminder_fired_detection_needs_the_reminders_own_sha():
    """ممیزی P4B: «یک کارتِ DM آن حوالی بود» تحویل نیست — دکتر/قلب هر ۲۰-۳۰
    دقیقه کارت می‌فرستند. تحویل = ردیفی با digest ِ **خودِ متنِ یادآوری**
    (همان fire_text ی که مرکز می‌فرستد و tg_send_log از آن sha می‌سازد)."""
    import reminders as _rm
    import tg_send_log as _tsl

    c, cl = Clock(), FakeClient()
    j = _journey(c, cl)
    _fresh(j)
    _center_config(j)
    _seed_to(j, "P4B", prompt_ts=c.t, meta={})
    st = j.load_state()
    j._rec(st, "P4A")["meta"]["reminder_id"] = "RM-9"
    j.save_state(st)
    # ۱) شلیک‌نشده ⇒ PENDING
    item = {"id": "RM-9", "text": "آب", "due": c.t + 900,
            "created": c.t, "done": False, "fired": False}
    _plant_reminders(j, [item])
    c.advance(aj.DEFAULT_WINDOW_S + 60)
    j.tick()
    assert j.load_state()["phases"]["P4B"]["verdict"] == aj.VERDICT_PENDING
    # ۲) fired ولی فقط یک کارتِ بی‌ربط نزدیکِ همان لحظه ⇒ هنوز PENDING
    fired_at = c.t + 900
    item = {**item, "fired": True, "fired_ts": fired_at}
    _plant_reminders(j, [item])
    _plant_send_row(j, ts=fired_at + 2, stream="center", sha="doctor-card")
    c.advance(1200)
    j.tick()
    rec = j.load_state()["phases"]["P4B"]
    assert rec["verdict"] == aj.VERDICT_PENDING, rec
    assert any("شلیک ثبت شد" in e for e in rec["evidence"]), rec["evidence"]
    # ۳) ردیف با sha ِ خودِ متنِ یادآوری ⇒ PASS (نویسنده و خواننده یک متن)
    _plant_send_row(j, ts=fired_at + 3, stream="center",
                    sha=_tsl.digest(_rm.fire_text(item)))
    j.tick()
    assert j.load_state()["phases"]["P4B"]["verdict"] == aj.VERDICT_PASS


# ─── P5: سؤال از والت ──────────────────────────────────────────────────────
def t_ask_vault_pass_needs_cursor_plus_fresh_outer_content():
    """PASS ِ P5 = مصرفِ آپدیت + پاسخِ outer ی که محتوایش نه تکراریِ ۲۴ساعته
    است نه یادآوریِ خودکاشته. مالکِ واقعی همین ردپا را می‌سازد."""
    c, cl = Clock(), FakeClient()
    j = _journey(c, cl)
    _fresh(j)
    _center_config(j, last_offset=2000)
    _seed_to(j, "P5", prompt_ts=c.t, meta={"offset_at_prompt": 2000})
    _plant_send_row(j, ts=c.t + 40, stream="center", sha="vault-answer-1",
                    bot_role="outer")
    _center_config(j, last_offset=2003)
    c.advance(600)
    j.tick()
    rec = j.load_state()["phases"]["P5"]
    assert rec["verdict"] == aj.VERDICT_PASS, rec


def t_a_spontaneous_card_without_cursor_movement_never_passes_p5():
    """همان گونهٔ سبزِ کاذبِ P1 (کارتِ ۴۲۱ کاراکتریِ inner/دکتر) که ممیزی گفت
    در P5 هم زنده است: ردیفِ DM بدونِ هیچ آپدیتِ مصرف‌شده ⇒ PENDING."""
    c, cl = Clock(), FakeClient()
    j = _journey(c, cl)
    _fresh(j)
    _center_config(j, last_offset=2000)
    _seed_to(j, "P5", prompt_ts=c.t, meta={"offset_at_prompt": 2000})
    _plant_send_row(j, ts=c.t + 30, stream=None, sha="c08279492294b840",
                    bot_role="outer", chars=421)
    c.advance(600)
    j.tick()
    rec = j.load_state()["phases"]["P5"]
    assert rec["verdict"] == aj.VERDICT_PENDING, rec


def t_the_journeys_own_planted_reminder_is_not_an_ask_vault_answer():
    """ممیزی P5 FALSE-PASS (خود-ساخته): یادآوریِ P4A داخلِ پنجرهٔ P5 شلیک
    می‌شود و ردیفِ DM می‌سازد؛ حتی اگر مالک همان لحظه دکمه‌ای هم زده باشد
    (cursor جلو رفته)، آن ردیف جوابِ والت نیست."""
    import reminders as _rm
    import tg_send_log as _tsl

    c, cl = Clock(), FakeClient()
    j = _journey(c, cl)
    _fresh(j)
    _center_config(j, last_offset=2000)
    item = {"id": "RM-9", "text": "آب بخورم", "due": c.t + 60, "scope": "dm",
            "created": c.t - 600, "done": False, "fired": True,
            "fired_ts": c.t + 60}
    _plant_reminders(j, [item])
    st = _seed_to(j, "P5", prompt_ts=c.t, meta={"offset_at_prompt": 2000})
    st["phases"]["P4A"] = {**j._rec(st, "P4A"),
                           "meta": {"reminder_id": "RM-9"}}
    j.save_state(st)
    _plant_send_row(j, ts=c.t + 61, stream="center",
                    sha=_tsl.digest(_rm.fire_text(item)), bot_role="outer")
    _center_config(j, last_offset=2001)          # تپِ دکمهٔ خودِ یادآوری
    c.advance(600)
    j.tick()
    rec = j.load_state()["phases"]["P5"]
    assert rec["verdict"] != aj.VERDICT_PASS, rec


def t_a_recurring_24h_card_sha_is_not_an_ask_vault_answer():
    """ممیزی P5: کارتی که همین محتوا را در ۲۴ ساعتِ قبل هم فرستاده بود
    (دوره‌ای/قالبی) پاسخِ سؤالِ تازهٔ مالک نیست."""
    c, cl = Clock(), FakeClient()
    j = _journey(c, cl)
    _fresh(j)
    _center_config(j, last_offset=2000)
    _plant_send_row(j, ts=Clock().t - 3600, stream="center", sha="hourly-tpl",
                    bot_role="outer")            # همان محتوا، یک ساعت قبل
    _seed_to(j, "P5", prompt_ts=c.t, meta={"offset_at_prompt": 2000})
    _plant_send_row(j, ts=c.t + 40, stream="center", sha="hourly-tpl",
                    bot_role="outer")
    _center_config(j, last_offset=2003)
    c.advance(600)
    j.tick()
    rec = j.load_state()["phases"]["P5"]
    assert rec["verdict"] != aj.VERDICT_PASS, rec


# ─── P6: فرمانِ طبیعیِ گروه ────────────────────────────────────────────────
def t_autonomous_group_streams_never_pass_p6():
    """سه نمونهٔ زندهٔ ممیزی (P6 FALSE-PASS): digestِ stream=center، کارتِ
    leg-card-lead، کارتِ لولهٔ stream=lead — همه topic=22، هیچ‌کدام پاسخِ
    فرمانِ مالک نیستند."""
    for stream in ("center", "leg-card-lead", "lead"):
        c, cl = Clock(), FakeClient()
        j = _journey(c, cl)
        _fresh(j)
        _center_config(j)
        _seed_to(j, "P6", prompt_ts=c.t,
                 meta={"topic": 22, "chat": -1004475788460})
        _plant_send_row(j, ts=c.t + 60, stream=stream, sha=f"x-{stream}",
                        surface="group", topic=22, chat=-1004475788460)
        c.advance(600)
        j.tick()
        rec = j.load_state()["phases"]["P6"]
        assert rec["verdict"] != aj.VERDICT_PASS, (stream, rec)
        assert rec["verdict"] == aj.VERDICT_PENDING, (stream, rec)


def t_a_distinguishable_reply_stream_still_passes_p6():
    """ضدِ overcorrection: اگر مرکز روزی پاسخِ فرمان را با استریمِ متمایز
    (cmd-reply) بفرستد، همان باید سبز شود — گاردی که هرگز سبز نشود دروغِ
    خودش است."""
    c, cl = Clock(), FakeClient()
    j = _journey(c, cl)
    _fresh(j)
    _center_config(j)
    _seed_to(j, "P6", prompt_ts=c.t, meta={"topic": 22, "chat": -1004475788460})
    _plant_send_row(j, ts=c.t + 60, stream="cmd-reply", sha="reply1",
                    surface="group", topic=22, chat=-1004475788460)
    c.advance(600)
    j.tick()
    rec = j.load_state()["phases"]["P6"]
    assert rec["verdict"] == aj.VERDICT_PASS, rec
    assert any("cmd-reply" in e for e in rec["evidence"]), rec["evidence"]


def t_a_group_row_claimed_by_another_phase_is_invisible_to_p6():
    """دفترِ claim ِ سطحِ گروه (ممیزی §۴): ردیفی که فازِ دیگری قبلاً مصرف
    کرده دوباره شمرده نمی‌شود."""
    c, cl = Clock(), FakeClient()
    j = _journey(c, cl)
    _fresh(j)
    _center_config(j)
    st = _seed_to(j, "P6", prompt_ts=c.t,
                  meta={"topic": 22, "chat": -1004475788460})
    _plant_send_row(j, ts=c.t + 60, stream="cmd-reply", sha="reply1",
                    surface="group", topic=22, chat=-1004475788460)
    st = j.load_state()
    st["phases"]["P8"] = {**j._rec(st, "P8"), "verdict": aj.VERDICT_PASS}
    j._claim(st, "P8", "group_rows", f"{c.t + 60}|reply1")
    j.save_state(st)
    c.advance(600)
    j.tick()
    assert j.load_state()["phases"]["P6"]["verdict"] == aj.VERDICT_PENDING


# ─── P7: رفعِ مانع ─────────────────────────────────────────────────────────
def _plant_lead_tasks(j, tasks):
    j.lead_tasks_path.parent.mkdir(parents=True, exist_ok=True)
    j.lead_tasks_path.write_text(
        json.dumps({"seq": len(tasks), "tasks": tasks}, ensure_ascii=False),
        "utf-8")


def t_an_empty_blocked_snapshot_never_grades_everything():
    """ممیزی P7 (latent FALSE-PASS): snapshot ِ خالی فیلترِ id را خاموش می‌کرد
    و کارِ مارکردارِ **دیروز** PASS ِ فوری می‌شد. حالا پیش‌نیازِ غایب = BLOCKED."""
    c, cl = Clock(), FakeClient()
    j = _journey(c, cl)
    _fresh(j)
    _center_config(j)
    _seed_to(j, "P7", prompt_ts=c.t, meta={"blocked_before": {"blocked_ids": []}})
    _plant_lead_tasks(j, [{"id": "TASK-9", "state": "WORKING",
                           "text": "کارِ کهنه\n➕ اطلاعات مالک: Bondi",
                           "updated": c.t - 86400}])
    c.advance(600)
    j.tick()
    rec = j.load_state()["phases"]["P7"]
    assert rec["verdict"] == aj.VERDICT_BLOCKED, rec
    assert rec["verdict"] != aj.VERDICT_PASS


def t_a_marker_updated_before_the_prompt_is_stale_evidence():
    """ممیزی P7 (بی‌زمانی): مارکرِ «➕ اطلاعات مالک» ی که updated اش قبل از
    درخواست است، رفعِ مانعِ دیروز است نه امروز."""
    c, cl = Clock(), FakeClient()
    j = _journey(c, cl)
    _fresh(j)
    _center_config(j)
    _seed_to(j, "P7", prompt_ts=c.t,
             meta={"blocked_before": {"blocked_ids": ["TASK-1"]}})
    _plant_lead_tasks(j, [{"id": "TASK-1", "state": "WORKING",
                           "text": "آدرس؟\n➕ اطلاعات مالک: Parramatta",
                           "updated": c.t - 5000}])
    c.advance(600)
    j.tick()
    assert j.load_state()["phases"]["P7"]["verdict"] == aj.VERDICT_PENDING
    # و همان مارکر با updated ِ بعد از درخواست ⇒ PASS (مالکِ واقعی)
    _plant_lead_tasks(j, [{"id": "TASK-1", "state": "WORKING",
                           "text": "آدرس؟\n➕ اطلاعات مالک: Parramatta",
                           "updated": c.t + 100}])
    j.tick()
    assert j.load_state()["phases"]["P7"]["verdict"] == aj.VERDICT_PASS


# ─── P8: رأیِ مالک روی لیدِ آزمایشی ────────────────────────────────────────
def _plant_outcome(j, *, recorded_ts, event_type="accepted-measurement",
                   lead_id=None, correlation_id=None, proposal_id="pp-1",
                   leg_id="lead", payload=None, idem=None):
    """ردیفِ outcomes با **نویسندهٔ تولیدی** (outcome_store.record) — فقط
    recorded_at بعداً به ساعتِ تزریقیِ تست پین می‌شود."""
    import sys as _s
    _out = str(_OPS / "outcomes")
    if _out not in _s.path:
        _s.path.insert(0, _out)
    import sqlite3 as _sq

    import outcome_store as _os
    store = _os.OutcomeStore(path=j.outcomes_db_path)
    ev = {"event_type": event_type, "lead_id": lead_id,
          "correlation_id": correlation_id, "proposal_id": proposal_id,
          "leg_id": leg_id, "payload": payload or {},
          "idempotency_key": idem or f"t-{recorded_ts}-{lead_id}",
          "occurred_at": datetime_iso(recorded_ts)}
    assert store.record(ev)
    store._conn.close()                    # ویندوز: قفلِ باز = unlink ِ ناموفق
    con = _sq.connect(str(j.outcomes_db_path))
    con.execute("UPDATE outcomes SET recorded_at=? WHERE idempotency_key=?",
                (datetime_iso(recorded_ts), ev["idempotency_key"]))
    con.commit()
    con.close()


def datetime_iso(ts: float) -> str:
    from datetime import datetime as _dt
    return _dt.fromtimestamp(float(ts)).isoformat()


def t_an_autonomous_research_measurement_is_not_the_owners_vote():
    """بازتولیدِ ممیزی P8 FALSE-PASS: research_loop خودش accepted-measurement
    می‌نویسد (self_run=True، بدونِ source ِ tg-*) — رأیِ مالک نیست."""
    c, cl = Clock(), FakeClient()
    j = _journey(c, cl)
    _fresh(j)
    _center_config(j)
    _seed_to(j, "P8", prompt_ts=c.t,
             meta={"candidate": {"ok": True, "lead_id": "LEAD-J1"}})
    _plant_outcome(j, recorded_ts=c.t + 120, leg_id="research",
                   proposal_id="self-1",
                   payload={"self_run": True, "measurement_only": True,
                            "verifier": "research_loop"})
    c.advance(900)
    j.tick()
    rec = j.load_state()["phases"]["P8"]
    assert rec["verdict"] != aj.VERDICT_PASS, rec
    assert rec["verdict"] == aj.VERDICT_PENDING, rec


def t_a_tg_vote_on_someone_elses_lead_is_not_this_phases_vote():
    """جوش به لیدِ خودِ فاز (ممیزی P8): رأیِ tg ِ واقعی روی لیدِ دیگر —
    مثلاً کارتِ کهنهٔ دیروز — شاهدِ این فاز نیست."""
    c, cl = Clock(), FakeClient()
    j = _journey(c, cl)
    _fresh(j)
    _center_config(j)
    _seed_to(j, "P8", prompt_ts=c.t,
             meta={"candidate": {"ok": True, "lead_id": "LEAD-J1"}})
    _plant_outcome(j, recorded_ts=c.t + 120, lead_id="LEAD-OLD",
                   correlation_id="LEAD-OLD",
                   payload={"source": "tg-proposal-button",
                            "measurement_only": True})
    c.advance(900)
    j.tick()
    rec = j.load_state()["phases"]["P8"]
    assert rec["verdict"] != aj.VERDICT_PASS, rec
    assert any("وصل نیست" in e for e in rec["evidence"]), rec["evidence"]


def t_the_owners_button_vote_on_the_synthetic_lead_passes_p8():
    """مثبت: رأیِ دکمه (source=tg-proposal-button) روی همان لیدِ مصنوعیِ
    این فاز ⇒ PASS — گاردِ سخت نباید مالکِ واقعی را رد کند."""
    c, cl = Clock(), FakeClient()
    j = _journey(c, cl)
    _fresh(j)
    _center_config(j)
    _seed_to(j, "P8", prompt_ts=c.t,
             meta={"candidate": {"ok": True, "lead_id": "LEAD-J1"}})
    _plant_send_row(j, ts=c.t + 60, stream="lead", sha="card1",
                    surface="group", topic=22, chat=-1004475788460)
    _plant_outcome(j, recorded_ts=c.t + 120, lead_id="LEAD-J1",
                   correlation_id="LEAD-J1",
                   payload={"owner_verdict_raw": "accepted",
                            "source": "tg-proposal-button",
                            "measurement_only": True})
    c.advance(900)
    j.tick()
    rec = j.load_state()["phases"]["P8"]
    assert rec["verdict"] == aj.VERDICT_PASS, rec
    assert any("tg-proposal-button" in e for e in rec["evidence"]), rec["evidence"]


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
    for part in aj.split_report(report):
        assert len(part) <= 4096, len(part)     # سقفِ سختِ تلگرام
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
    # حذفِ تسکِ ناموجود باید صادقانه گزارش شود، نه crash — و سفر هرگز
    # «متوقف شدم» ادعا نکند وقتی حذف نشده (ممیزی §5b).
    schtask = st["phases"]["P12"]["meta"]["schtask"]
    assert schtask["ok"] is False, schtask
    assert any("زمان‌بندی" in e for e in st["phases"]["P12"]["evidence"]), \
        st["phases"]["P12"]["evidence"]


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
    # ممیزی §6 ردیف ۱۶: فازِ بی‌درخواست هم قابلیتش سنجیده می‌شود — این‌جا
    # URL ِ تونل غایب است ⇒ BLOCKED ِ صادق (نه NOT-RUN ِ گنگ، نه TIMEOUT).
    assert st["phases"]["P9"]["verdict"] == aj.VERDICT_BLOCKED, st["phases"]["P9"]
    assert any("نوبتِ درخواست نرسید" in e
               for e in st["phases"]["P9"]["evidence"]), st["phases"]["P9"]
    assert st["phases"]["P1"]["verdict"] != aj.VERDICT_PASS
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
    # اصلاحِ ممیزی (P9 — «سوییت خودش باگ را برکت می‌داد»): ضربهٔ بی‌auth ِ
    # دروازه (کراولر/اسکنر/شِل) دیگر PASS نیست؛ صادقانه PENDING.
    assert rec["verdict"] == aj.VERDICT_PENDING, rec
    assert any("authed نیست" in e for e in rec["evidence"]), rec["evidence"]
    # تپِ واقعیِ مالک = ردیفِ authed روی مسیرِ api (همان شکلی که خودِ دروازه
    # می‌نویسد: بعد از عبورِ initData از دیوارِ HMAC).
    with j.miniapp_hits_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": time.time(), "path": "/api/miniapp",
                            "ok": True, "authed": True}) + "\n")
    j.tick()
    rec = j.load_state()["phases"]["P9"]
    assert rec["verdict"] == aj.VERDICT_PASS, rec
    assert any(e.startswith(aj.OWNER_PREFIX) and "HMAC" in e
               for e in rec["evidence"]), rec["evidence"]


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


# ─── اثباتِ قابلیت روی ماژولِ تولیدیِ واقعی (همه در پوشهٔ موقت) ─────────────
def t_capture_proof_writes_a_real_note_and_dedups_the_second_send():
    """P2 — `capture.handle` ِ واقعی: نوت با message_id/chat_id، و ارسالِ دوم
    dedup. نه یک بایت داخلِ والتِ تحتِ آزمون."""
    j = _journey()
    _fresh(j)
    with _Flags(**PROOF_FLAGS):
        cap = j._prove_capture_text()
    assert cap["ok"], cap
    assert ".md" in cap["line"] and "dedup" in cap["line"], cap["line"]
    assert "ثبت شد" in cap["line"], "ack ِ واقعی باید در شاهد بیاید"
    assert not list(j.raw_dir.glob("*.md")) if j.raw_dir.exists() else True


def t_media_proof_keeps_file_id_and_refuses_a_fake_transcript():
    j = _journey()
    _fresh(j)
    with _Flags(**PROOF_FLAGS):
        cap = j._prove_capture_media()
    assert cap["ok"], cap
    assert "file_id" in cap["line"] and "[voice]" in cap["line"], cap["line"]
    assert "transcript" in cap["line"], "صداقتِ «متن‌سازی نیست» باید ادعا شود"


def t_reminder_proof_covers_parse_fire_and_the_quiet_window():
    """پارس + شلیک + سکوتِ شب — و هیچ‌کدام در storeِ زندهٔ یادآوری."""
    j = _journey()
    _fresh(j)
    with _Flags(**PROOF_FLAGS):
        cap = j._prove_reminders()
    assert cap["ok"], cap
    assert "۱۵ دقیقه" in cap["line"] and "۲۳:۳۰" in cap["line"], cap["line"]
    assert not j.reminders_path.exists(), "اثبات نباید یادآوریِ واقعی بسازد"


def t_leg_command_proof_maps_every_verb_and_never_swallows_a_work_sentence():
    import leg_commands as lc

    j = _journey()
    with _Flags(**PROOF_FLAGS):
        cap = j._prove_leg_command()
    assert cap["ok"], cap
    # گاردِ بی‌دندان نباشد. لنگرِ جهش باید **یکتا** باشد: نگاشتِ پنج فرمان را
    # دست‌نخورده می‌گذاریم و فقط جملهٔ کار را می‌بلعیم — وگرنه چکِ اولِ اثبات
    # می‌ترکد و هرگز معلوم نمی‌شود گاردِ «بلعیدن» زنده است یا نه.
    orig = lc.classify
    lc.classify = lambda t, _o=orig: _o(t) or "status"
    try:
        bad = j._prove_leg_command()
    finally:
        lc.classify = orig
    assert not bad["ok"] and "کار گم می‌شود" in bad["line"], bad
    assert not bad.get("blocked"), "بلعیدنِ کار نقص است، نه فلگِ خاموش"


def t_stuck_lead_proof_unblocks_and_stamps_the_owner_line():
    j = _journey()
    _fresh(j)
    with _Flags(**PROOF_FLAGS):
        cap = j._prove_leg_resolve()
    assert cap["ok"], cap
    assert "BLOCKED" in cap["line"] and "Parramatta" in cap["line"], cap["line"]
    assert not j.lead_tasks_path.exists(), "کارِ آزمایشی نباید در صفِ زنده بنشیند"


def t_lead_card_proof_builds_a_ready_card_without_sending_anything():
    cl = FakeClient()
    j = _journey(client=cl)
    with _Flags(**PROOF_FLAGS):
        cap = j._prove_lead_card()
    assert cap["ok"], cap
    assert "draft" in cap["line"] and int(cap["card_chars"]) > 50, cap
    assert cl.sent == [], "اثباتِ کارت هرگز چیزی نمی‌فرستد"


def t_miniapp_proof_wants_200_on_the_shell_and_403_on_the_api():
    c = Clock()
    http = FakeHttp()
    j = _journey(c, http_fn=http)
    _fresh(j)
    j.miniapp_url_path.parent.mkdir(parents=True, exist_ok=True)
    j.miniapp_url_path.write_text(json.dumps({"url": "https://probe.invalid"}),
                                  "utf-8")
    cap = j._prove_miniapp()
    assert cap["ok"], cap
    assert http.calls == ["https://probe.invalid/miniapp",
                          "https://probe.invalid/api/miniapp"], http.calls
    # دیوارِ باز = قابلیتِ خراب، نه «مالک نبود»
    j2 = _journey(c, http_fn=FakeHttp(api=200))
    open_wall = j2._prove_miniapp()
    assert not open_wall["ok"] and not open_wall.get("blocked"), open_wall
    # URL غایب = پیش‌نیازِ ساختاری، نه نقص
    j.miniapp_url_path.unlink()
    assert j._prove_miniapp().get("blocked") is True


def t_question_budget_proof_round_trips_submit_ask_and_answer():
    j = _journey()
    _fresh(j)
    with _Flags(**PROOF_FLAGS):
        cap = j._prove_qbudget()
    assert cap["ok"], cap
    assert "Q-" in cap["line"], cap["line"]
    assert not j.qbudget_path.exists(), "بودجهٔ زنده نباید مصرف شود"


# ─── P10: تحویلِ سؤال بودجه را مصرف می‌کند (ممیزی، سؤالِ دوباره) ───────────
def t_p10_marks_the_question_asked_so_the_centre_wont_resend_it():
    """ممیزی P10: submit دیگر asked=True نمی‌کند؛ بدونِ mark_asked ِ ما،
    ضربانِ مرکز همان سؤال را pending می‌بیند و **دوباره** می‌فرستد."""
    import question_budget as qb

    c, cl = Clock(), FakeClient()
    j = _journey(c, cl)
    _fresh(j)
    _center_config(j)
    st = j.load_state()
    rec = j._rec(st, "P10")
    with _Flags(**PROOF_FLAGS):
        ok = j._prompt_p10(st, rec)
        assert ok, rec
        assert rec["meta"].get("marked_asked") is True, rec
        assert qb.pending(c.t) is None, \
            "سؤالِ تحویل‌شده نباید در pending بماند (سؤالِ دوباره = اسپم)"


# ─── P11: جمع‌بندیِ شب — تطبیقِ محتوایی، نه مجاورتی ────────────────────────
NOW_EVE = time.mktime((2026, 7, 31, 22, 0, 0, 0, 0, -1))


def t_evening_wrap_never_claims_an_arbitrary_dm_row():
    """ممیزی P11: «هر کارتی بعد از ۲۱:۲۵» متناظرِ جمع‌بندی نیست و claim ِ آن
    ردیف را از بقیه می‌دزدید. سندِ ارسال cursor ِ strict است؛ ردیف فقط با
    sha ِ متنِ بازساختهٔ خودِ brief.evening_text مصرف می‌شود."""
    import tg_send_log as _tsl

    import brief as _bf

    c, cl = Clock(NOW_EVE), FakeClient()
    j = _journey(c, cl)
    _fresh(j)
    _center_config(j, last_evening_day="2026-07-31")
    _seed_to(j, "P11", prompt_ts=c.t, prompt_mid=None)
    _plant_send_row(j, ts=c.t + 30, stream="center", sha="doctor-card-eve",
                    bot_role="outer")            # کارتِ بی‌ربطِ همان حوالی
    c.advance(60)
    j.tick()
    st = j.load_state()
    rec = st["phases"]["P11"]
    assert rec["verdict"] == aj.VERDICT_PASS, rec        # cursor ِ strict = سند
    blob = json.dumps(st.get("consumed") or {})
    assert "doctor-card-eve" not in blob, "ردیفِ دلبخواه نباید مصرف شود"
    assert any("sha" in e for e in rec["evidence"]), rec["evidence"]
    # و وقتی ردیفی با sha ِ خودِ متنِ جمع‌بندی هست ⇒ همان مصرف می‌شود
    _fresh(j)
    _center_config(j, last_evening_day="2026-07-31")
    _seed_to(j, "P11", prompt_ts=c.t, prompt_mid=None)
    ccfg = json.loads(j.center_config_path.read_text("utf-8"))
    expect = _tsl.digest(_bf.evening_text(now=c.t + 60, cfg=ccfg))
    _plant_send_row(j, ts=c.t + 30, stream="center", sha=expect,
                    bot_role="outer")
    c.advance(60)
    j.tick()
    st = j.load_state()
    assert st["phases"]["P11"]["verdict"] == aj.VERDICT_PASS
    assert expect in json.dumps(st.get("consumed") or {}), \
        "ردیفِ هم‌sha باید توسطِ P11 مصرف شده باشد"


def t_evening_wrap_before_the_cursor_is_pending():
    c, cl = Clock(NOW_EVE), FakeClient()
    j = _journey(c, cl)
    _fresh(j)
    _center_config(j)                            # بدونِ last_evening_day
    _seed_to(j, "P11", prompt_ts=c.t, prompt_mid=None)
    c.advance(60)
    j.tick()
    assert j.load_state()["phases"]["P11"]["verdict"] == aj.VERDICT_PENDING


# ─── ساختاری (ممیزی §5a): درخواستِ ساختاراً ناساختنی سفر را قفل نمی‌کند ────
def t_a_structurally_unbuildable_prompt_becomes_blocked_and_advances():
    """URL ِ تونل غایب: قبلاً P9 تا سقفِ ۶ ساعت می‌چرخید و P10..P12 هرگز
    اجرا نمی‌شدند (سکوت به‌جای خبر). حالا بعد از MAX_ATTEMPTS حکمِ صادقِ
    BLOCKED می‌گیرد و مکان‌نما رد می‌شود."""
    c, cl = Clock(), FakeClient()
    j = _journey(c, cl)
    _fresh(j)
    _center_config(j)
    _seed_to(j, "P9", prompt_ts=None)
    try:
        j.miniapp_url_path.unlink()
    except OSError:
        pass
    for _ in range(aj.MAX_ATTEMPTS):
        c.advance(900)
        j.tick()
    st = j.load_state()
    assert st["phases"]["P9"]["verdict"] == aj.VERDICT_BLOCKED, st["phases"]["P9"]
    assert st["phase_idx"] > [i for i, p in enumerate(aj._PHASES)
                              if p["key"] == "P9"][0], "باید رد شده باشد"


def t_a_pure_send_failure_still_never_advances():
    """مرزِ اصلاحِ §5a: شکستِ **ارسال** (تلگرام قطع) ساختاری نیست — رفتارِ
    قدیمی می‌ماند: PENDING و صفر پیشروی (وگرنه قطعیِ شبکه همهٔ فازها را
    BLOCKED ِ کاذب می‌کرد)."""
    c = Clock()
    cl = FakeClient(fail=True)
    j = _journey(c, cl)
    _fresh(j)
    _center_config(j)
    _seed_to(j, "P1", prompt_ts=None)
    for _ in range(aj.MAX_ATTEMPTS + 2):
        c.advance(900)
        j.tick()
    st = j.load_state()
    assert st["phases"]["P1"]["verdict"] == aj.VERDICT_PENDING, st["phases"]["P1"]
    assert st["phase_idx"] == 1, st["phase_idx"]


# ─── دفترِ claim (ممیزی §۴): پس‌گرفتنِ حکم claim را آزاد می‌کند ────────────
def t_a_regraded_verdict_releases_its_claims():
    """فایلِ زنده همین حالا یک claim ِ یتیم دارد (P1 ِ سبزِ کاذب که TIMEOUT
    شد ولی ردیفش مصرف‌شده ماند). حالا: حکمِ غیرِ PASS ⇒ claim آزاد."""
    c, cl = Clock(), FakeClient()
    j = _journey(c, cl)
    _fresh(j)
    _center_config(j, last_offset=1000)
    st = _seed_to(j, "P5", prompt_ts=c.t, meta={"offset_at_prompt": 1000})
    st = j.load_state()
    rec1 = j._rec(st, "P1")
    rec1["verdict"] = aj.VERDICT_TIMEOUT          # حکمِ برگشته
    j._claim(st, "P1", "dm_rows", f"{c.t + 30}|vault-answer-9")
    j.save_state(st)
    _plant_send_row(j, ts=c.t + 30, stream="center", sha="vault-answer-9",
                    bot_role="outer")
    _center_config(j, last_offset=1003)
    c.advance(600)
    j.tick()
    st = j.load_state()
    assert "P1" not in (st.get("consumed") or {}), st.get("consumed")
    assert st["phases"]["P5"]["verdict"] == aj.VERDICT_PASS, \
        "ردیفِ آزادشده باید دوباره دیدنی باشد"


def t_a_passing_phase_keeps_its_claims_and_legacy_buckets_survive():
    c, cl = Clock(), FakeClient()
    j = _journey(c, cl)
    _fresh(j)
    _center_config(j)
    st = j.load_state()
    st["phases"] = {"P2": {**j._rec(st, "P2"), "verdict": aj.VERDICT_PASS}}
    j._claim(st, "P2", "raw_notes", "note-a.md")
    st["consumed"]["raw_notes"] = ["legacy-b.md"]     # شکلِ تختِ قدیمی
    j._release_stale_claims(st)
    assert "P2" in st["consumed"], st["consumed"]
    assert "note-a.md" in j._consumed(st, "raw_notes")
    assert "legacy-b.md" in j._consumed(st, "raw_notes"), \
        "خواندنِ شکلِ قدیمی نباید بشکند (فایلِ زندهٔ در جریان)"


# ─── ساختاری (ممیزی §5b): کلیدِ کشتار با تسکِ واقعی می‌خواند ───────────────
def t_the_default_task_name_matches_the_live_scheduled_task():
    assert aj.DEFAULT_TASK_NAME == "OCTOPUS-Journey-Tick", aj.DEFAULT_TASK_NAME


def t_deleting_a_missing_task_is_reported_honestly_not_claimed():
    """Query-اول: تسکِ نبوده «حذف شد» ادعا نمی‌شود؛ پیامِ not-found برمی‌گردد
    و Delete اصلاً صدا زده نمی‌شود."""
    j = _journey(task_name="OctopusJourneyTestTaskDoesNotExist")
    r = j._delete_scheduled_task()
    assert r["ok"] is False, r
    assert r.get("found") is False, r
    assert "task not found" in str(r.get("msg")), r


# ─── حکمِ سه‌حالته: PASS / CAPABILITY-OK / BROKEN ──────────────────────────
def t_capability_ok_replaces_timeout_when_the_owner_never_taps():
    """قلبِ خواستهٔ مالک: هیچ نوتی نیامد، ولی خودِ capture در-پروسه اثبات شد ⇒
    CAPABILITY-OK، نه TIMEOUT ِ کور."""
    c, cl = Clock(), FakeClient()
    j = _journey(c, cl)
    _fresh(j)
    _center_config(j)
    _seed_to(j, "P2", prompt_ts=c.t)
    with _Flags(**PROOF_FLAGS):
        for _ in range(aj.MAX_ATTEMPTS):
            c.advance(aj.DEFAULT_WINDOW_S + 60)
            j.tick()
    rec = j.load_state()["phases"]["P2"]
    assert rec["verdict"] == aj.VERDICT_CAPABILITY_OK, rec
    assert any(e.startswith(aj.OWNER_PREFIX) for e in rec["evidence"]), rec
    assert any(e.startswith(aj.CAP_PREFIX) for e in rec["evidence"]), rec
    assert j.load_state()["phase_idx"] > 2, "فازِ پایانی باید جلو برود"


def t_a_broken_capability_is_loud_and_terminal():
    """ماژولِ تولیدی می‌ترکد ⇒ BROKEN (بلندترین خبر)، نه TIMEOUT ِ مبهم."""
    import capture

    c, cl = Clock(), FakeClient()
    j = _journey(c, cl)
    _fresh(j)
    _center_config(j)
    _seed_to(j, "P2", prompt_ts=c.t)
    orig = capture.handle

    def boom(*_a, **_kw):
        raise RuntimeError("مسیرِ والت خراب است")
    capture.handle = boom
    try:
        with _Flags(**PROOF_FLAGS):
            for _ in range(aj.MAX_ATTEMPTS):
                c.advance(aj.DEFAULT_WINDOW_S + 60)
                j.tick()
    finally:
        capture.handle = orig
    rec = j.load_state()["phases"]["P2"]
    assert rec["verdict"] == aj.VERDICT_BROKEN, rec
    line = [e for e in rec["evidence"] if e.startswith(aj.CAP_PREFIX)]
    assert line and "RuntimeError" in line[0], rec["evidence"]
    assert "خطا" in line[0], line


def t_a_disarmed_flag_is_blocked_not_broken():
    """فلگِ خاموش نقص نیست — پیش‌نیازِ ساختاریِ غایب است."""
    c, cl = Clock(), FakeClient()
    j = _journey(c, cl)
    _fresh(j)
    _center_config(j)
    _seed_to(j, "P2", prompt_ts=c.t)
    with _Flags(OCTOPUS_TG_CAPTURE="0"):
        for _ in range(aj.MAX_ATTEMPTS):
            c.advance(aj.DEFAULT_WINDOW_S + 60)
            j.tick()
    rec = j.load_state()["phases"]["P2"]
    assert rec["verdict"] == aj.VERDICT_BLOCKED, rec
    assert any("خاموش" in e for e in rec["evidence"]), rec["evidence"]


def t_owner_evidence_still_outranks_the_in_process_proof():
    """اثبات جای مشاهده را نمی‌گیرد: نوتِ واقعیِ مالک ⇒ همان PASS ِ قدیمی."""
    c, cl = Clock(), FakeClient()
    j = _journey(c, cl)
    _fresh(j)
    _center_config(j)
    _seed_to(j, "P2", prompt_ts=c.t)
    p = _plant_raw_note(j, "2026-07-31 1006 رنگ.md", "ثبت: خرید رنگ ۵۰ دلار")
    with _Flags(**PROOF_FLAGS):
        c.advance(300)
        j.tick()
    rec = j.load_state()["phases"]["P2"]
    assert rec["verdict"] == aj.VERDICT_PASS, rec
    assert any(p.name in e and e.startswith(aj.OWNER_PREFIX)
               for e in rec["evidence"]), rec["evidence"]


def t_the_miniapp_probe_hit_is_never_read_as_the_owners_tap():
    """ضربهٔ خودِ اثبات هم در miniapp-hits می‌نشیند — اگر شمرده شود، همان سبزِ
    کاذبی می‌شود که P1 یک‌بار خورد."""
    c = Clock()
    j = _journey(c, http_fn=FakeHttp())
    _fresh(j)
    _center_config(j)
    j.miniapp_url_path.parent.mkdir(parents=True, exist_ok=True)
    j.miniapp_url_path.write_text(json.dumps({"url": "https://probe.invalid"}),
                                  "utf-8")
    _seed_to(j, "P9", prompt_ts=c.t, meta={"url_present": True})
    j.miniapp_hits_path.parent.mkdir(parents=True, exist_ok=True)
    with j.miniapp_hits_path.open("a", encoding="utf-8") as f:      # ضربهٔ پروب
        f.write(json.dumps({"ts": c.t + 1, "path": "/miniapp", "ok": True,
                            "authed": False}) + "\n")
    j.tick()
    rec = j.load_state()["phases"]["P9"]
    assert rec["verdict"] == aj.VERDICT_PENDING, rec
    assert rec["meta"]["capability"]["ok"] is True, rec["meta"]
    with j.miniapp_hits_path.open("a", encoding="utf-8") as f:      # تپِ خودِ مالک
        f.write(json.dumps({"ts": c.t + 10, "path": "/api/miniapp", "ok": True,
                            "authed": True}) + "\n")
    j.tick()
    rec = j.load_state()["phases"]["P9"]
    assert rec["verdict"] == aj.VERDICT_PASS, rec
    assert any("initData ِ معتبر" in e for e in rec["evidence"]), rec["evidence"]


def t_an_unauthed_shell_hit_is_capability_not_the_owner():
    """ممیزی P9 (قوی‌ترین سبزِ کاذب): تونل عمومی است و کراولرِ preview ِ
    تلگرام/اسکنرها بلافاصله ردیفِ بی‌auth می‌سازند؛ سرِ پایانِ صبر حکم
    CAPABILITY-OK است نه PASS."""
    c = Clock()
    j = _journey(c, http_fn=FakeHttp())
    _fresh(j)
    _center_config(j)
    j.miniapp_url_path.parent.mkdir(parents=True, exist_ok=True)
    j.miniapp_url_path.write_text(json.dumps({"url": "https://probe.invalid"}),
                                  "utf-8")
    _seed_to(j, "P9", prompt_ts=c.t, meta={"url_present": True})
    j.miniapp_hits_path.parent.mkdir(parents=True, exist_ok=True)
    with j.miniapp_hits_path.open("a", encoding="utf-8") as f:  # کراولر/اسکنر
        f.write(json.dumps({"ts": c.t + 8, "path": "/miniapp", "ok": True,
                            "authed": False}) + "\n")
        f.write(json.dumps({"ts": c.t + 9, "path": "/api/miniapp", "ok": False,
                            "authed": False}) + "\n")
    for _ in range(aj.MAX_ATTEMPTS):
        c.advance(aj.DEFAULT_WINDOW_S + 60)
        j.tick()
    rec = j.load_state()["phases"]["P9"]
    assert rec["verdict"] == aj.VERDICT_CAPABILITY_OK, rec
    assert rec["verdict"] != aj.VERDICT_PASS


# ─── گاردِ آلودگی: اثبات‌ها هیچ بایتی از درختِ زنده را تکان نمی‌دهند ────────
def _snapshot(root) -> dict:
    out = {}
    for p in sorted(Path(root).rglob("*")):
        try:
            if p.is_file():
                s = p.stat()
                out[str(p)] = (s.st_mtime_ns, s.st_size)
        except OSError:
            continue
    return out


def t_running_every_proof_leaves_live_state_and_the_vault_untouched():
    """درسِ «هر مسیرِ تحتِ آزمون را ایزوله کن»، این‌بار برعکس: خودِ اثبات‌ها
    نباید هیچ مسیری را لمس کنند — نه state، نه vault، نه env."""
    c = Clock()
    j = _journey(c, http_fn=FakeHttp())
    _fresh(j)
    _center_config(j)
    j.miniapp_url_path.parent.mkdir(parents=True, exist_ok=True)
    j.miniapp_url_path.write_text(json.dumps({"url": "https://probe.invalid"}),
                                  "utf-8")
    before = _snapshot(ENV["root"])
    env_before = dict(os.environ)
    state_before = opslib.STATE_DIR
    with _Flags(**PROOF_FLAGS):
        caps = [j._prove_capture_text(), j._prove_capture_media(),
                j._prove_reminders(), j._prove_leg_command(),
                j._prove_leg_resolve(), j._prove_lead_card(),
                j._prove_miniapp(), j._prove_qbudget()]
    assert all(cap.get("ok") for cap in caps), \
        [cap["line"] for cap in caps if not cap.get("ok")]
    after = _snapshot(ENV["root"])
    assert after == before, {
        "added": sorted(set(after) - set(before)),
        "changed": sorted(k for k in set(after) & set(before)
                          if after[k] != before[k])}
    assert opslib.STATE_DIR == state_before, opslib.STATE_DIR
    assert os.environ.get("OCTOPUS_STATE_DIR") == \
        env_before.get("OCTOPUS_STATE_DIR")
    assert os.environ.get("OCTOPUS_LEG_TASKS_DIR") == \
        env_before.get("OCTOPUS_LEG_TASKS_DIR")


# ─── کارنامهٔ سه‌گروهی ─────────────────────────────────────────────────────
def t_the_final_report_groups_every_phase_into_three_buckets_with_counts():
    c, cl = Clock(), FakeClient()
    j = _journey(c, cl)
    _fresh(j)
    _center_config(j)
    _seed_to(j, "P12", prompt_ts=None)              # همهٔ فازهای قبلی PASS
    st = j.load_state()
    st["phases"]["P2"]["verdict"] = aj.VERDICT_CAPABILITY_OK
    st["phases"]["P2"]["evidence"] = [aj.CAP_PREFIX + "capture ِ متن سالم"]
    st["phases"]["P3"]["verdict"] = aj.VERDICT_BROKEN
    st["phases"]["P3"]["evidence"] = [aj.CAP_PREFIX + "خطا — RuntimeError: بوم"]
    st["phases"]["P4A"]["verdict"] = aj.VERDICT_TIMEOUT
    j.save_state(st)
    report = j.compose_report(j.load_state())
    graded = len(aj._PHASES) - 1
    want = {aj.GROUP_SEEN: graded - 3, aj.GROUP_CAPABLE: 1,
            aj.GROUP_BROKEN: 1, aj.GROUP_UNKNOWN: 1}
    for head, n in want.items():
        assert f"<b>{head}</b> ({aj._fa(n)})" in report, (head, n, report[:400])
    assert f"✅ {aj._fa(want[aj.GROUP_SEEN])} · 🟢 ۱ · 🔴 ۱ · ⌛️ ۱" in report
    assert "capture ِ متن سالم" in report, "شاهدِ هر فاز باید بماند"
    assert "خطا — RuntimeError: بوم" in report
    assert "<b>کارهای بازِ تو</b>" in report
    groups = j.report_groups(j.load_state())
    assert [ph["key"] for ph, _r in groups[aj.GROUP_BROKEN]] == ["P3"]
    assert sum(len(v) for v in groups.values()) == graded


def t_an_empty_broken_group_is_still_stated_out_loud():
    """«۰ خراب» خودش خبرِ خوبی است — نبودِ سرگروه یعنی مالک باید حدس بزند."""
    c, cl = Clock(), FakeClient()
    j = _journey(c, cl)
    _fresh(j)
    _center_config(j)
    _seed_to(j, "P12", prompt_ts=None)
    report = j.compose_report(j.load_state())
    assert f"<b>{aj.GROUP_BROKEN}</b> (۰)" in report, report[-600:]
    assert "— هیچ" in report


def t_the_report_is_one_message_and_splits_only_when_it_overflows():
    c, cl = Clock(), FakeClient()
    j = _journey(c, cl)
    _fresh(j)
    _center_config(j)
    _seed_to(j, "P12", prompt_ts=None)
    assert len(aj.split_report(j.compose_report(j.load_state()))) == 1
    long = "\n".join(f"▸ خطِ {i} " + "پ" * 120 for i in range(200))
    parts = aj.split_report(long)
    assert len(parts) > 1, len(long)
    assert all(len(p) <= 4096 for p in parts), [len(p) for p in parts]
    assert parts[1].startswith("(ادامهٔ کارنامه"), parts[1][:40]
    assert sum(p.count("▸") for p in parts) == 200, "هیچ خطی نباید گم شود"


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
