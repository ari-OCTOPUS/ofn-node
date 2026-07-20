#!/usr/bin/env python3
"""audit.py — Project-F · لاگِ append-onlyِ تأییدهای انسانی (2026-07-20).

هر approve/finalize/dm-approve یک خط JSON در ``langar/approvals.jsonl`` می‌نویسد
تا مسیرِ HITL قابل‌ممیزی باشد (چه کسی، کی، روی چه آیتمی). فقط متادیتای
content-free: هرگز متنِ hook/caption/body کامل ثبت نمی‌شود — فقط id/status/actor.

stdlib-only · fail-soft (audit هرگز pipeline را نمی‌شکند) · thread-safe.
"""
from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent          # brain/
_PROJECT_ROOT = _HERE.parent                     # Project-F/
# قابل‌انحراف با PF_AUDIT_FILE (تست/harness) — مثل PF_BRAIN_DIR در orchestrator
DEFAULT_AUDIT_FILE = Path(os.environ.get("PF_AUDIT_FILE")
                          or (_PROJECT_ROOT / "langar" / "approvals.jsonl"))

_LOCK = threading.RLock()


def audit_append(event: str, payload: dict, path: str | Path | None = None) -> bool:
    """یک رویدادِ تأیید را append می‌کند. True=نوشته شد، False=خطای بی‌صدا.

    payload باید content-free باشد (id/actor/status/channel) — caller مسئول است؛
    این‌جا هم به‌عنوان کمربندِ دوم فقط کلیدهای امن عبور داده می‌شوند."""
    safe_keys = ("id", "actor", "status", "channel", "kind", "ok", "reason",
                 "link_code", "duplicate")
    row = {"ts": time.time(), "event": str(event)[:40]}
    for k in safe_keys:
        if k in payload:
            row[k] = payload[k] if isinstance(payload[k], (bool, int, float)) \
                else str(payload[k])[:80]
    target = Path(path) if path else DEFAULT_AUDIT_FILE
    try:
        with _LOCK:
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        return True
    except OSError:
        return False
