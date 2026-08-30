"""status_banner.py — بنرِ پیشگیرانهٔ وضعیت برای چت (صداقتِ چت، TASK 4).

یک جملهٔ واحدِ فقط‌خواندنی که می‌گوید آیا ارگانیسم متوقف / سهمیه‌تمام / کهنه است —
**بدونِ هیچ تماسِ پولی**. ساخته‌شده از فایل‌های فقط‌خواندنی:
  - STOP/HALT flags (HALT-ALL · STOP-ORGANISM · STOP-CORTEX) با mtime‌ی «از کِی»
  - fugu_quota.status() (remaining / cap / used_total / killed)
وقتی همه سالم‌اند → text="" و level="ok" (بنری نیست که نمایش داده شود).

قراردادِ خروجی:
    {"level": "ok"|"warn"|"halt", "text": str, "halted": bool,
     "halt_reason": str|None, "quota": dict|None}
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Optional, Tuple

HERE = Path(__file__).resolve().parent
_OPS = HERE.parent                  # _ops
_CORTEX = _OPS / "cortex"

# پرچم‌های stopِ مرتبط با چت (به‌ترتیبِ اولویت).
_STOP_FLAGS = (
    ("HALT-ALL", "HALT-ALL"),
    ("STOP-ORGANISM", "STOP-ORGANISM"),
    ("STOP-CORTEX", "STOP-CORTEX"),
)


def _detect_stop(ops_dir: Path) -> Tuple[Optional[str], Optional[float]]:
    """اولین پرچمِ stopِ فعال را برگردان: (reason, mtime). هیچ‌کدام → (None, None)."""
    for reason, name in _STOP_FLAGS:
        p = Path(ops_dir) / name
        try:
            if p.exists():
                try:
                    return reason, p.stat().st_mtime
                except OSError:
                    return reason, None
        except OSError:
            continue
    return None, None


def _fmt_since(mtime: Optional[float], now: float) -> str:
    """«از X پیش» — خلاصه‌شده به s/min/h."""
    if mtime is None:
        return ""
    age = max(0.0, now - mtime)
    if age < 60:
        return f"{int(age)}s"
    if age < 3600:
        return f"{int(age // 60)}min"
    return f"{int(age // 3600)}h"


def _quota_status() -> Optional[dict]:
    """fugu_quota.status() به‌صورتِ best-effort (None اگر import نشد)."""
    import sys as _sys
    if str(_CORTEX) not in _sys.path:
        _sys.path.insert(0, str(_CORTEX))
    try:
        import fugu_quota as _fq  # noqa: WPS433
        return _fq.status()
    except Exception:  # noqa: BLE001 — بنر نباید شکستِ import را به خطا تبدیل کند
        return None


def status_banner(*, now: Optional[float] = None,
                  ops_dir=None,
                  quota: Optional[dict] = None) -> dict:
    """بنرِ وضعیت — فقط‌خواندنی، بدونِ تماسِ پولی.

    `ops_dir`: دایرکتوری برای دیدنِ پرچم‌های STOP (پیش‌فرض _ops). برای تست: یک tmp dir.
    `quota`:   اگر داده شود، همان استفاده می‌شود (برای تست)؛ وگرنه fugu_quota.status() خوانده می‌شود.
    """
    now = now if now is not None else time.time()
    ops = Path(ops_dir) if ops_dir else _OPS
    parts = []
    level = "ok"

    # ۱) پرچم‌های stop/halt
    reason, mtime = _detect_stop(ops)
    if reason:
        level = "halt"
        when = f"، از {_fmt_since(mtime, now)} پیش" if mtime else ""
        parts.append(f"🔴 ارگانیسم متوقف است ({reason}{when})")

    # ۲) سهمیهٔ مدل پولی
    if quota is None:
        quota = _quota_status()
    if quota and (quota.get("killed") or (quota.get("remaining", 1) or 0) <= 0):
        if level != "halt":
            level = "warn"
        parts.append(
            f"⚠️ سهمیهٔ مدل پولی تمام ({quota.get('used_total', 0)}/"
            f"{quota.get('cap', 0)}) — تا نیمه‌شب UTC ریست"
        )

    return {
        "level": level,
        "text": " · ".join(parts),
        "halted": bool(reason),
        "halt_reason": reason,
        "quota": quota,
    }


if __name__ == "__main__":
    import json as _json
    print(_json.dumps(status_banner(), ensure_ascii=False, indent=2))
