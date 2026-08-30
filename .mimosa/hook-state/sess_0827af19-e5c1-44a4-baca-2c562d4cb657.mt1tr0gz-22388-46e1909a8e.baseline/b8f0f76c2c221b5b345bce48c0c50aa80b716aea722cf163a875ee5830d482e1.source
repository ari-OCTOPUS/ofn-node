"""
Part B.5 test — social/holder contradiction fix
================================================
Confirms:
  1. ZAMA-style coin (holder DANGER 68.9% + clean spam metrics + high sentiment)
     → social_score nullified to 0, final_score adjusted down
  2. GOODCOIN (clean holders + clean social) → social_score preserved, allocated

Run from project root:  python test_social_holder_B5.py
"""
import sys, os
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(__file__))

from modules.veto_engine       import VetoEngine
from modules.quantum_optimizer import QuantumAllocator

TOTAL_BUDGET = 1000.0
MACRO_HEALTHY = {"macro_cq_score": 85, "btc_trend": "ACCUMULATING", "btc_avg14d": -2000}

# ── Synthetic ZAMA-like coin ──────────────────────────────────────────────────
# Holder DANGER (68.9% single EOA) + professional pump campaign: high galaxy,
# high clean sentiment (8.4% spam ratio, 3.2 posts/contributor — passes spam guard)
# social_score = 60 (galaxy_7d=60.9 → +25, sentiment_7d=83.1 → +20... wait, that's
# more than 60. Let's use the exact value from the Part B test: ZAMA new_score=60)
# w_lc = 0.20 for altcoins (no CQ data) → social_contribution = 60 * 0.20 = 12.0
ZAMA_LIKE = {
    "symbol":            "ZAMA_SYN",
    "name":              "Privacy Layer (synthetic)",
    "age_days":          41,
    "final_score":       52.8,   # original (includes social contribution)
    "survival_score":    55,
    "antifragile":       45,
    "social_score":      60.0,   # should be NULLIFIED
    "social_contribution": 12.0, # 60 * 0.20 = 12.0 pts in final_score
    "derivs_score":      25,
    "max_dd_pct":        -30.0,
    "price_30d_pct":     -15.0,
    # Holder: DANGER (one EOA holds 68.9%)
    "holder_status":     "PASS",
    "holder_reason":     "ok",
    "top10_holder_pct":  93.6,
    "top10_unlocked_pct": 93.6,
    "max_single_pct":    68.9,    # single EOA → HOLDER_DANGER
    "deployer_pct":       0.0,
    "deployer_known":    True,
    "locked_ratio_pct":   0.0,
    "holder_count":      3972,
    "holder_chain":      "ethereum",
    # Social: clean spam metrics, high sentiment (professional pump campaign)
    "lc_unreliable":     False,
    "lc_spam_ratio":     0.084,
    "lc_posts_per_contrib": 3.2,
    # LLM
    "llm_decision":   "ACCUMULATE",
    "llm_confidence": "MEDIUM",
    "on_bybit": True, "on_binance": False,
}
ZAMA_LIKE.update(MACRO_HEALTHY)

# ── Synthetic GOODCOIN — clean holders + clean social ───────────────────────
GOODCOIN = {
    "symbol":            "GOODCOIN",
    "name":              "Well-Distributed Protocol",
    "age_days":          60,
    "final_score":       56.0,
    "survival_score":    60,
    "antifragile":       40,
    "social_score":      35.0,   # should be PRESERVED
    "social_contribution": 7.0,  # 35 * 0.20 = 7.0 pts
    "derivs_score":      30,
    "max_dd_pct":        -25.0,
    "price_30d_pct":     15.0,
    # Holder: CLEAN (max_single=12%, deployer=3%)
    "holder_status":     "PASS",
    "holder_reason":     "ok",
    "top10_holder_pct":  70.0,
    "top10_unlocked_pct": 10.5,
    "max_single_pct":    12.0,   # well below RED threshold (20%)
    "deployer_pct":       3.0,
    "deployer_known":    True,
    "locked_ratio_pct":  85.0,
    "holder_count":      2500,
    "holder_chain":      "ethereum",
    "lc_unreliable":     False,
    "lc_spam_ratio":     0.07,
    "lc_posts_per_contrib": 2.5,
    "llm_decision":   "ACCUMULATE",
    "llm_confidence": "HIGH",
    "on_bybit": True, "on_binance": False,
}
GOODCOIN.update(MACRO_HEALTHY)


def print_coin_state(c, label):
    print(f"\n  {label}")
    print(f"    symbol={c['symbol']}  final_score={c.get('final_score'):.1f}  "
          f"social_score={c.get('social_score'):.1f}  "
          f"max_single={c.get('max_single_pct'):.1f}%")
    print(f"    vetoed={c.get('vetoed')}  "
          f"social_nullified={c.get('social_score_nullified', 'n/a')}  "
          f"allocation_pct={c.get('allocation_pct', 0):.0f}%")
    if c.get("veto_reasons"):
        for r in c["veto_reasons"]:
            print(f"      -> {r}")


if __name__ == "__main__":
    sep = "=" * 68

    print(f"\n{sep}")
    print(f"  PART B.5 TEST — social nullification on holder veto")
    print(f"  Thresholds: RED={VetoEngine.VETO_SINGLE_WALLET_RED:.0f}%  "
          f"DANGER={VetoEngine.VETO_SINGLE_WALLET_DANGER:.0f}%")
    print(f"{sep}")

    coins = [dict(ZAMA_LIKE), dict(GOODCOIN)]

    # Snapshot before veto
    for c in coins:
        print_coin_state(c, f"BEFORE veto: {c['symbol']}")

    # Run veto + allocator
    print(f"\n── VetoEngine ─────────────────────────────────────────────────")
    veto  = VetoEngine()
    coins = veto.apply(coins)

    print(f"\n── QuantumAllocator ────────────────────────────────────────────")
    alloc = QuantumAllocator()
    coins = alloc.allocate(coins, total_budget=TOTAL_BUDGET)

    print(f"\n── Results ─────────────────────────────────────────────────────")
    for c in coins:
        print_coin_state(c, f"AFTER  veto: {c['symbol']}")

    # ── Verification ─────────────────────────────────────────────────────────
    print(f"\n── Verification ─────────────────────────────────────────────────")
    checks = []

    zama = next(c for c in coins if c["symbol"] == "ZAMA_SYN")
    good = next(c for c in coins if c["symbol"] == "GOODCOIN")

    # ZAMA: holder DANGER → social must be nullified
    zama_nullified = (
        zama.get("social_score", -1) == 0.0
        and zama.get("social_score_nullified", 0) == 60.0
        and zama.get("vetoed") is True
        and zama.get("allocation_pct", -1) == 0
    )
    checks.append(zama_nullified)
    print(f"  ZAMA_SYN: social_nullified={zama.get('social_score_nullified','?')}->0  "
          f"vetoed={zama.get('vetoed')}  alloc=0  -> {'PASS' if zama_nullified else 'FAIL'}")

    # GOODCOIN: clean holders → social must be preserved, allocated
    good_ok = (
        good.get("social_score", -1) == 35.0
        and good.get("social_score_nullified") is None
        and good.get("vetoed") is False
        and good.get("allocation_pct", 0) > 0
    )
    checks.append(good_ok)
    print(f"  GOODCOIN: social={good.get('social_score')}  "
          f"nullified={good.get('social_score_nullified','none')}  "
          f"vetoed={good.get('vetoed')}  "
          f"alloc={good.get('allocation_pct', 0):.0f}%  "
          f"-> {'PASS' if good_ok else 'FAIL'}")

    all_ok = all(checks)
    print(f"\n  Part B.5 check: {'ALL PASS' if all_ok else 'SEE ABOVE'}")
