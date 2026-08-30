"""prompt.py — بارگذاریِ پرامپتِ سیستمیِ مغز از BRAIN_PROMPT.md."""

from __future__ import annotations

from pathlib import Path

_FALLBACK = (
    "تو تسهیلگرِ یک کارگاهِ خصوصیِ N-of-1 هستی. هر بار فقط یک سؤالِ دقیق، کوتاه و "
    "قابلِ‌پاسخ بپرس که سوار بر داده‌ی کاربر باشد. خروجی فارسی و در قالب:\n"
    "🧭 حوزه: <حوزه>\n❓ <یک سؤال>\nچرا امروز: <یک جمله>\n"
    "پزشک نیستی؛ تشخیص/تجویز نده. نشخوارِ منفی را تقویت نکن."
)


def get_system_prompt() -> str:
    # BRAIN_PROMPT.md در ریشه‌ی پروژه (یک پوشه بالاتر از brain/)
    p = Path(__file__).resolve().parent.parent / "BRAIN_PROMPT.md"
    try:
        return p.read_text(encoding="utf-8")
    except OSError:
        return _FALLBACK
