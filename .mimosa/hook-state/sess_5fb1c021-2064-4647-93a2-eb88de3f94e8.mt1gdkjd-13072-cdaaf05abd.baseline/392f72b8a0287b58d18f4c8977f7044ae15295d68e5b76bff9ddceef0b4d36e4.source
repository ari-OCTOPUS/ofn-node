"""test_new_capability_cards.py — قابلیتی که مالک نمی‌بیندش، وجود ندارد.

سه بار در یک هفته در همین مخزن ماژولی کامل، تست‌شده و بی‌صداکننده تحویل شد.
`capability_registry` برای همین ساخته شده: هر ماژولی که `card()` **بی‌آرگومان**
داشته باشد خودبه‌خود در فهرستِ تلگرام می‌آید، بدونِ لمسِ `center.py`. یعنی
سطح‌دارشدن یک قرارداد است، نه یک سیم‌کشیِ دستی.

این فایل آن قرارداد را برای سه قابلیتِ ۲۰۲۶-۰۸-۰۱ قفل می‌کند، و — مهم‌تر —
قفل می‌کند که هیچ‌کدام هنگام نمایش چیزی نشت ندهند. کارتِ وضعیت جایی است که
نشتِ PII بیشترین احتمال را دارد، چون طبیعتش «همه‌چیز را نشان بده» است.
"""
import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))

import harness  # noqa: E402
ENV = harness.setup("new-capability-cards")

sys.path.insert(0, str(_HERE.parent / "legs"))
import capability_registry as cr   # noqa: E402
import dark_capabilities as dc     # noqa: E402
import lead_email_intake as ie     # noqa: E402
import lead_suppression as ls      # noqa: E402

_MODULES = {"dark_capabilities": dc, "lead_suppression": ls, "lead_email_intake": ie}

_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
# رقم‌های بلند: شمارهٔ حساب، توکن، هش. ABN و شمارهٔ تلفن جای دیگری‌اند نه این کارت‌ها.
_LONGNUM_RE = re.compile(r"\d{9,}")


def t_a_every_new_capability_has_a_card():
    for name, mod in _MODULES.items():
        assert hasattr(mod, "card"), f"{name} کارت ندارد"
        assert callable(mod.card), name


def t_b_the_card_takes_no_arguments():
    """قراردادِ کشف: فقط `card()` ِ بی‌آرگومان خودکار پیدا می‌شود.

    اگر کسی روزی پارامتری اضافه کند، ماژول بی‌صدا از فهرست می‌افتد — همان‌طور
    که `lead_card` (که عمداً آرگومان می‌گیرد) در فهرست نیست.
    """
    import inspect
    for name, mod in _MODULES.items():
        sig = inspect.signature(mod.card)
        required = [p for p in sig.parameters.values()
                    if p.default is inspect.Parameter.empty
                    and p.kind not in (p.VAR_POSITIONAL, p.VAR_KEYWORD)]
        assert not required, f"{name}.card آرگومانِ اجباری دارد: {required}"


def t_c_the_registry_actually_discovers_them():
    """گاردِ کدِ مرده — همان الگویی که این هفته سه بار تکرار شد."""
    found = cr.discover()
    blob = str(found)
    for name in _MODULES:
        assert name in blob, f"{name} در capability_registry دیده نمی‌شود"


def t_d_a_card_never_raises():
    """کارت در پروسهٔ زندهٔ مرکز رندر می‌شود. استثنا آن‌جا یعنی سکوتِ کلِ منو."""
    for name, mod in _MODULES.items():
        out = mod.card()
        assert isinstance(out, str) and out.strip(), name


def t_e_no_card_leaks_an_address_or_a_long_number():
    """کارتِ وضعیت پرخطرترین جای نشت است، چون طبیعتش «همه را نشان بده» است."""
    for name, mod in _MODULES.items():
        out = mod.card()
        assert not _EMAIL_RE.search(out), f"{name} آدرس نشت داد"
        assert not _LONGNUM_RE.search(out), f"{name} رقمِ بلند نشت داد"


def t_f_no_card_prints_a_flag_value():
    """نامِ فلگ مجاز است، مقدارش نه — و مقادیرِ `.env` هرگز.

    گاردِ نامِ محرمانه از `flag_drift` قرض گرفته می‌شود تا دو تعریفِ واگرا از
    «راز» در سیستم نداشته باشیم.
    """
    import flag_drift
    for name, mod in _MODULES.items():
        out = mod.card()
        for tok in re.findall(r"[A-Z][A-Z0-9_]{5,}", out):
            if flag_drift.is_secret_name(tok):
                assert f"{tok}=" not in out, f"{name} مقدارِ {tok} را چاپ کرد"


def t_g_a_broken_scan_degrades_to_a_message_not_a_crash():
    """اگر منبعِ داده بترکد، کارت باید بگوید «نشد»، نه اینکه منو را بکشد."""
    orig = dc.scan
    dc.scan = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom"))
    try:
        out = dc.card()
        assert isinstance(out, str) and out.strip()
        assert "RuntimeError" in out or "نشد" in out, out
    finally:
        dc.scan = orig


def t_h_the_suppression_card_says_hearing_is_never_gated():
    """ناوردیِ قانونی که باید روی خودِ کارت دیده شود.

    مالک باید از روی کارت بفهمد که شنیدنِ STOP خاموش‌شدنی **نیست** — وگرنه
    ممکن است فکر کند با خاموش‌کردنِ فلگ کلِ سازوکار خوابیده و این تصورِ غلط
    دقیقاً همان چیزی است که به نقضِ Spam Act ختم می‌شود.
    """
    out = ls.card()
    assert "STOP" in out, out
    assert "گیت‌پذیر نیست" in out or "همیشه" in out, out


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_new_capability_cards: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
