"""
LLM Evaluator -- Claude-powered coin analysis (Phase 3 revised)
================================================================
Phase 3 changes (Principle P-C — LLM is ADVISORY):
  3.1: Removed "MUST give ACCUMULATE" and "Keep ACCUMULATE if unchanged" language.
       LLM may return all-WATCH if cohort warrants it. No manufactured conviction.
  3.2: Feeds killer fields to LLM: chain, asset_type, lp_locked_pct (with status),
       holder_concentration_effective, forensic_reasons, deployer_pct.
  3.3: llm_verdict demoted from hard veto to advisory signal. A coin is never
       allocated on LLM enthusiasm alone; forensic/quant gates own kill decisions.
       LLM_VERDICT=WATCH/SKIP is now a SOFT advisory flag in veto_engine.
       (Hard veto pathway: llm_confidence=LOW + score < ceiling still fires.)

P4 retained: Historical context from paper_ledger for consistency.
"""
import json
from pathlib import Path
from collections import defaultdict
from config import ANTHROPIC_API_KEY

_LEDGER_PATH = Path("data/paper_ledger.jsonl")
_MAX_HISTORY_CYCLES = 10


class LLMEvaluator:
    MODEL     = "claude-sonnet-4-5"
    MAX_COINS = 15

    def __init__(self):
        self._client = None
        self._coin_history = self._load_coin_history()
        if not ANTHROPIC_API_KEY:
            print("  [LLMEvaluator] No ANTHROPIC_API_KEY -- skipping Claude eval")
            return
        try:
            from anthropic import Anthropic
            self._client = Anthropic(api_key=ANTHROPIC_API_KEY)
        except ImportError:
            print("  [LLMEvaluator] 'anthropic' package not installed")

    @staticmethod
    def _load_coin_history() -> dict:
        history = defaultdict(lambda: {"decisions": [], "last_score": 0.0})
        if not _LEDGER_PATH.exists():
            return history
        try:
            lines = _LEDGER_PATH.read_text(encoding="utf-8").strip().splitlines()
            for line in lines[-_MAX_HISTORY_CYCLES:]:
                cycle = json.loads(line)
                for coin in cycle.get("coins", []):
                    sym = coin.get("symbol", "").upper()
                    dec = coin.get("llm_decision", "")
                    if sym and dec and dec != "KILLED":
                        history[sym]["decisions"].append(dec)
                        history[sym]["last_score"] = coin.get("final_score", 0.0)
        except Exception as e:
            print(f"  [LLMEvaluator] Could not load coin history: {e}")
        return history

    def evaluate_coins(self, coins: list) -> list:
        # Skip forensic-killed coins — they already have llm_decision=KILLED
        active = [c for c in coins if not c.get("forensic_killed")]
        _default(coins, "WATCH", "Not evaluated")
        if not self._client:
            return coins
        for i in range(0, len(active), self.MAX_COINS):
            self._eval_chunk(active[i : i + self.MAX_COINS])
        return coins

    def _build_coin_line(self, idx: int, c: dict) -> str:
        """Phase 3.2 — include killer fields with their status."""
        age_note = (" <- NEW (<35d, antifragility data limited)"
                    if c["age_days"] < 35 else "")

        # Forensic fields with explicit status
        lp_fv       = c.get("lp_locked_fv", {}) or {}
        lp_status   = lp_fv.get("status", "MISSING")
        lp_val      = lp_fv.get("value")
        lp_str      = (f"{lp_val:.0f}%" if lp_val is not None else lp_status)

        cluster_fv  = c.get("cluster_fv", {}) or {}
        cluster_str = cluster_fv.get("status", "MISSING")
        if cluster_fv.get("status") == "MEASURED" and cluster_fv.get("value") is not None:
            v = cluster_fv["value"]
            cluster_str = (f"{v*100:.0f}%" if isinstance(v, float) else str(v))

        asset_type  = c.get("asset_type", "UNKNOWN")
        chain       = (c.get("holder", {}) or {}).get("chain", "unknown")
        forensic    = "; ".join(c.get("forensic_reasons", [])) or "none"

        # Holder effective concentration
        h           = c.get("holder", {}) or {}
        max_single  = h.get("max_single_pct", 0.0)
        deployer    = h.get("deployer_pct", 0.0)
        h_status    = h.get("status", "UNKNOWN")
        social_st   = c.get("social_status", "MISSING")

        return (
            "%d. %s (%s) | age=%dd%s | chain=%s | asset_type=%s | mcap=$%.1fM\n"
            "   scores: surv=%.0f anti=%.0f social=%.0f[%s] deriv=%.0f final=%.1f/100\n"
            "   price:  maxDD=%+.0f%% 7d=%+.1f%% 30d=%+.1f%%\n"
            "   safety: lp_locked=%s holder_max=%s%%[%s] deployer=%.1f%% cluster=%s\n"
            "   forensic: %s" % (
                idx, c["symbol"], c["name"][:18],
                c["age_days"], age_note, chain, asset_type,
                c.get("market_cap", 0) / 1e6,
                c["survival_score"], c["antifragile"],
                c.get("social_score", 0), social_st,
                c.get("derivs_score", 0), c["final_score"],
                c.get("max_dd_pct", 0), c.get("price_7d_pct", 0),
                c.get("price_30d_pct", 0),
                lp_str, max_single, h_status, deployer, cluster_str,
                forensic,
            )
        )

    def _build_prompt(self, coins: list) -> str:
        lines = [self._build_coin_line(i+1, c) for i, c in enumerate(coins)]

        # P4: History block — preserved but without manufactured consistency pressure
        history_lines = []
        for c in coins:
            sym  = c["symbol"].upper()
            hist = self._coin_history.get(sym, {})
            decs = hist.get("decisions", [])
            if not decs:
                continue
            acc  = decs.count("ACCUMULATE")
            watch= decs.count("WATCH")
            skip = decs.count("SKIP")
            recent = " -> ".join(decs[-3:][::-1])
            history_lines.append(
                "  %s: %d cycle(s) | A=%d W=%d S=%d | last=%s (score=%.1f) | recent: %s" % (
                    sym, len(decs), acc, watch, skip,
                    decs[-1], hist.get("last_score", 0.0), recent,
                )
            )

        history_block = ""
        if history_lines:
            history_block = (
                "\nPRIOR DECISIONS (for context — update freely if fundamentals changed):\n"
                + "\n".join(history_lines) + "\n\n"
            )

        coins_str = "\n\n".join(lines)

        # Phase 3.1: removed "MUST give ACCUMULATE" and consistency-anchoring language
        # Phase 3.3: LLM verdict is advisory — it does not allocate or kill alone
        prompt = (
            "You are a crypto forensic analyst providing an ADVISORY opinion.\n"
            "Your output feeds into an automated pipeline — you do NOT make final decisions.\n"
            "Veto and allocation logic runs separately. Your job: flag risks and assess fundamentals.\n\n"
            "CONTEXT: %d coins passed hard filters (age 14-180d, mcap $100K-$75M, "
            "Binance/Bybit listed). All safety checks not yet run.\n\n"
            "FIELD MEANINGS:\n"
            "- surv: GitHub + exchange presence + supply dist. >=45 solid.\n"
            "- anti: drawdown recovery strength. 0 on <35d coins is normal.\n"
            "- social[status]: LunarCrush score. MISSING/UNRELIABLE = no indexing, not zero community.\n"
            "- deriv: Perp OI+funding signal. >=60 = active positioning.\n"
            "- lp_locked: %% of LP token in burn/locker contracts (MISSING = not yet checked).\n"
            "- holder_max[status]: largest single wallet. HOLD_FOR_REVIEW = chain not supported.\n"
            "- cluster: first-block sniper cluster fraction (MISSING = not checked).\n"
            "- asset_type: MINING_POW = structural mining edge. DEFI_TOKEN/INFRASTRUCTURE = speculative.\n\n"
            "%s"
            "DECISION GUIDE:\n"
            "ACCUMULATE -> fundamentals suggest accumulation AND no forensic red flags.\n"
            "WATCH      -> interesting but concerns exist, or safety fields are MISSING.\n"
            "SKIP       -> clear negative signal: rug structure, dead metrics, high risk.\n\n"
            "RULES:\n"
            "1. MISSING safety field (lp_locked, cluster) -> lean WATCH, not ACCUMULATE.\n"
            "2. If all coins warrant WATCH or SKIP, return that — do not force ACCUMULATE.\n"
            "3. asset_type=DEFI_TOKEN is speculative — treat with extra caution on LP/holder.\n"
            "4. Reasoning: 2-3 sentences. Reference specific field values.\n\n"
            "Coins:\n%s\n\n"
            "Return ONLY a JSON array (same order):\n"
            '[{"symbol":"XXX","decision":"WATCH","confidence":"MEDIUM",'
            '"reasoning":"...","risk_note":"..."}]'
        ) % (len(coins), history_block, coins_str)

        return prompt

    def _eval_chunk(self, chunk: list) -> None:
        prompt = self._build_prompt(chunk)
        try:
            resp = self._client.messages.create(
                model=self.MODEL,
                max_tokens=2400,
                messages=[{"role": "user", "content": prompt}],
            )
            text = resp.content[0].text.strip()
            if "```" in text:
                for seg in text.split("```"):
                    seg = seg.strip().lstrip("json").strip()
                    if seg.startswith("["):
                        text = seg
                        break
            evaluations = json.loads(text)
            eval_map = {e["symbol"].upper(): e for e in evaluations}
            for c in chunk:
                ev = eval_map.get(c["symbol"].upper(), {})
                c["llm_decision"]   = ev.get("decision",   "WATCH")
                c["llm_confidence"] = ev.get("confidence", "LOW")
                c["llm_reasoning"]  = ev.get("reasoning",  "")
                c["llm_risk_note"]  = ev.get("risk_note",  "")
            acc = sum(1 for c in chunk if c.get("llm_decision") == "ACCUMULATE")
            print("  [LLMEvaluator] %d evaluated -- %d ACCUMULATE" % (len(chunk), acc))
        except json.JSONDecodeError as e:
            print("  [LLMEvaluator] JSON parse error: %s" % e)
        except Exception as e:
            print("  [LLMEvaluator] API error: %s" % e)


def _default(coins: list, decision: str, reason: str) -> None:
    for c in coins:
        if not c.get("forensic_killed"):
            c.setdefault("llm_decision",   decision)
            c.setdefault("llm_confidence", "LOW")
            c.setdefault("llm_reasoning",  reason)
            c.setdefault("llm_risk_note",  "")
