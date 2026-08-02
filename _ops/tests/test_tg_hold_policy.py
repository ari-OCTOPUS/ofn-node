#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_tg_hold_policy — هفت اثباتِ رأیِ مالک VQ-TG-HOLD-001 (§۸)، با fake transport.

متنِ رأی، §۸: «بعد از پیاده‌سازی با fake transport و runtime receipt اثبات کن:
  ۱ یک critical جدید → Inner DM
  ۲ یک approval → بات دارای handler
  ۳ یک پیام عادی جدید → digest
  ۴ یک duplicate → HOLD
  ۵ یک recovery → receipt
  ۶ یک پیام هسته‌ای → هرگز گروه
  ۷ backlog تاریخی → صفر ارسال»

fake transport = کلاینت‌های ساختگی با قراردادِ سنجیده‌شدهٔ واقعی؛ ارسالِ
واقعی صفر. runtime receipt بعد از ری‌استارت از tg-send-log می‌آید.
"""
import json
import os
import sys
import time
from pathlib import Path

import harness

ENV = harness.setup("tg-hold-policy")

_OPS = Path(__file__).resolve().parent.parent
_TC = str(_OPS / "telegram_center")
if _TC not in sys.path:
    sys.path.insert(0, _TC)

import hold_policy as hp  # noqa: E402
import surface_policy as sp  # noqa: E402
import surface_router as sr  # noqa: E402

OWNER = 6150431610
GROUP = -1004475788460
CFG = {"chat_id": GROUP, "topics": {"lead": 22, "system": 28}}
NOW = 1_785_400_000.0                          # clockِ تزریقی — نه ساعتِ دیوار


def _fresh():
    """state ِ تمیز برای هر سنجه — فایل‌های ایزولهٔ harness پاک می‌شوند."""
    for p in (hp._state_path(), hp._buffer_path(), hp._urgent_path(),
              hp._viewed_path(), hp._markers_path()):
        try:
            p.unlink()
        except OSError:
            pass


class _FakeClient:
    def __init__(self, name):
        self.name = name
        self.owner_chat_id = OWNER
        self.center_chat_id = GROUP
        self.sent = []

    def wired(self):
        return True

    def send(self, text, *, chat_id=None, topic_id=None, keyboard=None,
             pin=False, stream="center"):
        self.sent.append({"text": text, "chat_id": chat_id,
                          "topic_id": topic_id, "stream": stream})
        return 4000 + len(self.sent)


def _flag(on: bool):
    if on:
        os.environ["OCTOPUS_TG_SPLIT_V1"] = "1"
    else:
        os.environ.pop("OCTOPUS_TG_SPLIT_V1", None)


def _flush_urgent_like_the_center(clients) -> list:
    """همان حلقه‌ای که center.beat می‌زند — این‌جا با کلاینتِ fake."""
    sent = []
    upto = None
    for u in hp.urgent_pending(now=NOW + 5, cap=5):
        cl, cid, tid = sr.resolve("center-urgent", clients=clients, cfg=CFG)
        if cl is None:
            break
        cl.send(str(u.get("text") or ""), chat_id=cid, topic_id=tid,
                stream="center-urgent")
        sent.append(u)
        upto = float(u.get("ts") or 0)
    if upto:
        hp.mark_urgent_flushed(upto)
    return sent


# ── اثباتِ ۱: critical ِ جدید → Inner DM ────────────────────────────────────
def t_proof1_a_new_critical_reaches_the_inner_dm():
    _fresh()
    _flag(True)
    try:
        d = hp.submit("doctor", "🔴 CRITICAL: قلب از کار افتاد", now=NOW)
        assert d["action"] == hp.SEND and d["reason"] == "transition-to-red", d
        c = {"inner": _FakeClient("inner"), "outer": _FakeClient("outer")}
        _flush_urgent_like_the_center(c)
        assert len(c["inner"].sent) == 1, "بحرانی به inner نرسید"
        assert c["inner"].sent[0]["chat_id"] == OWNER, "مقصد DM ِ مالک نیست"
        assert c["inner"].sent[0]["topic_id"] is None
        assert not c["outer"].sent, "بحرانی نباید روی outer برود"
    finally:
        _flag(False)


# ── اثباتِ ۲: approval → باتِ دارای handler ────────────────────────────────
def t_proof2_approvals_bypass_the_classifier_and_keep_their_handler_bot():
    """کارتِ approval هرگز وارد dedupe/digest نمی‌شود (needs_owner → فوری)،
    و parity ِ «هر دکمه handler ِ همان بات» را سوییتِ جداگانه قفل کرده —
    این‌جا فقط مرزِ ورود سنجیده می‌شود."""
    os.environ[sp.FLAG] = "1"
    try:
        assert sp.route("doctor", needs_owner=True) == (sp.DM, "needs-owner")
        # و متنِ approval-مانند هم اگر از مسیرِ محیطی برسد، حداقل گم نمی‌شود:
        d = hp.submit("doctor", "نیازمندِ تأیید: ارتقای حافظه", now=NOW)
        assert d["action"] in (hp.SEND, hp.DIGEST), d
    finally:
        os.environ.pop(sp.FLAG, None)


# ── اثباتِ ۳: پیامِ عادیِ جدید → digest ─────────────────────────────────────
def t_proof3_a_new_normal_message_lands_in_the_hourly_digest():
    _fresh()
    d = hp.submit("needs", "صفِ نیازها: ۳ موردِ باز", now=NOW)
    assert d["action"] == hp.DIGEST, d
    # «حداکثر ساعتی یک‌بار» سقفِ نرخ است نه تأخیرِ اولین تحویل — اولین flush
    # همان موقع می‌رود (چیزی برای انتظار نیست):
    text = hp.flush_digest(now=NOW + 60)
    assert text and "needs" in text, text
    # (۲۰۲۶-۰۷-۳۱، رفعِ inner-5): flush_digest نشانگر را جلو نمی‌برد —
    # صداکننده بعد از ارسالِ موفق mark_digest_flushed می‌زند (قراردادِ urgent).
    hp.mark_digest_flushed(now=NOW + 60)
    # ولی آیتمِ نو در همان ساعت، تا سررسید صبر می‌کند:
    hp.submit("doctor", "یافتهٔ تازهٔ دکتر", now=NOW + 120)
    assert hp.flush_digest(now=NOW + 180) is None, "سقفِ یک-در-ساعت شکست"
    text2 = hp.flush_digest(now=NOW + 60 + 3601)
    assert text2 and "doctor" in text2, text2
    hp.mark_digest_flushed(now=NOW + 60 + 3601)
    _flag(True)
    try:
        c = {"inner": _FakeClient("inner"), "outer": _FakeClient("outer")}
        cl, cid, tid = sr.resolve("center-health-digest", clients=c, cfg=CFG)
        assert cl is c["inner"] and cid == OWNER and tid is None, (cid, tid)
    finally:
        _flag(False)
    # «حداکثر یک پیام در ساعت»: flush ِ بلافاصله بعدی خالی است.
    assert hp.flush_digest(now=NOW + 3602) is None


# ── اثباتِ ۴: duplicate → HOLD ──────────────────────────────────────────────
def t_proof4_a_duplicate_is_held_even_when_only_the_numbers_changed():
    """درسِ «شمارنده در کلیدِ dedup»: عددِ تازه ≠ وضعیتِ تازه."""
    _fresh()
    hp.submit("heart", "دامنهٔ ضربان: ۵۶ ثانیه · وضعیت پایدار", now=NOW)
    d = hp.submit("heart", "دامنهٔ ضربان: ۶۱ ثانیه · وضعیت پایدار", now=NOW + 10)
    assert d["action"] == hp.HOLD and d["reason"].startswith("duplicate"), d
    # و بحرانیِ تکراری هم فقط شمرده می‌شود — «CRITICAL فقط در transition/escalation»:
    hp.submit("doctor", "🔴 خطِ قرمز: دیسک پُر", now=NOW + 20)
    d2 = hp.submit("doctor", "🔴 خطِ قرمز: دیسک پُر", now=NOW + 30)
    assert d2["action"] == hp.HOLD, d2
    # ولی escalation (متنِ بحرانیِ **متفاوت**) دوباره می‌رود:
    d3 = hp.submit("doctor", "🔴 خطِ قرمز: دیسک پُر و حافظه هم رفت", now=NOW + 40)
    assert d3["action"] == hp.SEND and d3["reason"] == "escalation", d3


# ── اثباتِ ۵: recovery → receipt ────────────────────────────────────────────
def t_proof5_a_recovery_sends_a_short_receipt_not_the_full_text():
    _fresh()
    hp.submit("heart", "🔴 CRITICAL: قلب ایستاد", now=NOW)
    long_ok = "🟢 برگشتیم به حالتِ سبز؛ " + "جزئیاتِ طولانی " * 30
    d = hp.submit("heart", long_ok, now=NOW + 100)
    assert d["action"] == hp.SEND and d["reason"] == "recovery", d
    assert d["receipt"] and "بازگشت" in d["receipt"], d
    rows = hp.urgent_pending(now=NOW + 101, cap=5)
    assert rows, "رسیدِ recovery در outbox نیست"
    assert rows[-1]["text"] == d["receipt"], "متنِ کامل رفته، نه رسیدِ کوتاه"
    assert len(rows[-1]["text"]) < 120, rows[-1]["text"]


# ── اثباتِ ۶: پیامِ هسته‌ای → هرگز گروه ─────────────────────────────────────
def t_proof6_core_streams_can_never_reach_the_group():
    """سه لایه، هر سه سنجیده: policy ِ روشن، policy ِ خاموش+fallback، و
    ماشینِ حالت — هیچ‌کدام مقصدِ گروهی برای جریانِ هسته‌ای تولید نمی‌کنند."""
    os.environ[sp.FLAG] = "1"
    try:
        for s in ("doctor", "heart", "needs", "summary", "cortisol", "brain"):
            dest, _ = sp.route(s)
            assert dest != sp.GROUP, (s, dest)
    finally:
        os.environ.pop(sp.FLAG, None)
    # مسیرِ قدیمی (fallback ِ نبودِ policy) — §۵ رأی: جدولش دیگر مدخلِ هسته‌ای
    # ندارد؛ (None,None) یعنی DM ِ مالک، نه گروه.
    sys.path.insert(0, str(_OPS / "budget"))
    import approval_channel as ac
    for s in ("doctor", "heart", "needs", "summary", "cortisol", "alert",
              "brain", "discovery", "c6"):
        assert s not in ac._STREAM_TOPIC, f"{s} هنوز در جدولِ fallback است"
    assert "lead" in ac._STREAM_TOPIC, "پا نباید از جدول حذف شود (بیش‌بست)"


# ── اثباتِ ۷: backlog ِ تاریخی → صفر ارسال ──────────────────────────────────
def t_proof7_the_historical_backlog_is_structurally_unreplayable():
    """ضمانت ساختاری، نه قولی: hold_policy هرگز held-stream.jsonl را نمی‌خواند."""
    import ast
    src = Path(hp.__file__).read_text("utf-8")
    assert "held-stream" not in src, "hold_policy به فایلِ backlog اشاره دارد"
    # و رفتاری: یک backlog ِ ساختگیِ بزرگ در آرشیو، policy ِ تازه — صفر خروجی.
    _fresh()
    for i in range(50):
        sp._archive("doctor", f"پیامِ کهنهٔ {i}")
    assert hp.urgent_pending(now=NOW, cap=50) == [], "backlog وارد outbox شد"
    assert hp.flush_digest(now=NOW + 7200) is None, "backlog وارد digest شد"


# ── §۶: نمای ناگفته‌ها ──────────────────────────────────────────────────────
def t_the_held_view_summarises_without_echoing_text():
    _fresh()
    rows = [{"ts": NOW - 60, "stream": "doctor",
             "text": "SECRETPAYLOAD-XYZZY جزئیاتِ حساس"} for _ in range(15)]
    out = hp.held_view(rows, now=NOW)
    assert "SECRETPAYLOAD" not in out, "متن echo شد"
    assert "HELD_VIEWED" in out, "برچسبِ وضعیت غایب"
    assert out.count("–") <= 10, "بیش از ۱۰ موردِ تازه"
    # و خواندن، وضعیت را ثبت می‌کند ولی هیچ ارسالی نمی‌سازد (تابع client ندارد).
    v = json.loads(hp._viewed_path().read_text("utf-8"))
    assert v["status"] == "HELD_VIEWED", v


def t_classifier_failure_never_silences_and_never_crashes_the_send_path():
    """fail-safe: state ِ خراب ⇒ حکم داده می‌شود، استثنا بالا نمی‌آید."""
    _fresh()
    hp._state_path().parent.mkdir(parents=True, exist_ok=True)
    hp._state_path().write_text("{این json نیست", "utf-8")
    d = hp.submit("doctor", "🔴 CRITICAL: باز هم قرمز", now=NOW)
    assert d["action"] == hp.SEND, d


def t_the_organism_writer_can_never_clobber_the_flush_marker():
    """⚠️ باگِ زندهٔ ۰۸-۰۲: نشانگرِ flush ۲۷ ساعت گیر کرد و «دایجستِ ساعتی»
    ۲۵۴ بار در یک روز رفت — هر ~۵ دقیقه. علت: classify() ِ پروسهٔ organism
    با هر پیام کلِ state را load→save می‌کند و نشانگری که مرکز نوشته بود را
    لِه می‌کرد (یا نوشتنِ نادرِ مرکز زیرِ قفلِ AV می‌باخت و False ِ بی‌صدا).
    سومین موردِ «دو نویسنده روی یک فایلِ حالت» در سه روز.

    سناریوی دقیقِ زنده: mark ِ مرکز → نوشتنِ organism (classify) → سنجش."""
    _fresh()
    hp.submit("doctor", "دکتر: وضعیتِ تازه ۱", now=NOW)          # آیتم واردِ بافر
    assert hp.digest_due(now=NOW + 3700) is True
    # ⚠️ دو نسخهٔ قبلیِ این تست هر دو کور بودند و جهشِ «mark به state ِ
    # مشترک بنویس» سبز می‌ماند: نسخهٔ ۱ لِه‌شدن را ترتیبی شبیه‌سازی می‌کرد
    # (تک-پروسه، load ِ بعدی نشانگر را می‌بیند و حفظ می‌کند)؛ نسخهٔ ۲
    # درهم‌تنیده بود ولی snapshot را **بعد** از اولین mark می‌گرفت، پس
    # نشانگر داخلِ snapshot بود و لِه بی‌اثر. ترتیبِ مرگِ واقعی:
    # خواندنِ organism → mark ِ مرکز → نوشتنِ organism.
    st_stale = hp._load_state()              # organism خواند — نشانگرِ کهنه
    assert hp.mark_digest_flushed(now=NOW + 3700) is True   # مرکز فرستاد
    st_stale.setdefault("streams", {})["doctor"] = {
        "sig": "x", "sev": "normal", "ts": NOW + 3800}
    hp._save_state(st_stale)                 # organism ذخیره کرد — لِه‌گر
    # و آیتم‌های تازهٔ واقعی (متنِ واقعاً متفاوت — امضا رقم را حذف می‌کند،
    # درسِ «شمارنده در کلیدِ dedup»؛ متنِ هم‌اسکلت HOLD می‌شود و به بافر
    # نمی‌رسد)
    for word in ("الف", "ب", "پ", "ت", "ث"):
        hp.submit("doctor", f"دکتر: مشکلِ تازهٔ {word}", now=NOW + 3800)
    # سنجه: نشانگر جان به در برده — دایجست تا یک ساعتِ بعد سررسید نیست
    assert hp.digest_due(now=NOW + 3900) is False,         "نویسندهٔ organism نشانگرِ مرکز را لِه کرد — رگبارِ ۵دقیقه‌ای برمی‌گردد"
    # و بعد از یک ساعت، با آیتم‌های تازه، درست سررسید می‌شود
    assert hp.digest_due(now=NOW + 3700 + 3601) is True


def t_the_urgent_marker_survives_the_same_interleaving():
    """قرینهٔ همان گارد برای مسیرِ urgent — همان بیماری، همان درهم‌تنیدگی."""
    _fresh()
    hp.submit("doctor", "🔴 CRITICAL: قرمز شد", now=NOW)      # واردِ outbox
    rows = hp.urgent_pending(now=NOW + 10)
    assert rows, "outbox خالی است"
    st_stale = hp._load_state()              # organism خواند
    assert hp.mark_urgent_flushed(float(rows[-1]["ts"])) is True   # مرکز فرستاد
    hp._save_state(st_stale)                 # organism لِه کرد
    assert hp.urgent_pending(now=NOW + 20) == [],         "ردیفِ flush‌شده دوباره برگشت — رگبارِ پیامِ بحرانیِ تکراری"


def t_a_marker_already_in_the_shared_state_is_still_honoured():
    """سازگاری با گذشته: نشانگری که قبلاً در state ِ مشترک نوشته شده (نصبِ
    قدیمی) باید همچنان دیده شود — خواننده max ِ دو منبع است."""
    _fresh()
    st = hp._load_state()
    st["last_digest_flush"] = NOW + 100
    hp._save_state(st)
    hp.submit("doctor", "دکتر: چیزی", now=NOW + 200)
    assert hp.digest_due(now=NOW + 300) is False,         "نشانگرِ قدیمیِ داخلِ state ِ مشترک نادیده گرفته شد"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_tg_hold_policy: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
