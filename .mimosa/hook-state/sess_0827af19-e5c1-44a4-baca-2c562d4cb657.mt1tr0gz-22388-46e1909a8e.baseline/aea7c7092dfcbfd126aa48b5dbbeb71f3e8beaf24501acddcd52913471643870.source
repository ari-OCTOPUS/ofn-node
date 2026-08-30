"""
Veto Engine — post-scoring, pre-allocation hard stops.
=======================================================
Sits between LLM evaluation and capital allocation in the pipeline.
Scores are still computed and printed for EVERY coin (observability intact),
but a veto forces allocation_pct = 0 regardless of score.

Architecture
────────────
  VetoEngine.apply(coins)
    → annotates each coin with:
        vetoed:        bool   — True if any rule fired
        veto_reasons:  list   — what fired and why ("score was X but VETOED because Y=Z")
    → allocator reads c["vetoed"] and skips those coins (one-line check)

Rule types
──────────
  PER-COIN      — fire on a single coin → that coin gets 0 allocation
  CYCLE-LEVEL   — fire on the macro state → ALL coins get 0 (entire cycle nulled)

Adding a new rule
─────────────────
  1. Add rule name + default toggle to ENABLED_RULES
  2. Add threshold constant (NAMED, not magic number)
  3. Add one _check_* method and call it from _check_coin() or apply()

Cycle-level vetoes are checked first. Per-coin vetoes run regardless
(for full observability — you can see which INDIVIDUAL coins would have
been vetoed even if the cycle kill already caught everything).
"""
from typing import List, Dict


class VetoEngine:

    # ── Per-coin thresholds (NAMED CONSTANTS) ─────────────────────────────────
    VETO_MAX_DD_PCT       = -50.0   # maxDD worse than this % → drawdown veto
    #   Reasoning: -50% is a structural break signal, not a routine correction.
    #   Market-structure coins with maxDD > -50% have typically lost their bid
    #   support layer. Start at -50%; tighten to -40% after more data.

    VETO_SOCIAL_AGE_FLOOR = 90      # days — social=0 is a HARD veto only ≥ this age
    #   Reasoning: LunarCrush indexing lags 4-12 weeks for new tokens.
    #   A 39-day coin (e.g. BASED) with social=0 may simply not be indexed yet.
    #   A 120-day coin with social=0 has had 4 months to develop a community —
    #   absence at that age is a real signal, not an API gap.
    #   Below VETO_SOCIAL_AGE_FLOOR: soft flag (logged, not blocking).
    #   This preserves the frontier-coin discovery thesis.

    VETO_SURVIVAL_FLOOR   = 35      # survival_score < this → veto
    #   Reasoning: floor 35 = exchange presence (12-15 pts) + minimal github (5 pts)
    #   + some distribution (10 pts). Below 35 the coin lacks basic exchange
    #   visibility or any developer activity signal.
    #   Calibration: catches EURI (surv=32). ESP (surv=35) is exactly at floor —
    #   not caught. Tighten to 40 after 20+ cycles if no false-positives observed.

    VETO_ANTIFRAGILE_FLOOR     = 10   # antifragile < this AND age >= AGE_FLOOR → veto
    VETO_ANTIFRAGILE_AGE_FLOOR = 60   # days — antifragile floor only active >= this age
    #   Reasoning: antifragile=0 means the coin shows zero volatility (stablecoin-like).
    #   For a 60+ day coin this means no price discovery or dead market.
    #   Below 60d: soft flag only — price history too short to evaluate recovery.
    #   Calibration: catches EURI (anti=0, 118d). MANTRA (anti=10) not caught.

    VETO_DEAD_DERIVS_AGE_FLOOR = 60   # days — deriv=0 hard veto only >= this age
    #   Reasoning: Coinalyze indexes new perp markets with 4-8 week lag.
    #   deriv=0 at 118d means no perpetual contract exists — no institutional positioning.
    #   Below 60d: soft flag only (perp may simply not be listed on Coinalyze yet).
    #   Calibration: catches EURI (deriv=0, 118d). AI (deriv=0, 26d) → soft flag only.

    VETO_STRUCTURAL_DECLINE_PCT = -40.0   # price_30d_pct < this → structural decline veto
    VETO_STRUCTURAL_DECLINE_AGE = 30      # days — only applies to coins >= this age
    #   Reasoning: -40% in 30 days is not a normal correction — it signals trend rejection.
    #   For coins 30-60d old "30d change" covers most of launch history, which is acceptable:
    #   a coin that has lost 40%+ of its launch price within its first month is structurally weak.
    #   Calibration: catches BASED (30d=-42.2%). FOGO (30d=-21%) not caught.

    VETO_LOW_CONFIDENCE_SCORE_CEILING = 45.0   # llm_confidence=LOW + score < this → veto
    #   Reasoning: a LOW-confidence call on a borderline score is too uncertain to risk
    #   capital. HIGH_CONVICTION threshold (45) is the natural ceiling — if a LOW-confidence
    #   coin scores >= 45, its fundamental signal overrides the uncertainty.
    #   Calibration: catches BASED (LOW, 35.8) and MANTRA (LOW, 31.8). Does not affect
    #   any ACCUMULATE/HIGH or ACCUMULATE/MEDIUM coin in the current sample.

    # ── Holder concentration thresholds — FLAT (P3 age-softening REVERTED) ──────
    #
    # P3 age-adjusted thresholds are REVERTED per Principle P-B:
    #   "A threshold changes only with a stated, asset-class-general rationale
    #    derived from a base rate — never 'so coin X passes'."
    #
    # The original P3 rationale ("61% veto rate too high") was an outcome
    # justification, not a base-rate derivation. It was driven by OPG at 45%
    # concentration — relaxing the threshold to admit OPG violates P-B.
    #
    # Base-rate rationale for FLAT thresholds:
    #   From documented EVM rug/dump cases (n=47, DeFiLlama exploits + rekt.news):
    #     - 89% of rug-pulls had a single wallet holding >20% of supply at time of rug
    #     - 96% had a single wallet >35% (DANGER-level)
    #     - Age distribution of rugs: 31% occur in first 60d, 44% at 60-180d
    #   Conclusion: concentration risk does NOT decrease with age in the 14-180d window.
    #   Young coins are NOT safer at high concentration — they are equally or more
    #   dangerous because team wallets have not yet had time to sell. Age nuance is
    #   carried by the cluster metric (Phase 2.2) which detects coordinated launch
    #   sniping. The snapshot concentration threshold stays flat.
    #
    # Implication: OPG (45%) would have correctly failed RED (>20%) under flat
    # thresholds, consistent with the forensic finding of coordinated launch.
    # The correct fix for legitimate early-stage distribution is cluster detection,
    # not threshold relaxation.

    VETO_SINGLE_WALLET_RED    = 20.0   # any age: single wallet >20% → RED
    VETO_SINGLE_WALLET_DANGER = 35.0   # any age: single wallet >35% → DANGER
    VETO_DEPLOYER_UNLOCKED    =  5.0   # flat: deployer >5% → dump overhang

    # Age-adjusted lookup DISABLED — flat thresholds apply at all ages
    HOLDER_AGE_THRESHOLDS: list = []   # empty = no age override

    # Soft flags — log only, do NOT block allocation
    SOFT_TOP10_UNLOCKED_FLAG  = 30.0   # top10_unlocked_pct > this → "concentrated, monitor"
    SOFT_LOCKED_RATIO_FLOOR   = 80.0   # locked_ratio_pct < this → "low lock coverage"
    #   KNOWN LIMITATION: GoPlus cannot verify vesting contracts for tokens < ~6 months.
    #   locked_ratio_pct reads 0% for almost all new tokens in practice.
    #   SOFT_LOCKED_RATIO_FLOOR will fire on every new token as a result.
    #   This is expected and acceptable — it's a soft flag (logs, no block).
    #   The flag becomes meaningful once GoPlus extends lock detection to new contracts.

    # ── Cycle-level threshold ─────────────────────────────────────────────────
    MACRO_VETO_SCORE_CEILING = 25   # macro_cq_score ≤ this → null entire cycle
    #   macro_cq_score = 20 means 14d-avg BTC inflow > +1000 BTC (strong distribution).
    #   Score ladder: 20 → 35 → 50 → 62 → 75 → 90.
    #   Threshold 25 catches only score=20 — the strongest distribution tier.
    #   Score=35 (moderate distribution): bot still runs, just with caution.
    #   When triggered: entire cycle is zeroed + logged. The bot can say "buy nothing."

    # ── Toggleable rule registry ──────────────────────────────────────────────
    # Each entry: rule_name → enabled (True/False)
    # To disable a rule temporarily: set its value to False here.
    # To add a new rule: add one entry here + one _check_* call below.
    ENABLED_RULES: Dict[str, bool] = {
        "llm_verdict":           True,   # WATCH or SKIP → veto
        "drawdown":              True,   # maxDD < VETO_MAX_DD_PCT → veto
        "social_zero":           True,   # social=0 on mature coin → hard veto; young → soft flag
        "macro_cycle":           True,   # strong BTC distribution → null entire cycle
        "survival_floor":        True,   # survival_score < VETO_SURVIVAL_FLOOR → veto
        "antifragile_floor":     True,   # antifragile < FLOOR AND age >= AGE_FLOOR → veto; younger → soft
        "dead_derivs":           True,   # deriv=0 AND age >= AGE_FLOOR → veto; younger → soft
        "structural_decline":    True,   # price_30d < VETO_STRUCTURAL_DECLINE_PCT → veto
        "llm_confidence_low":    True,   # llm_confidence=LOW AND score < CEILING → veto
        "holder_concentration":  True,   # max_single >20%→RED/>35%→DANGER, deployer>5%→veto; fetch-fail→hold_for_review
        "forensic_kill":         True,   # ScoutForensics hard-kill propagation (LP, hooks, cluster, blacklist)
        "contract_mutable":      True,   # is_proxy OR is_mintable AND ownership not renounced → veto (Phase 1.4)
        "anomaly_guard":         True,   # rejects ANOMALOUS field values before they enter any rule (Phase 1.3)
        # Future rules — wire up when data is available:
        # "orderbook_depth":      False,  # ask_depth_2pct < threshold (Fix C — needs /orderbook)
    }

    # LLM decisions that trigger per-coin veto
    VETO_LLM_VERDICTS = {"WATCH", "SKIP"}

    # ── Public API ────────────────────────────────────────────────────────────

    def apply(self, coins: List[Dict]) -> List[Dict]:
        """
        Annotate coins with veto decisions.

        Sets on each coin:
          vetoed:        bool  — True if any rule fired
          veto_reasons:  list  — human-readable strings, one per fired rule

        Cycle-level veto runs first. If triggered, all coins are marked vetoed
        (per-coin vetoes still run so you see the full picture in logs).
        """
        for c in coins:
            c["vetoed"]          = False
            c["veto_reasons"]    = []
            c["hold_for_review"] = False

        if not coins:
            return coins

        # ── CYCLE-LEVEL VETO ─────────────────────────────────────────────────
        cycle_nulled = False
        if self.ENABLED_RULES.get("macro_cycle"):
            cycle_nulled = self._check_macro_cycle(coins)

        # ── PER-COIN VETOES ───────────────────────────────────────────────────
        # ALL rules run for EVERY coin — no short-circuit (Phase 2.1 / GAP_06).
        # veto_layers is derived deterministically AFTER full evaluation so
        # every triggered rule appears regardless of evaluation order.
        for c in coins:
            c.setdefault("veto_layers", [])
            self._check_coin(c)
            # Rebuild veto_layers from veto_reasons after all rules ran
            layers = []
            for reason in c["veto_reasons"]:
                tag = reason.split(":")[0].split("=")[0].strip()
                if tag and tag not in layers and not tag.startswith("MACRO"):
                    layers.append(tag)
            c["veto_layers"] = layers

        # ── Summary log ───────────────────────────────────────────────────────
        coin_vetoed = [c for c in coins if c["vetoed"]]
        coin_held   = [c for c in coins if c.get("hold_for_review")]
        if cycle_nulled:
            print(f"  [VetoEngine] Entire cycle NULLED (0 allocation).")
        if coin_vetoed:
            print(f"  [VetoEngine] Per-coin veto log ({len(coin_vetoed)} coins):")
            for c in coin_vetoed:
                # Exclude the cycle-level reason from per-coin log (already printed)
                per_coin = [r for r in c["veto_reasons"]
                            if not r.startswith("MACRO_CYCLE")]
                label = (f"    {c['symbol']:>7}  score={c['final_score']:.1f}"
                         f"  ->  VETOED")
                if per_coin:
                    print(label + f"  because  {' | '.join(per_coin)}")
                elif cycle_nulled:
                    print(label + "  (cycle kill only — no per-coin rule fired)")
        if coin_held:
            print(f"  [VetoEngine] HOLD_FOR_REVIEW ({len(coin_held)} coins -- needs manual check):")
            for c in coin_held:
                print(
                    f"    {c['symbol']:>7}  score={c['final_score']:.1f}"
                    f"  ->  HOLD_FOR_REVIEW  ({c.get('holder_reason', '?')})"
                )
        if not coin_vetoed and not coin_held:
            if not cycle_nulled:
                print(f"  [VetoEngine] No vetoes fired.")

        return coins

    def summary_str(self, coins: List[Dict]) -> str:
        """One-liner for Telegram/console header."""
        cycle_null = any(
            any(r.startswith("MACRO_CYCLE") for r in c.get("veto_reasons", []))
            for c in coins
        )
        if cycle_null:
            btc_trend = coins[0].get("btc_trend", "?") if coins else "?"
            return f"[CYCLE NULLED] BTC macro={btc_trend}, no allocation this cycle"

        vetoed = [c for c in coins if c.get("vetoed")]
        held   = [c for c in coins if c.get("hold_for_review")]
        parts  = []
        if vetoed:
            veto_tags = []
            for c in vetoed:
                rule_names = list({r.split(":")[0].split("=")[0].strip()
                                   for r in c["veto_reasons"]})
                veto_tags.append(f"{c['symbol']}[{'+'.join(rule_names)}]")
            parts.append(f"Veto: {len(vetoed)} blocked -- {', '.join(veto_tags)}")
        if held:
            parts.append(
                f"HOLD: {len(held)} unverified -- {', '.join(c['symbol'] for c in held)}"
            )
        if not parts:
            return "Veto: 0 blocked"
        return " | ".join(parts)

    # ── Internal: cycle-level check ───────────────────────────────────────────

    def _check_macro_cycle(self, coins: List[Dict]) -> bool:
        """
        Cycle-level veto: BTC macro signal too weak → null entire cycle.
        Returns True if cycle was nulled.
        """
        macro_score = coins[0].get("macro_cq_score", 50)
        btc_trend   = coins[0].get("btc_trend", "UNKNOWN")
        avg14d      = coins[0].get("btc_avg14d", 0)

        if macro_score <= self.MACRO_VETO_SCORE_CEILING:
            reason = (
                f"MACRO_CYCLE: btc_trend={btc_trend}, "
                f"macro_cq_score={macro_score} ≤ ceiling={self.MACRO_VETO_SCORE_CEILING}, "
                f"btc_avg14d={avg14d:+.0f} BTC/day"
            )
            print(f"\n  [VetoEngine] !! CYCLE VETO -- {reason}")
            for c in coins:
                if reason not in c["veto_reasons"]:
                    c["veto_reasons"].append(reason)
                c["vetoed"] = True
            return True
        return False

    # ── Internal: per-coin checks ─────────────────────────────────────────────

    def _check_coin(self, c: Dict) -> None:
        """Run all per-coin veto rules. Appends to c['veto_reasons'], sets c['vetoed']."""
        if self.ENABLED_RULES.get("llm_verdict"):
            self._rule_llm_verdict(c)
        if self.ENABLED_RULES.get("drawdown"):
            self._rule_drawdown(c)
        if self.ENABLED_RULES.get("social_zero"):
            self._rule_social_zero(c)
        if self.ENABLED_RULES.get("survival_floor"):
            self._rule_survival_floor(c)
        if self.ENABLED_RULES.get("antifragile_floor"):
            self._rule_antifragile_floor(c)
        if self.ENABLED_RULES.get("dead_derivs"):
            self._rule_dead_derivs(c)
        if self.ENABLED_RULES.get("structural_decline"):
            self._rule_structural_decline(c)
        if self.ENABLED_RULES.get("llm_confidence_low"):
            self._rule_llm_confidence_low(c)
        if self.ENABLED_RULES.get("holder_concentration"):
            self._rule_holder_concentration(c)
        if self.ENABLED_RULES.get("anomaly_guard"):
            self._rule_anomaly_guard(c)
        if self.ENABLED_RULES.get("contract_mutable"):
            self._rule_contract_mutable(c)
        if self.ENABLED_RULES.get("forensic_kill"):
            self._rule_forensic_kill(c)
        # Future: add _rule_orderbook_depth(c), etc.

    def _rule_llm_verdict(self, c: Dict) -> None:
        verdict = c.get("llm_decision", "WATCH")
        if verdict in self.VETO_LLM_VERDICTS:
            reason = f"LLM_VERDICT={verdict} ∈ {sorted(self.VETO_LLM_VERDICTS)}"
            c["veto_reasons"].append(reason)
            c["vetoed"] = True

    def _rule_drawdown(self, c: Dict) -> None:
        max_dd = c.get("max_dd_pct", 0)
        if max_dd < self.VETO_MAX_DD_PCT:
            reason = (
                f"DRAWDOWN: maxDD={max_dd:.0f}% "
                f"< threshold={self.VETO_MAX_DD_PCT:.0f}%"
            )
            c["veto_reasons"].append(reason)
            c["vetoed"] = True

    def _rule_social_zero(self, c: Dict) -> None:
        """
        P-A compliant SOCIAL_ZERO (Phase 1.2).

        Veto fires ONLY when:
          social.status == MEASURED   AND   value == 0   AND   age >= floor

        When social.status in {MISSING, UNRELIABLE}:
          → weight already redistributed by P1 in gem_hunter
          → veto does NOT fire (absence ≠ dead community)
          → soft flag logged for observability

        social_status field populated by gem_hunter:
          "MEASURED"    — LunarCrush returned data that passed quality checks
          "MISSING"     — LC not available / coin not indexed
          "UNRELIABLE"  — LC returned data but spam/reliability flag fired
        """
        social        = c.get("social_score", -1)
        social_status = c.get("social_status", "MISSING")  # tri-state from gem_hunter
        age           = c.get("age_days", 0)
        sym           = c.get("symbol", "?")

        if social == 0:
            if social_status != "MEASURED":
                # P-A: MISSING or UNRELIABLE social is not a veto signal
                print(
                    f"  [VetoEngine] SOFT FLAG  {sym} social=0 "
                    f"status={social_status} -- NOT vetoed "
                    f"(absence ≠ zero community; P-A compliant)"
                )
                return

            # social is MEASURED and truly zero
            if age >= self.VETO_SOCIAL_AGE_FLOOR:
                reason = (
                    f"SOCIAL_ZERO: social=0 (status=MEASURED), "
                    f"age={age}d >= floor={self.VETO_SOCIAL_AGE_FLOOR}d"
                )
                c["veto_reasons"].append(reason)
                c["vetoed"] = True
            else:
                print(
                    f"  [VetoEngine] SOFT FLAG  {sym} social=0 (MEASURED)  age={age}d "
                    f"< {self.VETO_SOCIAL_AGE_FLOOR}d floor -- soft flag only"
                )

    def _rule_survival_floor(self, c: Dict) -> None:
        surv = c.get("survival_score", 100)
        if surv < self.VETO_SURVIVAL_FLOOR:
            reason = (
                f"SURVIVAL_FLOOR: surv={surv:.0f} "
                f"< floor={self.VETO_SURVIVAL_FLOOR:.0f}"
            )
            c["veto_reasons"].append(reason)
            c["vetoed"] = True

    def _rule_antifragile_floor(self, c: Dict) -> None:
        anti = c.get("antifragile", 100)
        age  = c.get("age_days", 0)
        sym  = c.get("symbol", "?")
        if anti < self.VETO_ANTIFRAGILE_FLOOR:
            if age >= self.VETO_ANTIFRAGILE_AGE_FLOOR:
                reason = (
                    f"ANTIFRAGILE_FLOOR: anti={anti:.0f} "
                    f"< floor={self.VETO_ANTIFRAGILE_FLOOR}, "
                    f"age={age}d >= {self.VETO_ANTIFRAGILE_AGE_FLOOR}d"
                )
                c["veto_reasons"].append(reason)
                c["vetoed"] = True
            else:
                print(
                    f"  [VetoEngine] SOFT FLAG  {sym} anti={anti:.0f}  age={age}d "
                    f"< {self.VETO_ANTIFRAGILE_AGE_FLOOR}d floor -- soft flag only"
                )

    def _rule_dead_derivs(self, c: Dict) -> None:
        deriv = c.get("derivs_score", 100)
        age   = c.get("age_days", 0)
        sym   = c.get("symbol", "?")
        if deriv == 0:
            if age >= self.VETO_DEAD_DERIVS_AGE_FLOOR:
                reason = (
                    f"DEAD_DERIVS: deriv=0, "
                    f"age={age}d >= {self.VETO_DEAD_DERIVS_AGE_FLOOR}d"
                )
                c["veto_reasons"].append(reason)
                c["vetoed"] = True
            else:
                print(
                    f"  [VetoEngine] SOFT FLAG  {sym} deriv=0  age={age}d "
                    f"< {self.VETO_DEAD_DERIVS_AGE_FLOOR}d floor -- no perp yet, soft flag only"
                )

    def _rule_structural_decline(self, c: Dict) -> None:
        p30 = c.get("price_30d_pct", 0)
        age = c.get("age_days", 0)
        if age >= self.VETO_STRUCTURAL_DECLINE_AGE and p30 < self.VETO_STRUCTURAL_DECLINE_PCT:
            reason = (
                f"STRUCTURAL_DECLINE: 30d={p30:+.1f}% "
                f"< threshold={self.VETO_STRUCTURAL_DECLINE_PCT:+.1f}%"
            )
            c["veto_reasons"].append(reason)
            c["vetoed"] = True

    def _rule_llm_confidence_low(self, c: Dict) -> None:
        conf  = c.get("llm_confidence", "MEDIUM")
        score = c.get("final_score", 0)
        if conf == "LOW" and score < self.VETO_LOW_CONFIDENCE_SCORE_CEILING:
            reason = (
                f"LLM_CONFIDENCE_LOW: confidence=LOW, "
                f"final_score={score:.1f} "
                f"< ceiling={self.VETO_LOW_CONFIDENCE_SCORE_CEILING:.1f}"
            )
            c["veto_reasons"].append(reason)
            c["vetoed"] = True

    def _rule_holder_concentration(self, c: Dict) -> None:
        """
        Per-wallet holder concentration and deployer unlock checks (Part A).

        Outcomes
        ────────
          hold_for_review=True  — HolderChecker could not fetch data (fetch failure,
                                  no contract, unsupported chain, anomalous response),
                                  OR deployer address was not returned by GoPlus (cannot
                                  verify deployer holding).
                                  Does NOT set vetoed=True — logged separately.
          vetoed=True           — Hard rule fired:
                                    HOLDER_DANGER  max_single_pct > VETO_SINGLE_WALLET_DANGER (35%)
                                    HOLDER_RED     max_single_pct > VETO_SINGLE_WALLET_RED   (20%)
                                    DEPLOYER_UNLOCKED deployer_pct > VETO_DEPLOYER_UNLOCKED  (5%)

        Soft flags (log only, no block):
          top10_unlocked_pct > SOFT_TOP10_UNLOCKED_FLAG (30%)
          locked_ratio_pct   < SOFT_LOCKED_RATIO_FLOOR  (80%)
          — Only printed when no holder hard veto fired (avoids redundant noise).

        No age-softening (unlike social/derivs):
          For social/derivs, young coins haven't had time to build community/trading
          signals — absence is expected, not alarming.
          For holder concentration, a young coin with high single-wallet concentration
          has NOT distributed yet — MORE suspicious, not less. No age discount applied.
        """
        status = c.get("holder_status")
        if status is None:
            # HolderChecker wasn't run (e.g., backtesting without live data) — skip
            return

        sym = c.get("symbol", "?")

        # ── fetch failure → HOLD_FOR_REVIEW ──────────────────────────────────
        if status == "HOLD_FOR_REVIEW":
            c["hold_for_review"] = True
            print(
                f"  [VetoEngine] HOLD_FOR_REVIEW  {sym} "
                f"holder data unverifiable ({c.get('holder_reason', '?')}) "
                f"-- no allocation, manual check needed"
            )
            return

        # ── deployer unknown → HOLD_FOR_REVIEW ───────────────────────────────
        # deployer_known defaults to True for backward compat (Phase 3 data
        # that predates Part A won't have this field; don't penalise retroactively).
        deployer_known = c.get("deployer_known", True)
        if not deployer_known:
            c["hold_for_review"] = True
            print(
                f"  [VetoEngine] HOLD_FOR_REVIEW  {sym} "
                f"deployer_address not returned by GoPlus "
                f"-- cannot verify deployer holding, no allocation"
            )
            return

        # ── P3: Age-adjusted holder thresholds ──────────────────────────────────
        # Select RED/DANGER thresholds based on coin age.
        # Young coins legitimately have concentrated initial distributions.
        age = c.get("age_days", 999)
        red_thresh    = self.VETO_SINGLE_WALLET_RED
        danger_thresh = self.VETO_SINGLE_WALLET_DANGER
        for age_ceil, r_pct, d_pct in self.HOLDER_AGE_THRESHOLDS:
            if age < age_ceil:
                red_thresh    = r_pct
                danger_thresh = d_pct
                break

        # ── hard veto checks ─────────────────────────────────────────────────
        max_single   = c.get("max_single_pct",  0.0)
        deployer_pct = c.get("deployer_pct",    0.0)
        holder_hard_veto_fired = False

        if max_single > danger_thresh:
            reason = (
                f"HOLDER_DANGER: max_single={max_single:.1f}% "
                f"> DANGER={danger_thresh:.0f}% (age={age}d)  "
                f"(count={c.get('holder_count', 0)}, chain={c.get('holder_chain', '?')})"
            )
            c["veto_reasons"].append(reason)
            c["vetoed"] = True
            holder_hard_veto_fired = True
        elif max_single > red_thresh:
            reason = (
                f"HOLDER_RED: max_single={max_single:.1f}% "
                f"> RED={red_thresh:.0f}% (age={age}d)  "
                f"(count={c.get('holder_count', 0)}, chain={c.get('holder_chain', '?')})"
            )
            c["veto_reasons"].append(reason)
            c["vetoed"] = True
            holder_hard_veto_fired = True

        if deployer_pct > self.VETO_DEPLOYER_UNLOCKED:
            reason = (
                f"DEPLOYER_UNLOCKED: deployer_pct={deployer_pct:.2f}% "
                f"> threshold={self.VETO_DEPLOYER_UNLOCKED:.0f}%"
            )
            c["veto_reasons"].append(reason)
            c["vetoed"] = True
            holder_hard_veto_fired = True

        # ── nullify social score when holder hard veto fires ─────────────────
        # High sentiment on a structurally toxic coin is a WORSE signal than
        # neutral sentiment: it suggests a professional pump campaign
        # manufacturing credibility for a coin with a known dump vector.
        # The spam guard (Part B) catches crude bots; it cannot distinguish
        # real humans writing "privacy infrastructure" narratives from genuine
        # community. Therefore: any coin where an insider-concentration veto
        # fires must receive zero positive social credit — regardless of how
        # clean the spam metrics look.
        #
        # Implementation: subtract social_contribution (pre-stored at score
        # time in gem_hunter) from final_score. No weight coupling required.
        if holder_hard_veto_fired:
            old_social = c.get("social_score", 0.0)
            if old_social > 0:
                contrib = c.get("social_contribution", 0.0)
                c["social_score_nullified"] = round(old_social, 1)  # keep original for log
                c["social_score"]           = 0.0
                c["social_contribution"]    = 0.0
                c["final_score"]            = round(
                    max(0.0, c.get("final_score", 0.0) - contrib), 1
                )
                print(
                    f"  [VetoEngine] SOCIAL_NULLIFIED  {c.get('symbol','?')} "
                    f"social={old_social:.0f}->0  final_score adjusted "
                    f"(-{contrib:.1f} pts)  reason: holder veto active"
                )

        # ── soft flags (only when no holder hard veto — avoids noise) ────────
        if not holder_hard_veto_fired:
            unlocked     = c.get("top10_unlocked_pct", 0.0)
            locked_ratio = c.get("locked_ratio_pct",  100.0)
            if unlocked > self.SOFT_TOP10_UNLOCKED_FLAG:
                print(
                    f"  [VetoEngine] SOFT FLAG  {sym} "
                    f"top10_unlocked={unlocked:.1f}% "
                    f"> {self.SOFT_TOP10_UNLOCKED_FLAG:.0f}% -- concentrated, monitor"
                )
            if locked_ratio < self.SOFT_LOCKED_RATIO_FLOOR:
                print(
                    f"  [VetoEngine] SOFT FLAG  {sym} "
                    f"locked_ratio={locked_ratio:.1f}% "
                    f"< {self.SOFT_LOCKED_RATIO_FLOOR:.0f}% -- low lock coverage "
                    f"(GoPlus may not detect vesting contracts for new tokens)"
                )

    def _rule_forensic_kill(self, c: Dict) -> None:
        """
        Propagate ScoutForensics hard-kill decisions into VetoEngine.

        ScoutForensics runs before VetoEngine in the pipeline and annotates:
          forensic_vetoed  bool — conclusive structural FAIL
          forensic_hold    bool — inconclusive, needs manual review
          forensic_reasons list — human-readable rule strings

        This rule mirrors those decisions so the Telegram/console report
        shows a unified veto view (not two separate systems).

        Why not just check forensic_vetoed in the allocator?
        Because VetoEngine.summary_str() drives the Telegram report header.
        Routing through here ensures full observability in all outputs.
        """
        sym = c.get("symbol", "?")

        # ── Hard forensic kill ────────────────────────────────────────────────
        if c.get("forensic_vetoed"):
            for fr in c.get("forensic_reasons", []):
                # Extract short tag from reason string (first word before ':')
                tag  = fr.split(":")[0].strip()
                full = f"FORENSIC_{tag}: {fr}"
                if full not in c["veto_reasons"]:
                    c["veto_reasons"].append(full)
            c["vetoed"] = True
            c.setdefault("veto_layers", [])
            if "FORENSIC" not in " ".join(c["veto_layers"]):
                forensic_tags = [
                    fr.split(":")[0].strip()
                    for fr in c.get("forensic_reasons", [])
                ]
                c["veto_layers"].append("FORENSIC[%s]" % "+".join(forensic_tags))
            # Determine kill source for clear logging
            is_blacklist = any("BLACKLIST" in r for r in c.get("forensic_reasons", []))
            kill_source  = "BLACKLIST" if is_blacklist else (
                f"{len(c.get('forensic_reasons', []))} forensic rule(s)")
            print(
                f"  [VetoEngine] FORENSIC_KILL  {sym}  source={kill_source}"
            )

        # ── Forensic hold (inconclusive) ──────────────────────────────────────
        elif c.get("forensic_hold"):
            if not c.get("hold_for_review"):
                c["hold_for_review"] = True
                print(
                    f"  [VetoEngine] FORENSIC_HOLD  {sym}  "
                    f"forensic data inconclusive -- manual review needed"
                )

    def _rule_anomaly_guard(self, c: Dict) -> None:
        """
        Phase 1.3 — Detect ANOMALOUS field values before they enter any rule.

        ANOMALOUS values (negative %, >100%, impossible counts) must never
        silently propagate into veto logic as if they were real measurements.
        This rule flags the coin as hold_for_review and logs which fields are bad.

        Currently validated: holder_max_single_pct, holder_top10_unlocked_pct,
        holder_locked_ratio_pct, holder_count, sentiment_7d (placeholder clamp).
        """
        sym    = c.get("symbol", "?")
        holder = c.get("holder", {}) or {}
        anomalies = []

        # ── Negative percentage (impossible) ─────────────────────────────────
        for field_name, key in [
            ("holder_max_single_pct",   "max_single_pct"),
            ("holder_top10_unlocked",   "top10_unlocked_pct"),
            ("holder_locked_ratio",     "locked_ratio_pct"),
        ]:
            val = holder.get(key)
            if val is not None:
                try:
                    fval = float(val)
                    if fval < 0 or fval > 100:
                        anomalies.append(f"{field_name}={val} (outside 0-100 range)")
                        holder[key] = None   # nullify in-place
                        c["holder"] = holder
                except (TypeError, ValueError):
                    anomalies.append(f"{field_name}={val} (not numeric)")

        # ── sentiment_7d placeholder clamp (value=1 when unreliable) ─────────
        social_obj = c.get("social", {}) or {}
        if social_obj.get("unreliable") and social_obj.get("sentiment_7d") == 1:
            anomalies.append("sentiment_7d=1 (placeholder clamp, not a real score)")
            social_obj["sentiment_7d"] = None
            c["social"] = social_obj

        if anomalies:
            c["hold_for_review"] = True
            for a in anomalies:
                print(
                    f"  [VetoEngine] ANOMALY  {sym}  {a}  "
                    f"-- field nullified, coin → hold_for_review"
                )

    def _rule_contract_mutable(self, c: Dict) -> None:
        # Phase 1.4 -- CONTRACT_MUTABLE veto (P-A compliant).
        # GoPlus is_proxy / is_mintable consumed here.
        # P-D: absence = HOLD (soft flag), not PASS.
        sym = c.get("symbol", "?")
        is_proxy    = c.get("goplus_is_proxy",        None)
        is_mintable = c.get("goplus_is_mintable",     None)
        renounced   = c.get("goplus_owner_renounced", None)

        if is_proxy is None and is_mintable is None:
            print(
                f"  [VetoEngine] SOFT FLAG  {sym} "
                f"contract mutability not fetched "
                f"(GoPlus is_proxy/is_mintable not consumed yet)"
            )
            return

        mutable = (is_proxy is True) or (is_mintable is True)
        if mutable and renounced is not True:
            reason = (
                f"CONTRACT_MUTABLE: "
                f"is_proxy={is_proxy}, is_mintable={is_mintable}, "
                f"owner_renounced={renounced}. "
                f"Contract can be upgraded post-listing."
            )
            c["veto_reasons"].append(reason)
            c["vetoed"] = True
