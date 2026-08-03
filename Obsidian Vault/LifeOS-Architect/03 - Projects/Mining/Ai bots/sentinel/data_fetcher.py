"""
SENTINEL — data_fetcher.py
Data fetching layer with fallback, cache, and graceful degradation.
لایه دریافت داده با fallback، کش، و تحمل خطای API.

Sources / منابع:
  CoinGecko   — price, 24h change, 90-day history (free, always-on backbone)
  LunarCrush  — social sentiment, galaxy score, alt-rank
  CryptoQuant — on-chain: exchange flows, miner flows, NVT (BTC/ETH only)
  alternative.me — Fear & Greed index (free)

MOCK MODE (SENTINEL_MOCK_MODE=1):
  Returns deterministic fixture data so the entire codebase can be
  built, tested, and backtested without live API keys.
  یک حالت آفلاین که بدون کلید API واقعی کار می‌کند.
"""

import os
import time
import json
import logging
import requests
from datetime import datetime
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# MOCK FIXTURES — داده‌های ثابت برای حالت آفلاین
# These represent a realistic "mid-bear" snapshot so scorers can be tested.
# این داده‌ها یک وضعیت واقع‌بینانه‌ی "میانه‌ی بازار نزولی" را شبیه‌سازی می‌کنند.
# ─────────────────────────────────────────────
MOCK_PRICE = {
    "CORE": {"price": 0.85,  "change_24h": -2.1, "high_90d": 1.40,
             "low_90d": 0.55, "drawdown_from_90d_high": 0.393,
             "ma50": 0.95, "ma200": 0.78,
             "source": "mock", "timestamp": "2026-05-22T10:00:00"},
    "XEL":  {"price": 0.012, "change_24h": -3.5, "high_90d": 0.025,
             "low_90d": 0.007, "drawdown_from_90d_high": 0.520,
             "ma50": 0.015, "ma200": None,
             "source": "mock", "timestamp": "2026-05-22T10:00:00"},
    "XMR":  {"price": 192,   "change_24h": -6.1, "high_90d": 320,
             "low_90d": 148, "drawdown_from_90d_high": 0.400,
             "ma50": 215, "ma200": 185,
             "source": "mock", "timestamp": "2026-05-22T10:00:00"},
    "ZEC":  {"price": 32,    "change_24h": -5.5, "high_90d": 60,
             "low_90d": 22, "drawdown_from_90d_high": 0.467,
             "ma50": 40, "ma200": 35,
             "source": "mock", "timestamp": "2026-05-22T10:00:00"},
    "TAO":  {"price": 380,   "change_24h": -1.8, "high_90d": 650,
             "low_90d": 240, "drawdown_from_90d_high": 0.415,
             "ma50": 420, "ma200": 360,
             "source": "mock", "timestamp": "2026-05-22T10:00:00"},
    "DIL":  {"price": 0.003, "change_24h": 0.5, "high_90d": 0.005,
             "low_90d": 0.001, "drawdown_from_90d_high": 0.400,
             "ma50": None, "ma200": None,
             "source": "mock", "timestamp": "2026-05-22T10:00:00"},
    "USDC": {"price": 1.00, "change_24h": 0.0, "high_90d": 1.00,
             "low_90d": 1.00, "drawdown_from_90d_high": 0.0,
             "ma50": 1.00, "ma200": 1.00,
             "source": "mock", "timestamp": "2026-05-22T10:00:00"},
    "USDT": {"price": 1.00, "change_24h": 0.0, "high_90d": 1.00,
             "low_90d": 1.00, "drawdown_from_90d_high": 0.0,
             "ma50": 1.00, "ma200": 1.00,
             "source": "mock", "timestamp": "2026-05-22T10:00:00"},
}

MOCK_FEAR_GREED = {"value": 30, "classification": "Fear",
                   "source": "mock", "timestamp": "2026-05-22T10:00:00"}

MOCK_SOCIAL = {
    "CORE": {"social_score": 220, "sentiment": 0.38, "galaxy_score": 48,
             "alt_rank": 45, "social_volume_24h": 22000, "bullish_pct": -4,
             "source": "mock", "timestamp": "2026-05-22T10:00:00"},
    "XEL":  {"social_score": 35,  "sentiment": 0.52, "galaxy_score": 28,
             "alt_rank": 420, "social_volume_24h": 1200, "bullish_pct": 8,
             "source": "mock", "timestamp": "2026-05-22T10:00:00"},
    "XMR":  {"social_score": 180, "sentiment": 0.28, "galaxy_score": 44,
             "alt_rank": 24, "social_volume_24h": 12000, "bullish_pct": -12,
             "source": "mock", "timestamp": "2026-05-22T10:00:00"},
    "ZEC":  {"social_score": 90,  "sentiment": 0.26, "galaxy_score": 38,
             "alt_rank": 55, "social_volume_24h": 5000, "bullish_pct": -10,
             "source": "mock", "timestamp": "2026-05-22T10:00:00"},
    "TAO":  {"social_score": 310, "sentiment": 0.55, "galaxy_score": 54,
             "alt_rank": 18, "social_volume_24h": 38000, "bullish_pct": 5,
             "source": "mock", "timestamp": "2026-05-22T10:00:00"},
    "DIL":  {"social_score": 12,  "sentiment": 0.48, "galaxy_score": 22,
             "alt_rank": 890, "social_volume_24h": 300, "bullish_pct": 3,
             "source": "mock", "timestamp": "2026-05-22T10:00:00"},
}

# MOCK_ONCHAIN: CryptoQuant فقط BTC/ETH را پشتیبانی می‌کند — این داده‌ها فقط به‌عنوان
# macro context استفاده می‌شوند (نه برای معامله‌ی مستقیم BTC/ETH)
MOCK_ONCHAIN = {
    "BTC": {"exchange_netflow": -3200, "miner_netflow": -180, "nvt": 52,
            "source": "mock", "timestamp": "2026-05-22T10:00:00"},
    "ETH": {"exchange_netflow": -1800, "miner_netflow": -90,  "nvt": 48,
            "source": "mock", "timestamp": "2026-05-22T10:00:00"},
}

# نگاشت نماد به CoinGecko ID
COINGECKO_IDS = {
    "CORE": "coredaoorg",
    "XEL":  "xelis",
    "XMR":  "monero",
    "ZEC":  "zcash",
    "TAO":  "bittensor",
    "DIL":  "dilithion",
    "USDC": "usd-coin",
    "USDT": "tether",
}

# نگاشت نماد به LunarCrush symbol
LUNARCRUSH_SYMBOLS = {
    "CORE": "CORE",
    "XEL":  "XEL",
    "XMR":  "XMR",
    "ZEC":  "ZEC",
    "TAO":  "TAO",
    "DIL":  "DIL",
}

# نگاشت نماد به CryptoQuant slug (فقط BTC و ETH پشتیبانی کامل دارند)
CRYPTOQUANT_SLUGS = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
}


class DataFetcher:
    def __init__(self, config: dict, mock_mode: bool = False):
        # mock_mode: use fixture data — no network calls, no API keys required
        # حالت mock: از داده‌های ثابت استفاده می‌کند، نیاز به اینترنت و کلید ندارد
        self.mock_mode = mock_mode or bool(int(os.getenv("SENTINEL_MOCK_MODE", "0")))
        if self.mock_mode:
            logger.info("DataFetcher: MOCK MODE active (no live API calls)")

        self.config = config
        api_cfg = config.get("api", {})
        self.cg_base = api_cfg.get("coingecko_base", "https://api.coingecko.com/api/v3")
        self.cq_base = api_cfg.get("cryptoquant_base", "https://api.cryptoquant.com/v1")
        self.lc_base = api_cfg.get("lunarcrush_base", "https://lunarcrush.com/api4/public")
        self.fg_url  = api_cfg.get("fear_greed_url", "https://api.alternative.me/fng/")
        self.timeout = api_cfg.get("request_timeout", 15)
        self.retries = api_cfg.get("retry_count", 3)
        self.retry_delay = api_cfg.get("retry_delay", 5)

        self.cg_key = os.getenv("COINGECKO_API_KEY", "")
        self.cq_key = os.getenv("CRYPTOQUANT_API_KEY", "")
        self.lc_key = os.getenv("LUNARCRUSH_API_KEY", "")

        # کش ساده در RAM (تازه‌سازی هر ۱۵ دقیقه)
        self._cache: Dict[str, Any] = {}
        self._cache_ts: Dict[str, float] = {}
        self._cache_ttl = 900  # ثانیه

    # ─────────────────────────────────────────────
    # ابزارهای پایه
    # ─────────────────────────────────────────────

    def _get(self, url: str, headers: dict = None, params: dict = None) -> Optional[dict]:
        """GET با retry و timeout"""
        for attempt in range(self.retries):
            try:
                resp = requests.get(url, headers=headers or {}, params=params or {},
                                    timeout=self.timeout)
                resp.raise_for_status()
                return resp.json()
            except requests.exceptions.HTTPError as e:
                if resp.status_code == 429:
                    wait = int(resp.headers.get("Retry-After", self.retry_delay * (attempt + 1)))
                    logger.warning(f"Rate limit hit for {url}. Waiting {wait}s...")
                    time.sleep(wait)
                else:
                    logger.error(f"HTTP {resp.status_code} for {url}: {e}")
                    return None
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request attempt {attempt+1}/{self.retries} failed for {url}: {e}")
                if attempt < self.retries - 1:
                    time.sleep(self.retry_delay)
        logger.error(f"All retries failed for {url}")
        return None

    def _cached(self, key: str) -> Optional[Any]:
        if key in self._cache:
            if time.time() - self._cache_ts.get(key, 0) < self._cache_ttl:
                return self._cache[key]
        return None

    def _store(self, key: str, value: Any) -> None:
        self._cache[key] = value
        self._cache_ts[key] = time.time()

    # ─────────────────────────────────────────────
    # CoinGecko — قیمت و تاریخچه
    # ─────────────────────────────────────────────

    def get_price_data(self, symbol: str, override_price: float = None) -> Optional[dict]:
        """override_price: used by backtest.py to inject historical prices"""
        if self.mock_mode:
            data = dict(MOCK_PRICE.get(symbol, {}))
            if override_price is not None and data:
                # backtest uses this to replay historical prices
                # بک‌تست از این برای بازپخش قیمت‌های تاریخی استفاده می‌کند
                data["price"] = override_price
            return data or None
        """
        برمی‌گرداند: {price, change_24h, high_90d, low_90d, drawdown_from_90d_high}
        """
        cached = self._cached(f"price_{symbol}")
        if cached:
            return cached

        coin_id = COINGECKO_IDS.get(symbol)
        if not coin_id:
            return None

        headers = {}
        if self.cg_key:
            headers["x-cg-pro-api-key"] = self.cg_key

        # قیمت فعلی
        data = self._get(
            f"{self.cg_base}/simple/price",
            headers=headers,
            params={"ids": coin_id, "vs_currencies": "usd",
                    "include_24hr_change": "true"}
        )
        if not data or coin_id not in data:
            logger.warning(f"CoinGecko price unavailable for {symbol}")
            return None

        price = data[coin_id].get("usd", 0)
        change_24h = data[coin_id].get("usd_24h_change", 0)

        # تاریخچه ۹۰ روز
        hist = self._get(
            f"{self.cg_base}/coins/{coin_id}/market_chart",
            headers=headers,
            params={"vs_currency": "usd", "days": "90", "interval": "daily"}
        )
        high_90d = low_90d = price
        if hist and "prices" in hist:
            prices_90 = [p[1] for p in hist["prices"] if p[1]]
            if prices_90:
                high_90d = max(prices_90)
                low_90d  = min(prices_90)

        drawdown = 0.0
        if high_90d > 0:
            drawdown = (high_90d - price) / high_90d  # 0.0 تا 1.0

        # میانگین‌های متحرک ۵۰ و ۲۰۰ روز
        ma50 = ma200 = None
        hist_200 = self._get(
            f"{self.cg_base}/coins/{coin_id}/market_chart",
            headers=headers,
            params={"vs_currency": "usd", "days": "200", "interval": "daily"}
        )
        if hist_200 and "prices" in hist_200:
            all_prices = [p[1] for p in hist_200["prices"] if p[1]]
            if len(all_prices) >= 200:
                ma200 = sum(all_prices[-200:]) / 200
            if len(all_prices) >= 50:
                ma50 = sum(all_prices[-50:]) / 50

        result = {
            "price": price,
            "change_24h": change_24h,
            "high_90d": high_90d,
            "low_90d": low_90d,
            "drawdown_from_90d_high": drawdown,
            "ma50": ma50,
            "ma200": ma200,
            "source": "coingecko",
            "timestamp": datetime.utcnow().isoformat(),
        }
        self._store(f"price_{symbol}", result)
        return result

    # ─────────────────────────────────────────────
    # Fear & Greed Index
    # ─────────────────────────────────────────────

    def get_fear_greed(self, override_value: int = None) -> Optional[dict]:
        if self.mock_mode:
            data = dict(MOCK_FEAR_GREED)
            if override_value is not None:
                data["value"] = override_value
            return data
        """برمی‌گرداند: {value: 0-100, classification: str}"""
        cached = self._cached("fear_greed")
        if cached:
            return cached

        data = self._get(self.fg_url, params={"limit": 1})
        if not data or not data.get("data"):
            logger.warning("Fear & Greed index unavailable")
            return None

        entry = data["data"][0]
        result = {
            "value": int(entry.get("value", 50)),
            "classification": entry.get("value_classification", "Neutral"),
            "source": "alternative.me",
            "timestamp": datetime.utcnow().isoformat(),
        }
        self._store("fear_greed", result)
        return result

    # ─────────────────────────────────────────────
    # LunarCrush — social signal
    # ─────────────────────────────────────────────

    def get_social_data(self, symbol: str) -> Optional[dict]:
        if self.mock_mode:
            return dict(MOCK_SOCIAL.get(symbol, {})) or None
        """
        برمی‌گرداند: {social_score, sentiment, galaxy_score, alt_rank, volume_24h_social}
        sentiment: 0.0 تا 1.0 (بیشتر = مثبت‌تر)
        """
        if not self.lc_key:
            logger.warning("LunarCrush API key missing — social signal unavailable")
            return None

        cached = self._cached(f"social_{symbol}")
        if cached:
            return cached

        lc_sym = LUNARCRUSH_SYMBOLS.get(symbol)
        if not lc_sym:
            return None

        headers = {"Authorization": f"Bearer {self.lc_key}"}
        data = self._get(
            f"{self.lc_base}/coins/{lc_sym}/v1",
            headers=headers
        )
        if not data or "data" not in data:
            logger.warning(f"LunarCrush data unavailable for {symbol}")
            return None

        d = data["data"]
        # نرمال‌سازی sentiment به 0-1
        # LunarCrush sentiment معمولاً عدد 1-5 یا درصد است — اینجا محافظانه نرمال می‌کنیم
        raw_sentiment = d.get("average_sentiment", 3)
        sentiment_norm = max(0.0, min(1.0, (raw_sentiment - 1) / 4))

        result = {
            "social_score": d.get("social_score", 0),
            "sentiment": sentiment_norm,
            "galaxy_score": d.get("galaxy_score", 0),
            "alt_rank": d.get("alt_rank", 9999),
            "social_volume_24h": d.get("social_volume_24h", 0),
            "bullish_pct": d.get("percent_change_social_volume_24h", 0),
            "source": "lunarcrush",
            "timestamp": datetime.utcnow().isoformat(),
        }
        self._store(f"social_{symbol}", result)
        return result

    # ─────────────────────────────────────────────
    # CryptoQuant — on-chain signal (فقط BTC/ETH)
    # ─────────────────────────────────────────────

    def get_onchain_data(self, symbol: str) -> Optional[dict]:
        if self.mock_mode:
            return dict(MOCK_ONCHAIN.get(symbol, {})) or None
        """
        برمی‌گرداند: {exchange_netflow, miner_netflow, nvt_signal, active_addresses}
        فقط برای BTC و ETH کامل است؛ برای بقیه None
        """
        if symbol not in CRYPTOQUANT_SLUGS:
            return None

        if not self.cq_key:
            logger.warning("CryptoQuant API key missing — on-chain signal unavailable")
            return None

        cached = self._cached(f"onchain_{symbol}")
        if cached:
            return cached

        slug = CRYPTOQUANT_SLUGS[symbol]
        headers = {"Authorization": f"Bearer {self.cq_key}"}

        # Exchange netflow (خروج بزرگ از صرافی = انباشت = صعودی)
        netflow_data = self._get(
            f"{self.cq_base}/{slug}/exchange-flows/netflow",
            headers=headers,
            params={"window": "day", "limit": 1}
        )
        exchange_netflow = 0
        if netflow_data and "data" in netflow_data:
            items = netflow_data["data"]
            if items:
                exchange_netflow = items[-1].get("value", 0)

        # Miner netflow (ماینرها می‌فروشند؟)
        miner_data = self._get(
            f"{self.cq_base}/{slug}/miner-flows/netflow",
            headers=headers,
            params={"window": "day", "limit": 1}
        )
        miner_netflow = 0
        if miner_data and "data" in miner_data:
            items = miner_data["data"]
            if items:
                miner_netflow = items[-1].get("value", 0)

        # NVT Signal
        nvt_data = self._get(
            f"{self.cq_base}/{slug}/network-indicator/nvt",
            headers=headers,
            params={"window": "day", "limit": 1}
        )
        nvt = None
        if nvt_data and "data" in nvt_data:
            items = nvt_data["data"]
            if items:
                nvt = items[-1].get("value")

        if exchange_netflow == 0 and miner_netflow == 0 and nvt is None:
            logger.warning(f"CryptoQuant returned empty data for {symbol}")
            return None

        result = {
            "exchange_netflow": exchange_netflow,   # منفی = خروج از صرافی (صعودی)
            "miner_netflow": miner_netflow,          # منفی = ماینرها نگه می‌دارند (صعودی)
            "nvt": nvt,
            "source": "cryptoquant",
            "timestamp": datetime.utcnow().isoformat(),
        }
        self._store(f"onchain_{symbol}", result)
        return result

    # ─────────────────────────────────────────────
    # جمع‌آوری همه داده‌های یک دارایی
    # ─────────────────────────────────────────────

    def fetch_all(self, symbol: str) -> dict:
        """
        همه داده‌های یک دارایی را جمع می‌کند.
        در صورت ناموجود بودن هر منبع، آن بخش None است.
        """
        result = {
            "symbol": symbol,
            "price": None,
            "fear_greed": None,
            "social": None,
            "onchain": None,
            "available_signals": [],
            "data_quality": "full",   # full | partial | minimal
        }

        result["price"] = self.get_price_data(symbol)
        if result["price"]:
            result["available_signals"].append("price")

        result["fear_greed"] = self.get_fear_greed()
        if result["fear_greed"]:
            result["available_signals"].append("fear_greed")

        # social فقط برای دارایی‌های غیر stablecoin
        if symbol in LUNARCRUSH_SYMBOLS:
            result["social"] = self.get_social_data(symbol)
            if result["social"]:
                result["available_signals"].append("social")

        # on-chain فقط BTC/ETH
        if symbol in CRYPTOQUANT_SLUGS:
            result["onchain"] = self.get_onchain_data(symbol)
            if result["onchain"]:
                result["available_signals"].append("onchain")

        # ارزیابی کیفیت داده
        n = len(result["available_signals"])
        if n == 0:
            result["data_quality"] = "none"
        elif n <= 1:
            result["data_quality"] = "minimal"
        elif n <= 2:
            result["data_quality"] = "partial"
        else:
            result["data_quality"] = "full"

        logger.info(f"{symbol}: signals={result['available_signals']}, quality={result['data_quality']}")
        return result

    def fetch_market_overview(self) -> dict:
        """Fear & Greed + قیمت همه دارایی‌ها را یک‌جا برمی‌گرداند"""
        overview = {"fear_greed": self.get_fear_greed(), "assets": {}}
        for sym in COINGECKO_IDS:
            overview["assets"][sym] = self.get_price_data(sym)
        return overview
