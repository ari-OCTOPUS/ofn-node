"""memory_chain — زنجیرهٔ هشِ حافظه (نقشهٔ سند تلاقی، گام ۲؛ به‌سبک SEDM).

هر تغییرِ وضعیتِ مهمِ لید (reply/optout/followup/quote/booked) یک ردیفِ
هش‌زنجیره‌ای append-only می‌گیرد؛ chain_verify() دست‌کاری را آشکار می‌کند.
الگوی همان لجرِ هوک‌های Cursor است — حالا برای حافظهٔ CRM.
نمرهٔ صادق: E3 (تست سبز + نقضِ عمدی شناسایی‌شده در تست دندان‌ها).
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent / "budget"))
import opslib  # noqa: E402

CHAIN = opslib.STATE_DIR / "memory-chain.jsonl"


def _prev_hash(fh) -> str:
    last = None
    for line in fh:
        if line.strip():
            last = line
    if not last:
        return "0" * 64
    try:
        return json.loads(last).get("this_hash", "0" * 64)
    except Exception:  # noqa: BLE001
        return "0" * 64


def append(kind: str, lead_id: str, detail: dict | None = None) -> dict:
    rec = {"kind": str(kind), "lead_id": str(lead_id)[:80],
           "ts": opslib.now_iso(), "detail": detail or {}}
    CHAIN.parent.mkdir(parents=True, exist_ok=True)
    with CHAIN.open("a+", encoding="utf-8", newline="\n") as fh:
        fh.seek(0)
        prev = _prev_hash(fh)
        rec["prev_hash"] = prev
        body = json.dumps(rec, sort_keys=True, ensure_ascii=False)
        rec["this_hash"] = hashlib.sha256(
            (prev + body).encode("utf-8")).hexdigest()
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


def chain_verify(path: Path = CHAIN) -> dict:
    """بازبینی کاملِ زنجیره. خروجی {ok, rows, first_break}."""
    rows = 0
    prev = "0" * 64
    try:
        with path.open("r", encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                rows += 1
                try:
                    rec = json.loads(line)
                except Exception:
                    return {"ok": False, "rows": rows, "first_break": f"row{rows}:unparsable"}
                exp = hashlib.sha256(
                    (rec.get("prev_hash", "") + json.dumps(
                        {k: rec[k] for k in rec if k != "this_hash"},
                        sort_keys=True, ensure_ascii=False)).encode()
                ).hexdigest()
                if rec.get("prev_hash") != prev:
                    return {"ok": False, "rows": rows,
                            "first_break": f"row{rows}:prev-hash-mismatch"}
                if rec.get("this_hash") != exp:
                    return {"ok": False, "rows": rows,
                            "first_break": f"row{rows}:hash-mismatch"}
                prev = rec["this_hash"]
    except OSError:
        return {"ok": True, "rows": 0, "first_break": None}  # زنجیرهٔ خالی سالم است
    return {"ok": True, "rows": rows, "first_break": None}


if __name__ == "__main__":
    print(json.dumps(chain_verify(), ensure_ascii=False))
