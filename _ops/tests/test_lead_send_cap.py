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
import mail_credentials as mc          # noqa: E402
import consent_gate as cg              # noqa: E402
import consent_store as cs             # noqa: E402

# ⚠️ از وقتی transport یک fallback ِ Gmail دارد، کلیدهای زندهٔ ماشینِ میزبان
# می‌توانند این تست را بی‌خبر مسلح کنند. هر مسیرِ credential صریحاً کنترل شود،
# و هیچ `.env` ِ واقعی‌ای وسطِ تست تزریق نکند.
mc._ensure_env_loaded = lambda: None
for _k in (mc.GMAIL_ADDR_ENV, mc.GMAIL_SECRET_ENV, mc.GMAIL_FALLBACK_FLAG):
    os.environ.pop(_k, None)

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
    os.environ.pop(cg.FLAG, None)
    for k in tuple(_SMTP_ENV) + (mc.GMAIL_ADDR_ENV, mc.GMAIL_SECRET_ENV,
                                 mc.GMAIL_FALLBACK_FLAG):
        os.environ.pop(k, None)
    if hasattr(lot, "_orig_impl"):
        lot._default_send_impl = lot._orig_impl


# ── consent_gate D2a wiring (۲۰۲۶-۰۸-۰۷) — کمکِ گرانتِ رضایتِ store-backed ─────────
# send_one حالا consent_gate.may_release را **قبل از** release_and_settle صدا
# می‌زند (لایهٔ سومِ مستقلِ consent). این فایل منطقِ سقفِ روزانه را می‌سنجد، نه
# consent_gate را — پس هر لیدی که واقعاً باید بفرستد باید رضایتِ store-backed
# داشته باشد، وگرنه هرگز به شمارنده/سقف نمی‌رسد (هم‌الگوی test_lead_outbound_transport.py).
def _grant_consent(lead_id: str, *, channel: str = "telegram_manual") -> None:
    os.environ[cg.FLAG] = "1"
    store = cs.ConsentStore()
    try:
        store.upsert_current({
            "lead_id": lead_id, "candidate_type": "consented_inbound",
            "consent_basis": "explicit", "consent_evidence": "quote_form",
            "consent_state": "CONSENTED_INBOUND", "compliance_state": "UNREVIEWED",
            "outreach_allowed": True, "retention_class": "consented_customer",
            "retention_anchor_at": "2026-07-21T00:00:00+00:00",
            "source_channel": channel})
    finally:
        store.close()


def _one_send(gate, i):
    lead_id = f"lead-cap-{i}"
    eid = gate.request("lead_outbound", lead_id, beat=1)
    a = leg.authorize(eid, lead_id, f"tok-{i}")
    assert a["ok"], a
    _grant_consent(lead_id)
    cand = dict(CAND); cand["lead_id"] = lead_id
    return ow.send_one(eid, cand, "draft body", gate=gate, now_ms=NOW_MS + i)


def t_a_cap_default_ten_env_overridable():
    """پیش‌فرض ۱۰؛ رأی ۲۰۲۶-۰۸-۱۲ اجازهٔ override با OCTOPUS_LEAD_DAILY_SEND_CAP."""
    import importlib
    old = os.environ.pop("OCTOPUS_LEAD_DAILY_SEND_CAP", None)
    try:
        importlib.reload(ow)
        assert ow.LEAD_DAILY_SEND_CAP == 10
        os.environ["OCTOPUS_LEAD_DAILY_SEND_CAP"] = "100"
        importlib.reload(ow)
        assert ow.LEAD_DAILY_SEND_CAP == 100
        assert ow.cap_reached(now=NOW_S) is False or ow.sends_today(now=NOW_S) >= 100
    finally:
        if old is None:
            os.environ.pop("OCTOPUS_LEAD_DAILY_SEND_CAP", None)
        else:
            os.environ["OCTOPUS_LEAD_DAILY_SEND_CAP"] = old
        importlib.reload(ow)


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


def t_h_cap_hit_stops_before_settle_even_if_the_gate_layer_regressed():
    """بازبینی ۰۷-۳۱ (security W1): کمربندِ worker باید **قبل از**
    release_and_settle بایستد. سناریوی رگرسیونِ لایهٔ گیت شبیه‌سازی می‌شود
    (may_release ِ همیشه-allow): با ترتیبِ قدیمی effect اول settle می‌شد
    (مصرف می‌شد) و بعد ارسال رد می‌شد — settle-بی‌ارسال. با ترتیبِ نو effect
    دست‌نخورده (pending) می‌مانَد و transport هم صفر تماس می‌گیرد."""
    _fresh_counter()
    _fresh_authz()
    for _ in range(10):
        ow.record_send(now=NOW_S)              # سقف پُر — بدونِ حتی یک ارسال
    assert ow.cap_reached(now=NOW_S) is True
    spy = SpyImpl()
    _arm(spy)
    orig_may_release = leg.may_release
    leg.may_release = lambda *a, **k: {"allow": True, "reason": "ok",
                                       "status": "pending"}
    try:
        gate = _gate("belt-order")
        eid = gate.request("lead_outbound", "lead-belt", beat=1)
        leg.authorize(eid, "lead-belt", "tok-belt")
        r = ow.send_one(eid, CAND, "draft", gate=gate, now_ms=NOW_MS)
        assert r["status"] == "CAP_REACHED" and r["sent"] is False, r
        assert gate.status_of(eid) == "pending", \
            f"effect ِ سقف‌خورده settle/مصرف شد: {gate.status_of(eid)!r}"
        assert spy.calls == 0, "سقف‌خورده به transport رسید"
    finally:
        leg.may_release = orig_may_release
        _disarm()
        _fresh_counter()


def t_hb_cap_holds_on_the_real_gmail_credential_path_too():
    """سقف نباید وابسته به **مسیرِ credential** باشد. این تست همان کمربندِ
    قبل-از-settle را این‌بار روی مسیری می‌سنجد که واقعاً زنده می‌شود
    (fallback ِ Gmail، رأیِ ARM ِ ۰۷-۳۱) — نه فقط روی OCTOPUS_SMTP_* ِ ساختگی."""
    _fresh_counter()
    _fresh_authz()
    spy = SpyImpl()
    os.environ["OCTOPUS_WIRE_LEAD_OUTBOUND"] = "1"
    os.environ[mc.GMAIL_ADDR_ENV] = "owner.person@gmail.com"
    os.environ[mc.GMAIL_SECRET_ENV] = "GMAIL-PW-SENTINEL-CAP"
    os.environ[mc.GMAIL_FALLBACK_FLAG] = "1"
    lot._orig_impl = getattr(lot, "_orig_impl", lot._default_send_impl)
    lot._default_send_impl = spy
    try:
        assert mc.resolve()["how"] == "gmail-app-password", mc.resolve()
        gate = _gate("gmail-cap")
        # ۱۰ ارسالِ واقعی از همین مسیر
        for i in range(10):
            r = _one_send(gate, 100 + i)
            assert r.get("sent") is True, (i, r)
        assert spy.calls == 10 and ow.sends_today(now=NOW_S) == 10
        # یازدهمی: نه transport، نه settle
        eid = gate.request("lead_outbound", "lead-cap-gmail", beat=1)
        leg.authorize(eid, "lead-cap-gmail", "tok-gmail")
        r11 = ow.send_one(eid, CAND, "draft", gate=gate, now_ms=NOW_MS)
        assert r11["status"] == "CAP_REACHED" and r11["sent"] is False, r11
        assert spy.calls == 10, "سقف روی مسیرِ Gmail نشت کرد"
        assert gate.status_of(eid) == "pending", \
            f"effect ِ سقف‌خورده مصرف شد: {gate.status_of(eid)!r}"
    finally:
        _disarm()
        _fresh_counter()


def t_i_drive_outbound_flag_off_is_zero_effects():
    """درایور (بازبینی ۰۷-۳۱، wiring W2): فلگِ مستر خاموش ⇒ {"driven": 0} و
    صفر اثر — نه release، نه settle، نه transport."""
    _fresh_counter()
    _fresh_authz()
    os.environ.pop("OCTOPUS_WIRE_LEAD_OUTBOUND", None)
    spy = SpyImpl()
    os.environ.update(_SMTP_ENV)
    import lead_outbound_transport as _lot2
    _orig = _lot2._default_send_impl
    _lot2._default_send_impl = spy
    try:
        gate = _gate("drv-off")
        eid = gate.request("lead_outbound", "lead-drv-off", beat=1)
        leg.authorize(eid, "lead-drv-off", "tok-off")
        out = ow.drive_outbound(gate=gate, now_ms=NOW_MS)
        assert out == {"driven": 0}, out
        assert gate.status_of(eid) == "pending", "flag-off ولی effect لمس شد"
        assert spy.calls == 0
    finally:
        _lot2._default_send_impl = _orig
        for k in _SMTP_ENV:
            os.environ.pop(k, None)


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
