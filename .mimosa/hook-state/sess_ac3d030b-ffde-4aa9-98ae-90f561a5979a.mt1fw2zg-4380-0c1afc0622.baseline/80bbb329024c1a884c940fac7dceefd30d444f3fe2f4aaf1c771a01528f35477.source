#!/usr/bin/env python3
"""dlq.py — Dead Letter Queue: append-only برای رکوردهای شکست‌خوردهٔ نیازمندِ مرورِ انسان.

خط‌قرمزهای سخت:
  • append-only jsonl — هیچ رکوردی حذف نمی‌شود (فقط resolved=true می‌خورد).
  • cap روی تعداد ردیف (I6: از budgets.yaml یا default 10000).
  • secrets هرگز در payload ذخیره نمی‌شوند (strip قبل از append).
  • stdlib-only؛ $0 offline؛ propose-only.
"""
from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
import opslib  # noqa: E402

DLQ_PATH = opslib.STATE_DIR / "dlq.jsonl"
REVIEW_PATH = opslib.STATE_DIR / "dlq-review.md"


def _cfg() -> dict:
    """پیکربندی از budgets.yaml → resilience.dlq."""
    try:
        b = opslib.load_budgets()
    except Exception:  # noqa: BLE001
        b = {}
    r = (b.get("resilience") or {}).get("dlq") or {}
    return {
        "max_rows": int(r.get("max_rows", 10_000)),
        "tag": "FACT(budgets.yaml)" if r else "EST(default)",
    }


def _strip_secrets(record: dict) -> dict:
    """هر کلیدی که حاوی secret/key/token/pass است → [REDACTED]."""
    safe = {}
    for k, v in record.items():
        kl = str(k).lower()
        if any(x in kl for x in ("secret", "key", "token", "pass", "credential", "auth")):
            safe[k] = "[REDACTED]"
        elif isinstance(v, dict):
            safe[k] = _strip_secrets(v)
        elif isinstance(v, list):
            safe[k] = [_strip_secrets(i) if isinstance(i, dict) else i for i in v]
        else:
            safe[k] = v
    return safe


def _row_count() -> int:
    try:
        if not DLQ_PATH.exists():
            return 0
        with open(DLQ_PATH, "r", encoding="utf-8") as fh:
            return sum(1 for _ in fh if _.strip())
    except OSError:
        return 0


def append(payload: dict, reason: str, source: str = "unknown",
           record_type: str = "proposal", retry_count: int = 0) -> dict:
    """یک رکورد شکست‌خورده به DLQ append کن. خروجی: {dlq_id, status, capped}."""
    cfg = _cfg()
    if _row_count() >= cfg["max_rows"]:
        opslib.alert([f"DLQ cap reached ({cfg['max_rows']}) — new record dropped"])
        return {"dlq_id": None, "status": "dropped", "capped": True}

    dlq_id = f"DLQ-{uuid.uuid4().hex[:12]}"
    record = {
        "dlq_id": dlq_id,
        "ts": opslib.now_iso(),
        "source": source,
        "record_type": record_type,
        "payload": _strip_secrets(payload),
        "reason": reason,
        "retry_count": retry_count,
        "status": "unresolved",
        "resolved_at": None,
    }
    opslib.append_jsonl(DLQ_PATH, record)
    return {"dlq_id": dlq_id, "status": "queued", "capped": False}


def list_unresolved(limit: int = 100, offset: int = 0) -> list[dict]:
    """ردیف‌های unresolved را برگردان (جدید→قدیمی)."""
    out: list[dict] = []
    if not DLQ_PATH.exists():
        return out
    with open(DLQ_PATH, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("status") == "unresolved":
                out.append(rec)
    # جدید→قدیمی (jsonl append است؛ وارون)
    out.reverse()
    return out[offset:offset + limit]


def mark_resolved(dlq_id: str) -> dict:
    """ resolved = یک رکورد جدید append کن (idempotency با timestamp). """
    record = {
        "dlq_id": dlq_id,
        "ts": opslib.now_iso(),
        "status": "resolved",
        "resolved_at": opslib.now_iso(),
    }
    opslib.append_jsonl(DLQ_PATH, record)
    return {"dlq_id": dlq_id, "status": "resolved"}


def retry_ready(max_retry_count: int = 3) -> list[dict]:
    """ردیف‌های unresolved که هنوز به سقف retry نرسیده‌اند."""
    return [r for r in list_unresolved() if r.get("retry_count", 0) < max_retry_count]


def write_review_md() -> dict:
    """یک فایل markdown انسانی از unresolvedها بساز (overwrite OK — گزارش‌خواندنی)."""
    unresolved = list_unresolved(limit=500)
    lines = [f"# DLQ Review — {opslib.now_iso()}",
             f"unresolved count: {len(unresolved)}",
             "", "| dlq_id | source | type | reason | retry | ts |",
             "|--------|--------|------|--------|-------|----|"]
    for r in unresolved:
        lines.append(
            f"| {r['dlq_id']} | {r['source']} | {r['record_type']} | "
            f"{r['reason'][:60]} | {r.get('retry_count',0)} | {r['ts'][:19]} |")
    lines.append("\n> propose-only: هر ردیف نیازمندِ verdict انسانی است.")
    REVIEW_PATH.parent.mkdir(parents=True, exist_ok=True)
    REVIEW_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"path": str(REVIEW_PATH), "unresolved_count": len(unresolved)}


if __name__ == "__main__":
    import sys
    if "--review" in sys.argv:
        print(json.dumps(write_review_md(), ensure_ascii=False, indent=2))
    else:
        print(json.dumps({"unresolved": len(list_unresolved()), "cfg": _cfg()}, ensure_ascii=False, indent=2))
