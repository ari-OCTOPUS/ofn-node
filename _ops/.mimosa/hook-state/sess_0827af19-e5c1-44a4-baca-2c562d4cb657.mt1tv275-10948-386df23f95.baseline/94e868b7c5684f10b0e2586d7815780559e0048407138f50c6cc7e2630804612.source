#!/usr/bin/env python3
"""raw_store.py — انبارِ شواهدِ خامِ immutable (فازِ صفرِ نقدِ 2026-07-16، لایهٔ ۱ معماری).

اصلِ تغییرناپذیر (قاعدهٔ ۱ نقد): **رکوردِ خام هرگز ویرایش/حذف/بازنویسی نمی‌شود** —
نه توسطِ AI، نه کاربر، نه rule. txn-store لایهٔ *مشتق* است؛ این‌جا لایهٔ evidence است.

کلیدِ idempotency (ترتیبِ نقد): اول شناسهٔ providerِ منبع
(`source_system:account_id:external_id`)، فقط اگر external_id نبود → fingerprintِ
چندفیلدی (sha256 از date|amount|desc|account). ingestِ دوباره = skip، نه overwrite.

فایل: personal/raw/<source_system>.jsonl (append-only، gitignored — دادهٔ مالیِ واقعی).
API فقط ingest/load — **هیچ متدِ mutation وجود ندارد** (عمداً).
$0 · stdlib + opslib · fail-soft در خواندن، fail-closed در نوشتن.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
if str(_HERE.parent / "budget") not in sys.path:
    sys.path.insert(0, str(_HERE.parent / "budget"))
import opslib  # noqa: E402

_SAFE_NAME = re.compile(r"[^A-Za-z0-9_\-]")


def _raw_dir() -> Path:
    return opslib.ORG_ROOT / "03 - Projects" / "Accounting" / "personal" / "raw"


def _file_for(source_system: str, raw_dir: Path | None) -> Path:
    name = _SAFE_NAME.sub("-", str(source_system or "unknown"))[:40] or "unknown"
    return (raw_dir or _raw_dir()) / f"{name}.jsonl"


def _fingerprint(rec: dict, account_id: str) -> str:
    """fallback فقط وقتی providerِ منبع external_id نمی‌دهد — چندفیلدی، نه فقط desc."""
    key = "|".join(str(rec.get(k, "")) for k in ("date", "amount", "amount_cents", "desc",
                                                 "description")) + "|" + str(account_id)
    return "fp-" + hashlib.sha256(key.encode("utf-8")).hexdigest()[:20]


def _raw_id(source_system: str, account_id: str, rec: dict, occurrence: int = 1) -> str:
    """id پایدار: providerِ منبع اول؛ fallback = fingerprint + ترتیبِ تکرار در همان batch
    (auditِ 2026-07-16 #19/#36: دو تراکنشِ واقعیِ یکسان بدونِ external_id هر دو ثبت شوند)."""
    ext = str(rec.get("external_id") or rec.get("id") or "").strip()
    if ext:
        tail = ext
    else:
        tail = _fingerprint(rec, account_id)
        if occurrence > 1:
            tail += f"#{occurrence}"
    return f"{source_system}:{account_id}:{tail}"


def _read_lines(path: Path) -> tuple[list[dict], int]:
    """(rows, corrupt_count) — ضدِ crash روی بایتِ غیرUTF-8 (audit #16)."""
    rows: list[dict] = []
    corrupt = 0
    try:
        if not path.exists():
            return rows, corrupt
        raw = path.read_bytes()
    except OSError:
        return rows, corrupt
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("utf-8", errors="replace")
        corrupt += 1
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
            if isinstance(d, dict):
                rows.append(d)
            else:
                corrupt += 1
        except ValueError:
            corrupt += 1
    return rows, corrupt


def _existing_ids(path: Path) -> set:
    rows, _ = _read_lines(path)
    return {str(d["raw_id"]) for d in rows if d.get("raw_id")}


def _append_fsync(p: Path, rec: dict) -> None:
    """append ضدِ-torn: یک write + flush + fsync (audit #21)."""
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        fh.flush()
        os.fsync(fh.fileno())


def ingest(source_system: str, account_id: str, records: list,
           raw_dir: Path | None = None, batch_note: str = "") -> dict:
    """رکوردهای خام را append کن (idempotent، زیرِ قفلِ فایل). شمارشِ صادق — هرگز overwrite.
    هر رکورد verbatim + hash. دو رکوردِ *یکسان* در یک batch بدونِ external_id → هر دو ثبت
    (ordinal #2)؛ re-ingestِ همان batch → همه skip."""
    p = _file_for(source_system, raw_dir)
    ingested = skipped = bad = 0
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        lock = opslib.LockedJson(p)                   # فقط قفل (p.lock) — ضدِ دو ingestِ همزمان
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": f"prep: {type(e).__name__}",
                "ingested": 0, "skipped_existing": 0, "bad": 0}
    try:
        with lock:
            seen = _existing_ids(p)
            occ: dict = {}                            # fingerprint → شمارِ تکرار در این batch
            for rec in (records or []):
                if not isinstance(rec, dict):
                    bad += 1
                    continue
                ext = str(rec.get("external_id") or rec.get("id") or "").strip()
                if ext:
                    rid = _raw_id(source_system, account_id, rec)
                else:
                    fp = _fingerprint(rec, account_id)
                    occ[fp] = occ.get(fp, 0) + 1
                    rid = _raw_id(source_system, account_id, rec, occurrence=occ[fp])
                if rid in seen:
                    skipped += 1
                    continue
                raw_json = json.dumps(rec, ensure_ascii=False, sort_keys=True)
                row = {"raw_id": rid, "source_system": str(source_system),
                       "account_id": str(account_id),
                       "external_id": ext or None,
                       "ingested_at": opslib.now_iso(),
                       "batch_note": str(batch_note or "")[:100],
                       "raw_hash": "sha256:" + hashlib.sha256(raw_json.encode("utf-8")).hexdigest()[:32],
                       "raw": rec}
                try:
                    _append_fsync(p, row)
                except Exception as e:  # noqa: BLE001 — نوشتن شکست = صادقانه گزارش
                    return {"ok": False, "error": f"append: {type(e).__name__}",
                            "ingested": ingested, "skipped_existing": skipped, "bad": bad}
                seen.add(rid)
                ingested += 1
    except TimeoutError:
        return {"ok": False, "error": "قفلِ raw مشغول است — retry",
                "ingested": ingested, "skipped_existing": skipped, "bad": bad}
    return {"ok": True, "file": str(p), "ingested": ingested,
            "skipped_existing": skipped, "bad": bad}


def load_raw(source_system: str, raw_dir: Path | None = None) -> list[dict]:
    """خواندنِ خام (فقط‌خواندنی، ضدِ crash روی byteِ خراب). فایل هرگز بازنویسی نمی‌شود."""
    rows, _ = _read_lines(_file_for(source_system, raw_dir))
    return rows


if __name__ == "__main__":
    print(json.dumps({"raw_dir": str(_raw_dir())}, ensure_ascii=False))
