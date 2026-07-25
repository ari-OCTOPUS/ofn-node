#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""c6_producer.py — C2 · تولیدکنندهٔ صادقِ فرضیهٔ C6 (پشتِ OCTOPUS_WIRE_C6_PRODUCER).

هر فرضیه فقط از یک سنجهٔ واقعیِ read-only ساخته می‌شود و count>floor شرط تولید است.
صفِ خالی نتیجهٔ سالم است و «no-pending-hypothesis» به‌خودی‌خودی نیاز به ساختن فرضیهٔ
ساختگی نیست. dedupe محتوایی روی کل صف؛ سقف pending و سقف کل ردیف‌ها؛ خطا = alert + no-op.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE), str(_HERE / "budget"), str(_HERE / "outcomes")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib  # noqa: E402
import c6_probes  # noqa: E402

FLAG = "OCTOPUS_WIRE_C6_PRODUCER"
MAX_PENDING_ROWS = 10
MAX_QUEUE_ROWS = 50


def flag_on() -> bool:
    return str(os.environ.get(FLAG, "")).strip().lower() in ("1", "true", "yes", "on")


def _sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _read_rows(queue: Path) -> list[dict]:
    rows = []
    try:
        if queue.exists():
            for ln in queue.read_text("utf-8").splitlines():
                if not ln.strip():
                    continue
                try:
                    d = json.loads(ln)
                except ValueError:
                    continue
                if isinstance(d, dict):
                    rows.append(d)
    except OSError:
        pass
    return rows


def _existing_id(rows: list[dict], probe: str, subject: str) -> str:
    return "c6-" + _sha(f"{probe}|{subject}")[:12]


def _already_present(rows: list[dict], hid: str, probe: str, subject: str) -> bool:
    for r in rows:
        if str(r.get("id") or "") == hid:
            return True
        if str(r.get("probe") or "") == probe and str(r.get("subject") or "") == subject:
            return True
    return False


def _mk_row(probe: str, measured: dict) -> dict:
    spec = c6_probes.PROBES[probe]
    hid = _existing_id([], probe, spec["subject"])
    return {
        "id": hid,
        "kind": "mechanism_count",
        "probe": probe,
        "subject": spec["subject"],
        "question": spec["question"],
        "floor": spec["floor"],
        "measured": measured,
        "status": "PENDING",
        "source": "c6_producer",
        "honesty": "measured-only; no fabricated hypotheses",
    }


def produce(queue: Path) -> dict:
    """سعی می‌کند حداکثر یک فرضیهٔ صادقِ جدید append کند؛ هرگز raise نمی‌کند."""
    try:
        if not flag_on():
            return {"produced": False, "reason": "flag-off"}
        queue = Path(queue)
        rows = _read_rows(queue)
        pending = [r for r in rows if str(r.get("status") or "") == "PENDING"]
        if len(pending) >= MAX_PENDING_ROWS:
            return {"produced": False, "reason": "pending-cap"}
        if len(rows) >= MAX_QUEUE_ROWS:
            return {"produced": False, "reason": "queue-cap"}

        new_rows = list(rows)
        for probe, spec in c6_probes.PROBES.items():
            measured = spec["measure"]()
            count = int(measured.get("count", -1)) if isinstance(measured, dict) else -1
            if count < 0:
                continue
            if count <= int(spec["floor"]):
                continue
            hid = _existing_id(new_rows, probe, spec["subject"])
            if _already_present(new_rows, hid, probe, spec["subject"]):
                continue
            row = _mk_row(probe, measured)
            queue.parent.mkdir(parents=True, exist_ok=True)
            with open(queue, "a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
            return {"produced": True, "id": row["id"], "probe": probe}
        return {"produced": False, "reason": "no-defect"}
    except Exception as e:  # noqa: BLE001
        try:
            opslib.alert([f"c6_producer failed (no-op): {type(e).__name__}: {e}"])
        except Exception:
            pass
        return {"produced": False, "reason": f"failsoft:{type(e).__name__}"}
