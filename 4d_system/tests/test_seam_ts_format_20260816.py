"""test_seam_ts_format_20260816.py — SEAM-LOOP فاز ۱-۳ (مصوب مالک).

قفلِ رگرسیونِ فرمت timestamp نویسندهٔ hypotheses:
نویسندهٔ فعلی (پس از R16) `isoformat(timespec='seconds')` روی datetimeِ
offset-دار می‌نویسد = همیشه `\d+00:00` و بدون میکروثانیه.
رسوبِ ۳۸۲ ردیفِ ژوئیه (naive + میکروثانیهٔ ۵/۶رقمی) محصولِ نویسندهٔ قدیمی
است؛ این تست تضمین می‌کند نویسندهٔ جدید هرگز به آن فرمت برنگردد — چون هر
مصرف‌کنندهٔ fromisoformat با naive/aware و کسریِ ناقص می‌شکند (سه عددِ غلط
در گاوج median همان روز، سند زنده‌اش).

(نکتهٔ محیط: DB_PATH ماژول-سطحی است؛ با monkeypatch به فایلِ tmp هدایت
می‌شود — DB زنده هرگز لمس نمی‌شود.)
"""
import re
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from memory import store  # noqa: E402

ISO_AWARE_SECONDS = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+00:00$")


def test_writer_timestamp_format(monkeypatch, tmp_path):
    db = tmp_path / "t.db"
    monkeypatch.setattr(store, "DB_PATH", db)
    store._ensure_db()
    rid = store.save_hypothesis("test-domain", "seam-1-3 format lock", "unit")
    assert rid and db.exists()
    conn = sqlite3.connect(str(db))
    ts = conn.execute(
        "SELECT timestamp FROM hypotheses WHERE id = ?", (rid,)).fetchone()[0]
    conn.close()
    assert ISO_AWARE_SECONDS.match(ts), f"فرمت نویسنده برگشت/خراب شد: {ts!r}"
    d = datetime.fromisoformat(ts)          # مصرف‌کنندهٔ استاندارد نباید بشکند
    assert d.tzinfo is not None, "naive ممنوع — تلهٔ تفریق aware/naive"
