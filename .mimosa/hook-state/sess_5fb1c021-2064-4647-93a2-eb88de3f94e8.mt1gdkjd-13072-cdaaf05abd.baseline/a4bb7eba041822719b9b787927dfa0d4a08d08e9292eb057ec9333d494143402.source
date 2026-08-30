"""
Coin Hunter Bot — Discovery + Evaluation + Allocation + Learning
===================================================================
کشف کوین‌های نوظهور (≤180d) با پتانسیل بقای بلندمدت.

اجرا:
  python main.py            ← هر 6 ساعت یک‌بار
  python main.py --once     ← یک بار و خروج

پایپ‌لاین:
  1. Hard filters (mcap range, liquidity, listing, blacklist)
  2. Age filter (≤ MAX_AGE_DAYS)
  3. Scoring: survival + antifragility + social (LC) + derivatives (CAL) + on-chain (CQ)
  4. Claude evaluation  → ACCUMULATE / WATCH / SKIP + reasoning
  5. Quantum allocation → Barbell (80% CORE / 20% SPECULATIVE) + Kelly weights
  6. Self-learning      → log outcomes, track 7d/30d performance
  7. Telegram + Discord report
"""
import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

# Windows UTF-8 fix
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import schedule
from colorama import Fore, Style, init

from modules.gem_hunter        import GemHunter
from modules.scout_forensics   import ScoutForensics
from modules.llm_evaluator     import LLMEvaluator
from modules.holder_checker    import HolderChecker
from modules.veto_engine       import VetoEngine
from modules.quantum_optimizer import QuantumAllocator
from modules.self_improver     import SelfImprover
from modules.notifier          import send_coin_hunter_report, send_error
from modules.paper_trader      import PaperTrader
from config                    import PAPER_MODE

# P6: Macro monotony detection constants
_LEDGER_PATH          = Path("data/paper_ledger.jsonl")
_MACRO_MONOTONY_LIMIT = 8    # alert if macro_cq_score unchanged this many consecutive cycles


def _check_macro_monotony(current_score: float) -> None:
    """
    P6 FIX: Detect if macro_cq_score has been stuck at the same value for
    _MACRO_MONOTONY_LIMIT or more consecutive cycles and send a Telegram alert.

    Rationale: macro_cq_score=20 for 6+ straight cycles means either:
      (a) CryptoQuant API is returning stale data / the bot's key expired, OR
      (b) BTC has genuinely been in sustained distribution for weeks (unusual).
    Both cases warrant human attention. Without this check the bot silently
    nulls every cycle with no signal that something may be broken.
    """
    if not _LEDGER_PATH.exists():
        return
    try:
        lines = _LEDGER_PATH.read_text(encoding="utf-8").strip().splitlines()
        if len(lines) < _MACRO_MONOTONY_LIMIT:
            return  # not enough history yet

        # Collect macro_cq_score from the last N cycles (oldest first)
        recent_scores = []
        for line in lines[-_MACRO_MONOTONY_LIMIT:]:
            cycle = json.loads(line)
            # macro score is stored per-coin but identical across all coins
            coins_in_cycle = cycle.get("coins", [])
            if coins_in_cycle:
                score = coins_in_cycle[0].get("macro_cq_score", None)
            else:
                score = cycle.get("macro", {}).get("macro_cq_score", None)
            if score is None:
                return  # unexpected format, abort silently
            recent_scores.append(float(score))

        # Check if ALL recent scores are identical AND equal to current
        if len(set(recent_scores)) == 1 and recent_scores[0] == current_score:
            msg = (
                f"⚠️ MACRO SENSOR ALERT\n"
                f"macro_cq_score stuck at {current_score:.0f} "
                f"for {_MACRO_MONOTONY_LIMIT}+ consecutive cycles.\n"
                f"Possible causes:\n"
                f"• CryptoQuant API returning stale data\n"
                f"• API key quota exhausted\n"
                f"• Genuine extreme sustained BTC distribution (verify manually)\n"
                f"Action: Check CryptoQuant dashboard → BTC exchange netflow"
            )
            print(f"\n  [MacroMonotony] !! {_MACRO_MONOTONY_LIMIT} identical macro scores detected")
            try:
                send_error(msg)
            except Exception as e:
                print(f"  [MacroMonotony] Could not send alert: {e}")
    except Exception as e:
        print(f"  [MacroMonotony] check error: {e}")

init(autoreset=True)
C  = Fore.CYAN; Y = Fore.YELLOW; G = Fore.GREEN; R = Fore.RED; RS = Style.RESET_ALL

TOTAL_BUDGET = 1000.0   # $ — فقط برای نمایش درصدها


def hdr(t):  print(f"\n{C}{'='*64}\n  {t}\n{'='*64}{RS}")
def ok(t):   print(f"  {G}✓{RS} {t}")
def warn(t): print(f"  {R}!{RS} {t}")
def sec(t):  print(f"\n{Y}── {t} {'─'*(55-len(t))}{RS}")


def _print_table(coins: list, filter_str: str):
    """جدول کامل روی کنسول"""
    print(f"\n  {filter_str}\n")
    if not coins:
        return
    print(f"  {'Sym':<7} {'Name':<18} {'Age':>5} {'MCap':>9} "
          f"{'Sur':>4} {'Ant':>4} {'Soc':>4} {'Der':>4} "
          f"{'Final':>5} {'MaxDD':>6} {'Exch':<3} {'Decision':<12} {'Alloc':>6}")
    print(f"  {'-'*105}")
    for g in coins:
        exch  = "BY" if g.get("on_bybit")  else ("BN" if g.get("on_binance") else "--")
        dec   = g.get("llm_decision", "?")
        alloc = f"{g.get('allocation_pct',0):.0f}%" if g.get("allocation_pct", 0) > 0 else "—"
        dec_color = G if dec == "ACCUMULATE" else (Y if dec == "WATCH" else R)
        print(f"  {g['symbol']:<7} {g['name'][:18]:<18} {g['age_days']:>4}d "
              f"${g['market_cap']/1e6:>6.2f}M "
              f"{g['survival_score']:>4.0f} "
              f"{g['antifragile']:>4.0f} "
              f"{g.get('social_score', 0):>4.0f} "
              f"{g.get('derivs_score', 0):>4.0f} "
              f"{g['final_score']:>5.1f} "
              f"{g['max_dd_pct']:>+5.0f}% "
              f"{exch}  "
              f"{dec_color}{dec:<12}{RS} {alloc:>6}")


def run_hunt():
    hdr(f"Coin Hunter Bot  |  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # ── Step 1-3: Discovery + Scoring ────────────────────────────────────────
    sec("Step 1–3: Discovery & Scoring")
    hunter = GemHunter()
    df     = hunter.find_gems()

    filter_str = hunter.filter_settings_str()
    rej_str    = hunter.rejection_summary()
    scanned    = hunter.last_scanned_count()

    if df.empty:
        warn(f"0 coins passed filters (scanned {scanned})")
        print(f"  {Y}Rejected:{RS} {rej_str}")
        print(f"  {filter_str}")
        payload = {
            "gems":              [],
            "rejections":        hunter.last_rejections(),
            "scanned":           scanned,
            "filter_settings":   filter_str,
            "rejection_summary": rej_str,
            "insight":           "",
        }
        try:
            send_coin_hunter_report(payload)
            ok("Telegram report sent (empty)")
        except Exception as e:
            warn(f"Telegram error: {e}")
        return

    ok(f"Found {len(df)} qualified coins (scanned {scanned})")
    coins = df.to_dict(orient="records")

    # BTC macro print (from first coin — same for all)
    if coins:
        btc_t = coins[0].get("btc_trend", "")
        btc_a = coins[0].get("btc_avg14d", 0)
        macro_s = coins[0].get("macro_cq_score", 50)
        if btc_t and btc_t != "UNKNOWN":
            emoji = {"ACCUMULATING": G, "NEUTRAL": Y, "DISTRIBUTING": R}.get(btc_t, "")
            ok(f"CryptoQuant BTC → {emoji}{btc_t}{RS} | avg14d: {btc_a:+.0f} BTC | score: {macro_s:.0f}")
        # P6: Alert if macro score has been unchanged for too many consecutive cycles
        _check_macro_monotony(macro_s)

    # ── Step 3.5: Scout Forensics — pre-LLM structural kill layer ────────────
    sec("Step 3.5: Scout Forensics")
    forensic_summary = ""
    try:
        scout   = ScoutForensics()
        coins   = scout.apply(coins)
        forensic_summary = scout.summary_str(coins)
        ok(forensic_summary)
        # Remove forensic-vetoed coins from LLM evaluation (saves API calls)
        # They are still passed to VetoEngine for full observability in logs
        coins_for_llm = [c for c in coins if not c.get("forensic_vetoed")]
        forensic_killed = len(coins) - len(coins_for_llm)
        if forensic_killed:
            ok(f"Forensics: {forensic_killed} coin(s) removed before LLM eval")
    except Exception as e:
        warn(f"Scout forensics error: {e}")
        coins_for_llm = coins

    # ── Step 4: Claude evaluation ─────────────────────────────────────────────
    sec("Step 4: Claude Evaluation")
    try:
        evaluator = LLMEvaluator()
        coins_for_llm = evaluator.evaluate_coins(coins_for_llm)
        # Merge LLM results back — forensic-vetoed coins keep default WATCH/LOW
        llm_map = {c["symbol"]: c for c in coins_for_llm}
        for c in coins:
            if c["symbol"] in llm_map:
                c.update({k: v for k, v in llm_map[c["symbol"]].items()
                          if k.startswith("llm_")})
        acc_count = sum(1 for c in coins if c.get("llm_decision") == "ACCUMULATE")
        wat_count = sum(1 for c in coins if c.get("llm_decision") == "WATCH")
        ok(f"Claude: {acc_count} ACCUMULATE, {wat_count} WATCH, "
           f"{len(coins)-acc_count-wat_count} SKIP")
    except Exception as e:
        warn(f"Claude evaluation error: {e}")

    # ── Step 4.3: Holder concentration check (Fix B) ─────────────────────────
    sec("Step 4.3: Holder Concentration")
    try:
        from config import GOPLUS_API_KEY
        checker = HolderChecker(goplus_api_key=GOPLUS_API_KEY)
        coins   = checker.fetch(coins)
        ok(checker.summary_str(coins))
    except Exception as e:
        warn(f"Holder check error: {e}")

    # ── Step 4.5: Veto layer (post-scoring, pre-allocation) ──────────────────
    sec("Step 4.5: Veto Layer")
    veto_summary = ""
    try:
        veto = VetoEngine()
        coins = veto.apply(coins)
        veto_summary = veto.summary_str(coins)
        ok(veto_summary)
    except Exception as e:
        warn(f"Veto engine error: {e}")

    # ── Step 5: Quantum allocation ────────────────────────────────────────────
    sec("Step 5: Quantum Allocation")
    try:
        allocator = QuantumAllocator()
        coins     = allocator.allocate(coins, total_budget=TOTAL_BUDGET)
        ok(allocator.summary_str(coins, TOTAL_BUDGET))
        # جدول خلاصه خرید
        buys = [(c["symbol"], c["buy_tier"], c.get("allocation_tier", ""), c["allocation_pct"], c["allocation_usd"])
                for c in coins if c.get("allocation_pct", 0) > 0]
        if buys:
            print(f"\n  {C}{'─'*62}")
            print(f"  {'SYM':<7} {'TIER':<16} {'CAT':<5} {'%':>5}  {'$':>8}")
            print(f"  {'─'*62}{RS}")
            for sym, tier, cat, pct, usd in buys:
                color = G if "STRONG" in tier else (G if "✅" in tier else Y)
                # Abbreviate SPECULATIVE → SPEC for column alignment
                cat_short = "SPEC" if cat == "SPECULATIVE" else cat
                cat_c = C if cat == "CORE" else (Y if cat == "SPECULATIVE" else RS)
                print(f"  {color}{sym:<7}{RS} {tier:<16} {cat_c}{cat_short:<5}{RS} {pct:>4.0f}%  ${usd:>7.0f}")
            print(f"  {C}{'─'*62}{RS}")
    except Exception as e:
        warn(f"Allocation error: {e}")

    # ── Step 5.5: Paper-trade ledger ─────────────────────────────────────────
    if PAPER_MODE:
        sec("Step 5.5: Paper Trade Log")
        try:
            paper = PaperTrader()
            paper.log_cycle(coins, total_budget=TOTAL_BUDGET)
            paper.print_cycle_report(coins, total_budget=TOTAL_BUDGET)
            ok("Paper cycle logged → data/paper_ledger.jsonl")
        except Exception as e:
            warn(f"Paper trader error: {e}")

    # ── Step 6: Self-learning ─────────────────────────────────────────────────
    sec("Step 6: Self-Learning")
    insight = ""
    try:
        improver = SelfImprover()
        improver.update_performance()
        # Only log non-vetoed coins — vetoed coins aren't valid recommendations
        active_coins = [c for c in coins if not c.get("vetoed", False)]
        improver.log_recommendations(active_coins)
        insight = improver.insight_str()
        ok(insight)
    except Exception as e:
        warn(f"Self-improver error: {e}")

    # ── Console table ─────────────────────────────────────────────────────────
    _print_table(coins, filter_str)
    print(f"\n  {Y}Rejected:{RS} {rej_str}")

    # Per-coin Claude reasoning
    print(f"\n  {C}── Claude Reasoning {'─'*44}{RS}")
    for c in coins:
        dec   = c.get("llm_decision", "?")
        conf  = c.get("llm_confidence", "")
        color = G if dec == "ACCUMULATE" else (Y if dec == "WATCH" else R)
        print(f"  {color}{c['symbol']:>6} [{dec}/{conf}]{RS}")
        if c.get("llm_reasoning"):
            print(f"         {c['llm_reasoning']}")
        if c.get("llm_risk_note"):
            print(f"         ⚠ {c['llm_risk_note']}")

    # ── Notify ────────────────────────────────────────────────────────────────
    payload = {
        "gems":              coins,
        "rejections":        hunter.last_rejections(),
        "scanned":           scanned,
        "filter_settings":   filter_str,
        "rejection_summary": rej_str,
        "veto_summary":      veto_summary,
        "insight":           insight,
    }
    try:
        send_coin_hunter_report(payload)
        ok("Telegram + Discord report sent")
    except Exception as e:
        warn(f"Notify error: {e}")


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Coin Hunter Bot")
    parser.add_argument("--once", action="store_true", help="یک بار اجرا و خروج")
    args = parser.parse_args()

    try:
        run_hunt()
    except Exception as e:
        send_error(f"Coin Hunter crashed: {e}")
        raise

    if args.once:
        sys.exit(0)

    schedule.every(6).hours.do(run_hunt)
    print(f"\n{C}Scheduled every 6 hours. Ctrl+C to stop.{RS}")
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    main()
