#!/usr/bin/env python3
"""company_books.py — آداپتورِ ریلِ A: دفترِ شرکت در اپِ حسابداریِ حرفه‌ای (2026-07-16).

معماری: [[03 - Projects/Accounting/ARCHITECTURE-TWO-RAILS]]. دفترِ مالیاتیِ شرکت = خودِ اپ؛
اختاپوس رهبرِ ارکستر است: می‌خواند، پیش‌نویسِ اینویس می‌سازد (propose-only)، وضعیت را به
تلگرام می‌آورد، و بانک↔اپ را متقابل چک می‌کند. **ارسالِ ایمیل کارِ خودِ اپ است** —
اختاپوس SMTP ندارد (safety-by-absence).

طراحی provider-agnostic: هر providerِ پشتیبانی‌شده یک ماژولِ `books_<name>.py` هم‌پوشه
است با قراردادِ حداقلی:
    connect_check() -> {"ok": bool, "org": str|None, "note": str}
    list_invoices(status=None, limit=20) -> {"ok": bool, "invoices": [...], "note": str}
    create_draft_invoice(inv: dict) -> {"ok": bool, "draft_id": str|None, "note": str}
هر متد fail-soft و بدونِ echoِ هیچ secret. انتخابِ provider از env:
    COMPANY_BOOKS_PROVIDER=<name>   +   OCTOPUS_WIRE_COMPANY_BOOKS=1
توکن/کلیدها فقط در .env (gitignored) با پیشوندِ همان provider (مثلاً XERO_*).

مرزها (تغییرناپذیر): نوشتن فقط DRAFT (تأیید/ارسال با مالک) · هیچ پرداخت/جابه‌جاییِ پول ·
هیچ tax-conclusion (اپ + حسابدارِ ثبت‌شده تصمیم می‌گیرند) · فلگ خاموش = no-opِ صادق.
$0 · stdlib · fail-soft.
"""
from __future__ import annotations

import importlib
import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
if str(_HERE.parent / "budget") not in sys.path:
    sys.path.insert(0, str(_HERE.parent / "budget"))

_FLAG = "OCTOPUS_WIRE_COMPANY_BOOKS"
_PROVIDER_ENV = "COMPANY_BOOKS_PROVIDER"
_KNOWN_PROVIDERS = ("xero", "myob", "qbo", "zoho", "reckon")


def _provider_name() -> str:
    return str(os.environ.get(_PROVIDER_ENV, "") or "").strip().lower()


def wired() -> bool:
    return os.environ.get(_FLAG) == "1" and bool(_provider_name())


def _load_provider():
    """ماژولِ providerِ پیکربندی‌شده (books_<name>). نبود/خطا → None (وضعِ صادقِ خاموش)."""
    name = _provider_name()
    if name not in _KNOWN_PROVIDERS:
        return None
    try:
        return importlib.import_module(f"books_{name}")
    except Exception:  # noqa: BLE001 — providerِ هنوز-ساخته‌نشده = خاموشِ صادق
        return None


def status() -> dict:
    """وضعِ ریلِ شرکت — PII/secret-free، برای کارتِ /finance. هرگز crash نمی‌کند."""
    if os.environ.get(_FLAG) != "1":
        return {"wired": False, "provider": _provider_name() or None,
                "note": "خاموش (فلگ OCTOPUS_WIRE_COMPANY_BOOKS)"}
    name = _provider_name()
    if not name:
        return {"wired": False, "provider": None,
                "note": f"provider تنظیم نشده ({_PROVIDER_ENV} در .env)"}
    mod = _load_provider()
    if mod is None:
        return {"wired": False, "provider": name,
                "note": f"providerِ {name} هنوز پیاده‌سازی/نصب نشده"}
    try:
        r = mod.connect_check()
        return {"wired": bool(r.get("ok")), "provider": name,
                "org": r.get("org"), "note": str(r.get("note", ""))[:120]}
    except Exception as e:  # noqa: BLE001
        return {"wired": False, "provider": name, "note": f"خطای اتصال: {type(e).__name__}"}


def list_invoices(status_filter: str | None = None, limit: int = 20) -> dict:
    """اینویس‌های اپ (read-only). خاموش/خطا → لیستِ خالیِ صادق."""
    if not wired():
        return {"ok": False, "invoices": [], "note": "ریلِ شرکت خاموش است"}
    mod = _load_provider()
    if mod is None:
        return {"ok": False, "invoices": [], "note": "provider در دسترس نیست"}
    try:
        return mod.list_invoices(status=status_filter, limit=int(limit))
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "invoices": [], "note": f"خطا: {type(e).__name__}"}


def create_draft_invoice(inv: dict) -> dict:
    """پیش‌نویسِ اینویس در اپ — **همیشه DRAFT** (قاعدهٔ ۳ معماری). ارسال/approve با مالک.
    inv حداقلی: {contact_name, line_items:[{description, quantity, unit_amount_aud}], reference}.
    گاردِ سخت: هر تلاش برای status غیرِ DRAFT همین‌جا رد می‌شود، قبل از رسیدن به provider."""
    if not wired():
        return {"ok": False, "draft_id": None, "note": "ریلِ شرکت خاموش است"}
    if not isinstance(inv, dict) or not inv.get("line_items"):
        return {"ok": False, "draft_id": None, "note": "اینویسِ نامعتبر (line_items لازم)"}
    if str(inv.get("status", "DRAFT")).upper() != "DRAFT":
        return {"ok": False, "draft_id": None,
                "note": "فقط DRAFT مجاز است — approve/ارسال با مالک (قاعدهٔ propose-only)"}
    mod = _load_provider()
    if mod is None:
        return {"ok": False, "draft_id": None, "note": "provider در دسترس نیست"}
    try:
        payload = dict(inv)
        payload["status"] = "DRAFT"                     # تحمیلِ مرز، مستقل از ورودی
        return mod.create_draft_invoice(payload)
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "draft_id": None, "note": f"خطا: {type(e).__name__}"}


if __name__ == "__main__":
    print(json.dumps(status(), ensure_ascii=False, indent=2))
