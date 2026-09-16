#!/usr/bin/env python3
"""rollback — برگرداندنِ artifactهای A1. کوچک، صریح، و بدونِ ادعای بزرگ.

دامنه عمداً باریک است: فقط فایل‌هایی که خودِ executor در sandbox ساخته و در
رسید ثبت کرده. هیچ ادعایی دربارهٔ برگرداندنِ اثرِ بیرونی نمی‌شود — چون A2..A5
در این دور اصلاً اجرا نمی‌شوند و «rollback ِ یک پیامِ ارسال‌شده» یک دروغ است.

قاعده: `rollback_available` در رسید فقط وقتی `True` است که **هر** artifact
مسیرِ ثبت‌شده و داخلِ sandbox داشته باشد. یکی که نداشته باشد ⇒ کلِ رسید
`rollback_available=False` — نه «نیمه‌برگشت‌پذیر»، که معنایش هیچ است.

$0 · stdlib · فقط داخلِ sandbox می‌نویسد/حذف می‌کند.
"""
from __future__ import annotations

from pathlib import Path

from scope_guard import contained


def plan_for(artifacts, *, sandbox_root) -> dict:
    """نقشهٔ برگشت + آیا اصلاً برگشت‌پذیر است."""
    items, unsafe = [], []
    root = Path(sandbox_root).resolve()
    for a in (artifacts or []):
        p = (a or {}).get("path") if isinstance(a, dict) else a
        if not p:
            unsafe.append({"path": None, "why": "no-path"})
            continue
        try:
            rp = Path(p).resolve()
        except (OSError, ValueError):
            unsafe.append({"path": str(p), "why": "unresolvable"})
            continue
        if not contained(rp, root):
            unsafe.append({"path": str(p), "why": "outside-sandbox"})
            continue
        items.append({"path": str(rp), "op": "delete"})
    return {"available": bool(items) and not unsafe,
            "items": items, "unsafe": unsafe}


def execute(plan: dict) -> dict:
    """برگشت را انجام بده. ناتمام = صریح، نه بی‌صدا."""
    if not (plan or {}).get("available"):
        return {"ok": False, "reason": "not-available",
                "unsafe": (plan or {}).get("unsafe", [])}
    done, failed = [], []
    for it in plan.get("items", []):
        p = Path(it["path"])
        try:
            if p.exists():
                p.unlink()
            done.append(str(p))
        except OSError as e:
            failed.append({"path": str(p), "error": type(e).__name__})
    return {"ok": not failed, "reverted": done, "failed": failed}
