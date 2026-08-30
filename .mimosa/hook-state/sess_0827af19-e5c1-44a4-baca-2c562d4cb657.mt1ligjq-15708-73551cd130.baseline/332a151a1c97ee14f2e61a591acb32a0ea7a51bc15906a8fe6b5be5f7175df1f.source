"""
research_wiring_example.py — نمونه‌ی مستقلِ سیم‌کشیِ /research با ProClient.

این فایل اجرا/import نمی‌شود؛ فقط الگوست تا ببینی چطور pro و fallbackِ محلی را
به هم وصل کنی. منطقِ واقعی در bot.py (تابعِ cmd_research) از قبل به همین شکل وصل شده.

الگو:
    ۱) اول ProClient().research(query) را صدا بزن.
    ۲) اگر fallback=True بود → researcherِ محلی.
    ۳) منبع را به کاربر نشان بده (pro یا محلی).
"""

from pro_client import ProClient


def local_research(query: str) -> dict:
    """جایگزینِ نمونه؛ در پروژه این همان _RESEARCHER.research(...) است."""
    return {"brief": f"پاسخِ محلی برای: {query}", "sources": []}


def handle_research(query: str) -> str:
    # ۱) تلاش با بک‌اندِ pro
    pro = ProClient().research(query, target="armin")

    if not pro.get("fallback"):
        # ۲) موفق از سمتِ pro
        srcs = pro.get("sources") or []
        src_lines = "\n".join(
            f"  • {s.get('url') if isinstance(s, dict) else s}" for s in srcs[:5]) or "  —"
        return (f"🔎 منبع: langar-pro (decision #{pro.get('decision_id')})\n\n"
                f"{pro.get('brief', '')}\n📚 منابع:\n{src_lines}")

    # ۳) fallback محلی (pro خاموش/در دسترس نبود)
    out = local_research(query)
    return f"🔎 منبع: محلی · (دلیلِ fallback: {pro.get('reason')})\n\n{out['brief']}"


if __name__ == "__main__":
    # تستِ دستی: بدونِ LANGAR_PRO_URL باید مسیرِ محلی برود
    print(handle_research("آیا کافئین دیروقت RMSSD را پایین می‌آورد؟"))
