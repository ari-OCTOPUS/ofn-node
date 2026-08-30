#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""سازندهٔ بستهٔ هولداوت پنهان — DA-1-L1 (PHASE02 STEP2).

منبعِ برچسب‌دارِ واقعی: بک‌تستِ پیش‌ثبتِ وظیفهٔ سختِ رصدخانه (n=351، p و y).
خروجی: holdout_items.json — طلای آشکار هرگز در بسته نیست؛ فقط هش
sha256(salt||y) + فضای پاسخ احتمالاتی. salt در فایل جدا — مالکیت مالک
(README). قطعی/بازتولیدپذیر (seed ثابت)؛ حذف صفر — فقط انجماد.
"""
from __future__ import annotations

import hashlib
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = Path(r"C:/Users/Armin/Desktop/OCTOPUS-NBB-CP-WORKING/nbb-control-plane"
           r"/_ops/observatory/scripts/backtest-hardtask-results.json")
SEED = 20260816
N_ITEMS = 60   # نمونهٔ کافی برای تفکیک بری‌ری؛ بقیه برای هولداوت‌های بعدی می‌ماند


def _gold_hash(salt: str, y) -> str:
    return hashlib.sha256(f"{salt}::{y}".encode("utf-8")).hexdigest()[:24]


def main() -> int:
    rng = random.Random(SEED)
    salt = f"holdout-salt-{rng.getrandbits(64):016x}"
    rows = json.loads(SRC.read_text(encoding="utf-8"))["rows"]
    rng.shuffle(rows)
    picked = rows[:N_ITEMS]
    items = [{
        "item_id": f"h-{i:03d}",
        "observable": {"date": r.get("date")},     # فقط شناسهٔ رویداد
        "gold_hash": _gold_hash(salt, r["y"]),
        "answer_space": "probability:[0,1]",
    } for i, r in enumerate(picked)]
    (HERE / "holdout_items.json").write_text(
        json.dumps({"schema": "octopus-holdout/1", "n": len(items),
                    "created": "2026-08-16", "seed": SEED, "source": "hardtask-backtest",
                    "items": items}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    (HERE / "holdout.salt").write_text(salt, encoding="utf-8")
    # نگاشت داخلی برای داوری خودمان (بیرون از بستهٔ عمومی): yهای واقعی همان‌جا
    (HERE / "gold.local-only.json").write_text(
        json.dumps({it["item_id"]: r["y"] for it, r in zip(items, picked)}),
        encoding="utf-8")
    print(f"holdout frozen: {len(items)} items از {len(rows)}؛ salt + gold محلی جدا شد")
    return 0


if __name__ == "__main__":
    sys.exit(main())
