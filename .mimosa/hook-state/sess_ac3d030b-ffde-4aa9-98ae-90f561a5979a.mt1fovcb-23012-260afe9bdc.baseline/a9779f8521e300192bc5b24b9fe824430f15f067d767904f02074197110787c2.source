"""epoch_guard — پنجرهٔ «هر N ضربان» که ری‌استارت آن را صفر نکند.

مسئله‌ای که این ماژول می‌بندد، ۲۰۲۶-۰۷-۲۸ با اندازه‌گیری پیدا شد:

`wiring.py` شش حالتِ **ماژول‌سطح** دارد که آخرین پنجرهٔ شلیک‌شده را نگه می‌دارند —
`_INGEST_STATE` · `_HEART_STATE` · `_ACCT_STATE` · `_NUDGE_STATE` ·
`_HEARTBEAT_STATE` · `_DISCOVERY_STATE` (و `_consolidation_epoch_fired` داخلِ
`neural_stack`). همه در **حافظه**‌اند. هر ری‌استارت صفرشان می‌کند، پس اولین تیکِ
بعد از هر بوت شرطِ `epoch <= last_epoch` را رد می‌کند و **همهٔ شش کادنس با هم
شلیک می‌کنند** — صرف‌نظر از اینکه پنجره‌شان واقعاً رسیده باشد یا نه.

نشانه‌ای که به آن رسیدیم: کارتِ «نیازت دارم» با تناوبِ **۶ ساعت** چهار بار در یک
ساعت آمد. تناوب درست بود؛ ری‌استارت‌ها آن را دور می‌زدند.

چرا این بدتر از یک باگِ ساده است: از بیرون شبیهِ «سیستم پرحرف است» به نظر
می‌رسد، نه شبیهِ نقص. و هر کسی که برای رفعش تناوب را بلندتر کند، مشکل را
عمیق‌تر می‌کند — چون علت تناوب نیست، **فراموشی هنگام بوت** است.

مرزها
─────
· فلگ خاموش (پیش‌فرض) → `already_fired` همیشه False برمی‌گرداند، یعنی رفتارِ
  امروز بایت‌به‌بایت. صداکننده همچنان چکِ حافظه‌ایِ خودش را دارد.
· هیچ‌چیز نمی‌فرستد، هیچ تصمیمی نمی‌گیرد. فقط «این پنجره قبلاً شلیک شد؟».
· fail-soft: هر خطای دیسک → False (یعنی اجازهٔ شلیک). گم‌شدنِ یک کارت بدتر از
  یک کارتِ اضافه است، پس شکست به سمتِ **گفتن** می‌افتد نه سکوت.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE), str(_HERE / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib  # noqa: E402

FLAG = "OCTOPUS_EPOCH_GUARD_DISK"


def enabled() -> bool:
    return str(os.environ.get(FLAG, "") or "").strip().lower() in (
        "1", "true", "yes", "on")


def _path() -> Path:
    return Path(opslib.STATE_DIR) / "epoch-guard.json"


def _load() -> dict:
    try:
        d = json.loads(_path().read_text("utf-8"))
        return d if isinstance(d, dict) else {}
    except Exception:  # noqa: BLE001 — نبودِ فایل/JSONِ خراب = هنوز چیزی شلیک نشده
        return {}


def already_fired(name: str, epoch: int) -> bool:
    """آیا این پنجره برای این کادنس قبلاً شلیک شده — حتی پیش از ری‌استارت؟"""
    if not enabled():
        return False                      # فلگ خاموش = رفتارِ قبلی
    try:
        return int(_load().get(str(name), -1)) >= int(epoch)
    except (TypeError, ValueError):
        return False


def mark_fired(name: str, epoch: int) -> bool:
    """این پنجره را شلیک‌شده ثبت کن. برمی‌گرداند: آیا نوشته شد."""
    if not enabled():
        return False
    try:
        p = _path()
        p.parent.mkdir(parents=True, exist_ok=True)
        with opslib.LockedJson(p) as lj:
            d = _load()
            prev = d.get(str(name))
            if prev is not None and int(prev) >= int(epoch):
                return False              # عقب نرو
            d[str(name)] = int(epoch)
            lj.write(d)
        return True
    except Exception:  # noqa: BLE001 — ثبت‌نشدن هرگز کادنس را نمی‌کشد
        return False


def card() -> str:
    """کارتِ وضعیت — برای `/x`."""
    if not enabled():
        return ("⏱ <b>پنجرهٔ کادنس — حافظهٔ دیسکی</b>\n"
                f"خاموش. روشن‌کردن: <code>OWNER_AUTH: ARM FLAG {FLAG}</code>\n"
                "خاموش یعنی هر ری‌استارت همهٔ کادنس‌ها را یک‌بار بی‌قید شلیک می‌کند.")
    d = _load()
    if not d:
        return "⏱ <b>پنجرهٔ کادنس</b> · روشن — هنوز چیزی ثبت نشده."
    rows = "\n".join(f"• <code>{k}</code>: پنجرهٔ {v}" for k, v in sorted(d.items())[:10])
    return f"⏱ <b>پنجرهٔ کادنس</b> · روشن · {len(d)} کادنس\n{rows}"
