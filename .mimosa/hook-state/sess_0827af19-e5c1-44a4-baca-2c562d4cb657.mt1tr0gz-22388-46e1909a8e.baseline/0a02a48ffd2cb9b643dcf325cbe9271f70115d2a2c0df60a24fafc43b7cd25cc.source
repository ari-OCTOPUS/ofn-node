"""
coordinator/candidate_bridge.py
================================
آخرین سیکل QA را از paper_ledger.jsonl می‌خواند و
کوین‌هایی را که ارزش ارزیابی Sentinel را دارند برمی‌گرداند.

قوانین فیلتر:
  - forensic_killed == True → حذف (blacklist)
  - final_score < QA_SCORE_FLOOR → حذف
  - هر چیزی دیگه‌ای می‌ماند — حتی vetoed — تا Sentinel هم نظر بده
"""
import json
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Optional

sys.path.insert(0, str(Path(__file__).parent))
from config import QA_LEDGER, QA_SCORE_FLOOR


def load_latest_cycle() -> Optional[Dict]:
    """آخرین سیکل کامل را از ledger برمی‌گرداند."""
    if not QA_LEDGER.exists():
        print(f"[CandidateBridge] ledger not found: {QA_LEDGER}")
        return None
    lines = QA_LEDGER.read_text(encoding="utf-8").strip().splitlines()
    if not lines:
        return None
    return json.loads(lines[-1])


def extract_candidates(cycle: Dict) -> List[Dict]:
    """
    کوین‌های قابل ارزیابی را از سیکل استخراج می‌کند.
    ساختار خروجی:
      {
        symbol, name, age_days, final_score,
        survival_score, antifragile, derivs_score,
        social_score, social_status,
        max_dd_pct, price_7d_pct, price_30d_pct,
        vetoed, veto_reasons, veto_layers,
        forensic_killed, forensic_vetoed, forensic_hold,
        edge_present, edge_decision,
        holder_max_single_pct, holder_chain,
        macro_cq_score, btc_trend,
        cycle_ts, cycle_nulled,
      }
    """
    macro = cycle.get("macro", {})
    cycle_ts      = cycle.get("cycle_ts", "")
    cycle_nulled  = cycle.get("cycle_nulled", True)
    macro_cq      = macro.get("macro_cq_score", 0)
    btc_trend     = macro.get("btc_trend", "UNKNOWN")

    candidates = []
    for c in cycle.get("coins", []):
        sym   = c.get("symbol", "?")
        score = c.get("final_score", 0)

        # حذف blacklist
        if c.get("forensic_killed") or c.get("llm_decision") == "KILLED":
            print(f"[CandidateBridge]   {sym} → skip (BLACKLISTED)")
            continue

        # حذف زیر floor
        if score < QA_SCORE_FLOOR:
            print(f"[CandidateBridge]   {sym} → skip (score={score:.1f} < {QA_SCORE_FLOOR})")
            continue

        # holder data (ممکنه nested یا flat باشه)
        holder = c.get("holder", {}) or {}
        max_single = (c.get("max_single_pct")
                      or holder.get("max_single_pct", 0.0))
        chain = (c.get("holder_chain")
                 or holder.get("chain", ""))

        candidate = {
            # اطلاعات پایه
            "symbol":        sym,
            "name":          c.get("name", sym),
            "age_days":      c.get("age_days", 0),
            "final_score":   score,
            "market_cap":    c.get("market_cap", 0),

            # scores
            "survival_score": c.get("survival_score", 0),
            "antifragile":    c.get("antifragile", 0),
            "derivs_score":   c.get("derivs_score", 0),
            "social_score":   c.get("social_score", 0),
            "social_status":  c.get("social_status", "MISSING"),

            # price action
            "max_dd_pct":    c.get("max_dd_pct", 0),
            "price_7d_pct":  c.get("price_7d_pct", 0),
            "price_30d_pct": c.get("price_30d_pct", 0),

            # QA decisions
            "vetoed":        c.get("vetoed", True),
            "veto_reasons":  c.get("veto_reasons", []),
            "veto_layers":   c.get("veto_layers", []),
            "hold_for_review": c.get("hold_for_review", False),
            "llm_decision":  c.get("llm_decision", "WATCH"),

            # forensics
            "forensic_vetoed": c.get("forensic_vetoed", False),
            "forensic_hold":   c.get("forensic_hold", False),
            "forensic_reasons": c.get("forensic_reasons", []),
            "lp_locked_fv":  c.get("lp_locked_fv", {"status": "MISSING", "value": None}),

            # edge layer
            "edge_present":  c.get("edge_present", []),
            "edge_decision": c.get("edge_decision", "NO_EDGE"),

            # holder
            "holder_max_single_pct": max_single,
            "holder_chain":          chain,
            "holder_status":         holder.get("status", c.get("holder_status", "UNKNOWN")),

            # macro (همان برای همه)
            "macro_cq_score": macro_cq,
            "btc_trend":      btc_trend,
            "cycle_ts":       cycle_ts,
            "cycle_nulled":   cycle_nulled,
        }
        candidates.append(candidate)
        print(f"[CandidateBridge]   {sym} → included "
              f"(score={score:.1f} vetoed={c.get('vetoed')} "
              f"edge={c.get('edge_decision','?')})")

    print(f"[CandidateBridge] {len(candidates)} candidates extracted "
          f"from cycle {cycle_ts[:16]}")
    return candidates


def load_candidates() -> tuple:
    """
    Main entry point.
    Returns (candidates: List[Dict], cycle_meta: Dict)
    """
    cycle = load_latest_cycle()
    if cycle is None:
        return [], {}

    meta = {
        "cycle_ts":     cycle.get("cycle_ts", ""),
        "cycle_nulled": cycle.get("cycle_nulled", True),
        "macro":        cycle.get("macro", {}),
        "n_coins":      cycle.get("n_coins", 0),
    }
    candidates = extract_candidates(cycle)
    return candidates, meta
