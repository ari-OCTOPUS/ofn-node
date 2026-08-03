"""
menus.py — معماریِ تجربه‌ی کاربری: منوی اصلی + ۹ زیرمنو.

داده‌ی منوها اینجا متمرکز است (نه پخش در bot.py). bot.py فقط این‌ها را رندر می‌کند.
هر دسته فقط دستورهای خودش را نشان می‌دهد — نه همه‌چیز یکجا.
"""

from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# هر دسته: key → (عنوان، توضیحِ کوتاه، [(دستور، توضیح)])
MENU = {
    "record": ("📋 ثبت امروز و بدن",
               "وضعیتِ روزانه‌ات را ثبت می‌کنی: خواب، بدن، مصرف، مکان، یادداشت و RMSSD.",
               [("/log", "ثبت کامل روزانه"), ("/checkin", "چک‌این سریع بدون RMSSD"),
                ("/rmssd", "محاسبه RMSSD از داده خام"), ("/rmssd_help", "راهنمای اندازه‌گیری"),
                ("/today", "خلاصه امروز"), ("/streak", "پیوستگی روزهای ثبت")]),
    "patterns": ("📊 الگوها و گزارش‌ها",
                 "LANGAR کمک می‌کند الگوها را ببینی، نه اینکه حکم قطعی بدهد. همبستگی ≠ علیت.",
                 [("/trend", "روند RMSSD/خواب/مصرف"), ("/review_weekly", "مرور هفتگی"),
                  ("/review_monthly", "مرور ماهانه"), ("/habit_report", "گزارش عادت‌ها")]),
    "insights": ("💡 بینش‌ها و صداقت ذهنی",
                 "فکرها و فرضیه‌هایت ثبت می‌شوند؛ فردا برای داوریِ هوشیار جلویت می‌آیند.",
                 [("/insight", "ثبت بینش/فرضیه"), ("/recheck", "داوریِ برگشت‌ناپذیر"),
                  ("/insights", "فهرست بینش‌ها"), ("/insight_stats", "آمار بینش‌ها")]),
    "habits": ("🌱 عادت‌ها و اهداف",
               "هدف و عادت می‌سازی — بدونِ زبانِ شرم، با قدم‌های کوچک.",
               [("/habit", "ساخت عادت"), ("/done", "ثبت انجامِ امروز"),
                ("/habits", "فهرست عادت‌ها"), ("/habit_report", "گزارش عادت‌ها"),
                ("/goal", "تعریف هدف"), ("/coach", "پیشنهادِ آرامِ داده‌محور")]),
    "experiments": ("🧪 آزمایش شخصی N-of-1",
                    "فرضیه‌ها را به آزمایشِ واقعی روی داده‌ی خودت تبدیل می‌کنی. (نه تشخیصِ پزشکی)",
                    [("/experiment", "طراحی آزمایش"), ("/experiments", "فهرست آزمایش‌ها"),
                     ("/experiment_report", "گزارش نتیجه"), ("/experiment_stop", "توقف آزمایش")]),
    "research": ("🔎 پژوهش و طراحی زندگی",
                 "درباره‌ی یک سؤال تحقیق می‌کند، منابع را خلاصه می‌کند، و پیشنهادِ آزمایش می‌دهد. تصمیمِ نهایی با توست.",
                 [("/research", "پژوهشِ وب با منبع"), ("/architect", "طراحی بر اساسِ اهداف"),
                  ("/contract", "قراردادِ انسان‑AI")]),
    "mind": ("🧠 مدل ذهنی و مغز دوم",
             "LANGAR آرام‌آرام مدلِ ذهنی‌اش از تو را بهتر می‌کند — برای خودشناسی، نه کنترل.",
             [("/ask", "سؤالِ روزانه"), ("/reflect", "یادداشت آزاد"),
              ("/mind", "مدل ذهنی فعلی"), ("/improve", "تنظیم آرامِ سیستم")]),
    "data": ("🔒 داده، حریم خصوصی و کنترل",
             "داده‌هایت را ببین، خروجی بگیر، یا بات را ساکت/فعال کن.",
             [("/export", "خروجی JSON"), ("/export_csv", "خروجی CSV"),
              ("/import_muse", "ورود فایل Muse"), ("/status", "وضعیت سیستم"),
              ("/halt", "توقف بات"), ("/resume", "ادامه"), ("/privacy", "حریم خصوصی")]),
    "ailab": ("🤖 AI-Lab | آزمایشگاه هوش مصنوعی",
              "تحقیق و طراحی درباره‌ی خودِ هوش مصنوعی. از داده‌ی شخصیِ تو جدا نگهداری می‌شود.",
              [("/ailab", "منوی AI-Lab"), ("/ai_research", "تحقیق درباره AI"),
               ("/ai_digest", "خلاصه‌ی پیشرفت‌ها"), ("/ai_architect", "طراحی معماری"),
               ("/ai_ideas", "ثبت ایده"), ("/ai_roadmap", "نقشه راه"),
               ("/ai_propose_update", "پیشنهادِ آپدیت (بدونِ اجرا)")]),
}
ORDER = ["record", "patterns", "insights", "habits", "experiments",
         "research", "mind", "data", "ailab"]

NEW_USER_PATH = ("🌟 تازه شروع کرده‌ای؟ این مسیر را برو:\n"
                 "۱) /checkin  ۲) /habit  ۳) /ask  ۴) بعد از چند روز /trend")


def main_menu_text() -> str:
    return ("LANGAR — دفترچه‌ی همیشه‌روشن برای خودشناسی، آزمایشِ شخصی و رشدِ آرام.\n"
            "امروز کدام بخش را باز می‌کنی؟\n\n" + NEW_USER_PATH)


def main_menu_keyboard() -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(MENU[k][0], callback_data=f"menu:{k}")] for k in ORDER]
    return InlineKeyboardMarkup(rows)


def category_text(key: str) -> str:
    title, desc, cmds = MENU[key]
    lines = [f"{c} — {d}" for c, d in cmds]
    return f"{title}\n\n{desc}\n\n" + "\n".join(lines)


def category_keyboard(key: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ منوی اصلی", callback_data="menu:main")]])


def suggest_for_unknown() -> str:
    return ("این دستور را نشناختم. شاید یکی از این‌ها:\n"
            "• منوی اصلی: /menu\n• ثبت امروز: /checkin\n• AI-Lab: /ailab")
