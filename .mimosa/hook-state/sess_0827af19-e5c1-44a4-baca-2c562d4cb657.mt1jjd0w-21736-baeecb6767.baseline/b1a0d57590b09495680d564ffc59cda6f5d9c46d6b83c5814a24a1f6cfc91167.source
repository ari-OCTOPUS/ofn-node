#!/usr/bin/env python3
"""Human-readable read-only views. HTML-safe enough for Telegram parse mode off/plain text."""
from __future__ import annotations

from . import catalog

_ICON = {
    "LIVE": "🟢", "WIRED_NOT_LOADED": "🟡", "INTEGRATED_IN_SANDBOX": "🧪",
    "IMPLEMENTED_NOT_INTEGRATED": "🟠", "IMPLEMENTED_NOT_WIRED": "⚪",
    "NOT_LIVE": "⚫", "MANIFEST_MISSING": "🔴", "MANIFEST_INVALID": "🔴", "UNKNOWN": "❔",
}


def status_label(s: str) -> str:
    return {
        "LIVE": "زنده", "WIRED_NOT_LOADED": "وصل، هنوز بارگذاری نشده",
        "INTEGRATED_IN_SANDBOX": "فقط در سندباکس",
        "IMPLEMENTED_NOT_INTEGRATED": "ساخته، هنوز یکپارچه نشده",
        "IMPLEMENTED_NOT_WIRED": "ساخته، صداکننده ندارد",
        "NOT_LIVE": "زنده نیست",
        "MANIFEST_MISSING": "manifest ندارد",
        "MANIFEST_INVALID": "manifest ناسازگار",
        "UNKNOWN": "نامعلوم",
    }.get(s, s)


def home(rows: list[dict] | None = None) -> str:
    rs = rows if rows is not None else catalog.discover()
    live = sum(r["status"] == "LIVE" for r in rs)
    visible = len(rs)
    broken = sum(bool(r["errors"]) for r in rs)
    lines = ["🐙 اختاپوس — مرکز مالک", "", f"قابلیت‌های دیده‌شده: {visible}",
             f"واقعاً زنده: {live} · نیازمند اتصال/تعمیر: {visible-live}"]
    if broken:
        lines.append(f"manifest ناسازگار: {broken} (پنهان نشده؛ پایین مشخص است)")
    lines += ["", "بگو:", "• «الان چه هدفی داری؟»", "• «چه چیزی واقعاً زنده است؟»",
              "• «همه قابلیت‌ها را نشان بده»", "• «چه چیزی مانع تکمیل هدف است؟»",
              "• «یک مأموریت فقط‌خواندنی بساز»", "", "هیچ action حساسی بدون کارت و رأی اجرا نمی‌شود."]
    return "\n".join(lines)


def capabilities(rows: list[dict] | None = None) -> str:
    rs = rows if rows is not None else catalog.discover()
    lines = ["🧩 قابلیت‌های اختاپوس", ""]
    if not rs:
        return "🧩 هیچ capability manifest معتبری پیدا نشد."
    for r in rs:
        lines.append(f"{_ICON.get(r['status'], '❔')} {r['title']} — {status_label(r['status'])}")
        lines.append(f"   id={r['capability_id']} · v{r['version']} · سطح={r['surface']}")
        if r["errors"]:
            lines.append("   مشکل: " + "، ".join(r["errors"][:4]))
    lines += ["", "🟢 فقط یعنی شاهد runtime در probe اعلام شده؛ ثبت در فهرست مجوز اجرا نیست."]
    return "\n".join(lines)


def capability(row: dict | None) -> str:
    if not row:
        return "❔ چنین قابلیتی در کاتالوگ پیدا نشد."
    lines = [f"{_ICON.get(row['status'], '❔')} {row['title']}",
             f"وضعیت: {status_label(row['status'])}",
             f"نسخه: {row['version']}", f"سطح: {row['surface']}",
             f"ریسک: {row['risk_class']} · نیازمند رأی: {'بله' if row['owner_gate'] else 'خیر'}",
             f"شاهد وضعیت: {row['probe'] or 'ندارد'}"]
    if row["errors"]:
        lines.append("مشکل manifest: " + "، ".join(row["errors"]))
    lines += ["", "این کارت فقط اطلاعات است؛ مجوز اجرا نیست."]
    return "\n".join(lines)


def keyboard(rows: list[dict] | None = None, page: int = 0, per: int = 8) -> list:
    rs = rows if rows is not None else catalog.discover()
    p = max(0, int(page or 0)); chunk = rs[p*per:(p+1)*per]
    kb = []
    for r in chunk:
        text = f"{_ICON.get(r['status'], '❔')} {r['title']}"[:48]
        kb.append([{"text": text, "callback_data": f"oc:c:{r['capability_id']}"[:64]}])
    nav = []
    if p:
        nav.append({"text": "◀️", "callback_data": f"oc:p:{p-1}"})
    if (p+1)*per < len(rs):
        nav.append({"text": "▶️", "callback_data": f"oc:p:{p+1}"})
    if nav: kb.append(nav)
    kb.append([{"text": "🏠 خانه", "callback_data": "oc:home"}])
    return kb
