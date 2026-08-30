# -*- coding: utf-8 -*-
"""process_identity.py — A11: PID جدید باید بگوید کدام commit/hash را اجرا می‌کند."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
_ROOT = _OPS.parent
CENTER_PY = _HERE / "center.py"
IDENTITY_PATH = _OPS / "state" / "telegram" / "process-identity.json"
STARTED_LOG = _OPS / "state" / "telegram" / "process-started.jsonl"
HANDLER_SCHEMA_VERSION = "typed-v1"
CANONICAL_BOT_ID = 7992324219


def _sha256(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return ""


def _git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(_ROOT), "rev-parse", "HEAD"],
            text=True, stderr=subprocess.DEVNULL, timeout=8).strip()
    except (subprocess.SubprocessError, OSError):
        return ""


def build(*, poller_lease_id: str | None = None) -> dict:
    return {
        "event": "TELEGRAM_PROCESS_STARTED",
        "process_id": os.getpid(),
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "started_at_unix": time.time(),
        "git_commit": _git_commit(),
        "center_py_sha256": _sha256(CENTER_PY),
        "handler_schema_version": HANDLER_SCHEMA_VERSION,
        "bot_id": CANONICAL_BOT_ID,
        "poller_lease_id": poller_lease_id or "",
        "short_build_id": ((_git_commit() or "?")[:7]
                           + "/" + HANDLER_SCHEMA_VERSION),
    }


def write_started(identity: dict | None = None) -> dict:
    rec = dict(identity or build())
    IDENTITY_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = IDENTITY_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, IDENTITY_PATH)
    with STARTED_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


def load() -> dict:
    try:
        d = json.loads(IDENTITY_PATH.read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}
