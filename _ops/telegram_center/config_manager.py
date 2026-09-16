#!/usr/bin/env python3
"""ConfigManager — single owner of hot-loop state-file configuration (Wave B).

Owner order 2026-08-21:
- config is read once at boot; reload only on generation/digest change
- every consumer takes an immutable snapshot (copy) — mutation never reaches
  the cached state
- last-known-good + stale=true; a malformed file never replaces the healthy
  snapshot
- no raw Path.read_text / hot-loop read-replace (all reads bounded via
  bounded_io; writes atomic via bounded write + os.replace)

The center's module-level _load_config/_save_config delegates here, so all
existing call sites keep working while the semantics become manager-owned.
"""
from __future__ import annotations

import hashlib
import json
import os
import threading
from pathlib import Path

_OPS = Path(__file__).resolve().parent.parent


class ConfigManager:
    """Thread-safe snapshot config store for one JSON state file."""

    def __init__(self, path: Path, *, reader=None, writer=None,
                 digest_of=None):
        self._path = Path(path)
        self._lock = threading.RLock()
        self._snapshot: dict = {}
        self._lkg: dict = {}
        self._digest: str | None = None
        self._gen: tuple | None = None   # (st_mtime_ns, st_size) fast pre-check
        self._stale: bool = False
        self._booted: bool = False
        self._reader = reader  # callable(path) -> str | None (None on stall)
        self._writer = writer  # callable(path, text) -> bool
        self._digest_of = digest_of  # callable(text) -> str (default sha256)

    @staticmethod
    def _stat_gen(path: Path) -> tuple | None:
        """Lock-free fast generation: (mtime_ns, size); None when unreadable."""
        try:
            st = path.stat()
            return (st.st_mtime_ns, st.st_size)
        except OSError:
            return None

    # ── internals ───────────────────────────────────────────────────────────
    def _read_text(self) -> str | None:
        if self._reader is not None:
            return self._reader(self._path)
        try:
            import bounded_io as _bio
            return _bio.read_text(self._path)
        except Exception:  # noqa: BLE001 — fail-soft read
            return None

    def _write_text(self, text: str) -> bool:
        if self._writer is not None:
            return bool(self._writer(self._path, text))
        try:
            import bounded_io as _bio
            tmp = self._path.with_suffix(self._path.suffix + ".tmp")
            if not _bio.write_text(tmp, text):
                return False
            os.replace(tmp, self._path)
            return True
        except OSError:
            return False

    @staticmethod
    def _compute_digest(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def _ingest(self, text: str) -> dict:
        """Parse; malformed returns {} so LKG logic decides (never crash)."""
        try:
            d = json.loads(text)
            return d if isinstance(d, dict) else {}
        except ValueError:
            return {}

    # ── public API ──────────────────────────────────────────────────────────
    def _refresh_gen(self) -> None:
        self._gen = self._stat_gen(self._path)

    def boot(self) -> dict:
        """First read at startup. Missing/stalled -> {} with stale=True."""
        with self._lock:
            self._booted = True
            self._refresh_gen()
            text = self._read_text()
            if text is None:
                self._stale = True
                return self.get()
            parsed = self._ingest(text)
            if not parsed:
                # malformed or empty: never replaces last-known-good
                self._stale = True
                return self.get()
            self._snapshot = parsed
            self._lkg = parsed
            self._digest = self._digest_of(text) if self._digest_of else self._compute_digest(text)
            self._stale = False
            return self.get()

    def get(self) -> dict:
        """Immutable snapshot for consumers (copy — mutation is never cached)."""
        with self._lock:
            return dict(self._snapshot)

    def reload(self) -> dict:
        """Re-read ONLY when the file generation changed.

        Fast pre-check: stat (lock-free) — unchanged (mtime_ns, size) means no
        read at all. Otherwise a bounded read; digest decides whether the state
        actually changed. On stall/malformed: serve last-known-good + stale.
        """
        with self._lock:
            if not self._booted:
                return self.boot()
            gen = self._stat_gen(self._path)
            if gen is not None and gen == self._gen:
                return self.get()          # same generation: zero I/O
            text = self._read_text()
            if text is None:
                self._stale = True
                try:
                    import health_metrics as _hm
                    _hm.record_config_event("read_timeout")
                except Exception:  # noqa: BLE001
                    pass
                return self.get()          # stale-but-alive beats frozen
            new_digest = self._digest_of(text) if self._digest_of else self._compute_digest(text)
            if new_digest == self._digest:
                self._refresh_gen()        # touched but identical: remember
                return self.get()          # unchanged content: no reload
            parsed = self._ingest(text)
            if not parsed:
                self._stale = True
                try:
                    import health_metrics as _hm
                    _hm.record_config_event("cache_fallback")
                except Exception:  # noqa: BLE001
                    pass
                return self.get()          # malformed never replaces LKG
            self._snapshot = parsed
            self._lkg = parsed
            self._digest = new_digest
            self._refresh_gen()
            self._stale = False
            return self.get()

    def commit(self, cfg: dict) -> bool:
        """Write-through: persist + refresh digest/LKG. Atomic + bounded."""
        with self._lock:
            try:
                text = json.dumps(cfg, ensure_ascii=False, indent=2)
            except (TypeError, ValueError):
                return False
            if not self._write_text(text):
                return False
            self._snapshot = dict(cfg)
            self._lkg = dict(cfg)
            self._digest = self._digest_of(text) if self._digest_of else self._compute_digest(text)
            self._refresh_gen()
            self._stale = False
            return True

    def observe_write(self, cfg: dict) -> None:
        """Refresh manager state after an EXTERNAL successful write (no re-write).
        Used by center._save_config, which keeps its fsync+retry+alert loop."""
        with self._lock:
            try:
                text = json.dumps(cfg, ensure_ascii=False, indent=2)
                self._digest = self._digest_of(text) if self._digest_of else self._compute_digest(text)
            except (TypeError, ValueError):
                return
            self._snapshot = dict(cfg)
            self._lkg = dict(cfg)
            self._refresh_gen()
            self._stale = False

    @property
    def stale(self) -> bool:
        with self._lock:
            return self._stale

    @property
    def last_known_good(self) -> dict:
        with self._lock:
            return dict(self._lkg)

    @property
    def digest(self) -> str | None:
        with self._lock:
            return self._digest


def bounded_json_read(path: Path) -> dict:
    """Bounded JSON read for non-config state (mission sweep, doctor rfcs).
    Returns {} on stall/malformed — callers must treat {} as fail-soft.
    Never blocks the poll loop; never raises on I/O.
    """
    try:
        import bounded_io as _bio
        text = _bio.read_text(path)
        if text is None:
            return {}
        d = json.loads(text)
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}
