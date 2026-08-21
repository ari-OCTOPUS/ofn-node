#!/usr/bin/env python3
"""Bounded state-file/transport I/O — the Telegram center must never freeze.

Windows third-party byte-range locks and DNS getaddrinfo have no timeout and
cannot be cancelled from another thread. Every hot-loop operation runs in a
daemon worker with a hard wall-clock bound; a stalled operation returns
None/False so the loop continues with memory state.

Worker growth is capped (MAX_CONCURRENT): saturated workers fail soft instead
of spawning, so repeated environmental stalls cannot accumulate threads.
"""
from __future__ import annotations

import queue
import threading
from pathlib import Path

_MAX_CONCURRENT = 4
_lock = threading.Lock()
_active = 0


def active_worker_count() -> int:
    with _lock:
        return _active


def run(fn, timeout_s: float = 3.0):
    """Run fn in a bounded daemon worker.

    Returns fn()'s result; re-raises its exception; None on stall or when the
    worker pool is saturated (fail-soft, no new thread spawned).
    """
    global _active
    with _lock:
        if _active >= _MAX_CONCURRENT:
            return None
        _active += 1
    box: queue.Queue = queue.Queue(maxsize=1)

    def _worker():
        try:
            box.put(fn())
        except Exception as exc:  # noqa: BLE001 — surfaced to caller
            box.put(exc)
        finally:
            global _active
            with _lock:
                _active -= 1

    try:
        threading.Thread(target=_worker, daemon=True).start()
    except Exception:
        with _lock:
            _active -= 1
        raise
    try:
        got = box.get(timeout=max(0.0, float(timeout_s)))
    except queue.Empty:
        return None
    if isinstance(got, Exception):
        raise got
    return got


def read_text(path: Path, timeout_s: float = 3.0) -> str | None:
    """Read a file with a hard wall-clock bound; None on stall/error."""
    try:
        got = run(lambda: path.read_text("utf-8"), timeout_s=timeout_s)
    except Exception:  # noqa: BLE001 — fail-soft read
        return None
    return got


def write_text(path: Path, text: str, timeout_s: float = 3.0) -> bool:
    """Write a file with a hard wall-clock bound; False on stall/error."""
    def _write():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return True

    try:
        return run(_write, timeout_s=timeout_s) is True
    except Exception:  # noqa: BLE001 — fail-soft write
        return False
