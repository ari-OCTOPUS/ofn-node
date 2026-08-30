"""test_lead_form_notification.py — مسیری که لوله برایش ساخته شد، و چهار جا شکست.

زمینه
─────
`lead_email_intake` (۱۳/۱۳) و `lead_first_reply` (۳۶/۳۶) هر دو سبز تحویل شدند.
بعد یک اعلانِ **واقعیِ فرمِ سایت** از سرتاسرِ لوله عبور داده شد — همان چیزی که
قرار است فردا از `masterpainting.sydney` برسد — و چهار نقص بیرون افتاد که
هیچ‌کدام از آن ۴۹ تست نمی‌دیدشان. علتِ مشترک: هر دو سوییت ماژولِ خودشان را
می‌سنجیدند، نه **درزِ میانشان**.

    ۱ ایمیلِ تماسِ لید = `noreply@` خودِ مالک.
      در اعلانِ فرم، پاکتِ نامه **خودِ سایت** است. ترتیبِ `reply_to → from →
      body` یعنی اگر فرم Reply-To نگذارد، آدرسِ noreply برنده می‌شود. لیدی
      ثبت می‌شد که هیچ‌کس نمی‌توانست به مشتری جواب دهد — و این تا لحظهٔ تماس
      نامرئی بود.

    ۲ «Hi Website».
      نامِ سلام از نامِ نمایشیِ فرستنده («Website Form») می‌آمد. اولین چیزی که
      مشتری می‌خواند.

    ۳ هیچ پاسخی، برای هر فرمی که فیلدِ ایمیل دارد — یعنی تقریباً همه.
      بدنهٔ فرم خطِ `Email: sam@…` دارد؛ آن آدرس داخلِ نقلِ‌قول می‌آمد و گاردِ
      PII ِ پایین‌دست کلِ پاسخ را رد می‌کرد (`self_guard_pii_email`). گارد درست
      عمل می‌کرد؛ ولی «هیچ پاسخی» جوابِ درستِ یک لیدِ سالم نیست. منبع پاک شد و
      گارد به‌عنوان لایهٔ آخر ماند.

    ۴ نقلِ‌قولی که مثلِ ماشین حرف می‌زد.
      `"Name: Sam Jones Email: Phone: Suburb: Carlingford Message: …"` — دقیقاً
      همان لحنی که نقلِ‌قول قرار بود از آن فرار کند.

درسِ ساختاری (ثبت‌شده در حافظه، این‌بار روی درزِ دو ماژول): **خواننده و نویسنده
را با هم بسنج، از مسیرِ تولیدی، نه با فیکسچر.**
"""
import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))

import harness  # noqa: E402
ENV = harness.setup("lead-form-notification")

sys.path.insert(0, str(_HERE.parent / "legs"))
import os                       # noqa: E402
import lead_email_intake as ie  # noqa: E402
import lead_first_reply as fr   # noqa: E402

_FORM_DOMAIN = "@example-site.test"
_CUST = "sam.jones@customer.test"


def _on():
    os.environ["OCTOPUS_WIRE_LEAD_FIRST_REPLY"] = "1"
    os.environ["OCTOPUS_LEAD_FORM_SENDERS"] = _FORM_DOMAIN


def _off():
    os.environ.pop("OCTOPUS_WIRE_LEAD_FIRST_REPLY", None)
    os.environ.pop("OCTOPUS_LEAD_FORM_SENDERS", None)


def _msg(body: str, reply_to: str = "") -> dict:
    m = {"message_id": "<form-1@site>",
         "from": "Website Form <noreply" + _FORM_DOMAIN + ">",
         "subject": "New enquiry from website",
         "body": body, "date": "2026-08-01"}
    if reply_to:
        m["reply_to"] = reply_to
    return m


_BODY = ("Name: Sam Jones\n"
         "Email: " + _CUST + "\n"
         "Phone: 0412 345 678\n"
         "Suburb: Carlingford\n"
         "Message: I need my 3 bedrooms painted before Christmas.\n"
         "The ceilings are water damaged.\n"
         "Quote me $5000.")


def _candidate(body=_BODY, reply_to=""):
    n = ie.normalize(_msg(body, reply_to))
    v = ie.classify(n)
    assert v["is_inquiry"], "اعلانِ فرم باید استعلام شناخته شود"
    assert v["channel"] == "website_form", v["channel"]
    return ie.to_candidate(n, v["channel"], ie.dedup_key(n))


# ── ۱ · تماسِ قابلِ‌تماس ─────────────────────────────────────────────────────
def t_a_contact_email_is_the_customer_not_the_notifier():
    """قلبِ ماجرا: لیدی که نمی‌شود جوابش را داد، لید نیست."""
    _on()
    try:
        c = _candidate()
        assert c["contact"]["email"] == _CUST, c["contact"]
        assert "noreply" not in c["contact"]["email"], c["contact"]
    finally:
        _off()


def t_b_reply_to_still_wins_when_the_form_sets_it():
    """`Reply-To` مکانیزمِ استانداردِ فرم‌هاست و باید مقدم بماند."""
    _on()
    try:
        c = _candidate(reply_to="Real Person <real@customer.test>")
        assert c["contact"]["email"] == "real@customer.test", c["contact"]
    finally:
        _off()


def t_c_a_non_form_email_keeps_the_envelope_sender():
    """و مسیرِ عادی نباید عوض شود: در ایمیلِ مستقیم، فرستنده **همان** مشتری است."""
    _on()
    try:
        m = {"message_id": "<direct@x>", "from": "Sam <sam@customer.test>",
             "subject": "painting quote", "body": "Can you paint my house?",
             "date": "2026-08-01"}
        n = ie.normalize(m)
        c = ie.to_candidate(n, ie.classify(n)["channel"], ie.dedup_key(n))
        assert c["contact"]["email"] == "sam@customer.test", c["contact"]
    finally:
        _off()


# ── ۲ · سلام ────────────────────────────────────────────────────────────────
def t_d_the_greeting_uses_the_customers_name():
    _on()
    try:
        assert _candidate()["contact"]["name"] == "Sam Jones"
        b = fr.compose_first_reply(_candidate()).get("body") or ""
        assert b.startswith("Hi Sam"), b[:60]
        assert "Website" not in b.splitlines()[0], b[:60]
    finally:
        _off()


def t_e_a_nameless_form_is_not_a_crash():
    """نبودِ نام باید سلامِ بی‌نام بدهد، نه استثنا و نه «Hi Website»."""
    _on()
    try:
        c = _candidate(body="Message: Please paint my hallway.\nSuburb: Epping")
        assert not c["contact"].get("name"), c["contact"]
        r = fr.compose_first_reply(c)
        assert r.get("ok"), r.get("reason")
        assert "Website" not in (r.get("body") or "").splitlines()[0]
    finally:
        _off()


# ── ۳ · پاسخ اصلاً تولید می‌شود ─────────────────────────────────────────────
def t_f_a_form_that_carries_an_email_field_still_gets_a_reply():
    """ناوردیِ اصلی: گارد باید نگهبان باشد، نه سدِّ راه.

    قبل از فیکس: `self_guard_pii_email` و **هیچ متنی** — برای هر فرمی که فیلدِ
    ایمیل دارد، یعنی عملاً همه. قابلیت برای همان مسیری که ساخته شده بود ساکت
    بود.
    """
    _on()
    try:
        r = fr.compose_first_reply(_candidate())
        assert r.get("ok"), r.get("reason")
        assert (r.get("body") or "").strip(), "بدنهٔ تهی"
    finally:
        _off()


def t_g_the_customers_email_never_appears_in_the_body():
    """و گاردِ لایهٔ آخر همچنان باید معنا داشته باشد."""
    _on()
    try:
        b = (fr.compose_first_reply(_candidate()).get("body") or "").lower()
        assert _CUST not in b, "آدرسِ مشتری نشت کرد"
        assert not re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+",
                             b.split("abn")[0]), b[:400]
    finally:
        _off()


def t_h_no_price_and_no_customer_phone_survive():
    """جملهٔ قیمت باید **کامل** بیفتد، و تلفنِ خودِ مشتری هم نباید نقل شود."""
    _on()
    try:
        b = fr.compose_first_reply(_candidate()).get("body") or ""
        head = b.split("ABN")[0]          # ABN عمداً رقم دارد و قانوناً الزامی است
        assert "5000" not in head and "$" not in head, head[:400]
        assert "0412" not in head and "345 678" not in head, head[:400]
    finally:
        _off()


# ── ۴ · لحنِ انسانی ─────────────────────────────────────────────────────────
def t_i_the_echo_quotes_the_message_not_the_form_metadata():
    """نقلِ‌قول باید حرفِ مشتری باشد، نه جدولِ فیلدهای فرم."""
    _on()
    try:
        b = fr.compose_first_reply(_candidate()).get("body") or ""
        assert "ceilings are water damaged" in b, b[:400]
        for meta in ("Suburb:", "Phone:", "Email:", "Name:"):
            assert meta not in b, f"فرادادهٔ «{meta}» در متن ماند\n{b[:400]}"
    finally:
        _off()


def t_j_a_multiline_message_is_kept_whole():
    """پیامِ چندخطی تا برچسبِ بعدی ادامه دارد — نه فقط خطِ اول."""
    _on()
    try:
        scope = _candidate()["request"]["scope_text"]
        assert "before Christmas" in scope and "water damaged" in scope, scope
        assert "Suburb" not in scope, scope
    finally:
        _off()


def t_k_a_body_with_no_message_field_falls_back_to_the_whole_body():
    """اگر فیلدِ پیام نبود، هیچ اطلاعاتی نباید گم شود."""
    _on()
    try:
        scope = _candidate(body="I want the outside of my house painted.")["request"]["scope_text"]
        assert "outside of my house" in scope, scope
    finally:
        _off()


# ── دندان ───────────────────────────────────────────────────────────────────
def t_l_teeth_the_old_envelope_order_would_fail_t_a():
    """بازسازیِ رفتارِ پیش از فیکس: ترتیبِ قدیمی آدرسِ noreply را می‌داد."""
    _on()
    try:
        n = ie.normalize(_msg(_BODY))
        old = ie._addr_of(n["reply_to"]) or ie._addr_of(n["from"]) or ie._addr_of(n["body"])
        assert old != _CUST and "noreply" in old, old
    finally:
        _off()


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_lead_form_notification: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
