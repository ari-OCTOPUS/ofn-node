"""
SENTINEL — data_pipeline.py
اجرای روزانه‌ی pipeline — جمع‌آوری + محاسبه‌ی fusion + ذخیره

این اسکریپت را با cron یا systemd timer روی Pi یک بار در روز (مثلاً ۰۱:۰۰) اجرا کن.
زمان اجرا: ~۳-۵ دقیقه (rate-limited)

نحوه اجرا:
  python3 data_pipeline.py          # یک چرخه
  SENTINEL_MOCK_MODE=1 python3 data_pipeline.py  # mock

برای systemd (اضافه به deploy.sh):
  OnCalendar=*-*-* 01:00:00
  ExecStart=/home/sentinel/sentinel/venv/bin/python3 data_pipeline.py
"""

import os
import sys
import logging
from datetime import datetime, timezone
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))
from lc_client import LunarCrushClient
from cq_client import CryptoQuantClient
from data_store import DataStore
from signal_fusion import SignalFusion
from sector_scanner import SectorScanner

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("data_pipeline.log", encoding="utf-8"),
    ]
)
logger = logging.getLogger("data_pipeline")

# نسخه ۲.۰ — BTC/ETH با CORE/XEL/TAO/DIL جایگزین شدند
# MEMECOIN از لیست خارج است — ماهانه تغییر می‌کند، دستی مدیریت می‌شود
# CryptoQuant onchain فقط BTC/ETH — بخش‌های ۳ و ۴ برای macro context ثابت ماندند
SYMBOLS = ["CORE", "XEL", "XMR", "ZEC", "TAO", "DIL"]


def run_pipeline(cfg: dict, data_dir: str = "data") -> bool:
    mock_mode = bool(os.getenv("SENTINEL_MOCK_MODE"))

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

    logger.info("=" * 50)
    logger.info(f"Pipeline شروع شد | mock={mock_mode}")
    logger.info("=" * 50)

    errors = []

    # ─── ۱. Universe snapshot روزانه ───
    try:
        universe = lc.get_universe(limit=300)
        if universe:
            ds.append_universe(universe)
            logger.info(f"Universe: {len(universe)} کوین")
    except Exception as e:
        logger.error(f"Universe snapshot شکست خورد: {e}")
        errors.append("universe")

    # ─── ۲. Time-series هر سمبل (۷ روز اخیر — incremental) ───
    for sym in SYMBOLS:
        try:
            rows = lc.get_coin_timeseries(sym, days=7)
            if rows:
                ds.append_timeseries(sym, rows)
                logger.info(f"LC timeseries {sym}: {len(rows)} روز")
        except Exception as e:
            logger.error(f"LC timeseries {sym} شکست: {e}")
            errors.append(f"lc_ts_{sym}")

    # ─── ۳. Exchange flows (incremental ۷ روز) ───
    for sym in ["BTC", "ETH"]:
        try:
            rows = cq.get_exchange_flows_timeseries(sym, days=7)
            if rows:
                ds.append_exchange_flows(sym, rows)
                logger.info(f"CQ exchange_flows {sym}: {len(rows)} روز")
        except Exception as e:
            logger.error(f"CQ flows {sym} شکست: {e}")
            errors.append(f"cq_flows_{sym}")

    # ─── ۴. Whale + Miner + Stablecoin (هر بار fresh) ───
    try:
        for sym in ["BTC", "ETH"]:
            rows = cq.get_whale_ratio_timeseries(sym, days=7)
            if rows:
                ds.append_whale_ratio(sym, rows)
    except Exception as e:
        logger.error(f"Whale ratio شکست: {e}")

    try:
        miner = cq.get_miner_flows_timeseries(days=7)
        if miner:
            ds.append_miner_flows(miner)
    except Exception as e:
        logger.error(f"Miner flows شکست: {e}")

    try:
        stable = cq.get_stablecoin_flows_timeseries(days=7)
        if stable:
            ds.append_stablecoin_flows(stable)
    except Exception as e:
        logger.error(f"Stablecoin flows شکست: {e}")

    # ─── ۵. محاسبه fusion signals ───
    logger.info("محاسبه‌ی fusion signals...")
    fusion_results = fusion.compute_all(SYMBOLS)
    records = fusion.to_records(fusion_results)
    ds.append_signals(records)

    for r in fusion_results:
        logger.info(
            f"  {r.symbol}: {r.quadrant} | "
            f"social={r.social_signal} | macro={r.macro_regime} | "
            f"kelly={r.kelly_frac:.1f} | modifier={r.score_modifier:+.1f}"
        )

    # ─── ۶. Sector Scan ───
    try:
        scanner = SectorScanner(cfg, lc, cq, ds)
        sector_results = scanner.scan_all()
        if sector_results:
            sector_records = SectorScanner.to_records(sector_results)
            ds.append_signals(sector_records)          # در sector_signals.parquet ذخیره می‌شود
            logger.info(f"Sector scan: {len(sector_results)} نتیجه ذخیره شد")
        else:
            logger.info("Sector scan: هیچ کوینی در sectors تعریف نشده — skip")
    except Exception as e:
        logger.error(f"Sector scan شکست خورد: {e}")
        errors.append("sector_scan")

    # ─── ۷. خلاصه ───
    ok = len(errors) == 0
    status = "✅ کامل" if ok else f"⚠️ با {len(errors)} خطا"
    logger.info(f"\nPipeline {status} | {datetime.now(timezone.utc).isoformat()}")

    if errors:
        logger.warning(f"خطاهای pipeline: {errors}")

    return ok


def main():
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    data_dir = os.getenv("SENTINEL_DATA_DIR", "data")
    success = run_pipeline(cfg, data_dir=data_dir)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
