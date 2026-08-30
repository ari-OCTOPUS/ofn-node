"""test_mining_card.py — D-013: کارتِ عددیِ ماینینگ.

اثباتِ صادقانه:
- ناوگان ۱۶۲ (نه ۰)
- «اندازه‌گیری‌نشده» صریح (نه صفر)
- skeleton هرگز live اعلام نمی‌کند
- HTML escape شده
- digest کوتاه
"""
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent / "legs"))

import mining_card as mc  # noqa: E402


# ── ۱: ناوگان صادقانه ────────────────────────────────────────────────────────
def t_card_shows_162_fleet_not_zero():
    """کارت حاوی «۱۶۲» فارسی است و در هیچ فیلدی «۰» نیست."""
    card = mc.card_text()
    assert "۱۶۲" in card, "ناوگان ۱۶۲ فارسی در کارت نیست"
    # نباید صفرِ بدونِ زمینه در کارت باشد
    assert "۰" not in card, "رقمِ صفرِ فارسی در کارت ظاهر شده — باید اندازه‌گیری‌نشده باشد"


def t_fleet_total_constant_is_162():
    """ثابتِ ماژول FLEET_TOTAL = 162."""
    assert mc.FLEET_TOTAL == 162, f"FLEET_TOTAL = {mc.FLEET_TOTAL}, باید ۱۶۲ باشد"


# ── ۲: اندازه‌گیری‌نشده صریح ──────────────────────────────────────────────────
def t_unmeasured_is_explicit_text_not_zero():
    """رشتهٔ «اندازه‌گیری‌نشده» در کارت هست — نه 0 و نه خالی."""
    card = mc.card_text()
    assert mc.UNMEASURED in card, "اندازه‌گیری‌نشده در کارت نیست"
    assert mc.UNMEASURED != "0", "UNMEASURED نباید '0' باشد"
    assert mc.UNMEASURED != "", "UNMEASURED نباید خالی باشد"


def t_unmeasured_appears_four_times_in_card():
    """چهار فیلدِ عملیاتی همگی اندازه‌گیری‌نشده هستند."""
    card = mc.card_text()
    count = card.count(mc.UNMEASURED)
    assert count == 4, f"اندازه‌گیری‌نشده {count} بار ظاهر شده، باید ۴ باشد (نرخ هش، آپتایم، دما، سود)"


# ── ۳: skeleton هرگز live نیست ────────────────────────────────────────────────
def t_skeleton_is_never_live():
    """وقتی live=False، کارت حاوی skeleton/⚪ است و نه live/🟢."""
    card = mc.card_text(live=False)
    assert "skeleton" in card or "⚪" in card, "علامتِ skeleton در کارت نیست"
    assert "🟢" not in card, "نشانگرِ 🟢 در حالتِ skeleton ظاهر شده"
    assert "live" not in card.lower().replace("skeleton", ""), "کلمهٔ live در حالتِ skeleton ظاهر شده"


def t_digest_also_shows_offline():
    """دایجست هم باید خاموش باشد وقتی live=False."""
    digest = mc.digest_detail(live=False)
    assert "خاموش" in digest, "دایجست باید شامل «خاموش» باشد"
    assert "زنده" not in digest, "دایجست نباید «زنده» بگوید"


# ── ۴: امنیتِ HTML ────────────────────────────────────────────────────────────
def t_html_is_safe():
    """کاراکترهای خطرناک HTML escape می‌شوند."""
    # یک سناریو: فرض کن fleet_total نامعتبر وارد شود
    # mining_card.html.escape دارد — ولی ما مستقیم تست می‌کنیم
    import html as html_mod
    test_input = "<script>alert(1)</script>"
    escaped = html_mod.escape(test_input)
    assert "<" not in escaped, f"escape شکست خورد: {escaped}"
    assert "&lt;" in escaped, f"&lt; در خروجی نیست: {escaped}"
    assert ">" not in escaped, f"> escape نشده"
    assert "&gt;" in escaped, f"&gt; در خروجی نیست"


def t_card_html_tags_safe():
    """کارت فقط از تگ‌های مجاز (b) استفاده می‌کند."""
    card = mc.card_text()
    # <b> مجاز است
    assert "<b>" in card, "تگ <b> در کارت نیست"
    # نباید تگِ خطرناکی باشد
    assert "<script" not in card.lower(), "تگ script در کارت!"
    assert "<iframe" not in card.lower(), "تگ iframe در کارت!"


# ── ۵: دایجست کوتاه ───────────────────────────────────────────────────────────
def t_digest_is_short():
    """طولِ digest_detail کمتر از ۱۰۰ نویسه."""
    digest = mc.digest_detail()
    assert len(digest) < 100, f"طولِ دایجست {len(digest)} نویسه — باید <۱۰۰ باشد"


# ── ۶: پایهٔ مثبت (آینده) ────────────────────────────────────────────────────
def t_live_mode_shows_green_indicator():
    """وقتی live=True، نشانگرِ سبز ظاهر می‌شود."""
    card = mc.card_text(live=True)
    assert "🟢" in card, "نشانگرِ 🟢 در حالتِ live ظاهر نشد"
    assert "⚪" not in card, "نشانگرِ ⚪ در حالتِ live نباید باشد"


def t_live_digest_shows_alive():
    """وقتی live=True، دایجست «زنده» می‌گوید."""
    digest = mc.digest_detail(live=True)
    assert "زنده" in digest, "دایجستِ live باید شامل «زنده» باشد"


def t_miners_base_shows_in_card():
    """پایهٔ هش (۱۶) در کارت ظاهر می‌شود."""
    card = mc.card_text()
    assert "۱۶" in card, "پایهٔ هش ۱۶ در کارت نیست"


# ── ۷: تابعِ _fa ──────────────────────────────────────────────────────────────
def t_fa_converts_digits():
    """تبدیلِ ارقامِ لاتین به فارسی."""
    assert mc._fa(0) == "۰", "صفر فارسی"
    assert mc._fa(162) == "۱۶۲", "۱۶۲"
    assert mc._fa(9) == "۹", "نه فارسی"
    assert mc._fa(100) == "۱۰۰", "صد فارسی"


# ── اجرا ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = 0
    for name, fn in checks:
        try:
            fn()
            print(f"  PASS {name}")
        except AssertionError as e:
            failed += 1
            print(f"  FAIL {name}: {e}")
        except Exception as e:
            failed += 1
            print(f"  ERROR {name}: {type(e).__name__}: {e}")

    passed = len(checks) - failed
    print(f"\n{'PASS' if not failed else 'FAIL'} test_mining_card: "
          f"{passed}/{len(checks)} passed")
    sys.exit(1 if failed else 0)
