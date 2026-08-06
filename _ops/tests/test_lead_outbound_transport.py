#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_lead_outbound_transport — آداپترِ ایمیلِ واقعیِ Lane G (رأی ۱۷).

اثبات می‌کند:
  · بدونِ ۵ envِ SMTP → NOT_ARMED صادقانه؛ صفر communication.sent؛ شمارنده دست‌نخورده.
  · ارسالِ موفق (SMTP ساختگیِ تزریقی) → communication.sent در funnel.db + شمارنده++.
  · شکستِ SMTP → communication.failed + رسیدِ شکست + شمارنده دست‌نخورده.
  · نشانِ STOP/opt-out → SUPPRESSED، صفر تلاش، تغذیهٔ دفاعیِ consent_store.suppression.
  · secret (پسورد/کاربر) و گیرندهٔ کامل هرگز در رسیدها نمی‌نشیند (ماسکِ local-part).
  (قفلِ test_effector_gate_bridge محترم: sent فقط از نتیجهٔ واقعیِ transport.)
"""
import json
import os
import sys
from pathlib import Path

import harness

ENV = harness.setup("lead-outbound-transport")

_OPS = Path(__file__).resolve().parent.parent
for _p in (str(_OPS), str(_OPS / "legs"), str(_OPS / "budget"), str(_OPS / "outcomes")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib                          # noqa: E402
import outbound_worker as ow           # noqa: E402
import lead_outbound_transport as lot  # noqa: E402
import mail_credentials as mc          # noqa: E402
import funnel_store as fs              # noqa: E402

_SMTP_ENV = {"OCTOPUS_SMTP_HOST": "localhost", "OCTOPUS_SMTP_PORT": "2525",
             "OCTOPUS_SMTP_USER": "smtp-test-user",
             "OCTOPUS_SMTP_PASS": "hunter2-super-secret",
             "OCTOPUS_SMTP_FROM": "quotes@example.com"}

# ⚠️ خطرِ واقعیِ کشف‌شدهٔ ۰۷-۳۱: از وقتی transport یک fallback ِ Gmail دارد، اگر
# ماشینِ میزبان `GMAIL_ADDRESS`/`GMAIL_APP_PASSWORD` ِ **زنده** در env داشته باشد
# (اجرا از درختِ زنده، یا `.env` ِ لودشده)، تستِ «بی-creds» دیگر NOT_ARMED نمی‌گرفت
# و چون `send_impl` نمی‌دهد، `_default_send_impl` ِ **واقعی** به یک آدرسِ نمونه
# ایمیل می‌زد. پس هر مسیرِ credential باید در این فایل صریحاً کنترل شود.
_CRED_KEYS = tuple(_SMTP_ENV) + (mc.GMAIL_ADDR_ENV, mc.GMAIL_SECRET_ENV,
                                 mc.GMAIL_FALLBACK_FLAG)
for _k in _CRED_KEYS:
    os.environ.pop(_k, None)
# و هیچ `.env` ِ واقعی‌ای وسطِ تست کلید تزریق نکند (تعیّن + صفر کلیدِ واقعی).
mc._ensure_env_loaded = lambda: None

NOW_S = 1_785_400_000.0


def _set_creds(on: bool):
    for k in _CRED_KEYS:
        os.environ.pop(k, None)
    if on:
        os.environ.update(_SMTP_ENV)


def _fresh_counter():
    try:
        ow._counter_path().unlink()
    except OSError:
        pass


def _events_text() -> str:
    p = opslib.STATE_DIR / "legs" / "lead-inbox" / "events.jsonl"
    try:
        return p.read_text("utf-8")
    except OSError:
        return ""


def _funnel_types(lead_id: str) -> list:
    store = fs.FunnelStore()
    try:
        return [r[1] for r in store.events_for_lead(lead_id)]
    finally:
        store.close()


def _cand(lead_id: str, email="customer.one@example.com", **extra) -> dict:
    c = {"lead_id": lead_id, "contact": {"email": email},
         "source": {"channel": "telegram_manual"}}
    c.update(extra)
    return c


class SpyImpl:
    def __init__(self, fail=False):
        self.calls = []
        self.fail = fail

    def __call__(self, host, port, user, pw, from_addr, to_addr, message):
        self.calls.append({"host": host, "to": to_addr, "message": message})
        if self.fail:
            raise ConnectionError("boom")


def t_a_no_creds_is_honest_not_armed():
    _set_creds(False)
    _fresh_counter()
    r = lot.send(_cand("L-nocreds"), "hello", now=NOW_S)
    assert r == {"sent": False, "status": "NOT_ARMED", "detail": "smtp-creds-missing"}, r
    assert "communication.sent" not in _funnel_types("L-nocreds"), \
        "NOT_ARMED نباید communication.sent بزند (settle ≠ sent)"
    assert ow.sends_today(now=NOW_S) == 0, "NOT_ARMED نباید بشمارد"


def t_b_confirmed_send_writes_receipt_and_counts():
    _set_creds(True)
    _fresh_counter()
    spy = SpyImpl()
    r = lot.send(_cand("L-ok"), {"subject": "Quote", "body": "قیمتِ کار"},
                 now=NOW_S, send_impl=spy)
    assert r["sent"] is True and r["status"] == "SENT", r
    assert len(spy.calls) == 1 and spy.calls[0]["to"] == "customer.one@example.com"
    assert "communication.sent" in _funnel_types("L-ok"), "رسیدِ funnel نیست"
    assert ow.sends_today(now=NOW_S) == 1, "ارسالِ تأییدشده باید بشمارد"
    import email as _em
    _msg = _em.message_from_string(spy.calls[0]["message"])
    _body = _msg.get_payload(decode=True).decode("utf-8")
    assert "Reply STOP" in _body, "پیامِ ایمیل بدونِ راهِ opt-out"


def t_c_failed_send_writes_failed_and_never_counts():
    _set_creds(True)
    _fresh_counter()
    spy = SpyImpl(fail=True)
    r = lot.send(_cand("L-fail"), "hello", now=NOW_S, send_impl=spy)
    assert r["sent"] is False and r["status"] == "FAILED", r
    types = _funnel_types("L-fail")
    assert "communication.failed" in types and "communication.sent" not in types, types
    assert ow.sends_today(now=NOW_S) == 0, "شکست نباید بشمارد"
    assert '"communication.failed"' in _events_text(), "رسیدِ شکست در events.jsonl نیست"


def t_d_stop_marker_is_suppressed_and_feeds_consent_store():
    _set_creds(True)
    spy = SpyImpl()
    r = lot.send(_cand("L-stop", email="stopme@example.com", opt_out=True),
                 "hello", now=NOW_S, send_impl=spy)
    assert r["sent"] is False and r["status"] == "SUPPRESSED", r
    assert not spy.calls, "کاندیدِ STOP نباید هیچ تلاشی بگیرد"
    import consent_store as cs
    store = cs.ConsentStore()
    try:
        reason = store.suppression_active("stopme@example.com")
    finally:
        store.close()
    assert reason, "suppression باید به consent_store تغذیه شده باشد"
    # و بارِ دوم هم suppressed می‌مانَد (این‌بار از خودِ جدولِ suppression)
    r2 = lot.send(_cand("L-stop2", email="stopme@example.com"),
                  "hello", now=NOW_S, send_impl=spy)
    assert r2["status"] == "SUPPRESSED" and not spy.calls, r2


def t_e_missing_recipient_is_honest():
    _set_creds(True)
    spy = SpyImpl()
    r = lot.send({"lead_id": "L-noaddr", "contact": {}}, "hello",
                 now=NOW_S, send_impl=spy)
    assert r["status"] == "NO_RECIPIENT" and not spy.calls, r


def t_f_secrets_and_full_recipient_never_reach_receipts():
    text = _events_text()
    assert "hunter2-super-secret" not in text, "پسورد در رسید نشسته!"
    assert "smtp-test-user" not in text, "کاربرِ SMTP در رسید نشسته!"
    assert "customer.one@example.com" not in text, "گیرندهٔ کامل در رسید نشسته!"
    assert "cu***@example.com" in text, "ماسکِ local-part در رسید نیست"
    assert lot.mask_recipient("ab.cd@x.com") == "ab***@x.com"
    assert lot.mask_recipient("") == "***"


def t_g_transport_never_raises():
    _set_creds(True)
    r = lot.send(None, None, now=NOW_S, send_impl=SpyImpl())
    assert isinstance(r, dict) and r.get("sent") is False, r


def t_ib_market_signal_is_denied_even_with_perfect_consent_on_an_allowed_channel():
    """جهش‌سنجیِ واقعیِ ناوردای «سیگنال هرگز نمی‌فرستد» (R1).

    چرا این تست جدا از t_i لازم شد: کاندیدِ t_i هم‌زمان market_signal است، هم
    basis=none، هم روی کانالِ سیگنالیِ facebook_group — یعنی **سه** دلیلِ مستقلِ
    رد. پس وقتی گاردِ market_signal را جهش دادیم t_i سبز ماند (لایه‌های دیگر
    گرفتندش): t_i ناوردا را می‌سنجد ولی این گاردِ خاص را پین نمی‌کند.
    این‌جا فیکسچر عمداً **زیرِ سطحِ هدف** است: رضایتِ صریح با evidence، روی
    کانالِ مجازِ telegram_manual — تنها چیزی که جلوی ارسال را می‌گیرد همان
    ردهٔ market_signal است (`classify` ِ declared زیرِ سقفِ کانال را می‌پذیرد).
    اگر R1 بمیرد، این کاندید واقعاً می‌رود — و این تست قرمز می‌شود."""
    import lead_effect_gate as leg
    import consent_firewall as cf
    _set_creds(True)
    _fresh_counter()
    try:
        leg._authz_store().unlink()
    except OSError:
        pass
    signal_cand = {"lead_id": "L-sig2",
                   "candidate_type": "market_signal",
                   "source": {"channel": "telegram_manual"},
                   "consent": {"basis": "explicit",
                               "evidence": "submitted_quote_form"},
                   "request": {"scope_text": "repaint hallway"},
                   "contact": {"email": "signal.victim@example.com"}}
    # پیش‌شرطِ فیکسچر: واقعاً market_signal طبقه‌بندی می‌شود و تنها مانع همین است.
    assert cf.classify(signal_cand) == "market_signal", cf.classify(signal_cand)
    gate = _drv_gate("sig2")
    eid = gate.request("lead_outbound", "L-sig2", beat=1)
    assert leg.authorize(eid, "L-sig2", "tok-sig2")["ok"]
    os.environ["OCTOPUS_WIRE_LEAD_OUTBOUND"] = "1"
    spy = SpyImpl()
    _orig = lot._default_send_impl
    lot._default_send_impl = spy
    try:
        r = ow.send_one(eid, signal_cand, {"subject": "Q", "body": "x"},
                        gate=gate, now_ms=int(NOW_S * 1000))
    finally:
        lot._default_send_impl = _orig
        os.environ.pop("OCTOPUS_WIRE_LEAD_OUTBOUND", None)
    assert r["sent"] is False, f"سیگنال فرستاده شد — نقضِ R1: {r}"
    assert r["status"] == "gate_denied", r
    assert not spy.calls, "سیگنال به transport رسید — نقضِ R1"
    assert gate.status_of(eid) == "pending", \
        f"سیگنال نباید settle/مصرف شود: {gate.status_of(eid)!r}"
    assert ow.sends_today(now=NOW_S) == 0


# ── fallback ِ Gmail + خودآزمون (شبِ ۰۷-۳۱: لوله واقعاً کامل شد) ────────────────
OWNER_ADDR = "owner.person@gmail.com"
OWNER_PW = "GMAIL-PW-SENTINEL-4c7e"


def _arm_gmail():
    """fallback ِ Gmail را مسلح کن (بدونِ هیچ کلیدِ واقعی — همه ساختگی)."""
    _set_creds(False)
    os.environ[mc.GMAIL_ADDR_ENV] = OWNER_ADDR
    os.environ[mc.GMAIL_SECRET_ENV] = OWNER_PW
    os.environ[mc.GMAIL_FALLBACK_FLAG] = "1"


def t_j_gmail_fallback_completes_the_arc_and_reads_the_secret_at_send_time():
    """قوسِ واقعیِ Lane G: بدونِ هیچ secret ِ نو، با کلیدهای موجودِ Gmail،
    ارسال کامل می‌شود — و پسورد **لحظهٔ ارسال** از env با نامش خوانده می‌شود."""
    _arm_gmail()
    _fresh_counter()
    spy = SpyImpl()
    r = lot.send(_cand("L-gmail", email="gmail.customer@example.com"),
                 {"subject": "Quote", "body": "کارِ نقاشی"},
                 now=NOW_S, send_impl=spy)
    assert r["sent"] is True and r["status"] == "SENT", r
    call = spy.calls[0]
    assert call["host"] == "smtp.gmail.com", call
    assert ow.sends_today(now=NOW_S) == 1, "ارسالِ واقعیِ لید باید بشمارد"
    # پسورد از env با **نام** خوانده شد و به impl رسید — ولی از resolve بیرون نیامد
    assert lot._read_secret(mc.resolve()) == OWNER_PW
    assert mc.resolve().get("secret_env") == mc.GMAIL_SECRET_ENV
    assert OWNER_PW not in json.dumps(mc.resolve(), ensure_ascii=False)


def t_k_gmail_creds_without_the_flag_are_honestly_not_armed():
    """کلیدها هستند ولی رأیِ مالک (فلگ) نیست ⇒ NOT_ARMED با دلیلی که نامِ فلگ
    را می‌گوید، و **صفر** تلاشِ ارسال."""
    _arm_gmail()
    os.environ.pop(mc.GMAIL_FALLBACK_FLAG, None)
    spy = SpyImpl()
    r = lot.send(_cand("L-noflag"), "hello", now=NOW_S, send_impl=spy)
    assert r["sent"] is False and r["status"] == "NOT_ARMED", r
    assert mc.GMAIL_FALLBACK_FLAG in r["detail"], r
    assert not spy.calls, "بدونِ فلگ نباید هیچ تلاشی برود"


def t_l_self_test_goes_only_to_the_owner_address():
    _arm_gmail()
    _fresh_counter()
    spy = SpyImpl()
    r = lot.self_test(send_impl=spy, now=NOW_S)
    assert r["sent"] is True and r["status"] == "SENT", r
    assert len(spy.calls) == 1 and spy.calls[0]["to"] == OWNER_ADDR, spy.calls
    import email as _em
    m = _em.message_from_string(spy.calls[0]["message"])
    assert "SELF-TEST" in m["Subject"], m["Subject"]
    body = m.get_payload(decode=True).decode("utf-8")
    assert "No lead was contacted" in body, body


def t_m_self_test_refuses_any_recipient_that_is_not_the_owner():
    """قفلِ ۱ — خودآزمون نباید به سلاحِ ارسالِ دلخواه تبدیل شود."""
    _arm_gmail()
    spy = SpyImpl()
    for victim in ("someone.else@example.com", "attacker@evil.test",
                   "OWNER.PERSON@gmail.com.evil.test"):
        r = lot.self_test(victim, send_impl=spy, now=NOW_S)
        assert r["sent"] is False and r["status"] == "REFUSED", (victim, r)
        assert not spy.calls, f"خودآزمون به {victim} تلاشِ ارسال کرد!"
    # ولی خودِ آدرسِ مالک (حتی با حروفِ بزرگ/فاصله) پذیرفته می‌شود
    r_ok = lot.self_test("  OWNER.Person@Gmail.com  ", send_impl=spy, now=NOW_S)
    assert r_ok["status"] == "SENT", r_ok


def t_n_self_test_never_touches_the_cap_counter_or_the_funnel_ledger():
    """قفلِ ۲ و ۳ — خودآزمون سهمیهٔ روزانهٔ لید را نمی‌خورد و در قیفِ فروش
    به‌عنوانِ «ارتباط با مشتری» ثبت نمی‌شود."""
    _arm_gmail()
    _fresh_counter()
    before = ow.sends_today(now=NOW_S)
    for _ in range(3):
        assert lot.self_test(send_impl=SpyImpl(), now=NOW_S)["sent"] is True
    assert ow.sends_today(now=NOW_S) == before == 0, \
        "خودآزمون شمارندهٔ سقف را لمس کرد"
    assert not _funnel_types("self-test"), "خودآزمون در دفترِ funnel نشست"
    # شکستِ خودآزمون هم نباید communication.failed ِ قیف بنویسد
    assert lot.self_test(send_impl=SpyImpl(fail=True), now=NOW_S)["status"] == "FAILED"
    assert not _funnel_types("self-test"), "شکستِ خودآزمون در دفترِ funnel نشست"
    assert ow.sends_today(now=NOW_S) == 0


def t_o_self_test_without_creds_is_honest_and_silent():
    _set_creds(False)
    spy = SpyImpl()
    r = lot.self_test(send_impl=spy, now=NOW_S)
    assert r["sent"] is False and r["status"] == "NOT_ARMED", r
    assert not spy.calls


def t_p_no_secret_value_ever_reaches_the_receipts():
    """قاعدهٔ §۱۰ روی کلِ رسیدها — شاملِ مسیرِ Gmail و خودآزمون."""
    text = _events_text()
    for secret in (OWNER_PW, "hunter2-super-secret"):
        assert secret not in text, f"secret در رسیدها نشسته: {secret[:6]}…"
    assert OWNER_ADDR not in text, "آدرسِ کاملِ مالک در رسیدها نشسته"
    assert "ow***@gmail.com" in text, "ماسکِ آدرسِ مالک در رسیدِ خودآزمون نیست"
    assert '"communication.self_test"' in text, "رسیدِ خودآزمون نوشته نشد"


# ── درایورِ drive_outbound (بازبینی ۰۷-۳۱، wiring W2) ───────────────────────
def _drv_gate(name):
    import chrono
    db = chrono.ChronoDB(str(opslib.STATE_DIR / f"drv-{name}.db"))
    return chrono.EffectorGate(db)


def _seed_inbox(lead_id, *, email="drv.customer@example.com",
                candidate_type="consented_inbound", basis="explicit",
                channel="telegram_manual", attribution_id="AT-DRV-001"):
    p = opslib.STATE_DIR / "legs" / "lead-inbox" / f"{lead_id}.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({
        "lead_id": lead_id, "source": channel,
        "attribution_id": attribution_id,
        "candidate": {"candidate_type": candidate_type,
                      "consent": {"basis": basis},
                      "request": {"scope_text": "repaint hallway"},
                      "contact": {"email": email}}},
        ensure_ascii=False), "utf-8")
    return p


def _seed_draft(attribution_id, scope="Repaint of hallway, two coats.",
                total_incl_gst=(1980.0, 2640.0)):
    d = opslib.STATE_DIR / "legs" / "lead-drafts"
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"{attribution_id}.json"
    rec = {"schema": "lead-quote.v1", "qt_number": "QT-20260731-001",
           "attribution_id": attribution_id, "intake": {"scope": scope},
           "draft_only": True, "sent": False}
    # GAP-2 (۰۸-۰۱): از این تاریخ کوتِ **بی‌مبلغ** ایمیل نمی‌شود — درایور با
    # رسیدِ `no-price` skip می‌کند. فیکسچرِ قبلی هیچ breakdownی نداشت، پس t_h/t_i
    # سرِ چیزی قرمز می‌شدند که ربطی به قراردادِ خودشان (ارسال/R1) ندارد. همان
    # کلیدی نوشته می‌شود که `lead_quote.create_quote` از `PriceBreakdown.to_dict()`
    # پایدار می‌کند. `None` = کوتِ عمداً بی‌مبلغ.
    if total_incl_gst is not None:
        rec["breakdown"] = {"total_incl_gst": list(total_incl_gst)}
    p.write_text(json.dumps(rec, ensure_ascii=False), "utf-8")
    return p


def t_h_driver_sends_the_authorized_effect_via_the_spy_transport():
    """قوسِ کامل: authorize → drive_outbound → send_one → transport (جاسوس).
    پیش‌نویس از lead-drafts، گیرنده از contact ِ inbox؛ effect ِ بی‌پیش‌نویس
    skip با رسیدِ no-draft — نه ارسالِ کور."""
    import lead_effect_gate as leg
    _set_creds(True)
    _fresh_counter()
    try:
        leg._authz_store().unlink()
    except OSError:
        pass
    _seed_inbox("L-drv", attribution_id="AT-DRV-001")
    _seed_draft("AT-DRV-001")
    _seed_inbox("L-nodraft", email="nod.customer@example.com",
                attribution_id="")          # عمداً بدونِ پیش‌نویس
    gate = _drv_gate("send")
    e1 = gate.request("lead_outbound", "L-drv", beat=1)
    assert leg.authorize(e1, "L-drv", "tok-drv")["ok"]
    e2 = gate.request("lead_outbound", "L-nodraft", beat=1)
    assert leg.authorize(e2, "L-nodraft", "tok-nod")["ok"]
    os.environ["OCTOPUS_WIRE_LEAD_OUTBOUND"] = "1"
    spy = SpyImpl()
    _orig = lot._default_send_impl
    lot._default_send_impl = spy
    try:
        out = ow.drive_outbound(gate=gate, now_ms=int(NOW_S * 1000))
    finally:
        lot._default_send_impl = _orig
        os.environ.pop("OCTOPUS_WIRE_LEAD_OUTBOUND", None)
    assert out["sent"] == 1 and out["driven"] == 1, out
    assert out["skipped"] == 1, out
    assert len(spy.calls) == 1 and spy.calls[0]["to"] == "drv.customer@example.com", \
        spy.calls
    import email as _em
    _m = _em.message_from_string(spy.calls[0]["message"])
    _body = _m.get_payload(decode=True).decode("utf-8")
    assert "Repaint of hallway" in _body, \
        f"بدنهٔ پیش‌نویسِ واقعی به transport نرسید: {_body!r}"
    # GAP-2: اگر روزی فیکسچرِ بالا دوباره بی‌مبلغ شود، این تست باید همان‌جا
    # قرمز شود — نه اینکه بی‌صدا یک «کوت»ِ بی‌عدد را سبز بشمارد.
    assert "A$1,980.00" in _body, \
        f"مبلغِ ثبت‌شدهٔ کوت به بدنه نرسید (GAP-2): {_body!r}"
    assert gate.status_of(e1) == "settled", gate.status_of(e1)
    assert gate.status_of(e2) == "pending", "بی‌پیش‌نویس نباید release/settle شود"
    assert '"no-draft"' in _events_text(), "رسیدِ no-draft نوشته نشد"
    assert ow.sends_today(now=NOW_S) == 1, "ارسالِ درایور شمرده نشد"


def t_i_driver_never_sends_a_market_signal_even_if_somehow_authorized():
    """R1 ساختاری در درایور: حتی اگر یک market_signal به‌زور authorize شده
    باشد، بازچکِ گیت (may_release داخلِ send_one) آن را deny می‌کند —
    صفر transport، صفر settle."""
    import lead_effect_gate as leg
    _set_creds(True)
    _fresh_counter()
    try:
        leg._authz_store().unlink()
    except OSError:
        pass
    _seed_inbox("L-sig", email="victim@example.com",
                candidate_type="market_signal", basis="none",
                channel="facebook_group", attribution_id="AT-SIG-001")
    _seed_draft("AT-SIG-001")
    gate = _drv_gate("sig")
    eid = gate.request("lead_outbound", "L-sig", beat=1)
    assert leg.authorize(eid, "L-sig", "tok-sig")["ok"]   # authorize ِ زوری
    os.environ["OCTOPUS_WIRE_LEAD_OUTBOUND"] = "1"
    spy = SpyImpl()
    _orig = lot._default_send_impl
    lot._default_send_impl = spy
    try:
        out = ow.drive_outbound(gate=gate, now_ms=int(NOW_S * 1000))
    finally:
        lot._default_send_impl = _orig
        os.environ.pop("OCTOPUS_WIRE_LEAD_OUTBOUND", None)
    assert out["sent"] == 0, out
    assert not spy.calls, "market_signal به transport رسید — نقضِ R1"
    assert gate.status_of(eid) == "pending", \
        f"سیگنال نباید settle شود: {gate.status_of(eid)!r}"
    res = [r for r in out.get("results", []) if r["effect_id"] == eid]
    assert res and res[0]["status"] == "gate_denied", out


# ── آلارمِ send_one: NOT_ARMED (طراحی) در برابرِ شکستِ واقعی (۲۰۲۶-۰۸-۰۶) ──────
def t_q_a_not_armed_stub_stays_quiet_but_a_real_failure_still_alarms():
    """همان کلاسِ آلارمِ گمراه‌کنندهٔ امشب (model_router/deep_think/self_patch —
    سقفِ روزانهٔ فوگو را «خرابی» می‌خواندند)، این‌بار در send_one: قبلِ فیکس، هر
    effectِ کانالِ غیرایمیل که به stubِ NOT_ARMED می‌خورد (طراحیِ همیشگی —
    docstring بالای فایل: «بقیهٔ کانال‌ها stub می‌مانند») همان هشدارِ
    «transport نفرستاد» ی را می‌گرفت که برای شکستِ واقعیِ SMTP گرفته می‌شود.
    باید تفکیک شود: NOT_ARMED ساکت بماند؛ شکستِ واقعیِ کانالِ مسلح (email +
    creds + SMTP ناموفق) همان هشدارِ قدیمی را بدهد."""
    import lead_effect_gate as leg
    calls = []
    real_alert = opslib.alert
    opslib.alert = lambda items: calls.extend(list(items))
    try:
        # (الف) کانالِ غیرایمیل بدونِ contact.email → stubِ NOT_ARMED طراحی‌شده
        _fresh_counter()
        try:
            leg._authz_store().unlink()
        except OSError:
            pass
        gate = _drv_gate("q-notarmed")
        eid = gate.request("lead_outbound", "L-q1", beat=1)
        assert leg.authorize(eid, "L-q1", "tok-q1")["ok"]
        os.environ["OCTOPUS_WIRE_LEAD_OUTBOUND"] = "1"
        try:
            cand = {"lead_id": "L-q1", "candidate_type": "consented_inbound",
                    "consent": {"basis": "explicit"},
                    "request": {"scope_text": "repaint hallway"},
                    "contact": {}, "source": {"channel": "telegram_manual"}}
            r = ow.send_one(eid, cand, "hello", gate=gate, now_ms=int(NOW_S * 1000))
        finally:
            os.environ.pop("OCTOPUS_WIRE_LEAD_OUTBOUND", None)
        assert r["sent"] is False and r["status"] == "NOT_ARMED", r
        assert not calls, f"NOT_ARMED ِ طراحی‌شده نباید alert بزند: {calls}"

        # (ب) کانالِ email مسلح ولی SMTP واقعاً شکست می‌خورد → همان هشدارِ قدیمی
        calls.clear()
        _set_creds(True)
        _fresh_counter()
        try:
            leg._authz_store().unlink()
        except OSError:
            pass
        gate2 = _drv_gate("q-fail")
        eid2 = gate2.request("lead_outbound", "L-q2", beat=1)
        assert leg.authorize(eid2, "L-q2", "tok-q2")["ok"]
        os.environ["OCTOPUS_WIRE_LEAD_OUTBOUND"] = "1"
        spy = SpyImpl(fail=True)
        _orig = lot._default_send_impl
        lot._default_send_impl = spy
        try:
            # _cand() به‌تنهایی consent ندارد (basis="" → unknown → gate deny
            # می‌کند قبل از رسیدن به transport) — این‌جا باید مثلِ t_ib/_seed_inbox
            # رضایتِ صریح داشته باشد تا واقعاً به transport برسد و SMTP شکست بخورد.
            cand2 = _cand("L-q2", candidate_type="consented_inbound",
                          consent={"basis": "explicit"},
                          request={"scope_text": "repaint hallway"})
            r2 = ow.send_one(eid2, cand2, {"subject": "Q", "body": "x"},
                             gate=gate2, now_ms=int(NOW_S * 1000))
        finally:
            lot._default_send_impl = _orig
            os.environ.pop("OCTOPUS_WIRE_LEAD_OUTBOUND", None)
        assert r2["sent"] is False and r2["status"] == "FAILED", r2
        assert calls, "شکستِ واقعیِ SMTP باید alert بزند"
        assert "transport نفرستاد" in calls[-1], calls[-1]
        assert "NOT_ARMED" not in calls[-1], calls[-1]
    finally:
        opslib.alert = real_alert
        _set_creds(False)


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_lead_outbound_transport: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
