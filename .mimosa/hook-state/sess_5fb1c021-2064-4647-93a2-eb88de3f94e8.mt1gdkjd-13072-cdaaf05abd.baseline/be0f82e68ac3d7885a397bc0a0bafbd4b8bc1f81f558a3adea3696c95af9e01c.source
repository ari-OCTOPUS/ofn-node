"""
SENTINEL — harvest.py
کشیدن کامل تاریخچه قبل از مرگ اشتراک

⚠️  این اسکریپت را فقط یک بار اجرا کن (یا هر بار که اشتراکت تمدید شد).
⚠️  CoinGecko را هم در یک پنجره موازی اجرا کن تا همه تاریخچه‌ها داشته باشی.

چه می‌کند:
  1. LunarCrush time-series همه کاندیدها (تا ۳۶۵ روز)
  2. LunarCrush universe snapshot امروز
  3. LunarCrush topics: bitcoin, privacy, defi, ai-agents
  4. CryptoQuant exchange_flows BTC + ETH (تا ۳۶۵ روز)
  5. CryptoQuant whale_ratio BTC + ETH
  6. CryptoQuant miner_flows BTC
  7. CryptoQuant stablecoin_flows

نحوه اجرا:
  # روی Pi با اینترنت واقعی:
  python3 harvest.py

  # تست بدون API (داده مصنوعی):
  SENTINEL_MOCK_MODE=1 python3 harvest.py --days 90
"""

import os
import sys
import time
import argparse
import logging
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))
from lc_client import LunarCrushClient
from cq_client import CryptoQuantClient
from data_store import DataStore

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("harvest")

# ─── کاندیدهای SENTINEL + موضوعات اضافی برای context ───
LC_SYMBOLS  = ["CORE", "XEL", "XMR", "ZEC", "TAO", "DIL"]
LC_TOPICS   = ["coredao", "monero", "privacy-coins", "bittensor", "ai-agents"]
# CryptoQuant فقط BTC/ETH را پشتیبانی می‌کند — macro context فقط
CQ_SYMBOLS  = ["BTC", "ETH"]


def harvest_lunarcrush(lc: LunarCrushClient, ds: DataStore, days: int):
    print("\n" + "═"*55)
    print("  📡 LunarCrush — شروع harvest")
    print("═"*55)

    # ─── Universe snapshot ───
    print("\n[LC-1] Universe snapshot...")
    universe = lc.get_universe(limit=300)
    if universe:
        ds.append_universe(universe)
        print(f"  ✅ {len(universe)} کوین ذخیره شد")
    else:
        print("  ⚠️  Universe خالی بود")

    # ─── Time-series هر سمبل ───
    for sym in LC_SYMBOLS:
        print(f"\n[LC-2] Time-series {sym} ({days} روز)...")
        rows = lc.get_coin_timeseries(sym, days=days)
        if rows:
            ds.append_timeseries(sym, rows)
            print(f"  ✅ {len(rows)} روز ذخیره شد")
        else:
            print(f"  ⚠️  داده‌ای برای {sym} نیامد")

        # Rate limiter بین کوین‌ها (در live mode)
        if not lc.mock_mode:
            time.sleep(7)

    # ─── Sectors ───
    print("\n[LC-3] Sectors...")
    sectors = lc.get_sectors()
    if sectors:
        ds.append_sectors(sectors)
        print(f"  ✅ {len(sectors)} سکتور ذخیره شد")

    # ─── Topics ───
    for topic in LC_TOPICS:
        print(f"\n[LC-4] Topic: {topic}...")
        ts = lc.get_topic_timeseries(topic, days=min(days, 90))
        if ts:
            # Topics رو به‌عنوان sectors ذخیره می‌کنیم با symbol = topic
            for row in ts:
                row["topic"] = topic
            ds.append_sectors(ts)
            print(f"  ✅ {len(ts)} روز topic data ذخیره شد")

        if not lc.mock_mode:
            time.sleep(7)


def harvest_cryptoquant(cq: CryptoQuantClient, ds: DataStore, days: int):
    print("\n" + "═"*55)
    print("  📡 CryptoQuant — شروع harvest")
    print("═"*55)

    # ─── Exchange Flows ───
    for sym in CQ_SYMBOLS:
        print(f"\n[CQ-1] Exchange flows {sym} ({days} روز)...")
        rows = cq.get_exchange_flows_timeseries(sym, days=days)
        if rows:
            ds.append_exchange_flows(sym, rows)
            print(f"  ✅ {len(rows)} روز ذخیره شد")
        else:
            print(f"  ⚠️  داده‌ای برای {sym} نیامد")

        if not cq.mock_mode:
            time.sleep(2)

    # ─── Whale Ratio ───
    for sym in CQ_SYMBOLS:
        print(f"\n[CQ-2] Whale ratio {sym} ({days} روز)...")
        rows = cq.get_whale_ratio_timeseries(sym, days=days)
        if rows:
            ds.append_whale_ratio(sym, rows)
            print(f"  ✅ {len(rows)} روز ذخیره شد")

        if not cq.mock_mode:
            time.sleep(2)

    # ─── Miner Flows (فقط BTC) ───
    print(f"\n[CQ-3] Miner flows BTC ({days} روز)...")
    miner_rows = cq.get_miner_flows_timeseries(days=days)
    if miner_rows:
        ds.append_miner_flows(miner_rows)
        print(f"  ✅ {len(miner_rows)} روز ذخیره شد")

    # ─── Stablecoin Flows ───
    print(f"\n[CQ-4] Stablecoin flows ({days} روز)...")
    stable_rows = cq.get_stablecoin_flows_timeseries(days=days)
    if stable_rows:
        ds.append_stablecoin_flows(stable_rows)
        print(f"  ✅ {len(stable_rows)} روز ذخیره شد")


def print_summary(ds: DataStore):
    print("\n" + "═"*55)
    print("  📊 خلاصه‌ی فایل‌های ذخیره‌شده")
    print("═"*55)
    stats = ds.get_stats()
    if not stats:
        print("  هیچ فایلی پیدا نشد")
        return
    for path, info in stats.items():
        if "error" in info:
            print(f"  ❌ {path}: {info['error']}")
        else:
            print(f"  ✅ {path}: {info['rows']} ردیف · {info['size_kb']} KB")


def main():
    parser = argparse.ArgumentParser(
        description="SENTINEL harvest — کشیدن تاریخچه‌ی کامل قبل از مرگ اشتراک"
    )
    parser.add_argument("--days", type=int, default=365,
                        help="تعداد روزهای تاریخچه (پیش‌فرض: ۳۶۵)")
    parser.add_argument("--data-dir", default="data",
                        help="مسیر ذخیره‌ی فایل‌های Parquet")
    parser.add_argument("--lc-only", action="store_true",
                        help="فقط LunarCrush")
    parser.add_argument("--cq-only", action="store_true",
                        help="فقط CryptoQuant")
    args = parser.parse_args()

    # ─── Config ───
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    mock_mode = bool(os.getenv("SENTINEL_MOCK_MODE"))

    lc = LunarCrushClient(
        api_key=os.getenv("LUNARCRUSH_API_KEY", ""),
        mock_mode=mock_mode,
    )
    cq = CryptoQuantClient(
        api_key=os.getenv("CRYPTOQUANT_API_KEY", ""),
        mock_mode=mock_mode,
    )
    ds = DataStore(base_dir=args.data_dir)

    print("\n" + "═"*55)
    print("  SENTINEL — Harvest")
    print(f"  روزها: {args.days} · Mock: {mock_mode}")
    print(f"  ذخیره در: {args.data_dir}/")
    print("═"*55)

    if mock_mode:
        print("  ⚠️  MOCK MODE — داده واقعی کشیده نمی‌شود")
    else:
        print("  🔴 LIVE MODE — API واقعی")

    if not args.cq_only:
        harvest_lunarcrush(lc, ds, args.days)

    if not args.lc_only:
        harvest_cryptoquant(cq, ds, args.days)

    print_summary(ds)

    print("\n" + "═"*55)
    print("  ✅ Harvest کامل شد!")
    print("  فایل‌ها در: " + args.data_dir + "/")
    print("  بعدی: python3 data_pipeline.py  (اجرای روزانه)")
    print("═"*55 + "\n")


if __name__ == "__main__":
    main()
