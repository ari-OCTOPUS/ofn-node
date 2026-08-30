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


def t_every_allowlisted_action_has_a_ui_caller():
    """هر اقدامِ مجاز باید از UI قابلِ صدا زدن باشد.

    ⚠️ تا امروز `lead.add_note` و `value.record_event` **صفر صداکننده** داشتند:
    در رجیستری بودند، تست داشتند، و از دسترسِ مالک بیرون. الگویی که این مخزن
    بارها خورده — «قابلیت هست، صداکننده نیست». فهرست از خودِ موتور خوانده
    می‌شود، پس اقدامِ هفتمی که فردا اضافه شود هم بی‌UI نمی‌ماند.
    """
    src = (_OPS / "agi2027_control" / "ops_actions.py").read_text(encoding="utf-8")
    m = re.search(r"ALLOWED_ACTIONS\s*=\s*\{([^}]*)\}", src)
    assert m, "‏ALLOWED_ACTIONS پیدا نشد"
    actions = re.findall(r'"([a-z_]+\.[a-z_]+)"', m.group(1))
    assert len(actions) >= 5, f"فهرستِ اقدام‌ها مشکوکانه کوتاه است: {actions}"
    # ۲۰۲۶-۰۸-۰۹: `diagnostics.noop` از جنسِ لید/کار/ارزش نیست — اقدامِ
    # مالک‌محور نیست، فقط پروبِ سلامتِ مسیرِ نوشتنِ soak_gateway.py است
    # (بدونِ اثر روی جدول‌های واقعی). ساختنِ دکمه برایش دقیقاً همان
    # چیزی می‌شد که این تست جلویش را می‌گیرد در جهتِ عکس: قابلیتی که هیچ
    # مالکی نباید ببیندش، توی UI ظاهر شود.
    NO_UI_ACTIONS = {"diagnostics.noop"}
    missing = [a for a in actions if a not in NO_UI_ACTIONS and ('"%s"' % a) not in JS]
    assert not missing, f"اقدامِ بی‌صداکننده در UI: {missing}"


def t_the_write_path_never_reports_optimistically():
    """رسید باید وضعِ **واقعیِ** برگشتی را بگوید، نه «✅ شد».

    موتور شش وضعِ متفاوت برمی‌گرداند و DUPLICATE یعنی «قبلاً همین ثبت شده»
    نه «انجام شد». اگر همه یک شکل نشان داده شوند، همان کارتِ رسیدِ جعلی
    ساخته می‌شود که مالک را یک بار گمراه کرد.

    ⚠️ نسخهٔ اولِ این assert دو جهش را زنده گذاشت و هر دو ضعفِ خودش بود:
    `st in body` با `XDUPLICATE` هم پاس می‌شد (تلهٔ زیررشته‌ای — همان که این
    مخزن بارها خورده)، و `'"bad"' in body` با عوض‌کردنِ لحنِ BLOCKED هم پاس
    می‌ماند چون DENIED هنوز "bad" بود. حالا نگاشت واقعاً parse می‌شود و
    ادعا **معنایی** است نه متنی.
    """
    m = re.search(r"var\s+ACT_TONE\s*=\s*\{([^}]*)\}", JS)
    assert m, "‏ACT_TONE پیدا نشد"
    pairs = dict(re.findall(r'(\w+)\s*:\s*"(\w+)"', m.group(1)))
    for st in ("APPLIED", "DUPLICATE", "BLOCKED", "DENIED", "ERROR"):
        assert st in pairs, f"وضعِ {st} در رسید نگاشت ندارد (کلیدها: {sorted(pairs)})"
    # ادعای معناییِ باربر: «ثبت شد» و «قبلاً بود» و «رد شد» باید سه چیزِ
    # متفاوت دیده شوند. اگر دوتایشان یکی شود، رسید دیگر تفکیک نمی‌کند.
    assert pairs["DUPLICATE"] != pairs["APPLIED"], (
        f"‏DUPLICATE مثلِ APPLIED رندر می‌شود ({pairs['APPLIED']}) — "
        "«شد» و «قبلاً بود» یکی شدند")
    for st in ("BLOCKED", "DENIED", "ERROR"):
        assert pairs[st] != pairs["APPLIED"], (
            f"وضعِ {st} با لحنِ موفقیت ({pairs['APPLIED']}) رندر می‌شود")


def t_every_read_endpoint_has_a_ui_consumer():
    """هر مسیرِ خواندنیِ allowlist‌شده باید یک مصرف‌کننده در UI داشته باشد.

    ⚠️ `/api/lifecycle` ساخته و تست‌شده بود (۱۶ ادعا) و **صفر مصرف‌کننده**
    داشت. نتیجه: صفِ تأیید به مالک «۰» نشان می‌داد در حالی که ۲۷ کارت راکد
    بود. همان الگویی که این مخزن بارها خورده — قابلیت هست، صداکننده نیست.

    فهرست از خودِ gateway خوانده می‌شود، پس مسیرِ بعدی هم نمی‌تواند بی‌مصرف
    بماند. مسیرهای proxy (`/api/pf/*`) این‌جا نیستند چون در allowlist نیستند؛
    آن‌ها را صداکننده‌های renderPF پوشش می‌دهند.
    """
    # 2026-08-16 (R9 debt-sweep): مسیرهای اعلام‌شده به‌عنوانِ API-only — پشتِ
    # owner-auth فقط-خواندنی، برای audit/curl/تست؛ عمداً تبِ UI ندارند.
    # هر افزودنی به این فهرست باید اینجا دلیلش ثبت شود (الگوی «مصرف‌کننده یا
    # مستند»؛ مگاپرامپت R9). حذف‌شان از READ_API_PATHS ممنوع (حذف ممنوع).
    API_ONLY_READ_PATHS = {
        "/api/epistemic",           # پنلِ C6/C7؛ مصرف‌کنندهٔ test_epistemic_c6c7 + audit
        "/api/octopus/receipts",    # زنجیرهٔ رسیدهای ارگانیسم — سطحِ audit (curl)
        "/api/octopus/runs",        # تاریخچهٔ اجراها — سطحِ audit (curl)
    }
    gw = (_OPS / "telegram_center" / "miniapp_gateway.py").read_text(encoding="utf-8")
    m = re.search(r"READ_API_PATHS\s*=\s*\{(.*?)\}", gw, re.S)
    assert m, "‏READ_API_PATHS پیدا نشد"
    paths = sorted(set(re.findall(r'"(/api/[a-z/\-]+)"', m.group(1))))
    assert len(paths) >= 8, f"فهرستِ مسیرها مشکوکانه کوتاه است: {paths}"
    orphan = [p for p in paths
              if ('api("%s")' % p) not in JS and p not in API_ONLY_READ_PATHS]
    assert not orphan, f"مسیرِ خواندنی بدونِ مصرف‌کننده در UI: {orphan}"


def t_toast_trusts_preescaped_html_not_conditional_escape():
    """ممیزیِ وب‌اپ ۲۰۲۶-۰۸-۰۷ (XSS، فیکس‌شده): `toast()` قبلاً بسته به
    فارسی‌بودنِ msg یا esc می‌کرد یا خام می‌گذاشت — یعنی هر پیامِ فارسی
    (تقریباً همه‌شان) بدونِ escape مستقیم به innerHTML می‌رفت. حالا باید
    msg را بی‌شرط trust کند (چون msg از پیش یا رشتهٔ لفظیِ ثابت است یا با
    esc()/ltr() ساخته شده — همان قراردادی که هر صداکنندهٔ toast در این فایل
    از قبل رعایت می‌کند)."""
    idx = JS.find("function toast(")
    assert idx >= 0, "‏toast تعریف نشده"
    body = JS[idx:idx + 500]
    assert "w.innerHTML = msg;" in body, f"‏toast دیگر msg را بی‌شرط trust نمی‌کند: {body[:200]}"
    assert "؀" not in body and "ۿ" not in body, \
        "‏toast هنوز شرطِ فارسی‌بودن دارد — escapeِ نامتقارن برگشته"


def t_home_quiet_list_always_escapes():
    """ممیزیِ وب‌اپ ۲۰۲۶-۰۸-۰۷ (XSS، فیکس‌شده): برعکسِ toast — اینجا رشتهٔ
    فارسی escape می‌شد و غیرِفارسی خام می‌رفت. فهرستِ «چیزِ دیگر سالم است»
    امروز فقط از رشته‌هایِ لفظیِ ثابت پر می‌شود، ولی escape باید بی‌شرط
    بماند تا اگر فردا محتوایِ پویا اضافه شد، از قبل امن باشد."""
    idx = JS.find("چیزِ دیگر سالم است")
    assert idx >= 0, "‏فهرستِ «چیزِ دیگر سالم است» در viewHome پیدا نشد"
    body = JS[idx:idx + 300]
    assert "esc(c)" in body, f"‏فهرستِ آرام دیگر c را با esc() نمی‌پوشاند: {body[:200]}"
    assert "؀" not in body and "ۿ" not in body, \
        "‏فهرستِ آرام هنوز شرطِ فارسی‌بودن دارد — escapeِ نامتقارن برگشته"


def t_tabs_have_aria_roles_and_roving_tabindex():
    """ممیزیِ وب‌اپ ۲۰۲۶-۰۸-۰۷ (دسترس‌پذیری): تبِ فارسی برای screen reader
    قبلاً فقط یک <div> بی‌نقش بود. حالا باید role="tablist"/"tab"/"tabpanel"
    و roving tabindex (فعال=0، بقیه=-1) داشته باشد."""
    assert 'role="tablist"' in HTML, "‏#tabs نقشِ tablist ندارد"
    assert 'role="tabpanel"' in HTML, "‏#content نقشِ tabpanel ندارد"
    n_tabs = len(re.findall(r'data-tab="', HTML))
    n_role_tab = len(re.findall(r'role="tab"', HTML))
    assert n_role_tab == n_tabs, f"هر تب باید role=\"tab\" داشته باشد: {n_role_tab} از {n_tabs}"
    n_selected = len(re.findall(r'aria-selected="(?:true|false)"', HTML))
    assert n_selected == n_tabs, f"هر تب باید aria-selected داشته باشد: {n_selected} از {n_tabs}"
    # فقط یکی tabindex=0 (تبِ فعال)، بقیه -1 — roving tabindex استاندارد
    assert HTML.count('tabindex="0"') == 1, "دقیقاً یک تب باید tabindex=\"0\" باشد"
    assert HTML.count('tabindex="-1"') == n_tabs - 1, "بقیهٔ تب‌ها باید tabindex=\"-1\" باشند"


def t_tabs_keydown_handles_arrows_home_end():
    """کیبورد: فقط کلیک کار می‌کرد. حالا Left/Right/Home/End باید تبِ بعدی/
    قبلی/اول/آخر را focus و فعال کنند — الگوی استانداردِ ARIA tabs."""
    idx = JS.find('tabs.addEventListener("keydown"')
    assert idx >= 0, "‏هندلرِ keydown روی #tabs پیدا نشد"
    body = JS[idx:idx + 700]
    for key in ("ArrowRight", "ArrowLeft", "Home", "End"):
        assert f'"{key}"' in body, f"کلیدِ {key} در هندلرِ کیبورد نیست: {body[:200]}"
    assert "next.focus()" in body, "هندلرِ کیبورد focus را جابه‌جا نمی‌کند"


def t_csp_meta_present_and_scoped():
    """ممیزیِ وب‌اپ ۲۰۲۶-۰۸-۰۷: بدونِ CSP، هر XSS ِ آینده مستقیم اسکریپت اجرا
    می‌کند. باید بسته باشد (نه 'unsafe-inline' برای script)، ولی style باید
    unsafe-inline داشته باشد (‏~۱۵ جا style="…" مستقیم در innerHTML ساخته
    می‌شود — بدونش پیش‌نمایش ظاهراً می‌شکند)."""
    m = re.search(r'<meta http-equiv="Content-Security-Policy" content="([^"]*)"', HTML)
    assert m, "‏متاتگِ CSP در index.html نیست"
    csp = m.group(1)
    assert "default-src 'self'" in csp
    assert "script-src" in csp and "'unsafe-inline'" not in csp.split("script-src")[1].split(";")[0], \
        "‏script-src نباید unsafe-inline داشته باشد"
    assert "style-src 'self' 'unsafe-inline'" in csp, \
        "‏style-src باید unsafe-inline داشته باشد وگرنه style=\"…\" ها بی‌اثر می‌شوند"
    assert "https://telegram.org" in csp, "‏اسکریپتِ تلگرام باید در script-src allowlist باشد"


def t_visibility_change_rerenders_active_tab():
    """ممیزیِ وب‌اپ ۲۰۲۶-۰۸-۰۷: onActive فقط پشتِ bridge ِ تلگرام سیم‌کشی
    شده — در devMode/پیش‌نمایشِ مرورگر اصلاً صدا زده نمی‌شود. رویدادِ
    استانداردِ visibilitychange باید همان تبِ فعال را دوباره رندر کند."""
    idx = JS.find('addEventListener("visibilitychange"')
    assert idx >= 0, "‏هندلرِ visibilitychange پیدا نشد"
    body = JS[idx:idx + 300]
    assert "tab.active" in body, "‏هندلرِ visibilitychange تبِ فعال را پیدا نمی‌کند"
    assert "render(" in body, "‏هندلرِ visibilitychange دوباره render نمی‌کند"


if __name__ == "__main__":
    CHECKS = [(n, f) for n, f in sorted(globals().items())
              if n.startswith("t_") and callable(f)]
    failed = harness.run(CHECKS)
    print(f"\n{'✅' if not failed else '❌'} test_miniapp_look_locked: "
          f"{len(CHECKS) - failed}/{len(CHECKS)} passed")
    sys.exit(1 if failed else 0)
