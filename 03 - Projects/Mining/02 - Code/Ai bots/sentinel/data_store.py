"""
SENTINEL — data_store.py
ذخیره‌سازی Parquet append-only

قانون اصلی: هیچ‌وقت overwrite نکن — همیشه append با timestamp.
ساختار:
  data/
  ├── lunarcrush/
  │   ├── universe_YYYYMMDD.parquet
  │   ├── ts/{symbol}_daily.parquet
  │   └── sectors_daily.parquet
  ├── cryptoquant/
  │   ├── btc_exchange_flows.parquet
  │   ├── btc_whale_ratio.parquet
  │   ├── btc_miner_flows.parquet
  │   └── stablecoin_flows.parquet
  └── merged/
      └── regime_and_signals.parquet

نحوه استفاده:
  from data_store import DataStore
  ds = DataStore(base_dir="data")
  ds.append_universe(rows)             # لیست دیکشنری
  ds.append_timeseries("CORE", rows)
  df = ds.read("lunarcrush/ts/CORE_daily.parquet")
"""

import os
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

import pandas as pd

logger = logging.getLogger(__name__)


class DataStore:
    """
    مدیریت ذخیره‌ی Parquet با قانون append-only.
    """

    def __init__(self, base_dir: str = "data"):
        self.base = Path(base_dir)
        self._init_dirs()

    def _init_dirs(self):
        for sub in ["lunarcrush/ts", "cryptoquant", "merged"]:
            (self.base / sub).mkdir(parents=True, exist_ok=True)

    # ─── helper ───────────────────────────────────────────

    def _path(self, relative: str) -> Path:
        return self.base / relative

    def _now_ts(self) -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def _append_parquet(self, path: Path, rows: List[dict], tag: str = "") -> bool:
        """
        append لیست دیکشنری به فایل Parquet.
        اگر فایل نبود می‌سازد. اگر بود، خواند + concat + نوشت.
        """
        if not rows:
            logger.warning(f"append_parquet: rows خالی برای {path}")
            return False

        new_df = pd.DataFrame(rows)
        new_df["_inserted_at"] = self._now_ts()

        if path.exists():
            try:
                existing = pd.read_parquet(path)
                # جلوگیری از ورودی‌های تکراری بر اساس timestamp اگر وجود داشت
                if "timestamp" in existing.columns and "timestamp" in new_df.columns:
                    existing_ts = set(existing["timestamp"].astype(str))
                    new_df = new_df[~new_df["timestamp"].astype(str).isin(existing_ts)]
                    if new_df.empty:
                        logger.info(f"{path.name}: همه ردیف‌ها تکراری — skip")
                        return True
                combined = pd.concat([existing, new_df], ignore_index=True)
            except Exception as e:
                logger.error(f"خواندن {path} شکست خورد: {e} — جایگزین می‌کنیم")
                combined = new_df
        else:
            combined = new_df

        combined.to_parquet(path, index=False)
        logger.info(f"{'✅' if tag else ''} {path.name}: {len(new_df)} ردیف جدید → جمع {len(combined)}")
        return True

    # ─── LunarCrush ───────────────────────────────────────

    def append_universe(self, rows: List[dict]) -> bool:
        """
        snapshot روزانه‌ی universe — با تاریخ در نام فایل.
        هر روز یک فایل جداگانه (نه overwrite).
        """
        today = datetime.now(timezone.utc).strftime("%Y%m%d")
        path = self._path(f"lunarcrush/universe_{today}.parquet")
        if path.exists():
            logger.info(f"universe_{today}.parquet قبلاً ذخیره شده — skip")
            return True
        return self._append_parquet(path, rows, tag="🌙")

    def append_timeseries(self, symbol: str, rows: List[dict]) -> bool:
        """
        تاریخچه‌ی روزانه‌ی یک کوین — به فایل {SYMBOL}_daily.parquet اضافه می‌شود.
        """
        path = self._path(f"lunarcrush/ts/{symbol.upper()}_daily.parquet")
        return self._append_parquet(path, rows, tag="📈")

    def append_sectors(self, rows: List[dict]) -> bool:
        """مومنتوم سکتورها — یک فایل، append روزانه."""
        path = self._path("lunarcrush/sectors_daily.parquet")
        return self._append_parquet(path, rows, tag="🏷️")

    # ─── CryptoQuant ──────────────────────────────────────

    def append_exchange_flows(self, symbol: str, rows: List[dict]) -> bool:
        """جریان exchange برای BTC یا ETH."""
        sym = symbol.upper()
        path = self._path(f"cryptoquant/{sym.lower()}_exchange_flows.parquet")
        return self._append_parquet(path, rows, tag="💰")

    def append_whale_ratio(self, symbol: str, rows: List[dict]) -> bool:
        """نسبت تراکنش نهنگ‌ها."""
        path = self._path(f"cryptoquant/{symbol.lower()}_whale_ratio.parquet")
        return self._append_parquet(path, rows, tag="🐋")

    def append_miner_flows(self, rows: List[dict]) -> bool:
        """جریان ماینرها — فقط BTC."""
        path = self._path("cryptoquant/btc_miner_flows.parquet")
        return self._append_parquet(path, rows, tag="⛏️")

    def append_stablecoin_flows(self, rows: List[dict]) -> bool:
        """جریان stablecoin ها."""
        path = self._path("cryptoquant/stablecoin_flows.parquet")
        return self._append_parquet(path, rows, tag="🏦")

    # ─── Merged / Fusion ──────────────────────────────────

    def append_signals(self, rows: List[dict]) -> bool:
        """
        سیگنال‌های fusion محاسبه‌شده (social_signal + macro_regime + quadrant).
        این فایل را SENTINEL می‌خواند به‌جای تماس مستقیم با API.
        """
        path = self._path("merged/regime_and_signals.parquet")
        return self._append_parquet(path, rows, tag="🔮")

    # ─── خواندن ───────────────────────────────────────────

    def read(self, relative: str,
             since_days: int = None) -> Optional[pd.DataFrame]:
        """
        خواندن یک فایل Parquet.
        since_days: اگر داده‌شود، فقط N روز اخیر را برمی‌گرداند.
        """
        path = self._path(relative)
        if not path.exists():
            return None
        try:
            df = pd.read_parquet(path)
            if since_days and "timestamp" in df.columns:
                cutoff = (datetime.now(timezone.utc).timestamp() - since_days * 86400)
                df["_ts_num"] = pd.to_numeric(df["timestamp"], errors="coerce")
                df = df[df["_ts_num"] >= cutoff].drop(columns=["_ts_num"])
            return df
        except Exception as e:
            logger.error(f"خواندن {path} شکست خورد: {e}")
            return None

    def latest_signal(self, symbol: str) -> Optional[dict]:
        """
        آخرین سطر سیگنال fusion برای یک symbol.
        این همان چیزی است که data_fetcher از آن می‌خواند.
        """
        df = self.read("merged/regime_and_signals.parquet")
        if df is None or df.empty:
            return None
        if "symbol" in df.columns:
            df = df[df["symbol"] == symbol]
        if df.empty:
            return None
        # مرتب بر اساس timestamp اگر وجود داشت
        if "timestamp" in df.columns:
            df = df.sort_values("timestamp")
        return df.iloc[-1].to_dict()

    def get_stats(self) -> dict:
        """گزارش وضعیت همه فایل‌ها — برای داشبورد."""
        stats = {}
        for p in sorted(self.base.rglob("*.parquet")):
            try:
                df = pd.read_parquet(p)
                stats[str(p.relative_to(self.base))] = {
                    "rows": len(df),
                    "size_kb": round(p.stat().st_size / 1024, 1),
                    "columns": list(df.columns),
                }
            except Exception:
                stats[str(p.relative_to(self.base))] = {"error": "خواندن شکست خورد"}
        return stats
