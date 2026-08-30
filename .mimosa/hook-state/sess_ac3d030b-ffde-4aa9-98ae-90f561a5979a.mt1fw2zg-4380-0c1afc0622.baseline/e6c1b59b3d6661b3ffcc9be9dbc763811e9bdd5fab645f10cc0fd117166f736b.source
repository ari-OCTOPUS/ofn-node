"""
SENTINEL — run_daily.py
اجرای روزانه روی لپ‌تاپ — یک اسکریپت، همه چیز

چه می‌کند:
  ۱. داده‌ی LunarCrush + CryptoQuant را می‌کشد (incremental 7 روز)
  ۲. سیگنال fusion را محاسبه می‌کند (DEPLOY / ACCUMULATE / WAIT / TRAP)
  ۳. گزارش Telegram می‌فرستد
  ۴. همه چیز را در data/ ذخیره می‌کند

نحوه اجرا:
  python run_daily.py            ← اجرای واقعی با API
  python run_daily.py --mock     ← تست بدون API
  python run_daily.py --harvest  ← اولین بار: تاریخچه‌ی کامل ۳۶۵ روز

زمان اجرا: ~۳-۵ دقیقه (rate limited)
"""

import os
import sys
import argparse
import logging
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

# ─── بارگذاری .env ───
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    print("⚠️  فایل .env پیدا نشد!")
    print("    cp .env.template .env")
    print("    سپس API keyها را وارد کن")
    sys.exit(1)

import yaml
sys.path.insert(0, str(Path(__file__).parent))

from lc_client import LunarCrushClient
from cq_client import CryptoQuantClient
from data_store import DataStore
from signal_fusion import SignalFusion
from telegram_signaler import TelegramSignaler

# ─── لاگ ───
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("sentinel_daily.log", encoding="utf-8"),
    ]
)
logger = logging.getLogger("run_daily")

SYMBOLS = ["CORE", "XEL", "XMR", "ZEC", "TAO", "DIL"]

QUADRANT_EMOJI = {
    "DEPLOY":           "🚀",
    "ACCUMULATE":       "⭐",
    "WAIT":             "⏳",
    "TRAP":             "⚠️",
    "NEUTRAL":          "➡️",
    "SOCIAL_ONLY_HOT":  "🔥",
    "SOCIAL_ONLY_QUIET":"😴",
    "MACRO_ONLY_BULL":  "📈",
    "MACRO_ONLY_BEAR":  "📉",
    "UNKNOWN":          "❓",
}

KELLY_BAR = {
    0.0: "░░░░░",
    0.2: "█░░░░",
    0.3: "██░░░",
    0.35:"██░░░",
    0.4: "██░░░",
    0.5: "███░░",
    0.6: "████░",
    0.8: "█████",
}

def kelly_bar(k: float) -> str:
    """نمایش بصری Kelly fraction."""
    nearest = min(KELLY_BAR.keys(), key=lambda x: abs(x - k))
    return KELLY_BAR[nearest]


def build_telegram_report(fusion_results: list, mock_mode: bool) -> str:
    """ساخت پیام Telegram از نتایج fusion."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    mode_tag = " [MOCK]" if mock_mode else ""

    lines = [
        f"📊 <b>SENTINEL — گزارش روزانه{mode_tag}</b>",
        f"🗓️ {now}",
        "",
        "─────────────────────────",
    ]

    for r in fusion_results:
        emoji = QUADRANT_EMOJI.get(r.quadrant, "❓")
        bar = kelly_bar(r.kelly_frac)

        lines.append(f"\n{emoji} <b>{r.symbol}</b>  —  {r.quadrant}")
        lines.append(f"Kelly: {bar} ({r.kelly_frac:.0%})")

        if r.social_signal is not None:
            s_icon = "📣" if r.social_signal > 0.05 else ("🔇" if r.social_signal < -0.05 else "➡️")
            lines.append(f"Social: {s_icon} {r.social_signal:+.2f}")

        if r.macro_regime is not None:
            m_icon = "💹" if r.macro_regime > 0.05 else ("🧊" if r.macro_regime < -0.05 else "➡️")
            lines.append(f"Macro:  {m_icon} {r.macro_regime:+.2f}")
        else:
            lines.append(f"Macro:  ❌ داده ندارد (privacy coin)")

        # conviction text — فقط خط اول
        conviction_first = r.conviction.split("\n")[0] if r.conviction else ""
        if conviction_first:
            lines.append(f"<i>{conviction_first}</i>")

    lines += [
        "",
        "─────────────────────────",
        "",
        "📌 <b>راهنما:</b>",
        "🚀 DEPLOY = بالاترین اطمینان — ورود",
        "⭐ ACCUMULATE = ورود قبل از هایپ",
        "⏳ WAIT = صبر کن",
        "⚠️ TRAP = هایپ بدون پشتوانه — نخر",
        "",
        "<i>ربات فقط سیگنال می‌دهد — خرید دستی است</i>",
        f"🔒 هرگز کلید خصوصی به ربات نده",
    ]

    return "\n".join(lines)


def run(mock_mode: bool = False, data_dir: str = "data", harvest: bool = False):
    """اجرای کامل pipeline روزانه."""

    print()
    print("=" * 55)
    print("  SENTINEL — Daily Run")
    print(f"  {'MOCK MODE' if mock_mode else 'LIVE MODE'}")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 55)

    # ─── check keys ───
    if not mock_mode:
        missing = []
        for key in ["LUNARCRUSH_API_KEY", "CRYPTOQUANT_API_KEY",
                    "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"]:
            if not os.getenv(key):
                missing.append(key)
        if missing:
            print(f"\n❌ API key‌های زیر در .env خالی هستند:")
            for k in missing:
                print(f"   {k}")
            sys.exit(1)

    # ─── clients ───
    lc = LunarCrushClient(
        api_key=os.getenv("LUNARCRUSH_API_KEY", ""),
        mock_mode=mock_mode,
    )
    cq = CryptoQuantClient(
        api_key=os.getenv("CRYPTOQUANT_API_KEY", ""),
        mock_mode=mock_mode,
    )
    ds = DataStore(base_dir=data_dir)
    fusion = SignalFusion(lc, cq)

    # ─── ۱. اگر harvest، تاریخچه کامل بکش ───
    if harvest:
        from harvest import harvest_lunarcrush, harvest_cryptoquant
        print("\n📡 حالت Harvest — تاریخچه‌ی ۳۶۵ روزه...")
        harvest_lunarcrush(lc, ds, days=365)
        harvest_cryptoquant(cq, ds, days=365)
        print("✅ Harvest کامل شد\n")

    # ─── ۲. داده‌ی روزانه (incremental 7 روز) ───
    print("\n[1/3] دریافت داده‌های روزانه...")
    errors = []

    # Universe
    try:
        universe = lc.get_universe(limit=200)
        if universe:
            ds.append_universe(universe)
            print(f"  ✅ Universe: {len(universe)} کوین")
    except Exception as e:
        logger.error(f"Universe: {e}")
        errors.append("universe")

    # LC timeseries
    for sym in SYMBOLS:
        try:
            rows = lc.get_coin_timeseries(sym, days=7)
            if rows:
                ds.append_timeseries(sym, rows)
                print(f"  ✅ LC {sym}: {len(rows)} روز")
        except Exception as e:
            logger.error(f"LC {sym}: {e}")
            errors.append(f"lc_{sym}")

    # CQ flows
    for sym in ["BTC", "ETH"]:
        try:
            rows = cq.get_exchange_flows_timeseries(sym, days=7)
            if rows:
                ds.append_exchange_flows(sym, rows)
            rows = cq.get_whale_ratio_timeseries(sym, days=7)
            if rows:
                ds.append_whale_ratio(sym, rows)
            print(f"  ✅ CQ {sym}: flows + whale")
        except Exception as e:
            logger.error(f"CQ {sym}: {e}")
            errors.append(f"cq_{sym}")

    try:
        miner = cq.get_miner_flows_timeseries(days=7)
        if miner:
            ds.append_miner_flows(miner)
            print(f"  ✅ CQ miner flows: {len(miner)} روز")
    except Exception as e:
        logger.error(f"Miner: {e}")

    try:
        stable = cq.get_stablecoin_flows_timeseries(days=7)
        if stable:
            ds.append_stablecoin_flows(stable)
            print(f"  ✅ CQ stablecoin flows: {len(stable)} روز")
    except Exception as e:
        logger.error(f"Stablecoin: {e}")

    # ─── ۳. محاسبه fusion signals ───
    print("\n[2/3] محاسبه‌ی سیگنال‌ها...")
    fusion_results = fusion.compute_all(SYMBOLS)
    records = fusion.to_records(fusion_results)
    ds.append_signals(records)

    print()
    for r in fusion_results:
        emoji = QUADRANT_EMOJI.get(r.quadrant, "❓")
        bar = kelly_bar(r.kelly_frac)
        print(f"  {emoji}  {r.symbol:<5}  {r.quadrant:<20}  Kelly {bar}  "
              f"social={r.social_signal!s:>6}  macro={r.macro_regime!s:>6}")

    # ─── ۴. ارسال Telegram ───
    print("\n[3/3] ارسال Telegram...")

    cfg_path = Path(__file__).parent / "config.yaml"
    with open(cfg_path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    signaler = TelegramSignaler(cfg)
    message = build_telegram_report(fusion_results, mock_mode)

    if signaler.send(message):
        print("  ✅ پیام Telegram ارسال شد")
    else:
        print("  ❌ ارسال Telegram شکست خورد — لاگ را بررسی کن")
        errors.append("telegram")

    # ─── خلاصه ───
    print()
    print("=" * 55)
    status = "✅ کامل" if not errors else f"⚠️  با {len(errors)} خطا: {errors}"
    print(f"  نتیجه: {status}")
    print(f"  داده در: {data_dir}/")
    print(f"  لاگ:    sentinel_daily.log")
    print("=" * 55)
    print()

    return len(errors) == 0


def main():
    parser = argparse.ArgumentParser(
        description="SENTINEL Daily Run — اجرای روزانه روی لپ‌تاپ"
    )
    parser.add_argument("--mock", action="store_true",
                        help="Mock mode — بدون API واقعی (برای تست)")
    parser.add_argument("--harvest", action="store_true",
                        help="اولین اجرا: تاریخچه‌ی ۳۶۵ روزه بکش")
    parser.add_argument("--data-dir", default="data",
                        help="مسیر ذخیره داده (پیش‌فرض: data/)")
    args = parser.parse_args()

    mock = args.mock or bool(os.getenv("SENTINEL_MOCK_MODE"))
    success = run(
        mock_mode=mock,
        data_dir=os.getenv("SENTINEL_DATA_DIR", args.data_dir),
        harvest=args.harvest,
    )
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
