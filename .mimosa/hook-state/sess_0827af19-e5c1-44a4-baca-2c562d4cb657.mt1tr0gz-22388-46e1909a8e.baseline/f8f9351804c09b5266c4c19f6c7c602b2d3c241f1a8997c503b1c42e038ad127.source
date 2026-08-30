"""
data/real_api.py — Real-world time series from free APIs (no key required).

Sources:
    - Yahoo Finance (via yfinance) — stock/crypto prices
    - Synthetic fallback if network unavailable

All functions return a numpy array + metadata dict.
"""
from __future__ import annotations

import numpy as np


def fetch_yahoo_finance(ticker: str = "^GSPC", period: str = "5y",
                        interval: str = "1d") -> dict:
    """
    Fetch daily returns from Yahoo Finance.

    Args:
        ticker:   Yahoo symbol (^GSPC=S&P500, BTC-USD, AAPL, etc.)
        period:   1y, 2y, 5y, 10y, max
        interval: 1d, 1wk, 1mo

    Returns: {series, label, n, source, info}
    """
    try:
        import yfinance as yf
    except ImportError:
        return _fallback("yfinance not installed — using synthetic substitute")

    try:
        try:
            data = yf.download(ticker, period=period, interval=interval,
                               progress=False, auto_adjust=True, timeout=20)
        except TypeError:
            # نسخه‌های قدیمی‌ترِ yfinance پارامترِ timeout ندارند
            data = yf.download(ticker, period=period, interval=interval,
                               progress=False, auto_adjust=True)
        if data.empty:
            return _fallback(f"no data for ticker {ticker}")

        close = data["Close"].dropna().values.flatten()
        close = close[close > 0]  # گاردِ log(0)/log(منفی) — مطابقِ بقیه‌ی fetcherها
        if close.size < 3:
            return _fallback(f"non-positive/empty closes for {ticker}")
        returns = np.diff(np.log(close))  # log returns

        return {
            "series":  returns,
            "label":   f"Yahoo Finance: {ticker} ({period} log-returns)",
            "n":       len(returns),
            "source":  "yahoo_finance",
            "info":    {"ticker": ticker, "period": period, "interval": interval},
        }
    except Exception as e:
        return _fallback(f"fetch error: {e}")


def fetch_noaa_temperature(station: str = "GHCND:USW00014922",
                           dataset: str = "GHCND") -> dict:
    """
    Fetch temperature data from NOAA (requires no key for some endpoints,
    but the NCEI API is more reliable). We use a simplified approach:
    fetch from a public CSV mirror if available, else fallback.

    Station USW00014922 = Chicago O'Hare.
    """
    try:
        import requests
        # NCEI public daily summary (no key needed for this endpoint)
        url = ("https://www.ncei.noaa.gov/access/services/data/v1?"
               f"dataset={dataset}&stations={station}"
               "&dataTypes=TAVG&startDate=2020-01-01&endDate=2024-12-31"
               "&format=json&units=metric")
        resp = _requests_get(url, timeout=15)
        if resp.status_code == 200 and resp.text.strip():
            records = resp.json()
            temps = [float(r["TAVG"]) for r in records
                     if r.get("TAVG") not in (None, "")]
            if temps:
                series = np.array(temps, dtype=float)
                return {
                    "series": series,
                    "label":  f"NOAA daily temp: {station}",
                    "n":      len(series),
                    "source": "noaa_ncei",
                    "info":   {"station": station},
                }
        return _fallback("NOAA API returned empty")
    except Exception as e:
        return _fallback(f"NOAA fetch error: {e}")


import time
import json
import hashlib
from datetime import date

# استفاده‌ی اصولی از API: cache روزانه + محدودیتِ نرخ (politeness / ضدِ hammer)
_MIN_LIVE_INTERVAL = 4.0          # حداقل فاصله بین دو دریافتِ زنده از «همان» منبع
_GLOBAL_MIN_INTERVAL = 1.0        # فاصله‌ی کوچکِ سراسری بین هر دو دریافتِ زنده
_last_live_fetch = [0.0]          # زمانِ آخرین دریافتِ شبکه (سراسری)
_last_live_by_source: dict = {}   # B4: تایمرِ per-source

# B7: retry با backoff نمایی — یک blip گذرا دیگر مستقیم به fallbackِ مصنوعی نمی‌افتد
import os as _os
_RETRY_ATTEMPTS = int(_os.getenv("NET_RETRY_ATTEMPTS", "3"))


def _requests_get(url, **kw):
    """GET با ۲-۳ تلاش و backoff نمایی؛ فقط خطاهای transport را retry می‌کند."""
    import requests
    last = None
    for attempt in range(max(_RETRY_ATTEMPTS, 1)):
        try:
            return requests.get(url, **kw)
        except requests.exceptions.RequestException as e:
            last = e
            time.sleep(0.5 * (2 ** attempt))
    raise last


def _throttled(source_key: str) -> bool:
    """B4: قبلاً یک تایمرِ سراسری، منبعِ دومِ چرخش را هم به fallbackِ مصنوعی
    می‌انداخت (بیشترِ «داده‌ی واقعی» عملاً مصنوعی می‌شد). حالا هر منبع سقفِ
    خودش را دارد + یک فاصله‌ی کوچکِ سراسری برای politeness.
    اگر مجاز بود، تایمرها را جلو می‌برد و False برمی‌گرداند."""
    now = time.time()
    if now - _last_live_fetch[0] < _GLOBAL_MIN_INTERVAL:
        return True
    if now - _last_live_by_source.get(source_key, 0.0) < _MIN_LIVE_INTERVAL:
        return True
    _last_live_fetch[0] = now
    _last_live_by_source[source_key] = now
    return False


def _cache_dir():
    from config.settings import OUTPUT_DIR
    d = OUTPUT_DIR / "real_cache"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _cached_fetch(cache_key: str, fetch_fn, live_source: str) -> dict:
    """پوششِ عمومیِ اصولی: cache روزانه + throttle + ذخیره — برای هر منبعِ واقعی."""
    import numpy as np
    key = f"{cache_key}|{date.today().isoformat()}"
    cf = _cache_dir() / (hashlib.md5(key.encode("utf-8")).hexdigest() + ".json")
    if cf.exists():
        try:
            d = json.loads(cf.read_text(encoding="utf-8"))
            d["series"] = np.asarray(d["series"], dtype=float)
            d["source"] = live_source + "(cache)"
            return d
        except Exception:
            pass
    if _throttled(cache_key):
        return _fallback(f"throttled — حداقل {_MIN_LIVE_INTERVAL:.0f}s بین دریافت‌های زنده‌ی همان منبع")
    res = fetch_fn()
    if res.get("source") == live_source:
        try:
            payload = {**res, "series": np.asarray(res["series"], dtype=float).tolist()}
            cf.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass
    return res


def fetch_frankfurter(base: str = "USD", quote: str = "EUR", years: int = 3) -> dict:
    """Frankfurter — نرخِ ارزِ رسمیِ ECB (بدونِ کلید). خروجی: log-returnهای روزانه."""
    try:
        import requests
        import numpy as np
        from datetime import timedelta
        end = date.today()
        start = end - timedelta(days=365 * years)
        url = (f"https://api.frankfurter.app/{start.isoformat()}..{end.isoformat()}"
               f"?from={base}&to={quote}")
        r = _requests_get(url, timeout=20)
        if r.status_code != 200:
            return _fallback(f"frankfurter http {r.status_code}")
        rates = r.json().get("rates", {})
        vals = [rates[d][quote] for d in sorted(rates) if quote in rates[d]]
        arr = np.asarray(vals, dtype=float)
        arr = arr[arr > 0]
        if len(arr) < 30:
            return _fallback(f"frankfurter few points {base}{quote}")
        returns = np.diff(np.log(arr))
        return {"series": returns, "label": f"FX {base}/{quote} ({years}y)",
                "n": len(returns), "source": "frankfurter",
                "info": {"base": base, "quote": quote}}
    except Exception as e:
        return _fallback(f"frankfurter error: {e}")


def fetch_coingecko(coin: str = "bitcoin", days: int = 365) -> dict:
    """CoinGecko — قیمتِ روزانه‌ی کریپتو (بدونِ کلید). خروجی: log-returns."""
    try:
        import requests
        import numpy as np
        url = (f"https://api.coingecko.com/api/v3/coins/{coin}/market_chart"
               f"?vs_currency=usd&days={days}&interval=daily")
        r = _requests_get(url, timeout=20,
                        headers={"User-Agent": "4d_system-research"})
        if r.status_code != 200:
            return _fallback(f"coingecko http {r.status_code}")
        prices = [p[1] for p in r.json().get("prices", []) if p and p[1]]
        arr = np.asarray(prices, dtype=float)
        arr = arr[arr > 0]
        if len(arr) < 30:
            return _fallback(f"coingecko few points {coin}")
        returns = np.diff(np.log(arr))
        return {"series": returns, "label": f"Crypto {coin} ({days}d)",
                "n": len(returns), "source": "coingecko",
                "info": {"coin": coin}}
    except Exception as e:
        return _fallback(f"coingecko error: {e}")


def fetch_openmeteo(lat: float, lon: float, name: str = "", years: int = 3) -> dict:
    """Open-Meteo — دمای روزانه‌ی رسمی (بدونِ کلید). سری خام (ساختارِ فصلیِ قوی)."""
    try:
        import requests
        import numpy as np
        from datetime import timedelta
        end = date.today() - timedelta(days=7)
        start = end - timedelta(days=365 * years)
        url = ("https://archive-api.open-meteo.com/v1/archive"
               f"?latitude={lat}&longitude={lon}"
               f"&start_date={start.isoformat()}&end_date={end.isoformat()}"
               "&daily=temperature_2m_mean&timezone=UTC")
        r = _requests_get(url, timeout=25)
        if r.status_code != 200:
            return _fallback(f"openmeteo http {r.status_code}")
        temps = r.json().get("daily", {}).get("temperature_2m_mean", [])
        arr = np.asarray([t for t in temps if t is not None], dtype=float)
        if len(arr) < 30:
            return _fallback(f"openmeteo few points {name}")
        return {"series": arr, "label": f"Temp {name or f'{lat},{lon}'} ({years}y)",
                "n": len(arr), "source": "openmeteo",
                "info": {"lat": lat, "lon": lon, "name": name}}
    except Exception as e:
        return _fallback(f"openmeteo error: {e}")


# جهانِ داده‌ی واقعی — چند منبعِ رسمیِ keyless، هر کدام با امضای رفتاریِ متمایز
REAL_UNIVERSE = (
    [("fx", b, q) for b, q in [("USD", "EUR"), ("USD", "GBP"), ("USD", "JPY"),
                                ("USD", "CHF"), ("USD", "AUD"), ("USD", "CAD"),
                                ("EUR", "GBP"), ("EUR", "JPY"), ("GBP", "JPY")]]
    + [("crypto", c) for c in ["bitcoin", "ethereum", "solana", "cardano",
                                "dogecoin", "litecoin", "ripple", "polkadot"]]
    + [("temp", lat, lon, nm) for lat, lon, nm in [
        (52.52, 13.41, "Berlin"), (35.68, 139.69, "Tokyo"),
        (40.71, -74.01, "NYC"), (30.04, 31.24, "Cairo"),
        (-33.87, 151.21, "Sydney"), (55.75, 37.62, "Moscow"),
        (1.35, 103.82, "Singapore"), (-23.55, -46.63, "SaoPaulo")]]
    + [("stock", t, p) for t in ["AAPL", "MSFT", "TSLA", "NVDA", "AMZN"]
       for p in ["2y"]]
)


def fetch_real(index: int) -> dict:
    """یک سری‌زمانیِ واقعی از جهانِ چندمنبعی (چرخشی، cache+throttleدار)."""
    spec = REAL_UNIVERSE[index % len(REAL_UNIVERSE)]
    kind = spec[0]
    if kind == "fx":
        _, b, q = spec
        return _cached_fetch(f"fx|{b}|{q}", lambda: fetch_frankfurter(b, q), "frankfurter")
    if kind == "crypto":
        _, c = spec
        return _cached_fetch(f"crypto|{c}", lambda: fetch_coingecko(c), "coingecko")
    if kind == "temp":
        _, lat, lon, nm = spec
        return _cached_fetch(f"temp|{nm}", lambda: fetch_openmeteo(lat, lon, nm), "openmeteo")
    if kind == "stock":
        _, t, p = spec
        return fetch_cached(t, p, "1d")
    return _fallback("unknown real spec")


def fetch_stooq(symbol: str = "^spx", period: str = "5y") -> dict:
    """
    Stooq — CSV رسمیِ رایگان (بدونِ کلید). منبعِ اختیاریِ کمکی؛ در fetch_real
    استفاده نمی‌شود چون Stooq اغلب anti-bot دارد و Yahoo/Frankfurter/… پوشش می‌دهند.

    symbol مثال‌ها: aapl.us، ^spx (S&P500)، btcusd، eurusd، xauusd (طلا).
    خروجی: log-returnهای روزانه.
    """
    try:
        import requests
        import numpy as np
        url = f"https://stooq.com/q/d/l/?s={symbol}&i=d"
        resp = _requests_get(url, timeout=20,
                            headers={"User-Agent": "Mozilla/5.0 (4d_system research)"})
        text = resp.text or ""
        if resp.status_code != 200 or not text.strip() or text.lstrip().startswith("<"):
            return _fallback(f"stooq: no data for {symbol}")
        lines = text.strip().splitlines()
        if len(lines) < 30 or not lines[0].lower().startswith("date"):
            return _fallback(f"stooq: bad csv for {symbol}")

        closes = []
        for ln in lines[1:]:
            parts = ln.split(",")
            if len(parts) >= 5:
                try:
                    closes.append(float(parts[4]))   # ستونِ Close
                except ValueError:
                    continue
        close = np.asarray(closes, dtype=float)
        n_map = {"1y": 252, "2y": 504, "5y": 1260, "10y": 2520}
        if period in n_map:
            close = close[-n_map[period]:]
        close = close[close > 0]
        if len(close) < 30:
            return _fallback(f"stooq: too few points for {symbol}")

        returns = np.diff(np.log(close))
        return {
            "series":  returns,
            "label":   f"Stooq: {symbol} ({period} log-returns)",
            "n":       len(returns),
            "source":  "stooq",
            "info":    {"symbol": symbol, "period": period},
        }
    except Exception as e:
        return _fallback(f"stooq error: {e}")


def fetch_stooq_cached(symbol: str = "^spx", period: str = "5y") -> dict:
    """پوششِ اصولیِ Stooq: cache روزانه + throttle (مثلِ fetch_cached)."""
    import numpy as np
    key = f"stooq|{symbol}|{period}|{date.today().isoformat()}"
    cf = _cache_dir() / (hashlib.md5(key.encode("utf-8")).hexdigest() + ".json")

    if cf.exists():
        try:
            d = json.loads(cf.read_text(encoding="utf-8"))
            d["series"] = np.asarray(d["series"], dtype=float)
            d["source"] = "stooq(cache)"
            return d
        except Exception:
            pass

    if _throttled(f"stooq|{symbol}"):
        return _fallback(f"throttled — حداقل {_MIN_LIVE_INTERVAL:.0f}s بین دریافت‌های زنده‌ی همان منبع")

    res = fetch_stooq(symbol, period)
    if res.get("source") == "stooq":
        try:
            payload = {**res, "series": np.asarray(res["series"], dtype=float).tolist()}
            cf.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass
    return res


def fetch_cached(ticker: str = "^GSPC", period: str = "2y",
                 interval: str = "1d") -> dict:
    """
    پوششِ اصولیِ Yahoo Finance:
      • cache روزانه — داده‌ی روزانه در طولِ روز ثابت است، پس دوباره دانلود نمی‌شود.
      • throttle — بیش از یک دریافتِ زنده در هر _MIN_LIVE_INTERVAL ثانیه نمی‌زند
        (وگرنه fallback می‌دهد تا API را نکوبد).
    """
    import numpy as np
    key = f"{ticker}|{period}|{interval}|{date.today().isoformat()}"
    cf = _cache_dir() / (hashlib.md5(key.encode("utf-8")).hexdigest() + ".json")

    # ۱) cache روزانه
    if cf.exists():
        try:
            d = json.loads(cf.read_text(encoding="utf-8"))
            d["series"] = np.asarray(d["series"], dtype=float)
            d["source"] = "yahoo_finance(cache)"
            return d
        except Exception:
            pass

    # ۲) throttle — اگر تازه از همین منبع دریافتِ زنده کرده‌ایم، API را نکوب
    if _throttled(f"yahoo|{ticker}"):
        return _fallback(f"throttled — حداقل {_MIN_LIVE_INTERVAL:.0f}s بین دریافت‌های زنده‌ی همان منبع")

    # ۳) دریافتِ زنده + ذخیره در cache (فقط داده‌ی واقعی)
    res = fetch_yahoo_finance(ticker, period, interval)
    if res.get("source") == "yahoo_finance":
        try:
            payload = {**res, "series": np.asarray(res["series"], dtype=float).tolist()}
            cf.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass
    return res


def _fallback(reason: str) -> dict:
    """Generate a synthetic AR(1) substitute when real data is unavailable.

    B4: seed از reason+زمان مشتق می‌شود — قبلاً seed ثابتِ ۹۹ یعنی «همان» سریِ
    بایت‌به‌بایت یکسان بارها واردِ آمار می‌شد و شمارش‌ها را دوبرابر می‌کرد.
    برچسبِ source صادقانه synthetic_fallback می‌ماند تا از تجمیعِ «داده‌ی
    واقعی» قابلِ‌تفکیک باشد.
    """
    seed = int(hashlib.md5(f"{reason}|{time.time_ns()}".encode("utf-8"))
               .hexdigest()[:8], 16)
    rng = np.random.default_rng(seed)
    n = 2000
    s = np.zeros(n)
    for t in range(1, n):
        s[t] = 0.3 * s[t-1] + rng.normal(0, 0.1)
    return {
        "series":  s,
        "label":   f"[SYNTHETIC FALLBACK] {reason}",
        "n":       n,
        "source":  "synthetic_fallback",
        "info":    {"reason": reason, "fallback": True, "seed": seed},
    }


# Catalog of real-data sources
CATALOG = {
    "S&P 500 daily returns":     lambda: fetch_yahoo_finance("^GSPC", "5y", "1d"),
    "Bitcoin daily returns":     lambda: fetch_yahoo_finance("BTC-USD", "3y", "1d"),
    "Apple stock returns":       lambda: fetch_yahoo_finance("AAPL", "5y", "1d"),
    "Tesla stock returns":       lambda: fetch_yahoo_finance("TSLA", "3y", "1d"),
    "NOAA Chicago temp":         lambda: fetch_noaa_temperature(),
}


def generate(name: str) -> dict:
    """Fetch by catalog name."""
    return CATALOG[name]()


if __name__ == "__main__":
    print("=== Testing real data sources ===\n")
    for name in ["S&P 500 daily returns", "Bitcoin daily returns"]:
        result = generate(name)
        series = result["series"]
        print(f"{name}")
        print(f"  label: {result['label']}")
        print(f"  source: {result['source']}")
        print(f"  n={len(series)}  mean={series.mean():+.6f}  "
              f"var={series.var():.6f}  lag1_ac={np.corrcoef(series[:-1], series[1:])[0,1]:+.4f}")
        print()
