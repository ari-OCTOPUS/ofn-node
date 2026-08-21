#!/usr/bin/env python3
"""Bounded state-file I/O — the Telegram center must never freeze on a file.

Windows third-party byte-range locks (antivirus scans of frequently rewritten
state files) can block plain reads/writes indefinitely. Every hot-loop file
operation goes through a daemon worker with a hard timeout; a stalled
operation returns None/False so the poll loop continues with memory state.
"""
from __future__ import annotations

import queue
import threading
from pathlib import Path


def read_text(path: Path, timeout_s: float = 3.0) -> str | None:
    """Read a file with a hard wall-clock bound; None on stall/error."""
    box: queue.Queue = queue.Queue(maxsize=1)

    def _worker():
        try:
            box.put(path.read_text("utf-8"))
        except Exception as exc:  # noqa: BLE001 — fail-soft read
            box.put(exc)

    threading.Thread(target=_worker, daemon=True).start()
    try:
        got = box.get(timeout=timeout_s)
    except queue.Empty:
        return None
    if isinstance(got, Exception):
        return None
    return got


def write_text(path: Path, text: str, timeout_s: float = 3.0) -> bool:
    """Write a file with a hard wall-clock bound; False on stall/error."""
    box: queue.Queue = queue.Queue(maxsize=1)

    def _worker():
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
            box.put(True)
        except Exception as exc:  # noqa: BLE001 — fail-soft write
            box.put(exc)

    threading.Thread(target=_worker, daemon=True).start()
    try:
        got = box.get(timeout=timeout_s)
    except queue.Empty:
        return False
    return got is True
