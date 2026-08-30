#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_lead_card — کارتی که مردِ روی نردبان می‌تواند با یک دست به آن عمل کند.

گزارشِ WHY-NO-REAL-LEADS-2026-08-01، ردیف‌های ۱۱ / ۱۲ / ۱۴. اثبات می‌کند:

  A) flag خاموش = بایت‌به‌بایت همان امروز — خروجی با بازسازیِ **verbatim** ِ بدنهٔ
     پیش از فیکس مقایسه می‌شود، نه با یک ادعا.
  B) دندان: همان بدنهٔ بازسازی‌شده نه نام دارد، نه تلفن، نه ایمیل، نه `tel:` —
     پس هر assert ِ تماسِ این فایل روی کدِ دیروز **قرمز** است.
  C) `tel:` ِ کارآمد: نرمال‌سازیِ E.164 ِ استرالیا روی هر شکلِ واقعیِ ورودی.
  D) bidi: هر تکهٔ LTR داخلِ ایزولهٔ U+2066…U+2069 (زخمِ ثبت‌شدهٔ این مخزن)؛
     رقمِ فارسی برای امتیاز، ASCII برای شماره (رقمِ فارسی شماره‌گیری نمی‌شود).
  E) تحویل = **پیامِ نو**، هرگز ویرایش — با transport ِ جعلی که هر دو مسیر را ثبت
     می‌کند: ۱ ارسال، ۰ ویرایش.
  F) هیچ دکمه‌ای ارسال نمی‌کند: فعل‌ها ⊆ SAFE_VERBS؛ صفحه‌کلیدِ متخاصم (prop/qt/url)
     تشخیص داده و **دور ریخته** می‌شود.
  G) لیدِ بی‌تماس ⇒ هشدارِ صریحِ «اطلاعات تماس ندارد»، نه شکافِ خالی، و بی‌دکمهٔ 📞.
  H) صداکنندهٔ تولیدی: مسیرِ واقعی `score_lead(...).card()` — نه فقط خودِ ماژول.

⚠️ صفر شبکه، صفر SMTP، صفر transport ِ واقعی. transport فقط جعلیِ تزریقی.
"""
import os
import sys
from pathlib import Path

import harness

ENV = harness.setup("lead-card")

_OPS = Path(__file__).resolve().parent.parent
for _p in (str(_OPS), str(_OPS / "legs")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ماشینِ میزبان فلگِ زنده دارد — تست باید قطعی باشد.
for _k in ("OCTOPUS_WIRE_LEAD_CARD_CONTACT", "OCTOPUS_LEAD_DIRECT_RESIDENTIAL"):
    os.environ.pop(_k, None)

import lead_card as lc        # noqa: E402
import lead_scorer as ls      # noqa: E402

LRI, PDI = "⁦", "⁩"

LEAD = {
    "lead_id": "LEAD-20260801-007",
    "source": "website_form",
    "description": "Quote to repaint the interior of my 3 bedroom house, walls and ceilings",
    "address": "12 Pennant Pde, Carlingford NSW 2118",
    "suburb": "Carlingford",
    "candidate": {
        "contact": {"name": "Sarah Nguyen", "email": "sarah.nguyen@example.com",
                    "phone": "0412 345 678", "preferred_channel": "phone"},
        "request": {"scope_text": "Repaint interior"},
    },
}
NO_CONTACT_LEAD = {
    "lead_id": "LEAD-20260801-008",
    "source": "facebook_group",
    "description": "Someone in the group is after an exterior repaint",
    "suburb": "Baulkham Hills",
    "candidate": {"contact": {}},
}


def _scored(action="draft", score=72, lead=None):
    return ls.ScoredLead(category="residential_repaint_direct",
                         category_label="رنگ‌آمیزیِ مسکونیِ مستقیم",
                         score=score, action=action,
                         reasons=["paint_scope", "in_radius"],
                         lead=dict(lead if lead is not None else LEAD))


# ── بازسازیِ verbatim ِ بدنهٔ پیش از فیکس (lead_scorer.py:208-220، ۲۰۲۶-۰۸-۰۱) ──
# این تابع «دیروز» است. هر assert ِ تماسی که در ادامه می‌آید باید روی آن بشکند.
def _legacy_card(sc) -> str:
    L = sc.lead
    emoji = {"draft": "🟢", "save": "🟡", "skip": "⚪️"}.get(sc.action, "🏢")
    lines = [
        f"{emoji} {L.get('source', 'lead')} | score: {sc.score} | {sc.category}",
        f"📌 {str(L.get('description', '')).strip()}",
        f"📍 {L.get('address', 'n/a')}",
    ]
    if L.get("url"):
        lines.append(f"🔗 {L['url']}")
    lines.append("🧠 " + "; ".join(sc.reasons))
    return "\n".join(lines)


class FakeTransport:
    """کانالِ جعلی که **هر دو** مسیر را ثبت می‌کند تا «نو در برابر ویرایش» سنجیدنی شود."""

    def __init__(self, ok=True):
        self.sends, self.edits, self.ok = [], [], ok

    def send(self, text, keyboard=None, stream=None):
        self.sends.append({"text": text, "keyboard": keyboard, "stream": stream})
        return self.ok

    def edit(self, message_id, text, keyboard=None, stream=None):
        self.edits.append({"message_id": message_id, "text": text})
        return True


# ═══ A) flag خاموش = بایت‌به‌بایت همان امروز ═══════════════════════════════════
def t_a_flag_off_is_byte_identical_to_pre_fix():
    os.environ.pop(lc.FLAG, None)
    sc = _scored()
    assert lc.enabled() is False
    assert sc.card() == _legacy_card(sc), "flag خاموش خروجی را تغییر داد"
    # و «0» هم مثل غیاب است — غیاب یعنی خاموش، نه روشنِ ضمنی.
    os.environ[lc.FLAG] = "0"
    try:
        assert lc.enabled() is False
        assert sc.card() == _legacy_card(sc)
    finally:
        os.environ.pop(lc.FLAG, None)


# ═══ B) دندان: کارتِ دیروز هیچ راهی برای تماس ندارد ═══════════════════════════
def t_b_teeth_pre_fix_card_carries_no_contact():
    sc = _scored()
    old = _legacy_card(sc)
    for needle in ("Sarah Nguyen", "0412", "+61", "tel:", "sarah.nguyen@example.com"):
        assert needle not in old, f"بازسازیِ «دیروز» غلط است: {needle} در آن هست"
    # حالا همان لید با فلگِ روشن — همان assertهایی که بالا قرمزند، این‌جا سبزند.
    os.environ[lc.FLAG] = "1"
    try:
        new = sc.card()
        assert "Sarah Nguyen" in new, new
        assert "sarah.nguyen@example.com" in new, new
        assert "tel:+61412345678" in new, new
    finally:
        os.environ.pop(lc.FLAG, None)


# ═══ C) tel: ِ کارآمد ═════════════════════════════════════════════════════════
def t_c_tel_uri_normalises_every_real_australian_shape():
    cases = {
        "0412 345 678": "tel:+61412345678",
        "0412345678": "tel:+61412345678",
        "+61 412 345 678": "tel:+61412345678",
        "+61412345678": "tel:+61412345678",
        "61412345678": "tel:+61412345678",
        "(02) 9876 5432": "tel:+61298765432",
    }
    for raw, want in cases.items():
        assert lc.tel_uri(raw) == want, f"{raw!r} → {lc.tel_uri(raw)!r} != {want!r}"
    # غیرقابلِ نرمال‌سازی ⇒ None، نه حدس. حدسِ اشتباه = زنگ‌زدن به غریبه.
    for bad in ("", None, "n/a", "call me", "12345", "0412 34"):
        assert lc.tel_uri(bad) is None, f"{bad!r} حدس زده شد: {lc.tel_uri(bad)!r}"
    # و شماره در کارت، ASCII و شماره‌گیری‌شدنی می‌ماند.
    r = lc.render(LEAD, scored=_scored())
    assert r["tel_uri"] == "tel:+61412345678"
    assert "tel:+61412345678" in r["text"]
    assert "+61 412 345 678" in r["text"], r["text"]


# ═══ D) bidi + رقمِ فارسی ══════════════════════════════════════════════════════
def t_d_ltr_runs_are_bidi_isolated_and_digits_are_persian_only_in_prose():
    r = lc.render(LEAD, scored=_scored(score=72), lead_id="LEAD-20260801-007")
    text = r["text"]
    for run in ("+61 412 345 678", "tel:+61412345678",
                "sarah.nguyen@example.com", "LEAD-20260801-007", "website_form"):
        assert LRI + run + PDI in text, f"تکهٔ LTR بدونِ ایزوله: {run!r}"
    assert "امتیاز ۷۲" in text, text          # رقمِ فارسی در متنِ فارسی
    # ولی شماره هرگز فارسی نمی‌شود — رقمِ فارسی نه شماره‌گیری می‌شود نه linkify.
    for fa in "۰۱۲۳۴۵۶۷۸۹":
        assert fa not in r["tel_uri"]
    # هیچ ایزولهٔ باز-نشده‌ای نماند.
    assert text.count(LRI) == text.count(PDI), text


# ═══ E) پیامِ نو، نه ویرایش ═══════════════════════════════════════════════════
def t_e_delivered_as_new_message_never_an_edit():
    r = lc.render(LEAD, scored=_scored())
    assert r["delivery"] == lc.DELIVERY_NEW_MESSAGE == "new_message"
    assert r["edit_message_id"] is None
    tr = FakeTransport()
    out = lc.deliver(tr.send, r, edit_fn=tr.edit)
    assert out["sent"] is True and out["edits"] == 0, out
    assert len(tr.sends) == 1, tr.sends
    assert tr.edits == [], "کارت ویرایش شد — گوشیِ مالک هرگز نمی‌لرزد"
    assert tr.sends[0]["stream"] == "lead", tr.sends[0]
    # کانالِ خراب هرگز beat را نمی‌کشد و هرگز به ویرایش fallback نمی‌کند.
    def boom(text, keyboard=None, stream=None):
        raise RuntimeError("channel down")
    tr2 = FakeTransport()
    out2 = lc.deliver(boom, r, edit_fn=tr2.edit)
    assert out2["sent"] is False and out2["edits"] == 0 and tr2.edits == [], out2


# ═══ F) هیچ دکمه‌ای ارسال نمی‌کند ═════════════════════════════════════════════
def t_f_no_button_can_trigger_a_send():
    r = lc.render(LEAD, scored=_scored(), lead_id="LEAD-20260801-007",
                  first_reply={"subject": "Re: your painting enquiry",
                               "body": "Hi Sarah, thanks for getting in touch."},
                  verbs_ready={"lcall", "ldraft"})
    kb = r["keyboard"]
    assert kb is not None, "با verbs_ready اعلام‌شده باید دکمه بیاید"
    verbs = [str(b["callback_data"]).split(":", 1)[0]
             for row in kb["inline_keyboard"] for b in row]
    assert set(verbs) <= lc.SAFE_VERBS, verbs
    assert "lcall" in verbs and "ldraft" in verbs, verbs
    assert lc.has_send_button(kb) is False
    for row in kb["inline_keyboard"]:
        for b in row:
            assert "url" not in b and "web_app" not in b, b
    # بدونِ اعلامِ صریحِ فعل‌های مسیریابی‌شده ⇒ بی‌دکمه (هرگز دکمهٔ مرده).
    assert lc.render(LEAD, scored=_scored(), lead_id="X")["keyboard"] is None

    # صفحه‌کلیدِ متخاصم: هر سه شکل باید مثبت شوند و در تحویل **دور ریخته** شوند.
    for evil in (
        {"inline_keyboard": [[{"text": "✅ آره", "callback_data": "prop:ok:tok"}]]},
        {"inline_keyboard": [[{"text": "📄 کوت", "callback_data": "qt:send:1"}]]},
        {"inline_keyboard": [[{"text": "📞 زنگ", "url": "tel:+61412345678"}]]},
        {"inline_keyboard": [[{"text": "ارسال ایمیل", "callback_data": "lcall:X"}]]},
    ):
        assert lc.has_send_button(evil) is True, evil
        tr = FakeTransport()
        payload = dict(r, keyboard=evil)
        out = lc.deliver(tr.send, payload, edit_fn=tr.edit)
        assert out["sent"] is True and out["dropped_unsafe_keyboard"] is True, out
        assert tr.sends[0]["keyboard"] is None, tr.sends[0]

    # و پیش‌نویس فقط **مرور** می‌شود — هیچ transport ای صدا نمی‌خورد.
    dv = lc.draft_review_text({"subject": "Re: enquiry", "body": "Hi Sarah"},
                              lead_id="LEAD-20260801-007")
    assert "Hi Sarah" in dv and "مرور" in dv, dv


# ═══ G) لیدِ بی‌تماس: هشدارِ صریح، نه شکافِ خالی ═══════════════════════════════
def t_g_missing_contact_renders_explicit_warning_not_an_empty_gap():
    r = lc.render(NO_CONTACT_LEAD, scored=_scored(action="save", score=61,
                                                  lead=NO_CONTACT_LEAD),
                  lead_id="LEAD-20260801-008", verbs_ready={"lcall", "ldraft"})
    assert r["has_contact"] is False
    assert r["tel_uri"] is None
    assert "اطلاعات تماس ندارد" in r["text"], r["text"]
    assert set(r["missing"]) == {"نام", "تلفن", "ایمیل"}, r["missing"]
    assert r["keyboard"] is None, "بدونِ تلفن نباید دکمهٔ 📞 ساخته شود"
    assert "📞" not in r["text"], r["text"]
    # هیچ خطِ برچسب‌دارِ تهی («👤 » یا «✉️ ») نماند.
    for line in r["text"].splitlines():
        assert line.strip() not in ("👤", "✉️", "📞", "👤 <b></b>"), repr(line)
    # تماسِ ناقص (ایمیل هست، تلفن نه) ⇒ کارت زنده، ولی ناقص‌بودن اعلام می‌شود.
    partial = dict(NO_CONTACT_LEAD,
                   candidate={"contact": {"name": "Dan", "email": "dan@example.com"}})
    r2 = lc.render(partial, scored=_scored(lead=partial))
    assert r2["has_contact"] is True and r2["missing"] == ["تلفن"], r2["missing"]
    assert "ناقص" in r2["text"] and "اطلاعات تماس ندارد" not in r2["text"]


# ═══ H) شرحِ کار به زبانِ خودِ مشتری + محله ════════════════════════════════════
def t_h_card_carries_customer_words_and_suburb():
    text = lc.render(LEAD, scored=_scored())["text"]
    assert "Quote to repaint the interior of my 3 bedroom house" in text, text
    assert "Carlingford" in text, text


# ═══ I) صداکنندهٔ تولیدی: مسیرِ واقعیِ score_lead → .card() ═══════════════════
def t_i_production_path_score_lead_then_card():
    os.environ["OCTOPUS_LEAD_DIRECT_RESIDENTIAL"] = "1"
    os.environ[lc.FLAG] = "1"
    try:
        sc = ls.score_lead(dict(LEAD))
        card = sc.card()
        assert "Sarah Nguyen" in card and "tel:+61412345678" in card, card
        assert "sarah.nguyen@example.com" in card, card
        assert card != _legacy_card(sc)
    finally:
        os.environ.pop(lc.FLAG, None)
        os.environ.pop("OCTOPUS_LEAD_DIRECT_RESIDENTIAL", None)
    # فلگ که برداشته شد، همان شیء دوباره کارتِ دیروز را می‌دهد — rollback زنده است.
    assert sc.card() == _legacy_card(sc)


# ═══ J) هیچ I/O و هیچ شبکه‌ای ═════════════════════════════════════════════════
def t_j_module_is_pure_no_network_no_writes():
    src = (_OPS / "legs" / "lead_card.py").read_text("utf-8")
    for banned in ("smtplib", "socket", "requests", "urllib",
                   "write_text", "open(", "subprocess"):
        assert banned not in src, f"lead_card باید خالص بماند — {banned}"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_lead_card: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
