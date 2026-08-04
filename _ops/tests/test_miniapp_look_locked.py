#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_miniapp_look_locked — ظاهر قفل است: تیره، ثابت، و بی‌راهِ فرار.

    چرا این فایل هست: مالک **سه بار** گفت «هنوز سفید است» و هر سه بار سوییتِ
    موجود ۲۲/۲۲ سبز بود — چون آن سوییت خودِ باگ را pin کرده بود. یک قاعدهٔ
    ظاهری که فقط در کامنت نوشته شده، enforce نیست. این‌ها همان قاعده‌ها را
    ماشین‌خوان می‌کنند:

      ۱. هیچ شاخهٔ روشنی در CSS نمانده (نه data-theme=light، نه مدیا-کوئری).
      ۲. پالتِ پایه واقعاً تیره است — با **محاسبهٔ روشنایی**، نه تطبیقِ رشته.
      ۳. هیچ گزینشِ ظاهری نمانده: نه [data-skin]، نه کلیدِ localStorage.
      ۴. letter-spacing ِ غیرصفر هیچ‌جا نیست (خطِ فارسی پیوسته است).
      ۵. شمارِ ستون‌های نوارِ تب با شمارِ تب‌های index.html می‌خواند.
      ۶. هر tone ای که app.js می‌دهد، در CSS قاعده دارد — وگرنه «خطر» به
         رنگِ «سالم» رندر می‌شود.

    ⚠️ همهٔ assertها روی CSS/JS ِ **کامنت‌زدوده** اجرا می‌شوند. درسِ تکراریِ
    این مخزن: کدِ خوب دربارهٔ خودش حرف می‌زند، پس گرپِ متنی به توضیح می‌خورد
    نه به قاعده — و تستِ کاذب بدتر از تستِ نداشته است.

    سبکِ main-style: harness.setup اول، توابعِ t_*، harness.run، sys.exit.
"""
import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
for _p in (str(_OPS), str(_HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import harness  # noqa: E402

ENV = harness.setup("miniapp-look-locked")

MINI = harness.REAL_VAULT / "_ops" / "telegram_center" / "miniapp"
CSS_RAW = (MINI / "style.css").read_text(encoding="utf-8")
JS_RAW = (MINI / "app.js").read_text(encoding="utf-8")
HTML = (MINI / "index.html").read_text(encoding="utf-8")

#: CSS بدونِ کامنت
CSS = re.sub(r"/\*[\s\S]*?\*/", "", CSS_RAW)
#: JS بدونِ کامنتِ خطی و بلوکی. رشته‌ها دست‌نخورده می‌مانند چون خودِ
#: مقادیرِ tone داخلِ رشته‌اند و باید دیده شوند.
JS = re.sub(r"//[^\n]*", "", re.sub(r"/\*[\s\S]*?\*/", "", JS_RAW))


def _lum(hex_str: str) -> float:
    """روشناییِ ادراکی (ITU-R BT.601) — کافی برای «تیره است؟»."""
    h = hex_str.lstrip("#")
    h = "".join(c * 2 for c in h) if len(h) == 3 else h[:6]
    n = int(h, 16)
    return (0.299 * ((n >> 16) & 255) + 0.587 * ((n >> 8) & 255) + 0.114 * (n & 255)) / 255


def t_base_palette_is_actually_dark():
    """`--bg` را **حساب** می‌کنم نه grep — assert ِ رشته‌ای با اولین تنظیمِ
    سایه می‌میرد و به کامنتی که دربارهٔ رنگ حرف می‌زند هم می‌خورد."""
    m = re.search(r"--bg\s*:\s*(#[0-9a-fA-F]{3,8})", CSS)
    assert m, "‏--bg در CSS تعریف نشده"
    lum = _lum(m.group(1))
    assert lum < 0.2, f"پالتِ پایه تیره نیست: {m.group(1)} روشنایی={lum:.2f}"


def t_no_light_branch_survives_anywhere():
    """شاخهٔ خاموشِ در دسترس همان باگِ فرداست — باید حذف شود نه انتخاب‌نشده."""
    assert 'data-theme="light"' not in CSS and "data-theme='light'" not in CSS, \
        "شاخهٔ data-theme=light هنوز در CSS هست"
    assert not re.search(r"prefers-color-scheme\s*:\s*light", CSS), \
        "مدیا-کوئریِ prefers-color-scheme: light هنوز هست"


def t_telegram_theme_cannot_paint_the_palette():
    """ریشهٔ «سه بار سفید»: نگاشتِ تم به متغیرهای پالت باید خالی بماند.

    `setVar` در app.js استایلِ **inline** روی documentElement می‌نویسد که در
    cascade از `:root{}` بالاتر است؛ پس هر کلیدِ پالت در این نگاشت، پالتِ
    تیره را بی‌صدا می‌کشد.
    """
    shell = re.sub(r"/\*[\s\S]*?\*/", "",
                   (MINI / "tg_shell.js").read_text(encoding="utf-8"))
    m = re.search(r"THEME_MAP\s*=\s*\{([^}]*)\}", shell)
    assert m, "‏THEME_MAP پیدا نشد"
    body = m.group(1).strip()
    assert not body, f"‏THEME_MAP خالی نیست: {body[:120]}"


def t_no_appearance_selector_remains():
    """رأیِ مالک: «گزینش را پاک کن». نه selector، نه کلیدِ ماندگار."""
    assert "data-skin" not in CSS, "قاعدهٔ [data-skin] هنوز در CSS هست"
    assert "data-skin" not in JS, "‏app.js هنوز data-skin ست می‌کند"
    assert "octo-skin" not in JS, "کلیدِ localStorage ِ ظاهر هنوز نوشته می‌شود"


def t_zero_letter_spacing_on_every_rule():
    """خطِ فارسی پیوسته است: هر tracking — مثبت یا منفی — اتصال را می‌شکند."""
    vals = [v.strip() for v in re.findall(r"letter-spacing\s*:\s*([^;}]+)", CSS)]
    bad = [v for v in vals if v not in ("0", "normal", "0px", "0em")]
    assert not bad, f"‏letter-spacing ِ غیرصفر: {bad}"


def t_tab_grid_matches_the_tab_count():
    """‏repeat(5) با شش تب یعنی تبِ ششم به خطِ دوم می‌افتد و یک‌پنجم عرض می‌گیرد."""
    tabs = len(re.findall(r'data-tab="', HTML))
    assert tabs >= 5, f"شمارِ تب مشکوک است: {tabs}"
    m = re.search(r"\.tabs\{[^}]*grid-template-columns\s*:\s*repeat\(\s*([^,]+),", CSS)
    assert m, "‏grid-template-columns ِ نوارِ تب پیدا نشد"
    spec = m.group(1).strip()
    if spec != "auto-fit":
        assert spec.isdigit() and int(spec) == tabs, \
            f"نوارِ تب {spec} ستون دارد ولی {tabs} تب هست"


def t_every_declared_tone_has_a_css_rule():
    """هر رنگ‌واژهٔ اعلام‌شده باید در CSS قاعده داشته باشد.

    ⚠️ نسخهٔ اولِ این تست با regex دنبالِ رشته‌های ساده می‌گشت و **کور بود**:
    صداکننده‌ای که tone را با ternary می‌دهد (`c.depleted ? "bad" : …`) اصلاً
    دیده نمی‌شد، و جهشِ «یک tone ِ بی‌قاعده اضافه کن» زنده ماند. سنجهٔ
    `len(tones) >= 4` هم پاس می‌شد و اعتمادِ کاذب می‌داد.

    پس به‌جای دقیق‌ترکردنِ جارو، قاعده بسته شد: `TONES` در app.js اعلام
    می‌شود و همین‌جا خوانده. تحلیلِ ایستا دیگر لازم نیست حدس بزند.
    """
    m = re.search(r"var\s+TONES\s*=\s*\[([^\]]*)\]", JS)
    assert m, "‏TONES در app.js اعلام نشده"
    tones = re.findall(r'"(\w+)"', m.group(1))
    assert len(tones) >= 6, f"فهرستِ TONES مشکوکانه کوتاه است: {tones}"
    missing = [t for t in tones
               if not re.search(r"\.(?:ring|orb|ap)\." + t + r"\b", CSS)]
    assert not missing, f"‏tone ِ اعلام‌شده بدونِ قاعدهٔ CSS: {missing}"


def t_unknown_tone_falls_back_to_unknown_not_healthy():
    """‏tone ِ خارج از فهرست باید «نامعلوم» شود، نه سبزِ آرام‌بخش.

    این نیمهٔ دومِ قاعده است: فهرست جلوی اشتباهِ امروز را می‌گیرد، این یکی
    جلوی اشتباهِ فردا. هر سه شکلِ گرد (ring/orb/arc) باید از همان دروازه
    رد شوند وگرنه یکی‌شان درزِ باز می‌ماند.
    """
    m = re.search(r"function\s+toneOf\s*\(([^)]*)\)\s*\{([^}]*)\}", JS)
    assert m, "‏toneOf تعریف نشده"
    body = m.group(2)
    assert "TONES" in body, "‏toneOf فهرست را نمی‌خواند"
    assert '"unk"' in body, "‏toneOf به «نامعلوم» برنمی‌گردد"
    for shape in ('class="ring ', 'class="orb ', 'class="ap '):
        idx = JS.find(shape)
        assert idx >= 0, f"شکلِ {shape!r} پیدا نشد"
        seg = JS[idx:idx + 120]
        assert "toneOf(" in seg, f"شکلِ {shape!r} از دروازهٔ toneOf رد نمی‌شود: {seg[:80]}"


def t_the_sky_actually_tiles():
    """آسمانی که tile نشود، کلاً ۹ نقطه در تمامِ صفحه دارد — یعنی نامرئی."""
    sizes = re.findall(r"\.sky\s+\.s\d\{[^}]*background-size\s*:\s*([^;}]+)", CSS)
    assert len(sizes) >= 2, f"لایه‌های ستارهٔ آسمان پیدا نشدند: {sizes}"
    for s in sizes:
        assert "%" not in s, f"لایهٔ آسمان tile نمی‌شود (background-size:{s.strip()})"


if __name__ == "__main__":
    CHECKS = [(n, f) for n, f in sorted(globals().items())
              if n.startswith("t_") and callable(f)]
    failed = harness.run(CHECKS)
    print(f"\n{'✅' if not failed else '❌'} test_miniapp_look_locked: "
          f"{len(CHECKS) - failed}/{len(CHECKS)} passed")
    sys.exit(1 if failed else 0)
