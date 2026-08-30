"""
Part A test — per-wallet holder veto
======================================
Two scenarios:

  Scenario 1 — Real 8 coins (live GoPlus, fixed CHAIN_PRIORITY)
    OPG  should now hit Base chain → max_single=45.2% → HOLDER_DANGER veto
    ZAMA should hit ETH  chain → max_single=68.9% → HOLDER_DANGER veto

  Scenario 2 — Synthetic well-distributed frontier coin
    max_single=12%, deployer=3%, top10_unlocked=10.5%, locked_ratio=85%
    Must PASS all holder rules and get allocation under healthy macro.

Run from project root:  python test_veto_partA.py
"""
import sys, json, os
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(__file__))

from modules.holder_checker    import HolderChecker
from modules.veto_engine       import VetoEngine
from modules.quantum_optimizer import QuantumAllocator
from config import GOPLUS_API_KEY

TOTAL_BUDGET = 1000.0

LLM_MAP = {
    "OPG":    {"llm_decision": "ACCUMULATE", "llm_confidence": "HIGH"},
    "FOGO":   {"llm_decision": "ACCUMULATE", "llm_confidence": "MEDIUM"},
    "ZAMA":   {"llm_decision": "ACCUMULATE", "llm_confidence": "MEDIUM"},
    "BASED":  {"llm_decision": "WATCH",      "llm_confidence": "LOW"},
    "MANTRA": {"llm_decision": "WATCH",      "llm_confidence": "LOW"},
    "ESP":    {"llm_decision": "SKIP",       "llm_confidence": "HIGH"},
    "AI":     {"llm_decision": "SKIP",       "llm_confidence": "HIGH"},
    "EURI":   {"llm_decision": "SKIP",       "llm_confidence": "HIGH"},
}

MACRO_HEALTHY = {
    "macro_cq_score": 85,
    "btc_trend":      "ACCUMULATING",
    "btc_avg14d":     -2000,
}

# Synthetic well-distributed frontier coin.
# Spec (from user): top wallet ~12% unlocked, deployer ~3%,
#   top10 ~65% spread (total=70%, 85% locked → ~10.5% unlocked), healthy macro.
# Expected result: PASS all holder rules, get allocation.
SYNTHETIC_COIN = {
    "symbol":         "GOODCOIN",
    "name":           "Well-Distributed Protocol",
    "age_days":       60,
    "market_cap":     15_000_000,
    "final_score":    55.0,
    "survival_score": 60,
    "antifragile":    40,
    "social_score":   40,
    "derivs_score":   30,
    "max_dd_pct":     -25.0,
    "price_30d_pct":  15.0,
    # Holder data — set directly (bypasses HolderChecker, tests VetoEngine in isolation)
    "holder_status":      "PASS",
    "holder_reason":      "ok",
    "top10_holder_pct":   70.0,    # top-10 wallets hold 70% of supply
    "top10_unlocked_pct": 10.5,    # 85% of top-10 is locked → 15% unlocked = 70*0.15
    "max_single_pct":     12.0,    # largest single wallet = 12% (spread across 10)
    "deployer_pct":        3.0,    # deployer still holds 3% (below 5% threshold)
    "deployer_known":     True,    # creator_address was returned by GoPlus
    "locked_ratio_pct":   85.0,    # 85% of top-10 concentration is locked
    "holder_count":       2500,
    "holder_chain":       "ethereum",
    # LLM eval
    "llm_decision":   "ACCUMULATE",
    "llm_confidence": "HIGH",
    # Exchange presence
    "on_bybit":   True,
    "on_binance": False,
}
SYNTHETIC_COIN.update(MACRO_HEALTHY)


def load_coins():
    cache = json.loads(open("data/coin_hunter_cache.json", encoding="utf-8").read())
    coins = []
    for r in cache["records"]:
        c = dict(r)
        c.update(LLM_MAP.get(c["symbol"],
                             {"llm_decision": "WATCH", "llm_confidence": "MEDIUM"}))
        c.update(MACRO_HEALTHY)
        coins.append(c)
    return coins


def print_result_table(coins):
    print(f"\n  {'Sym':<10} {'Score':>6} {'MaxSng':>7} {'Depl':>7} {'Chain':<12} {'Alloc':>6}  Flags")
    print(f"  {'-'*80}")
    for c in coins:
        alloc  = f"{c.get('allocation_pct', 0):.0f}%" if c.get("allocation_pct", 0) > 0 else "--"
        ms     = c.get("max_single_pct", 0)
        dp     = c.get("deployer_pct", 0)
        chain  = c.get("holder_chain", "?") or "?"
        status = c.get("holder_status", "?")
        flags  = []
        if c.get("vetoed"):
            short = [r.split(":")[0] for r in c.get("veto_reasons", [])]
            flags.append(f"VETOED[{'+'.join(short)}]")
        if c.get("hold_for_review"):
            flags.append(f"HOLD({c.get('holder_reason','?')[:25]})")
        if not flags and status == "PASS":
            flags.append("OK")
        print(f"  {c['symbol']:<10} {c['final_score']:>6.1f} {ms:>6.1f}% {dp:>6.4f}%"
              f" {chain:<12} {alloc:>6}  {' '.join(flags)}")


if __name__ == "__main__":
    sep = "=" * 70

    # ────────────────────────────────────────────────────────────────────────
    # Scenario 1 — Real 8 coins (live GoPlus, fixed CHAIN_PRIORITY)
    # ────────────────────────────────────────────────────────────────────────
    print(f"\n{sep}")
    print(f"  PART A — Scenario 1: Real 8 coins [SYNTHETIC macro=85 ACCUMULATING]")
    print(f"{sep}")

    coins = load_coins()

    print("\n── Step 4.3: Holder Check (CHAIN_PRIORITY: ETH > Base > Arb > BSC) " + "─" * 1)
    checker = HolderChecker(goplus_api_key=GOPLUS_API_KEY)
    coins   = checker.fetch(coins)
    print(f"  {checker.summary_str(coins)}")

    print("\n── Step 4.5: Veto Engine " + "─" * 44)
    veto  = VetoEngine()
    coins = veto.apply(coins)
    print(f"  Summary: {veto.summary_str(coins)}")

    print("\n── Step 5: Allocation " + "─" * 46)
    alloc = QuantumAllocator()
    coins = alloc.allocate(coins, total_budget=TOTAL_BUDGET)
    print(f"  {alloc.summary_str(coins, TOTAL_BUDGET)}")

    print_result_table(coins)

    # ── Verify OPG and ZAMA both hit DANGER ─────────────────────────────────
    print(f"\n── Verification: OPG and ZAMA must show HOLDER_DANGER " + "─" * 14)
    all_ok = True
    for sym, expected_chain, expected_ms in [
        ("OPG",  "base",     45.0),   # multisig used for Binance dump (F2)
        ("ZAMA", "ethereum", 68.0),   # single EOA holds ~68.9%
    ]:
        c = next((x for x in coins if x["symbol"] == sym), None)
        if c is None:
            print(f"  {sym}: NOT FOUND IN RESULTS")
            all_ok = False
            continue
        ms      = c.get("max_single_pct", 0)
        chain   = c.get("holder_chain", "?")
        reasons = [r for r in c.get("veto_reasons", []) if "HOLDER_DANGER" in r]
        danger  = bool(reasons)
        chain_ok = (chain == expected_chain)
        ms_ok    = (ms >= expected_ms)
        result_str = "PASS" if (danger and chain_ok and ms_ok) else "FAIL"
        print(f"  {sym}: chain={chain} ({expected_chain}: {'OK' if chain_ok else 'WRONG'})  "
              f"max_single={ms:.1f}% ({'>=' + str(expected_ms) + '%': <9}: {'OK' if ms_ok else 'LOW'})  "
              f"HOLDER_DANGER: {'YES' if danger else 'NO'}  "
              f"-> {result_str}")
        if not (danger and ms_ok):
            all_ok = False
    print(f"\n  Scenario 1 check: {'ALL PASS' if all_ok else 'SEE ABOVE'}")

    # ────────────────────────────────────────────────────────────────────────
    # Scenario 2 — Synthetic well-distributed frontier coin
    # ────────────────────────────────────────────────────────────────────────
    print(f"\n{sep}")
    print(f"  PART A — Scenario 2: Synthetic well-distributed coin (must PASS + allocate)")
    print(f"{sep}")
    print(f"  Spec: max_single=12%  deployer=3%  top10_unlocked=10.5%  locked_ratio=85%")
    print(f"        threshold RED={VetoEngine.VETO_SINGLE_WALLET_RED:.0f}%  "
          f"DANGER={VetoEngine.VETO_SINGLE_WALLET_DANGER:.0f}%  "
          f"deployer_threshold={VetoEngine.VETO_DEPLOYER_UNLOCKED:.0f}%")

    synth = [dict(SYNTHETIC_COIN)]

    print("\n── Step 4.5: Veto Engine (no holder fetch — fields set directly) " + "─" * 4)
    veto2 = VetoEngine()
    synth = veto2.apply(synth)
    print(f"  Summary: {veto2.summary_str(synth)}")

    print("\n── Step 5: Allocation " + "─" * 46)
    alloc2 = QuantumAllocator()
    synth  = alloc2.allocate(synth, total_budget=TOTAL_BUDGET)
    print(f"  {alloc2.summary_str(synth, TOTAL_BUDGET)}")

    print_result_table(synth)

    c = synth[0]
    got_alloc = c.get("allocation_pct", 0) > 0
    no_veto   = not c.get("vetoed", False)
    no_hold   = not c.get("hold_for_review", False)
    passed    = got_alloc and no_veto and no_hold
    print(f"\n  GOODCOIN result: {'PASS' if passed else 'FAIL'}")
    print(f"    vetoed={c.get('vetoed')}  hold={c.get('hold_for_review')}")
    print(f"    veto_reasons={c.get('veto_reasons', [])}")
    print(f"    allocation_pct={c.get('allocation_pct', 0):.0f}%  "
          f"(${c.get('allocation_usd', 0):.0f} of ${TOTAL_BUDGET:.0f})")
    if not passed:
        print("  *** FAIL — synthetic coin should have passed all checks ***")
