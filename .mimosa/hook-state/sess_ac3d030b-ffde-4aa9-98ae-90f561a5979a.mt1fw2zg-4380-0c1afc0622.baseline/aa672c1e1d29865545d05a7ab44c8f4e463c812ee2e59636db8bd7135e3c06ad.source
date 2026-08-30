"""
brain/housekeeping.py — سقفِ هوشمندِ نگه‌داری (تصمیمِ کاربر: archive، نه حذف).

رشدِ بی‌سقفِ داده‌های خودمختار (یادداشتِ vault، فایلِ ریتم، الگو، رویداد) را مهار
می‌کند: قدیمی‌ترها به «آرشیو» منتقل می‌شوند — هیچ چیزی حذف نمی‌شود.

سقف‌ها (قابلِ‌تنظیم با env):
  HK_MAX_AUTO_NOTES   = 500   یادداشتِ خودکارِ فعال در vault (بقیه → آرشیو/)
  HK_MAX_RHYTHMS      = 500   فایلِ .npy فعال (بقیه → outputs/rhythms/archive/)
  HK_MAX_PATTERNS     = 1000  ردیفِ فعالِ patterns (بقیه → جدولِ patterns_archive)
  HK_MAX_EVENTS       = 5000  ردیفِ dashboard_events (بقیه → events_archive)

اسکن‌های vault (گراف/RAG/امضا) پوشه‌ی آرشیو را نادیده می‌گیرند، پس اثرِ فوری:
گرافِ سبک‌تر، indexِ کوچک‌تر، rerunِ سریع‌تر.
"""
from __future__ import annotations

import os
import sqlite3
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

ARCHIVE_DIRNAME = "آرشیو"

MAX_AUTO_NOTES = int(os.getenv("HK_MAX_AUTO_NOTES", "500"))
MAX_RHYTHMS = int(os.getenv("HK_MAX_RHYTHMS", "500"))
MAX_PATTERNS = int(os.getenv("HK_MAX_PATTERNS", "1000"))
MAX_EVENTS = int(os.getenv("HK_MAX_EVENTS", "5000"))
# فایل‌های خطیِ append-only که قبلاً هیچ سقفی نداشتند (رشدِ بی‌نهایت در لوپِ همیشه‌روشن):
MAX_PACKET_LINES = int(os.getenv("HK_MAX_PACKET_LINES", "2000"))   # decision_packets.jsonl
MAX_IDEA_LINES = int(os.getenv("HK_MAX_IDEA_LINES", "2000"))       # autonomous_ideas.md
MAX_PROPOSALS = int(os.getenv("HK_MAX_PROPOSALS", "200"))          # self_code_proposals/


def archive_vault_notes(cap: int = MAX_AUTO_NOTES) -> int:
    """یادداشت‌های خودکارِ قدیمیِ vault → زیرپوشه‌ی آرشیو (جابه‌جایی، نه حذف)."""
    from brain.vault_sync import ANALYSIS_DIR
    if not ANALYSIS_DIR.exists():
        return 0
    # فقط یادداشت‌های خودکار (🔍-…)؛ دست‌سازها هرگز جابه‌جا نمی‌شوند
    autos = sorted(
        (p for p in ANALYSIS_DIR.glob("*.md") if p.name.startswith("🔍")),
        key=lambda p: p.stat().st_mtime, reverse=True,
    )
    if len(autos) <= cap:
        return 0
    arch = ANALYSIS_DIR / ARCHIVE_DIRNAME
    arch.mkdir(exist_ok=True)
    moved = 0
    for p in autos[cap:]:
        try:
            p.rename(arch / p.name)
            moved += 1
        except Exception as e:
            logger.warning("archive note failed %s: %s", p.name, e)
    return moved


def archive_rhythms(cap: int = MAX_RHYTHMS) -> int:
    """فایل‌های .npy قدیمی → outputs/rhythms/archive/."""
    from data.rhythm_store import RHYTHM_DIR
    if not RHYTHM_DIR.exists():
        return 0
    npys = sorted(RHYTHM_DIR.glob("*.npy"),
                  key=lambda p: p.stat().st_mtime, reverse=True)
    if len(npys) <= cap:
        return 0
    arch = RHYTHM_DIR / "archive"
    arch.mkdir(exist_ok=True)
    moved = 0
    for p in npys[cap:]:
        try:
            p.rename(arch / p.name)
            moved += 1
        except Exception as e:
            logger.warning("archive rhythm failed %s: %s", p.name, e)
    return moved


def _columns(conn, table: str) -> list[str]:
    return [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]


def _archive_rows(table: str, cap: int, archive_table: str) -> int:
    """ردیف‌های قدیمیِ یک جدول → جدولِ آرشیو (کپی + حذف از فعال).

    مقاوم در برابرِ drift اسکیمای جدول: اگر جدولِ آرشیو قبلاً (پیش از افزودنِ
    ستونی مثلِ temporal_mi در مهاجرتِ B6) ساخته شده باشد، `INSERT ... SELECT *`
    با «۱۵ ستون ولی ۱۶ مقدار» شکست می‌خورد و آرشیو خاموش می‌ماند — یعنی سقفِ
    نگه‌داری هرگز اعمال نمی‌شود (جدول بی‌سقف رشد می‌کند). پس ابتدا ستون‌های
    جاافتاده‌ی آرشیو را با ALTER اضافه می‌کنیم (آرشیو، نه حذف: هیچ ستونی گم
    نمی‌شود) و سپس با فهرستِ صریحِ ستون‌های مشترک درج می‌کنیم.
    """
    from memory.store import DB_PATH
    conn = sqlite3.connect(str(DB_PATH))
    try:
        exists = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)
        ).fetchone()
        if not exists:
            return 0
        n = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        if n <= cap:
            return 0
        cutoff_id = conn.execute(
            f"SELECT id FROM {table} ORDER BY id DESC LIMIT 1 OFFSET ?", (cap - 1,)
        ).fetchone()[0]

        live_cols = _columns(conn, table)
        arch_exists = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (archive_table,)
        ).fetchone()
        if not arch_exists:
            conn.execute(f"CREATE TABLE {archive_table} AS "
                         f"SELECT * FROM {table} WHERE 0")
        else:
            # ستون‌های موجود در جدولِ زنده ولی غایب در آرشیو را اضافه کن.
            arch_cols = set(_columns(conn, archive_table))
            for col in live_cols:
                if col not in arch_cols:
                    conn.execute(
                        f'ALTER TABLE {archive_table} ADD COLUMN "{col}"')

        # درجِ صریحِ ستون‌های مشترک (پس از هم‌ترازی: همه‌ی live_cols موجودند).
        shared = [c for c in live_cols if c in set(_columns(conn, archive_table))]
        col_list = ", ".join(f'"{c}"' for c in shared)
        conn.execute(
            f"INSERT INTO {archive_table} ({col_list}) "
            f"SELECT {col_list} FROM {table} WHERE id < ?", (cutoff_id,))
        cur = conn.execute(f"DELETE FROM {table} WHERE id < ?", (cutoff_id,))
        conn.commit()
        return cur.rowcount
    finally:
        conn.close()


def trim_textfile(path: Path, cap: int) -> int:
    """فایلِ خطی (jsonl / md) را به cap خطِ آخر محدود می‌کند.

    خطوطِ قدیمی به «<نام>_archive<پسوند>» append می‌شوند — مطابقِ سیاستِ
    housekeeping: آرشیو، نه حذف. نوشتنِ اتمیک (tmp + os.replace).
    """
    try:
        if cap <= 0 or not path.exists():
            return 0
        lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
        if len(lines) <= cap:
            return 0
        overflow, keep = lines[:-cap], lines[-cap:]
        arch = path.parent / f"{path.stem}_archive{path.suffix}"
        with open(arch, "a", encoding="utf-8") as f:
            f.writelines(overflow)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text("".join(keep), encoding="utf-8")
        os.replace(tmp, path)
        return len(overflow)
    except Exception as e:
        logger.warning("trim_textfile failed for %s: %s", path, e)
        return 0


def archive_self_code_proposals(cap: int = MAX_PROPOSALS) -> int:
    """پوشه‌های قدیمیِ self_code_proposals → زیرپوشه‌ی آرشیو (جابه‌جایی، نه حذف).

    اجرای ماهانه صدها پیشنهاد می‌سازد؛ این رشد را مهار می‌کند (فقط پوشه‌های
    تصمیم‌گرفته‌شده آرشیو می‌شوند؛ pending_approval هرگز جابه‌جا نمی‌شود)."""
    from config.settings import OUTPUT_DIR
    base = OUTPUT_DIR / "self_code_proposals"
    if not base.exists():
        return 0
    import json as _json
    dirs = [d for d in base.iterdir() if d.is_dir() and d.name != ARCHIVE_DIRNAME]
    dirs.sort(key=lambda d: d.stat().st_mtime, reverse=True)
    if len(dirs) <= cap:
        return 0
    arch = base / ARCHIVE_DIRNAME
    arch.mkdir(exist_ok=True)
    moved = 0
    for d in dirs[cap:]:
        # pending را دست نزن (منتظرِ تأییدِ مالک)
        try:
            meta = _json.loads((d / "meta.json").read_text(encoding="utf-8"))
            if meta.get("status") == "pending_approval":
                continue
        except Exception:
            pass
        try:
            d.rename(arch / d.name)
            moved += 1
        except Exception as e:
            logger.warning("archive proposal failed %s: %s", d.name, e)
    return moved


def run_housekeeping() -> dict:
    """اجرای همه‌ی سقف‌ها. برمی‌گرداند: شمارِ جابه‌جاشده‌ها به تفکیک."""
    from config.settings import OUTPUT_DIR
    out = {
        "vault_notes": archive_vault_notes(),
        "rhythms": archive_rhythms(),
        "patterns": _archive_rows("patterns", MAX_PATTERNS, "patterns_archive"),
        "events": _archive_rows("dashboard_events", MAX_EVENTS, "events_archive"),
        "packet_lines": trim_textfile(OUTPUT_DIR / "decision_packets.jsonl",
                                      MAX_PACKET_LINES),
        "idea_lines": trim_textfile(OUTPUT_DIR / "autonomous_ideas.md",
                                    MAX_IDEA_LINES),
        "proposals": archive_self_code_proposals(),
    }
    # B15: پشتیبانِ روزانه‌ی وضعیتِ حیاتی (DB + strategy + frontier)؛ HK_BACKUP=0 خاموش
    try:
        from brain.backup import maybe_daily_backup
        out["backup"] = 1 if maybe_daily_backup() else 0
    except Exception as e:
        logger.warning("daily backup failed: %s", e)
        out["backup"] = 0
    total = sum(out.values())
    if total:
        logger.info("housekeeping archived: %s", out)
    return out


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(run_housekeeping())
