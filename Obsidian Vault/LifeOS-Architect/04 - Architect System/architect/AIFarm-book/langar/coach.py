"""
coach.py — کوچِ قاعده‌محورِ deterministic (نه نصیحتِ مبهمِ AI).

recommend(ctx) یک تابعِ خالص است: ورودی یک dict از سیگنال‌های ازپیش‌محاسبه‌شده،
خروجی یک لیستِ پیشنهادِ آرام و داده‌محور (فارسی). هیچ ادعای پزشکی، هیچ علیت.
"""

from __future__ import annotations

DISCLAIMER = "ℹ️ این تشخیص نیست؛ سیگنال‌های شخصیِ توست. هم‌زمان چند متغیر را تغییر نده."


def recommend(ctx: dict) -> list[str]:
    """
    کلیدهای ctx (همه اختیاری):
      n_logs:int, rmssd_below_baseline:bool, sleep_low:bool, used_recently:bool,
      insight_confirm_rate:float|None, insights_judged:int,
      days_since_export:int|None, exp_active:bool, exp_adherence:float|None,
      habit_missed:int  (بیشترین missهای پیاپیِ یک عادت)
    """
    recs: list[str] = []

    if ctx.get("n_logs", 0) < 3:
        recs.append("داده‌ات هنوز کم است؛ چند روز پشت‌سرِ هم /log بزن تا الگو معنا پیدا کند.")
        return recs  # با داده‌ی کم، بقیه‌ی قواعد نامعتبرند

    if ctx.get("rmssd_below_baseline") and ctx.get("sleep_low"):
        recs.append("RMSSDِ اخیرت زیرِ baseline و خوابت هم پایین بوده. فردا را ساده بگیر و خواب را در اولویت بگذار.")
    elif ctx.get("rmssd_below_baseline") and ctx.get("used_recently"):
        recs.append("RMSSDِ پایین هم‌زمان با مصرفِ اخیر دیده می‌شود. به‌جای نتیجه‌گیری، یک آزمایشِ N-of-1 بساز (/experiment) و رابطه را بسنج.")
    elif ctx.get("rmssd_below_baseline"):
        recs.append("RMSSDِ اخیرت زیرِ baseline است — یک سیگنالِ بازیابی. تغییرِ بزرگ نده؛ فقط مشاهده کن.")

    rate = ctx.get("insight_confirm_rate")
    if rate is not None and ctx.get("insights_judged", 0) >= 4 and rate < 0.4:
        recs.append("نرخِ تأییدِ بینش‌هایت پایین است؛ بیشتر با تگِ S/P ثبت کن تا E — یعنی فروتن‌تر فرض بگیر.")

    dse = ctx.get("days_since_export")
    if dse is not None and dse > 21:
        recs.append(f"{dse} روز است export نگرفته‌ای. یک /export برای پشتیبان بگیر.")

    adh = ctx.get("exp_adherence")
    if ctx.get("exp_active") and adh is not None and adh < 0.6:
        recs.append("پایبندیِ آزمایشِ فعالت پایین است؛ مداخله را کوچک‌تر کن تا قابلِ‌اجراتر شود.")

    if ctx.get("habit_missed", 0) >= 3:
        recs.append("یک عادت چند روز پشت‌سرِ هم جا مانده. به‌جای فشار، «نسخه‌ی حداقلی»‌اش را اجرا کن.")

    if not recs:
        recs.append("سیگنالِ هشداری نیست. مسیر را همین‌طور ادامه بده و داده جمع کن.")
    return recs


def format_report(recs: list[str]) -> str:
    body = "\n".join(f"• {r}" for r in recs)
    return f"🧭 پیشنهادِ کوچ:\n{body}\n\n{DISCLAIMER}"
