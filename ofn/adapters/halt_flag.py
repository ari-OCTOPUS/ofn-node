"""halt_flag — the file side of the layer-3 kill switch (I/O adapter).

The Scheduler reads this BEFORE every run creation, not after. HALT stops
STARTS; in-flight work goes to HELD (the outbox already has that state) and
the default on restart is DO-NOT-RESEND, so halting must never duplicate an
external effect.

Resume is the deliberate removal of the flag file — never a "0" written by
an automated loop. `write_halt`/`clear_halt` are owner/supervisor hands.
"""

from __future__ import annotations

from pathlib import Path
from typing import Union

from ofn.kernel import halt
from ofn.kernel.errors import FailClosedError

PathLike = Union[str, Path]


def halt_flag_active(path: PathLike) -> bool:
    """Missing file → not halted (normal state). Present but unreadable or
    unparsable → halted (fail-closed). The predicate itself is
    kernel.halt.is_halted; this adds only the read."""
    p = Path(path)
    try:
        raw = p.read_text(encoding="utf-8") if p.exists() else None
    except (OSError, UnicodeError):
        # Unreadable (I/O) OR un-decodable (not UTF-8) ≙ unparsable intent.
        # UnicodeDecodeError is not an OSError; failing to catch it would
        # let the predicate throw instead of fail closed.
        raw = ""
    return halt.is_halted(raw)


def write_halt(path: PathLike, *, reason: str = "owner") -> None:
    """Arm the switch. Content is always the canonical '1'; the reason is
    recorded by the caller in the incidents log, not smuggled into the
    flag (an unparsable flag must mean HALTED, and a chatty flag would
    collide with that)."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("1\n", encoding="utf-8")


def clear_halt(path: PathLike) -> None:
    """Resume = deliberate removal. Raises if the flag was not armed, so a
    stray clear can never masquerade as an owner decision."""
    p = Path(path)
    if not p.exists():
        raise FailClosedError(f"halt flag not present at {p} — nothing to clear")
    p.unlink()
