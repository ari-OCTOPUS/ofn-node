"""
SENTINEL — phase_manager.py
مدیریت فاز ۰ (کالیبراسیون) · فاز ۱ (استقرار) · فاز ۲ (تعادل‌بخشی)
"""

import sqlite3
import logging
import json
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


class PhaseManager:
    def __init__(self, config: dict, db_path: str = "state.db"):
        self.config = config
        self.db_path = db_path
        self.ph_cfg = config["phases"]
        self._init_db()

    # ─────────────────────────────────────────────
    # راه‌اندازی پایگاه داده
    # ─────────────────────────────────────────────

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS phase_state (
                    key   TEXT PRIMARY KEY,
                    value TEXT
                );

                CREATE TABLE IF NOT EXISTS score_history (
                    id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol    TEXT,
                    score     REAL,
                    label     TEXT,
                    data_json TEXT,
                    ts        TEXT DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS volatility_samples (
                    id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol    TEXT,
                    price     REAL,
                    ts        TEXT DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS price_alerts_sent (
                    id       INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol   TEXT,
                    price    REAL,
                    change   REAL,
                    ts       TEXT DEFAULT (datetime('now'))
                );
            """)
        logger.info("Database initialized")

    # ─────────────────────────────────────────────
    # خواندن / نوشتن وضعیت فاز
    # ─────────────────────────────────────────────

    def _get_state(self, key: str, default=None):
        with self._conn() as conn:
            row = conn.execute("SELECT value FROM phase_state WHERE key=?", (key,)).fetchone()
            if row:
                try:
                    return json.loads(row["value"])
                except:
                    return row["value"]
            return default

    def _set_state(self, key: str, value):
        with self._conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO phase_state(key, value) VALUES (?,?)",
                (key, json.dumps(value))
            )

    # ─────────────────────────────────────────────
    # شروع ربات (اولین اجرا)
    # ─────────────────────────────────────────────

    def initialize(self):
        """اگر هنوز شروع نشده، فاز ۰ را آغاز می‌کند"""
        if self._get_state("phase") is None:
            self._set_state("phase", 0)
            self._set_state("phase0_start", datetime.utcnow().isoformat())
            self._set_state("phase1_start", None)
            self._set_state("phase2_start", None)
            logger.info("SENTINEL initialized → Phase 0 (Calibration)")
        else:
            logger.info(f"SENTINEL resumed → Phase {self._get_state('phase')}")

    # ─────────────────────────────────────────────
    # فاز ۰ — کالیبراسیون
    # ─────────────────────────────────────────────

    def record_volatility(self, symbol: str, price: float):
        """ذخیره نمونه‌ی قیمت روزانه برای کالیبراسیون نوسان"""
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO volatility_samples(symbol, price) VALUES (?,?)",
                (symbol, price)
            )

    def get_volatility_stats(self, symbol: str) -> dict:
        """
        محاسبه نوسان و دامنه برای هر کوین
        """
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT price FROM volatility_samples WHERE symbol=? ORDER BY ts",
                (symbol,)
            ).fetchall()

        prices = [r["price"] for r in rows]
        if len(prices) < 2:
            return {"samples": len(prices), "volatility_pct": None, "range_pct": None}

        # نوسان روزانه (انحراف معیار تغییرات درصدی)
        changes = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
        mean_change = sum(changes) / len(changes)
        variance = sum((c - mean_change)**2 for c in changes) / len(changes)
        volatility = variance ** 0.5

        # دامنه
        rng = (max(prices) - min(prices)) / min(prices) if min(prices) > 0 else 0

        return {
            "samples": len(prices),
            "volatility_pct": round(volatility * 100, 2),
            "range_pct": round(rng * 100, 2),
            "min_price": min(prices),
            "max_price": max(prices),
        }

    def should_advance_from_phase0(self) -> bool:
        """
        بررسی می‌کند آیا از فاز ۰ باید خارج شود
        """
        if self.get_current_phase() != 0:
            return False

        p0_cfg = self.ph_cfg["phase_0"]
        start_str = self._get_state("phase0_start")
        if not start_str:
            return False

        start = datetime.fromisoformat(start_str)
        days_elapsed = (datetime.utcnow() - start).days
        min_samples = p0_cfg.get("min_volatility_samples", 10)

        # شرط حداقل نمونه‌ها
        with self._conn() as conn:
            count = conn.execute(
                "SELECT COUNT(DISTINCT ts) FROM volatility_samples"
            ).fetchone()[0]

        has_enough_samples = count >= min_samples
        has_min_days = days_elapsed >= p0_cfg["min_days"]
        has_max_days = days_elapsed >= p0_cfg["max_days"]

        if has_max_days:
            return True  # حداکثر مدت → اجباری خارج می‌شود
        if has_min_days and has_enough_samples:
            return True

        return False

    def advance_to_phase1(self):
        self._set_state("phase", 1)
        self._set_state("phase1_start", datetime.utcnow().isoformat())
        logger.info("→ Advanced to Phase 1 (Deployment)")

    # ─────────────────────────────────────────────
    # فاز ۱ — استقرار سرمایه
    # ─────────────────────────────────────────────

    def get_phase1_days_elapsed(self) -> int:
        start_str = self._get_state("phase1_start")
        if not start_str:
            return 0
        start = datetime.fromisoformat(start_str)
        return (datetime.utcnow() - start).days

    def is_phase1_deadline_approaching(self, warn_days: int = 30) -> bool:
        """ماه ۶ نزدیک است؟"""
        elapsed = self.get_phase1_days_elapsed()
        return elapsed >= (180 - warn_days)

    def should_advance_to_phase2(self) -> bool:
        elapsed = self.get_phase1_days_elapsed()
        return elapsed >= 180  # ۶ ماه = ~۱۸۰ روز

    def advance_to_phase2(self):
        self._set_state("phase", 2)
        self._set_state("phase2_start", datetime.utcnow().isoformat())
        logger.info("→ Advanced to Phase 2 (Rebalancing)")

    # ─────────────────────────────────────────────
    # فاز ۲ — تعادل‌بخشی
    # ─────────────────────────────────────────────

    def check_rebalance_needed(self, current_allocations: dict,
                               target_allocations: dict) -> list:
        """
        بررسی می‌کند کدام دارایی‌ها از وزن هدف منحرف شده‌اند.
        current_allocations: {symbol: current_pct}
        target_allocations: {symbol: target_pct}
        """
        alerts = []
        threshold = self.ph_cfg["phase_2"]["rebalance_alert_pct"]
        for sym, target in target_allocations.items():
            current = current_allocations.get(sym, 0)
            deviation = abs(current - target)
            if deviation >= threshold:
                alerts.append({
                    "symbol": sym,
                    "current_pct": round(current, 1),
                    "target_pct": target,
                    "deviation": round(deviation, 1),
                })
        return alerts

    # ─────────────────────────────────────────────
    # ثبت و خواندن امتیازها
    # ─────────────────────────────────────────────

    def record_score(self, score_result: dict, market_data: dict):
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO score_history(symbol, score, label, data_json) VALUES (?,?,?,?)",
                (
                    score_result["symbol"],
                    score_result.get("score"),
                    score_result.get("label"),
                    json.dumps({
                        "details": score_result.get("details", {}),
                        "active_scenarios": score_result.get("active_scenarios", []),
                    })
                )
            )

    def get_score_baseline(self, symbol: str, days: int = 14) -> dict:
        """
        میانگین امتیاز در N روز گذشته — «نرمال» هر کوین
        """
        since = (datetime.utcnow() - timedelta(days=days)).isoformat()
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT score FROM score_history WHERE symbol=? AND ts>=? AND score IS NOT NULL",
                (symbol, since)
            ).fetchall()

        scores = [r["score"] for r in rows]
        if not scores:
            return {"symbol": symbol, "avg_score": None, "samples": 0}

        return {
            "symbol": symbol,
            "avg_score": round(sum(scores) / len(scores), 2),
            "min_score": round(min(scores), 2),
            "max_score": round(max(scores), 2),
            "samples": len(scores),
        }

    # ─────────────────────────────────────────────
    # ردیابی هشدارهای قیمت
    # ─────────────────────────────────────────────

    def record_price_alert(self, symbol: str, price: float, change_pct: float):
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO price_alerts_sent(symbol, price, change) VALUES (?,?,?)",
                (symbol, price, change_pct)
            )

    def last_price_alert_time(self, symbol: str) -> Optional[datetime]:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT ts FROM price_alerts_sent WHERE symbol=? ORDER BY ts DESC LIMIT 1",
                (symbol,)
            ).fetchone()
        if row:
            return datetime.fromisoformat(row["ts"])
        return None

    # ─────────────────────────────────────────────
    # وضعیت کلی
    # ─────────────────────────────────────────────

    def get_current_phase(self) -> int:
        return self._get_state("phase", 0)

    def get_status_summary(self) -> dict:
        phase = self.get_current_phase()
        summary = {
            "phase": phase,
            "phase_name": {0: "کالیبراسیون", 1: "استقرار سرمایه", 2: "تعادل‌بخشی"}.get(phase),
        }
        if phase == 0:
            start_str = self._get_state("phase0_start")
            if start_str:
                days = (datetime.utcnow() - datetime.fromisoformat(start_str)).days
                summary["days_in_phase"] = days
                summary["phase0_complete_pct"] = min(100, round(days / self.ph_cfg["phase_0"]["max_days"] * 100))
        elif phase == 1:
            elapsed = self.get_phase1_days_elapsed()
            summary["days_in_phase"] = elapsed
            summary["months_remaining"] = max(0, round((180 - elapsed) / 30, 1))
        return summary
