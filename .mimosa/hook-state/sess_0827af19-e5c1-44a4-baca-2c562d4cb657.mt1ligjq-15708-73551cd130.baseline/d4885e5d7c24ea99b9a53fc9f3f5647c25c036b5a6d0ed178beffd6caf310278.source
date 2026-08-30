"""
SENTINEL — backtest.py
Replay the scoring logic over ≥1 year of historical CoinGecko data.
بازپخش منطق امتیازدهی روی داده‌های تاریخی CoinGecko (حداقل ۱ سال).

HONEST FRAMING / اعلام صادقانه:
  This is a logic validator, NOT a profit simulator.
  This tells you:  "would the scoring thresholds have triggered entries at
                    reasonable times, and how often?"
  This does NOT tell you: "how much profit would you have made."
  Without real social + on-chain history, we run in PRICE-ONLY mode.
  Signals that would need social/on-chain data are approximated.

Usage:
  python3 backtest.py                     # CORE, XEL, XMR, ZEC, TAO, DIL · 1 year
  python3 backtest.py --days 730          # 2 years
  python3 backtest.py --symbol CORE --days 365
  python3 backtest.py --no-fetch          # use cached data in backtest_cache/
"""

import os
import sys
import json
import time
import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import requests
import yaml

sys.path.insert(0, str(Path(__file__).parent))
from scorer import EntryScorer

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("backtest")

CACHE_DIR = Path(__file__).parent / "backtest_cache"
CACHE_DIR.mkdir(exist_ok=True)

COINGECKO_IDS = {
    "CORE": "coredaoorg",
    "XEL":  "xelis",
    "XMR":  "monero",
    "ZEC":  "zcash",
    "TAO":  "bittensor",
    "DIL":  "dilithion",
}

# ─────────────────────────────────────────────
# Data fetching (price history only — free CoinGecko)
# ─────────────────────────────────────────────

def fetch_price_history(symbol: str, days: int = 365) -> Optional[list]:
    """
    Returns list of (timestamp_ms, price_usd) pairs from CoinGecko.
    Falls back to cache if API fails.
    """
    coin_id = COINGECKO_IDS.get(symbol)
    if not coin_id:
        logger.error(f"Unknown symbol: {symbol}")
        return None

    cache_file = CACHE_DIR / f"{symbol}_{days}d.json"

    # Try cache first
    if cache_file.exists():
        age_hours = (time.time() - cache_file.stat().st_mtime) / 3600
        if age_hours < 24:
            logger.info(f"{symbol}: using cached price history ({age_hours:.1f}h old)")
            with open(cache_file) as f:
                return json.load(f)

    logger.info(f"{symbol}: fetching {days}-day history from CoinGecko...")
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {"vs_currency": "usd", "days": str(days), "interval": "daily"}

    for attempt in range(3):
        try:
            resp = requests.get(url, params=params, timeout=20)
            resp.raise_for_status()
            data = resp.json()
            prices = data.get("prices", [])
            if prices:
                with open(cache_file, "w") as f:
                    json.dump(prices, f)
                logger.info(f"{symbol}: {len(prices)} daily prices fetched")
                return prices
        except requests.exceptions.HTTPError as e:
            if resp.status_code == 429:
                wait = 60
                logger.warning(f"Rate limited. Waiting {wait}s...")
                time.sleep(wait)
            else:
                logger.error(f"HTTP {resp.status_code}: {e}")
                break
        except Exception as e:
            logger.warning(f"Attempt {attempt+1}: {e}")
            time.sleep(5)

    if cache_file.exists():
        logger.warning(f"{symbol}: API failed, using stale cache")
        with open(cache_file) as f:
            return json.load(f)

    return None


# ─────────────────────────────────────────────
# Scoring in price-only mode (no live social/on-chain)
# ─────────────────────────────────────────────

def build_price_snapshot(symbol: str, prices: list, idx: int,
                         lookback: int = 90) -> dict:
    """
    Build a market_data dict from the price series at position idx.
    We approximate:
      - drawdown from trailing 90-day high
      - MA50 / MA200 (rolling average)
      - Fear & Greed: approximated from recent volatility (NOT real F&G)
      - Social: fixed mid-neutral (50% sentiment) — clearly marked as approximation
      - On-chain: None (excluded from scoring)

    The approximation of F&G from price vol is NOT accurate.
    It is used only to keep the scorer running in price-only mode.
    Results below are labeled "PRICE-ONLY APPROXIMATION".
    """
    window = prices[max(0, idx - lookback): idx + 1]
    current_price = prices[idx][1]

    if not window:
        return {}

    price_vals = [p[1] for p in window if p[1] > 0]
    high_90d = max(price_vals) if price_vals else current_price
    low_90d  = min(price_vals) if price_vals else current_price
    drawdown = (high_90d - current_price) / high_90d if high_90d > 0 else 0

    # Moving averages
    all_prices = [p[1] for p in prices[:idx + 1] if p[1] > 0]
    ma50  = sum(all_prices[-50:])  / min(50,  len(all_prices)) if all_prices else None
    ma200 = sum(all_prices[-200:]) / min(200, len(all_prices)) if all_prices else None

    # Crude F&G approximation: if price is well below MA50, fear is high
    # This is an approximation only. Real backtest needs historical F&G data.
    approx_fg = 50
    if ma50 and current_price < ma50 * 0.85:
        approx_fg = 25   # deep fear
    elif ma50 and current_price < ma50 * 0.95:
        approx_fg = 38
    elif ma50 and current_price > ma50 * 1.10:
        approx_fg = 72   # greed
    elif ma50 and current_price > ma50 * 1.03:
        approx_fg = 60

    # Approximate sentiment from 30-day momentum (crude)
    window_30 = [p[1] for p in prices[max(0, idx-30): idx+1] if p[1] > 0]
    if len(window_30) >= 2:
        momentum = (current_price - window_30[0]) / window_30[0]
        sentiment = max(0.1, min(0.9, 0.5 + momentum * -1.5))  # contrarian
    else:
        sentiment = 0.5

    is_onchain = False  # CryptoQuant onchain فقط برای macro context (BTC/ETH) — در backtest نداریم

    available = ["price", "fear_greed", "social"]
    if is_onchain:
        available.append("onchain")

    return {
        "symbol": symbol,
        "price": {
            "price": current_price,
            "change_24h": (
                (current_price - prices[idx-1][1]) / prices[idx-1][1] * 100
                if idx > 0 else 0
            ),
            "high_90d": high_90d,
            "low_90d": low_90d,
            "drawdown_from_90d_high": drawdown,
            "ma50": ma50,
            "ma200": ma200,
        },
        "fear_greed": {"value": approx_fg, "classification": "approx"},
        "social": {
            "sentiment": sentiment,
            "galaxy_score": 50,
            "alt_rank": 1,
            "social_volume_24h": 0,
            "bullish_pct": 0,
            "social_score": 0,
        },
        # Crude on-chain approximation based on price momentum only
        "onchain": {
            "exchange_netflow": -1000 if drawdown > 0.3 else 500,
            "miner_netflow": -100 if drawdown > 0.25 else 200,
            "nvt": 60,
        } if is_onchain else None,
        "available_signals": available,
        "data_quality": "full" if len(available) >= 3 else "partial",
        "_backtest_approx": True,
    }


# ─────────────────────────────────────────────
# Backtest runner
# ─────────────────────────────────────────────

def run_backtest(symbol: str, config: dict, days: int = 365,
                 no_fetch: bool = False) -> dict:
    logger.info(f"\n{'='*55}")
    logger.info(f"Backtest: {symbol} · {days} days")
    logger.info(f"{'='*55}")

    if no_fetch:
        cache_file = CACHE_DIR / f"{symbol}_{days}d.json"
        if not cache_file.exists():
            logger.error(f"No cache found for {symbol}. Run without --no-fetch first.")
            return {}
        with open(cache_file) as f:
            prices = json.load(f)
    else:
        prices = fetch_price_history(symbol, days)
        if not prices:
            logger.error(f"Could not fetch price history for {symbol}")
            return {}

    # Disable scenario modifiers for clean price-only backtest
    cfg = {**config}
    for sc in cfg.get("scenarios", {}).values():
        sc["status"] = "inactive"
    scorer = EntryScorer(cfg)

    scores = []
    labels = []
    entry_dates = {
        "strong_entry":   [],
        "moderate_entry": [],
        "weak_entry":     [],
        "watch_only":     [],
    }

    # Start at day 90 to have enough lookback
    start_idx = min(90, len(prices) - 1)
    for i in range(start_idx, len(prices)):
        ts_ms = prices[i][0]
        date = datetime.utcfromtimestamp(ts_ms / 1000).strftime("%Y-%m-%d")
        snapshot = build_price_snapshot(symbol, prices, i)
        if not snapshot:
            continue

        result = scorer.score(symbol, snapshot)
        score = result.get("score")
        label = result.get("label", "watch_only")

        if score is not None:
            scores.append(score)
            labels.append(label)
            if label in entry_dates:
                entry_dates[label].append({
                    "date": date,
                    "score": round(score, 1),
                    "price": round(snapshot["price"]["price"], 2),
                    "drawdown_pct": round(snapshot["price"]["drawdown_from_90d_high"] * 100, 1),
                })

    if not scores:
        logger.warning(f"{symbol}: no scores computed")
        return {}

    n = len(scores)
    avg_score = sum(scores) / n
    min_score = min(scores)
    max_score = max(scores)

    label_counts = {k: len(v) for k, v in entry_dates.items()}
    label_pcts = {k: round(c / n * 100, 1) for k, c in label_counts.items()}

    return {
        "symbol": symbol,
        "days_analyzed": n,
        "date_range": (
            datetime.utcfromtimestamp(prices[start_idx][0] / 1000).strftime("%Y-%m-%d"),
            datetime.utcfromtimestamp(prices[-1][0] / 1000).strftime("%Y-%m-%d"),
        ),
        "score_stats": {
            "avg": round(avg_score, 1),
            "min": round(min_score, 1),
            "max": round(max_score, 1),
        },
        "label_distribution": label_counts,
        "label_distribution_pct": label_pcts,
        "sample_entries": {
            label: entries[:5]  # first 5 examples per zone
            for label, entries in entry_dates.items()
        },
        "tranche_timing": {
            "strong_entries": len(entry_dates["strong_entry"]),
            "consecutive_runs": _longest_run(labels, "strong_entry"),
        },
        "flags": _sanity_flags(label_pcts, avg_score, symbol),
    }


def _longest_run(labels: list, target: str) -> int:
    """Longest consecutive run of a label."""
    best = cur = 0
    for l in labels:
        cur = cur + 1 if l == target else 0
        best = max(best, cur)
    return best


def _sanity_flags(pcts: dict, avg_score: float, symbol: str) -> list:
    """
    Honest flagging of suspicious backtest results.
    هشدارهای صادقانه در مورد نتایج مشکوک.
    """
    flags = []
    strong_pct = pcts.get("strong_entry", 0)
    watch_pct  = pcts.get("watch_only", 0)

    if strong_pct > 60:
        flags.append(
            f"⚠️  THRESHOLD TOO LOOSE: strong_entry fires {strong_pct}% of days "
            f"— thresholds may need raising. / آستانه خیلی شل است."
        )
    if strong_pct < 2:
        flags.append(
            f"⚠️  THRESHOLD TOO TIGHT: strong_entry fires only {strong_pct}% of days "
            f"— may miss real opportunities. / آستانه خیلی سخت است."
        )
    if watch_pct > 90:
        flags.append(
            f"⚠️  ALMOST ALWAYS WATCHING: {watch_pct}% of days in watch_only. "
            f"Thresholds may be too high for {symbol}. / اغلب فقط رصد می‌کند."
        )
    if avg_score > 70:
        flags.append(
            f"⚠️  AVG SCORE {avg_score} > 70: scoring may be systematically too bullish. "
            f"/ میانگین امتیاز خیلی بالاست."
        )
    if avg_score < 20:
        flags.append(
            f"⚠️  AVG SCORE {avg_score} < 20: scoring may be systematically too bearish. "
            f"/ میانگین امتیاز خیلی پایین است."
        )
    if not flags:
        flags.append(
            "✅ No major sanity issues found — thresholds look reasonable for this period. "
            "/ مشکل مهمی در آستانه‌ها یافت نشد."
        )
    return flags


# ─────────────────────────────────────────────
# Report formatting
# ─────────────────────────────────────────────

def print_report(result: dict):
    if not result:
        return
    sym = result["symbol"]
    dr = result["date_range"]
    ss = result["score_stats"]
    ld = result["label_distribution_pct"]
    tt = result["tranche_timing"]

    print(f"\n{'═'*60}")
    print(f"  SENTINEL Backtest Report — {sym}")
    print(f"  SENTINEL گزارش بک‌تست — {sym}")
    print(f"{'═'*60}")
    print(f"  Period / دوره:    {dr[0]} → {dr[1]}")
    print(f"  Days scored:      {result['days_analyzed']}")
    print(f"  Score avg/min/max: {ss['avg']} / {ss['min']} / {ss['max']}")
    print(f"\n  Label distribution / توزیع برچسب‌ها:")
    for label, pct in ld.items():
        bar = "█" * int(pct / 2)
        n   = result["label_distribution"].get(label, 0)
        print(f"    {label:20s}  {bar:50s}  {pct:5.1f}% ({n}d)")
    print(f"\n  Strong entries:   {tt['strong_entries']} days")
    print(f"  Longest strong run: {tt['consecutive_runs']} consecutive days")

    print(f"\n  ── Flags / هشدارها ──")
    for flag in result["flags"]:
        print(f"  {flag}")

    print(f"\n  ── Sample strong-entry dates (first 5) ──")
    for e in result.get("sample_entries", {}).get("strong_entry", [])[:5]:
        print(f"    {e['date']}  score={e['score']}  ${e['price']:,.0f}  "
              f"−{e['drawdown_pct']}% from 90d high")

    print(f"\n  ⚠️  PRICE-ONLY APPROXIMATION MODE")
    print(f"  Social and on-chain signals are price-derived proxies, NOT real data.")
    print(f"  Real deployment will use LunarCrush + CryptoQuant APIs.")
    print(f"  این بک‌تست فقط قیمت را استفاده می‌کند. social/on-chain تقریب هستند.")
    print()


# ─────────────────────────────────────────────
# CLI entry point
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="SENTINEL backtest runner")
    parser.add_argument("--symbol", default=None,
                        help="Single symbol (CORE/XEL/XMR/ZEC/TAO/DIL). Default: all.")
    parser.add_argument("--days", type=int, default=365,
                        help="History length in days (default: 365)")
    parser.add_argument("--no-fetch", action="store_true",
                        help="Use cached data only")
    args = parser.parse_args()

    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    symbols = [args.symbol.upper()] if args.symbol else list(COINGECKO_IDS.keys())

    print("\n" + "═" * 60)
    print("  SENTINEL — Backtest")
    print("  منطق امتیازدهی را روی داده‌های تاریخی اعتبارسنجی می‌کند")
    print("  Validates scoring logic on historical price data")
    print("═" * 60)
    print(f"  Symbols: {', '.join(symbols)}  ·  Days: {args.days}")
    print(f"  ⚠️  Price-only mode: social/on-chain are approximations")
    print()

    all_results = {}
    for sym in symbols:
        result = run_backtest(sym, config, days=args.days, no_fetch=args.no_fetch)
        all_results[sym] = result
        print_report(result)
        time.sleep(1.5)  # Respect CoinGecko rate limit between symbols

    # Save results
    out_file = CACHE_DIR / f"backtest_results_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    with open(out_file, "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\nResults saved to: {out_file}")
    print(f"نتایج ذخیره شد در: {out_file}")


if __name__ == "__main__":
    main()
