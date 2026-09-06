"""halt_flag — the file side of the layer-3 kill switch (I/O adapter).

The Scheduler reads this BEFORE every run creation, not after. HALT stops
STARTS; in-flight work goes to HELD (the outbox already has that state) and
the default on restart is DO-NOT-RESEND, so halting must never duplicate an
external effect.

Resume is the deliberate removal of the flag file — never a "0" written by
an automated loop. `write_halt`/`clear_halt` are owner/supervisor hands.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Union

from ofn.kernel import halt
from ofn.kernel.errors import FailClosedError

PathLike = Union[str, Path]


def halt_flag_active(path: PathLike) -> bool:
    """Missing file → not halted (normal state). Present but unreadable or
    unparsable → halted (fail-closed). The predicate itself is
    kernel.halt.is_halted; this adds only the read.

    Bytes-first so binary junk cannot raise UnicodeDecodeError out of the
    predicate (P1 close-with-ref / non-UTF-8 fail-closed, kept on rebase).
    """
    p = Path(path)
    try:
        # Symlink first: exists() follows the target, and a planted link
        # is not a flag we can verify. Present-but-not-a-file ≙ HALTED.
        if p.is_symlink():
            return True
        if not p.exists():
            return halt.is_halted(None)
        raw_bytes = p.read_bytes()
        try:
            raw = raw_bytes.decode("utf-8")
        except (UnicodeDecodeError, ValueError, UnicodeError):
            raw = ""  # undecodable intent ≙ HALTED
    except OSError:
        raw = ""  # unreadable ≙ unparsable intent — halted
    return halt.is_halted(raw)


def write_halt(path: PathLike, *, reason: str = "owner") -> None:
    """Arm the switch. Content is always the canonical '1'; the reason is
    recorded by the caller in the incidents log, not smuggled into the
    flag (an unparsable flag must mean HALTED, and a chatty flag would
    collide with that)."""
    p = Path(path)
    # A directory is not a flag. os.replace onto an empty dir can
    # succeed on some POSIX systems — refuse rather than clobber.
    if p.exists() and not p.is_symlink() and p.is_dir():
        raise FailClosedError(
            f"halt flag path is a directory at {p} — refusing replace")
    p.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        os.chmod(p.parent, 0o700)
    except OSError:
        pass
    tmp = p.with_suffix(p.suffix + ".tmp")
    # Binary write: Windows text mode would emit CRLF (b"1\r\n"),
    # which is not the canonical flag. Bytes-first, same as the reader.
    with tmp.open("wb") as f:
        f.write(b"1\n")
        f.flush()
        os.fsync(f.fileno())
    try:
        os.chmod(tmp, 0o600)
    except OSError:
        pass
    os.replace(tmp, p)  # atomic: a reader never observes a torn flag
    try:
        os.chmod(p, 0o600)
    except OSError:
        pass


def clear_halt(path: PathLike) -> None:
    """Resume = deliberate removal. Raises if the flag was not armed, so a
    stray clear can never masquerade as an owner decision.

    A planted symlink is an armed (HALTED) fact — unlink the link, never
    the target. A directory is not a flag and is never rmdir'd.
    """
    p = Path(path)
    if p.is_symlink():
        p.unlink()
        return
    if not p.exists():
        raise FailClosedError(f"halt flag not present at {p} — nothing to clear")
    if p.is_dir():
        raise FailClosedError(
            f"halt flag path is a directory at {p} — will not rmdir")
    if not p.is_file():
        raise FailClosedError(
            f"halt flag path is not a regular file at {p}")
    p.unlink()
