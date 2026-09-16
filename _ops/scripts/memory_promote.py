#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""memory_promote.py — promotion pass for PENDING canonical-memory rows (A1 wiring).

PENDING = نویسندهٔ غیرسیستمیِ بدون ردپا. این ابزار هر PENDING را با رادارِ تناقض
می‌سنجد: پاک ⇒ ADMITTED؛ تناقض ⇒ QUARANTINED؛ هر تصمیم با رسید در
_ops/state/memory/admission-receipts.jsonl ثبت می‌شود (append-only).

Usage:
  python -X utf8 _ops/scripts/memory_promote.py list     # فقط نمایش
  python -X utf8 _ops/scripts/memory_promote.py run      # ارتقای واقعی
"""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "_ops/memory"))

import memory_store as MS
import contradiction_radar as CR
from admission import Admission, _now

DB = ROOT / "_ops/state/memory/memory.db"


def pending_rows(store):
    return store._conn.execute(
        "SELECT memory_id, content FROM memory WHERE admission_state='PENDING' "
        "ORDER BY created_at").fetchall()


def main(mode: str) -> int:
    store = MS.MemoryStore(path=DB)
    radar = CR.ContradictionRadar(store=store)
    adm = Admission(store, gate=None, radar=radar)
    rows = pending_rows(store)
    print(f"PENDING rows: {len(rows)}")
    promoted = quarantined = 0
    for mid, content in rows:
        if mode != "run":
            print("  ", mid, (content or "")[:70])
            continue
        flags = radar.check_against_store(new_content=content, new_memory_id=mid)
        if flags:
            store.quarantine(mid)
            quarantined += 1
            adm._receipt("QUARANTINED", {"trace_id": f"promote:{mid}", "content": (content or "")[:80]},
                         {"memory_id": mid, "flags": [str(f)[:80] for f in flags[:2]]})
        else:
            store._conn.execute(
                "UPDATE memory SET admission_state='ADMITTED' WHERE memory_id=? AND admission_state='PENDING'",
                (mid,))
            store._conn.commit()
            promoted += 1
            adm._receipt("ADMITTED", {"trace_id": f"promote:{mid}", "content": (content or "")[:80]},
                         {"memory_id": mid, "via": "memory_promote.run"})
    if mode == "run":
        print(f"promoted={promoted} quarantined={quarantined} remaining={len(pending_rows(store))}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "list"))
