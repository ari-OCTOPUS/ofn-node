#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""learning_evaluator.py — ارزیابِ یادگیری با baseline منجمد و holdout جدا (CL01-P5).

قرارداد خروجی — فقط یکی از دو برچسب:
  LEARNING_VERIFIED                فقط اگر: بعد < قبل روی holdout (Brier با حدِ
                                   min_delta) و پوشش provenance ≥ حداقل.
  MEMORY_LIVE_LEARNING_UNVERIFIED  هر حالت دیگر — از جمله «هنوز پنجرهٔ live نیست».

خام بودن بدون شاهد هرگز VERIFIED نمی‌سازد؛ سکوتِ معیار = UNVERIFIED.
"""
from __future__ import annotations

import hashlib
import json
import random
import sqlite3
from pathlib import Path

SCHEMA = "learning-evaluator.v1"
MIN_BRIER_DELTA = 0.0   # بهبود باید اکیداً مثبت باشد
MIN_PROVENANCE_COVERAGE = 0.9


def _sha(obj) -> str:
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True,
                                     default=str).encode("utf-8")).hexdigest()


def freeze_baseline(metrics: dict, out_path) -> dict:
    """baseline را منجمد می‌کند: artifact + هش کناری (قرارداد خانه: هشِ خودِ فایل کنار فایل)."""
    art = {"schema": SCHEMA, "kind": "frozen-baseline", "metrics": metrics,
           "evaluation_contract": {"min_brier_delta": MIN_BRIER_DELTA,
                                   "min_provenance_coverage": MIN_PROVENANCE_COVERAGE}}
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(art, ensure_ascii=False, indent=1), encoding="utf-8")
    (Path(str(out_path) + ".sha256")).write_text(
        hashlib.sha256(out_path.read_bytes()).hexdigest() + "  " + out_path.name, encoding="utf-8")
    return art


def holdout_split(ids: list, seed: int = 20260818, ratio: float = 0.3) -> dict:
    """تقسیم قطعیِ و مستندِ holdout — عضویت تغییرناپذیر (seed ثابت، مرتب‌سازی پایدار)."""
    ids = sorted(str(i) for i in ids)
    rng = random.Random(seed)
    shuffled = ids[:]
    rng.shuffle(shuffled)
    n_hold = max(0, int(round(len(shuffled) * ratio)))
    hold = sorted(shuffled[:n_hold])
    train = sorted(shuffled[n_hold:])
    doc = {"schema": SCHEMA, "kind": "holdout-membership", "seed": seed, "ratio": ratio,
           "n_total": len(ids), "n_holdout": len(hold), "n_train": len(train),
           "holdout_ids": hold}
    doc["membership_sha256"] = _sha(hold)
    return doc


def brier_from_ledger(ledger) -> float | None:
    """Brier روی جفت‌های (confidence, hit) — None یعنی «داده‌ای نیست، ادعا ممنوع»."""
    rows: list[tuple[float, int]] = []
    with ledger._conn() as c:  # noqa: SLF001 — ابزار ارزیابِ خودِ دفتر
        for pid, conf in c.execute("SELECT prediction_id, confidence FROM predictions"):
            outs = ledger.outcomes(pid)
            if not outs:
                continue
            text = " ".join(o["outcome"].lower() for o in outs)
            if "hit" in text or "true" in text or "ok:" in text:
                y = 1
            elif "miss" in text or "false" in text or "fail" in text:
                y = 0
            else:
                continue
            rows.append((float(conf), y))
    if not rows:
        return None
    return sum((p - y) ** 2 for p, y in rows) / len(rows)


def provenance_coverage(store_path) -> dict:
    """پوششٔ provenance/timestamp/confidence/expiry ردیف‌های ADMITTED یک MemoryStore (فقط‌خواندن).
    اسکیمای واقعی: memory_id · provenance_json · created_at · confidence · valid_to."""
    con = sqlite3.connect(f"file:{store_path}?mode=ro", uri=True)
    try:
        rows = con.execute(
            "SELECT COUNT(*),"
            " SUM(CASE WHEN provenance_json IS NOT NULL AND provenance_json != '' THEN 1 ELSE 0 END),"
            " SUM(CASE WHEN created_at IS NOT NULL AND created_at != '' THEN 1 ELSE 0 END),"
            " SUM(CASE WHEN confidence IS NOT NULL AND confidence != '' THEN 1 ELSE 0 END),"
            " SUM(CASE WHEN valid_to IS NOT NULL AND valid_to != '' THEN 1 ELSE 0 END)"
            " FROM memory WHERE admission_state='ADMITTED'").fetchone()
    except sqlite3.OperationalError:
        return {"admitted": 0, "coverage": None, "note": "schema-miss"}
    finally:
        con.close()
    n, p, t, c, e = (rows[0] or 0), (rows[1] or 0), (rows[2] or 0), (rows[3] or 0), (rows[4] or 0)
    if not n:
        return {"admitted": 0, "coverage": None, "note": "no-admitted-rows"}
    return {"admitted": n, "provenance": round(p / n, 4), "timestamp": round(t / n, 4),
            "confidence": round(c / n, 4), "expiry": round(e / n, 4),
            "coverage": round((p + t + c + e) / (4 * n), 4)}


def decide(before: dict | None, after: dict | None) -> dict:
    reasons = []
    if before is None or after is None:
        reasons.append("metrics unavailable (no live window / empty ledger)")
        label = "MEMORY_LIVE_LEARNING_UNVERIFIED"
    else:
        b0, b1 = before.get("brier"), after.get("brier")
        cov = after.get("provenance_coverage", {}).get("coverage")
        if b0 is None or b1 is None:
            label = "MEMORY_LIVE_LEARNING_UNVERIFIED"
            reasons.append("brier missing on one side")
        elif (b0 - b1) > MIN_BRIER_DELTA and (cov is not None and cov >= MIN_PROVENANCE_COVERAGE):
            label = "LEARNING_VERIFIED"
            reasons.append(f"brier {b0:.4f}->{b1:.4f}; coverage={cov}")
        else:
            label = "MEMORY_LIVE_LEARNING_UNVERIFIED"
            reasons.append(f"brier {b0}->{b1}; coverage={cov} (thresholds not met)")
    return {"schema": SCHEMA, "label": label, "reasons": reasons}
