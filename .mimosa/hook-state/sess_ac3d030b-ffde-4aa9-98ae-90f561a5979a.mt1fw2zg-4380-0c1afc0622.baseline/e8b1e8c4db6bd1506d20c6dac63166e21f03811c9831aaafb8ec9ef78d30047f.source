"""Event-driven file watcher. On a vault change -> incremental index + ledger.

Two entry points:
  * reconcile(): one full pass (index_dir) -- deterministic, used at startup and
    by tests. Also the --once mode.
  * handle_event(): process ONE create/modify/delete event. Module-level so the
    event logic is testable without a live watchdog Observer.
  * watch(): live mode using watchdog; forwards events to handle_event().

Polling on a fixed minute interval is intentionally NOT provided: the genome
forbids it (event-driven is ~100x cheaper on a personal vault).
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

# make sibling packages importable regardless of CWD
_ROOT = Path(__file__).resolve().parents[1]
for _sub in ("ledger", "perception"):
    sys.path.insert(0, str(_ROOT / _sub))

from indexer import Indexer          # noqa: E402
from ledger import Ledger            # noqa: E402


def reconcile(vault: str | Path, indexer: Indexer, ledger: Ledger) -> dict[str, int]:
    """Full pass: index everything under vault, log a summary. Returns stats."""
    stats = indexer.index_dir(vault)
    ledger.append("INDEX", {"mode": "reconcile", **stats,
                            "files": indexer.stats()["files"]}, actor="watcher")
    return stats


def handle_event(indexer: Indexer, ledger: Ledger, path: str, op: str) -> str:
    """Process one file event (create/modify/delete). Module-level so it is
    testable WITHOUT a live watchdog Observer. The live handler just forwards
    here. Returns the indexer result / 'removed' / 'ignored'."""
    p = Path(path)
    if p.suffix.lower() not in indexer.exts:
        return "ignored"
    ledger.append("OBSERVE", {"path": str(p), "op": op}, actor="watcher")
    if op == "deleted":
        indexer.remove(p)
        ledger.append("INDEX", {"path": str(p), "op": "removed"}, actor="watcher")
        return "removed"
    result = indexer.index_file(p)
    if result not in ("unchanged", "skipped"):
        ledger.append("INDEX", {"path": str(p), "result": result}, actor="watcher")
    return result


def watch(vault: str | Path, indexer: Indexer, ledger: Ledger,
          settle: float = 0.5) -> None:  # pragma: no cover (live loop)
    """Live event-driven watch. Requires `pip install watchdog`."""
    try:
        from watchdog.events import FileSystemEventHandler
        from watchdog.observers import Observer
    except ImportError:
        raise SystemExit("watch mode needs watchdog: pip install watchdog")

    reconcile(vault, indexer, ledger)  # backfill before going live

    class _Handler(FileSystemEventHandler):
        def on_created(self, e): handle_event(indexer, ledger, e.src_path, "created")    # noqa: E704
        def on_modified(self, e): handle_event(indexer, ledger, e.src_path, "modified")  # noqa: E704
        def on_deleted(self, e): handle_event(indexer, ledger, e.src_path, "deleted")    # noqa: E704

    obs = Observer()
    obs.schedule(_Handler(), str(vault), recursive=True)
    obs.start()
    ledger.append("HEARTBEAT", {"component": "watcher", "state": "online"}, actor="watcher")
    try:
        while True:
            time.sleep(settle)
    except KeyboardInterrupt:
        ob