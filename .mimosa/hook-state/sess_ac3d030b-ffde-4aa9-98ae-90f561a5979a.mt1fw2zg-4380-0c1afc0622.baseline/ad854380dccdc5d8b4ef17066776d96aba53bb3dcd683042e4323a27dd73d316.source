"""
rollback.py — بکاپ و بازگردانیِ امن قبل از هر تغییرِ ریسکی.

پیش از اعمالِ هر patch یا migrationِ بزرگ، یک snapshot گرفته می‌شود تا اگر
چیزی خراب شد، بتوان برگشت. فقط فایل (هیچ اجرای کد).
"""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path


def backup_file(path: str | Path, backup_dir: str | Path = "backups") -> str | None:
    """یک کپیِ زمان‌دار از فایل می‌گیرد. مسیرِ بکاپ را برمی‌گرداند (یا None)."""
    src = Path(path)
    if not src.exists():
        return None
    bdir = Path(backup_dir)
    bdir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    dest = bdir / f"{src.name}.{stamp}.bak"
    shutil.copy2(src, dest)
    return str(dest)


def restore_file(backup_path: str | Path, target: str | Path) -> bool:
    """یک بکاپ را روی مقصد بازمی‌گرداند."""
    bp = Path(backup_path)
    if not bp.exists():
        return False
    shutil.copy2(bp, Path(target))
    return True
