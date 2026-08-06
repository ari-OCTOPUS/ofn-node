#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_lead_price_in_email — کوتی که عدد ندارد کوت نیست (GAP-2، ۲۰۲۶-۰۸-۰۱).

مسئله‌ای که این تست قفل می‌کند: تا امروز بدنهٔ ایمیلی که واقعاً به مشتری
می‌رفت فقط `intake.scope` بود — یک «Quote QT-…» بدونِ هیچ مبلغی. مشتری یک
ایمیل با موضوعِ «کوت» می‌گرفت که داخلش هیچ عددی نبود.

قواعدی که این‌جا گارد می‌شوند:
  · مبلغِ **ثبت‌شده** (breakdown.total_incl_gst ِ همان رکوردِ lead-quote.v1) در
    بدنه می‌نشیند — با ارز، کامای هزارگان و افشای GST؛ همان‌طور که مشتریِ
    استرالیایی انتظار دارد.
  · عدد **دوباره محاسبه نمی‌شود**: اگر نرخ‌های pricing.py فردا عوض شوند،
    ایمیل باید همان عددِ کوت را بگوید، نه عددِ تازه.
  · مبلغِ غایب/صفر/خراب ⇒ **ارسال نمی‌شود** و در عوض رسیدِ `no-price:<دلیل>` +
    alert به مالک می‌نشیند. نه ایمیلِ بی‌قیمت، نه سکوت.
  · خطِ opt-out (الزامِ انطباق) در بدنه باقی می‌مانَد.
  · گیت/سقف/ترتیبِ settle دست‌نخورده: کوتِ بی‌مبلغ effect را مصرف نمی‌کند
    (pending می‌مانَد) و شمارندهٔ سقف را بالا نمی‌برد.
"""
import json
import os
import sys
from pathlib import Path

import harness

ENV = harness.setup("lead-price-in-email")     # قبل از هر importی که state می‌نویسد

_OPS = Path(__file__).resolve().parent.parent
for _p in (str(_OPS), str(_OPS / "legs"), str(_OPS / "budget"), str(_OPS / "outcomes")):
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

# ⚠️ همان تلهٔ ۰۷-۳۱: کلیدهای زندهٔ ماشینِ میزبان (یا `.env` ِ واقعی) می‌توانند
# transport را بی‌خبر مسلح کنند و ایمیلِ واقعی بفرستند. هر مسیرِ credential
# صریحاً کنترل می‌شود و `.env` هرگز لود نمی‌شود.
mc._ensure_env_loaded = lambda: None
_SMTP_ENV = {"OCTOPUS_SMTP_HOST": "localhost", "OCTOPUS_SMTP_PORT": "2525",
             "OCTOPUS_SMTP_USER": "price-test-user",
             "OCTOPUS_SMTP_PASS": "price-test-pass",
             "OCTOPUS_SMTP_FROM": "quotes@example.com"}
_CRED_KEYS = tuple(_SMTP_ENV) + (mc.GMAIL_ADDR_ENV, mc.GMAIL_SECRET_ENV,
                                 mc.GMAIL_FALLBACK_FLAG)
for _k in _CRED_KEYS:
    os.environ.pop(_k, None)

NOW_MS = 1_785_400_000_000
NOW_S = NOW_MS / 1000.0

# عددِ نشانه‌دار: هم کاما می‌خواهد، هم اعشار، و هیچ‌جای دیگرِ سیستم تولیدش نمی‌کند.
PRICE_LO = 4321.05
PRICE_HI = 6543.20
PRICE_TEXT = "A$4,321.05 – A$6,543.20 (incl. GST)"


class SpyImpl:
    """جاسوسِ لایهٔ سیم (send_impl) — هیچ SMTP واقعی؛ پیامِ کامل نگه داشته می‌شود."""

    def __init__(self):
        self.calls = []

    def __call__(self, host, port, user, pw, from_addr, to_addr, message):
        self.calls.append({"to": to_addr, "message": message})


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
    db = chrono.ChronoDB(str(opslib.STATE_DIR / f"price-{name}.db"))
    return chrono.EffectorGate(db)


def _events_text() -> str:
    try:
        return (opslib.STATE_DIR / "legs" / "lead-inbox" / "events.jsonl").read_text("utf-8")
    except OSError:
        return ""


def _alerts_text() -> str:
    try:
        return opslib.ALERTS_MD.read_text("utf-8")
    except OSError:
        return ""


def _seed_inbox(lead_id, attribution_id, email="price.customer@example.com"):
    p = opslib.STATE_DIR / "legs" / "lead-inbox" / f"{lead_id}.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({
        "lead_id": lead_id, "source": "telegram_manual",
        "attribution_id": attribution_id,
        "candidate": {"candidate_type": "consented_inbound",
                      "consent": {"basis": "explicit"},
                      "request": {"scope_text": "repaint hallway"},
                      "contact": {"email": email}}}, ensure_ascii=False), "utf-8")
    return p


def _seed_quote(attribution_id, breakdown, scope="Repaint of hallway, two coats.",
                intake=None):
    """رکوردِ lead-quote.v1 با یک breakdown ِ دلخواه (None = بدونِ breakdown)."""
    d = opslib.STATE_DIR / "legs" / "lead-drafts"
    d.mkdir(parents=True, exist_ok=True)
    rec = {"schema": "lead-quote.v1", "qt_number": "QT-20260801-007",
           "attribution_id": attribution_id,
           "intake": dict(intake) if intake else {"scope": scope},
           "draft_only": True, "sent": False}
    if breakdown is not None:
        rec["breakdown"] = breakdown
    p = d / f"{attribution_id}.json"
    p.write_text(json.dumps(rec, ensure_ascii=False), "utf-8")
    return p


# ── consent_gate D2a wiring (۲۰۲۶-۰۸-۰۷) — کمکِ گرانتِ رضایتِ store-backed ─────────
# drive_outbound حالا consent_gate.may_draft را **قبل از** compose (_draft_for)
# صدا می‌زند (لایهٔ سومِ مستقلِ consent). این فایل منطقِ قیمت را می‌سنجد (GAP-2)،
# نه consent_gate را — پس هر لیدی که از `_drive()` می‌گذرد باید رضایتِ store-backed
# داشته باشد، وگرنه هرگز به _draft_for/بررسیِ قیمت نمی‌رسد و consent-denied ِ
# زودتر منطقِ no-price را می‌پوشاند (هم‌الگوی test_lead_outbound_transport.py).
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


def _drive(lead_id, attribution_id, breakdown, *,
           scope="Repaint of hallway, two coats.", intake=None):
    """قوسِ تولیدیِ کامل: authorize → drive_outbound → send_one → transport (جاسوس).
    خروجی: (out, spy, gate, effect_id)."""
    _fresh_counter()
    _fresh_authz()
    _seed_inbox(lead_id, attribution_id)
    _seed_quote(attribution_id, breakdown, scope=scope, intake=intake)
    gate = _gate(lead_id)
    eid = gate.request("lead_outbound", lead_id, beat=1)
    assert leg.authorize(eid, lead_id, f"tok-{lead_id}")["ok"]
    _grant_consent(lead_id)
    spy = SpyImpl()
    os.environ["OCTOPUS_WIRE_LEAD_OUTBOUND"] = "1"
    os.environ.update(_SMTP_ENV)
    _orig = lot._default_send_impl
    lot._default_send_impl = spy
    try:
        out = ow.drive_outbound(gate=gate, now_ms=NOW_MS)
    finally:
        lot._default_send_impl = _orig
        os.environ.pop("OCTOPUS_WIRE_LEAD_OUTBOUND", None)
        os.environ.pop(cg.FLAG, None)
        for k in _CRED_KEYS:
            os.environ.pop(k, None)
    return out, spy, gate, eid


def _body_of(message: str) -> str:
    import email as _em
    return _em.message_from_string(message).get_payload(decode=True).decode("utf-8")


# ── ۱. قالبِ پول ────────────────────────────────────────────────────────────────
def t_a_money_is_formatted_the_way_an_australian_customer_expects():
    """ارز + کامای هزارگان + دو رقمِ اعشار + افشای GST. lo == hi ⇒ یک عدد."""
    assert ow.format_aud(4321.05, 6543.20) == PRICE_TEXT, ow.format_aud(4321.05, 6543.2)
    one = ow.format_aud(1200.0, 1200.0)
    assert one == "A$1,200.00 (incl. GST)", one
    assert "–" not in one, "بازهٔ تکراری برای عددِ یکتا"
    big = ow.format_aud(1234567.8, 1234567.8)
    assert big == "A$1,234,567.80 (incl. GST)", big


# ── ۲. مبلغِ واقعی در ایمیلِ واقعی ─────────────────────────────────────────────
def t_b_the_recorded_amount_reaches_the_customers_email():
    """قلبِ GAP-2: عددِ ثبت‌شدهٔ کوت باید در بدنه‌ای باشد که به SMTP می‌رسد."""
    out, spy, gate, eid = _drive("L-price-ok", "AT-PRICE-001",
                                 {"total_incl_gst": [PRICE_LO, PRICE_HI]})
    assert out["sent"] == 1 and out["driven"] == 1, out
    assert len(spy.calls) == 1, spy.calls
    body = _body_of(spy.calls[0]["message"])
    assert PRICE_TEXT in body, f"مبلغ در بدنه نیست: {body!r}"
    assert "Repaint of hallway" in body, f"scope گم شد: {body!r}"
    assert gate.status_of(eid) == "settled", gate.status_of(eid)
    assert ow.sends_today(now=NOW_S) == 1, "ارسالِ قیمت‌دار شمرده نشد"


def t_c_the_opt_out_line_survives_the_new_body():
    """الزامِ انطباق: افزودنِ قیمت نباید خطِ opt-out را از بدنه بیرون کند."""
    out, spy, _g, _e = _drive("L-price-optout", "AT-PRICE-002",
                              {"total_incl_gst": [PRICE_LO, PRICE_HI]})
    assert out["sent"] == 1, out
    body = _body_of(spy.calls[0]["message"])
    assert "Reply STOP to opt out." in body, f"خطِ opt-out گم شد: {body!r}"


def t_d_the_number_is_the_recorded_one_not_a_recomputed_one():
    """رکورد یک intake ِ **کامل** دارد؛ پس اگر کسی روزی قیمت را از روی همان
    intake دوباره محاسبه کند، عددِ زنده و معتبری در می‌آید — ولی عددی که مشتری
    و دفتر روی کوت دیده‌اند این نیست. بدنه باید عددِ **ثبت‌شده** را بگوید.
    (این تست تا وقتی intake ِ سیدشده نیمه‌کاره بود بی‌دندان بود: محاسبهٔ مجدد
    صفر می‌داد و جهشِ re-compute زنده می‌ماند — جهشِ M5 ِ ۰۸-۰۱.)"""
    import pricing   # noqa: WPS433 — فقط برای اثباتِ «عددِ محاسبه‌ای فرق دارد»
    intake_full = {"scope": "Repaint of hallway", "size_m2": 120.0,
                   "area_type": "interior", "surface_type": "wall",
                   "prep_level": "standard", "access_type": "ladder",
                   "segment": "residential", "paint_quality": "standard",
                   "coat_count": 2}
    recomputed = pricing.estimate_price(
        pricing.QuoteIntake(**intake_full)).to_dict()["total_incl_gst"]
    assert float(recomputed[1]) > 0, f"پایهٔ محاسبه صفر است — تست بی‌دندان: {recomputed}"
    assert abs(float(recomputed[1]) - PRICE_HI) > 1.0, \
        f"عددِ محاسبه‌ای تصادفاً برابرِ عددِ ثبت‌شده است — تست بی‌دندان می‌شود: {recomputed}"
    out, spy, _g, _e = _drive("L-price-frozen", "AT-PRICE-003",
                              {"total_incl_gst": [PRICE_LO, PRICE_HI]},
                              intake=intake_full)
    assert out["sent"] == 1, out
    body = _body_of(spy.calls[0]["message"])
    assert PRICE_TEXT in body, body
    assert f"{float(recomputed[1]):,.2f}" not in body, \
        f"عددِ re-compute در ایمیل نشست: {body!r}"


def t_e_the_second_recorded_source_is_accepted_too():
    """رکوردِ قدیمی‌ای که breakdown ندارد ولی همان عدد در
    proposal.payload.price_range_aud نشسته است — همان عدد، نه محاسبهٔ نو."""
    _fresh_counter()
    _seed_quote("AT-PRICE-004", None)
    p = opslib.STATE_DIR / "legs" / "lead-drafts" / "AT-PRICE-004.json"
    rec = json.loads(p.read_text("utf-8"))
    rec["proposal"] = {"payload": {"price_range_aud": [PRICE_LO, PRICE_HI]}}
    p.write_text(json.dumps(rec, ensure_ascii=False), "utf-8")
    draft, why = ow._draft_for("AT-PRICE-004")
    assert why == "" and draft is not None, (draft, why)
    assert PRICE_TEXT in draft["body"], draft


# ── ۳. مبلغِ غایب/صفر/خراب: نه ارسال، نه سکوت ─────────────────────────────────
def t_f_a_quote_without_an_amount_is_never_emailed():
    """رکوردِ بی‌مبلغ: صفر تماسِ transport، effect دست‌نخورده، شمارنده دست‌نخورده،
    رسیدِ no-price نوشته می‌شود و مالک alert می‌گیرد."""
    out, spy, gate, eid = _drive("L-price-missing", "AT-PRICE-005", None)
    assert out["sent"] == 0 and out["skipped"] == 1, out
    assert spy.calls == [], f"ایمیلِ بی‌قیمت رفت: {spy.calls}"
    assert gate.status_of(eid) == "pending", \
        f"effect ِ بی‌مبلغ مصرف شد: {gate.status_of(eid)!r}"
    assert ow.sends_today(now=NOW_S) == 0, "ارسالِ نشده شمرده شد"
    assert '"no-price:missing"' in _events_text(), "رسیدِ no-price نوشته نشد"
    assert "بدونِ مبلغ" in _alerts_text(), "مالک از کوتِ بی‌مبلغ خبردار نشد"


def t_g_a_zero_amount_is_not_a_price():
    """«۰» بدترین حالت است: شبیهِ قیمت است ولی قیمت نیست."""
    out, spy, gate, eid = _drive("L-price-zero", "AT-PRICE-006",
                                 {"total_incl_gst": [0, 0]})
    assert out["sent"] == 0 and spy.calls == [], (out, spy.calls)
    assert gate.status_of(eid) == "pending", gate.status_of(eid)
    assert '"no-price:zero-or-negative"' in _events_text(), _events_text()[-400:]
    draft, why = ow._draft_for("AT-PRICE-006")
    assert draft is None and why == "no-price:zero-or-negative", (draft, why)


def t_h_broken_amount_shapes_are_all_refused_with_a_reason():
    """هر شکلِ خرابِ مبلغ یک دلیلِ **متمایز** می‌دهد — «نمی‌دانم» هرگز ارسال نیست."""
    cases = [({"total_incl_gst": "1500"}, "no-price:malformed"),
             ({"total_incl_gst": [1500.0]}, "no-price:malformed"),
             ({"total_incl_gst": ["abc", "def"]}, "no-price:non-numeric"),
             ({"total_incl_gst": [None, 1500.0]}, "no-price:non-numeric"),
             ({"total_incl_gst": [-10.0, 1500.0]}, "no-price:zero-or-negative"),
             ({"total_incl_gst": [9000.0, 1500.0]}, "no-price:inverted"),
             ({}, "no-price:missing")]
    for i, (bd, expect) in enumerate(cases):
        aid = f"AT-PRICE-BAD-{i:02d}"
        _seed_quote(aid, bd)
        draft, why = ow._draft_for(aid)
        assert draft is None, (aid, bd, draft)
        assert why == expect, (aid, bd, why, expect)


def t_i_a_missing_draft_is_still_a_missing_draft():
    """قراردادِ قدیمی نشکند: نبودِ رکورد همچنان `no-draft` است، نه `no-price`."""
    draft, why = ow._draft_for("AT-PRICE-NOPE")
    assert draft is None and why == "no-draft", (draft, why)
    draft2, why2 = ow._draft_for("")
    assert draft2 is None and why2 == "no-draft", (draft2, why2)


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_lead_price_in_email: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
