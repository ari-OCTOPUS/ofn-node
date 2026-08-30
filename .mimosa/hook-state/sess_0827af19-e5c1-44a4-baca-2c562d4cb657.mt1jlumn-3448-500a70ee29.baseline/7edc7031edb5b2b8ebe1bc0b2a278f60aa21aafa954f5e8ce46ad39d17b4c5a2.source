#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_deferral_rebuild_boot.py — GAP-3 (C2-C): کارتِ «بعداً» بعد از خواب برمی‌گردد.

پوشش (لیستِ اجباریِ spec):
  1. defer → restart → کارت دوباره ظاهر می‌شود (و توکنش کار می‌کند)
  2. defer → رأیِ نهایی → restart → دیگر rebuild نمی‌شود
  3. دو بوتِ پشت‌سرهم → فقط یک rebuild (dedupeِ durable)
  4. ۵ defer → یک دایجستِ واحد (نه ۵ پیام) با ردیفِ دکمه برای هرکدام
  5. outcomes.db غایب → skip بی‌صدا، بوت سالم
  6. deferralِ منقضی (TTL) → rebuild نمی‌شود
$0 آفلاین؛ صفر شبکه؛ state در sandbox.
"""
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("deferral-rebuild")
_OPS = Path(__file__).resolve().parent.parent
for _p in (str(_OPS), str(_OPS / "budget"), str(_OPS / "legs"), str(_OPS / "outcomes")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from live_loop import LiveLoop, _InMemoryBus  # noqa: E402
from leg import Leg, TaskPacket  # noqa: E402
import proposal_token as pt  # noqa: E402
import deferral_rebuild as dr  # noqa: E402
import opslib  # noqa: E402

_OWNER = 777
_DB = Path(str(opslib.STATE_DIR)) / "outcomes" / "outcomes.db"


class _FakeChannel:
    def __init__(self):
        self.sent = []
        self._owner = _OWNER

    def send_text(self, text, reply_markup=None):
        self.sent.append({"text": text, "reply_markup": reply_markup})
        return True


def _env_on():
    os.environ["OCTOPUS_WIRE_PROPOSAL_BUTTONS"] = "1"
    os.environ["OCTOPUS_WIRE_VERDICT_OUTCOME"] = "1"
    os.environ[pt.SECRET_ENV] = "unit-test-secret-not-real"
    os.environ["TELEGRAM_OWNER_CHAT_ID"] = str(_OWNER)
    os.environ.pop(dr.DEFER_TTL_ENV, None)


def _wipe():
    if _DB.exists():
        _DB.unlink()


def _leg_with(n=1):
    packet = TaskPacket(leg_id="test-leg", organ="TEST",
                        read_allowlist=("03 - Projects/Lead-نقاشی/PROJECT.md",),
                        tools=("draft",), budget_aud=0.0)
    leg = Leg(packet, organ_table={"TEST": {"floor": 0}})
    for i in range(n):
        leg.emit_proposal("draft_quote", {"scope": f"paint room {i}", "expected_aud": 100 + i})
    return leg


def _tokens(chan):
    toks = []
    for m in chan.sent:
        kb = (m.get("reply_markup") or {}).get("inline_keyboard") or []
        for row in kb:
            toks.append(row[0]["callback_data"].split(":", 2)[2])
    return toks


def _deliver_and_defer(n=1):
    """تحویلِ n کارت و تپِ «بعداً» روی همه — برمی‌گرداند توکن‌ها."""
    chan = _FakeChannel()
    loop = LiveLoop(bus=_InMemoryBus(), approval_channel=chan, leg=_leg_with(n))
    loop.route_leg_proposals(deliver=True)
    toks = _tokens(chan)
    assert len(toks) == n
    for t in toks:
        rec = loop.record_proposal_outcome_by_token(t, "later", from_id=_OWNER)
        assert rec and rec.get("event") == "deferred"
    return loop, chan, toks


def _fresh_boot():
    """«restart»: loop و channelِ نو با RAMِ خالی (leg بدونِ پیشنهاد تا router چیزی نفرستد)."""
    chan = _FakeChannel()
    loop = LiveLoop(bus=_InMemoryBus(), approval_channel=chan, leg=_leg_with(0))
    return loop, chan


# ── ۱: defer → restart → کارت برمی‌گردد و توکنش کار می‌کند ─────────────────────
def t_defer_restart_rebuilds():
    _env_on(); _wipe()
    _deliver_and_defer(1)
    loop2, chan2 = _fresh_boot()
    res = dr.rebuild_deferred_cards(loop2, chan2)
    assert res["rebuilt"] == 1 and not res["digest"], f"یک کارتِ کامل: {res}"
    assert len(chan2.sent) == 1 and chan2.sent[0]["reply_markup"], "کارت با کیبورد"
    tok = _tokens(chan2)[0]
    rec = loop2.record_proposal_outcome_by_token(tok, "ok", from_id=_OWNER)
    assert rec is not None and rec.get("verdict") == "approved", "توکنِ بازسازی‌شده باید کار کند"


# ── ۲: تصمیم‌گرفته دیگر برنمی‌گردد ──────────────────────────────────────────────
def t_decided_not_rebuilt():
    _env_on(); _wipe()
    loop1, chan1, toks = _deliver_and_defer(1)
    assert loop1.record_proposal_outcome_by_token(toks[0], "ok", from_id=_OWNER)
    loop2, chan2 = _fresh_boot()
    res = dr.rebuild_deferred_cards(loop2, chan2)
    assert res["rebuilt"] == 0 and len(chan2.sent) == 0, f"decided نباید برگردد: {res}"


# ── ۳: دو بوتِ پشت‌سرهم → یک rebuild ────────────────────────────────────────────
def t_two_boots_dedupe():
    _env_on(); _wipe()
    _deliver_and_defer(1)
    loop2, chan2 = _fresh_boot()
    assert dr.rebuild_deferred_cards(loop2, chan2)["rebuilt"] == 1
    loop3, chan3 = _fresh_boot()
    res = dr.rebuild_deferred_cards(loop3, chan3)
    assert res["rebuilt"] == 0 and len(chan3.sent) == 0, f"بوتِ دوم نباید تکرار کند: {res}"


# ── ۴: ۵ defer → یک دایجست ──────────────────────────────────────────────────────
def t_five_defers_single_digest():
    _env_on(); _wipe()
    _deliver_and_defer(5)
    loop2, chan2 = _fresh_boot()
    res = dr.rebuild_deferred_cards(loop2, chan2)
    assert res["rebuilt"] == 5 and res["digest"], f"دایجست برای ۵: {res}"
    assert len(chan2.sent) == 1, "دقیقاً یک پیام، نه طوفان"
    kb = chan2.sent[0]["reply_markup"]["inline_keyboard"]
    assert len(kb) == 5, "هر معوق یک ردیفِ دکمه"
    # یکی از ردیف‌ها را تصمیم بگیر — قوس کامل است
    tok = kb[2][0]["callback_data"].split(":", 2)[2]
    assert loop2.record_proposal_outcome_by_token(tok, "no", from_id=_OWNER) is not None


# ── ۵: DB غایب → skip بی‌صدا ───────────────────────────────────────────────────
def t_missing_db_silent_skip():
    _env_on(); _wipe()
    loop2, chan2 = _fresh_boot()
    res = dr.rebuild_deferred_cards(loop2, chan2)
    assert res.get("skipped") == "no-db" and len(chan2.sent) == 0


# ── ۶: منقضی rebuild نمی‌شود (ولی رویدادش در DB می‌ماند) ───────────────────────
def t_expired_not_rebuilt():
    _env_on(); _wipe()
    _deliver_and_defer(1)
    os.environ[dr.DEFER_TTL_ENV] = "1"
    time.sleep(1.2)
    loop2, chan2 = _fresh_boot()
    res = dr.rebuild_deferred_cards(loop2, chan2)
    os.environ.pop(dr.DEFER_TTL_ENV, None)
    assert res["rebuilt"] == 0 and len(chan2.sent) == 0, f"منقضی نباید برگردد: {res}"
    import sqlite3
    con = sqlite3.connect(f"file:{_DB}?mode=ro", uri=True)
    n = con.execute("SELECT COUNT(*) FROM outcomes WHERE event_type='deferred'").fetchone()[0]
    con.close()
    assert n == 1, "رویدادِ deferred باید در DB بماند (append-only)"


if __name__ == "__main__":
    failed = harness.run([
        ("[۱] defer → restart → کارت برمی‌گردد + توکن کار می‌کند", t_defer_restart_rebuilds),
        ("[۲] decided دیگر برنمی‌گردد", t_decided_not_rebuilt),
        ("[۳] دو بوت → یک rebuild (dedupeِ durable)", t_two_boots_dedupe),
        ("[۴] ۵ معوق → یک دایجست", t_five_defers_single_digest),
        ("[۵] DB غایب → skip بی‌صدا", t_missing_db_silent_skip),
        ("[۶] منقضی برنمی‌گردد؛ رویداد می‌ماند", t_expired_not_rebuilt),
    ])
    sys.exit(1 if failed else 0)
