#!/usr/bin/env python3
"""integration_receipt — نوشتنِ اتمیکِ رسیدِ ترجمه، داخلِ namespace خودمان.

عمداً از `opslib.LockedJson` استفاده نمی‌کند: آن ماژول امروز روی `_ops/state/`
با `WinError 5` شکست می‌خورد (VQ-OBS-REPLACE-001) و مرزِ ادغام نباید به
مشکلی که تشخیصش هنوز باز است گره بخورد.

و همان قاعدهٔ پلِ اقدام این‌جا هم برقرار است: **رسیدی که ننشیند، ترجمه‌ای است
که اثباتش وجود ندارد** — پس شکستِ نوشتن `ok=False` می‌دهد، نه هشدارِ بی‌صدا.

$0 · stdlib · فقط داخلِ namespace خودش می‌نویسد.
"""
from __future__ import annotations

import json
import os
from pathlib import Path


def atomic_write(path, text: str) -> dict:
    last = None
    for attempt in (1, 2):
        try:
            p = Path(path)
            p.parent.mkdir(parents=True, exist_ok=True)
            tmp = p.with_suffix(p.suffix + f".tmp{attempt}")
            tmp.write_text(text, encoding="utf-8")
            os.replace(tmp, p)
            return {"ok": True, "attempts": attempt}
        except OSError as e:
            last = f"{type(e).__name__}: {e}"
    return {"ok": False, "error": last}


def write(receipt: dict, *, out_dir, name: str = None) -> dict:
    rid = str(receipt.get("translation_id") or "unknown")
    safe = "".join(c if (c.isalnum() or c in "._-") else "_" for c in rid)[:80]
    p = Path(out_dir) / (name or f"{safe}.json")
    r = atomic_write(p, json.dumps(receipt, ensure_ascii=False, indent=1))
    return {"ok": r["ok"], "path": str(p) if r["ok"] else None,
            "error": r.get("error")}


def append_ledger(receipt: dict, *, ledger_path) -> dict:
    try:
        p = Path(ledger_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "a", encoding="utf-8") as f:
            f.write(json.dumps(receipt, ensure_ascii=False) + "\n")
        return {"ok": True}
    except OSError as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}
