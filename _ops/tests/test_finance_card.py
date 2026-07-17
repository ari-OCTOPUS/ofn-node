"""test_finance_card.py — 2026-07-16: تبِ 💰 دارایی‌ها/حساب (ASSET-OVERSIGHT + دفترِ شخصی).
تبِ فقط‌خواندنیِ جدیدِ کابین که دو ماژولِ موجود را رو می‌کند:
  • asset_map.asset_map_status() — نقشهٔ نظارتِ دارایی (سیگنالِ امن + پیشنهادِ advisory).
  • personal_ledger.personal_status() — دفترِ شخصی/مشترک؛ فقط ترازِ تجمیعی + رشتهٔ تسویه.
گارانتی‌ها: (۱) present → aggregate رندر می‌شود؛ (۲) absent/off → «خاموش/خالی»ِ صادق؛
(۳) هرگز تراکنشِ منفرد / شماره‌حساب / عددِ ساختگی؛ (۴) صفر مسیرِ mutation (بدونِ دکمهٔ act)."""
import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))

import harness
ENV = harness.setup("finance_card")

from approval_channel import TelegramApprovalChannel  # noqa: E402


def _chan():
    return TelegramApprovalChannel()


# ── فیکسچرها: شکلِ خروجیِ واقعیِ دو ماژول + دانه‌های leakِ عمدی که رندر باید نادیده بگیرد ──
ASSET_FIXTURE = {
    "assets": [
        # کلیدهای whitelist (leg/category/live/age_days/signal) + دو کلیدِ leakِ عمدی
        # (amount_aud/note) که رندرِ درست هرگز نباید echo کند:
        {"leg": "crypto", "category": "digital-assets", "live": True,
         "age_days": 2.0, "signal": "positions=3 mkt=live",
         "amount_aud": 987654.32, "note": "F:/secret/wallet/path"},
        {"leg": "accounting", "category": "financial-books", "live": False,
         "age_days": 45.0, "signal": "workbooks=2"},
    ],
    "categories": 2, "stale_count": 1, "unavailable": [],
    "proposals": ["accounting داده ≈45 روز کهنه → منبع را refresh کن (پیشنهاد، نه اجرا)."],
    "propose_only": True, "as_of": "2026-07-16T10:00:00",
}

PERSONAL_FIXTURE = {
    "leg": "personal-ledger", "live": True, "signal": "entries=12",
    "balance": {
        "per_party": {
            "armin": {"income": 8000.0, "expense": 4800.0, "asset": 156000.0,
                      "liability": 4000.0, "cashflow": 3200.0, "net_worth": 152000.0},
            "abbas": {"cashflow": 900.0, "net_worth": 41000.0},
        },
        "joint_settlement": {"net_owed_to_armin": 425.5, "currency": "AUD"},
        "entity_ato": {
            "income_total": 8000.0, "expense_total": 5500.0,
            "net_before_tax": 2500.0, "gst_total": 250.0,
            # تفکیکِ ریزِ per-category — عددِ دانه‌ریزی که تبِ «فقط تجمیعی» نباید رو کند:
            "by_category": {"expense": {"SECRET_TXN_CAT": 66677.88}},
        },
        "counts": {"party": 8, "joint": 4}, "currency": "AUD",
        # لیستِ تراکنشِ خام + شماره‌حساب — دانهٔ leak که هرگز نباید رندر شود:
        "entries": [{"desc": "RAW_TXN_SENTINEL payment to Acct #12345678",
                     "amount": 111222.33}],
    },
    "proposal": ("پیشنهاد (تأییدِ خودت لازم): عباس حدودِ 425.50 AUD به تو (آرمین) بدهکار است. "
                 "وقتی تسویه شد دستی ثبت کن — اختاپوس پول جابه‌جا نمی‌کند."),
    "note": "۳ دفتر (آرمین/عباس/واحدِ ATO-NSW) + تسویهٔ مشترک.",
}

# دانه‌های leak که در هیچ حالتی نباید در متن دیده شوند (تراکنش/شماره‌حساب/فیلدِ غیرِ whitelist)
_LEAK_SENTINELS = ("987654", "wallet", "SECRET_TXN_CAT", "66677",
                   "RAW_TXN_SENTINEL", "12345678", "111222")


def t_a_finance_registered_and_read_only():
    """تب در TAB_PAGES ثبت شده و کیبوردش صفر مسیرِ mutation دارد (بدونِ act:/app:/card:)."""
    assert "finance" in TelegramApprovalChannel.TAB_PAGES
    kb = _chan()._tab_keyboard("finance")["inline_keyboard"]
    cds = [b["callback_data"] for row in kb for b in row]
    assert "menu:main" in cds
    for cd in cds:
        assert not cd.startswith("act:"), cd     # هیچ دکمهٔ اکشن/توگل
        assert not cd.startswith("app:"), cd     # هیچ کارتِ تأییدِ پول
        assert not cd.startswith("card:"), cd    # صرفاً نمایش، بدونِ زیرکارتِ mutation


def t_b_command_and_menu_route_to_finance():
    """/finance و menu:finance هر دو یک dict با text+reply_markup می‌دهند (بدونِ crash).
    از 2026-07-18: /finance نسخهٔ فارسیِ سادهٔ «وضعِ من» می‌دهد (UX-SPEC §۳.۱)."""
    ch = _chan()
    for out in (ch.handle_command("/finance"), ch.dispatch_callback("menu:finance")):
        assert isinstance(out, dict), out
        assert "text" in out and "reply_markup" in out
        assert "وضعِ من" in out["text"]            # header فارسیِ ساده (نه «دارایی‌ها/حساب»)


def t_c_present_renders_asset_and_personal_aggregates():
    """با دادهٔ حاضر (نسخهٔ EXPERT): سیگنالِ asset_map + ترازِ تجمیعیِ دفتر + رشتهٔ تسویه.
    از 2026-07-18 این بخش‌ها در _finance_text_expert هستند (نسخهٔ ساده فقط شبکه را نشان می‌دهد)."""
    ch = _chan()
    ch._finance_data = lambda: (ASSET_FIXTURE, PERSONAL_FIXTURE)  # seamِ تزریق
    txt = ch._finance_text_expert()
    # asset_map: هر پا با category + signal
    assert "نقشهٔ دارایی" in txt
    assert "crypto" in txt and "digital-assets" in txt and "positions=3" in txt
    assert "accounting" in txt and "financial-books" in txt
    assert "پیشنهاد" in txt        # رشتهٔ advisory
    # personal: ترازِ تجمیعیِ هر طرف + رول‌آپِ ATO + تسویه
    assert "آرمین" in txt and "152000" in txt      # net_worthِ تجمیعی (نه تراکنش)
    assert "عباس" in txt and "41000" in txt
    assert "ATO" in txt and "2500" in txt          # net_before_taxِ تجمیعی
    assert "تسویهٔ مشترک" in txt and "425.50" in txt  # رشتهٔ پیشنهادِ تسویه (خالصِ مجاز)


def t_d_present_never_leaks_raw_txn_or_account_number():
    """هیچ تراکنشِ منفرد/شماره‌حساب/فیلدِ غیرِ whitelist (amount_aud/by_category/entries) — نسخهٔ EXPERT."""
    ch = _chan()
    ch._finance_data = lambda: (ASSET_FIXTURE, PERSONAL_FIXTURE)
    txt = ch._finance_text_expert()
    for s in _LEAK_SENTINELS:
        assert s not in txt, f"leak: {s!r} در متنِ کارت دیده شد"


def t_e_absent_renders_honest_off_and_no_fake_number():
    """منبعِ غایب (None, None) → «خاموش/خالی»ِ صادق؛ صفر عددِ ساختگیِ پول — نسخهٔ EXPERT."""
    ch = _chan()
    ch._finance_data = lambda: (None, None)
    txt = ch._finance_text_expert()
    assert "خاموش/خالی" in txt or "خاموش" in txt
    assert "asset_map در دسترس نیست" in txt
    assert "خالی" in txt                       # دفترِ خالی
    # هیچ ترازِ تجمیعیِ ساختگی رندر نشده
    assert "ثروتِ خالص" not in txt and "خالصِ پیش" not in txt and "تسویهٔ مشترک" not in txt
    # هیچ عددِ پول‌مانند (اعشار دو‌رقمی) یا عددِ درشت (شماره‌حساب/مبلغ) در حالتِ خاموش
    assert not re.search(r"\d+\.\d{2}", txt), f"عددِ اعشاریِ ساختگی: {txt!r}"
    assert not re.search(r"\d{4,}", txt), f"عددِ درشتِ ساختگی: {txt!r}"
    for s in _LEAK_SENTINELS:
        assert s not in txt


def t_f_off_ledger_present_asset_partial():
    """asset حاضر ولی دفتر خاموش (live=False با note) → asset رندر، دفتر «خالی»ِ صادق — نسخهٔ EXPERT."""
    ch = _chan()
    off_personal = {"leg": "personal-ledger", "live": False, "signal": "ledger نیست",
                    "note": "ledger.json نیست — از قالب کپی و دونه‌دونه پر کن."}
    ch._finance_data = lambda: (ASSET_FIXTURE, off_personal)
    txt = ch._finance_text_expert()
    assert "crypto" in txt                      # asset رندر شد
    assert "خالی" in txt                        # دفترِ خاموش، صادق
    assert "ثروتِ خالص" not in txt              # بدونِ ترازِ ساختگی
    for s in _LEAK_SENTINELS:
        assert s not in txt


def t_g_real_path_never_crashes_and_ledger_off():
    """مسیرِ واقعیِ _render_tab(finance) (بدونِ تزریق) در mini-vault: بدونِ crash؛
    از 2026-07-18 header «وضعِ من» (نه «دارایی»)؛ network_summary خاموش → «داده‌ای وصل نیست»."""
    r = _chan()._render_tab("finance")
    assert isinstance(r, dict) and "text" in r and "reply_markup" in r
    txt = r["text"]
    assert "وضعِ من" in txt                     # header فارسیِ ساده (نه «دارایی»)
    # هیچ شماره‌حساب‌مانند (رشتهٔ ۸+ رقمی) از مسیرِ واقعی نشت نکند
    assert not re.search(r"\d{8,}", txt), f"شماره‌حساب‌مانند: {txt!r}"


# ── بخشِ ۳: شبکهٔ حسابدار (accountant.network_summary_card) — تجمیعِ PII-امن ──
NET_FIXTURE = {
    "live": True, "unique": 576, "as_of": "2026-07-16", "reconciled": True,
    "armin_net": "-12603.40", "abbas_net": "5394.28",
    "assoc_total": "-53422.93", "client_revenue": "42074.00",
    "wage_total": "19250.00", "wage_days": 77, "wage_n": 26,
    "counts": {"confirmed": 21, "auto": 27, "needs_review": 528},
}
_NET_NAME_LEAKS = ("sume", "asadi", "maliheh", "behzad", "carmy",
                   "carbon", "starr", "lynne", "harper")


def t_h_network_section_renders_aggregate_no_names():
    """بخشِ شبکه (نسخهٔ سادهٔ «وضعِ من»): مابه‌التفاوتِ آرمین/عباس + جمع‌های بی‌نام.
    از 2026-07-18 (UX-SPEC §۳.۱): «خالصِ بانکی» → «مابه‌التفاوت»، «سنتِ سازگار» → «عدد‌ها می‌خونن»."""
    ch = _chan()
    ch._finance_data = lambda: (None, None)          # بخش‌های expert خاموش
    ch._network_summary = lambda: NET_FIXTURE
    txt = ch._finance_text()
    assert "وضعِ من" in txt                            # header فارسیِ ساده
    # اعدادِ تجمیعی همچنان نمایش داده می‌شوند (RD-001: مبلغِ دقیق مجاز؛ ~ با گردکردنِ نمایشی)
    # با کامای هزارگان (فرمتِ :,.0f): ~$5,394 و ~$42,074
    assert "5,394" in txt and "42,074" in txt
    assert "آرمین" in txt and "عباس" in txt
    assert "مابه‌التفاوت" in txt                        # جایگزینِ «خالصِ بانکی»
    assert "عدد‌ها می‌خونن" in txt                      # جایگزینِ «سنتِ سازگار»
    # هیچ‌کدام از اصطلاحاتِ ممنوع (UX-SPEC §۲) نباید باشد
    assert "خالصِ بانکی" not in txt
    assert "سنتِ سازگار" not in txt
    assert "Dr" not in txt and "Cr" not in txt
    assert "ATO" not in txt
    # هرگز نامِ مشتری/طرف‌حسابِ شخصِ ثالث
    for name in _NET_NAME_LEAKS:
        assert name not in txt, f"leak: {name!r}"
    low = txt.lower()
    for name in _NET_NAME_LEAKS:
        assert name not in low, f"نشتِ نامِ شخصِ ثالث: {name!r}"


def t_i_network_off_is_honest():
    """منبعِ خاموش → «داده‌ای وصل نیست»ِ صادق، صفر عددِ ساختگی (UX-SPEC §۳.۱).
    از 2026-07-18: header «وضعِ من»، پیامِ صادقانه به‌جای «شبکهٔ حسابِ خاموش»."""
    ch = _chan()
    ch._finance_data = lambda: (None, None)
    ch._network_summary = lambda: {"live": False, "note": "txn-store خالی است."}
    txt = ch._finance_text()
    assert "وضعِ من" in txt                      # header فارسیِ ساده
    assert "داده" in txt or "چیزی" in txt        # پیامِ صادقانهٔ «داده‌ای وصل نیست»


if __name__ == "__main__":
    for f in (t_a_finance_registered_and_read_only,
              t_b_command_and_menu_route_to_finance,
              t_c_present_renders_asset_and_personal_aggregates,
              t_d_present_never_leaks_raw_txn_or_account_number,
              t_e_absent_renders_honest_off_and_no_fake_number,
              t_f_off_ledger_present_asset_partial,
              t_g_real_path_never_crashes_and_ledger_off,
              t_h_network_section_renders_aggregate_no_names,
              t_i_network_off_is_honest):
        f()
        print("ok", f.__name__)
    print("PASS test_finance_card")
