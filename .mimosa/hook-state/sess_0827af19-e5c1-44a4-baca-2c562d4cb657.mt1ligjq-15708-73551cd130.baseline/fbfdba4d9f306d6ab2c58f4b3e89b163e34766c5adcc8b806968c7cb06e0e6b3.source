"""
SENTINEL — telegram_signaler.py
قالب‌بندی و ارسال سیگنال‌های تلگرام
"""

import os
import logging
import requests
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

# ایموجی‌های وضعیت
LABEL_EMOJI = {
    "strong_entry":   "🟢",
    "moderate_entry": "🟡",
    "weak_entry":     "🟠",
    "watch_only":     "🔴",
    "stable_parking": "💵",
}

SCENARIO_EMOJI = {
    "quantum_threat":       "⚛️",
    "fiat_erosion":         "📉",
    "regulatory_crackdown": "⚖️",
}


class TelegramSignaler:
    def __init__(self, config: dict):
        self.config = config
        tg_cfg = config.get("telegram", {})
        self.bot_token = os.getenv(
            tg_cfg.get("bot_token_env_key", "TELEGRAM_BOT_TOKEN"), ""
        )
        self.chat_id = os.getenv(
            tg_cfg.get("chat_id_env_key", "TELEGRAM_CHAT_ID"), ""
        )
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        self.signal_cooldown = tg_cfg.get("signal_cooldown_minutes", 30)

    # ─────────────────────────────────────────────
    # ارسال پیام خام
    # ─────────────────────────────────────────────

    def send(self, text: str, parse_mode: str = "HTML") -> bool:
        if not self.bot_token or not self.chat_id:
            logger.error("Telegram credentials missing")
            return False
        try:
            resp = requests.post(self.api_url, json={
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": parse_mode,
                "disable_web_page_preview": True,
            }, timeout=10)
            resp.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Telegram send failed: {e}")
            return False

    # ─────────────────────────────────────────────
    # سیگنال ورود
    # ─────────────────────────────────────────────

    # ─── XMR/ZEC purchase-path note (update once Armin decides) ───────────
    # ⚠️  XMR is delisted from most major CEXs. Until a purchase path is
    # confirmed, signals include an honest reminder.
    # ⚠️  XMR از اکثر صرافی‌های بزرگ حذف شده. تا تصمیم نهایی، سیگنال
    # یادآوری می‌کند که مسیر خرید هنوز تأیید نشده است.
    PRIVACY_PURCHASE_NOTE = {
        "XMR": "⚠️ XMR: most CEXs have delisted it. Confirm your purchase path (atomic swap / P2P) before acting on this signal.\n⚠️ XMR: اکثر صرافی‌ها آن را حذف کرده‌اند. قبل از عمل، مسیر خرید (atomic swap / P2P) را تأیید کنید.",
        "ZEC": "⚠️ ZEC: check availability on your exchange. Delisting risk is elevated.\n⚠️ ZEC: موجودی در صرافی خود را بررسی کنید. ریسک delisting بالا است.",
    }

    def send_entry_signal(self, score_result: dict, market_data: dict,
                          suggested_aud: float, tranche_num: int,
                          total_tranches: int) -> bool:
        """
        Bilingual entry signal / سیگنال ورود دوزبانه با تمام جزئیات
        Format matches the spec example exactly.
        """
        sym = score_result["symbol"]
        score = score_result.get("score", 0)
        label = score_result.get("label", "watch_only")
        emoji = LABEL_EMOJI.get(label, "⚪")
        details = score_result.get("details", {})
        mode = score_result.get("mode", "limited")
        active_scenarios = score_result.get("active_scenarios", [])
        onchain_note = score_result.get("onchain_note", "")

        price = details.get("price", 0)
        drawdown = details.get("drawdown_pct", 0)
        fg_val = details.get("fear_greed_value", "N/A")

        label_en = {
            "strong_entry":   "favorable zone / ناحیه‌ی مساعد",
            "moderate_entry": "relatively favorable / نسبتاً مساعد",
            "weak_entry":     "cautious entry / ورود احتیاطی",
        }.get(label, label)

        social = market_data.get("social")
        social_line = ""
        if social:
            sent_pct = round(social.get("sentiment", 0.5) * 100)
            social_label = ("fear (favorable) / ترس (مساعد)" if sent_pct < 40
                            else ("neutral / خنثی" if sent_pct < 65
                                  else "greed / طمع"))
            social_line = f"Social: {social_label}"

        fg_line = ""
        if fg_val is not None and fg_val != "N/A":
            fg_en = ("fear (favorable) / ترس (مساعد)" if fg_val < 35
                     else ("greed / طمع" if fg_val > 65 else "neutral / خنثی"))
            fg_line = f"Fear & Greed: {fg_val} — {fg_en}"

        # ── Build the signal (spec-aligned format) ──
        lines = [
            f"{emoji} <b>{sym} — Entry Signal / سیگنال ورود</b>",
            f"",
            f"Favorability / نمره‌ی مساعدت: <b>{score}/100</b> ({label_en})",
            f"Price / قیمت: <b>${price:,.2f}</b>  ·  −{drawdown:.1f}% from 90-day high / از قله‌ی ۹۰روزه",
        ]

        if fg_line:
            lines.append(fg_line)
        if social_line:
            lines.append(social_line)

        if mode == "full":
            onchain = market_data.get("onchain")
            if onchain:
                netflow = onchain.get("exchange_netflow", 0)
                flow_en = "net outflow (accumulation) ✅" if netflow < 0 else "net inflow ⚠️"
                flow_fa = "خروج خالص (انباشت) ✅" if netflow < 0 else "ورود خالص ⚠️"
                lines.append(f"On-chain exchange flow: {flow_en} / {flow_fa}")

        lines.append(f"")
        lines.append(
            f"Suggestion / پیشنهاد: tranche {tranche_num} of {total_tranches}"
            f" ≈ <b>A${suggested_aud:,.0f}</b>"
        )
        lines.append(f"")
        lines.append(
            f"Reminder / یادآوری: after buying, move to cold wallet, then "
            f"<code>/confirm_{sym} {suggested_aud:.0f} &lt;price&gt;</code>"
        )

        # Privacy coin purchase-path warning
        if sym in self.PRIVACY_PURCHASE_NOTE:
            lines.append(f"")
            lines.append(self.PRIVACY_PURCHASE_NOTE[sym])

        # Active scenarios
        if active_scenarios:
            lines.append(f"")
            lines.append(f"🌐 <b>Active scenarios / سناریوهای فعال:</b>")
            for sc in active_scenarios:
                sc_emoji = SCENARIO_EMOJI.get(sc["name"], "•")
                mod_sign = "+" if sc["modifier"] > 0 else ""
                lines.append(f"  {sc_emoji} {sc['message']} (score adj: {mod_sign}{sc['modifier']:.0f})")

        if onchain_note:
            lines.append(f"")
            lines.append(f"{onchain_note}")

        lines.append(f"")
        lines.append(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M')} AEDT")

        return self.send("\n".join(lines))

    # ─────────────────────────────────────────────
    # سیگنال اطلاع‌رسانی ۵٪
    # ─────────────────────────────────────────────

    def send_price_alert(self, symbol: str, price: float,
                         change_pct: float, new_score: float,
                         score_label: str) -> bool:
        direction = "صعود" if change_pct > 0 else "پایین"
        dir_emoji = "📈" if change_pct > 0 else "📉"
        emoji = LABEL_EMOJI.get(score_label, "⚪")

        text = (
            f"{dir_emoji} <b>سیگنال اطلاع‌رسانی ۵٪</b>\n"
            f"\n"
            f"<b>{symbol}</b> — {direction} {abs(change_pct):.1f}٪ "
            f"(${price:,.2f})\n"
            f"\n"
            f"{emoji} نمره از {new_score:.0f} — {score_label}\n"
            f"🕐 {datetime.now().strftime('%H:%M')}"
        )
        return self.send(text)

    # ─────────────────────────────────────────────
    # گزارش روزانه
    # ─────────────────────────────────────────────

    def send_daily_report(self, all_scores: list, phase_summary: dict,
                          fear_greed: Optional[dict] = None) -> bool:
        phase = phase_summary.get("phase", 0)
        phase_name = phase_summary.get("phase_name", "نامشخص")

        header = f"📋 <b>گزارش روزانه SENTINEL</b>\n"
        header += f"🗓️ {datetime.now().strftime('%A %Y-%m-%d')}\n"
        header += f"📍 فاز {phase}: {phase_name}"

        if fear_greed:
            fg = fear_greed.get("value", 50)
            fg_cls = fear_greed.get("classification", "Neutral")
            header += f"\n😨 Fear & Greed: {fg} ({fg_cls})"

        if phase == 0:
            days = phase_summary.get("days_in_phase", 0)
            pct = phase_summary.get("phase0_complete_pct", 0)
            header += f"\n⏳ کالیبراسیون: روز {days} · {pct}٪ کامل"
        elif phase == 1:
            rem = phase_summary.get("months_remaining", 0)
            header += f"\n⏳ {rem} ماه تا پایان فاز استقرار"

        # جدول امتیازات
        score_lines = ["\n<b>امتیازات دارایی‌ها:</b>"]
        for sr in all_scores:
            sym = sr.get("symbol", "?")
            score = sr.get("score")
            label = sr.get("label", "watch_only")
            emoji = LABEL_EMOJI.get(label, "⚪")
            details = sr.get("details", {})
            price = details.get("price", 0)

            if score is not None:
                score_lines.append(
                    f"  {emoji} <b>{sym}</b>  {score:.0f}/۱۰۰  •  ${price:,.0f}"
                )
            else:
                score_lines.append(f"  💵 <b>{sym}</b>  نقدینگی")

        footer = (
            f"\n\n<i>ربات فقط سیگنال می‌دهد — خرید و انتقال به کیف سرد دستی است</i>\n"
            f"🕐 {datetime.now().strftime('%H:%M')} UTC+11"
        )

        text = header + "\n".join(score_lines) + footer
        return self.send(text)

    # ─────────────────────────────────────────────
    # هشدار rebalancing
    # ─────────────────────────────────────────────

    def send_rebalance_alert(self, deviations: list) -> bool:
        lines = ["⚖️ <b>هشدار تعادل‌بخشی</b>\n"]
        for d in deviations:
            sym = d["symbol"]
            cur = d["current_pct"]
            tgt = d["target_pct"]
            dev = d["deviation"]
            direction = "بیش از حد بزرگ" if cur > tgt else "کمتر از هدف"
            lines.append(f"  • <b>{sym}</b>: فعلی {cur}٪ | هدف {tgt}٪ | انحراف {dev}٪ ({direction})")
        lines.append(f"\nاین سیگنال است، نه دستور. تعادل‌بخشی دستی است.")
        return self.send("\n".join(lines))

    # ─────────────────────────────────────────────
    # تأیید خرید
    # ─────────────────────────────────────────────

    def send_purchase_confirmed(self, symbol: str, amount_aud: float,
                                price_usd: float, cold_wallet: str) -> bool:
        text = (
            f"✅ <b>خرید ثبت شد</b>\n"
            f"\n"
            f"<b>{symbol}</b>\n"
            f"💵 مبلغ: A${amount_aud:,.0f}  ·  قیمت: ${price_usd:,.2f}\n"
            f"🔒 کیف سرد: <code>{cold_wallet[:12]}...{cold_wallet[-6:]}</code>\n"
            f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        return self.send(text)

    # ─────────────────────────────────────────────
    # هشدار سناریو (Big Scenarios)
    # ─────────────────────────────────────────────

    def send_scenario_alert(self, scenario_name: str, new_status: str,
                            message: str) -> bool:
        emoji = SCENARIO_EMOJI.get(scenario_name, "🌐")
        status_text = {
            "inactive": "غیرفعال ⚪",
            "emerging": "در حال ظهور 🟡",
            "active":   "فعال 🔴",
        }.get(new_status, new_status)

        text = (
            f"{emoji} <b>به‌روزرسانی سناریو</b>\n"
            f"\n"
            f"<b>{scenario_name}</b> → {status_text}\n"
            f"\n"
            f"{message}\n"
            f"\n"
            f"امتیازدهی با وزن‌های جدید به‌روز شد."
        )
        return self.send(text)
