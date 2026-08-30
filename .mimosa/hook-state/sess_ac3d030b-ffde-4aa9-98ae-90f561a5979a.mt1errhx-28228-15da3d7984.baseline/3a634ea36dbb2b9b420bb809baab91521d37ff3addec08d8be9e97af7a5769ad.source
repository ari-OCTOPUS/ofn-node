#!/usr/bin/env python3
"""M2 — staleness_stamp: additive, flag-OFF overlay that stamps organ-freshness
onto the /ops "parts" cells (and the telegram "system" leg) so a STALE snapshot
can never render 🟢. Read-only. Fixes FM-1 (dead cortex renders green) + FM-2
(invisible staleness / the innervation-vs-parts split-brain).

WHY THIS IS PURELY ADDITIVE
  innervation.check() ALREADY computes, per organ, an honest {status, age_min,
  sla_min, connected} from the state-file mtime (cortex/cortex-state.json → 🔴 at
  age>3×SLA). Meanwhile part_loops.summary() derives each cell's 🟢 from the file
  CONTENT (e.g. coherence>=0.7) with NO age check — so a 36h-frozen coherence
  renders green right next to the innervation card that correctly shows cortex 🔴.
  The two surfaces are never reconciled. This module JOINS them: it takes the
  existing summary cells and, for any cell whose innervation organ is a dead-spot
  (or slow), downgrades that cell's glyph and appends the age to its detail. It
  rewrites nothing and NEVER upgrades — only downgrades where innervation has
  ground truth; unmatched cells pass through unchanged.

JOIN KEY
  Both surfaces lead each name with a distinctive emoji (part_loops "🧠 مغز" ↔
  innervation "🧠 مغزِ مرکزی"; "❤️ قلب" ↔ "❤️ قلب"). Key = name.split()[0].

GLYPH CONTRACT (important)
  part_loops cells use BARE glyphs ("🟢"/"🟡"/"⚪") and render.py matches them
  EXACTLY (_LEG_RANK, `st in ("🔴","🟡")`). So this module also sets a BARE glyph
  ("🔴"/"🟡") and carries the age in `detail` (+ a `stale`/`age_min` field). A
  decorated status like "🔴 کهنه" would silently break the leg-rank logic.

FLAG (default OFF — with it unset the panels render EXACTLY as before)
  OCTOPUS_WIRE_STALENESS_STAMP=1   enable stamping at the call-sites.

READ-ONLY: stamp()/stamp_summary() only read innervation and return NEW dicts (the
  input cells are copied, never mutated). No writes anywhere. Detection/annotation
  only — no action, no incident, no state.

CALL-SITES (the sanctioned flag-gated lines, one per render surface):
  live/server.py  (/ops parts card, right after part_loops.summary()):
    if os.environ.get("OCTOPUS_WIRE_STALENESS_STAMP")=="1":
        st["parts"] = <mod>.stamp(st["parts"])
  telegram_center/render.py (_collect_legs, right after `s = pl.summary()`):
    if flag and (m:=_import_soft("now_moves.staleness_stamp")): s = m.stamp_summary(s)

ROLLBACK
  Delete _ops/now_moves/staleness_stamp.py + remove the flag-gated line(s)
  (grep OCTOPUS_WIRE_STALENESS_STAMP). Or just leave the flag unset. Either returns
  every panel to its exact prior rendering — no other module imports this one.

$0 · stdlib-only · fail-soft.
"""
from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent          # _ops/now_moves
_OPS = _HERE.parent                              # _ops

FLAG = "OCTOPUS_WIRE_STALENESS_STAMP"


def _key(name: str) -> str:
    """Join key = the leading emoji/token of a cell/organ name."""
    toks = str(name or "").split()
    return toks[0] if toks else ""


def _hh(age_min) -> str:
    try:
        a = float(age_min)
    except (TypeError, ValueError):
        return "?"
    return f"{a / 60:.0f}h" if a >= 120 else f"{a:.0f}m"


def _annot(detail, age) -> str:
    tag = f"کهنه {_hh(age)}"
    d = str(detail or "").strip()
    return f"{d} · {tag}" if d else tag


def _innervation_check():
    """Lazy read-only innervation.check(). fail-soft → None (never raises)."""
    try:
        p = str(_OPS / "cortex")
        if p not in sys.path:
            sys.path.insert(0, p)
        import innervation
        return innervation.check()
    except Exception:
        return None


def _organ_index(check) -> dict:
    idx = {}
    for o in (check or {}).get("organs", []):
        k = _key(o.get("name", ""))
        if k:
            idx.setdefault(k, o)
    return idx


def stamp(parts, check=None):
    """Return a NEW parts list. Any cell whose innervation organ is a dead-spot
    (🔴/not connected) is set to a bare 🔴 + stale/age_min + age-in-detail; a cell
    currently 🟢 whose organ is slow (🟡) is set to 🟡. Never upgrades. Cells with
    no matching organ pass through unchanged. Pure read-only; never raises; the
    input list/dicts are not mutated."""
    try:
        idx = _organ_index(check if check is not None else _innervation_check())
    except Exception:
        return parts
    if not idx:
        return parts
    out = []
    for p in (parts or []):
        try:
            if not isinstance(p, dict):
                out.append(p)
                continue
            q = dict(p)
            o = idx.get(_key(q.get("name", "")))
            if o is not None:
                age = o.get("age_min")
                ost = str(o.get("status", ""))
                cur = str(q.get("status", ""))
                if age is not None and not o.get("connected", True):
                    q["status"] = "🔴"
                    q["stale"] = True
                    q["age_min"] = age
                    q["detail"] = _annot(q.get("detail"), age)
                elif age is not None and "🟡" in ost and "🟢" in cur:
                    q["status"] = "🟡"
                    q["stale"] = True
                    q["age_min"] = age
                    q["detail"] = _annot(q.get("detail"), age)
            out.append(q)
        except Exception:
            out.append(p)
    return out


def stamp_summary(summary, check=None):
    """Same, but takes/returns a part_loops.summary() dict (stamps its ['parts'])."""
    try:
        s = dict(summary or {})
        s["parts"] = stamp(s.get("parts", []), check=check)
        return s
    except Exception:
        return summary


def main(argv=None) -> int:
    """Read-only demo: stamp the LIVE part_loops.summary() and show which cells the
    freshness join would downgrade. Writes nothing."""
    import json
    try:
        if str(_OPS / "cortex") not in sys.path:
            sys.path.insert(0, str(_OPS / "cortex"))
        import part_loops
        before = part_loops.summary().get("parts", [])
    except Exception as e:
        print(json.dumps({"error": f"{type(e).__name__}: {e}"}, ensure_ascii=False))
        return 0
    after = stamp(before)
    stale = [c for c in after if isinstance(c, dict) and c.get("stale")]
    print(json.dumps({"n_parts": len(before), "n_stamped_stale": len(stale),
                      "stale_cells": [{"name": c.get("name"), "status": c.get("status"),
                                       "detail": c.get("detail"), "age_min": c.get("age_min")}
                                      for c in stale]},
                     ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
