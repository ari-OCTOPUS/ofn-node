#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""collector.py — یک عکسِ واحد از حالِ اختاپوس. فقط می‌خواند.

چرا این لایه وجود دارد
──────────────────────
تا امروز هر سطحی منبعِ خودش را جدا می‌خواند: `/now` یک‌جا، کارتِ بودجه جای دیگر،
واچ‌داگ جای سوم. نتیجه‌اش این بود که «حالِ اختاپوس» هیچ‌جا به‌صورتِ یک چیز وجود
نداشت — و هر خواننده می‌توانست تصویرِ متفاوتی بدهد بدونِ اینکه کسی متوجه شود.

این ماژول همان یک منبع است. `snapshot()` یک dict برمی‌گرداند و **هیچ‌چیز
نمی‌نویسد**.

مرزها (قراردادِ سخت — تست‌شده)
──────────────────────────────
· **صفر نوشتن.** این ماژول هیچ فایلی نمی‌سازد و تغییر نمی‌دهد. نویسنده فقط
  `supervisor.py` است و آن هم فقط داخلِ فضای‌نامِ خودش.
· **صفر اجرا.** نه `subprocess`، نه شبکه. حلقهٔ هیچ اندامی اجرا نمی‌شود —
  همان قراردادِ `cockpit_readmodel` (INV-7).
· **صفر secret.** هر رشتهٔ متنی از `redact` رد می‌شود. مرزِ مالک: «محتوای فایل و
  PII به‌صورتِ پیش‌فرض وارد تلگرام نشود».
· **fail-soft.** منبعِ خراب یا غایب ⇒ `None` و یک دلیل، نه استثنا. سطحی که
  نمی‌داند باید **بگوید نمی‌داند**، نه اینکه صفرِ مطمئن بدهد.

تازگی، نه فلگ
─────────────
هر بخش `age_minutes` دارد. درسِ ۰۷-۲۸: صفی که ۱۶ روز mtime ِ یخ‌زده داشت به هر
خواننده‌ای «۰ معطل» می‌داد — عددی که همیشه درست به نظر می‌رسید و هیچ‌وقت اطلاعاتی
نداشت. عدد بدونِ سنِ عدد، دروغِ مؤدبانه است.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
for _p in (str(_OPS), str(_OPS / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

SCHEMA = "control-plane.snapshot.v1"

# آستانهٔ «کهنه» برای نبضِ پروسه. مرکز هر تکرارِ حلقه می‌نویسد، پس ۵ دقیقه
# سکوت یعنی واقعاً چیزی ایستاده.
STALE_MIN = 5.0


def _opslib():
    try:
        import opslib  # noqa: WPS433
        return opslib
    except Exception:  # noqa: BLE001
        return None


def _redactor():
    """`redact` ِ کاکپیت — اگر نبود، تابعِ هویت (هرگز کرش)."""
    try:
        from cockpit_readmodel import redact  # noqa: WPS433
        return redact
    except Exception:  # noqa: BLE001
        return lambda s: s


def _state_dir() -> "Path | None":
    o = _opslib()
    try:
        return Path(o.STATE_DIR) if o is not None else None
    except Exception:  # noqa: BLE001
        return None


def _read_json(p: Path):
    try:
        return json.loads(p.read_text("utf-8"))
    except Exception:  # noqa: BLE001
        return None


def _age_minutes(p: Path) -> "float | None":
    """سنِ فایل بر حسبِ دقیقه — از mtime، که تنها لنگرِ غیرقابلِ‌جعل است."""
    try:
        delta = datetime.now(timezone.utc).timestamp() - p.stat().st_mtime
        return round(max(0.0, delta) / 60.0, 1)
    except Exception:  # noqa: BLE001
        return None


def processes() -> dict:
    """زنده‌بودنِ پروسه‌ها از نبضِ خودشان — نه از فلگ، نه از ادعا.

    غیابِ فایلِ نبض ≠ مرگ: یعنی **نمی‌دانیم**. سه‌حالتی گزارش می‌شود
    (`live` / `stale` / `unknown`) چون قرمزِ کاذب همان‌قدر بد است که سبزِ کاذب."""
    sd = _state_dir()
    out: dict = {"items": [], "unknown": True}
    if sd is None:
        out["reason"] = "opslib.STATE_DIR resolve نشد"
        return out
    pulse = sd / "pulse"
    if not pulse.is_dir():
        out["reason"] = "پوشهٔ نبض وجود ندارد"
        return out
    out["unknown"] = False
    for f in sorted(pulse.glob("*.json")):
        age = _age_minutes(f)
        if age is None:
            state = "unknown"
        elif age <= STALE_MIN:
            state = "live"
        else:
            state = "stale"
        out["items"].append({"name": f.stem, "state": state, "age_minutes": age})
    return out


def boot_flags() -> dict:
    """کدام پروسه با چند فلگ بالا آمده — شاهدِ بوت، نه محتوای فلگ.

    عمداً فقط **شمارش** برمی‌گردد نه نامِ فلگ: نامِ فلگ به تلگرام رفتن یعنی نشتِ
    سطحِ پیکربندی. اگر مالک نام خواست، مسیرِ اختصاصیِ خودش را دارد."""
    sd = _state_dir()
    out: dict = {"items": [], "unknown": True}
    if sd is None:
        out["reason"] = "STATE_DIR resolve نشد"
        return out
    out["unknown"] = False
    for f in sorted(sd.glob("flags-loaded-*.json")):
        data = _read_json(f)
        # ⚠️ نسخهٔ اول `len(data)` می‌گرفت و **کلیدهای پاکت** را می‌شمرد
        # (schema/source/pid/…) پس برای هر پروسه «۱۰ فلگ» می‌داد در حالی که
        # سیستم ۱۵۶ فلگ دارد. عددِ آبرومند ولی غلط. شمارش از `flags` می‌آید.
        flags = data.get("flags") if isinstance(data, dict) else None
        # `load_shortfall` همان سیگنالی است که حادثهٔ CRLF را لو داد: مرکز با
        # ۵۹ از ۱۵۶ فلگ بالا آمده بود و هیچ سطحی نمی‌گفت. صفر نیست ⇒ ناقص بوت
        # شده، حتی اگر پروسه سالم به نظر برسد.
        shortfall = data.get("load_shortfall") if isinstance(data, dict) else None
        out["items"].append({
            "process": f.stem.replace("flags-loaded-", ""),
            "flags_loaded": len(flags) if isinstance(flags, dict) else None,
            "load_shortfall": shortfall,
            "age_minutes": _age_minutes(f),
        })
    return out


def queues() -> dict:
    """صفِ تأییدِ **موجود** — هیچ صفِ موازی. فقط شمارش، نه محتوا."""
    o = _opslib()
    out: dict = {"unknown": True}
    try:
        root = Path(o.ORG_ROOT) if o is not None else None
    except Exception:  # noqa: BLE001
        root = None
    if root is None:
        out["reason"] = "ORG_ROOT resolve نشد"
        return out
    # آینهٔ `approval_store._APPROVALS_JSON` — آن‌جا `_ROOT = _OPS.parent` است،
    # یعنی ریشهٔ vault و **نه** داخلِ `_ops`. نسخهٔ اولِ من یک `_ops` اضافه
    # داشت و بی‌صدا «degraded» می‌داد؛ خواننده را باید با نویسندهٔ واقعی سنجید.
    p = root / "_octopus" / "state" / "approvals.json"
    if not p.exists():
        # هنوز هیچ آیتمی واردِ صف نشده. این **نادانستن** نیست، یک واقعیت است —
        # ولی «۰ معطل» هم نیست: تا وقتی نویسنده‌ای ننوشته، عدد وجود ندارد.
        out["unknown"] = False
        out["queue_file"] = "absent"
        out["reason"] = "هیچ آیتمی هنوز واردِ صفِ تأیید نشده"
        return out
    data = _read_json(p)
    if not isinstance(data, dict):
        out["reason"] = "صفِ تأیید خوانا نیست"
        return out
    out["unknown"] = False
    out["age_minutes"] = _age_minutes(p)
    for key in ("pending", "approved", "rejected", "denied"):
        v = data.get(key)
        if isinstance(v, list):
            out[key] = len(v)
    return out


def halt() -> dict:
    """آیا چیزی متوقف است — مسیرِ توقف باید **همیشه** خوانده شود."""
    o = _opslib()
    out: dict = {"unknown": True}
    if o is None:
        out["reason"] = "opslib در دسترس نیست"
        return out
    red = _redactor()
    try:
        reason = o.halt_reason()
    except Exception:  # noqa: BLE001
        reason = None
    try:
        halted = bool(o.master_halted())
    except Exception:  # noqa: BLE001
        out["reason"] = "master_halted خطا داد"
        return out
    out["unknown"] = False
    out["halted"] = halted
    out["why"] = red(str(reason)) if reason else None
    return out


def governance() -> dict:
    """فاصلهٔ germline و سلامتِ بکاپ — از خودِ opslib، نه سندِ دستی."""
    o = _opslib()
    out: dict = {"unknown": True}
    if o is None:
        out["reason"] = "opslib در دسترس نیست"
        return out
    out["unknown"] = False
    for name, fn in (("germline_lag_hours", "germline_lag_hours"),
                     ("backup_health", "backup_health"),
                     ("gitwrite_failed", "gitwrite_failed")):
        try:
            out[name] = getattr(o, fn)()
        except Exception:  # noqa: BLE001
            out[name] = None
    return out


def snapshot() -> dict:
    """عکسِ واحد. هیچ‌چیز نمی‌نویسد، هیچ‌چیز اجرا نمی‌کند.

    `degraded` می‌گوید چند بخش نتوانستند جواب بدهند — سطح باید این را نشان دهد،
    وگرنه یک عکسِ نیمه‌کور به‌عنوانِ سلامت خوانده می‌شود."""
    o = _opslib()
    try:
        now = o.now_iso() if o is not None else datetime.now(timezone.utc).isoformat()
    except Exception:  # noqa: BLE001
        now = datetime.now(timezone.utc).isoformat()

    sections = {
        "processes": processes(),
        "boot_flags": boot_flags(),
        "queues": queues(),
        "halt": halt(),
        "governance": governance(),
    }
    degraded = sorted(k for k, v in sections.items()
                      if isinstance(v, dict) and v.get("unknown"))
    return {
        "schema": SCHEMA,
        "generated": now,
        "degraded": degraded,
        "sections": sections,
    }


if __name__ == "__main__":  # pragma: no cover
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(snapshot(), ensure_ascii=False, indent=1))
