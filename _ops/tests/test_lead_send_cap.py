#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_lead_send_cap — سقفِ روزانهٔ ارسالِ لید (رأی مالک ۲۰۲۶-۰۷-۳۱: ۱۰).

اثبات می‌کند:
  · ۱۰ ارسالِ تأییدشده شمارنده را به ۱۰ می‌رساند؛ یازدهمی = CAP_REACHED با **صفر**
    فراخوانِ transport (جاسوس در لایهٔ send_impl، زنجیرهٔ تولیدیِ کامل).
  · rollover ِ نیمه‌شب با مقایسهٔ رشتهٔ تاریخ (clock تزریقی) شمارنده را صفر می‌کند.
  · lead_effect_gate.may_release در سقف deny می‌کند (reason=daily-cap، دفاع در عمق).
  · شمارندهٔ خراب = fail-closed (شمارِ نامعلوم = ارسال ممنوع).
  · عددِ سقف = ۱۰ و در کد با رأیِ مالک سنددار است.
"""
import json
import os
import sys
from pathlib import Path

import harness

ENV = harness.setup("lead-send-cap")

_OPS = Path(__file__).resolve().parent.parent
for _p in (str(_OPS), str(_OPS / "legs"), str(_OPS / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib                          # noqa: E402
import chrono                          # noqa: E402
import outbound_worker as ow           # noqa: E402
import lead_effect_gate as leg         # noqa: E402
import lead_outbound_transport as lot  # noqa: E402

NOW_MS = 1_785_400_000_000             # لنگرِ زمانی ثابت (یک روزِ مشخص)
NOW_S = NOW_MS / 1000.0
DAY_MS = 86_400_000

CAND = {"source": {"channel": "telegram_manual"},
        "candidate_type": "consented_inbound",
        "consent": {"basis": "explicit"},
        "request": {"scope_text": "repaint of apartment interior"},
        "contact": {"email": "customer@example.com"}}

_SMTP_ENV = {"OCTOPUS_SMTP_HOST": "localhost", "OCTOPUS_SMTP_PORT": "2525",
             "OCTOPUS_SMTP_USER": "test-user", "OCTOPUS_SMTP_PASS": "test-pass-x",
             "OCTOPUS_SMTP_FROM": "quotes@example.com"}


class SpyImpl:
    """جاسوسِ لایهٔ سیم (send_impl) — ارسالِ موفقِ ساختگی، شمارشِ فراخوان."""

    def __init__(self):
        self.calls = 0

    def __call__(self, host, port, user, pw, from_addr, to_addr, message):
        self.calls += 1


def _fresh_counter():
    try:
        ow._counter_path().unlink()
    except OSError:
        pass


def _fresh_authz():
    try:
        leg._authz_store().unlink()
    except OSError:
        pass


def _gate(name):
    db = chrono.ChronoDB(ENV["OPS_DIR"] + f"/state/cap-{name}.db")
    return chrono.EffectorGate(db)


def _arm(spy):
    os.environ["OCTOPUS_WIRE_LEAD_OUTBOUND"] = "1"
    os.environ.update(_SMTP_ENV)
    lot._orig_impl = getattr(lot, "_orig_impl", lot._default_send_impl)
    lot._default_send_impl = spy


def _disarm():
    os.environ.pop("OCTOPUS_WIRE_LEAD_OUTBOUND", None)
    for k in _SMTP_ENV:
        os.environ.pop(k, None)
    if hasattr(lot, "_orig_impl"):
        lot._default_send_impl = lot._orig_impl


def _one_send(gate, i):
    eid = gate.request("lead_outbound", f"lead-cap-{i}", beat=1)
    a = leg.authorize(eid, f"lead-cap-{i}", f"tok-{i}")
    assert a["ok"], a
    return ow.send_one(eid, CAND, "draft body", gate=gate, now_ms=NOW_MS + i)


def t_a_cap_constant_is_the_owner_vote():
    assert ow.LEAD_DAILY_SEND_CAP == 10, "سقف = رأی مالک ۲۰۲۶-۰۷-۳۱ = ۱۰"
    src = Path(ow.__file__).read_text("utf-8")
    assert "رأی مالک ۲۰۲۶-۰۷-۳۱" in src, "سندِ رأیِ مالک کنارِ عدد نیست"


def t_b_ten_sends_fill_the_counter_and_the_11th_is_cap_reached():
    """زنجیرهٔ تولیدیِ کامل: send_one → گیت → transport واقعی (send_impl جاسوس)."""
    _fresh_counter()
    _fresh_authz()
    spy = SpyImpl()
    _arm(spy)
    try:
        gate = _gate("full")
        for i in range(10):
            r = _one_send(gate, i)
            assert r.get("sent") is True and r.get("status") == "SENT", (i, r)
        assert spy.calls == 10, spy.calls
        assert ow.sends_today(now=NOW_S) == 10
        r11 = _one_send(gate, 10)
        assert r11.get("status") == "CAP_REACHED" and r11.get("sent") is False, r11
        assert spy.calls == 10, "یازدهمی نباید به transport برسد"
        assert ow.sends_today(now=NOW_S) == 10, "CAP_REACHED نباید بشمارد"
    finally:
        _disarm()


def t_c_cap_receipt_is_written():
    ev = opslib.STATE_DIR / "legs" / "lead-inbox" / "events.jsonl"
    recs = [json.loads(l) for l in ev.read_text("utf-8").splitlines() if l.strip()]
    assert any(r["event_type"] == "send.cap_reached" for r in recs), \
        "رسیدِ سقف در events.jsonl نیست"


def t_d_may_release_denies_at_cap_defense_in_depth():
    _fresh_authz()
    gate = _gate("gate-layer")
    eid = gate.request("lead_outbound", "lead-mr", beat=1)
    leg.authorize(eid, "lead-mr", "tok-mr")
    v = leg.may_release(eid, CAND, gate=gate, now=NOW_S)
    assert v["allow"] is False and v["reason"] == "daily-cap", v


def t_e_midnight_rollover_resets_by_date_string():
    _fresh_counter()
    for _ in range(3):
        ow.record_send(now=NOW_S)
    assert ow.sends_today(now=NOW_S) == 3
    tomorrow = NOW_S + 1.5 * 86400
    assert ow.sends_today(now=tomorrow) == 0, "روزِ نو باید صفر شروع شود"
    assert ow.cap_reached(now=tomorrow) is False
    # و may_release فردا دوباره اجازه می‌دهد (effect ِ سقف‌خورده گم نمی‌شود)
    _fresh_authz()
    gate = _gate("rollover")
    eid = gate.request("lead_outbound", "lead-ro", beat=1)
    leg.authorize(eid, "lead-ro", "tok-ro")
    v = leg.may_release(eid, CAND, gate=gate, now=tomorrow)
    assert v["allow"] is True, v


def t_f_corrupt_counter_fails_closed():
    p = ow._counter_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("NOT-JSON{{{", "utf-8")
    assert ow.sends_today(now=NOW_S) == ow.LEAD_DAILY_SEND_CAP, \
        "شمارِ نامعلوم باید fail-closed باشد (ارسال ممنوع)"
    assert ow.cap_reached(now=NOW_S) is True
    _fresh_counter()
    assert ow.sends_today(now=NOW_S) == 0


def t_g_flag_off_worker_is_inert_regardless_of_counter():
    _fresh_counter()
    os.environ.pop("OCTOPUS_WIRE_LEAD_OUTBOUND", None)
    gate = _gate("flag-off")
    eid = gate.request("lead_outbound", "lead-off", beat=1)
    leg.authorize(eid, "lead-off", "tok-off")
    r = ow.send_one(eid, CAND, "draft", gate=gate, now_ms=NOW_MS)
    assert r["status"] == "flag_off" and r["sent"] is False, r


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_lead_send_cap: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
