"""Live vault watcher — detects changes to the vault's markdown notes.

This is the "live" half of the Knowledge Reality module (v0.2). It runs a
``watchdog`` observer over the vault root in a background thread and writes a
small ``pending.json`` to the OUTPUT directory whenever a markdown file changes
— never inside the vault itself.

Design contract (mirrors the package invariants):

* **read-only.** The watcher only *observes* the vault; the single filesystem
  write (``pending.json``) is routed through :class:`ReadOnlyGuard.open_write`,
  so it is physically impossible for it to land inside the vault (fail closed).
* **stdlib + watchdog only in the kernel-facing surface.** watchdog lives in the
  adapter layer (like numpy/networkx) so the kernel stays pure.
* **debounced.** Editors fire many events per save (write, flush, rename); we
  collapse bursts with a debounce window and a content hash, so a "save that
  changed nothing" does not trigger a re-scan.

The dashboard polls ``pending.json`` on its auto-refresh tick (every 15 s) and
raises a banner when a rescan is warranted.
"""

from __future__ import annotations

import hashlib
import json
import os
import threading
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable

from ...kernel.guard import ReadOnlyGuard, ReadOnlyViolation

# watchdog is an optional dependency (the `[live]` extra). Importing it here is
# safe — if it is absent, `_Handler` simply is not the watchdog base class and
# `VaultWatcher.start()` reports False, so the dashboard falls back to manual
# re-run. We never want a missing optional dep to break the import.
try:
    from watchdog.events import FileSystemEventHandler
except Exception:  # pragma: no cover - exercised when watchdog is absent
    class FileSystemEventHandler:  # type: ignore[no-redef]
        """Stub used only when watchdog is not installed."""

__all__ = ["VaultWatcher", "LiveStatus", "read_pending", "clear_pending"]


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S")


@dataclass
class LiveStatus:
    """Serializable snapshot of the live-watcher state, written to pending.json."""

    vault_root: str
    last_event_at: str | None        # ISO of the most recent vault file change
    pending: bool                     # True ⇒ vault changed since the last accepted scan
    n_events_since_scan: int
    changed_files_sample: list[str]   # up to 50 most-recent changed .md paths (vault-relative)
    watcher_started_at: str
    updated_at: str

    def to_dict(self) -> dict:
        return asdict(self)


def _file_hash(path: Path) -> str | None:
    """Content hash of a file, or None if it is unreadable / vanished."""
    try:
        h = hashlib.sha256()
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()[:16]
    except OSError:
        return None


class VaultWatcher:
    """Watch a vault (read-only) and signal the dashboard when it changes.

    The watcher is deliberately cheap: it never builds the link graph itself.
    It only answers the question *"has anything under the vault changed since
    the dashboard last rebuilt?"*, by counting + hashing markdown events.

    Usage::

        w = VaultWatcher(vault="F:\\backup", out_dir="F:\\kre-out")
        w.start()              # background thread
        ...
        w.stop()               # join the thread

    All state is mirrored to ``<out>/pending.json`` so a restarted dashboard
    picks up where the last watcher left off.
    """

    # only markdown drives a re-scan — everything else is tooling noise
    _INTEREST = frozenset({".md", ".markdown"})

    def __init__(
        self,
        vault: str | os.PathLike[str],
        out_dir: str | os.PathLike[str],
        *,
        debounce_s: float = 2.0,
        sample_size: int = 50,
    ) -> None:
        self._vault = Path(vault).resolve()
        # The guard both validates out_dir is OUTSIDE the vault and creates it.
        self._guard = ReadOnlyGuard([self._vault])
        self._out_dir = self._guard.assert_out_dir(out_dir)
        self._debounce_s = debounce_s
        self._sample_size = sample_size

        self._lock = threading.Lock()
        self._stop_evt = threading.Event()
        self._thread: threading.Thread | None = None
        self._observer = None            # watchdog Observer (created lazily)
        self._started_at = _now_iso()
        self._last_event_at: str | None = None
        self._n_events = 0
        self._changed: list[str] = []    # vault-relative paths, newest last
        self._known_hashes: dict[str, str] = {}

    # ------------------------------------------------------------- public API
    def start(self) -> bool:
        """Spawn the background observer. Returns False (and no-ops) if watchdog
        is unavailable, so the dashboard degrades to manual re-run gracefully."""
        try:
            from watchdog.observers import Observer
            # FileSystemEventHandler is imported at class-definition time below;
            # this import is the availability probe that decides live vs manual.
            import watchdog.events  # noqa: F401
        except Exception:
            return False

        # mark this scan as accepted immediately on start, so the previous
        # session's "pending" flag does not fire spuriously.
        self._mark_accepted()
        self._stop_evt.clear()

        try:
            self._observer = Observer()
            self._observer.schedule(_Handler(self), str(self._vault), recursive=True)
            self._observer.start()
        except Exception:
            self._observer = None
            return False
        return True

    def stop(self, timeout: float = 3.0) -> None:
        self._stop_evt.set()
        obs = self._observer
        if obs is not None:
            try:
                obs.stop()
                obs.join(timeout)
            except Exception:
                pass
            self._observer = None

    def is_running(self) -> bool:
        obs = self._observer
        return bool(obs is not None and obs.is_alive())

    # ----------------------------------------------------- called by the handler
    def _on_any(self, path: Path, event_kind: str) -> None:
        # ignore non-markdown and anything inside excluded tooling dirs; the
        # scanner has its own canonical exclude set, but we mirror the obvious
        # ones here so the watcher doesn't flap on .git/.obsidian churn.
        if path.suffix.lower() not in self._INTEREST:
            return
        try:
            rel = path.resolve().relative_to(self._vault).as_posix()
        except ValueError:
            return                              # event outside the vault root
        if any(seg in _EXCLUDED_DIRS for seg in path.parts):
            return

        digest = _file_hash(path)
        prev = self._known_hashes.get(rel)
        if digest is not None and digest == prev and event_kind == "modified":
            # a save that left the bytes unchanged — ignore
            return
        if digest is not None:
            self._known_hashes[rel] = digest

        with self._lock:
            self._last_event_at = _now_iso()
            self._n_events += 1
            if rel not in self._changed:
                self._changed.append(rel)
            # keep the sample bounded, newest at the end
            if len(self._changed) > self._sample_size:
                del self._changed[: len(self._changed) - self._sample_size]
        self._flush()

    def _mark_accepted(self) -> None:
        """The dashboard just rebuilt from a fresh scan → clear the pending flag."""
        with self._lock:
            self._n_events = 0
            self._changed.clear()
            self._pending_written = False
        self._flush(force_pending=False)

    # ----------------------------------------------------------- persistence
    _pending_written = False

    def _status(self, force_pending: bool | None = None) -> LiveStatus:
        with self._lock:
            pending = bool(force_pending if force_pending is not None
                           else (self._n_events > 0))
            return LiveStatus(
                vault_root=str(self._vault),
                last_event_at=self._last_event_at,
                pending=pending,
                n_events_since_scan=self._n_events,
                changed_files_sample=list(self._changed),
                watcher_started_at=self._started_at,
                updated_at=_now_iso(),
            )

    def _flush(self, force_pending: bool | None = None) -> None:
        """Write pending.json OUTSIDE the vault (fail-closed via the guard)."""
        st = self._status(force_pending=force_pending)
        try:
            with self._guard.open_write(self._out_dir / "pending.json") as fh:
                json.dump(st.to_dict(), fh, ensure_ascii=False, indent=2)
            if force_pending is False:
                self._pending_written = False
            else:
                self._pending_written = st.pending
        except ReadOnlyViolation:
            # should be impossible — out_dir was validated at construction —
            # but we never want the watcher thread to take the app down.
            pass
        except OSError:
            pass


# --------------------------------------------------------------------- helpers
_EXCLUDED_DIRS = frozenset({
    ".git", ".obsidian", ".claude", ".zcode", ".cursor", ".venv", "venv",
    "__pycache__", "node_modules", "_worktrees",
})


class _Handler(FileSystemEventHandler):
    """Bridge watchdog events into the watcher, on the watchdog thread.

    Must subclass ``FileSystemEventHandler``: watchdog's emitter calls
    ``dispatch(event)`` (defined on the base class), which routes to our
    ``on_modified`` / ``on_created`` / … overrides below. A bare object raises
    ``AttributeError: no attribute 'dispatch'``.

    Debouncing is cooperative: we don't sleep here (that would delay other
    events); instead the dashboard treats ``pending=True`` as advisory and
    rebuilds at most once per refresh tick.
    """

    def __init__(self, watcher: VaultWatcher) -> None:
        super().__init__()
        self._w = watcher

    def _path(self, event) -> Path | None:
        src = getattr(event, "src_path", None)
        return Path(src) if src else None

    def on_modified(self, event) -> None:        # noqa: D401 - watchdog API
        if getattr(event, "is_directory", False):
            return
        p = self._path(event)
        if p is not None:
            self._w._on_any(p, "modified")

    def on_created(self, event) -> None:
        if getattr(event, "is_directory", False):
            return
        p = self._path(event)
        if p is not None:
            self._w._on_any(p, "created")

    def on_deleted(self, event) -> None:
        if getattr(event, "is_directory", False):
            return
        p = self._path(event)
        if p is not None:
            self._w._on_any(p, "deleted")

    def on_moved(self, event) -> None:
        if getattr(event, "is_directory", False):
            return
        # a rename: treat the destination as a creation
        dst = getattr(event, "dest_path", None)
        if dst:
            self._w._on_any(Path(dst), "moved")


# ----------------------------------------------- dashboard-side read helpers
def read_pending(out_dir: str | os.PathLike[str]) -> LiveStatus | None:
    """Read the watcher's pending.json, or None if no watcher ever ran."""
    p = Path(out_dir) / "pending.json"
    if not p.exists():
        return None
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        return LiveStatus(**d)
    except (OSError, ValueError, TypeError):
        return None


def clear_pending(vault: str | os.PathLike[str], out_dir: str | os.PathLike[str]) -> None:
    """Dashboard rebuilt from a fresh scan → mark the watcher's flag accepted.

    This is the one call the dashboard makes after a successful re-run so the
    "vault changed" banner clears until the next real change.
    """
    guard = ReadOnlyGuard([vault])
    out = guard.assert_out_dir(out_dir)
    st = LiveStatus(
        vault_root=str(Path(vault).resolve()),
        last_event_at=None,
        pending=False,
        n_events_since_scan=0,
        changed_files_sample=[],
        watcher_started_at=_now_iso(),
        updated_at=_now_iso(),
    )
    try:
        with guard.open_write(out / "pending.json") as fh:
            json.dump(st.to_dict(), fh, ensure_ascii=False, indent=2)
    except (ReadOnlyViolation, OSError):
        pass
