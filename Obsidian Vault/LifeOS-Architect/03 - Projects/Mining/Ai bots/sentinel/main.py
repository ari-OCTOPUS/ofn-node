"""
SENTINEL — main.py
حلقه‌ی اصلی · سبک · مناسب Raspberry Pi 3B
اجرا: python3 main.py
یا با cron هر ۱۵ دقیقه: */15 * * * * /usr/bin/python3 /home/pi/sentinel/main.py
"""

import os
import sys
import yaml
import logging
import logging.handlers
import time
import signal as sig_module
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

# ─── بارگذاری .env ───
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

from data_fetcher import DataFetcher
from scorer import EntryScorer
from phase_manager import PhaseManager
from telegram_signaler import TelegramSignaler
from wallet_tracker import WalletTracker

# ─────────────────────────────────────────────
# راه‌اندازی لاگ
# ─────────────────────────────────────────────

def setup_logging(config: dict):
    log_cfg = config.get("logging", {})
    level = getattr(logging, log_cfg.get("level", "INFO"))
    log_file = log_cfg.get("file", "sentinel.log")
    max_bytes = log_cfg.get("max_bytes", 5_242_880)
    backup_count = log_cfg.get("backup_count", 3)

    handlers = [
        logging.StreamHandler(sys.stdout),
        logging.handlers.RotatingFileHandler(
            log_file, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
        ),
    ]
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=handlers,
    )

logger = logging.getLogger("sentinel.main")

# ─────────────────────────────────────────────
# بارگذاری config
# ─────────────────────────────────────────────

def load_config() -> dict:
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

# ─────────────────────────────────────────────
# SENTINEL
# ─────────────────────────────────────────────

class SentinelBot:
    def __init__(self):
        self.config = load_config()
        setup_logging(self.config)
        logger.info("=" * 50)
        logger.info("SENTINEL starting up...")

        db_path = self.config["database"]["path"]
        self.fetcher   = DataFetcher(self.config)
        self.scorer    = EntryScorer(self.config)
        self.phase_mgr = PhaseManager(self.config, db_path)
        self.signaler  = TelegramSignaler(self.config)
        self.tracker   = WalletTracker(self.config, db_path)

        self.phase_mgr.initialize()
        self._last_daily_report = None
        self._last_price_check: dict = {}   # {symbol: (price, ts)}

    # ─────────────────────────────────────────────
    # گام اصلی — هر بار که اجرا می‌شود
    # ─────────────────────────────────────────────

    def run_cycle(self):
        phase = self.phase_mgr.get_current_phase()
        logger.info(f"--- Cycle start | Phase {phase} | {datetime.utcnow().isoformat()} ---")

        # ۱. گزارش روزانه (اگر ساعت مشخص فرا رسیده)
        self._maybe_send_daily_report()

        # ۲. بر اساس فاز
        if phase == 0:
            self._phase0_cycle()
            if self.phase_mgr.should_advance_from_phase0():
                self.phase_mgr.advance_to_phase1()
                self.signaler.send(
                    "✅ <b>فاز ۰ کامل شد!</b>\n\n"
                    "کالیبراسیون تمام — ربات وارد فاز ۱ (استقرار سرمایه) شد.\n"
                    "از این لحظه سیگنال‌های ورود صادر می‌شود."
                )

        elif phase == 1:
            self._phase1_cycle()
            if self.phase_mgr.should_advance_to_phase2():
                self.phase_mgr.advance_to_phase2()
                self.signaler.send(
                    "🏁 <b>فاز ۱ تمام شد!</b>\n\n"
                    "۶ ماه استقرار کامل. وارد فاز ۲ (تعادل‌بخشی) شدیم."
                )
        elif phase == 2:
            self._phase2_cycle()

        logger.info("--- Cycle complete ---")

    # ─────────────────────────────────────────────
    # فاز ۰ — کالیبراسیون
    # ─────────────────────────────────────────────

    def _phase0_cycle(self):
        """ثبت نوسان روزانه بدون صدور سیگنال"""
        status = self.phase_mgr.get_status_summary()
        days = status.get("days_in_phase", 0)
        logger.info(f"Phase 0: day {days}")

        for sym in self.config["assets"]:
            asset_cfg = self.config["assets"].get(sym, {})
            if asset_cfg.get("pole") == "stable" or asset_cfg.get("watch_only"):
                continue
            price_data = self.fetcher.get_price_data(sym)
            if price_data and price_data.get("price"):
                self.phase_mgr.record_volatility(sym, price_data["price"])
                logger.debug(f"  Volatility recorded: {sym} ${price_data['price']:,.2f}")

        # هشدار قیمت ۵٪ در فاز ۰ هم فعال است
        self._check_price_alerts(send_score=False)

        # گزارش وضعیت روزانه در فاز ۰
        if days % 1 == 0:  # هر روز
            for sym in ("CORE", "XEL", "XMR", "ZEC", "TAO", "DIL"):
                stats = self.phase_mgr.get_volatility_stats(sym)
                if stats["volatility_pct"] is not None:
                    logger.info(
                        f"  {sym}: vol={stats['volatility_pct']:.1f}٪  "
                        f"range={stats['range_pct']:.1f}٪  samples={stats['samples']}"
                    )

    # ─────────────────────────────────────────────
    # فاز ۱ — امتیازدهی و سیگنال
    # ─────────────────────────────────────────────

    def _phase1_cycle(self):
        """امتیاز هر دارایی را محاسبه و در صورت مساعد، سیگنال می‌دهد"""
        fear_greed = self.fetcher.get_fear_greed()
        all_scores = []

        for sym, asset_cfg in self.config["assets"].items():
            if asset_cfg.get("watch_only") or sym in ("USDC", "USDT"):
                all_scores.append({"symbol": sym, "score": None, "label": "stable_parking"})
                continue

            logger.info(f"Scoring {sym}...")
            market_data = self.fetcher.fetch_all(sym)
            score_result = self.scorer.score(sym, market_data)

            # ثبت در تاریخچه
            self.phase_mgr.record_score(score_result, market_data)
            all_scores.append(score_result)

            # سیگنال ورود اگر امتیاز کافی
            self._maybe_send_entry_signal(sym, score_result, market_data, asset_cfg)

        # هشدار قیمت ۵٪
        self._check_price_alerts(send_score=True, all_scores=all_scores)

        # هشدار پایان ماه ۶
        if self.phase_mgr.is_phase1_deadline_approaching(warn_days=30):
            elapsed = self.phase_mgr.get_phase1_days_elapsed()
            remaining_days = 180 - elapsed
            if remaining_days in (30, 15, 7, 3, 1):
                self.signaler.send(
                    f"⏰ <b>هشدار: {remaining_days} روز تا پایان فاز استقرار</b>\n\n"
                    f"دارایی‌های سرمایه‌گذاری‌نشده با DCA ساده وارد می‌شوند."
                )

    def _maybe_send_entry_signal(self, symbol: str, score_result: dict,
                                  market_data: dict, asset_cfg: dict):
        """بررسی می‌کند آیا باید سیگنال ورود بفرستد"""
        label = score_result.get("label", "watch_only")
        score = score_result.get("score")

        if label not in ("strong_entry", "moderate_entry", "weak_entry"):
            return
        if score is None:
            return

        # بررسی cooldown
        tg_cfg = self.config.get("telegram", {})
        cooldown_min = tg_cfg.get("signal_cooldown_minutes", 30)
        last_alert = self.phase_mgr.last_price_alert_time(symbol)
        if last_alert:
            if (datetime.utcnow() - last_alert).total_seconds() < cooldown_min * 60:
                logger.info(f"  {symbol}: cooldown active, skipping signal")
                return

        # بودجه و پله
        remaining = self.tracker.get_remaining_budget(symbol)
        if remaining < 50:  # حداقل A$50
            logger.info(f"  {symbol}: budget exhausted (${remaining:.0f} remaining)")
            return

        tranches_used = self.tracker.get_tranche_count(symbol)
        total_tranches = asset_cfg.get("dca_tranches", 4)
        if tranches_used >= total_tranches:
            logger.info(f"  {symbol}: all tranches used ({tranches_used}/{total_tranches})")
            return

        suggested = self.scorer.suggest_tranche(
            symbol, score_result, remaining, total_tranches - tranches_used
        )
        if not suggested or suggested < 50:
            return

        tranche_num = tranches_used + 1
        logger.info(f"  SIGNAL: {symbol} score={score:.0f} → tranche {tranche_num} A${suggested:.0f}")

        self.signaler.send_entry_signal(
            score_result=score_result,
            market_data=market_data,
            suggested_aud=suggested,
            tranche_num=tranche_num,
            total_tranches=total_tranches,
        )
        self.phase_mgr.record_price_alert(symbol, score_result["details"].get("price", 0), 0)

    # ─────────────────────────────────────────────
    # فاز ۲ — تعادل‌بخشی
    # ─────────────────────────────────────────────

    def _phase2_cycle(self):
        """رصد سلامت پرتفوی و هشدار rebalancing"""
        # قیمت‌های فعلی
        current_prices = {}
        for sym in self.config["assets"]:
            price_data = self.fetcher.get_price_data(sym)
            if price_data:
                current_prices[sym] = price_data.get("price", 0)

        # موجودی پرتفوی
        portfolio = self.tracker.get_portfolio_summary(current_prices)
        total_value = portfolio.get("total_value_usd", 0)

        if total_value > 0:
            current_allocs = {}
            for sym, data in portfolio["assets"].items():
                val = data.get("current_value_usd", 0)
                current_allocs[sym] = (val / total_value * 100) if total_value else 0

            target_allocs = {
                sym: cfg["allocation_pct"]
                for sym, cfg in self.config["assets"].items()
            }
            deviations = self.phase_mgr.check_rebalance_needed(current_allocs, target_allocs)
            if deviations:
                logger.info(f"Rebalance needed for: {[d['symbol'] for d in deviations]}")
                self.signaler.send_rebalance_alert(deviations)

        # سیگنال‌های ۵٪ ادامه دارد
        self._check_price_alerts(send_score=False)

    # ─────────────────────────────────────────────
    # هشدار قیمت ۵٪
    # ─────────────────────────────────────────────

    def _check_price_alerts(self, send_score: bool = False, all_scores: list = None):
        alert_pct = self.config["risk"]["price_alert_pct"] / 100
        tg_cfg = self.config.get("telegram", {})
        cooldown_min = tg_cfg.get("signal_cooldown_minutes", 30)

        for sym in ("CORE", "XEL", "XMR", "ZEC", "TAO", "DIL"):
            price_data = self.fetcher.get_price_data(sym)
            if not price_data:
                continue

            current_price = price_data.get("price", 0)
            prev = self._last_price_check.get(sym)

            if prev:
                prev_price, prev_ts = prev
                if prev_price > 0:
                    change = (current_price - prev_price) / prev_price
                    if abs(change) >= alert_pct:
                        # بررسی cooldown
                        last_alert = self.phase_mgr.last_price_alert_time(sym)
                        if last_alert and (datetime.utcnow() - last_alert).total_seconds() < cooldown_min * 60:
                            pass
                        else:
                            # یافتن امتیاز جاری
                            score_label = "unknown"
                            new_score = 0
                            if all_scores:
                                for sr in all_scores:
                                    if sr.get("symbol") == sym:
                                        new_score = sr.get("score", 0) or 0
                                        score_label = sr.get("label", "unknown")
                                        break

                            logger.info(f"PRICE ALERT: {sym} {change*100:.1f}٪ → ${current_price:,.2f}")
                            self.signaler.send_price_alert(
                                sym, current_price, change * 100, new_score, score_label
                            )
                            self.phase_mgr.record_price_alert(sym, current_price, change * 100)

            self._last_price_check[sym] = (current_price, datetime.utcnow())

    # ─────────────────────────────────────────────
    # گزارش روزانه
    # ─────────────────────────────────────────────

    def _maybe_send_daily_report(self):
        report_hour = self.config.get("telegram", {}).get("daily_report_hour", 8)
        now = datetime.utcnow()

        # UTC+11 = AEDT (سیدنی)
        sydney_hour = (now.hour + 11) % 24

        if sydney_hour == report_hour:
            today = now.date()
            if self._last_daily_report != today:
                self._last_daily_report = today
                self._send_full_daily_report()

    def _send_full_daily_report(self):
        logger.info("Sending daily report...")
        fear_greed = self.fetcher.get_fear_greed()
        phase_summary = self.phase_mgr.get_status_summary()
        all_scores = []

        for sym, asset_cfg in self.config["assets"].items():
            if sym in ("USDC", "USDT") or asset_cfg.get("watch_only"):
                all_scores.append({"symbol": sym, "score": None, "label": "stable_parking",
                                   "details": {}})
                continue
            market_data = self.fetcher.fetch_all(sym)
            score_result = self.scorer.score(sym, market_data)
            all_scores.append(score_result)

        self.signaler.send_daily_report(all_scores, phase_summary, fear_greed)

    # ─────────────────────────────────────────────
    # دستورات تلگرام (پردازش ساده)
    # ─────────────────────────────────────────────

    def process_command(self, command: str, args: str = ""):
        """
        دستورات اپراتور از طریق تلگرام:
        /status — وضعیت کلی
        /score BTC — امتیاز فوری
        /confirm_BTC AMOUNT PRICE — ثبت خرید
        /portfolio — گزارش پرتفوی
        /scenario quantum_threat active — تغییر وضعیت سناریو
        """
        cmd = command.lower().strip("/")

        if cmd == "status":
            summary = self.phase_mgr.get_status_summary()
            self.signaler.send(
                f"📊 <b>وضعیت SENTINEL</b>\n"
                f"فاز: {summary['phase']} — {summary['phase_name']}\n"
                f"روز در فاز: {summary.get('days_in_phase', '?')}"
            )

        elif cmd == "portfolio":
            prices = {}
            for sym in self.config["assets"]:
                pd = self.fetcher.get_price_data(sym)
                if pd:
                    prices[sym] = pd.get("price", 0)
            portfolio = self.tracker.get_portfolio_summary(prices)
            self.signaler.send(self.tracker.format_portfolio_text(portfolio))

        elif cmd.startswith("score"):
            target = args.strip().upper() if args else "CORE"
            market_data = self.fetcher.fetch_all(target)
            score_result = self.scorer.score(target, market_data)
            self.signaler.send(
                f"🔍 امتیاز فوری <b>{target}</b>\n"
                f"نمره: {score_result.get('score', 'N/A')}/۱۰۰\n"
                f"وضعیت: {self.scorer.label_to_persian(score_result.get('label', ''))}"
            )

        elif cmd.startswith("confirm_"):
            sym = cmd.split("_", 1)[1].upper()
            parts = args.split()
            if len(parts) >= 2:
                try:
                    amount_aud = float(parts[0])
                    price_usd = float(parts[1])
                    purchase_id = self.tracker.record_purchase(sym, amount_aud, price_usd)
                    self.signaler.send_purchase_confirmed(
                        sym, amount_aud, price_usd,
                        os.getenv(f"COLD_WALLET_{sym}", "نامشخص")
                    )
                except ValueError:
                    self.signaler.send("❌ فرمت اشتباه. مثال: /confirm_BTC 500 86400")

        elif cmd == "scenario":
            parts = args.split()
            if len(parts) == 2:
                sc_name, new_status = parts
                if self.scorer.update_scenario(sc_name, new_status):
                    scenario = self.config["scenarios"].get(sc_name, {})
                    self.signaler.send_scenario_alert(
                        sc_name, new_status,
                        scenario.get("alert_message", "سناریو به‌روز شد")
                    )


# ─────────────────────────────────────────────
# نقطه ورود
# ─────────────────────────────────────────────

def main():
    bot = SentinelBot()

    # اجرای یک چرخه (برای cron)
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        bot.run_cycle()
        return

    # حلقه دائم (برای اجرای مستقیم)
    logger.info("Running in continuous mode (Ctrl+C to stop)")
    interval = 900  # ۱۵ دقیقه

    def handle_sigterm(signum, frame):
        logger.info("SIGTERM received, shutting down...")
        sys.exit(0)

    sig_module.signal(sig_module.SIGTERM, handle_sigterm)

    while True:
        try:
            bot.run_cycle()
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt — stopping")
            break
        except Exception as e:
            logger.exception(f"Unexpected error in cycle: {e}")
            # ادامه می‌دهد حتی در صورت خطا
        logger.info(f"Sleeping {interval}s until next cycle...")
        time.sleep(interval)


if __name__ == "__main__":
    main()
