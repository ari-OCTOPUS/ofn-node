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

CALL-SITES (one flag-gated line each, via `opslib.kill_seam_denies()`):
  budget/organ_gate.py  (after `stop = opslib.halted()`):
    if not stop and opslib.kill_seam_denies(): stop = "STOP(organism)"
  debate/debate_loop.py (after `stop = opslib.halted(for_debate=True)`):
    if not stop and opslib.kill_seam_denies(): stop = "STOP(organism)"

⚠️ ۲۰۲۶-۰۸-۰۱ — چرا محلِ گزاره جابه‌جا شد: هر دو صداکننده `now_moves` را با
`__import__("now_moves.kill_seam_closer", …)` صدا می‌زدند، ولی هیچ‌کدام `_ops` را
روی `sys.path` ندارند (debate_loop فقط `_ops/debate` و `_ops/budget` می‌گذارد،
model_router هم همین‌طور). پس **مسلح‌کردنِ فلگ رزروِ پولی را deny نمی‌کرد، بلکه با
`ModuleNotFoundError: No module named 'now_moves'` می‌ترکاند** — و چون آن خط
پیش از هر `try` است، حتی یک ردیفِ لاگ هم ثبت نمی‌شد (نقضِ «ثبت همیشه»). حالا
گزارهٔ canonical در `opslib.kill_seam_denies()` است — همان ماژولی که هر دو
صداکننده از قبل import می‌کنند و خودش صاحبِ `STOP_ORGANISM` است — و این ماژول
فقط delegate می‌کند تا یک تعریف بماند نه دو تا. `halted()` دست‌نخورده.

ROLLBACK
  Delete this module + remove the two flag-gated lines (grep kill_seam_denies).
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
    callers behave exactly as before. Read-only, fail-soft (never raises).

    Thin delegate: the canonical predicate lives in `opslib.kill_seam_denies()` so the
    two hot call-sites need no cross-package import. Kept for this module's CLI/API."""
    try:
        p = str(_OPS / "budget")
        if p not in sys.path:
            sys.path.insert(0, p)
        import opslib
        return bool(opslib.kill_seam_denies())
    except Exception:
        return False


def main(argv=None) -> int:
    import json
    print(json.dumps({"flag": FLAG, "flag_active": os.environ.get(FLAG) == "1",
                      "seam_denies": seam_denies()}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
