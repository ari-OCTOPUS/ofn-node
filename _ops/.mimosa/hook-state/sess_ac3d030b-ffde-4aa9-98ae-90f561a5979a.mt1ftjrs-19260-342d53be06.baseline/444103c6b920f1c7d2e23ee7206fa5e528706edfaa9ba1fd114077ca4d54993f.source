#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ارزیاب هولداوت — DA-1-L1. تنها API عمومی: score(submissions) → aggregate.

پاسخ‌ها احتمالات [0,1] اند؛ نمره = بری‌ری (پایین‌تر بهتر). طلای آشکار
هرگز بیرون نمی‌آید — مقایسه روی هش(salt||y). نشتِ هر آیتم = صفر.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
_ITEMS = json.loads((HERE / "holdout_items.json").read_text(encoding="utf-8"))["items"]
_SALT = (HERE / "holdout.salt").read_text(encoding="utf-8").strip()


def _is_y(answer, gold_hash: str) -> bool:
    for y in ("0", "1"):
        h = hashlib.sha256(f"{_SALT}::{y}".encode("utf-8")).hexdigest()[:24]
        if h == gold_hash:
            return str(answer) == str(y) or (
                isinstance(answer, (int, float)) and (
                    (y == "1" and answer >= 0.5) or (y == "0" and answer < 0.5)))
    return False


def score(submissions: dict) -> dict:
    """submissions: {item_id: probability} → {n, brier} — فقط تجمیع."""
    n = 0
    s = 0.0
    for it in _ITEMS:
        p = submissions.get(it["item_id"])
        if p is None:
            continue
        try:
            p = min(1.0, max(0.0, float(p)))
        except (TypeError, ValueError):
            continue
        n += 1
        # بری‌ری از راه هش: y فقط به‌صورت 0/1 قابل-استنتاج از خود هش است
        for y in (0, 1):
            h = hashlib.sha256(f"{_SALT}::{y}".encode("utf-8")).hexdigest()[:24]
            if h == it["gold_hash"]:
                s += (p - y) ** 2
                break
    return {"n": n, "brier": round(s / n, 4) if n else None}


def items_observable() -> list[dict]:
    return [{"item_id": it["item_id"], **it["observable"]} for it in _ITEMS]
