"""
Quantum Capital Allocator
==========================
تخصیص سرمایه با Barbell strategy + Kelly weights.

پس از اعمال VetoEngine:
  ┌───────────────────────────────────────────────────────┐
  │  vetoed=True             →  0% (صرف‌نظر از score)    │
  │  ACCUMULATE + score≥35   →  BUY (full weight)        │
  │  WATCH + score≥35        →  fallback اگه veto خاموشه│
  │  score < 35  OR  SKIP    →  0%                        │
  └───────────────────────────────────────────────────────┘

VetoEngine (veto_engine.py) مسئول تصمیم‌گیری درباره‌ی WATCH/SKIP/مارکو هست.
این module فقط allocation رو انجام می‌ده، نه تصمیم می‌گیره.
"""
import numpy as np
from typing import List, Dict


class QuantumAllocator:
    # Score thresholds
    HIGH_CONVICTION  = 45.0   # score ≥ این → BUY حتی با WATCH
    BUY_THRESHOLD    = 35.0   # score ≥ این + ACCUMULATE → BUY
    WATCH_WEIGHT     = 0.70   # WATCH کوین‌ها ۷۰٪ وزن می‌گیرن

    # Barbell split (Phase 4.1 — asset_type aware, Principle P-E)
    # MINING_POW  → CORE sleeve (structural edge coins: cheap power, ARM fleet)
    # DEFI_TOKEN / INFRASTRUCTURE / UNKNOWN → SPECULATIVE sleeve only
    # Rationale: the bot's structural advantage is mining (electricity < $0.05/kWh,
    # ARM fleet). DEFI_TOKEN/INFRASTRUCTURE coins have no mining thesis — they are
    # pure speculative bets that compete with bots on equal footing.
    # Placing them in CORE would dilute the structural edge thesis.
    CORE_SURV   = 50          # secondary gate within MINING_POW: surv ≥ 50
    CORE_BUDGET = 0.80        # 80% budget → MINING_POW coins
    SPEC_BUDGET = 0.20        # 20% budget → DEFI_TOKEN/INFRASTRUCTURE/UNKNOWN
    SPEC_MAX_SINGLE = 0.10    # hard size cap per SPECULATIVE coin (10% of total budget)

    # Kelly caps
    MAX_SINGLE_ALLOC = 0.45   # حداکثر ۴۵٪ به یه کوین
    MIN_SINGLE_ALLOC = 0.05   # حداقل ۵٪ اگه انتخاب شد

    CONF_MULT = {"HIGH": 1.25, "MEDIUM": 1.00, "LOW": 0.80}

    def allocate(self, coins: List[Dict], total_budget: float = 1000.0) -> List[Dict]:
        """تخصیص $ و % به کوین‌های قابل خرید با Barbell strategy."""
        for c in coins:
            c["allocation_pct"]  = 0.0
            c["allocation_usd"]  = 0.0
            c["buy_tier"]        = "NONE"
            c["allocation_tier"] = "NONE"

        eligible = self._select_eligible(coins)
        if not eligible:
            return coins

        # ── Barbell split — asset_type routing (Phase 4.1 / Principle P-E) ───
        # MINING_POW → CORE (structural thesis coins)
        # Everything else → SPECULATIVE (directional bets, size-capped)
        core = [c for c in eligible
                if c.get("asset_type") == "MINING_POW"
                and c.get("survival_score", 0) >= self.CORE_SURV]
        spec = [c for c in eligible if c not in core]

        if not spec:
            allocs = self._kelly_alloc(core, total_budget, total_budget)
            self._assign(coins, allocs, total_budget, "CORE")
        elif not core:
            # All speculative — cap each at SPEC_MAX_SINGLE of total budget
            spec_budget = total_budget * self.SPEC_BUDGET
            allocs = self._kelly_alloc(spec, spec_budget, total_budget,
                                       max_single_usd=total_budget * self.SPEC_MAX_SINGLE)
            self._assign(coins, allocs, total_budget, "SPECULATIVE")
        else:
            core_allocs = self._kelly_alloc(core,
                                            total_budget * self.CORE_BUDGET,
                                            total_budget)
            spec_allocs = self._kelly_alloc(spec,
                                            total_budget * self.SPEC_BUDGET,
                                            total_budget,
                                            max_single_usd=total_budget * self.SPEC_MAX_SINGLE)
            self._assign(coins, core_allocs, total_budget, "CORE")
            self._assign(coins, spec_allocs, total_budget, "SPECULATIVE")

        return coins

    def _kelly_alloc(self, group: List[Dict],
                     group_budget: float,
                     total_budget: float,
                     max_single_usd: float = None) -> Dict[str, float]:
        """وزن‌دهی Kelly-inspired داخل یه گروه → {symbol: $amount}"""
        # Defensive: apply WATCH_WEIGHT even here.
        # Primary gate: VetoEngine blocks WATCH coins before allocation.
        # Secondary gate: if llm_verdict veto is disabled (or a WATCH coin
        # slips through for any reason), it still only gets WATCH_WEIGHT
        # allocation weight rather than silently matching ACCUMULATE coins.
        # This makes ENABLED_RULES["llm_verdict"] = False a safe toggle.
        scores = np.array([
            max(c.get("final_score", 1), 1.0)
            * self.CONF_MULT.get(c.get("llm_confidence", "MEDIUM"), 1.0)
            * (self.WATCH_WEIGHT if c.get("llm_decision") == "WATCH" else 1.0)
            for c in group
        ], dtype=float)

        weights = scores / scores.sum()

        # cap: نسبت به کل بودجه (or hard SPECULATIVE cap if provided)
        cap_usd = max_single_usd if max_single_usd is not None else (self.MAX_SINGLE_ALLOC * total_budget)
        max_w = min(cap_usd / max(group_budget, 1), 1.0)
        weights = np.minimum(weights, max_w)
        if weights.sum() > 0:
            weights = weights / weights.sum()

        # floor: نسبت به کل بودجه + نمی‌تونه بیشتر از 1/n بشه
        min_w = min(
            self.MIN_SINGLE_ALLOC * total_budget / max(group_budget, 1),
            1.0 / max(len(group), 1)
        )
        for i in range(len(weights)):
            if weights[i] < min_w:
                weights[i] = min_w
        if weights.sum() > 0:
            weights = weights / weights.sum()

        return {c["symbol"]: float(weights[i]) * group_budget
                for i, c in enumerate(group)}

    def _assign(self, coins: List[Dict], allocs: Dict[str, float],
                total_budget: float, tier_name: str) -> None:
        """$ و % و tier رو به کوین‌ها اختصاص می‌ده."""
        for c in coins:
            usd = allocs.get(c["symbol"])
            if usd is None:
                continue
            c["allocation_usd"]  = round(usd, 2)
            c["allocation_pct"]  = round(usd / total_budget * 100, 1)
            c["allocation_tier"] = tier_name
            c["buy_tier"]        = self._buy_tier_label(c)

    def _buy_tier_label(self, c: Dict) -> str:
        """label نشان‌دهنده قدرت توصیه خرید"""
        dec   = c.get("llm_decision", "WATCH")
        score = c.get("final_score", 0)
        if score >= self.HIGH_CONVICTION and dec != "SKIP":
            return "🔥 STRONG BUY"
        elif dec == "ACCUMULATE":
            return "✅ BUY"
        else:
            return "🔸 BUY SMALL"

    def _select_eligible(self, coins: List[Dict]) -> List[Dict]:
        """
        Post-veto eligibility backstop.

        VetoEngine (called upstream) handles the main gate:
          - WATCH/SKIP → vetoed
          - drawdown / social / macro → vetoed

        This method only needs to:
          1. Skip vetoed coins (set by VetoEngine)
          2. Skip SKIP decisions (belt-and-suspenders)
          3. Enforce minimum score floor (BUY_THRESHOLD)

        Note: HIGH_CONVICTION (≥45) no longer overrides LLM verdict.
        It only affects buy_tier_label (STRONG BUY vs BUY). If a coin
        reaches here with vetoed=False, its LLM decision was ACCUMULATE.
        """
        out = []
        for c in coins:
            if c.get("vetoed", False):
                continue
            if c.get("hold_for_review", False):
                continue      # unverified holder data — no allocation
            dec   = c.get("llm_decision", "WATCH")
            score = c.get("final_score", 0)
            if dec == "SKIP":
                continue
            if score >= self.BUY_THRESHOLD:
                out.append(c)
        return out

    def summary_str(self, coins: List[Dict], total_budget: float = 1000.0) -> str:
        items = [(c["symbol"], c["allocation_pct"], c["buy_tier"],
                  c.get("allocation_tier", ""))
                 for c in coins if c.get("allocation_pct", 0) > 0]
        if not items:
            return "Allocation: no eligible coins (all SKIP or score < 35)"
        parts = [f"{s} {p:.0f}% {t}" for s, p, t, _ in items]
        return f"Budget ${total_budget:.0f} → " + "  |  ".join(parts)
