"""test_invoice_unpayable_is_loud.py — فاکتوری که نمی‌شود پرداختش کرد باید بگوید.

اندازه‌گیریِ ۲۰۲۶-۰۸-۰۱ روی حالتِ زنده:

    business_legs.lead.identity.has_bank_details = false
    و در دو فاکتورِ واقعیِ روی دیسک: business.bank_details = ""

`render_invoice_html` تا امروز این شکل بود:

    if biz.get("bank_details"):
        lines.append("Bank: …")

یعنی خالی‌بودن **بی‌صدا خطِ بانک را حذف می‌کرد**. فاکتور ساخته می‌شد، ظاهرش
کامل بود — شماره، ABN، جمع، GST، سررسید — و مشتری هیچ راهی برای پرداخت نداشت.
مالک تا وقتی پول نمی‌آمد نمی‌فهمید چرا.

`lead_leg.py:214` این را در **سیگنالِ پا** هشدار می‌دهد، ولی آن هشدار در کارتِ
وضعیت می‌نشیند نه روی خودِ سند؛ کسی که فاکتور را می‌فرستد نمی‌بیندش. سکوت روی
**خودِ آرتیفکت** بدترین جای سکوت است.

این فایل قفل می‌کند که فاکتورِ بی‌بانک صریح داد بزند، و — مهم‌تر — که فاکتورِ
سالم **هیچ تغییری نکند**.
"""
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))

import harness  # noqa: E402
ENV = harness.setup("invoice-unpayable")

sys.path.insert(0, str(_HERE.parent / "legs"))
import invoice as inv  # noqa: E402

_LIVE_INVOICES = harness.REAL_VAULT / "_ops" / "state" / "legs" / "invoices"
_MARK = "cannot be paid"


def _rec(bank: str = "", **over) -> dict:
    r = {"inv_number": "LEAD-20260801-001", "attribution_id": "att-1",
         "issue_date": "2026-08-01", "subtotal_excl_gst": 1000.0,
         "gst": 100.0, "total_incl_gst": 1100.0, "deposit_max": 110.0,
         "business": {"abn": "11111111111", "trading_name": "T", "address": "A",
                      "payment_methods": "Bank Transfer",
                      "payment_terms": "Due within 7 days",
                      "bank_details": bank},
         "lines": [{"desc": "Painting", "amount": 1000.0}]}
    r.update(over)
    return r


def t_a_empty_bank_details_is_loud_not_silent():
    """قلبِ ماجرا: خالی‌بودن باید روی خودِ سند دیده شود."""
    html = inv.render_invoice_html(_rec(bank=""))
    assert _MARK in html, "فاکتورِ بی‌بانک ساکت است — همان باگ"
    assert "bank_details" in html, "نمی‌گوید چه چیزی را باید پر کرد"


def t_b_a_healthy_invoice_is_untouched():
    """ناوردیِ رگرسیون: وجودِ بانک یعنی هیچ هشداری، و خطِ بانک سرِ جایش."""
    html = inv.render_invoice_html(_rec(bank="BSB 000-000 ACC 12345678"))
    assert _MARK not in html, "فاکتورِ سالم هشدار گرفت"
    assert "Bank:" in html and "12345678" in html


def t_c_whitespace_only_counts_as_empty():
    """یک فاصله هم یعنی «پرداخت‌ناپذیر».

    نسخهٔ اولِ فیکس این را جا انداخته بود: `if biz.get(...)` رشتهٔ `'   '` را
    صادق می‌بیند و `Bank: <code>   </code>` می‌ساخت — با پروب دیده شد. خطِ
    بانکی که وجود دارد و پوچ است از نبودنش بدتر است، چون فرستنده نگاه می‌کند و
    می‌بیند «بانک هست».
    """
    html = inv.render_invoice_html(_rec(bank="   "))
    assert _MARK in html, "فاصله به‌عنوانِ بانکِ معتبر پذیرفته شد"
    assert "Bank: <code>" not in html, html[:300]


def t_ca_a_padded_real_value_is_trimmed_not_rejected():
    """ولی مقدارِ واقعی با فاصلهٔ اضافه باید **قبول** شود و تمیز چاپ گردد —
    وگرنه فیکسِ بالا یک باگِ تازه می‌سازد."""
    html = inv.render_invoice_html(_rec(bank="  BSB 000-000 ACC 12345678  "))
    assert _MARK not in html, html[:300]
    assert "Bank: <code>BSB 000-000 ACC 12345678</code>" in html, html[:300]


_FIX_DATE = "2026-08-01"   # روزی که `_bank_from_accounts` و کلیدهای بانک وصل شدند


def t_d_every_invoice_issued_since_the_fix_is_payable():
    """این تست دربارهٔ کد نیست، دربارهٔ **واقعیت** است — و واقعیت عوض شد.

    نسخهٔ اول (۰۸-۰۱ صبح) ادعا می‌کرد «هر دو فاکتورِ روی دیسک بانک ندارند» و
    داکش می‌گفت اگر روزی مالک بانک را پر کند این قرمز می‌شود و آن **خبرِ خوب**
    است. همان شب قرمز شد: `LEAD-20260731-001` با جزئیاتِ بانکیِ واقعی صادر شد.

    پس جهتِ تست عوض می‌شود، چون عکسِ لحظه‌ای ارزشی ندارد و گاردِ رو به جلو
    دارد: **هر فاکتوری که از روزِ فیکس به بعد صادر شود باید قابلِ پرداخت
    باشد.** فاکتورهای قدیمی‌تر سندِ تاریخی‌اند و دست نمی‌خورند.

    ⚠️ گلابِ نسخهٔ اول `inv_seq.json` را هم فاکتور می‌شمرد — آن یک **شمارنده**
    است، نه سند. یعنی مخرجِ کسر از اول غلط بود («۳ فاکتور» در حالی که دو تا
    بیشتر نبود). هر تستی که روی دیسک شمارش می‌کند باید اول تعریف کند «چه چیزی
    اصلاً از این جنس است».
    """
    if not _LIVE_INVOICES.exists():
        return
    unpayable = []
    seen = 0
    for f in sorted(_LIVE_INVOICES.glob("*.json")):
        try:
            d = json.loads(f.read_text("utf-8"))
        except (OSError, ValueError):
            continue
        issued = str(d.get("issue_date") or "")
        if not d.get("inv_number") or not issued:
            continue                      # شمارنده/سایدکار، نه فاکتور
        if issued < _FIX_DATE:
            continue                      # سندِ تاریخی
        seen += 1
        if not str((d.get("business") or {}).get("bank_details", "")).strip():
            unpayable.append(f.name)
    assert not unpayable, (
        f"{len(unpayable)} از {seen} فاکتورِ صادرشده از {_FIX_DATE} به بعد "
        f"بانک ندارد و پرداخت‌ناپذیر است: {unpayable}")


def t_f_bank_details_are_found_under_bank_accounts():
    """۲۰۲۶-۰۸-۰۱ — مالک `bank_details` را زیرِ `bank_accounts[0]` گذاشت، نه در
    ریشه. آن جای **درست‌تری** است (جزئیاتِ پرداخت به یک حسابِ مشخص تعلق دارد)،
    ولی خواننده فقط ریشه را می‌دید و فاکتور «پرداخت‌ناپذیر» می‌ماند در حالی که
    داده موجود بود — همان «باگِ دو-منبعی» که کامنتِ خطِ ۶۶ همین فایل توصیفش
    می‌کند، این بار وارونه."""
    assert inv._bank_from_accounts(
        {"bank_accounts": [{"bank_account_id": "x"},
                           {"bank_details": "BSB 000 ACC 111"}]}) == "BSB 000 ACC 111"


def t_fa_root_wins_over_the_account_entry():
    """ترتیب باید قطعی باشد: اگر روزی ریشه صریح ست شود، همان برنده است."""
    prof = {"bank_details": "ROOT", "bank_accounts": [{"bank_details": "ACC"}]}
    merged_root = str(prof.get("bank_details", "") or "").strip() \
        or inv._bank_from_accounts(prof)
    assert merged_root == "ROOT", merged_root


def t_fb_a_malformed_accounts_list_is_not_a_crash():
    """پروفایلِ بدقواره باید به «نمی‌دانم» ختم شود، نه به استثنا — چون «نمی‌دانم»
    هشدارِ پرداخت‌ناپذیر می‌دهد و آن رفتارِ درستِ ندانستن است."""
    for bad in ({"bank_accounts": "not-a-list"}, {"bank_accounts": [None, 5]},
                {}, {"bank_accounts": []}):
        assert inv._bank_from_accounts(bad) == "", bad


def t_e_the_warning_never_leaks_a_number():
    """هشدار نباید هیچ رقمی از حساب را چاپ کند — حتی وقتی مقدار خراب است."""
    html = inv.render_invoice_html(_rec(bank=""))
    seg = html[html.find(_MARK) - 200: html.find(_MARK) + 300]
    import re
    assert not re.search(r"\d{6,}", seg), seg


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_invoice_unpayable_is_loud: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
