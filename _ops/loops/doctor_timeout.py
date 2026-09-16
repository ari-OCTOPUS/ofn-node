# -*- coding: utf-8 -*-
"""One-open-mission + timeout. Pure functions + file quarantine with backup."""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

OPEN = frozenset({"proposed", "running", "awaiting-merge"})
DEFAULT_TIMEOUT_S = 7 * 86400


def expire_open_missions(
    missions: list[dict[str, Any]],
    *,
    now: float,
    timeout_s: float = DEFAULT_TIMEOUT_S,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Return (missions, log). Open missions older than timeout → failed."""
    log: list[str] = []
    out: list[dict[str, Any]] = []
    for raw in missions:
        m = dict(raw)
        created = m.get("created")
        try:
            created_f = float(created) if created is not None else 0.0
        except (TypeError, ValueError):
            created_f = 0.0
        age = now - created_f if created_f > 0 else 0.0
        if m.get("state") in OPEN and created_f > 0 and age >= float(timeout_s):
            mid = m.get("mission_id")
            notes = list(m.get("notes") or [])
            notes.append(
                f"quarantine: open-mission timeout after {int(age)}s "
                f"(limit {int(timeout_s)}s) — slot freed"
            )
            m["notes"] = notes
            m["state"] = "failed"
            m["quarantined"] = True
            log.append(f"timeout {mid} age_s={int(age)}")
        out.append(m)
    return out, log


def quarantine_file(
    path: Path,
    *,
    now: float,
    timeout_s: float,
    backup: Path,
) -> dict[str, Any]:
    """Backup then rewrite. Reversible via backup copy. Counts before/after."""
    path = Path(path)
    if not path.is_file():
        return {"ok": False, "reason": "missing", "n_before": 0, "n_after": 0}
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, backup)
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        return {"ok": False, "reason": "not_list", "backup": str(backup)}
    n_before = sum(1 for m in raw if isinstance(m, dict) and m.get("state") in OPEN)
    updated, log = expire_open_missions(raw, now=now, timeout_s=timeout_s)
    n_after = sum(1 for m in updated if m.get("state") in OPEN)
    path.write_text(json.dumps(updated, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "ok": True,
        "backup": str(backup),
        "n_open_before": n_before,
        "n_open_after": n_after,
        "quarantined": n_before - n_after,
        "log": log,
    }
