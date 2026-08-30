"""shadow_log.py — لاگ‌گر سایه‌ای m (بدون هیچ گیتِ فعالی — فقط مشاهده).

هر فراخوانی: m را با فراداده در _ops/state/margin-shadow.jsonl می‌نویسد.
fail-soft: خطای نوشتن هرگز caller را نمی‌کشد."""
from __future__ import annotations

import json
import time
from pathlib import Path

LOG = Path(__file__).resolve().parents[1] / "state" / "margin-shadow.jsonl"


def log_m(source: str, m: float, **meta) -> bool:
    rec = {"ts": time.time(), "source": source, "m": round(float(m), 4), **meta}
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with LOG.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        return True
    except OSError:
        return False
