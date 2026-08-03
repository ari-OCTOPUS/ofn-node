"""
QuantumAlpha Dashboard — Flask Server
اجرا: python dashboard/app.py
آدرس: http://localhost:5000
"""

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, jsonify, render_template

from config import SCAN_COINS
from modules.alpha_engine import AlphaEngine
from modules.backtester import Backtester

app = Flask(__name__)

CACHE_FILE  = os.path.join(os.path.dirname(__file__), "..", "data", "bt_cache.json")
CACHE_TTL   = 4 * 3600   # 4 ساعت

BACKTEST_COINS = list(dict.fromkeys(["BTC", "ETH", "SOL"] + SCAN_COINS))[:8]
LIVE_COINS     = ["BTC", "ETH", "SOL", "LINK", "AVAX", "INJ"]


# ── Cache helpers ─────────────────────────────────────────────────────────────

def _load_cache() -> dict | None:
    try:
        if not os.path.exists(CACHE_FILE):
            return None
        with open(CACHE_FILE, encoding="utf-8") as f:
            data = json.load(f)
        if time.time() - data.get("_ts", 0) < CACHE_TTL:
            return data
    except Exception:
        pass
    return None


def _save_cache(data: dict):
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    data["_ts"] = time.time()
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f)


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/backtest")
def api_backtest():
    cached = _load_cache()
    if cached:
        cached.pop("_ts", None)
        return jsonify(cached)
    try:
        bt     = Backtester(capital=1000)
        result = bt.run(BACKTEST_COINS, days=90)
        _save_cache(result)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/backtest/refresh")
def api_backtest_refresh():
    """حذف کش و اجرای دوباره"""
    try:
        if os.path.exists(CACHE_FILE):
            os.remove(CACHE_FILE)
        bt     = Backtester(capital=1000)
        result = bt.run(BACKTEST_COINS, days=90)
        _save_cache(result)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/live_scores")
def api_live():
    try:
        engine = AlphaEngine()
        snaps  = engine.analyze_batch(LIVE_COINS)
        return jsonify([
            {
                "symbol":     s.symbol,
                "score":      round(s.total_score, 1),
                "signal":     s.signal,
                "confidence": s.confidence,
                "price":      round(s.price_now, 4),
                "components": s.component_scores,
                "funding":    round(s.funding_rate_avg, 4),
                "netflow_7d": round(s.netflow_7d_usd / 1e6, 1),  # in $M
            }
            for s in snaps
        ])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print("\n" + "="*50)
    print("  QuantumAlpha Dashboard")
    print("  http://localhost:5000")
    print("="*50 + "\n")
    app.run(debug=False, host="0.0.0.0", port=5000)
