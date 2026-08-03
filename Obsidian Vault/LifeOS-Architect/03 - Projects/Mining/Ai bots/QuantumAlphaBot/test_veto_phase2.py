"""
Phase 2 veto rule test
======================
Two back-to-back runs on the same 8 cached coins:

  (a) REAL macro   — macro_cq_score=20 (DISTRIBUTING), identical to last live run.
                     Shows which new rules fire on top of cycle veto.

  (b) SYNTHETIC    — force macro_cq_score=85 / btc_trend=ACCUMULATING / btc_avg14d=-2000.
  [SYNTHETIC/TEST]  Cycle veto disabled. First time this bot produces a non-zero allocation.

Run from project root:
  python test_veto_phase2.py
"""
import sys
import json
import copy
import os

# Windows UTF-8 fix (emoji in summary_str)
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Make sure we can import the project modules
sys.path.insert(0, os.path.dirname(__file__))

from modules.veto_engine       import VetoEngine
from modules.quantum_optimizer import QuantumAllocator

TOTAL_BUDGET = 1000.0

# ── LLM results from the last real run (2026-05-25 16:26) ───────────────────
# These are injected because the test skips LLMEvaluator to avoid API calls.
LLM_MAP = {
    "OPG":    {"llm_decision": "ACCUMULATE", "llm_confidence": "HIGH",
               "llm_reasoning": "Top final score (50.9) with perfect derivatives positioning."},
    "FOGO":   {"llm_decision": "ACCUMULATE", "llm_confidence": "MEDIUM",
               "llm_reasoning": "Strong fundamentals (surv=60, deriv=100) with 130d maturity."},
    "ZAMA":   {"llm_decision": "ACCUMULATE", "llm_confidence": "MEDIUM",
               "llm_reasoning": "Positive momentum (+22.7% 7d) with balanced metrics."},
    "BASED":  {"llm_decision": "WATCH",      "llm_confidence": "LOW",
               "llm_reasoning": "-59% max drawdown and -42% monthly decline."},
    "MANTRA": {"llm_decision": "WATCH",      "llm_confidence": "LOW",
               "llm_reasoning": "Score below threshold, low antifragility after 82d."},
    "ESP":    {"llm_decision": "SKIP",       "llm_confidence": "HIGH",
               "llm_reasoning": "Final score (25.8) well below threshold."},
    "AI":     {"llm_decision": "SKIP",       "llm_confidence": "HIGH",
               "llm_reasoning": "Zero derivatives interest, sub-threshold score."},
    "EURI":   {"llm_decision": "SKIP",       "llm_confidence": "HIGH",
               "llm_reasoning": "Catastrophic final score (13.9), stablecoin-like."},
}


def load_coins() -> list:
    cache_path = os.path.join(os.path.dirname(__file__), "data", "coin_hunter_cache.json")
    with open(cache_path, encoding="utf-8") as f:
        records = json.load(f)["records"]
    coins = []
    for r in records:
        c = dict(r)
        sym = c["symbol"]
        c.update(LLM_MAP.get(sym, {"llm_decision": "WATCH", "llm_confidence": "MEDIUM"}))
        coins.append(c)
    return coins


def print_table(coins: list):
    print(f"\n  {'Sym':<7} {'Score':>6} {'Sur':>4} {'Anti':>4} {'Soc':>4} "
          f"{'Der':>4} {'MaxDD':>6} {'30d':>6} {'Decision':<12} {'Alloc':>6}")
    print(f"  {'-'*75}")
    for c in coins:
        alloc = f"{c.get('allocation_pct', 0):.0f}%" if c.get("allocation_pct", 0) > 0 else "—"
        dec   = c.get("llm_decision", "?")
        print(f"  {c['symbol']:<7} {c['final_score']:>6.1f} "
              f"{c['survival_score']:>4.0f} {c['antifragile']:>4.0f} "
              f"{c.get('social_score',0):>4.0f} {c.get('derivs_score',0):>4.0f} "
              f"{c['max_dd_pct']:>+5.0f}% {c.get('price_30d_pct',0):>+5.1f}% "
              f"{dec:<12} {alloc:>6}")


def run_scenario(label: str, coins: list, macro_override: dict = None):
    sep = "=" * 68
    print(f"\n{sep}")
    print(f"  {label}")
    print(f"{sep}")

    # Apply macro override
    if macro_override:
        for c in coins:
            c.update(macro_override)

    print("\n── Veto Layer " + "─" * 54)
    veto = VetoEngine()
    coins = veto.apply(coins)
    vs = veto.summary_str(coins)
    print(f"  Summary: {vs}")

    print("\n── Allocation " + "─" * 54)
    allocator = QuantumAllocator()
    coins = allocator.allocate(coins, total_budget=TOTAL_BUDGET)
    alloc_summary = allocator.summary_str(coins, TOTAL_BUDGET)
    print(f"  {alloc_summary}")

    buys = [(c["symbol"], c["buy_tier"], c.get("allocation_tier",""),
             c["allocation_pct"], c["allocation_usd"])
            for c in coins if c.get("allocation_pct", 0) > 0]
    if buys:
        print(f"\n  {'SYM':<7} {'TIER':<16} {'CAT':<5} {'%':>5}  {'$':>8}")
        print(f"  {'-'*50}")
        for sym, tier, cat, pct, usd in buys:
            cat_s = "SPEC" if cat == "SPECULATIVE" else cat
            print(f"  {sym:<7} {tier:<16} {cat_s:<5} {pct:>4.0f}%  ${usd:>7.0f}")
        print(f"  {'-'*50}")

    print_table(coins)
    return coins


# ── Main ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":

    # ── (a) REAL macro — identical to the last live run ─────────────────────
    coins_real = load_coins()
    run_scenario(
        "REAL MACRO  |  macro_cq_score=20  DISTRIBUTING  btc_avg14d=+1296",
        coins_real,
        macro_override=None,   # coins already carry macro=20 from cache
    )

    # ── (b) SYNTHETIC healthy macro — first non-zero allocation ever seen ────
    coins_synth = load_coins()
    run_scenario(
        "[SYNTHETIC/TEST]  macro_cq_score=85  ACCUMULATING  btc_avg14d=-2000",
        coins_synth,
        macro_override={
            "macro_cq_score": 85,
            "btc_trend":      "ACCUMULATING",
            "btc_avg14d":     -2000,
        },
    )
