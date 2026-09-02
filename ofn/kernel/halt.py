"""Layer-3 kill switch — the pure predicate.

Three containment layers exist (cap, release gate, halt). This module is
only the vocabulary decision for the third one; the file I/O lives in
`ofn.adapters.halt_flag` because reading a flag is I/O and I/O is not
kernel work.

The semantics were paid for twice:

  * An ABSENT switch means RUNNING. The 2026-08-15 NBB-CP inspection
    recorded «kill switch: غایب (طبیعی)» — absence is the normal state,
    not an emergency.
  * A switch we cannot parse means HALTED. Fail-closed on the fact we
    cannot verify — the same rule that reads 403 as policy, not traffic.
    An empty file is unparsable intent: halted.
"""

from __future__ import annotations

from typing import Optional

_HALTED = ("1", "true", "yes", "on")
_RUNNING = ("0", "false", "no", "off")


def is_halted(raw: Optional[str]) -> bool:
    """None (no flag file) → False; known-off words → False;
    known-on words → True; anything else (corrupt, empty, foreign
    vocabulary) → True. The kill switch may fail ON, never silently off."""
    if raw is None:
        return False
    text = raw.strip().lower()
    if text in _RUNNING:
        return False
    if text in _HALTED:
        return True
    return True
