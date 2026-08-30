"""Read-only guard — the single enforcement choke point for filesystem writes.

Design contract (mirrors nbb_cp INV-2 / INV-4 / INV-12):

* The vault root is **sacred**. No code path in this package may create, modify,
  rename or delete anything beneath it. Ever.
* There is exactly ONE way to open a file for writing in this package:
  :func:`safe_open_write`. It fails closed.
* Violations raise :class:`ReadOnlyViolation` — they are never downgraded to a
  warning, never swallowed.

stdlib-only by invariant: this module must stay importable without numpy,
networkx, streamlit or anything else.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import IO, Iterable

__all__ = [
    "ReadOnlyViolation",
    "ReadOnlyGuard",
    "safe_open_write",
]

_WRITE_MODES = set("wxa+")


class ReadOnlyViolation(RuntimeError):
    """Raised when any code attempts to write inside a protected root."""


def _resolve(p: str | os.PathLike[str]) -> Path:
    """Absolute, symlink-resolved path. `strict=False` so non-existent output
    paths still normalise (we must reject them *before* they are created)."""
    return Path(p).expanduser().resolve(strict=False)


class ReadOnlyGuard:
    """Holds the set of protected roots and answers 'may I write here?'.

    >>> g = ReadOnlyGuard(["/vault"])
    >>> g.is_protected("/vault/notes/a.md")
    True
    >>> g.is_protected("/out/report.json")
    False
    """

    def __init__(self, protected_roots: Iterable[str | os.PathLike[str]]) -> None:
        roots = [_resolve(r) for r in protected_roots]
        if not roots:
            # Fail closed: a guard with no roots would silently protect nothing.
            raise ReadOnlyViolation("ReadOnlyGuard requires at least one protected root")
        self._roots: tuple[Path, ...] = tuple(roots)

    @property
    def roots(self) -> tuple[Path, ...]:
        return self._roots

    def is_protected(self, path: str | os.PathLike[str]) -> bool:
        target = _resolve(path)
        for root in self._roots:
            if target == root or root in target.parents:
                return True
        return False

    def assert_writable(self, path: str | os.PathLike[str]) -> Path:
        """Return the resolved path, or raise if it lives under a protected root."""
        target = _resolve(path)
        for root in self._roots:
            if target == root or root in target.parents:
                raise ReadOnlyViolation(
                    f"refusing to write inside protected root\n"
                    f"  target : {target}\n"
                    f"  root   : {root}\n"
                    f"The vault is read-only by owner instruction. "
                    f"Point --out at a directory outside it."
                )
        return target

    def assert_out_dir(self, out_dir: str | os.PathLike[str]) -> Path:
        """Validate + create an output directory outside every protected root."""
        target = self.assert_writable(out_dir)
        target.mkdir(parents=True, exist_ok=True)
        return target

    # -- the ONE write path -------------------------------------------------
    def open_write(self, path: str | os.PathLike[str], mode: str = "w", **kw) -> IO:
        if not _WRITE_MODES & set(mode):
            raise ReadOnlyViolation(
                f"open_write called with non-write mode {mode!r}; use plain open() for reads"
            )
        target = self.assert_writable(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        kw.setdefault("encoding", None if "b" in mode else "utf-8")
        return open(target, mode, **kw)


def safe_open_write(guard: ReadOnlyGuard, path: str | os.PathLike[str],
                    mode: str = "w", **kw) -> IO:
    """Module-level alias so call sites read as an explicit guarded write."""
    return guard.open_write(path, mode=mode, **kw)
