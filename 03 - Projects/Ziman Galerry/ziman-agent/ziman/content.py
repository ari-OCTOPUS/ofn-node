"""تولیدِ draft محتوای مارکتینگ برای زیمان.

دو مسیر:
  • live: از طریقِ llm_router (Ollamaِ محلی → Anthropic API با بودجه). خرج fail-closed.
  • offline (پیش‌فرضِ امن): draftِ قالبیِ قطعی، با برچسبِ روشن. هرگز منتشر نمی‌شود.

قواعدِ سختِ برند (از Business-Zeiman.md و Strategy-DecisionLog.md):
  گل‌ها مصنوعی‌اند (نه رقیبِ گلِ تازه) · روایتِ کمیابی بر پایهٔ ظرفیتِ محدود ·
  PayID + تحویلِ محلیِ سیدنی · بازارِ گرم اول · هرگز انتشار بدونِ تأییدِ انسانی.
"""
from datetime import date

from . import llm_router


def pick_occasion(cfg, today=None):
    today = today or date.today()
    for a in cfg.get("calendar_anchors", []) or []:
        if int(a.get("month", 0)) == today.month:
            return a.get("name", "هدیه")
    occ = cfg.get("occasions") or ["هدیه"]
    return occ[today.timetuple().tm_yday % len(occ)]


def pick_product(cfg, today=None):
    today = today or date.today()
    products = cfg["business"]["products"]
    return products[today.timetuple().tm_yday % len(products)]


def _offline_draft(cfg, occasion, product) -> str:
    cap = cfg["capacity"]["units_per_week_ceiling"]
    name = cfg["business"]["name"]
    segs = "، ".join(cfg.get("audience", {}).get("segments", []) or [])
    return f"""# [OFFLINE DRAFT — بدونِ مدلِ زنده] {name}
مناسبت: {occasion} · محصول: {product} · تاریخ: {date.today()}

سلام 🌸
برای «{occasion}» یک هدیهٔ دست‌سازِ ماندگار داریم: {product}.
هر قطعه دست‌ساز و محدود است — ظرفیتِ ما فقط {cap} عدد در هفته است، پس هر سفارش خاص می‌ماند.
گل‌ها مصنوعی و ماندگارند (نه شاخهٔ بریده) — مناسبِ یادگاری و دکور.
تحویلِ محلی در سیدنی · پرداخت با PayID.

پیامِ مستقیم بده تا رنگ و بودجه را با هم تنظیم کنیم.

#هدیه_دست_ساز #سیدنی #{occasion.replace(' ', '_')} #زیمان #PayID

—
مخاطبِ هدف (بازارِ گرم): {segs}
یادداشت: این پیش‌نویس است؛ انتشار فقط با تأییدِ انسانی. ماهیتِ مصنوعیِ گل‌ها صراحتاً ذکر شود.
"""


def _draft_prompt(cfg, occasion, product, context):
    cap = cfg["capacity"]["units_per_week_ceiling"]
    system = (
        "تو کپی‌رایترِ یک برندِ هدایای دست‌سازِ لوکس در سیدنی به‌نامِ «زیمان» هستی. "
        "فارسیِ گرم و مجلسی بنویس. قواعدِ سخت: (۱) گل‌ها مصنوعی‌اند؛ هرگز مثلِ گلِ تازه تبلیغ نکن — "
        "بازارِ هدیهٔ یادگاری/دکوری. (۲) روایتِ کمیابی بر پایهٔ ظرفیتِ محدود "
        f"(فقط {cap} عدد در هفته). (۳) پرداخت PayID و تحویلِ محلیِ سیدنی. "
        "(۴) دعوت به پیامِ مستقیم برای بستنِ فروش، نه تبلیغِ سرد. "
        "یک کپشنِ کوتاهِ اینستاگرام + ۵ هشتگ بده. چیزی جز خودِ کپشن ننویس."
    )
    user = (f"مناسبت: {occasion}\nمحصول: {product}\n\n"
            f"زمینه از vault (خلاصه):\n{(context or '')[:1500]}")
    return system, user


def generate_draft(cfg, context="", occasion=None, product=None):
    """یک draft می‌سازد و (متن, mode) برمی‌گرداند.

    اول مسیرِ live از روتر (Ollama→API با بودجه)؛ اگر نبود، افتِ امن به offline.
    هرگز استثنا به بیرون نمی‌دهد.
    """
    occasion = occasion or pick_occasion(cfg)
    product = product or pick_product(cfg)
    system, user = _draft_prompt(cfg, occasion, product, context)
    max_tokens = int((cfg.get("generation") or {}).get("max_tokens", 700))
    name = cfg["business"]["name"]
    try:
        text, route = llm_router.generate(cfg, system, user, max_tokens)
        header = (f"# [LIVE DRAFT — {route}] {name}\n"
                  f"مناسبت: {occasion} · محصول: {product} · تاریخ: {date.today()}\n\n")
        return header + text.strip() + "\n\n—\nیادداشت: پیش‌نویس است؛ انتشار فقط با تأییدِ انسانی.", route
    except Exception:  # noqa: BLE001 — هیچ مسیرِ live نبود → offline امن
        return _offline_draft(cfg, occasion, product), "offline"


# ---------------------------------------------------------------------------
# تولیدِ دسته‌ایِ محتوای فروش: DMهای بازارِ گرم و پست‌های مناسبتی.
# همان دو مسیر: live (روتر) و offline (قالبی). هیچ‌کدام منتشر نمی‌کنند.
# ---------------------------------------------------------------------------
def _dm_variants(cfg):
    cap = cfg["capacity"]["units_per_week_ceiling"]
    occ = cfg.get("occasions") or ["مناسبت"]
    out = [("دوستِ نزدیک",
            "سلام [اسم] 🌸 راستی من و مامانم هدیه‌های دست‌سازِ ماندگار درست می‌کنیم — "
            f"گل‌آرایی، شادوباکس، سبدِ هدیه. چون دست‌سازه تعداد محدوده (هفته‌ای ~{cap} تا). "
            "اگه مناسبتی تو راه داری بگو برات یه چیزِ خاص کنار بذارم.")]
    for o in occ:
        out.append((f"مناسبت: {o}",
                    f"سلام [اسم] 🌸 برای «{o}» یه هدیهٔ دست‌سازِ ماندگار دارم که خاص می‌مونه "
                    "(گل‌ها مصنوعی‌ان، پس خراب نمی‌شن). رنگ‌بندی رو با سلیقهٔ خودت ست می‌کنم. "
                    "تحویلِ محلیِ سیدنی · پرداخت PayID."))
    out.append(("فالوآپِ نرم",
                "سلام [اسم] 🌸 یادآوری کنم اون گزینه‌ای که پسندیدی هنوز هست، ولی چون محدوده زود پُر می‌شه. "
                "بخوای همین امروز برات کنار می‌ذارم و با PayID نهایی می‌کنیم."))
    out.append(("هدیهٔ استراتژیک به فردِ تأثیرگذار",
                "سلام [اسم] 🌸 دوست دارم یکی از گل‌آرایی‌های دست‌سازمو بدونِ هیچ شرطی برات هدیه بفرستم. "
                "اگه پسندیدی و دلت خواست تو استوری معرفی کنی ممنون می‌شم — کاملاً اختیاری. آدرست رو بدم؟"))
    return out


def _post_variants(cfg):
    name = cfg["business"]["name"]
    return [
        ("معرفیِ برند",
         f"{name} 🌸 هدیه‌های دست‌سازِ ماندگار، ساختِ سیدنی. گل‌ها مصنوعی و ماندگارن — یادگاری می‌مونن نه چند روز. "
         "دست‌ساز و محدود. برای سفارش DM بده 💌 · تحویلِ محلیِ سیدنی · PayID\n"
         "#هدیه_دست_ساز #سیدنی #گل_ماندگار #زیمان"),
        ("اسپاتلایتِ شادوباکس",
         "یادگاری‌ای که خراب نمی‌شه 🖼️🌸 شادوباکسِ گلِ قاب‌شده — برای نامزدی، سالگرد یا هر لحظه‌ای که می‌خوای بمونه. "
         "رنگ‌بندی با سلیقهٔ خودت. DM برای رنگ و بودجه 💌\n#شادوباکس #هدیه_ماندگار #سیدنی #زیمان"),
        ("کمیابی / پشتِ صحنه",
         f"چرا تعدادمون کمه؟ چون واقعاً دست‌سازه ✋🌸 هفته‌ای فقط چند قطعه می‌سازیم تا کیفیت بالا بمونه. "
         "پس هر سفارش خاص می‌مونه. مناسبت داری؟ زودتر DM بده تا جا بمونه.\n#ساخت_دست #محدود #سیدنی #زیمان"),
    ]


def _batch_prompt(cfg, kind, n, context):
    cap = cfg["capacity"]["units_per_week_ceiling"]
    what = ("پیامِ مستقیمِ کوتاه (DM) برای بازارِ گرم" if kind == "dm"
            else "کپشنِ کوتاهِ اینستاگرام")
    system = (
        "تو کپی‌رایترِ برندِ هدایای دست‌سازِ لوکسِ «زیمان» در سیدنی هستی. فارسیِ گرم و مجلسی. "
        "قواعدِ سخت: (۱) گل‌ها مصنوعی‌اند؛ هرگز مثلِ گلِ تازه تبلیغ نکن. (۲) روایتِ کمیابی بر پایهٔ ظرفیتِ محدود "
        f"({cap} در هفته). (۳) PayID + تحویلِ محلیِ سیدنی. (۴) دعوت به پیامِ مستقیم، نه تبلیغِ سرد. "
        "جای اسم از [اسم] استفاده کن."
    )
    user = (f"{n} عددّ {what} بنویس، متنوع و برای مناسبت‌های مختلف. "
            f"به‌صورتِ فهرستِ شماره‌دار. فقط خودِ متن‌ها.\n\nزمینه:\n{(context or '')[:1200]}")
    return system, user


def _batch(cfg, kind, n, context, header_label, variants):
    system, user = _batch_prompt(cfg, kind, n, context)
    max_tokens = int((cfg.get("generation") or {}).get("max_tokens", 700)) + 200
    name = cfg["business"]["name"]
    try:
        body, route = llm_router.generate(cfg, system, user, max_tokens)
        head = f"# [LIVE {header_label} — {route}] {name} · {date.today()}\n\n"
        return head + body.strip() + "\n\n—\nپیش‌نویس؛ انتشار با تأییدِ انسانی.", route
    except Exception:  # noqa: BLE001 — افتِ امن به قالبِ offline
        picked = variants[:max(1, int(n))]
        body = "\n\n".join(f"**{i + 1}) {t}**\n> {msg}" for i, (t, msg) in enumerate(picked))
        head = f"# [OFFLINE {header_label} — بدونِ مدلِ زنده] {name} · {date.today()}\n\n"
        return head + body + "\n\n—\nپیش‌نویس؛ [اسم] را شخصی کن و دستی بفرست. انتشار با تأییدِ انسانی.", "offline"


def generate_dms(cfg, n=5, context=""):
    return _batch(cfg, "dm", n, context, "DMs", _dm_variants(cfg))


def generate_posts(cfg, n=3, context=""):
    return _batch(cfg, "posts", n, context, "POSTS", _post_variants(cfg))
