"""
SENTINEL — lc_client.py
کلاینت کامل LunarCrush با rate-limiter و mock mode

پوشش endpoint ها:
  - coins/list         : universe snapshot (همه کوین‌ها)
  - coins/{coin}       : جزئیات یک کوین
  - coins/{coin}/time-series : تاریخچه‌ی روزانه
  - topic/{topic}      : snapshot یک موضوع
  - topic/{topic}/time-series: تاریخچه‌ی موضوع
  - creators/list      : لیست کریتورها
  - categories/list    : سکتورها (pow, ai-agents, depin, ...)

محدودیت: Individual plan ≈ ۱۰ req/min → ۶.۵ ثانیه بین درخواست‌ها

نحوه استفاده:
  from lc_client import LunarCrushClient
  lc = LunarCrushClient(api_key="YOUR_KEY")
  snap = lc.get_coin("CORE")
  ts   = lc.get_coin_timeseries("CORE", days=180)
"""

import os
import time
import logging
from typing import Optional, List, Dict, Any

import requests

logger = logging.getLogger(__name__)

# ─── Mock fixtures (mock_mode=True) ───────────────────────
MOCK_COIN = {
    "CORE": {
        "symbol": "CORE", "name": "CoreDAO",
        "price": 0.85, "market_cap": 800_000_000,
        "galaxy_score": 52, "alt_rank": 45,
        "social_score": 2200, "social_volume_24h": 22000,
        "sentiment": 0.48, "bullish_pct": 51,
        "spam_pct": 3,
        "creator_count_24h": 180, "creator_growth_7d": 0.06,
        "interactions_24h": 95000,
    },
    "XEL": {
        "symbol": "XEL", "name": "Xelis",
        "price": 0.012, "market_cap": 15_000_000,
        "galaxy_score": 32, "alt_rank": 420,
        "social_score": 350, "social_volume_24h": 1200,
        "sentiment": 0.55, "bullish_pct": 60,
        "spam_pct": 2,
        "creator_count_24h": 12, "creator_growth_7d": 0.12,
        "interactions_24h": 3200,
    },
    "TAO": {
        "symbol": "TAO", "name": "Bittensor",
        "price": 380, "market_cap": 4_000_000_000,
        "galaxy_score": 58, "alt_rank": 18,
        "social_score": 3100, "social_volume_24h": 38000,
        "sentiment": 0.62, "bullish_pct": 65,
        "spam_pct": 5,
        "creator_count_24h": 420, "creator_growth_7d": 0.09,
        "interactions_24h": 210000,
    },
    "DIL": {
        "symbol": "DIL", "name": "Dilithion",
        "price": 0.003, "market_cap": 5_000_000,
        "galaxy_score": 22, "alt_rank": 890,
        "social_score": 120, "social_volume_24h": 300,
        "sentiment": 0.50, "bullish_pct": 52,
        "spam_pct": 1,
        "creator_count_24h": 5, "creator_growth_7d": 0.03,
        "interactions_24h": 800,
    },
    "XMR": {
        "symbol": "XMR", "name": "Monero",
        "price": 192, "market_cap": 3_500_000_000,
        "galaxy_score": 51, "alt_rank": 28,
        "social_score": 320, "social_volume_24h": 12000,
        "sentiment": 0.44, "bullish_pct": 47,
        "spam_pct": 3,
        "creator_count_24h": 85, "creator_growth_7d": -0.02,
        "interactions_24h": 28000,
    },
    "ZEC": {
        "symbol": "ZEC", "name": "Zcash",
        "price": 32, "market_cap": 510_000_000,
        "galaxy_score": 44, "alt_rank": 65,
        "social_score": 110, "social_volume_24h": 3800,
        "sentiment": 0.38, "bullish_pct": 41,
        "spam_pct": 6,
        "creator_count_24h": 22, "creator_growth_7d": -0.05,
        "interactions_24h": 7200,
    },
}

MOCK_SECTORS = [
    {"name": "pow", "coins": ["XMR", "ZEC", "XEL"], "sentiment_avg": 0.46, "galaxy_avg": 48},
    {"name": "privacy", "coins": ["XMR", "ZEC", "XEL"], "sentiment_avg": 0.42, "galaxy_avg": 47},
    {"name": "ai-agents", "coins": ["TAO"], "sentiment_avg": 0.70, "galaxy_avg": 72},
    {"name": "depin", "coins": ["CORE"], "sentiment_avg": 0.52, "galaxy_avg": 55},
]


class LunarCrushClient:
    """
    کلاینت کامل LunarCrush با rate-limiting خودکار.
    mock_mode=True → داده‌ی fixture برمی‌گرداند بدون هیچ درخواست شبکه‌ای.
    """

    BASE_URL = "https://lunarcrush.com/api4/public"
    MIN_INTERVAL = 6.5  # ثانیه بین درخواست‌ها (۱۰ req/min با margin)

    def __init__(self, api_key: str = "", mock_mode: bool = False):
        self.api_key = api_key or os.getenv("LUNARCRUSH_API_KEY", "")
        self.mock_mode = mock_mode or bool(os.getenv("SENTINEL_MOCK_MODE"))
        self._last_call = 0.0
        self._session = requests.Session()
        if self.api_key:
            self._session.headers.update({"Authorization": f"Bearer {self.api_key}"})

    # ─── Rate limiter ──────────────────────────────────────

    def _throttle(self):
        elapsed = time.time() - self._last_call
        if elapsed < self.MIN_INTERVAL:
            time.sleep(self.MIN_INTERVAL - elapsed)
        self._last_call = time.time()

    def _get(self, path: str, params: dict = None) -> Optional[dict]:
        if self.mock_mode:
            return None  # caller substitutes mock data
        self._throttle()
        url = f"{self.BASE_URL}/{path}"
        try:
            resp = self._session.get(url, params=params or {}, timeout=15)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                logger.warning("LunarCrush rate limit hit — sleeping 60s")
                time.sleep(60)
            else:
                logger.error(f"LunarCrush HTTP error {e.response.status_code}: {path}")
            return None
        except Exception as e:
            logger.error(f"LunarCrush request failed: {e}")
            return None

    # ─── Universe snapshot ─────────────────────────────────

    def get_universe(self, limit: int = 300) -> List[dict]:
        """
        کل لیست کوین‌ها با همه متریک‌ها (snapshot لحظه‌ای).
        برای ذخیره‌ی روزانه — هیچ‌وقت overwrite نکن.
        """
        if self.mock_mode:
            return list(MOCK_COIN.values())

        data = self._get("coins/list", params={"sort": "galaxy_score", "limit": limit})
        if not data:
            return []
        return data.get("data", [])

    # ─── جزئیات یک کوین ───────────────────────────────────

    def get_coin(self, symbol: str) -> Optional[dict]:
        """
        snapshot کامل یک کوین — galaxy_score، sentiment، creators، spam.
        """
        if self.mock_mode:
            return MOCK_COIN.get(symbol)

        data = self._get(f"coins/{symbol.lower()}/v1")
        if not data:
            return None
        return data.get("data")

    # ─── Time-series تاریخی ───────────────────────────────

    def get_coin_timeseries(self, symbol: str, days: int = 180) -> List[dict]:
        """
        تاریخچه‌ی روزانه‌ی یک کوین.
        **بحرانی:** این دیتا بعد از انقضا اشتراک از دست می‌رود — باید بکشی و ذخیره کنی.

        برمی‌گرداند: لیستی از dict با کلیدهای
          timestamp, price, galaxy_score, alt_rank, social_score,
          sentiment, social_volume_24h, interactions_24h
        """
        if self.mock_mode:
            import random
            random.seed(hash(symbol))
            base = MOCK_COIN.get(symbol, {})
            rows = []
            now = int(time.time())
            p = base.get("price", 100)
            for i in range(days, 0, -1):
                p *= (1 + random.gauss(0, 0.025))
                rows.append({
                    "timestamp": now - i * 86400,
                    "price": round(p, 4),
                    "galaxy_score": max(10, min(100, base.get("galaxy_score", 50) + random.gauss(0, 5))),
                    "alt_rank": max(1, base.get("alt_rank", 10) + random.randint(-5, 5)),
                    "social_score": max(0, base.get("social_score", 100) * random.uniform(0.7, 1.3)),
                    "sentiment": max(0.1, min(0.9, base.get("sentiment", 0.5) + random.gauss(0, 0.08))),
                    "social_volume_24h": max(0, int(base.get("social_volume_24h", 1000) * random.uniform(0.5, 1.8))),
                    "interactions_24h": max(0, int(base.get("interactions_24h", 5000) * random.uniform(0.4, 2.0))),
                    "creator_count_24h": max(0, int(base.get("creator_count_24h", 50) * random.uniform(0.6, 1.5))),
                    "spam_pct": max(0, min(50, base.get("spam_pct", 5) + random.gauss(0, 2))),
                })
            return rows

        # interval=day برای تاریخچه‌ی روزانه
        bucket = days * 86400
        data = self._get(
            f"coins/{symbol.lower()}/time-series/v2",
            params={"bucket": "day", "interval": f"{days}d"},
        )
        if not data:
            return []
        return data.get("data", [])

    # ─── Topics (روایت‌ها / Narratives) ───────────────────

    def get_topic(self, topic: str) -> Optional[dict]:
        """
        snapshot کامل یک topic (مثل "bitcoin", "defi", "ai-agents").
        """
        if self.mock_mode:
            return {
                "topic": topic,
                "interactions_24h": 1200000,
                "social_volume_24h": 85000,
                "sentiment": 0.55,
                "galaxy_score": 62,
                "num_coins": 12,
            }
        data = self._get(f"topic/{topic}/v1")
        if not data:
            return None
        return data.get("data")

    def get_topic_timeseries(self, topic: str, days: int = 90) -> List[dict]:
        """تاریخچه‌ی روزانه‌ی یک topic — برای narrative momentum."""
        if self.mock_mode:
            import random
            random.seed(hash(topic))
            rows = []
            now = int(time.time())
            for i in range(days, 0, -1):
                rows.append({
                    "timestamp": now - i * 86400,
                    "sentiment": max(0.1, min(0.9, 0.5 + random.gauss(0, 0.1))),
                    "social_volume_24h": max(0, int(50000 * random.uniform(0.5, 2.0))),
                    "interactions_24h": max(0, int(800000 * random.uniform(0.4, 2.5))),
                    "galaxy_score": max(20, min(100, 55 + random.gauss(0, 8))),
                })
            return rows

        data = self._get(f"topic/{topic}/time-series/v2",
                         params={"bucket": "day", "interval": f"{days}d"})
        if not data:
            return []
        return data.get("data", [])

    # ─── Sectors / Categories ──────────────────────────────

    def get_sectors(self) -> List[dict]:
        """
        همه سکتورها با مومنتوم — کدام روایت داغ می‌شود؟
        """
        if self.mock_mode:
            return MOCK_SECTORS

        data = self._get("categories/list/v1")
        if not data:
            return []
        return data.get("data", [])

    # ─── Creators ─────────────────────────────────────────

    def get_top_creators(self, symbol: str, limit: int = 20) -> List[dict]:
        """
        کریتورهای برتر یک کوین — برای فیلتر spam و بررسی کیفیت.
        نرخ رشد کریتورها (creator_growth) سیگنال اصلی است، نه فقط تعداد.
        """
        if self.mock_mode:
            return [
                {"username": f"user_{i}", "followers": 10000 - i * 300,
                 "interactions_24h": 5000 - i * 200, "is_verified": i < 3,
                 "sentiment": 0.5 + (i % 3 - 1) * 0.15}
                for i in range(min(limit, 10))
            ]

        data = self._get(f"coins/{symbol.lower()}/creators/v1",
                         params={"limit": limit})
        if not data:
            return []
        return data.get("data", [])

    # ─── سیگنال ترکیبی (social_signal) ───────────────────

    def compute_social_signal(self, symbol: str) -> Optional[float]:
        """
        social_signal ∈ [-1, +1]

        فرمول:
          raw = 0.40 * norm(galaxy_score, 0, 100)
              + 0.30 * (sentiment - 0.5) * 2          # -1..+1
              + 0.20 * (1 - spam_pct/50)              # spam penalty
              + 0.10 * clamp(creator_growth_7d, -0.2, 0.2) / 0.2

        برای SENTINEL scoring این عدد جایگزین social_score خام می‌شود.
        """
        coin = self.get_coin(symbol)
        if not coin:
            return None

        gs   = coin.get("galaxy_score", 50) / 100.0          # 0..1
        sent = (coin.get("sentiment", 0.5) - 0.5) * 2        # -1..+1
        spam = 1 - min(coin.get("spam_pct", 5), 50) / 50.0   # 0..1 (کمتر spam = بهتر)
        grow = coin.get("creator_growth_7d", 0)
        grow_norm = max(-1.0, min(1.0, grow / 0.2))           # -1..+1

        raw = 0.40 * gs + 0.30 * sent + 0.20 * spam + 0.10 * grow_norm

        # نرمال‌سازی به [-1, +1]
        # gs در [0..1] → raw range ≈ [−0.5, +1.0]
        # shift و scale می‌کنیم
        signal = max(-1.0, min(1.0, raw * 2 - 0.5))
        return round(signal, 4)
