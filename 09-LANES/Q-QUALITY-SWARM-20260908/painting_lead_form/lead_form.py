"""Store-only painting lead intake.

No send, no payment, no 0.0.0.0, no wire flags.
baseline_action is always 0 (no outbound).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BASELINE_ACTION = 0


def submit_lead(store_path: Path, payload: dict[str, Any], *, now: datetime | None = None) -> dict:
    """Append one lead. Returns the stored record. Fail-closed on empty name."""
    name = str(payload.get("name") or "").strip()
    contact = str(payload.get("contact") or "").strip()
    suburb = str(payload.get("suburb") or "").strip()
    message = str(payload.get("message") or "").strip()
    if not name:
        raise ValueError("name-required")
    ts = (now or datetime.now(timezone.utc)).strftime("%Y-%m-%dT%H:%M:%SZ")
    rec = {
        "name": name,
        "contact": contact,
        "suburb": suburb,
        "message": message,
        "baseline_action": BASELINE_ACTION,
        "channel": "store_only_form",
        "ts": ts,
        "sent": False,
        "paid": False,
    }
    store_path = Path(store_path)
    store_path.parent.mkdir(parents=True, exist_ok=True)
    with store_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        f.flush()
    return rec


def list_leads(store_path: Path) -> list[dict]:
    path = Path(store_path)
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows
