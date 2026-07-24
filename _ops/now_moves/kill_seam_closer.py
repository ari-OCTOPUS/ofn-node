#!/usr/bin/env python3
"""M5 — kill_seam_closer: additive, flag-OFF guard so the budget authority
organ_gate.reserve() AND the paid debate_loop.run_debate() ALSO honor
STOP_ORGANISM. Read-only predicate. Closes the audit's kill-switch seam.

THE SEAM (audit §Protection, weak control #1)
  opslib.halted() checks STOP_ARCHITECT / STOP_METABOLIC / STOP_DEBATE — but NOT
  _ops/STOP-ORGANISM (the file your telegram /stop and the dashboard kill write).
  Effectors check STOP_ORGANISM directly, but the SPEND authority (organ_gate.
  reserve) and the paid debate loop go through halted() — so a one-tap /stop does
  not by itself stop a paid reservation or a paid debate. This module supplies the
  missing check as a single flag-gated line at each of those two call-sites,
  WITHOUT editing opslib.halted() (which stays the shared source of truth).

FLAG (default OFF — with it unset seam_denies() is always False → zero change)
  OCTOPUS_WIRE_KILL_SEAM=1   make reserve()/run_debate() also deny on STOP-ORGANISM.

CALL-SITES (one flag-gated line each; the flag is checked at the call-site too, so
with it unset this module is never even imported → provably zero behavior change):
  budget/organ_gate.py  (after `stop = opslib.halted()`):
    if <flag> and not stop and <mod>.seam_denies(): stop = "STOP(organism)"
  debate/debate_loop.py (after `stop = opslib.halted(for_debate=True)`):
    if <flag> and not stop and <mod>.seam_denies(): stop = "STOP(organism)"

ROLLBACK
  Delete this module + remove the two flag-gated lines (grep OCTOPUS_WIRE_KILL_SEAM).
  Or just leave the flag unset. Either restores the exact prior gate behavior.

$0 · stdlib-only · fail-soft · read-only (never writes, only checks a flag file).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent          # _ops/now_moves
_OPS = _HERE.parent                              # _ops

FLAG = "OCTOPUS_WIRE_KILL_SEAM"


def seam_denies() -> bool:
    """True iff the flag is ON AND _ops/STOP-ORGANISM exists. Default OFF → False →
    callers behave exactly as before. Read-only, fail-soft (never raises)."""
    if os.environ.get(FLAG) != "1":
        return False
    try:
        p = str(_OPS / "budget")
        if p not in sys.path:
            sys.path.insert(0, p)
        import opslib
        return bool(opslib.STOP_ORGANISM.exists())
    except Exception:
        return False


def main(argv=None) -> int:
    import json
    print(json.dumps({"flag": FLAG, "flag_active": os.environ.get(FLAG) == "1",
                      "seam_denies": seam_denies()}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
