"""
brain/backup.py — B15: پشتیبانِ دوره‌ای وضعیتِ حیاتی (روتیشن‌دار).

چه چیزی: DB اصلی (4d_experiments.db — آزمایش‌ها/الگوها/فرضیه‌ها) + frontier.json
+ strategy.json — یعنی کلِ «حافظه و هویتِ» سیستم که تک‌نسخه بود.
چه چیزی نه: فایل‌های .npy ریتم‌ها (حجیم و بازتولیدپذیر از DB/کاتالوگ).

طراحی:
  • sqlite3 backup API — سازگار با WAL و نویسنده‌ی هم‌زمان (snapshot سازگار).
  • روزی حداکثر یک‌بار (marker تاریخ‌دار) — از housekeeping صدا زده می‌شود.
  • روتیشن: فقط HK_BACKUP_KEEP نسخه‌ی آخر می‌ماند (پیش‌فرض ۵).
  • خاموش‌کردن: HK_BACKUP=0
"""
from __future__ import annotations

import os
import shutil
import sqlite3
import logging
from datetime import date
from pathlib import Path

logger = logging.getLogger(__name__)

BACKUP_ENABLED = os.getenv("HK_BACKUP", "1") == "1"
BACKUP_KEEP = int(os.getenv("HK_BACKUP_KEEP", "5"))


def _backup_dir() -> Path:
    from config.settings import OUTPUT_DIR
    d = OUTPUT_DIR / "backups"
    d.mkdir(parents=True, exist_ok=True)
    return d


def backup_now(tag: str | None = None) -> Path | None:
    """یک snapshot کامل می‌گیرد. برمی‌گرداند مسیرِ پوشه‌ی backup یا None."""
    try:
        from memory.store import DB_PATH
        from config.settings import OUTPUT_DIR

        stamp = tag or date.today().isoformat()
        dest = _backup_dir() / stamp
        dest.mkdir(parents=True, exist_ok=True)

        # ۱) DB با backup API (نه copy — تا وسطِ نوشتنِ WAL هم سازگار باشد)
        if Path(DB_PATH).exists():
            src = sqlite3.connect(str(DB_PATH))
            try:
                dst = sqlite3.connect(str(dest / Path(DB_PATH).name))
                try:
                    src.backup(dst)
                finally:
                    dst.close()
            finally:
                src.close()

        # ۲) فایل‌های کوچکِ هویتی
        for rel in ("self_evolved/strategy.json",
                    "self_evolved/frontier.json"):
            p = OUTPUT_DIR / rel
            if p.exists():
                shutil.copy2(p, dest / p.name)

        _rotate()
        logger.info("backup written: %s", dest)
        return dest
    except Exception as e:
        logger.warning("backup failed: %s: %s", type(e).__name__, e)
        return None


def _rotate(keep: int | None = None) -> int:
    """پوشه‌های backup قدیمی‌تر از keep نسخه‌ی آخر حذف می‌شوند."""
    keep = BACKUP_KEEP if keep is None else keep
    try:
        dirs = sorted((p for p in _backup_dir().iterdir() if p.is_dir()),
                      key=lambda p: p.name, reverse=True)
        removed = 0
        for p in dirs[max(keep, 1):]:
            shutil.rmtree(p, ignore_errors=True)
            removed += 1
        return removed
    except Exception:
        return 0


def maybe_daily_backup() -> Path | None:
    """حداکثر یک backup در روز — برای فراخوانی از housekeeping (لوپِ همیشه‌روشن)."""
    if not BACKUP_ENABLED:
        return None
    marker = _backup_dir() / ".last_backup_date"
    today = date.today().isoformat()
    try:
        if marker.exists() and marker.read_text(encoding="utf-8").strip() == today:
            return None
    except Exception:
        pass
    dest = backup_now(tag=today)
    if dest is not None:
        try:
            marker.write_text(today, encoding="utf-8")
        except Exception:
            pass
    return dest


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("backup:", backup_now(tag="manual"))
