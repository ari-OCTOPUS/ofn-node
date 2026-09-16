#!/usr/bin/env python3
"""drive_queue_consumer.py — مصرف‌کنندهٔ محدودِ صفِ drive-queue.jsonl (2026-09-08).

شکافِ ممیزی صبح ۰۹-۰۸: بازشدن قفل، «قدم بعدی» را در صف می‌گذارد ولی هیچ‌کس صف را
نمی‌خواند؛ consumed همیشه false می‌ماند. این ماژول کوچک‌ترین مصرف‌کنندهٔ صادق است:

  قواعد (عمداً تنگ):
  1. فقط ردیف‌های consumed=false و lock != SBX_test.
  2. مصرف فقط وقتی «رسیدِ انجامِ» همان قفل در state/drive/ موجود و معتبر باشد
     (DONE_RECEIPTS زیر). بدون رسید = دست‌نخورده.
  3. هر مصرف: پرچم consumed=true روی همان سطر (بقیهٔ فیلدها عیناً می‌مانند) +
     یک سطر audit در queue-consumed-audit.jsonl (append-only) + رویداد queue.consumed.
  4. ردیفی که رسید-انجام ندارد (مثل L24 تا ۱۰-۰۶ یا MSG38 تا ثبتِ 182) هرگز
     لمس نمی‌شود — صف جای برنامه‌ریزی نیست، جای اثباتِ انجام است.

فراخوان: drive_loops.tick() (fail-soft) یا دستی:
  python drive_queue_consumer.py            # یک پاس مصرف
  python drive_queue_consumer.py --selftest
"""
from __future__ import annotations

import json
import sys
import tempfile
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import event_spine  # noqa: E402

DRIVE = _HERE / "state" / "drive"
QUEUE = DRIVE / "drive-queue.jsonl"
AUDIT = DRIVE / "queue-consumed-audit.jsonl"


def _receipt_ok(path: Path, check) -> bool:
    try:
        return bool(check(json.loads(path.read_text(encoding="utf-8"))))
    except (OSError, ValueError):
        return False


# قفل → (فایل رسید آینه‌ای، predicate). فقط چیزهایی که واقعاً تمام شده‌اند.
DONE_RECEIPTS: dict[str, tuple[Path, object]] = {
    "L23_hold_external": (
        DRIVE / "l23-first-mint-verified.json",
        lambda d: d.get("status") == "VERIFIED" and bool(d.get("evidence")),
    ),
}


def consume_pending(queue_path: Path | None = None, audit_path: Path | None = None) -> list[dict]:
    q = queue_path or QUEUE
    a = audit_path or AUDIT
    if not q.exists():
        return []
    lines = q.read_text(encoding="utf-8").splitlines()
    out_rows: list[str] = []
    consumed: list[dict] = []
    for ln in lines:
        if not ln.strip():
            continue
        try:
            row = json.loads(ln)
        except ValueError:
            out_rows.append(ln)  # سطر خراب دست‌نخورده می‌ماند
            continue
        lock = row.get("lock")
        if (row.get("consumed") or lock == "SBX_test" or lock not in DONE_RECEIPTS):
            out_rows.append(ln)
            continue
        path, check = DONE_RECEIPTS[lock]
        if not _receipt_ok(path, check):
            out_rows.append(ln)
            continue
        row["consumed"] = True
        row["consumed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        row["evidence"] = str(path)
        out_rows.append(json.dumps(row, ensure_ascii=False))
        rec = {"ts_utc": row["consumed_at"], "lock": lock,
               "next": row.get("next"), "evidence": str(path)}
        consumed.append(rec)
        with open(a, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    if consumed:
        q.write_text("\n".join(out_rows) + "\n", encoding="utf-8")
        try:
            event_spine.emit("queue.consumed", source="drive_queue_consumer",
                             payload={"items": [c["lock"] for c in consumed]})
        except Exception:  # noqa: BLE001 — رویداد نباید مصرف را برگرداند
            pass
    return consumed


def _selftest() -> bool:
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        fake_receipt = td / "r.json"
        fake_receipt.write_text(json.dumps({"status": "VERIFIED", "evidence": "x"}), encoding="utf-8")
        global DONE_RECEIPTS
        saved = DONE_RECEIPTS
        try:
            DONE_RECEIPTS = {"TST_lock": (fake_receipt, lambda d: d.get("status") == "VERIFIED")}
            q = td / "q.jsonl"
            a = td / "a.jsonl"
            q.write_text("\n".join([
                json.dumps({"ts_utc": "t", "lock": "SBX_test", "next": "n", "consumed": False}),
                json.dumps({"ts_utc": "t", "lock": "TST_lock", "next": "n", "consumed": False}),
                json.dumps({"ts_utc": "t", "lock": "OTHER", "next": "n", "consumed": False}),
            ]) + "\n", encoding="utf-8")
            got = consume_pending(q, a)
            rows = [json.loads(x) for x in q.read_text(encoding="utf-8").splitlines()]
            audit = [json.loads(x) for x in a.read_text(encoding="utf-8").splitlines()]
            ok = (len(got) == 1 and got[0]["lock"] == "TST_lock"
                  and [r for r in rows if r["lock"] == "TST_lock"][0]["consumed"] is True
                  and [r for r in rows if r["lock"] == "SBX_test"][0]["consumed"] is False
                  and [r for r in rows if r["lock"] == "OTHER"][0]["consumed"] is False
                  and len(audit) == 1)
            print(f"selftest: consumed_only_receipted={ok}")
            return bool(ok)
        finally:
            DONE_RECEIPTS = saved


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(0 if _selftest() else 1)
    for c in consume_pending():
        print("consumed:", c["lock"], "→", c["evidence"])
