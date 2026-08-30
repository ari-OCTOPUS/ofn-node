"""
SENTINEL — cq_client.py
کلاینت کامل CryptoQuant با rate-limiting و mock mode

پوشش endpoint ها:
  BTC:
    - exchange-flows (in/out/netflow)
    - flow-indicator (whale ratio, exchange whale ratio)
    - miner-flows (outflow ماینرها)
  ETH:
    - exchange-flows
    - staking-related (اگر پلن اجازه دهد)
  Stablecoin:
    - stablecoin-exchange-flows (نقدینگی آماده ورود)

نکته: exchange flows هفتگی (سه‌شنبه ۰۰:۰۰ UTC) به‌روز می‌شوند.
نکته: API فقط روی Professional/Premium پلن فعال است.

نحوه استفاده:
  from cq_client import CryptoQuantClient
  cq = CryptoQuantClient(api_key="YOUR_KEY")
  flows = cq.get_exchange_flows("BTC", days=90)
  regime = cq.compute_macro_regime()
"""

import os
import time
import logging
from typing import Optional, List, Dict

import requests

logger = logging.getLogger(__name__)

# ─── Mock fixtures ─────────────────────────────────────────
MOCK_EXCHANGE_FLOWS = {
    "BTC": {
        "inflow_usd":   1_200_000_000,
        "outflow_usd":  1_850_000_000,
        "netflow_usd":   -650_000_000,    # منفی = خروج خالص = انباشت ✅
        "inflow_btc":    13800,
        "outflow_btc":   21300,
        "netflow_btc":   -7500,
    },
    "ETH": {
        "inflow_usd":    480_000_000,
        "outflow_usd":   710_000_000,
        "netflow_usd":   -230_000_000,
        "inflow_eth":    145000,
        "outflow_eth":   215000,
        "netflow_eth":   -70000,
    },
}

MOCK_WHALE_RATIO = {
    "BTC": {
        "whale_ratio": 0.38,            # < 0.85 → فشار فروش نهنگ پایین ✅
        "exchange_whale_ratio": 0.42,
    },
    "ETH": {
        "whale_ratio": 0.31,
        "exchange_whale_ratio": 0.35,
    },
}

MOCK_MINER_FLOWS = {
    "BTC": {
        "miner_outflow_usd": 85_000_000,
        "miner_to_exchange_usd": 32_000_000,   # کم = ماینرها نمی‌فروشند ✅
        "miner_inventory_usd": 12_400_000_000,
    },
}

MOCK_STABLECOIN_FLOWS = {
    "USDT": {
        "exchange_inflow_usd": 920_000_000,   # مثبت = نقدینگی آماده ورود ✅
        "exchange_outflow_usd": 610_000_000,
        "exchange_netflow_usd": 310_000_000,
    },
    "USDC": {
        "exchange_inflow_usd": 340_000_000,
        "exchange_outflow_usd": 280_000_000,
        "exchange_netflow_usd": 60_000_000,
    },
}


class CryptoQuantClient:
    """
    کلاینت کامل CryptoQuant با rate-limiting خودکار.
    mock_mode=True → داده‌ی fixture برمی‌گرداند.
    """

    BASE_URL = "https://api.cryptoquant.com/v1"
    MIN_INTERVAL = 1.5   # CryptoQuant معمولاً ۱۰۰ req/min → ۰.۶s کافیه + margin

    def __init__(self, api_key: str = "", mock_mode: bool = False):
        self.api_key = api_key or os.getenv("CRYPTOQUANT_API_KEY", "")
        self.mock_mode = mock_mode or bool(os.getenv("SENTINEL_MOCK_MODE"))
        self._last_call = 0.0
        self._session = requests.Session()
        if self.api_key:
            self._session.headers.update({
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            })

    # ─── Rate limiter ──────────────────────────────────────

    def _throttle(self):
        elapsed = time.time() - self._last_call
        if elapsed < self.MIN_INTERVAL:
            time.sleep(self.MIN_INTERVAL - elapsed)
        self._last_call = time.time()

    def _get(self, path: str, params: dict = None) -> Optional[dict]:
        if self.mock_mode:
            return None
        self._throttle()
        url = f"{self.BASE_URL}/{path}"
        try:
            resp = self._session.get(url, params=params or {}, timeout=15)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                logger.warning("CryptoQuant rate limit hit — sleeping 30s")
                time.sleep(30)
            elif e.response.status_code == 402:
                logger.error("CryptoQuant: endpoint نیاز به پلن بالاتر دارد")
            else:
                logger.error(f"CryptoQuant HTTP {e.response.status_code}: {path}")
            return None
        except Exception as e:
            logger.error(f"CryptoQuant request failed: {e}")
            return None

    def _parse_timeseries(self, data: dict, value_key: str) -> List[dict]:
        """خروجی CryptoQuant رو به لیست دیکشنری تبدیل می‌کند."""
        if not data:
            return []
        result_data = data.get("data", {}).get("result", [])
        rows = []
        for entry in result_data:
            rows.append({
                "timestamp": entry.get("timestamp") or entry.get("date"),
                "value": entry.get(value_key) or entry.get("value"),
            })
        return rows

    # ─── Exchange Flows ────────────────────────────────────

    def get_exchange_flows(self, symbol: str, days: int = 90) -> Optional[dict]:
        """
        جریان ورود/خروج به صرافی‌ها — هسته‌ی سیگنال رژیم.
        netflow منفی = انباشت ✅   netflow مثبت = توزیع ⚠️
        """
        if self.mock_mode:
            return MOCK_EXCHANGE_FLOWS.get(symbol)

        coin = symbol.lower()
        window = f"{days}d"

        # ورودی
        inflow_data = self._get(
            f"{coin}/exchange-flows/inflow",
            params={"window": "day", "limit": days, "exchange": "all_exchange"},
        )
        outflow_data = self._get(
            f"{coin}/exchange-flows/outflow",
            params={"window": "day", "limit": days, "exchange": "all_exchange"},
        )
        if not inflow_data and not outflow_data:
            return None

        # محاسبه جمع ۳۰ روز اخیر
        def sum_values(data_resp):
            rows = self._parse_timeseries(data_resp or {}, "value")
            return sum(r.get("value", 0) or 0 for r in rows[-30:])

        inflow  = sum_values(inflow_data)
        outflow = sum_values(outflow_data)
        return {
            "inflow_usd":   inflow,
            "outflow_usd":  outflow,
            "netflow_usd":  outflow - inflow,
            "inflow_btc":   None,   # پُر از raw data اگر نیاز شد
            "outflow_btc":  None,
            "netflow_btc":  None,
        }

    def get_exchange_flows_timeseries(self, symbol: str, days: int = 365) -> List[dict]:
        """
        تاریخچه‌ی روزانه‌ی flow — برای harvest و ذخیره‌ی تاریخی.
        """
        if self.mock_mode:
            import random
            random.seed(hash(symbol + "flows"))
            base = MOCK_EXCHANGE_FLOWS.get(symbol, {})
            rows = []
            now = int(time.time())
            for i in range(days, 0, -1):
                nf = (base.get("netflow_usd", -300_000_000)
                      * random.uniform(0.2, 2.0) * (-1 if random.random() < 0.35 else 1))
                rows.append({
                    "timestamp": now - i * 86400,
                    "netflow_usd": round(nf),
                    "inflow_usd": round(abs(nf) * random.uniform(1.5, 3.0)),
                    "outflow_usd": round(abs(nf) * random.uniform(1.5, 3.0) + abs(nf)),
                })
            return rows

        coin = symbol.lower()
        data = self._get(
            f"{coin}/exchange-flows/netflow",
            params={"window": "day", "limit": days, "exchange": "all_exchange"},
        )
        return self._parse_timeseries(data, "value")

    # ─── Whale Ratio ───────────────────────────────────────

    def get_whale_ratio(self, symbol: str) -> Optional[dict]:
        """
        نسبت تراکنش‌های نهنگ به کل تراکنش‌ها.
        whale_ratio > 0.85 → فشار فروش نهنگ بالا ⚠️
        whale_ratio < 0.6  → نهنگ‌ها ساکت ✅
        """
        if self.mock_mode:
            return MOCK_WHALE_RATIO.get(symbol)

        data = self._get(
            f"{symbol.lower()}/flow-indicator/exchange-whale-ratio",
            params={"window": "day", "limit": 7},
        )
        rows = self._parse_timeseries(data, "value")
        if not rows:
            return None
        avg = sum(r.get("value", 0) or 0 for r in rows) / len(rows)
        return {"whale_ratio": round(avg, 4), "exchange_whale_ratio": round(avg, 4)}

    def get_whale_ratio_timeseries(self, symbol: str, days: int = 365) -> List[dict]:
        """تاریخچه whale ratio برای harvest."""
        if self.mock_mode:
            import random
            random.seed(hash(symbol + "whale"))
            base = MOCK_WHALE_RATIO.get(symbol, {}).get("whale_ratio", 0.5)
            rows = []
            now = int(time.time())
            for i in range(days, 0, -1):
                rows.append({
                    "timestamp": now - i * 86400,
                    "whale_ratio": max(0.1, min(1.0, base + random.gauss(0, 0.08))),
                })
            return rows

        data = self._get(
            f"{symbol.lower()}/flow-indicator/exchange-whale-ratio",
            params={"window": "day", "limit": days},
        )
        return self._parse_timeseries(data, "value")

    # ─── Miner Flows ───────────────────────────────────────

    def get_miner_flows(self, symbol: str = "BTC") -> Optional[dict]:
        """
        جریان خروجی ماینرها — مستقیماً به استراتژی ماینینگ ارمین مربوط.
        miner_to_exchange_usd بالا → ماینرها در حال فروش ⚠️
        """
        if symbol != "BTC":
            return None    # CryptoQuant فقط BTC miner data دارد

        if self.mock_mode:
            return MOCK_MINER_FLOWS.get("BTC")

        data = self._get(
            "btc/miner-flows/outflow",
            params={"window": "day", "limit": 30},
        )
        rows = self._parse_timeseries(data, "value")
        if not rows:
            return None
        avg_out = sum(r.get("value", 0) or 0 for r in rows[-7:]) / 7
        return {
            "miner_outflow_usd": round(avg_out),
            "miner_to_exchange_usd": round(avg_out * 0.38),  # تخمین
            "miner_inventory_usd": None,
        }

    def get_miner_flows_timeseries(self, days: int = 365) -> List[dict]:
        """تاریخچه miner flows برای harvest."""
        if self.mock_mode:
            import random
            random.seed(42)
            base = MOCK_MINER_FLOWS["BTC"]["miner_outflow_usd"]
            rows = []
            now = int(time.time())
            for i in range(days, 0, -1):
                rows.append({
                    "timestamp": now - i * 86400,
                    "miner_outflow_usd": max(0, int(base * random.uniform(0.5, 2.0))),
                    "miner_to_exchange_usd": max(0, int(base * 0.38 * random.uniform(0.3, 2.5))),
                })
            return rows

        data = self._get("btc/miner-flows/outflow", params={"window": "day", "limit": days})
        return self._parse_timeseries(data, "value")

    # ─── Stablecoin Flows ──────────────────────────────────

    def get_stablecoin_flows(self) -> dict:
        """
        جریان USDT + USDC به صرافی‌ها — نقدینگی آماده‌ی ورود.
        netflow مثبت = پول جدید وارد می‌شود ✅
        """
        if self.mock_mode:
            return {
                "total_netflow_usd": sum(
                    v["exchange_netflow_usd"] for v in MOCK_STABLECOIN_FLOWS.values()
                ),
                "usdt": MOCK_STABLECOIN_FLOWS.get("USDT", {}),
                "usdc": MOCK_STABLECOIN_FLOWS.get("USDC", {}),
            }

        usdt_data = self._get(
            "usdt/exchange-flows/netflow",
            params={"window": "day", "limit": 30, "exchange": "all_exchange"},
        )
        usdc_data = self._get(
            "usdc/exchange-flows/netflow",
            params={"window": "day", "limit": 30, "exchange": "all_exchange"},
        )

        def sum_rows(data_resp):
            rows = self._parse_timeseries(data_resp or {}, "value")
            return sum(r.get("value", 0) or 0 for r in rows[-7:])

        usdt_nf = sum_rows(usdt_data)
        usdc_nf = sum_rows(usdc_data)
        return {
            "total_netflow_usd": usdt_nf + usdc_nf,
            "usdt": {"exchange_netflow_usd": usdt_nf},
            "usdc": {"exchange_netflow_usd": usdc_nf},
        }

    def get_stablecoin_flows_timeseries(self, days: int = 365) -> List[dict]:
        """تاریخچه stablecoin flows برای harvest."""
        if self.mock_mode:
            import random
            random.seed(999)
            rows = []
            now = int(time.time())
            for i in range(days, 0, -1):
                rows.append({
                    "timestamp": now - i * 86400,
                    "total_netflow_usd": int(random.gauss(200_000_000, 400_000_000)),
                })
            return rows

        usdt_data = self._get(
            "usdt/exchange-flows/netflow",
            params={"window": "day", "limit": days, "exchange": "all_exchange"},
        )
        return self._parse_timeseries(usdt_data, "value")

    # ─── سیگنال ترکیبی (macro_regime) ────────────────────

    def compute_macro_regime(self, symbol: str = "BTC") -> Optional[float]:
        """
        macro_regime ∈ [-1, +1]

        فرمول:
          flow_score    = clamp(−netflow_btc / threshold, −1, +1)    # خروج = مثبت
          whale_score   = 1 − clamp(whale_ratio / 0.85, 0, 1)        # نهنگ ساکت = مثبت
          miner_score   = 1 − clamp(miner_to_exchange / threshold, 0, 1)
          stable_score  = clamp(stable_netflow / threshold, 0, 1)     # نقدینگی = مثبت

          raw = 0.40 * flow_score + 0.25 * whale_score
              + 0.20 * miner_score + 0.15 * stable_score

        مثبت = risk-on (پول واقعی وارد می‌شود، نهنگ‌ها نمی‌فروشند)
        منفی = risk-off (پول خارج می‌شود، فشار فروش نهنگ‌ها بالا)
        """
        flows    = self.get_exchange_flows(symbol)
        whale    = self.get_whale_ratio(symbol)
        miner    = self.get_miner_flows("BTC")  # همیشه BTC
        stables  = self.get_stablecoin_flows()

        if not flows:
            return None

        # Flow score: خروج خالص بزرگ‌تر = مثبت‌تر
        netflow_usd = flows.get("netflow_usd", 0) or 0
        # threshold: ۵۰۰M برای BTC، ۲۰۰M برای ETH
        threshold = 500_000_000 if symbol == "BTC" else 200_000_000
        flow_score = max(-1.0, min(1.0, -netflow_usd / threshold))  # منفی netflow = خروج = خوب

        # Whale score
        whale_ratio = (whale or {}).get("whale_ratio", 0.5)
        whale_score = 1.0 - min(1.0, whale_ratio / 0.85)

        # Miner score
        miner_to_ex = (miner or {}).get("miner_to_exchange_usd", 0) or 0
        miner_threshold = 50_000_000
        miner_score = 1.0 - min(1.0, miner_to_ex / miner_threshold)

        # Stablecoin score
        stable_nf = (stables or {}).get("total_netflow_usd", 0) or 0
        stable_score = max(0.0, min(1.0, stable_nf / 500_000_000))

        raw = (0.40 * flow_score +
               0.25 * whale_score +
               0.20 * miner_score +
               0.15 * stable_score)

        # نرمال‌سازی به [-1, +1]
        # بازه واقعی raw ≈ [-0.4, +1.0] → shift
        regime = max(-1.0, min(1.0, raw * 2 - 0.5))
        return round(regime, 4)
