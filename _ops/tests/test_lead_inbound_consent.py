"""test_lead_inbound_consent.py — پهن‌کردنِ مرزِ رضایت، و هر چیزی که نباید با آن پهن شود.

رأیِ مالک ۲۰۲۶-۰۸-۰۱: کسی که **خودش** به آدرسِ کسب‌وکار ایمیل زده، رضایتِ صریح
دارد. حقوقاً درست است — Spam Act 2003 روی پیامِ **ناخواسته** است و پاسخ به
آغازگر ناخواسته نیست — ولی این تنها تغییری در کلِ لوله است که **مرز** را
جابه‌جا می‌کند، نه یک قابلیت را. پس بارِ اثبات این‌جا سنگین‌تر از هر جای دیگر
است.

پیش از این تغییر: ایمیلِ مستقیم → کانالِ `other` → `market_signal` → لید ثبت
می‌شد ولی هیچ پاسخی نمی‌گرفت. یعنی مسیرِ **اصلی** ساکت بود.

خطری که این تغییر می‌سازد و این فایل می‌بندد: سقفِ کانال در
`consent_firewall._CHANNEL_CEILING` تعریف می‌شود و **هر** رکوردی که کانالش
`email_inbound` باشد `consented_inbound` می‌گیرد. اگر روزی ماژولِ دیگری — مثلاً
یک برداشت‌گرِ آدرس — همان رشته را بنویسد، دیوار بازش می‌کند. کنترل: تنها یک
تولیدکنندهٔ تولیدی مجاز است و آن با AST سنجیده می‌شود (t_h).

و مهم‌تر از همه: **پهن‌شدن نباید هیچ گاردِ دیگری را شل کند.** شش گاردِ
طبقه‌بند با فلگِ روشن هم باید دقیقاً همان‌قدر سخت‌گیر بمانند (t_c…t_g).
"""
import ast
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))

import harness  # noqa: E402
ENV = harness.setup("lead-inbound-consent")

sys.path.insert(0, str(_HERE.parent / "legs"))
import os                        # noqa: E402
import consent_firewall as cf    # noqa: E402
import lead_candidate_inbox as lci  # noqa: E402
import lead_email_intake as ie   # noqa: E402

FLAG = ie.INBOUND_CONSENT_FLAG
_OPS = _HERE.parent


def _on():
    os.environ[FLAG] = "1"


def _off():
    os.environ.pop(FLAG, None)


def _msg(**over) -> dict:
    m = {"message_id": "<real@customer.test>",
         "from": "Sam Jones <sam@customer.test>",
         "subject": "Painting quote for 3 bedrooms",
         "body": "Hi, I need my 3 bedrooms painted in Carlingford. When can you visit?",
         "date": "2026-08-01"}
    m.update(over)
    return m


def _ch(msg=None) -> str:
    return str(ie.classify(ie.normalize(msg or _msg())).get("channel") or "")


# ── فلگ: دو دنیای دقیق ──────────────────────────────────────────────────────
def t_a_flag_off_is_exactly_yesterday():
    """خاموش = `other` = market_signal = بدونِ پاسخِ خودکار. بایت‌به‌بایتِ دیروز."""
    _off()
    assert _ch() == "other"
    v = cf.evaluate(ie.to_candidate(ie.normalize(_msg()), "other", "k1"))
    assert v["candidate_type"] == "market_signal", v
    assert v["outreach_allowed"] is False, v


def t_b_flag_on_makes_a_real_inquiry_consented():
    _on()
    try:
        assert _ch() == "email_inbound"
        cand = ie.to_candidate(ie.normalize(_msg()), "email_inbound", "k2")
        assert cand["consent"]["basis"] == "explicit", cand["consent"]
        assert cand["consent"]["evidence"] == "inbound_email_to_business_address"
        v = cf.evaluate(cand)
        assert v["candidate_type"] == "consented_inbound", v
        assert v["outreach_allowed"] is True, v
    finally:
        _off()


# ── ناوردیِ اصلی: پهن‌شدن هیچ گاردی را شل نمی‌کند ────────────────────────────
def t_c_bulk_and_automated_mail_is_still_refused():
    """خبرنامه، اعلانِ بانک، پاسخِ خودکار — هیچ‌کدام نباید لید شوند."""
    _on()
    try:
        for over in (
                {"headers": {"list-unsubscribe": "<mailto:x@y>"}},
                {"headers": {"precedence": "bulk"}},
                {"headers": {"auto-submitted": "auto-replied"}}):
            m = _msg()
            m.update(over)
            assert _ch(m) == "", f"پیامِ انبوه/خودکار لید شد: {over}"
    finally:
        _off()


def t_d_a_noreply_sender_is_still_refused():
    _on()
    try:
        assert _ch(_msg(**{"from": "No Reply <noreply@bigcorp.test>"})) == ""
    finally:
        _off()


def t_e_marketing_text_is_still_refused():
    """پیامی که خودش تبلیغ است، لیدِ نقاشی نیست — حتی اگر واژهٔ رنگ داشته باشد."""
    _on()
    try:
        mark = sorted(ie._MARKETING_MARKS)[0]
        m = _msg(body="I need my bedrooms painted. When can you quote? " + mark)
        assert _ch(m) == "", f"نشانهٔ بازاریابی «{mark}» رد نشد"
    finally:
        _off()


def t_f_both_term_families_are_still_required():
    """فقط «کِی می‌آیی» بدونِ واژهٔ خدمت، و برعکس — هیچ‌کدام لید نیست."""
    _on()
    try:
        assert _ch(_msg(subject="hello", body="When can you visit? How much?")) == ""
        assert _ch(_msg(subject="paint", body="painting walls ceilings")) == ""
    finally:
        _off()


def t_g_an_inquiry_with_no_way_to_answer_is_still_refused():
    """لیدی که نمی‌شود جوابش را داد، لید نیست — و حالا که کانالش رضایت می‌گیرد،
    این گارد از قبل هم مهم‌تر است."""
    _on()
    try:
        assert _ch(_msg(**{"from": "Sam Jones", "body":
                           "I need my bedrooms painted. Please quote."})) == ""
    finally:
        _off()


def t_ga_owner_mail_to_himself_is_still_refused():
    _on()
    try:
        own = (ie._owner_addresses() or ("",))[0]
        if not own:
            os.environ["OCTOPUS_LEAD_OWNER_ADDRESSES"] = "boss@mp.test"
            own = "boss@mp.test"
        assert _ch(_msg(**{"from": f"Me <{own}>"})) == ""
    finally:
        os.environ.pop("OCTOPUS_LEAD_OWNER_ADDRESSES", None)
        _off()


# ── مرزِ اعتماد: تنها یک تولیدکننده ─────────────────────────────────────────
def t_h_exactly_one_production_module_may_emit_this_channel():
    """قلبِ ریسکِ این تغییر.

    سقفِ کانال یعنی **هر** رکوردی با این رشته `consented_inbound` می‌گیرد. اگر
    فردا ماژولِ دیگری — یک برداشت‌گرِ آدرس، یک import ِ CSV — همان رشته را
    بنویسد، دیوار بازش می‌کند و کسی متوجه نمی‌شود. پس تعداد تولیدکننده باید
    قفل باشد، نه توصیه.

    سه ذکرِ مجاز: تعریفِ سقف در دیوار، واژگانِ معتبر در inbox، و خودِ
    تولیدکننده. (`observability/leg_monitor.py` هم این رشته را دارد ولی آن
    نامِ **ماژولِ** `legs/email_inbound.py` است، نه مقدارِ کانال — تصادفِ رشته،
    و به همین دلیل این تست بر پایهٔ **فایل** می‌سنجد نه شمارشِ خام.)
    """
    allowed = {"legs/consent_firewall.py", "legs/lead_candidate_inbox.py",
               "legs/lead_email_intake.py", "observability/leg_monitor.py"}
    found = set()
    for p in _OPS.rglob("*.py"):
        if any(x in p.parts for x in ("tests", "__pycache__", "_Archive")):
            continue
        try:
            tree = ast.parse(p.read_text("utf-8", errors="replace"))
        except (SyntaxError, OSError, ValueError):
            continue
        for n in ast.walk(tree):
            if isinstance(n, ast.Constant) and n.value == "email_inbound":
                found.add(str(p.relative_to(_OPS)).replace("\\", "/"))
    extra = found - allowed
    assert not extra, (
        f"ماژولِ تازه‌ای کانالِ رضایت‌دار را می‌سازد: {sorted(extra)} — "
        "اگر عمدی است، مرزِ اعتماد را بازبینی کن و این فهرست را آگاهانه به‌روز کن")


def t_i_a_lying_producer_still_cannot_promote_itself():
    """رکوردی که کانالش چیزِ دیگری است ولی خودش را consented اعلام می‌کند."""
    for ch in ("other", "nsw_da", "domain_listing", "facebook_group", "made_up"):
        v = cf.evaluate({"source": {"channel": ch},
                         "candidate_type": "consented_inbound",
                         "consent": {"basis": "explicit"},
                         "request": {"scope_text": "paint my house"}})
        assert v["candidate_type"] != "consented_inbound", (ch, v)
        assert v["outreach_allowed"] is False, (ch, v)


def t_j_the_channel_is_valid_at_the_canonical_door():
    """اگر واژگانِ inbox آن را نشناسد، هر لیدِ واقعی quarantine می‌شود."""
    assert "email_inbound" in lci._VALID_CHANNELS
    assert cf._CHANNEL_CEILING.get("email_inbound") == "consented_inbound"


def t_k_teeth_without_the_flag_the_ceiling_is_unreachable():
    """دندان: فلگ تنها راهِ رسیدن به این کانال است.

    اگر روزی کسی گیتِ فلگ را از `classify` بردارد، این تست باید بفهمد — چون
    آن‌وقت خاموش‌بودن هم `email_inbound` می‌دهد.
    """
    _off()
    assert _ch() == "other", "بدونِ فلگ نباید به کانالِ رضایت‌دار رسید"
    _on()
    try:
        assert _ch() == "email_inbound"
    finally:
        _off()
    assert _ch() == "other", "خاموش‌کردنِ فلگ باید فوراً برگرداند"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_lead_inbound_consent: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
