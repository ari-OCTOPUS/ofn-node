"""
Self-Improver — Track outcomes and learn
=========================================
هر چرخه:
  1. log_recommendations() — توصیه‌های جدید رو ثبت می‌کنه
  2. update_performance()  — قیمت‌های 7d و 30d رو چک می‌کنه
  3. performance_summary() — آمار دقت تاریخی رو برمی‌گردونه
  4. insight_str()         — یک‌خطی برای گزارش Telegram

WIN  = 30d return ≥ +20%
LOSS = 30d return ≤ -20%
NEUTRAL = بین دو حد بالا
"""
import json
import time
import requests
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional


class SelfImprover:
    """Tracks Coin Hunter recommendations and measures 30-day outcomes."""

    HISTORY_FILE  = Path("data/self_improver_history.json")
    BINANCE_BASE  = "https://api.binance.com/api/v3"
    BYBIT_BASE    = "https://api.bybit.com/v5"
    TRACK_7D_SEC  = 7  * 86_400
    TRACK_30D_SEC = 30 * 86_400

    WIN_THRESHOLD  =  20.0   # %
    LOSS_THRESHOLD = -20.0   # %

    def __init__(self):
        self._history: List[Dict] = self._load_history()

    # ── Persistence ──────────────────────────────────────────────────────────

    def _load_history(self) -> List[Dict]:
        if not self.HISTORY_FILE.exists():
            return []
        try:
            return json.loads(self.HISTORY_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []

    def _save_history(self) -> None:
        try:
            self.HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
            self.HISTORY_FILE.write_text(
                json.dumps(self._history, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception as e:
            print(f"  [SelfImprover] save error: {e}")

    # ── Price helpers ─────────────────────────────────────────────────────────

    def _price_now(self, symbol: str) -> Optional[float]:
        """قیمت لحظه‌ای USDT — اول Binance، fallback Bybit"""
        # ── Binance first ──────────────────────────────────────────────────────
        try:
            r = requests.get(
                f"{self.BINANCE_BASE}/ticker/price",
                params={"symbol": f"{symbol}USDT"},
                timeout=8,
            )
            if r.status_code == 200:
                return float(r.json()["price"])
        except Exception:
            pass

        # ── Bybit fallback (Bybit-only coins) ──────────────────────────────────
        try:
            r = requests.get(
                f"{self.BYBIT_BASE}/market/tickers",
                params={"category": "spot", "symbol": f"{symbol}USDT"},
                timeout=8,
            )
            if r.status_code == 200:
                lst = r.json().get("result", {}).get("list", [])
                if lst:
                    return float(lst[0]["lastPrice"])
        except Exception:
            pass

        return None

    # ── Public API ────────────────────────────────────────────────────────────

    def log_recommendations(self, coins: List[Dict]) -> int:
        """
        توصیه‌های جدید رو ثبت می‌کنه.
        فقط ACCUMULATE و WATCH رو دنبال می‌کنه (SKIP منطقی نیست).
        کوین‌هایی که قبلاً ثبت شدن رو دوباره ثبت نمی‌کنه.

        Returns:
            تعداد موارد جدید اضافه‌شده
        """
        known = {r["symbol"] for r in self._history}
        now   = time.time()
        added = 0

        for c in coins:
            sym = c["symbol"]
            dec = c.get("llm_decision", "SKIP")
            if dec == "SKIP" or sym in known:
                continue

            entry_price = self._price_now(sym)
            record: Dict = {
                "symbol":       sym,
                "name":         c.get("name", ""),
                "decision":     dec,
                "confidence":   c.get("llm_confidence", "MED"),
                "final_score":  round(c.get("final_score", 0), 1),
                "survival":     round(c.get("survival_score", 0), 1),
                "antifragile":  round(c.get("antifragile", 0), 1),
                "social":       round(c.get("social_score", 0), 1),
                "age_days":     c.get("age_days", 0),
                "market_cap":   c.get("market_cap", 0),
                "alloc_pct":    c.get("allocation_pct", 0.0),
                "logged_at":    now,
                "logged_date":  datetime.now().strftime("%Y-%m-%d %H:%M"),
                "price_entry":  entry_price,
                "price_7d":     None,
                "price_30d":    None,
                "pct_7d":       None,
                "pct_30d":      None,
                "outcome":      "PENDING",
            }
            self._history.append(record)
            added += 1

        if added:
            self._save_history()
            print(f"  [SelfImprover] Logged {added} new recommendation(s)")
        return added

    def update_performance(self) -> Dict:
        """
        چک می‌کنه کدوم توصیه‌ها به 7d یا 30d رسیدن، قیمت می‌گیره.

        Returns:
            performance_summary()
        """
        now     = time.time()
        updated = 0

        for rec in self._history:
            if rec.get("outcome") == "PENDING":
                age = now - rec.get("logged_at", now)
                sym = rec["symbol"]
                ep  = rec.get("price_entry")

                # ── 7-day snapshot ────────────────────────────────────────
                if rec["price_7d"] is None and age >= self.TRACK_7D_SEC:
                    p = self._price_now(sym)
                    if p and ep:
                        rec["price_7d"] = p
                        rec["pct_7d"]   = round((p - ep) / ep * 100, 1)
                        updated += 1

                # ── 30-day final outcome ──────────────────────────────────
                if rec["price_30d"] is None and age >= self.TRACK_30D_SEC:
                    p = self._price_now(sym)
                    if p and ep:
                        rec["price_30d"] = p
                        pct30            = (p - ep) / ep * 100
                        rec["pct_30d"]   = round(pct30, 1)
                        if pct30 >= self.WIN_THRESHOLD:
                            rec["outcome"] = "WIN"
                        elif pct30 <= self.LOSS_THRESHOLD:
                            rec["outcome"] = "LOSS"
                        else:
                            rec["outcome"] = "NEUTRAL"
                        updated += 1

        if updated:
            self._save_history()
            print(f"  [SelfImprover] Updated {updated} outcome(s)")

        return self.performance_summary()

    def performance_summary(self) -> Dict:
        """آمار کامل از تاریخچه توصیه‌ها"""
        completed = [r for r in self._history if r["outcome"] != "PENDING"]
        pending   = [r for r in self._history if r["outcome"] == "PENDING"]

        def stats(group):
            if not group:
                return {"n": 0, "win": 0, "loss": 0, "neutral": 0,
                        "win_rate": 0.0, "avg_30d": 0.0}
            wins     = sum(1 for r in group if r["outcome"] == "WIN")
            losses   = sum(1 for r in group if r["outcome"] == "LOSS")
            neutrals = sum(1 for r in group if r["outcome"] == "NEUTRAL")
            pcts     = [r["pct_30d"] for r in group
                        if r.get("pct_30d") is not None]
            return {
                "n":        len(group),
                "win":      wins,
                "loss":     losses,
                "neutral":  neutrals,
                "win_rate": round(wins / len(group) * 100, 1),
                "avg_30d":  round(float(np.mean(pcts)), 1) if pcts else 0.0,
            }

        acc = [r for r in completed if r["decision"] == "ACCUMULATE"]
        wat = [r for r in completed if r["decision"] == "WATCH"]

        recent_wins   = [r["symbol"] for r in self._history
                         if r.get("outcome") == "WIN"][-5:]
        recent_losses = [r["symbol"] for r in self._history
                         if r.get("outcome") == "LOSS"][-5:]

        return {
            "total_logged":     len(self._history),
            "pending":          len(pending),
            "completed":        len(completed),
            "accumulate_stats": stats(acc),
            "watch_stats":      stats(wat),
            "recent_wins":      recent_wins,
            "recent_losses":    recent_losses,
        }

    def insight_str(self) -> str:
        """یک‌خطی برای Telegram/Discord"""
        s   = self.performance_summary()
        acc = s["accumulate_stats"]

        if s["total_logged"] == 0:
            return "Learning: no history yet — first cycle"

        if acc["n"] == 0:
            return f"Learning: {s['pending']} pending, no completed yet"

        wins_str   = " ".join(recent_wins := s["recent_wins"][-3:]) or "—"
        losses_str = " ".join(s["recent_losses"][-3:]) or "—"
        return (
            f"Learning: {acc['n']} ACCUMULATE evaluated | "
            f"win-rate {acc['win_rate']:.0f}% | "
            f"avg30d {acc['avg_30d']:+.1f}% | "
            f"recent ✅ {wins_str}  ❌ {losses_str}"
        )
