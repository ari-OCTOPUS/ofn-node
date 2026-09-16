"""
Paper Trader — cycle ledger + calibration tally
================================================
PAPER_MODE is the ONLY mode this codebase supports. This module logs what
WOULD have been bought if capital were committed. It contains no order-placement
code and makes no authenticated exchange calls. The only exchange API calls here
are public market-data price tickers (no key, no auth, read-only).

Real orders require a SEPARATE, EXPLICITLY REVIEWED implementation.

Ledger format
─────────────
  data/paper_ledger.jsonl  — one JSON object per line, one line per cycle.
  Append-only. Never modified after writing.
  Each record captures the FULL decision state so BOTH holder and social
  thresholds can be recalibrated against accumulated real data.

Usage
─────
  # From main.py (called automatically when PAPER_MODE=True):
  from modules.paper_trader import PaperTrader
  paper = PaperTrader()
  paper.log_cycle(coins, total_budget=TOTAL_BUDGET)
  paper.print_cycle_report(coins, total_budget=TOTAL_BUDGET)

  # Cross-cycle tally (run any time after 10+ cycles):
  python paper_report.py
"""
import json
import time
import requests
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Optional


LEDGER_PATH = Path("data/paper_ledger.jsonl")

# ── Price-snapshot endpoints (PUBLIC, no auth) ────────────────────────────────
_BYBIT_TICKER   = "https://api.bybit.com/v5/market/tickers"
_BINANCE_TICKER = "https://api.binance.com/api/v3/ticker/price"


class PaperTrader:
    """
    Logs paper cycles. Never touches exchange APIs for orders.
    Public price tickers are read for entry-price snapshots only.
    """

    # ── Public API ─────────────────────────────────────────────────────────────

    def log_cycle(self, coins: List[Dict], total_budget: float = 1000.0) -> None:
        """
        Append one complete cycle record to data/paper_ledger.jsonl.
        Each line is a valid JSON object (JSONL / ndjson format).

        Fields logged per coin (see spec):
          date, symbol, alloc_%/$, entry_price_usd, all veto reasons +
          layer breakdown, macro state, HOLD_FOR_REVIEW list,
          raw holder metrics (max_single, deployer, locked_ratio) and
          raw social metrics (galaxy_7d, sentiment_7d, spam_ratio,
          posts_per_contrib, lc_unreliable).
        """
        LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)

        ts = datetime.now(timezone.utc).isoformat()

        # ── Price snapshot (public market data only) ──────────────────────────
        prices = self._price_snapshot(coins)

        # ── Macro state ───────────────────────────────────────────────────────
        first = coins[0] if coins else {}
        macro = {
            "btc_trend":      first.get("btc_trend",      "UNKNOWN"),
            "macro_cq_score": first.get("macro_cq_score", 0),
            "btc_avg14d":     first.get("btc_avg14d",     0),
        }
        cycle_nulled = any(
            any(r.startswith("MACRO_CYCLE") for r in c.get("veto_reasons", []))
            for c in coins
        )

        # ── Per-coin records ──────────────────────────────────────────────────
        coin_records = []
        for c in coins:
            sym          = c.get("symbol", "")
            veto_reasons = c.get("veto_reasons", [])
            # Distil rule names (strip value detail) for quick scanning
            veto_layers  = sorted({
                r.split(":")[0].strip()
                for r in veto_reasons
                if not r.startswith("MACRO_CYCLE")
            })

            coin_records.append({
                # ── identity + scoring ────────────────────────────────────
                "symbol":         sym,
                "name":           c.get("name", ""),
                "age_days":       c.get("age_days", 0),
                "final_score":    c.get("final_score", 0),
                "survival_score": c.get("survival_score", 0),
                "antifragile":    c.get("antifragile", 0),
                "derivs_score":   c.get("derivs_score", 0),
                # ── allocation intent ─────────────────────────────────────
                "alloc_pct":         c.get("allocation_pct", 0),
                "alloc_usd":         c.get("allocation_usd", 0),
                "entry_price_usd":   prices.get(sym, 0),
                "buy_tier":          c.get("buy_tier", "NONE"),
                "allocation_tier":   c.get("allocation_tier", "NONE"),
                # ── veto state ────────────────────────────────────────────
                "vetoed":            c.get("vetoed", False),
                "hold_for_review":   c.get("hold_for_review", False),
                "veto_reasons":      veto_reasons,
                "veto_layers":       veto_layers,
                # ── holder raw metrics ────────────────────────────────────
                "holder": {
                    "status":             c.get("holder_status", ""),
                    "max_single_pct":     c.get("max_single_pct", 0),
                    "deployer_pct":       c.get("deployer_pct", 0),
                    "locked_ratio_pct":   c.get("locked_ratio_pct", 0),
                    "top10_unlocked_pct": c.get("top10_unlocked_pct", 0),
                    "holder_count":       c.get("holder_count", 0),
                    "chain":              c.get("holder_chain", ""),
                    "holder_reason":      c.get("holder_reason", ""),
                },
                # ── social raw metrics ────────────────────────────────────
                "social": {
                    "score":              c.get("social_score", 0),
                    "score_nullified":    c.get("social_score_nullified"),    # non-None if B.5 fired
                    "galaxy_7d":          c.get("lc_galaxy", 0),
                    "sentiment_7d":       c.get("lc_sentiment", 0),
                    "spam_ratio":         c.get("lc_spam_ratio", 0),
                    "posts_per_contrib":  c.get("lc_posts_per_contrib", 0),
                    "unreliable":         c.get("lc_unreliable", False),
                },
                # ── LLM eval ─────────────────────────────────────────────
                "llm_decision":   c.get("llm_decision", ""),
                "llm_confidence": c.get("llm_confidence", ""),
            })

        hold_list  = [c["symbol"] for c in coins if c.get("hold_for_review")]
        alloc_list = [c["symbol"] for c in coins if c.get("allocation_pct", 0) > 0]

        record = {
            "cycle_ts":          ts,
            "paper_mode":        True,
            "total_budget_usd":  total_budget,
            "macro":             macro,
            "cycle_nulled":      cycle_nulled,
            "n_coins":           len(coins),
            "allocated_symbols": alloc_list,
            "hold_for_review":   hold_list,
            "coins":             coin_records,
        }

        with open(LEDGER_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

        print(f"  [PaperTrader] Cycle logged → {LEDGER_PATH}  "
              f"(allocated: {alloc_list or 'none'})")

    def print_cycle_report(self, coins: List[Dict],
                           total_budget: float = 1000.0) -> None:
        """Readable per-cycle summary printed to console after each run."""
        first      = coins[0] if coins else {}
        trend      = first.get("btc_trend", "?")
        macro_sc   = first.get("macro_cq_score", 0)
        cycle_ts   = datetime.now().strftime("%Y-%m-%d %H:%M")

        allocated = [c for c in coins if c.get("allocation_pct", 0) > 0]
        vetoed    = [c for c in coins if c.get("vetoed")]
        held      = [c for c in coins if c.get("hold_for_review")]

        bar = "─" * 66
        print(f"\n{bar}")
        print(f"  PAPER CYCLE  {cycle_ts}  "
              f"[macro: {trend} / score={macro_sc:.0f}]")
        print(bar)

        if allocated:
            print(f"\n  WOULD BUY ({len(allocated)} coins, ${total_budget:.0f} budget):")
            for c in allocated:
                print(f"    {c['symbol']:<8} "
                      f"{c.get('allocation_pct',0):>4.0f}%  "
                      f"${c.get('allocation_usd',0):>7.0f}  "
                      f"score={c.get('final_score',0):.1f}  "
                      f"{c.get('buy_tier','')}")
        else:
            print(f"\n  WOULD BUY: none")

        if vetoed:
            print(f"\n  VETOED ({len(vetoed)}):")
            for c in vetoed:
                per_coin = [r for r in c.get("veto_reasons", [])
                            if not r.startswith("MACRO_CYCLE")]
                # Show most important rules (holder first, then others)
                holder_rules = [r.split(":")[0] for r in per_coin if "HOLDER" in r]
                other_rules  = [r.split(":")[0] for r in per_coin if "HOLDER" not in r]
                short = (holder_rules[:1] + other_rules[:2]) or ["?"]
                nullified_note = (
                    f"  social was {c.get('social_score_nullified',0):.0f} -> nullified"
                    if c.get("social_score_nullified")
                    else ""
                )
                print(f"    {c['symbol']:<8} [{' | '.join(short)}]  "
                      f"max_single={c.get('max_single_pct',0):.1f}%  "
                      f"social={c.get('social_score',0):.0f}"
                      f"{nullified_note}")

        if held:
            print(f"\n  HOLD_FOR_REVIEW ({len(held)} — unverified, no allocation):")
            for c in held:
                print(f"    {c['symbol']:<8} ({c.get('holder_reason','?')[:45]})")

        print(f"\n  Ledger: {LEDGER_PATH}")
        print(bar)

    def print_cross_cycle_tally(self) -> None:
        """
        Read the full ledger and print calibration statistics.
        Run after 10-20 cycles to evaluate threshold tuning needs.
        """
        if not LEDGER_PATH.exists():
            print("  No ledger found — run at least one paper cycle first.")
            return

        cycles = []
        with open(LEDGER_PATH, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        cycles.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass

        if not cycles:
            print("  Ledger is empty.")
            return

        n       = len(cycles)
        nonzero = sum(1 for cy in cycles if cy.get("allocated_symbols"))
        nulled  = sum(1 for cy in cycles if cy.get("cycle_nulled"))

        # Macro regime counts
        regimes: Dict[str, int] = {}
        for cy in cycles:
            trend = cy.get("macro", {}).get("btc_trend", "UNKNOWN")
            if cy.get("cycle_nulled"):
                trend = "CYCLE_NULLED"
            regimes[trend] = regimes.get(trend, 0) + 1

        # Aggregate raw metrics across all coin records
        holder_max_single: List[float] = []
        holder_deployer:   List[float] = []
        social_spam:       List[float] = []
        social_galaxy:     List[float] = []
        social_sentiment:  List[float] = []
        hold_counts:       List[int]   = []
        veto_rule_counts:  Dict[str, int] = {}
        nullification_count = 0

        for cy in cycles:
            hold_in_cycle = 0
            for c in cy.get("coins", []):
                h = c.get("holder", {})
                if h.get("status") == "PASS":
                    holder_max_single.append(h.get("max_single_pct", 0))
                    holder_deployer.append(h.get("deployer_pct", 0))
                if c.get("hold_for_review"):
                    hold_in_cycle += 1
                s = c.get("social", {})
                if s.get("galaxy_7d", 0) > 0:
                    social_spam.append(s.get("spam_ratio", 0))
                    social_galaxy.append(s.get("galaxy_7d", 0))
                    social_sentiment.append(s.get("sentiment_7d", 0))
                if s.get("score_nullified") is not None:
                    nullification_count += 1
                for vr in c.get("veto_reasons", []):
                    rule = vr.split(":")[0].strip()
                    veto_rule_counts[rule] = veto_rule_counts.get(rule, 0) + 1
            hold_counts.append(hold_in_cycle)

        def bucket(values: List[float], bounds: List[float], suffix: str = "") -> str:
            parts = []
            for i, hi in enumerate(bounds):
                lo = bounds[i-1] if i > 0 else 0.0
                cnt = sum(1 for v in values if lo <= v < hi)
                parts.append(f"{lo:.0f}–{hi:.0f}{suffix}={cnt}")
            cnt = sum(1 for v in values if v >= bounds[-1])
            parts.append(f"≥{bounds[-1]:.0f}{suffix}={cnt}")
            return "  ".join(parts)

        def fmt_stats(lst: List[float], suffix: str = "") -> str:
            if not lst:
                return "no data"
            return (f"min={min(lst):.1f}{suffix}  avg={sum(lst)/len(lst):.1f}{suffix}  "
                    f"max={max(lst):.1f}{suffix}  n={len(lst)}")

        sep = "=" * 66
        print(f"\n{sep}")
        print(f"  PAPER CYCLE TALLY  ({n} cycles)")
        print(sep)
        print(f"\n  Date range:  {cycles[0]['cycle_ts'][:10]} → {cycles[-1]['cycle_ts'][:10]}")
        print(f"  Budget/cycle: ${cycles[-1].get('total_budget_usd', 0):.0f}")
        print(f"  Non-zero allocation cycles: {nonzero} / {n}  ({nonzero/n*100:.0f}%)")
        print(f"  Cycle-nulled (macro veto):  {nulled} / {n}  ({nulled/n*100:.0f}%)")

        print(f"\n  Macro regimes:")
        for trend, cnt in sorted(regimes.items(), key=lambda x: -x[1]):
            print(f"    {trend:<22} {cnt:>3} cycles  ({cnt/n*100:.0f}%)")

        print(f"\n  Holder metrics  (coins with PASS status, {len(holder_max_single)} observations):")
        if holder_max_single:
            print(f"    max_single_pct : {bucket(holder_max_single, [20, 35, 60], '%')}")
            print(f"    deployer_pct   : {fmt_stats(holder_deployer, '%')}")
            above_red    = sum(1 for v in holder_max_single if v > 20) / len(holder_max_single) * 100
            above_danger = sum(1 for v in holder_max_single if v > 35) / len(holder_max_single) * 100
            print(f"    >20% (RED fires):    {above_red:.0f}% of all observed coins")
            print(f"    >35% (DANGER fires): {above_danger:.0f}% of all observed coins")
            print(f"    (If >80% above DANGER, threshold may be too low for frontier coins)")

        print(f"\n  HOLD_FOR_REVIEW per cycle: {fmt_stats(hold_counts)}")
        print(f"    (Target after 20 cycles: avg ≤ 2.0 — chain/API coverage improving)")

        print(f"\n  Social metrics  ({len(social_galaxy)} observations with LC data):")
        if social_galaxy:
            print(f"    spam_ratio     : {bucket([v*100 for v in social_spam], [10, 20, 40], '%')}")
            print(f"    galaxy_7d      : {bucket(social_galaxy, [30, 50, 70])}")
            print(f"    sentiment_7d   : {fmt_stats(social_sentiment)}")
            pct_unrel = sum(1 for v in social_spam if v > 0.15) / max(len(social_spam), 1) * 100
            print(f"    UNRELIABLE fired (>15%): {pct_unrel:.0f}% of observations")
            print(f"    Social nullifications (B.5 holder gate): {nullification_count}")

        if veto_rule_counts:
            print(f"\n  Top veto rules (all cycles):")
            for rule, cnt in sorted(veto_rule_counts.items(),
                                    key=lambda x: -x[1])[:12]:
                print(f"    {rule:<48} {cnt:>4}x")

        print(f"\n{sep}")
        print(f"\n  What to watch over 20 cycles:")
        print(f"    GAP 1 (holder data coverage)   HOLD_FOR_REVIEW avg ≤ 2.0/cycle")
        print(f"              Currently {sum(hold_counts)/max(n,1):.1f} avg.  "
              f"Closes as GoPlus coverage expands and")
        print(f"              non-EVM coins either list EVM contracts or get excluded earlier.")
        print(f"    GAP 2 (allocation rate)         Non-zero cycles ≥ 50% under ACCUMULATING macro")
        print(f"              Currently {nonzero/n*100:.0f}%.  Closes as coin universe grows "
              f"and thresholds calibrate.")
        print(f"    GAP 3 (threshold calibration)   DANGER (>35%) firing on >80% of coins = too strict")
        print(f"              Currently {above_danger:.0f}% (if <80%: thresholds are appropriate)."
              if holder_max_single else f"              No holder data yet.")
        print(f"    GAP 4 (social signal quality)   UNRELIABLE firing on >70% = spam threshold too low")
        print(f"              Currently {pct_unrel:.0f}%."
              if social_galaxy else f"              No social data yet.")
        print(f"    READY signal: GAP 1 + GAP 2 both closed across 20 cycles under ACCUMULATING macro.")

    # ── Internal: price snapshot ────────────────────────────────────────────────

    def _price_snapshot(self, coins: List[Dict]) -> Dict[str, float]:
        """
        Fetch current USD price for each coin.
        Uses PUBLIC read-only market tickers — no authentication, no orders.
        Returns {symbol: price_usd}. Price=0.0 when unavailable.
        """
        prices: Dict[str, float] = {}

        for i, c in enumerate(coins):
            sym   = c.get("symbol", "")
            price: Optional[float] = None

            # Bybit spot ticker (preferred — native volume exchange)
            if c.get("on_bybit") and price is None:
                try:
                    r = requests.get(
                        _BYBIT_TICKER,
                        params={"category": "spot", "symbol": f"{sym}USDT"},
                        timeout=8,
                    )
                    if r.ok:
                        items = r.json().get("result", {}).get("list", [])
                        if items:
                            val = float(items[0].get("lastPrice") or 0)
                            if val > 0:
                                price = val
                except Exception:
                    pass

            # Binance spot ticker (fallback)
            if c.get("on_binance") and price is None:
                try:
                    r = requests.get(
                        _BINANCE_TICKER,
                        params={"symbol": f"{sym}USDT"},
                        timeout=8,
                    )
                    if r.ok:
                        val = float(r.json().get("price") or 0)
                        if val > 0:
                            price = val
                except Exception:
                    pass

            prices[sym] = price if price is not None else 0.0

            # Gentle rate limiting between price calls
            if i < len(coins) - 1:
                time.sleep(0.2)

        return prices
