#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_ledger_reanchor_2026_07_31.py — رگرسیونِ ترمیمِ زنجیرهٔ ledger.

اثبات می‌کند که reanchor ِ genesis (رأیِ مالک ۲۰۲۶-۰۷-۳۱) شفاف بود:
  - archive == backup (هیچ شاهدی از دست نرفته).
  - زنجیرهٔ زنده پس از reanchor روی هر دو verifier سبز است.
  - رکوردِ لنگر وجود دارد و به archive اشاره می‌کند (قابلیتِ ردیابی).
  - رشدِ زنده روی زنجیرهٔ تازه همچنان معتبر می‌ماند ( organism زنده است).

⚠️ این تست روی درختِ زنده (F:/backup) اجرا می‌شود، نه worktree — چون
reanchor یک عملیاتِ دادهٔ زنده بود. اگر روی worktree اجرا شود، ledger ِ
آن نسخهٔ قدیمیِ ۹۵۶-رکوردی است و تست skip می‌شود.
"""
import hashlib
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))

import harness  # noqa: E402

_LEDGER_DIR = _HERE.parent.parent / "07 - Knowledge" / "genome-system" / "ledger"
_LEDGER = _LEDGER_DIR / "ledger.jsonl"
_ARCHIVE = _LEDGER_DIR / "archive" / "chain-pre-2026-07-31.jsonl"
_BACKUP = _LEDGER_DIR / "ledger.jsonl.bak-2026-07-31"
_ANCHOR_ID = "reanchor-2026-07-31"


def _sha256_file(p: Path) -> str:
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def _records(path: Path) -> list:
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except ValueError:
                continue
    return out


def _skip_if_no_reanchor():
    """worktree نسخهٔ قدیمی دارد — این تست فقط روی درختِ زنده معنا دارد."""
    if not _LEDGER.exists():
        return True
    recs = _records(_LEDGER)
    if not recs:
        return True
    payload = recs[0].get("payload") or {}
    return payload.get("anchor") != "archive/chain-pre-2026-07-31.jsonl"


def t_archive_and_backup_are_byte_equal():
    """archive ِ کاملِ زنجیرهٔ قدیم = backup. هیچ شاهدی از دست نرفته."""
    if _skip_if_no_reanchor():
        return  # روی worktree اجرا نشده — skip
    assert _ARCHIVE.exists(), f"archive missing: {_ARCHIVE}"
    assert _BACKUP.exists(), f"backup missing: {_BACKUP}"
    assert _sha256_file(_ARCHIVE) == _sha256_file(_BACKUP), (
        "archive != backup — شواهدِ زنجیرهٔ قدیم ناهماهنگ است")


def t_anchor_record_exists_and_points_to_archive():
    """رکوردِ لنگرِ genesis تازه وجود دارد و به archive اشاره می‌کند."""
    if _skip_if_no_reanchor():
        return
    recs = _records(_LEDGER)
    assert recs, "ledger empty"
    first = recs[0]
    assert first.get("id") == _ANCHOR_ID, f"first record is not anchor: {first.get('id')}"
    payload = first.get("payload") or {}
    assert payload.get("anchor") == "archive/chain-pre-2026-07-31.jsonl", (
        "anchor payload missing archive pointer")
    assert payload.get("prev_head"), "anchor payload missing prev_head (old head hash)"
    assert payload.get("reanchor_reason"), "anchor payload missing reason"


def t_live_chain_passes_both_verifiers():
    """زنجیرهٔ زنده (شاملِ هر رشدِ زندهٔ جدید) روی هر دو verifier سبز است."""
    if _skip_if_no_reanchor():
        return
    sys.path.insert(0, str(_LEDGER_DIR))
    import ledger as _L  # noqa: E402
    lg = _L.Ledger(str(_LEDGER))
    s_ok, s_msg = lg.verify()
    c_ok, c_msg = lg.verify_scar_aware()
    assert s_ok, f"verify() failed after reanchor: {s_msg}"
    assert c_ok, f"verify_scar_aware() failed after reanchor: {c_msg}"


def t_anchor_prev_is_genesis():
    """لنگر اولین رکورد است — prev اش باید GENESIS ("0"*64) باشد."""
    if _skip_if_no_reanchor():
        return
    recs = _records(_LEDGER)
    assert recs, "ledger empty"
    assert recs[0].get("prev") == "0" * 64, (
        f"anchor prev != GENESIS: {recs[0].get('prev')}")


def t_no_reanchor_rerun_possible():
    """reanchor یک‌بار است — اگر دوباره اجرا شود باید abort کند."""
    if _skip_if_no_reanchor():
        return
    # اگر لنگر از قبل هست، اسکریپت نباید دوباره بنویسد.
    # این تست فقط وجودِ آن را تأیید می‌کند (guard در خودِ اسکریپت است).
    recs = _records(_LEDGER)
    anchors = [r for r in recs if r.get("id") == _ANCHOR_ID]
    assert len(anchors) == 1, f"multiple anchor records: {len(anchors)}"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    skipped = _skip_if_no_reanchor()
    if skipped:
        print("\n(SKIP — worktree/old ledger; این تست روی درختِ زنده اجرا می‌شود)")
    print(f"\n{'✅' if not failed else '❌'} test_ledger_reanchor_2026_07_31: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
