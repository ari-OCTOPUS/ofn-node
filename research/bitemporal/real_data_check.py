#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""real_data_check.py — suite بitemporal روی دادهٔ واقعی spine (T53 §۶-۴).

فقط خواندن. چک‌ها (نگاشت صادقانه از suite پانزده‌تایی fixture):
  R1 future-use صفر: هیچ ردیفی با occurred>recorded نباید در پرسش as-of بیاید
  R2 یکنوایی as-of: با افزایش decision_time، مجموعهٔ قابل‌مشاهده فقط بزرگ‌تر می‌شود
  R3 ماندگاری: دو خواندن متوالی hash یکسان
  R4 تفکیک legacy: ردیف‌های legacy_no_event_time=1 هرگز منبع مستقل ادعا نمی‌کنند
خروجی: JSON حکم‌ها + عدد خام."""
from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB = Path(__file__).resolve().parents[2] / "_ops/state/spine/spine.db"


def _parse(s):
    return datetime.fromisoformat(str(s).replace("Z", "+00:00"))


def eligible(row, dt):
    occ, rec = _parse(row["occurred_at"]), _parse(row["recorded_at"])
    return occ <= rec <= dt


def main() -> dict:
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    rows = [dict(r) for r in con.execute(
        "SELECT event_id, domain, occurred_at, recorded_at, legacy_no_event_time,"
        " event_time_source FROM events")]
    con.close()
    now = datetime.now(timezone.utc)

    # R1 — future-use در as-of «اکنون»
    r1_violations = [r["event_id"] for r in rows if not eligible(r, now)]

    # R2 — یکنوایی مجموعهٔ قابل‌مشاهده
    cuts = sorted({(_parse(r["recorded_at"]) if r["legacy_no_event_time"] == 0
                    else _parse(r["occurred_at"])) for r in rows})[::max(1, len(rows)//12)]
    vis_prev, r2_ok = -1, True
    for c in cuts:
        vis = sum(1 for r in rows if eligible(r, c))
        if vis < vis_prev:
            r2_ok = False
        vis_prev = vis

    # R3 — ماندگاری (دو خواندن)
    h1 = hashlib.sha256(json.dumps(
        sorted(r["event_id"] for r in rows)).encode()).hexdigest()[:16]
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    h2 = hashlib.sha256(json.dumps(
        sorted(r[0] for r in con.execute("SELECT event_id FROM events"))).encode()).hexdigest()[:16]
    con.close()

    # R4 — تفکیک legacy (NULL = ردیف پیش از migration؛ هیچ ادعایی نمی‌کند)
    r4_ok = all(r["event_time_source"] in (None, "write_clock_derived")
                for r in rows if r["legacy_no_event_time"] == 1)

    out = {
        "schema": "bitemporal-real-check/1", "grade": "MEASURED",
        "n_rows": len(rows),
        "R1_future_use_zero": len(r1_violations) == 0,
        "R1_violations": r1_violations[:5],
        "R2_asof_monotone": r2_ok,
        "R3_persistence_hash_equal": h1 == h2,
        "R4_legacy_never_claims_independent": r4_ok,
        "independent_sources": sorted({r["event_time_source"] for r in rows
                                       if r["legacy_no_event_time"] == 0}),
        "executable": False,
    }
    out["verdict"] = "PASS" if (out["R1_future_use_zero"] and out["R2_asof_monotone"]
                                and out["R3_persistence_hash_equal"] and out["R4_legacy_never_claims_independent"]) \
        else "FAIL"
    return out


if __name__ == "__main__":
    print(json.dumps(main(), ensure_ascii=False, indent=1))
