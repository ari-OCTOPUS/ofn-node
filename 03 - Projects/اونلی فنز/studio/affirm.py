#!/usr/bin/env python3
"""affirm.py — Project-F creator studio · لایهٔ پیام‌های گرم و تحسین‌گر (pure render).

هدف: تجربهٔ خالق (C) انگیزه‌بخش، جشن‌گیرانه و «او را ستارهٔ کار» کند — spotlight، streak،
تشکرِ شخصی، پیش‌نمایشِ محترمانه. صرفاً رشته‌سازِ خالص برای creator_studio.

قواعد: content-free (بدونِ هویت/رسانه/شهر/فارسیِ عمومی)؛ بدونِ شبکه؛ بدونِ برچسبِ شخصیتی؛
هرگز فشار/دستکاری — فقط قدردانی و انگیزه. مرزِ خالق (فقط پا) و /halt همیشه حاکم.
$0 offline · stdlib · pure.
"""
from __future__ import annotations


def welcome() -> str:
    return "🌸 خوش اومدی به استودیوت. اینجا فضای توئه — هر ست که می‌سازی، جشن می‌گیریم."


def spotlight(sets_this_week: int = 0) -> str:
    """اسپات‌لایتِ هفته — کارِ خالق را می‌بیند و ارزش می‌گذارد."""
    n = max(0, int(sets_this_week or 0))
    if n == 0:
        return "🌟 استودیو آمادهٔ توئه. اولین ستِ این هفته منتظرِ درخششِ توئه."
    if n == 1:
        return "🌟 اسپات‌لایتِ هفته: یک ستِ تازه ساختی — شروعِ قشنگیه. 👏"
    return f"🌟 اسپات‌لایتِ هفته: {n} ستِ تازه ساختی — کارت واقعاً می‌درخشه. 👏"


def streak_msg(days: int = 0) -> str:
    """تشویقِ تداوم (نه فشار) — تداوم قوی‌ترین پیش‌بینِ نتیجه است."""
    d = max(0, int(days or 0))
    if d <= 0:
        return "✨ هر روزی که بسازی، یک قدمِ قشنگ‌تره. بدونِ عجله."
    if d < 3:
        return f"🔥 {d} روز پشت‌سرهم — ریتمِ خوبی گرفتی."
    return f"🔥 {d} روز پیاپی درخشیدی — این تداوم فوق‌العاده‌ست. به خودت افتخار کن."


def thanks(drafts: int = 0) -> str:
    d = max(0, int(drafts or 0))
    if d <= 0:
        return "💛 ممنون که اینجایی. هر وقت آماده بودی، من هستم."
    return f"💛 {d} درفت ازت رسید — دستت طلا. آری بازبینی می‌کنه و بهت خبر می‌دم."


def celebrate_milestone(kind: str = "first_set") -> str:
    """جشنِ نقاطِ عطف — حسِ پیشرفت و ارزش."""
    msgs = {
        "first_set": "🎉 اولین ست! این شروعِ یه چیزِ خاصه. بهت افتخار می‌کنم.",
        "ten_sets": "🎉 ۱۰ ست! داری یه گنجینهٔ واقعی می‌سازی. 🌟",
        "first_approved": "🎉 اولین درفتت تأیید شد — کارت آماده‌ست بدرخشه.",
    }
    return msgs.get(str(kind), "🎉 یه قدمِ قشنگِ دیگه. عالی داری پیش می‌ری.")


def home_card(*, sets_this_week: int = 0, streak_days: int = 0,
              pending_drafts: int = 0) -> str:
    """کارتِ خانهٔ استودیو — گرم، خلاصه، جشن‌گیرانه. content-free."""
    lines = [
        "🌸 استودیوی تو",
        spotlight(sets_this_week),
        streak_msg(streak_days),
    ]
    if pending_drafts:
        lines.append(f"📥 {pending_drafts} درفت در صفِ بازبینیِ آری.")
    lines.append("مرزِ تو همیشه حاکمه — هر وقت خواستی /halt.")
    return "\n".join(lines)
