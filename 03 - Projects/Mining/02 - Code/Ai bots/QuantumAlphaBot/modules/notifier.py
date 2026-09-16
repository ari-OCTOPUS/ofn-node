"""
Notifier — Coin Hunter report (Telegram + Discord)
====================================================
فرمت گزارش:
  • هدر: تاریخ + فیلترها
  • جدول کوین‌ها با امتیازها
  • ارزیابی Claude (ACCUMULATE/WATCH/SKIP + reasoning)
  • تخصیص سرمایه (% + $)
  • خلاصه Self-learning
  • دلایل رد
"""
import requests
from datetime import datetime
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, DISCORD_WEBHOOK


# ── Transport ────────────────────────────────────────────────────────────────

def _telegram(text: str):
    if not (TELEGRAM_TOKEN and TELEGRAM_CHAT_ID):
        return
    try:
        for i in range(0, len(text), 4000):
            requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                json={"chat_id": TELEGRAM_CHAT_ID, "text": text[i:i+4000],
                      "parse_mode": "Markdown"},
                timeout=10,
            )
    except Exception as e:
        print(f"[Telegram] {e}")


def _discord(text: str):
    if not DISCORD_WEBHOOK:
        return
    try:
        # Discord: 2000 char limit per message
        for i in range(0, len(text), 1900):
            requests.post(DISCORD_WEBHOOK,
                          json={"content": text[i:i+1900]},
                          timeout=10)
    except Exception as e:
        print(f"[Discord] {e}")


def _notify(text: str):
    _telegram(text)
    _discord(text)


# ── Decision emoji helpers ────────────────────────────────────────────────────

_DEC_EMOJI = {"ACCUMULATE": "🟢", "WATCH": "🟡", "SKIP": "🔴", "UNKNOWN": "⚪"}
_TIER_EMOJI = {"CORE": "🏛", "SPECULATIVE": "⚡", "CORE+SPEC": "💎", "NONE": ""}


# ── Main report ───────────────────────────────────────────────────────────────

def send_coin_hunter_report(payload: dict):
    """
    Telegram + Discord gزارش Coin Hunter.

    payload keys:
      gems              List[dict]   — کوین‌های پاس‌شده (می‌تونه خالی باشه)
      rejections        Dict[str,int]
      scanned           int
      filter_settings   str
      rejection_summary str
      insight           str          — Self-learning یک‌خطی
    """
    now     = datetime.now().strftime("%Y-%m-%d %H:%M")
    gems    = payload.get("gems", [])
    scanned = payload.get("scanned", 0)
    fs      = payload.get("filter_settings", "")
    rej     = payload.get("rejection_summary", "none")
    insight = payload.get("insight", "")

    # BTC macro trend از اولین gem (همه یکسانه)
    btc_trend = ""
    if gems:
        trend_val = gems[0].get("btc_trend", "")
        avg14d    = gems[0].get("btc_avg14d", 0)
        if trend_val and trend_val != "UNKNOWN":
            trend_emoji = {"ACCUMULATING": "🟢", "NEUTRAL": "🟡",
                           "DISTRIBUTING": "🔴"}.get(trend_val, "⚪")
            btc_trend = f"{trend_emoji} BTC macro: *{trend_val}* ({avg14d:+.0f} BTC/day)"

    lines = [
        f"*🪙 Coin Hunter Bot* — {now}",
        f"_{fs}_",
    ]
    if btc_trend:
        lines.append(btc_trend)
    lines.append("─" * 32)

    # ── Empty result ──────────────────────────────────────────────────────────
    if not gems:
        lines.append(f"*0 coins passed filters*  (scanned {scanned})")
        lines.append(f"_Rejected:_ {rej}")
        if insight:
            lines.append(f"_📊 {insight}_")
        _notify("\n".join(lines))
        return

    # ── Non-empty ─────────────────────────────────────────────────────────────
    acc_coins  = [g for g in gems if g.get("llm_decision") == "ACCUMULATE"]
    watch_coins = [g for g in gems if g.get("llm_decision") == "WATCH"]

    lines.append(f"*Found {len(gems)} qualifying coins*  (scanned {scanned})")
    if acc_coins:
        lines.append(f"🟢 *{len(acc_coins)} ACCUMULATE*  |  🟡 {len(watch_coins)} WATCH")
    lines.append("")

    for g in gems[:10]:
        sym  = g["symbol"]
        name = g["name"][:18]
        dec  = g.get("llm_decision", "UNKNOWN")
        conf = g.get("llm_confidence", "")
        tier = g.get("allocation_tier", "NONE")
        alloc_pct = g.get("allocation_pct", 0.0)
        alloc_usd = g.get("allocation_usd", 0.0)

        exch = "BYBIT" if g.get("on_bybit") else ("BINANCE" if g.get("on_binance") else "—")
        srcs = []
        if g.get("lc_available"):  srcs.append("LC")
        if g.get("cal_available"): srcs.append("CAL")
        if g.get("cq_available"):  srcs.append("CQ")
        tag = f"[{'+'.join(srcs)}]" if srcs else ""

        dec_em  = _DEC_EMOJI.get(dec, "⚪")
        tier_em = _TIER_EMOJI.get(tier, "")

        # Header row
        lines.append(
            f"{dec_em}{tier_em} `{sym}` ({name}) — age `{g['age_days']}d` {tag}"
        )
        # Scores
        lines.append(
            f"   mcap `${g['market_cap']/1e6:.1f}M` | "
            f"surv `{g['survival_score']:.0f}` "
            f"anti `{g['antifragile']:.0f}` "
            f"social `{g.get('social_score',0):.0f}` "
            f"deriv `{g.get('derivs_score',0):.0f}` "
            f"→ `{g['final_score']:.1f}/100`"
        )
        # Exch + DD
        lines.append(
            f"   maxDD `{g['max_dd_pct']:+.0f}%`  "
            f"7d `{g.get('price_7d_pct',0):+.1f}%`  "
            f"30d `{g.get('price_30d_pct',0):+.1f}%`  {exch}"
        )

        # Claude decision
        if dec not in ("UNKNOWN", ""):
            reasoning  = g.get("llm_reasoning", "")
            risk_note  = g.get("llm_risk_note", "")
            conf_label = f"({conf})" if conf else ""
            lines.append(f"   *{dec_em} {dec} {conf_label}*")
            if reasoning:
                lines.append(f"   _{reasoning}_")
            if risk_note:
                lines.append(f"   ⚠️ _{risk_note}_")

        # Allocation / Buy signal
        buy_tier = g.get("buy_tier", "NONE")
        if alloc_pct > 0 and buy_tier != "NONE":
            lines.append(
                f"   💰 *{buy_tier}* — `{alloc_pct:.0f}%` of budget  (${alloc_usd:.0f})"
            )

        lines.append("")   # blank separator

    lines.append(f"_Rejected:_ {rej}")

    if insight:
        lines.append(f"_📊 {insight}_")

    _notify("\n".join(lines))


# ── Generic alerts ────────────────────────────────────────────────────────────

def send_alert(message: str):
    _notify(f"*ALERT* ⚡\n{message}")


def send_error(message: str):
    _notify(f"*ERROR* 🚨\n{message}")
