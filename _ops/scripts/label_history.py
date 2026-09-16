#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""label_history.py — hash-chain helper for _ops/state/label-history.jsonl.

Closes audit VOID-item A4 (history append-only+parseable but NOT hash-linked).
Going forward every entry appended via this script carries entry_hash and
prev_hash; verify() validates the chain and (backwards-compatibly) skips
pre-anchor legacy rows.

Usage:
  python -X utf8 _ops/scripts/label_history.py verify
  python -X utf8 _ops/scripts/label_history.py append '{"label_id":..., ...}'  (json)
"""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path

HIST = Path(__file__).resolve().parents[2] / "_ops/state/label-history.jsonl"
SCHEMA = "label-history/2"


def _rows():
    if not HIST.exists():
        return []
    return [json.loads(l) for l in HIST.read_text(encoding="utf-8").splitlines() if l.strip()]


def _entry_hash(rec: dict) -> str:
    body = {k: rec.get(k) for k in sorted(rec) if k not in ("entry_hash",)}
    return hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":")).encode()).hexdigest()


def append(record: dict) -> dict:
    rows = _rows()
    prev = next((r["entry_hash"] for r in reversed(rows) if r.get("entry_hash")), None)
    rec = {"schema": SCHEMA, "prev_hash": prev, **record}
    rec["entry_hash"] = _entry_hash(rec)
    HIST.open("a", encoding="utf-8").write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


def verify() -> int:
    rows = _rows()
    chained, bad, prev = 0, 0, None
    for r in rows:
        if not r.get("entry_hash"):
            continue  # legacy pre-anchor row — parseable, skipped by chain
        if _entry_hash(r) != r["entry_hash"]:
            bad += 1
            print("HASH FAIL:", r.get("label_id"), r.get("ts_utc"))
        elif prev is not None and r.get("prev_hash") != prev:
            bad += 1
            print("CHAIN BREAK:", r.get("label_id"), r.get("ts_utc"))
        else:
            chained += 1
        prev = r.get("entry_hash")
    print(f"rows={len(rows)} chained_ok={chained} legacy={len(rows)-chained-bad} bad={bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "verify":
        sys.exit(verify())
    if len(sys.argv) >= 3 and sys.argv[1] == "append":
        print(json.dumps(append(json.loads(sys.argv[2])), ensure_ascii=False))
        sys.exit(0)
    print(__doc__)
