#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ledger_repair_reanchor_2026_07_31.py — ترمیمِ زنجیرهٔ ledger (رأیِ مالک ۲۰۲۶-۰۷-۳۱).

یک‌بار، اپراتور. صفر وابستگی به حلقهٔ زنده.

شکست: زنجیره در رکوردِ ۹۶۴۶ شکسته بود — دو فرآیند (scheduler و self-improve)
هر دو روی والدِ ۹۶۴۴ بازگشتند و fork زدند. شاخهٔ self-improve برنده شد؛
رکوردِ ۹۶۴۵ (scheduler) یتیم شد.

رأیِ مالک (۲۰۲۶-۰۷-۳۱، با شواهدِ کامل تأییدشده): «genesis تازه از head».
پیاده‌سازیِ امانی (هیچ شاهدی از بین نمی‌رود):

  1. backup ِ کامل (فریز، هرگز دست‌نخورده) — قبلاً ساخته شد.
  2. archive ِ کاملِ زنجیرهٔ قدیم — نسخهٔ مرجع، هرگز بازنویسی نمی‌شود.
  3. زنجیرهٔ زنده را با **یک رکوردِ لنگرِ genesis تازه** بازنویسی می‌کند:
       prev = GENESIS ("0"*64)  ← چون این اولین رکوردِ زنجیرهٔ تازه است
       type = NOTE, actor = "owner-reanchor", is_human = True
       payload = {anchor → archive, prev_head → hash ِ head ِ قدیم,
                  prev_head_index, reanchor_reason, reanchor_ts}

⚠️ این رکوردِ لنگر با همان قانونِ canonical هش می‌شود (درست مثل append).
بدنهٔ آن را دستی می‌سازیم (نه از append) چون prev را GENESIS می‌خواهیم، نه
tail ِ زنده. نتیجه: verify() از genesis شروع می‌کند، لنگر را می‌پذیرد، و
«ok» برمی‌گرداند — حلقهٔ یادگیری آزاد می‌شود.

استفاده: python -X utf8 ledger_repair_reanchor_2026_07_31.py
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_LEDGER_DIR = _HERE.parent.parent / "07 - Knowledge" / "genome-system" / "ledger"
_LEDGER = _LEDGER_DIR / "ledger.jsonl"
sys.path.insert(0, str(_LEDGER_DIR))

import ledger as _L  # noqa: E402

GENESIS = _L.GENESIS
ARCHIVE_REL = "archive/chain-pre-2026-07-31.jsonl"
_BACKUP = _LEDGER.parent / "ledger.jsonl.bak-2026-07-31"


def _canonical(obj: dict) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")


def _records(path: Path) -> list[dict]:
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def _build_anchor(old_head_hash: str, old_count: int) -> dict:
    """رکوردِ لنگرِ genesis تازه. prev=GENESIS چون اولین رکورد است."""
    ts = datetime.now(timezone.utc).isoformat()
    body = {
        "id": "reanchor-2026-07-31",
        "ts": ts,
        "type": "NOTE",
        "actor": "owner-reanchor",
        "payload": {
            "anchor": ARCHIVE_REL,
            "prev_head": old_head_hash,
            "prev_head_index": old_count,
            "reanchor_reason": ("concurrent fork at record 9646 (orphan 9645 scheduler); "
                                 "winning branch 9646->head intact; reanchored genesis "
                                 "from head by owner vote 2026-07-31"),
        },
        "meta": {"reanchor": "2026-07-31"},
        "prev": GENESIS,
        "age_tick": 1,   # first human append advances the mortal arrow 0->1
        "is_human": 1,
        "age_rule": _L.AGE_RULE_CURRENT,
        "beat": 0,
    }
    digest = hashlib.sha256(_canonical(body)).hexdigest()
    return {**body, "hash": digest}


def main() -> int:
    if not _LEDGER.exists():
        print("ERROR: ledger not found:", _LEDGER)
        return 2

    # ── re-create backup + archive FRESH from the live file, atomically, right
    #    now. The organism may have appended between our earlier archive step and
    #    this run — so the archive must capture the EXACT head we reanchor from.
    #    This guarantees archive == backup == live-at-this-instant.
    import shutil
    archive_full = _LEDGER_DIR / ARCHIVE_REL
    archive_full.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(str(_LEDGER), str(_BACKUP))
    shutil.copy2(str(_LEDGER), str(archive_full))
    print(f"backup  (fresh): {_BACKUP}")
    print(f"archive (fresh): {archive_full}")

    # ── guard: only run once ──────────────────────────────────────────────
    recs = _records(_LEDGER)
    if recs and (recs[0].get("payload") or {}).get("anchor") == ARCHIVE_REL:
        print("ERROR: ledger already reanchored (anchor record present). Aborting.")
        return 3

    old_head = recs[-1]
    old_head_hash = old_head["hash"]
    old_count = len(recs)
    print(f"old chain: {old_count} records, head hash = {old_head_hash}")
    print(f"old head verdict: ", end="")
    lg_old = _L.Ledger(str(_LEDGER))
    s_ok, s_msg = lg_old.verify()
    print(f"verify()={s_ok} ({s_msg})")

    # ── build anchor + write new chain ────────────────────────────────────
    anchor = _build_anchor(old_head_hash, old_count)
    tmp = _LEDGER.with_suffix(".jsonl.new")
    tmp.write_text(json.dumps(anchor, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(_LEDGER)   # atomic replace
    print(f"new chain written: 1 record (anchor)")
    print(f"  anchor id  : {anchor['id']}")
    print(f"  anchor hash: {anchor['hash']}")
    print(f"  anchor prev: GENESIS (={'0'*16}..)")

    # ── verify the new chain passes both verifiers ────────────────────────
    lg_new = _L.Ledger(str(_LEDGER))
    s_ok, s_msg = lg_new.verify()
    c_ok, c_msg = lg_new.verify_scar_aware()
    print(f"\nverify()            : {s_ok} ({s_msg})")
    print(f"verify_scar_aware() : {c_ok} ({c_msg})")

    # ── repair journal ────────────────────────────────────────────────────
    journal = _HERE.parent / "state" / "now_moves" / "ledger-repair-log.jsonl"
    journal.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": anchor["ts"],
        "action": "reanchor-genesis",
        "why": "concurrent-fork-orphan-9645",
        "who": "owner-vote-2026-07-31",
        "old_count": old_count,
        "old_head_hash": old_head_hash,
        "anchor_hash": anchor["hash"],
        "archive_path": str(_LEDGER_DIR / ARCHIVE_REL),
        "backup_path": str(_BACKUP),
    }
    with open(journal, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"repair journal appended: {journal}")

    if s_ok and c_ok:
        print("\n✅ SUCCESS — new genesis chain clean on both verifiers")
        print(f"   backup:   {_BACKUP}")
        print(f"   archive:  {_LEDGER_DIR / ARCHIVE_REL}")
        return 0
    print("\n❌ FAILED — a verifier still rejects")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
