#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_stateless_cb_restart.py — GAP-2 (C2-B): توکنِ statelessِ HMAC — restart دکمه را نمی‌کشد.

پوشش (لیستِ اجباریِ spec + قانونِ C2-B):
  1. mint با secret → «restart» (LiveLoopِ نو، RAM خالی، همان secret) → تپ → outcome ثبت PASS
  2. دست‌کاریِ sig → reject (fail-closed)
  3. exp گذشته → reject با سنتینلِ صادقِ expired
  4. verify → ثبت → تپِ دوباره بعد از restartِ دوم → already-decided، بدونِ ردیفِ دوم
  5. بدونِ secret → fallback به توکنِ RAMیِ قدیمی، بدونِ crash، مسیرِ تپ زنده
  6. callback_data ≤ ۶۴ بایت
  7. from_idِ غیرمالک → reject (bindِ owner در HMAC canon — ساختاری)
  8. verbِ ناشناخته روی کارتِ بازسازی‌شده → بی‌اثر
  9. defer → restart → تصمیمِ نهایی همچنان ممکن (کارت بعد از خواب زنده است)
 10. رجیستریِ تحویل idempotent (بازتحویل = ردیفِ نو نمی‌سازد)
$0 آفلاین؛ صفر شبکه؛ state در sandboxِ harness؛ secretِ تست مصنوعی است و هرگز echo نمی‌شود.
"""
import os
import sqlite3
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("stateless-cb")
_OPS = Path(__file__).resolve().parent.parent   # کدِ زیرِ تست = درختِ خودِ همین تست
for _p in (str(_OPS), str(_OPS / "budget"), str(_OPS / "legs"), str(_OPS / "outcomes")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from live_loop import LiveLoop, _InMemoryBus  # noqa: E402
from leg import Leg, TaskPacket  # noqa: E402
import proposal_token as pt  # noqa: E402
import opslib  # noqa: E402

_FLAG_BTN = "OCTOPUS_WIRE_PROPOSAL_BUTTONS"
_FLAG_OUT = "OCTOPUS_WIRE_VERDICT_OUTCOME"
_OWNER = 777
_TEST_SECRET = "unit-test-secret-not-real"   # مصنوعی — secret واقعی نیست
_DB = Path(str(opslib.STATE_DIR)) / "outcomes" / "outcomes.db"


class _FakeChannel:
    def __init__(self):
        self.sent = []
        self._owner = _OWNER          # همان قراردادِ TelegramApprovalChannel._owner

    def send_text(self, text, reply_markup=None):
        self.sent.append({"text": text, "reply_markup": reply_markup})
        return True


def _fake_leg():
    packet = TaskPacket(leg_id="test-leg", organ="TEST",
                        read_allowlist=("03 - Projects/Lead-نقاشی/PROJECT.md",),
                        tools=("draft",), budget_aud=0.0)
    return Leg(packet, organ_table={"TEST": {"floor": 0}})


def _mk_loop(chan, leg=None, amount=350):
    if leg is None:
        leg = _fake_leg()
        leg.emit_proposal("draft_quote", {"scope": "paint room", "expected_aud": amount})
    return LiveLoop(bus=_InMemoryBus(), approval_channel=chan, leg=leg), leg


def _sent_token(chan) -> str:
    kb = chan.sent[-1]["reply_markup"]
    assert kb, "کارت باید کیبورد داشته باشد"
    data = kb["inline_keyboard"][0][0]["callback_data"]      # "prop:ok:<token>"
    return data.split(":", 2)[2]


def _rows(event_type=None):
    if not _DB.exists():
        return []
    con = sqlite3.connect(f"file:{_DB}?mode=ro", uri=True)
    q = "SELECT proposal_id, event_type FROM outcomes"
    if event_type:
        q += f" WHERE event_type='{event_type}'"
    out = con.execute(q).fetchall()
    con.close()
    return out


def _env_on():
    os.environ[_FLAG_BTN] = "1"
    os.environ[_FLAG_OUT] = "1"
    os.environ[pt.SECRET_ENV] = _TEST_SECRET
    os.environ["TELEGRAM_OWNER_CHAT_ID"] = str(_OWNER)


def _wipe_db():
    if _DB.exists():
        _DB.unlink()


# ── ۱+۶+۱۰: mint → restart → تپ = outcome؛ ≤۶۴ بایت؛ رجیستری idempotent ─────────
def t_restart_survives_and_records():
    _env_on(); _wipe_db()
    chan = _FakeChannel()
    loop1, leg = _mk_loop(chan)
    loop1.route_leg_proposals(deliver=True)
    tok = _sent_token(chan)
    assert tok.startswith("pb1."), f"با secret باید stateless بسازد: {tok[:8]}"
    assert len(f"prop:later:{tok}".encode()) <= 64, "سقفِ ۶۴ بایتِ تلگرام"
    assert len(_rows("delivered")) == 1, "تحویل باید durable ثبت شود"
    # بازتحویل (همان پیشنهاد، loopِ نو) → رجیستری idempotent
    chan2 = _FakeChannel()
    loop_r, _ = _mk_loop(chan2, leg=leg)
    loop_r.route_leg_proposals(deliver=True)
    assert len(_rows("delivered")) == 1, "بازتحویل نباید ردیفِ delivered دوم بسازد"
    # «restart»: LiveLoopِ کاملاً نو، RAM خالی — تپِ مالک روی همان توکنِ قدیمی
    loop2, _ = _mk_loop(_FakeChannel(), leg=_fake_leg())
    assert tok not in loop2._proposal_cb, "پیش‌شرط: RAMِ نو خالی است"
    rec = loop2.record_proposal_outcome_by_token(tok, "ok", from_id=_OWNER)
    assert rec is not None and rec.get("verdict") == "approved", f"تپ بعد از restart باید ثبت شود: {rec}"
    acc = _rows("accepted-measurement")
    assert len(acc) == 1, f"دقیقاً یک outcome: {acc}"


# ── ۲: sig دست‌کاری‌شده → reject ────────────────────────────────────────────────
def t_forged_sig_rejected():
    _env_on(); _wipe_db()
    chan = _FakeChannel()
    loop1, _ = _mk_loop(chan)
    loop1.route_leg_proposals(deliver=True)
    tok = _sent_token(chan)
    bad = tok[:-1] + ("0" if tok[-1] != "0" else "1")
    loop2, _ = _mk_loop(_FakeChannel(), leg=_fake_leg())
    assert loop2.record_proposal_outcome_by_token(bad, "ok", from_id=_OWNER) is None
    assert len(_rows("accepted-measurement")) == 0, "جعل نباید چیزی ثبت کند"


# ── ۳: منقضی → سنتینلِ صادق ─────────────────────────────────────────────────────
def t_expired_honest_sentinel():
    _env_on(); _wipe_db()
    chan = _FakeChannel()
    loop1, _ = _mk_loop(chan)
    loop1.route_leg_proposals(deliver=True)
    pid = [r[0] for r in _rows("delivered")][0]
    old = pt.mint(pid, _OWNER, now=time.time() - pt.ttl_s() - 60)   # exp در گذشته
    assert old is not None
    loop2, _ = _mk_loop(_FakeChannel(), leg=_fake_leg())
    rec = loop2.record_proposal_outcome_by_token(old, "ok", from_id=_OWNER)
    assert rec == {"event": "expired", "advisory_only": True}, f"expired باید صادق باشد: {rec}"
    assert len(_rows("accepted-measurement")) == 0


# ── ۴: replay بعد از تصمیم → بدونِ ردیفِ دوم ───────────────────────────────────
def t_replay_no_second_row():
    _env_on(); _wipe_db()
    chan = _FakeChannel()
    loop1, _ = _mk_loop(chan)
    loop1.route_leg_proposals(deliver=True)
    tok = _sent_token(chan)
    loop2, _ = _mk_loop(_FakeChannel(), leg=_fake_leg())
    assert loop2.record_proposal_outcome_by_token(tok, "ok", from_id=_OWNER) is not None
    # «restartِ دوم» + replayِ همان callback
    loop3, _ = _mk_loop(_FakeChannel(), leg=_fake_leg())
    assert loop3.record_proposal_outcome_by_token(tok, "ok", from_id=_OWNER) is None, \
        "already-decided باید بی‌اثر باشد"
    assert len(_rows("accepted-measurement")) == 1, "replay نباید ردیفِ دوم بسازد"


# ── ۵: بدونِ secret → fallbackِ RAM، بدونِ crash ────────────────────────────────
def t_no_secret_falls_back_to_ram():
    _env_on(); _wipe_db()
    os.environ.pop(pt.SECRET_ENV, None)
    chan = _FakeChannel()
    loop1, _ = _mk_loop(chan)
    loop1.route_leg_proposals(deliver=True)
    tok = _sent_token(chan)
    assert not tok.startswith("pb1."), "بدونِ secret باید توکنِ قدیمیِ RAM باشد"
    rec = loop1.record_proposal_outcome_by_token(tok, "ok")   # مسیرِ RAMِ قدیمی زنده
    assert rec is not None
    deg = [s for s in loop1._advisory_signals if s.get("type") == "CB_TOKEN_DEGRADED"]
    assert deg, "degraded باید یک‌بار لاگ شود"


# ── ۷: from_idِ غیرمالک → reject (ساختاری) ─────────────────────────────────────
def t_wrong_owner_rejected():
    _env_on(); _wipe_db()
    chan = _FakeChannel()
    loop1, _ = _mk_loop(chan)
    loop1.route_leg_proposals(deliver=True)
    tok = _sent_token(chan)
    loop2, _ = _mk_loop(_FakeChannel(), leg=_fake_leg())
    assert loop2.record_proposal_outcome_by_token(tok, "ok", from_id=999) is None
    assert loop2.record_proposal_outcome_by_token(tok, "ok", from_id=None) is None
    assert len(_rows("accepted-measurement")) == 0, "غیرمالک نباید ثبت کند"


# ── ۸: verbِ ناشناخته روی کارتِ بازسازی‌شده → بی‌اثر ────────────────────────────
def t_bad_verb_on_rehydrated_inert():
    _env_on(); _wipe_db()
    chan = _FakeChannel()
    loop1, _ = _mk_loop(chan)
    loop1.route_leg_proposals(deliver=True)
    tok = _sent_token(chan)
    loop2, _ = _mk_loop(_FakeChannel(), leg=_fake_leg())
    assert loop2.record_proposal_outcome_by_token(tok, "settle", from_id=_OWNER) is None
    assert len(_rows("accepted-measurement")) == 0


# ── ۹: defer → restart → تصمیمِ نهایی ممکن ─────────────────────────────────────
def t_defer_survives_restart_then_decide():
    _env_on(); _wipe_db()
    chan = _FakeChannel()
    loop1, _ = _mk_loop(chan)
    loop1.route_leg_proposals(deliver=True)
    tok = _sent_token(chan)
    rec = loop1.record_proposal_outcome_by_token(tok, "later", from_id=_OWNER)
    assert rec and rec.get("event") == "deferred"
    assert len(_rows("deferred")) == 1, "تعویق باید durable باشد"
    loop2, _ = _mk_loop(_FakeChannel(), leg=_fake_leg())   # restart
    rec2 = loop2.record_proposal_outcome_by_token(tok, "ok", from_id=_OWNER)
    assert rec2 is not None and rec2.get("verdict") == "approved", \
        "کارتِ معوق بعد از restart باید قابلِ تصمیم باشد"
    assert len(_rows("accepted-measurement")) == 1


# ── F1 (red-team P2): schemeِ prop در لایهٔ channel owner-gated است ─────────────
def t_channel_owner_gates_prop_scheme():
    _env_on()
    from approval_channel import TelegramApprovalChannel

    class _HTTP:
        def get(self, url, timeout):
            return {"ok": True, "result": []}

        def post(self, url, body, timeout_s=10.0):
            return {"ok": True}

    h = _HTTP()
    ch = TelegramApprovalChannel(token="1:x", owner_chat_id=1,
                                 state_dir=str(opslib.STATE_DIR),
                                 http_get=h.get, http_post=h.post)
    seen = []

    def _hook(tok, verb, from_id=None):
        seen.append((verb, from_id))
        return {"event": "outcome"}
    ch._proposal_hook = _hook
    # عضوِ گروهِ allowlist اما غیرمالک (from_id != owner) → رد در لایهٔ channel، قلاب صدا نمی‌خورد
    r = ch.dispatch_callback("prop:ok:sometoken", from_id=999)
    assert not seen and "مالک" in str(r), f"F1: غیرمالک نباید به قلاب برسد: {seen} / {r}"
    # مالک → قلاب صدا می‌خورد
    ch.dispatch_callback("prop:ok:sometoken", from_id=1)
    assert seen and seen[-1][1] == 1, f"مالک باید عبور کند: {seen}"


# ── F4: ownerِ env با whitespace → مالک پس از restart قفل نمی‌شود ───────────────
def t_env_owner_whitespace_still_verifies():
    _env_on(); _wipe_db()

    class _NoOwnerChan(_FakeChannel):
        def __init__(self):
            super().__init__()
            self._owner = None            # mint به env می‌افتد
    os.environ["TELEGRAM_OWNER_CHAT_ID"] = "  777  "   # whitespace
    chan = _NoOwnerChan()
    loop1, _ = _mk_loop(chan)
    loop1.route_leg_proposals(deliver=True)
    tok = _sent_token(chan)
    assert tok.startswith("pb1."), "با secret باید stateless بسازد حتی با ownerِ env"
    loop2, _ = _mk_loop(_NoOwnerChan(), leg=_fake_leg())   # restart
    rec = loop2.record_proposal_outcome_by_token(tok, "ok", from_id=777)
    assert rec is not None and rec.get("verdict") == "approved", \
        "F4: whitespaceِ ownerِ env نباید مالکِ واقعی را قفل کند"
    os.environ["TELEGRAM_OWNER_CHAT_ID"] = str(_OWNER)


if __name__ == "__main__":
    failed = harness.run([
        ("[۱/۶/۱۰] restart → تپ ثبت می‌شود؛ ≤۶۴B؛ رجیستری idempotent", t_restart_survives_and_records),
        ("[F1] schemeِ prop در لایهٔ channel owner-gated", t_channel_owner_gates_prop_scheme),
        ("[F4] ownerِ env با whitespace قفل نمی‌کند", t_env_owner_whitespace_still_verifies),
        ("[۲] sigِ جعلی reject", t_forged_sig_rejected),
        ("[۳] منقضی → سنتینلِ صادق", t_expired_honest_sentinel),
        ("[۴] replay → بدونِ ردیفِ دوم", t_replay_no_second_row),
        ("[۵] بدونِ secret → fallbackِ RAM", t_no_secret_falls_back_to_ram),
        ("[۷] غیرمالک reject", t_wrong_owner_rejected),
        ("[۸] verbِ بد بی‌اثر", t_bad_verb_on_rehydrated_inert),
        ("[۹] defer بعد از restart زنده", t_defer_survives_restart_then_decide),
    ])
    sys.exit(1 if failed else 0)
