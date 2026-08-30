"""
fear_classifier.py — derive `fear_type` for the DISLOCATION edge (E-1)
======================================================================
The DISLOCATION edge in edges.yaml requires a `fear_type` input, but NO
module in the current QuantumAlphaBot pipeline produces it — so the edge
is killed on every coin (`fear_justified_or_unknown`). This module closes
that gap.

Design:
  • Zero API cost — derives purely from fields already MEASURED upstream:
      max_dd_pct          (GemHunter)
      holder_count_delta  (HolderChecker — + means holders GREW during the drawdown)
      forensic_vetoed / forensic_reasons (ScoutForensics)
      btc_trend           (GemHunter macro: ACCUMULATING/NEUTRAL/DISTRIBUTING)
  • Falsifiable (E-1): only PANIC_SELL / SECTOR_CONTAGION can enable the edge;
    INSIDER_DUMP / UNKNOWN are kills. Logic mirrors edges.yaml → fear_falsifiable.
  • E-0 honesty: incomplete data → UNKNOWN (never guess an edge into existence).

Wire in main.py Step 4.4 (AFTER HolderChecker 4.3, BEFORE EdgeClassifier):
    from modules.fear_classifier import classify_fear
    for c in coins:
        c["fear_type"] = classify_fear(c)
"""
from pathlib import Path

FEAR_TYPES = ("PANIC_SELL", "SECTOR_CONTAGION", "INSIDER_DUMP", "UNKNOWN")
# Only these two can enable DISLOCATION (see edges.yaml → DISLOCATION.signature).
EDGE_ENABLING = ("PANIC_SELL", "SECTOR_CONTAGION")

_DEFAULT_DD_FLOOR = 35.0


def _load_dd_floor(default: float = _DEFAULT_DD_FLOOR) -> float:
    """Read DD_FLOOR from edges.yaml if present; else fall back to default.

    Kept defensive so the module is unit-testable standalone (no edges.yaml,
    no pyyaml) — matching the fleet's MEASURED/MISSING robustness discipline.
    """
    try:
        import yaml  # optional dependency
        cfg = yaml.safe_load(Path("edges.yaml").read_text(encoding="utf-8"))
        return float(cfg.get("config_constants", {}).get("DD_FLOOR", default))
    except Exception:
        return default


DD_FLOOR = _load_dd_floor()


def classify_fear(c: dict, dd_floor: float | None = None) -> str:
    """
    Return one of FEAR_TYPES for a coin dict.

    Precedence (first match wins):
      1. Incomplete data           → UNKNOWN        (E-0: cannot falsify)
      2. Forensic flag OR holders fell during dd → INSIDER_DUMP (justified fear)
      3. Macro risk-off + real drawdown          → SECTOR_CONTAGION
      4. Organic drawdown, holders grew/flat      → PANIC_SELL
      5. Otherwise (no real dislocation)          → UNKNOWN
    """
    floor = DD_FLOOR if dd_floor is None else dd_floor

    dd = c.get("max_dd_pct")            # negative %, e.g. -42.0
    hd = c.get("holder_count_delta")    # int; +ve = holders grew during drawdown
    forensic = bool(c.get("forensic_vetoed")) or bool(c.get("forensic_reasons"))
    regime = str(c.get("btc_trend") or "UNKNOWN").upper()

    # 1. E-0: need both drawdown and holder signal to falsify the fear
    if dd is None or hd is None:
        return "UNKNOWN"

    dd = float(dd)
    hd = int(hd)

    # 2. Justified fear — the dislocation may be correct pricing → kill
    if forensic or hd < 0:
        return "INSIDER_DUMP"

    # A real dislocation requires drawdown past the floor (dd <= -floor)
    dislocated = dd <= -abs(floor)

    # 3. Macro-driven sector risk-off, holders stable/growing
    if dislocated and regime == "DISTRIBUTING":
        return "SECTOR_CONTAGION"

    # 4. Organic panic, holders growing/flat, macro not risk-off
    if dislocated and hd >= 0:
        return "PANIC_SELL"

    # 5. No real dislocation (this is beta/fair price, not mispricing)
    return "UNKNOWN"


def enables_edge(fear_type: str) -> bool:
    """True only for fear types that can produce edge_present in DISLOCATION."""
    return fear_type in EDGE_ENABLING
