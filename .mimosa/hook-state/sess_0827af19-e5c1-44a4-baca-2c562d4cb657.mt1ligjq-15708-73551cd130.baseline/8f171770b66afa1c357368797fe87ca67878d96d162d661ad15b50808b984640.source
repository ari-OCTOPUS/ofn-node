#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""گزارشِ صفِ فرضیه‌ها — R16 قدمِ صفر (فقط-خواندن، 2026-08-16).

هیچ تغییری در DB نمی‌دهد. خروجی: توزیعِ سن/دامنه + آنچه تحتِ سیاستِ
dormancy (۹۰روز، v1 پیشنهادی) برچسب می‌خورد + خانواده‌های تکراریِ تقریبی.
مبنای تصمیمِ مالک برای نسخهٔ قطعیِ سیاست.
"""
from __future__ import annotations

import re
import sqlite3
import sys
from collections import Counter
from datetime import datetime, timezone

DB = r"F:/backup/4d_system/outputs/4d_experiments.db"
DORMANCY_DAYS = 90


def main() -> int:
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    rows = con.execute(
        "SELECT id, timestamp, domain, hypothesis FROM hypotheses"
    ).fetchall()
    con.close()

    now = datetime.now(timezone.utc)
    domains = Counter()
    would_dormant = 0
    fam_counter: Counter[str] = Counter()
    for hid, ts, domain, hyp in rows:
        domains[domain or "؟"] += 1
        try:
            t = datetime.fromisoformat((ts or "").replace("Z", "+00:00"))
            if t.tzinfo is None:
                t = t.replace(tzinfo=timezone.utc)
            if (now - t).days > DORMANCY_DAYS:
                would_dormant += 1
        except ValueError:
            pass
        key = re.sub(r"\s+", " ", (hyp or "").lower())[:80]
        fam_counter[f"{domain or '؟'}::{key}"] += 1

    dupes = {k: n for k, n in fam_counter.items() if n > 1}

    print(f"کل: {len(rows)} فرضیه (همه pending، tested=0)")
    print(f"دامنه‌ها: {dict(domains.most_common(8))}")
    print(f"زیرِ سیاستِ dormancy({DORMANCY_DAYS}d) می‌رفت: {would_dormant}")
    print(f"خانواده‌های تکراریِ تقریبی (prefix-80): {len(dupes)} "
          f"({sum(dupes.values()) - len(dupes)} ردیفِ معناییِ اضافی)")
    if dupes:
        for k, n in list(dupes.items())[:5]:
            print(f"  ×{n}  {k[:70]}")
    print("\n(این گزارش چیزی تغییر نداد — سیاستِ v1 در "
          "02-DECISIONS/DECISION-ARTIFACTS-2026-08-16/ منتظر رأی مالک است)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
