"""
SENTINEL — telegram_bot.py
ربات تلگرام دوطرفه: دریافت دستورات + اجرا

نحوه اجرا (جدا از main.py):
  python3 telegram_bot.py

یا اینکه main.py خودش این رو به‌صورت thread اجرا می‌کند.

دستورات پشتیبانی‌شده:
  /start          — خوش‌آمدگویی و راهنما
  /help           — لیست دستورات
  /status         — وضعیت فاز و سیستم
  /report         — گزارش روزانه همین الان
  /score CORE     — امتیاز فوری یک دارایی
  /portfolio      — وضعیت پرتفوی
  /confirm_CORE 500 0.85   — ثبت خرید
  /scenario fiat_erosion active  — تغییر وضعیت سناریو
  /ping           — چک اتصال
"""

import os
import sys
import time
import logging
import requests
import threading
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# ─── بارگذاری .env ───
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

sys.path.insert(0, str(Path(__file__).parent))

logger = logging.getLogger("sentinel.telegram_bot")

# ─────────────────────────────────────────────────────────────
# کلاس اصلی ربات تلگرام
# ─────────────────────────────────────────────────────────────

class TelegramBot:
    """
    ربات تلگرام دوطرفه با long-polling
    نیازی به کتابخانه‌ی خارجی ندارد — فقط requests
    """

    POLL_TIMEOUT = 30   # ثانیه — long polling
    RETRY_DELAY  = 10   # ثانیه — در صورت خطا

    def __init__(self, sentinel_bot=None):
        """
        sentinel_bot: نمونه‌ای از SentinelBot (اختیاری)
        اگر None باشد، فقط دستورات ساده پاسخ می‌دهد
        """
        self.bot_token = os.getenv("SENTINEL_BOT_TOKEN", "")
        self.chat_id   = os.getenv("SENTINEL_CHAT_ID", "")
        self.sentinel  = sentinel_bot

        if not self.bot_token:
            raise ValueError("SENTINEL_BOT_TOKEN در .env تعریف نشده!")
        if not self.chat_id:
            raise ValueError("SENTINEL_CHAT_ID در .env تعریف نشده!")

        self.base_url   = f"https://api.telegram.org/bot{self.bot_token}"
        self.offset     = 0
        self._stop_flag = threading.Event()

        logger.info(f"TelegramBot آماده | chat_id={self.chat_id}")

    # ─────────────────────────────────────────────
    # ارسال پیام
    # ─────────────────────────────────────────────

    def send(self, text: str, parse_mode: str = "HTML") -> bool:
        """ارسال پیام به chat_id اصلی"""
        try:
            resp = requests.post(
                f"{self.base_url}/sendMessage",
                json={
                    "chat_id": self.chat_id,
                    "text": text,
                    "parse_mode": parse_mode,
                    "disable_web_page_preview": True,
                },
                timeout=15,
            )
            resp.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"ارسال پیام شکست خورد: {e}")
            return False

    # ─────────────────────────────────────────────
    # دریافت آپدیت‌ها (long polling)
    # ─────────────────────────────────────────────

    def _get_updates(self) -> list:
        try:
            resp = requests.get(
                f"{self.base_url}/getUpdates",
                params={
                    "offset": self.offset,
                    "timeout": self.POLL_TIMEOUT,
                    "allowed_updates": ["message"],
                },
                timeout=self.POLL_TIMEOUT + 5,
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("result", [])
        except requests.exceptions.Timeout:
            return []   # طبیعی است در long polling
        except Exception as e:
            logger.warning(f"getUpdates خطا: {e}")
            return []

    # ─────────────────────────────────────────────
    # امنیت — فقط chat_id مجاز
    # ─────────────────────────────────────────────

    def _is_authorized(self, update: dict) -> bool:
        msg = update.get("message", {})
        chat = msg.get("chat", {})
        return str(chat.get("id", "")) == str(self.chat_id)

    # ─────────────────────────────────────────────
    # پردازش هر پیام
    # ─────────────────────────────────────────────

    def _handle_update(self, update: dict):
        msg = update.get("message", {})
        text = msg.get("text", "").strip()

        if not text or not text.startswith("/"):
            return   # فقط دستورات پردازش می‌شوند

        parts = text.split(None, 1)
        raw_cmd = parts[0].lower()
        args    = parts[1] if len(parts) > 1 else ""

        # حذف @botname از دستور اگر وجود داشت
        if "@" in raw_cmd:
            raw_cmd = raw_cmd.split("@")[0]

        logger.info(f"دستور دریافت شد: {raw_cmd!r} args={args!r}")

        # ─── روتر دستورات ───
        try:
            if raw_cmd == "/start":
                self._cmd_start()
            elif raw_cmd == "/help":
                self._cmd_help()
            elif raw_cmd == "/ping":
                self._cmd_ping()
            elif raw_cmd == "/status":
                self._cmd_status()
            elif raw_cmd == "/report":
                self._cmd_report()
            elif raw_cmd == "/score":
                self._cmd_score(args)
            elif raw_cmd == "/portfolio":
                self._cmd_portfolio()
            elif raw_cmd == "/scenario":
                self._cmd_scenario(args)
            elif raw_cmd.startswith("/confirm_"):
                sym = raw_cmd.split("_", 1)[1].upper()
                self._cmd_confirm(sym, args)
            else:
                self.send(
                    f"❓ دستور ناشناخته: <code>{raw_cmd}</code>\n"
                    f"برای راهنما: /help"
                )
        except Exception as e:
            logger.exception(f"خطا در پردازش دستور {raw_cmd}: {e}")
            self.send(f"❌ خطا در اجرای دستور:\n<code>{e}</code>")

    # ─────────────────────────────────────────────
    # دستورات
    # ─────────────────────────────────────────────

    def _cmd_start(self):
        self.send(
            "🛡️ <b>SENTINEL فعال است</b>\n"
            "\n"
            "سیستم هوشمند رصد کریپتو آماده‌ی خدمت‌رسانی است.\n"
            "\n"
            "برای راهنما: /help"
        )

    def _cmd_help(self):
        self.send(
            "📋 <b>دستورات SENTINEL</b>\n"
            "\n"
            "🔍 <b>اطلاعات:</b>\n"
            "  /status — وضعیت فاز و سیستم\n"
            "  /report — گزارش روزانه همین الان\n"
            "  /score CORE — امتیاز فوری یک دارایی\n"
            "  /portfolio — وضعیت کامل پرتفوی\n"
            "\n"
            "✅ <b>ثبت خرید:</b>\n"
            "  /confirm_CORE 500 0.85\n"
            "  /confirm_XMR 350 192\n"
            "  /confirm_TAO 400 380\n"
            "\n"
            "🌐 <b>سناریوها:</b>\n"
            "  /scenario fiat_erosion active\n"
            "  /scenario quantum_threat emerging\n"
            "  /scenario regulatory_crackdown inactive\n"
            "\n"
            "⚙️ <b>سایر:</b>\n"
            "  /ping — چک اتصال"
        )

    def _cmd_ping(self):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.send(f"🟢 SENTINEL آنلاین است\n🕐 {now}")

    def _cmd_status(self):
        if not self.sentinel:
            self.send("⚠️ حالت محدود — SentinelBot متصل نیست")
            return
        try:
            summary = self.sentinel.phase_mgr.get_status_summary()
            phase   = summary.get("phase", "؟")
            name    = summary.get("phase_name", "؟")
            days    = summary.get("days_in_phase", "؟")

            lines = [
                f"📊 <b>وضعیت SENTINEL</b>",
                f"",
                f"📍 فاز {phase}: <b>{name}</b>",
                f"📅 روز در فاز: {days}",
            ]

            if phase == 0:
                pct = summary.get("phase0_complete_pct", 0)
                lines.append(f"⏳ پیشرفت کالیبراسیون: {pct}٪")
            elif phase == 1:
                rem = summary.get("months_remaining", "؟")
                lines.append(f"⏳ {rem} ماه تا پایان استقرار")
            elif phase == 2:
                lines.append("♻️ حالت تعادل‌بخشی فعال")

            lines.append(f"\n🕐 {datetime.now().strftime('%H:%M')}")
            self.send("\n".join(lines))
        except Exception as e:
            self.send(f"❌ خطا در دریافت وضعیت: {e}")

    def _cmd_report(self):
        if not self.sentinel:
            self.send("⚠️ حالت محدود — SentinelBot متصل نیست")
            return
        self.send("⏳ در حال تهیه گزارش...")
        try:
            self.sentinel._send_full_daily_report()
        except Exception as e:
            self.send(f"❌ خطا در تهیه گزارش: {e}")

    def _cmd_score(self, args: str):
        if not self.sentinel:
            self.send("⚠️ حالت محدود — SentinelBot متصل نیست")
            return

        sym = args.strip().upper() if args.strip() else "CORE"
        valid = list(self.sentinel.config.get("assets", {}).keys())
        if sym not in valid:
            self.send(
                f"❌ دارایی ناشناخته: <b>{sym}</b>\n"
                f"دارایی‌های معتبر: {', '.join(valid)}"
            )
            return

        self.send(f"⏳ در حال محاسبه امتیاز {sym}...")
        try:
            market_data  = self.sentinel.fetcher.fetch_all(sym)
            score_result = self.sentinel.scorer.score(sym, market_data)
            score  = score_result.get("score")
            label  = score_result.get("label", "watch_only")
            details = score_result.get("details", {})
            price  = details.get("price", 0)
            dd     = details.get("drawdown_pct", 0)

            from telegram_signaler import LABEL_EMOJI
            emoji = LABEL_EMOJI.get(label, "⚪")

            label_fa = {
                "strong_entry":   "ناحیه مساعد 🟢",
                "moderate_entry": "نسبتاً مساعد 🟡",
                "weak_entry":     "ورود احتیاطی 🟠",
                "watch_only":     "فقط رصد 🔴",
            }.get(label, label)

            score_text = f"{score:.0f}/۱۰۰" if score is not None else "N/A"

            self.send(
                f"{emoji} <b>امتیاز فوری — {sym}</b>\n"
                f"\n"
                f"نمره: <b>{score_text}</b>\n"
                f"وضعیت: {label_fa}\n"
                f"قیمت: ${price:,.2f}\n"
                f"از قله‌ی ۹۰روزه: −{dd:.1f}٪\n"
                f"\n"
                f"🕐 {datetime.now().strftime('%H:%M')}"
            )
        except Exception as e:
            self.send(f"❌ خطا در محاسبه امتیاز {sym}: {e}")

    def _cmd_portfolio(self):
        if not self.sentinel:
            self.send("⚠️ حالت محدود — SentinelBot متصل نیست")
            return
        try:
            prices = {}
            for sym in self.sentinel.config.get("assets", {}):
                pd = self.sentinel.fetcher.get_price_data(sym)
                if pd:
                    prices[sym] = pd.get("price", 0)
            portfolio = self.sentinel.tracker.get_portfolio_summary(prices)
            text = self.sentinel.tracker.format_portfolio_text(portfolio)
            self.send(text)
        except Exception as e:
            self.send(f"❌ خطا در دریافت پرتفوی: {e}")

    def _cmd_confirm(self, sym: str, args: str):
        if not self.sentinel:
            self.send("⚠️ حالت محدود — SentinelBot متصل نیست")
            return

        parts = args.split()
        if len(parts) < 2:
            self.send(
                f"❌ فرمت اشتباه\n"
                f"مثال: <code>/confirm_{sym} 500 86400</code>\n"
                f"(مبلغ AUD · قیمت USD)"
            )
            return

        try:
            amount_aud = float(parts[0])
            price_usd  = float(parts[1])
        except ValueError:
            self.send(f"❌ عدد نامعتبر. مثال: /confirm_{sym} 500 86400")
            return

        try:
            self.sentinel.tracker.record_purchase(sym, amount_aud, price_usd)
            cold = os.getenv(f"COLD_WALLET_{sym}", "تعریف‌نشده")
            self.sentinel.signaler.send_purchase_confirmed(sym, amount_aud, price_usd, cold)
        except Exception as e:
            self.send(f"❌ خطا در ثبت خرید: {e}")

    def _cmd_scenario(self, args: str):
        if not self.sentinel:
            self.send("⚠️ حالت محدود — SentinelBot متصل نیست")
            return

        parts = args.split()
        if len(parts) != 2:
            self.send(
                "❌ فرمت اشتباه\n"
                "مثال: <code>/scenario fiat_erosion active</code>\n"
                "وضعیت‌ها: <code>inactive</code> | <code>emerging</code> | <code>active</code>"
            )
            return

        sc_name, new_status = parts[0], parts[1]
        valid_scenarios = list(self.sentinel.config.get("scenarios", {}).keys())
        valid_statuses  = ["inactive", "emerging", "active"]

        if sc_name not in valid_scenarios:
            self.send(
                f"❌ سناریو ناشناخته: <b>{sc_name}</b>\n"
                f"سناریوهای معتبر: {', '.join(valid_scenarios)}"
            )
            return

        if new_status not in valid_statuses:
            self.send(
                f"❌ وضعیت نامعتبر: <b>{new_status}</b>\n"
                f"وضعیت‌های معتبر: {', '.join(valid_statuses)}"
            )
            return

        try:
            if self.sentinel.scorer.update_scenario(sc_name, new_status):
                scenario = self.sentinel.config["scenarios"].get(sc_name, {})
                self.sentinel.signaler.send_scenario_alert(
                    sc_name, new_status,
                    scenario.get("alert_message", "سناریو به‌روز شد")
                )
            else:
                self.send(f"⚠️ تغییری انجام نشد — وضعیت فعلی احتمالاً همین بود")
        except Exception as e:
            self.send(f"❌ خطا در به‌روزرسانی سناریو: {e}")

    # ─────────────────────────────────────────────
    # حلقه‌ی اصلی polling
    # ─────────────────────────────────────────────

    def run_forever(self):
        """
        حلقه‌ی اصلی — بی‌نهایت آپدیت‌ها رو چک می‌کنه
        با Ctrl+C یا stop() متوقف می‌شود
        """
        logger.info("TelegramBot شروع به polling کرد...")
        self.send("🟢 SENTINEL راه‌اندازی شد — آماده‌ی دریافت دستور")

        while not self._stop_flag.is_set():
            try:
                updates = self._get_updates()

                for update in updates:
                    self.offset = update["update_id"] + 1

                    if not self._is_authorized(update):
                        logger.warning(
                            f"پیام از chat_id غیرمجاز: "
                            f"{update.get('message', {}).get('chat', {}).get('id')}"
                        )
                        continue

                    self._handle_update(update)

            except KeyboardInterrupt:
                logger.info("متوقف شد (Ctrl+C)")
                break
            except Exception as e:
                logger.exception(f"خطای غیرمنتظره در polling loop: {e}")
                time.sleep(self.RETRY_DELAY)

        logger.info("TelegramBot متوقف شد.")

    def run_in_thread(self) -> threading.Thread:
        """
        ربات رو در یه thread جداگانه اجرا می‌کند
        (برای استفاده از داخل main.py)
        """
        t = threading.Thread(target=self.run_forever, daemon=True, name="TelegramBot")
        t.start()
        logger.info("TelegramBot در thread جداگانه اجرا شد")
        return t

    def stop(self):
        self._stop_flag.set()


# ─────────────────────────────────────────────────────────────
# نقطه‌ی ورود مستقل
# ─────────────────────────────────────────────────────────────

def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("telegram_bot.log", encoding="utf-8"),
        ]
    )

    # ─── راه‌اندازی SentinelBot ───
    try:
        import yaml
        from data_fetcher import DataFetcher
        from scorer import EntryScorer
        from phase_manager import PhaseManager
        from telegram_signaler import TelegramSignaler
        from wallet_tracker import WalletTracker

        config_path = Path(__file__).parent / "config.yaml"
        with open(config_path, encoding="utf-8") as f:
            cfg = yaml.safe_load(f)

        # ساختار ساده‌ای که دستورات رو پشتیبانی می‌کنه
        class MinimalSentinel:
            def __init__(self, config):
                self.config   = config
                db_path       = config["database"]["path"]
                self.fetcher  = DataFetcher(config)
                self.scorer   = EntryScorer(config)
                self.phase_mgr = PhaseManager(config, db_path)
                self.signaler  = TelegramSignaler(config)
                self.tracker   = WalletTracker(config, db_path)
                self.phase_mgr.initialize()

            def _send_full_daily_report(self):
                fear_greed    = self.fetcher.get_fear_greed()
                phase_summary = self.phase_mgr.get_status_summary()
                all_scores    = []
                for sym, asset_cfg in self.config["assets"].items():
                    if sym in ("USDC", "USDT") or asset_cfg.get("watch_only"):
                        all_scores.append({"symbol": sym, "score": None,
                                           "label": "stable_parking", "details": {}})
                        continue
                    market_data  = self.fetcher.fetch_all(sym)
                    score_result = self.scorer.score(sym, market_data)
                    all_scores.append(score_result)
                self.signaler.send_daily_report(all_scores, phase_summary, fear_greed)

        sentinel = MinimalSentinel(cfg)
        logger.info("SentinelBot متصل شد")

    except Exception as e:
        logger.warning(f"SentinelBot بارگذاری نشد ({e}) — حالت محدود فعال است")
        sentinel = None

    # ─── اجرای ربات ───
    bot = TelegramBot(sentinel_bot=sentinel)
    bot.run_forever()


if __name__ == "__main__":
    main()
