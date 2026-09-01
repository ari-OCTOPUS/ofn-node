"""rotate_logs — چرخشِ فشردهٔ events.jsonl (GAPS-4) — با تایمرِ بکاپ می‌آید.

اگر events.jsonl از ۵MB بزرگ‌تر شد: به state/archive/events-<YYYYMM>.jsonl.gz
فشرده و فایلِ اصلی از نو شروع می‌شود. event_id ها append-only می‌مانند؛
چیزی حذف نمی‌شود.
"""
from __future__ import annotations

import gzip
import shutil
import sys
from pathlib import Path

HOME = Path.home()
EVENTS = HOME / "ofn/data/state/legs/lead-inbox/events.jsonl"
ARCHIVE = HOME / "ofn/data/state/archive"
THRESHOLD = 5 * 1024 * 1024


def rotate(path: Path = EVENTS, threshold: int = THRESHOLD) -> dict:
    try:
        size = path.stat().st_size
    except OSError:
        return {"note": "no-events-file"}
    if size < threshold:
        return {"size": size, "rotated": False}
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    import datetime as _dt
    stamp = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m")
    dest = ARCHIVE / f"events-{stamp}.jsonl.gz"
    i = 0
    while dest.exists():
        i += 1
        dest = ARCHIVE / f"events-{stamp}-{i}.jsonl.gz"
    tmp = path.with_suffix(".jsonl.rotating")
    shutil.move(str(path), str(tmp))
    with tmp.open("rb") as fin, gzip.open(dest, "wb", compresslevel=9) as fout:
        shutil.copyfileobj(fin, fout)
    tmp.unlink()
    path.touch()
    return {"rotated": True, "archived": str(dest), "was_bytes": size}


if __name__ == "__main__":
    print(rotate())
