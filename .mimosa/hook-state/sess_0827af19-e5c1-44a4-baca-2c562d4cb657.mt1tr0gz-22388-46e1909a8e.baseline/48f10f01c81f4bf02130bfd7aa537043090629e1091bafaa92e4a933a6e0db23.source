"""
coordinator/confluence_scorer.py
==================================
امتیاز نهایی از ترکیب QA + Sentinel و تعیین action.

فرمول:
  qa_contrib     = (final_score/100) + edge_bonus + forensic_bonus   → 0..1.3 → clamp 0..1
  sentinel_contrib = kelly_frac + max(0, score_modifier/12)          → 0..1.8 → clamp 0..1
  confluence     = qa_contrib × QA_WEIGHT + sentinel_contrib × SENT_WEIGHT

Gate‌های سخت (همه باید True باشند):
  ① forensic_vetoed == False
  ② edge_present != []
  ③ sentinel_quadrant not in BLOCKED_QUADRANTS
  ④ macro_cq_score > MACRO_GATE_FLOOR  (macro gate)
  ⑤ kelly_frac >= MIN_KELLY_FOR_ACTION
  ⑥ final_score >= QA_SCORE_FLOOR
"""
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Optional

sys.path.insert(0, str(Path(__file__).parent))
from config import (
    QA_WEIGHT, SENT_WEIGHT,
    EDGE_BONUS, FORENSIC_BONUS, QA_SCORE_FLOOR,
    MIN_KELLY_FOR_ACTION, BLOCKED_QUADRANTS, MACRO_GATE_FLOOR,
    CONFLUENCE_THRESHOLD, WATCH_THRESHOLD,
    MINING_EDGES, BUYING_EDGES, NODE_EDGES,
    SENTINEL_DIR, SENTINEL_API_DELAY,
)


@dataclass
class ConfluenceResult:
    symbol:          str
    name:            str

    # scores
    qa_contrib:      float = 0.0
    sentinel_contrib:float = 0.0
    confluence:      float = 0.0

    # gates
    gates_passed:    bool  = False
    gate_failures:   List[str] = field(default_factory=list)

    # sentinel details
    sentinel_quadrant: str   = "UNKNOWN"
    sentinel_kelly:    float = 0.0
    sentinel_modifier: float = 0.0
    sentinel_conviction: str = ""
    sentinel_social:   Optional[float] = None
    sentinel_macro:    Optional[float] = None

    # action
    action:          str   = "NO_ACTION"   # MINE | BUY | MINE+BUY | NODE | WATCH | NO_ACTION
    action_reason:   str   = ""

    # passthrough QA fields
    final_score:     float = 0.0
    edge_present:    List[str] = field(default_factory=list)
    vetoed:          bool  = True
    veto_layers:     List[str] = field(default_factory=list)
    forensic_hold:   bool  = False
    cycle_ts:        str   = ""


class ConfluenceScorer:
    """
    ترکیب‌کننده‌ی نتایج QA و Sentinel.
    Sentinel را import می‌کند — نیاز به SENTINEL_DIR در sys.path دارد.
    """

    def __init__(self):
        self._fusion = None
        self._init_sentinel()

    def _init_sentinel(self):
        """Sentinel's SignalFusion را با API clients واقعی init می‌کند."""
        try:
            sys.path.insert(0, str(SENTINEL_DIR))
            from signal_fusion import SignalFusion
            from lc_client import LunarCrushClient
            from cq_client import CryptoQuantClient
            import yaml

            cfg_path = SENTINEL_DIR / "config.yaml"
            cfg = {}
            if cfg_path.exists():
                with open(cfg_path) as f:
                    cfg = yaml.safe_load(f) or {}

            lc_key  = cfg.get("lunarcrush_api_key", "")
            cq_key  = cfg.get("cryptoquant_api_key", "")

            lc  = LunarCrushClient(api_key=lc_key)  if lc_key  else None
            cq  = CryptoQuantClient(api_key=cq_key) if cq_key  else None

            self._fusion = SignalFusion(lc_client=lc, cq_client=cq)
            print("[ConfluenceScorer] Sentinel SignalFusion ready")
        except Exception as e:
            print(f"[ConfluenceScorer] Sentinel import failed: {e}")
            print("[ConfluenceScorer] running in QA-only mode (no Sentinel signals)")
            self._fusion = None

    def score_all(self, candidates: List[Dict]) -> List[ConfluenceResult]:
        results = []
        for c in candidates:
            r = self.score_one(c)
            results.append(r)
            sym   = r.symbol
            label = f"confluence={r.confluence:.2f} action={r.action}"
            if r.gates_passed and r.confluence >= CONFLUENCE_THRESHOLD:
                print(f"[ConfluenceScorer] ✓ {sym} → SIGNAL! {label}")
            else:
                gates_str = " | ".join(r.gate_failures) if r.gate_failures else "ok"
                print(f"[ConfluenceScorer]   {sym} → {label} | gates: {gates_str}")
            time.sleep(SENTINEL_API_DELAY)
        return results

    def score_one(self, c: Dict) -> ConfluenceResult:
        r = ConfluenceResult(
            symbol       = c["symbol"],
            name         = c.get("name", c["symbol"]),
            final_score  = c.get("final_score", 0),
            edge_present = c.get("edge_present", []),
            vetoed       = c.get("vetoed", True),
            veto_layers  = c.get("veto_layers", []),
            forensic_hold= c.get("forensic_hold", False),
            cycle_ts     = c.get("cycle_ts", ""),
        )

        # ── QA contribution ──────────────────────────────────────────────────
        qa_base = c.get("final_score", 0) / 100.0
        has_edge     = bool(c.get("edge_present"))
        forensic_ok  = (not c.get("forensic_vetoed")
                        and not c.get("forensic_hold")
                        and c.get("lp_locked_fv", {}).get("status") == "MEASURED")
        r.qa_contrib = min(
            qa_base
            + (EDGE_BONUS     if has_edge    else 0.0)
            + (FORENSIC_BONUS if forensic_ok else 0.0),
            1.0
        )

        # ── Gate checks ───────────────────────────────────────────────────────
        if c.get("forensic_vetoed"):
            r.gate_failures.append("forensic_vetoed")

        if not has_edge:
            r.gate_failures.append("no_edge (edge_present=[])")

        if c.get("final_score", 0) < QA_SCORE_FLOOR:
            r.gate_failures.append(f"qa_score<{QA_SCORE_FLOOR}")

        macro_ok = c.get("macro_cq_score", 0) > MACRO_GATE_FLOOR
        if not macro_ok:
            r.gate_failures.append(
                f"macro_cq={c.get('macro_cq_score',0)} ≤ {MACRO_GATE_FLOOR} (distributing)")

        # ── Sentinel signal ───────────────────────────────────────────────────
        if self._fusion is not None:
            try:
                result = self._fusion.compute(c["symbol"])
                r.sentinel_quadrant  = result.quadrant
                r.sentinel_kelly     = result.kelly_frac
                r.sentinel_modifier  = result.score_modifier
                r.sentinel_conviction= result.conviction
                r.sentinel_social    = result.social_signal
                r.sentinel_macro     = result.macro_regime

                # gate: blocked quadrant
                if result.quadrant in BLOCKED_QUADRANTS:
                    r.gate_failures.append(f"sentinel_quadrant={result.quadrant}")

                # gate: kelly too low
                if result.kelly_frac < MIN_KELLY_FOR_ACTION:
                    r.gate_failures.append(
                        f"kelly={result.kelly_frac:.2f} < {MIN_KELLY_FOR_ACTION}")

                r.sentinel_contrib = min(
                    result.kelly_frac
                    + max(0.0, result.score_modifier / 12.0),
                    1.0
                )
            except Exception as e:
                print(f"[ConfluenceScorer]   {c['symbol']} Sentinel error: {e}")
                r.sentinel_quadrant = "UNKNOWN"
                r.gate_failures.append(f"sentinel_error: {e}")
        else:
            # QA-only mode: sentinel contribution را از macro داریم
            macro_score = c.get("macro_cq_score", 20) / 100.0  # 0..1
            r.sentinel_quadrant  = "MACRO_ONLY"
            r.sentinel_kelly     = 0.3 if macro_ok else 0.1
            r.sentinel_contrib   = r.sentinel_kelly
            r.gate_failures.append("sentinel_unavailable (QA-only mode)")

        # ── Confluence ────────────────────────────────────────────────────────
        r.confluence  = round(
            r.qa_contrib   * QA_WEIGHT
            + r.sentinel_contrib * SENT_WEIGHT,
            3
        )
        r.gates_passed = len(r.gate_failures) == 0

        # ── Action routing ────────────────────────────────────────────────────
        r.action, r.action_reason = self._route_action(r, c)
        return r

    @staticmethod
    def _route_action(r: ConfluenceResult, c: Dict) -> tuple:
        if not r.gates_passed:
            return ("NO_ACTION",
                    "Gates failed: " + " | ".join(r.gate_failures))

        if r.confluence < WATCH_THRESHOLD:
            return ("NO_ACTION",
                    f"confluence={r.confluence:.2f} < watch_threshold={WATCH_THRESHOLD}")

        if r.confluence < CONFLUENCE_THRESHOLD:
            return ("WATCH",
                    f"confluence={r.confluence:.2f} — below accumulate threshold")

        # بالای threshold — action تعیین می‌شه از edge
        edges = set(r.edge_present)
        has_mining = bool(edges & MINING_EDGES)
        has_buying = bool(edges & BUYING_EDGES)
        has_node   = bool(edges & NODE_EDGES)

        if has_mining and has_buying:
            return ("MINE+BUY",
                    f"ENERGY+DISLOCATION — mine AND DCA | {r.sentinel_quadrant}")
        elif has_mining:
            return ("MINE",
                    f"ENERGY edge — mine in launch window | {r.sentinel_quadrant}")
        elif has_buying:
            return ("BUY",
                    f"DISLOCATION edge — DCA on weakness | {r.sentinel_quadrant}")
        elif has_node:
            return ("RUN_NODE",
                    f"YIELD edge — operate node | {r.sentinel_quadrant}")
        else:
            return ("NO_ACTION", "edge_present but no known routing")
