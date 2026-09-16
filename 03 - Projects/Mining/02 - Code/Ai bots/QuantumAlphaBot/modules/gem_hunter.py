"""
Coin Hunter Bot — Discovery Strategy
=======================================
کشف کوین‌های نوظهور با پتانسیل بقای بلندمدت.

پایپ‌لاین:
  1. HARD FILTERS (cheap, applied first):
     - mcap range [MIN_MARKET_CAP, MAX_MARKET_CAP]
     - blacklist (stock/wrapped/stable tokens)
     - listed on Bybit OR Binance spot (USDT pair)
     - REAL CEX volume ≥ MIN_REAL_VOL_24H  (native /tickers, NOT CG aggregated)
     - age within [MIN_AGE_DAYS, MAX_AGE_DAYS]   (requires detail call)
  2. SCORING (only on survivors):
     - Survival       30%  (premine + github + exchange + distribution)
     - Antifragility  25%  (volatility + recovery + red-day volume)
     - Social (LC)    20%  (galaxy + alt rank + sentiment)
     - Derivatives    15%  (OI growth + funding stability)
     - On-chain (CQ)  10%  (exchange outflow if covered)

Empty result is a valid outcome — no padding, no relaxing filters.
"""
import time
import json
import os
import requests
import pandas as pd
import numpy as np
from datetime import datetime, date
from pathlib import Path
from typing import List, Dict, Optional
from config import CRYPTOQUANT_API, COINALYZE_API, LUNARCRUSH_API


class GemHunter:
    """Coin Hunter Bot — newly-launched, survivable, antifragile coins."""

    CG_BASE  = "https://api.coingecko.com/api/v3"
    BINANCE  = "https://api.binance.com/api/v3"
    BYBIT    = "https://api.bybit.com/v5"
    CQ_BASE  = "https://api.cryptoquant.com/v1"
    LC_BASE  = "https://lunarcrush.com/api4/public"
    COINALYZE_BASE = "https://api.coinalyze.net/v1"

    # ── LunarCrush spam-guard thresholds (Part B) ───────────────────────────
    # Calibrated from OPG/FOGO live data (Jake Signals pump groups, cexscan bots).
    LC_SPAM_RATIO_THRESHOLD = 0.15   # spam/posts_active 7d avg > this → UNRELIABLE
    #   OPG 7d avg = 18.3% (pump-group spike 05-22/23)  → flagged
    #   FOGO 7d avg = 14.8%                             → borderline, caught by PPR
    #   BTC  7d avg = 6–9%                              → clean
    LC_SPAM_PPR_THRESHOLD   = 6.0    # posts_active / contributors_active 3d avg > this → UNRELIABLE
    #   FOGO 3d avg = 8.0 (381–484 posts, 49–56 contributors)  → flagged
    #   OPG  3d avg = 1.8 (507–638 posts, 277–343 contributors) → clean
    #   BTC  3d avg = 2.6                                        → clean
    LC_SERIES_INTERVAL      = "1w"   # time-series window (≈7 daily data points)

    # ── HARD FILTERS (named config constants — easy to tune) ────────────────
    MAX_AGE_DAYS       = 180          # 6 ماه — کمی فضا برای کشف
    MIN_AGE_DAYS       = 14           # حداقل 2 هفته (جلوگیری از fresh rug)
    MIN_MARKET_CAP     = 100_000      # $100K (حذف توکن‌های مرده)
    MAX_MARKET_CAP     = 75_000_000   # $75M (mid-early stage discovery)
    # Liquidity uses REAL native-exchange volume (Bybit/Binance USDT spot),
    # NOT CoinGecko's aggregated total_volume which inflates wash-traded
    # tokens by 3-10x via low-quality aggregated venues. Threshold tuned for
    # genuine early-stage activity while excluding pure ghost markets.
    MIN_REAL_VOL_24H   = 500_000      # $500K real CEX spot turnover (24h)

    # ── محدودیت‌های تحلیل (rate limit) ───────────────────────────────────────
    TOP_N_FOR_DETAIL = 25             # بیشتر = کشف بهتر
    TOP_N_OUTPUT     = 10
    CG_SLEEP_DETAIL  = 4.0            # delay بین detail call ها
    CG_SLEEP_PAGE    = 3.0

    # Disk cache برای جلوگیری از rate-limit بین چرخه‌ها
    CACHE_FILE       = Path("data/coin_hunter_cache.json")
    DETAIL_CACHE     = Path("data/coin_hunter_details.json")
    CACHE_TTL_SEC    = 3600 * 6       # 6 ساعت (طول یه چرخه)
    CACHE_SCHEMA_VER = 5              # Fix A: real-exchange volume gate

    # P5: filter-exit log — individual coin rejections with symbol + reason
    FILTER_EXITS_PATH = Path("data/filter_exits.jsonl")

    # کوین‌های پروکسی stock و wrapped که از crypto نیستن
    BLACKLIST_SUBSTRINGS = [
        "USD", "DAI", "WBTC", "WETH", "STETH", "WBETH",
        "XSTOCK", "X-STOCK",    # tokenized stocks
        "TSLAX", "AAPLX", "GOOGX", "NVDAX", "MSFTX", "CRCLX", "AMZNX",
        "WAVAX", "WSOL", "WMATIC",
    ]

    def __init__(self):
        self._bybit_symbols   = self._fetch_bybit_spot_symbols()
        self._binance_symbols = self._fetch_binance_spot_symbols()
        # Fix A: real per-exchange USDT spot volumes (24h). Replaces CG's
        # aggregated total_volume which inflates wash-traded tokens.
        self._real_volumes    = self._fetch_real_exchange_volumes()
        self._cached_df       = None
        self._detail_cache    = self._load_detail_cache()
        # rejection tracking برای debug + transparency
        self._rejections = self._fresh_rejection_dict()
        self._total_scanned = 0

    @staticmethod
    def _fresh_rejection_dict() -> Dict[str, int]:
        return {
            "blacklist":     0,
            "mcap_low":      0,
            "mcap_high":     0,
            "low_liquidity": 0,
            "not_listed":    0,
            "age_too_old":   0,
            "age_too_new":   0,
            "no_detail":     0,
        }

    # P5: Log individual filter exits so coin disappearance is traceable across cycles
    def _log_filter_exit(self, symbol: str, reason: str, detail: str = "") -> None:
        """Append one exit record to data/filter_exits.jsonl."""
        try:
            self.FILTER_EXITS_PATH.parent.mkdir(parents=True, exist_ok=True)
            record = {
                "ts":     datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "symbol": symbol,
                "reason": reason,
                "detail": detail,
            }
            with open(self.FILTER_EXITS_PATH, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(record, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"  [CoinHunter] filter_exit log error: {e}")

    def filter_settings_str(self) -> str:
        """خلاصه فیلترها برای هر گزارش"""
        return (f"Filters: age ≤ {self.MAX_AGE_DAYS}d | "
                f"mcap ${self.MIN_MARKET_CAP/1e6:.2f}M–"
                f"${self.MAX_MARKET_CAP/1e6:.0f}M | "
                f"real CEX vol ≥ ${self.MIN_REAL_VOL_24H/1e3:.0f}K")

    def rejection_summary(self) -> str:
        """رشته یک‌خطی برای نمایش دلیل ردها"""
        labels = [
            ("age_too_old",   "too old"),
            ("mcap_high",     "over mcap cap"),
            ("mcap_low",      "under mcap floor"),
            ("low_liquidity", "low liquidity"),
            ("not_listed",    "not on Bybit/Binance"),
            ("age_too_new",   "too new"),
            ("blacklist",     "stock/wrapped/stable"),
            ("no_detail",     "no detail data"),
        ]
        parts = []
        for key, label in labels:
            n = self._rejections.get(key, 0)
            if n > 0:
                parts.append(f"{n} {label}")
        return ", ".join(parts) if parts else "none"

    # ── Disk cache helpers ───────────────────────────────────────────────────

    def _load_disk_cache(self) -> Optional[pd.DataFrame]:
        if not self.CACHE_FILE.exists():
            return None
        try:
            data = json.loads(self.CACHE_FILE.read_text(encoding="utf-8"))
            # invalidate اگه schema تغییر کرده
            if data.get("schema_ver") != self.CACHE_SCHEMA_VER:
                return None
            age = time.time() - data.get("timestamp", 0)
            if age > self.CACHE_TTL_SEC:
                return None
            print(f"  [CoinHunter] Using disk cache (age: {age/60:.0f} min)")
            # cached rejection summary رو هم لود کن
            self._rejections    = data.get("rejections", self._fresh_rejection_dict())
            self._total_scanned = data.get("scanned", 0)
            return pd.DataFrame(data["records"])
        except Exception:
            return None

    def _save_disk_cache(self, df: pd.DataFrame):
        try:
            self.CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
            self.CACHE_FILE.write_text(json.dumps({
                "schema_ver": self.CACHE_SCHEMA_VER,
                "timestamp":  time.time(),
                "rejections": self._rejections,
                "scanned":    self._total_scanned,
                "records":    df.to_dict(orient="records"),
            }, ensure_ascii=False), encoding="utf-8")
        except Exception as e:
            print(f"  [CoinHunter cache save] {e}")

    def _load_detail_cache(self) -> Dict:
        if not self.DETAIL_CACHE.exists():
            return {}
        try:
            data = json.loads(self.DETAIL_CACHE.read_text(encoding="utf-8"))
            now = time.time()
            return {k: v for k, v in data.items()
                    if now - v.get("_cached_at", 0) < 24 * 3600}
        except Exception:
            return {}

    def _save_detail_cache(self):
        try:
            self.DETAIL_CACHE.parent.mkdir(parents=True, exist_ok=True)
            self.DETAIL_CACHE.write_text(
                json.dumps(self._detail_cache, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception as e:
            print(f"  [CoinHunter detail-cache save] {e}")

    # ── Exchange listings ────────────────────────────────────────────────────

    def _fetch_bybit_spot_symbols(self) -> set:
        try:
            r = requests.get(f"{self.BYBIT}/market/instruments-info",
                             params={"category": "spot"}, timeout=10)
            return {item["baseCoin"].upper()
                    for item in r.json().get("result", {}).get("list", [])}
        except Exception:
            return set()

    def _fetch_binance_spot_symbols(self) -> set:
        try:
            r = requests.get(f"{self.BINANCE}/exchangeInfo", timeout=10)
            return {s["baseAsset"].upper()
                    for s in r.json().get("symbols", [])
                    if s["status"] == "TRADING" and s["quoteAsset"] == "USDT"}
        except Exception:
            return set()

    def _fetch_real_exchange_volumes(self) -> Dict[str, float]:
        """
        Build {BASE_SYMBOL: max_usd_24h_volume} from NATIVE Bybit + Binance
        spot tickers (USDT pairs only).

        Why this exists (Fix A):
        CoinGecko's `total_volume` aggregates every venue's self-reported
        volume — including known wash-trading exchanges. For micro-caps this
        inflates by 3-10x. Example: ROBO showed $9.3M on CG, real Bybit+
        Binance combined was ~$1.9M. The old MIN_VOL_24H=$150K floor was
        effectively never binding for wash-traded tokens.

        We use exchange-native /tickers (one bulk call per venue) which
        reflect actual order-book turnover. USDT-quoted only — that's where
        real early-stage liquidity sits.

        Returns {} on total failure; per-exchange failures are logged but
        don't break the other side.
        """
        vols: Dict[str, float] = {}

        # ── Bybit: turnover24h = quote-currency (USDT) volume ─────────────
        try:
            r = requests.get(f"{self.BYBIT}/market/tickers",
                             params={"category": "spot"}, timeout=15)
            if r.status_code == 200:
                for t in r.json().get("result", {}).get("list", []):
                    sym = t.get("symbol", "")
                    if sym.endswith("USDT"):
                        base = sym[:-4].upper()
                        try:
                            v = float(t.get("turnover24h", 0) or 0)
                        except (TypeError, ValueError):
                            v = 0.0
                        if v > vols.get(base, 0):
                            vols[base] = v
        except Exception as e:
            print(f"  [CoinHunter] Bybit volume fetch failed: {e}")

        # ── Binance: quoteVolume = quote-currency (USDT) volume ───────────
        try:
            r = requests.get(f"{self.BINANCE}/ticker/24hr", timeout=20)
            if r.status_code == 200:
                for t in r.json():
                    sym = t.get("symbol", "")
                    if sym.endswith("USDT"):
                        base = sym[:-4].upper()
                        try:
                            v = float(t.get("quoteVolume", 0) or 0)
                        except (TypeError, ValueError):
                            v = 0.0
                        if v > vols.get(base, 0):
                            vols[base] = v
        except Exception as e:
            print(f"  [CoinHunter] Binance volume fetch failed: {e}")

        print(f"  [CoinHunter] Real-volume map: {len(vols)} USDT pairs loaded")
        return vols

    # ── CoinGecko ────────────────────────────────────────────────────────────

    def _fetch_low_cap_coins(self) -> List[Dict]:
        """
        صفحه‌های 3-10 از CoinGecko (rank ~200-1000) = جایی که
        کوین‌های $150K-$75M هستن. صفحه 3 برای $75M ceiling اضافه شد.
        """
        all_coins = []
        for page in [3, 4, 5, 6, 7, 8, 9, 10]:
            try:
                r = requests.get(
                    f"{self.CG_BASE}/coins/markets",
                    params={
                        "vs_currency": "usd",
                        "order":       "market_cap_desc",
                        "per_page":    100,
                        "page":        page,
                        "sparkline":   "false",
                        "price_change_percentage": "24h,7d,30d",
                    },
                    timeout=20,
                )
                if r.status_code == 429:
                    print(f"    [CG page {page}] 429 rate-limit — waiting 30s")
                    time.sleep(30)
                    continue
                r.raise_for_status()
                all_coins.extend(r.json())
                time.sleep(self.CG_SLEEP_PAGE)
            except Exception as e:
                print(f"    [CG page {page}] {e}")
        return all_coins

    def _fetch_coin_detail(self, coin_id: str, retries: int = 2) -> Optional[Dict]:
        """جزئیات یک کوین + cache + retry روی 429"""
        # 1. اول از cache disk بخون
        if coin_id in self._detail_cache:
            return self._detail_cache[coin_id]

        # 2. وگرنه از CG بگیر
        for attempt in range(retries + 1):
            try:
                r = requests.get(
                    f"{self.CG_BASE}/coins/{coin_id}",
                    params={
                        "localization":   "false",
                        "tickers":        "false",
                        "market_data":    "true",
                        "community_data": "false",
                        "developer_data": "true",
                        "sparkline":      "false",
                    },
                    timeout=15,
                )
                if r.status_code == 200:
                    detail = r.json()
                    detail["_cached_at"] = time.time()
                    self._detail_cache[coin_id] = detail
                    return detail
                if r.status_code == 429 and attempt < retries:
                    wait = 15 * (attempt + 1)
                    print(f"      [429 retry in {wait}s]", end=" ")
                    time.sleep(wait)
                    continue
                return None
            except Exception:
                return None
        return None

    # ── FILTER 1: AGE (HARD) ────────────────────────────────────────────────

    def _coin_age_days(self, detail: Dict) -> Optional[int]:
        """سن کوین از genesis_date — None اگه نمی‌دونیم"""
        g = detail.get("genesis_date")
        if g:
            try:
                d = datetime.strptime(g, "%Y-%m-%d").date()
                return (date.today() - d).days
            except Exception:
                pass

        # fallback: اولین ticker date
        last_updated = detail.get("last_updated", "")
        if last_updated:
            # CoinGecko نمی‌ده، ولی genesis_date اگه None باشه یعنی نسبتاً جدیده
            return None
        return None

    # ── FILTER 2: SURVIVAL SCORE (0-100) ────────────────────────────────────

    def _survival_score(self, detail: Dict, coin_market: Dict) -> Dict:
        """نمره بقا 0-100 + اجزای آن"""
        components = {
            "github":       0,   # 30 pts
            "premine":      0,   # 25 pts
            "distribution": 0,   # 25 pts
            "exchange":     0,   # 20 pts
        }

        # ── GitHub activity ───────────────────────────────────────────────
        dev = detail.get("developer_data") or {}
        commits_4w = dev.get("commit_count_4_weeks", 0) or 0
        stars      = dev.get("stars", 0) or 0
        forks      = dev.get("forks", 0) or 0

        gh_score = 0
        if commits_4w >= 20:    gh_score += 15
        elif commits_4w >= 5:   gh_score += 10
        elif commits_4w >= 1:   gh_score += 5
        if stars >= 500:        gh_score += 10
        elif stars >= 100:      gh_score += 7
        elif stars >= 20:       gh_score += 4
        if forks >= 50:         gh_score += 5
        components["github"] = min(30, gh_score)

        # ── Premine (circulating / max supply) ────────────────────────────
        md      = detail.get("market_data") or {}
        circ    = md.get("circulating_supply") or 0
        max_sup = md.get("max_supply") or md.get("total_supply") or 0

        if max_sup and circ:
            ratio = circ / max_sup
            if 0.50 <= ratio <= 0.85:    components["premine"] = 25   # ideal
            elif 0.30 <= ratio < 0.50:   components["premine"] = 15
            elif 0.85 < ratio <= 1.00:   components["premine"] = 10
            else:                        components["premine"] = 5    # خیلی premine
        else:
            components["premine"] = 10   # داده نداریم، neutral

        # ── Distribution (proxy از تعداد holders در CG community_data) ────
        # چون community_data خاموش کردیم، از circulating ratio هم به‌عنوان proxy استفاده می‌کنیم
        # alternative proxy: vol/mcap — اگه خیلی متمرکز بود volume کم نسبی داره
        sym  = coin_market.get("symbol", "").upper()
        vol  = float(coin_market.get("total_volume", 0) or 0)
        mc   = float(coin_market.get("market_cap", 1) or 1)
        v_mc = vol / max(mc, 1)
        if v_mc >= 0.15:    components["distribution"] = 25
        elif v_mc >= 0.08:  components["distribution"] = 18
        elif v_mc >= 0.04:  components["distribution"] = 10
        else:               components["distribution"] = 3

        # ── Exchange presence ─────────────────────────────────────────────
        on_bybit   = sym in self._bybit_symbols
        on_binance = sym in self._binance_symbols
        if on_bybit and on_binance:    components["exchange"] = 20
        elif on_bybit:                 components["exchange"] = 15
        elif on_binance:               components["exchange"] = 12
        else:                          components["exchange"] = 0

        total = sum(components.values())
        return {"score": total, "components": components,
                "on_bybit": on_bybit, "on_binance": on_binance}

    # ── EXTERNAL APIs: LunarCrush + Coinalyze + CryptoQuant ─────────────────

    def _lunarcrush_score(self, symbol: str) -> Dict:
        """
        LunarCrush quality signal: 7-day smoothed galaxy + sentiment (Part B).

        Uses /coins/{symbol}/time-series/v2 (daily, 7-day window) instead of
        the snapshot /v1 endpoint, which only returns galaxy_score + alt_rank
        (sentiment and interactions_24h are absent from the snapshot response).

        Spam guard
        ──────────
        Real OPG/FOGO data showed ~90% of posts were cexscan bots and paid
        pump groups (Jake Signals, irrelevant hashtags). Raw mention volume
        is actively misleading for frontier coins — a rug can look "popular"
        purely from pump-group activity.

        Guard fires when EITHER of these is true over the measurement window:
          spam_ratio_7d > LC_SPAM_RATIO_THRESHOLD (0.15) — spam >15% of posts
          ppc_3d        > LC_SPAM_PPR_THRESHOLD   (6.0)  — >6 posts/contributor
                                                             (bot-like automation)

        When the guard fires: score = 0, lc_unreliable = True.
        VetoEngine's SOCIAL_ZERO rule then applies age-aware handling:
          age < 90d → soft flag (same as LunarCrush indexing lag for new coins)
          age ≥ 90d → hard veto (established coin with no legitimate social)
        This makes spam non-rewarding without creating a new veto rule.

        Scoring (quality-only, no raw volume components)
        ──────────────────────────────────────────────────
          galaxy_7d_avg  ≥70→+40  ≥50→+25  ≥30→+10
          alt_rank_7d_avg ≤100→+25  ≤500→+15  ≤1000→+5
          sentiment_7d_avg (0-100 scale) ≥80→+20  ≥65→+10
          NO interactions/volume component (spam-prone, removed)
          Maximum: 85 pts

        Fields returned
        ───────────────
          score, available, galaxy_score (7d avg), alt_rank (7d avg),
          sentiment (7d avg, 0-100), lc_unreliable, lc_spam_ratio,
          lc_posts_per_contributor
        """
        if not LUNARCRUSH_API:
            return {"score": 0, "available": False}
        try:
            r = requests.get(
                f"{self.LC_BASE}/coins/{symbol.lower()}/time-series/v2",
                headers={"Authorization": f"Bearer {LUNARCRUSH_API}"},
                params={"bucket": "day", "interval": self.LC_SERIES_INTERVAL},
                timeout=15,
            )
            if r.status_code != 200:
                return {"score": 0, "available": False,
                        "reason": f"HTTP {r.status_code}"}

            pts = r.json().get("data") or []
            if not pts:
                return {"score": 0, "available": False, "reason": "empty_timeseries"}

            def _f(v, default=0.0): return float(v or default)
            def _avg(lst): return sum(lst) / max(len(lst), 1)

            # ── 7-day averages ────────────────────────────────────────────
            galaxy_7d    = _avg([_f(p.get("galaxy_score"))    for p in pts])

            # Galaxy-zero guard: galaxy_score = 0 means LunarCrush doesn't
            # independently track this coin (or the symbol maps to a different
            # token — e.g. "BASED" resolves to a popular meme coin, not ours).
            # Sentiment from zero-galaxy data is symbol-collision noise.
            if galaxy_7d < 1.0:
                return {"score": 0, "available": False,
                        "reason": "galaxy_zero_untracked"}
            alt_rank_7d  = _avg([_f(p.get("alt_rank"), 9999)  for p in pts])
            sentiment_7d = _avg([_f(p.get("sentiment"))       for p in pts])

            # ── Spam metrics ──────────────────────────────────────────────
            spam_ratios = [
                _f(p.get("spam")) / max(_f(p.get("posts_active")), 1)
                for p in pts
            ]
            spam_ratio_7d = _avg(spam_ratios)

            # Posts-per-contributor: 3-day window (most recent activity)
            recent = pts[-min(3, len(pts)):]
            ppc_3d = _avg([
                _f(p.get("posts_active")) / max(_f(p.get("contributors_active")), 1)
                for p in recent
            ])

            base = {
                "available":               True,
                "galaxy_score":            round(galaxy_7d, 1),    # 7d avg
                "alt_rank":                int(alt_rank_7d),        # 7d avg
                "sentiment":               round(sentiment_7d, 1),  # 7d avg, 0-100
                "lc_unreliable":           False,
                "lc_spam_ratio":           round(spam_ratio_7d, 3),
                "lc_posts_per_contributor": round(ppc_3d, 1),
            }

            # ── Spam guard ────────────────────────────────────────────────
            unreliable = (
                spam_ratio_7d > self.LC_SPAM_RATIO_THRESHOLD
                or ppc_3d     > self.LC_SPAM_PPR_THRESHOLD
            )
            if unreliable:
                base["score"]        = 0
                base["lc_unreliable"] = True
                return base

            # ── Quality scoring (no raw volume/interactions component) ────
            sc = 0
            if galaxy_7d >= 70:      sc += 40
            elif galaxy_7d >= 50:    sc += 25
            elif galaxy_7d >= 30:    sc += 10
            if alt_rank_7d <= 100:   sc += 25
            elif alt_rank_7d <= 500: sc += 15
            elif alt_rank_7d <= 1000: sc += 5
            # Sentiment on 0-100 scale (time-series; snapshot uses different scale)
            if sentiment_7d >= 80:   sc += 20
            elif sentiment_7d >= 65: sc += 10

            base["score"] = sc
            return base

        except Exception as e:
            return {"score": 0, "available": False, "reason": str(e)[:50]}

    def _coinalyze_derivatives(self, symbol: str) -> Dict:
        """
        Coinalyze: OI growth + funding stability برای کوین‌های جدید
        خروجی: {"score": 0-100, "oi_change_30d": ..., "funding_avg": ...}
        """
        if not COINALYZE_API:
            return {"score": 0, "available": False}
        try:
            sym     = f"{symbol}USDT_PERP.A"
            now     = int(time.time())
            from_ts = now - 30 * 86400

            # 1. OI history
            r1 = requests.get(
                f"{self.COINALYZE_BASE}/open-interest-history",
                params={"symbols": sym, "interval": "daily",
                        "from": from_ts, "to": now, "api_key": COINALYZE_API},
                timeout=10,
            )
            if r1.status_code != 200:
                return {"score": 0, "available": False}
            d1 = r1.json()
            if not d1:
                return {"score": 0, "available": False, "reason": "no_perp"}
            oi_hist = d1[0].get("history", [])
            if len(oi_hist) < 7:
                return {"score": 0, "available": False, "reason": "short_history"}

            old_oi = float(oi_hist[0].get("c", 0) or 0)
            new_oi = float(oi_hist[-1].get("c", 0) or 0)
            oi_change_pct = (new_oi - old_oi) / max(old_oi, 1) * 100

            # 2. Funding history
            r2 = requests.get(
                f"{self.COINALYZE_BASE}/funding-rate-history",
                params={"symbols": sym, "interval": "daily",
                        "from": from_ts, "to": now, "api_key": COINALYZE_API},
                timeout=10,
            )
            funds = []
            if r2.status_code == 200 and r2.json():
                fh = r2.json()[0].get("history", [])
                funds = [float(f.get("r", 0)) for f in fh[-30:]]

            funding_avg = float(np.mean(funds)) * 10_000 if funds else 0    # bps
            funding_std = float(np.std(funds)) * 10_000 if funds else 0     # bps

            # امتیاز Antifragile-relevant:
            sc = 0
            # OI رشد سالم (50%-300%) = پذیرش سریع توسط traderها
            if 50 <= oi_change_pct <= 300:    sc += 40
            elif 20 <= oi_change_pct < 50:    sc += 25
            elif 300 < oi_change_pct <= 500:  sc += 20    # خیلی hot
            elif 0 < oi_change_pct < 20:      sc += 10

            # Funding نزدیک صفر = سالم
            if abs(funding_avg) <= 5:    sc += 30
            elif abs(funding_avg) <= 15: sc += 15

            # Funding stability (پایین = bumpy نیست)
            if funding_std <= 10:    sc += 30
            elif funding_std <= 30:  sc += 15

            return {
                "score":          sc,
                "available":      True,
                "oi_change_30d":  round(oi_change_pct, 1),
                "funding_avg_bp": round(funding_avg, 2),
                "funding_std_bp": round(funding_std, 2),
            }
        except Exception as e:
            return {"score": 0, "available": False, "reason": str(e)[:50]}

    def _cryptoquant_onchain(self, symbol: str) -> Dict:
        """
        CryptoQuant: exchange-flow برای کوین‌های جدید
        پلن $100 معمولاً فقط BTC/ETH رو می‌ده.
        """
        if not CRYPTOQUANT_API:
            return {"score": 0, "available": False}
        try:
            r = requests.get(
                f"{self.CQ_BASE}/{symbol.lower()}/exchange-flows/netflow",
                headers={"Authorization": f"Bearer {CRYPTOQUANT_API}"},
                params={"window": "day", "limit": 14, "exchange": "all_exchange"},
                timeout=10,
            )
            if r.status_code in (400, 402, 403, 404):
                return {"score": 0, "available": False, "reason": "no_coverage"}
            r.raise_for_status()
            data = r.json().get("result", {}).get("data", [])
            if len(data) < 7:
                return {"score": 0, "available": False}

            # netflow منفی = خروج از صرافی = انباشت
            vals = [float(d.get("netflow_total", 0) or 0) for d in data[-7:]]
            avg_outflow = -float(np.mean(vals))   # positive = outflow

            sc = 0
            if avg_outflow > 1000:    sc += 50    # outflow قوی
            elif avg_outflow > 100:   sc += 30
            elif avg_outflow > 0:     sc += 15
            elif avg_outflow > -100:  sc += 5     # نوسانی

            return {"score": sc, "available": True,
                    "avg_outflow_7d": round(avg_outflow, 1)}
        except Exception:
            return {"score": 0, "available": False}

    def _cryptoquant_macro_signal(self) -> Dict:
        """
        BTC exchange-flow = سیگنال سلامت کلی بازار (یه بار در هر چرخه).

        اشتراک $100 CryptoQuant فقط BTC/ETH رو پوشش می‌ده.
        ولی BTC netflow بهترین پروکسی برای وضعیت ماکرو کریپتوه:
          منفی (outflow) = BTC از صرافی‌ها خارج می‌شه = accumulation = بهتر برای altcoin
          مثبت (inflow)  = BTC به صرافی‌ها وارد می‌شه = distribution = ریسک بالاتر

        Returns: {"score": 0-100, "trend": "ACCUMULATING|NEUTRAL|DISTRIBUTING",
                  "avg_14d": BTC, "available": bool}
        """
        if not CRYPTOQUANT_API:
            return {"score": 50, "available": False, "trend": "UNKNOWN",
                    "avg_14d": 0, "recent_3d": 0}
        try:
            r = requests.get(
                f"{self.CQ_BASE}/btc/exchange-flows/netflow",
                headers={"Authorization": f"Bearer {CRYPTOQUANT_API}"},
                params={"window": "day", "limit": 14, "exchange": "all_exchange"},
                timeout=10,
            )
            if r.status_code != 200:
                return {"score": 50, "available": False, "trend": "UNKNOWN",
                        "avg_14d": 0, "recent_3d": 0}
            data = r.json().get("result", {}).get("data", [])
            if not data:
                return {"score": 50, "available": False, "trend": "UNKNOWN",
                        "avg_14d": 0, "recent_3d": 0}

            vals     = [float(d.get("netflow_total", 0) or 0) for d in data[-14:]]
            avg_14d  = float(np.mean(vals))
            recent3  = float(np.mean([float(d.get("netflow_total", 0) or 0)
                                      for d in data[-3:]]))

            # امتیاز: خروج از صرافی = سالم‌تر
            if avg_14d < -5000:    sc = 90
            elif avg_14d < -1000:  sc = 75
            elif avg_14d < -200:   sc = 62
            elif avg_14d < 200:    sc = 50   # خنثی
            elif avg_14d < 1000:   sc = 35
            else:                  sc = 20   # توزیع قوی = محتاط باش

            trend = ("ACCUMULATING" if recent3 < -500 else
                     "DISTRIBUTING" if recent3 > 500  else "NEUTRAL")

            return {
                "score":     sc,
                "available": True,
                "trend":     trend,
                "avg_14d":   round(avg_14d, 0),
                "recent_3d": round(recent3, 0),
            }
        except Exception as e:
            return {"score": 50, "available": False, "trend": "UNKNOWN",
                    "avg_14d": 0, "recent_3d": 0, "reason": str(e)[:60]}

    # ── FILTER 3: ANTIFRAGILITY (Taleb) ─────────────────────────────────────

    def _antifragility_score(self, symbol: str) -> Dict:
        """
        کوین‌هایی که از نوسان منفعت می‌برن.
        اول Binance، اگه نبود (Bybit-only) از Bybit می‌گیره.
        """
        closes = volumes = None

        # ── Binance klines ─────────────────────────────────────────────────────
        try:
            r = requests.get(
                f"{self.BINANCE}/klines",
                params={"symbol": f"{symbol}USDT",
                        "interval": "1d", "limit": 60},
                timeout=10,
            )
            if r.status_code == 200:
                klines = r.json()
                if len(klines) >= 20:
                    closes  = np.array([float(k[4]) for k in klines])
                    volumes = np.array([float(k[5]) for k in klines])
        except Exception:
            pass

        # ── Bybit fallback (Bybit-only کوین‌ها) ─────────────────────────────
        if closes is None:
            try:
                r = requests.get(
                    f"{self.BYBIT}/market/kline",
                    params={"category": "spot", "symbol": f"{symbol}USDT",
                            "interval": "D", "limit": "60"},
                    timeout=10,
                )
                if r.status_code == 200:
                    items = list(reversed(
                        r.json().get("result", {}).get("list", [])
                    ))  # Bybit newest-first → reverse
                    if len(items) >= 20:
                        closes  = np.array([float(k[4]) for k in items])
                        volumes = np.array([float(k[5]) for k in items])
            except Exception:
                pass

        if closes is None:
            return {"score": 0, "max_dd": 0, "reason": "no_kline_data",
                    "components": {"vol_pts": 0, "recovery_pts": 0, "red_vol_pts": 0}}

        return self._calc_antifragility(closes, volumes)

    def _calc_antifragility(self, closes: np.ndarray, volumes: np.ndarray) -> Dict:
        """محاسبه امتیاز antifragility از time-series (close, volume)."""
        # 1. Volatility (می‌خوایم زیاد باشه) — 30 pts
        returns = np.diff(closes) / closes[:-1]
        vol = float(np.std(returns))
        if vol >= 0.10:    vol_score = 30
        elif vol >= 0.05:  vol_score = 20
        elif vol >= 0.03:  vol_score = 10
        else:              vol_score = 0

        # 2. Drawdown + Recovery — 40 pts
        # P2 FIX: Added partial-recovery tiers so score does not cliff-drop to 0
        # when a coin has partially recovered but not yet crossed the full threshold.
        # Original formula only rewarded near-complete recoveries, causing systematic
        # negative score drift as coins aged past launch with incomplete recoveries.
        peak       = np.maximum.accumulate(closes)
        drawdowns  = (closes - peak) / peak
        max_dd     = float(drawdowns.min())
        current_dd = float(drawdowns[-1])
        recovery_score = 0
        if max_dd <= -0.30:               # severe dump
            if current_dd >= -0.10:       # near-full recovery
                recovery_score = 40
            elif current_dd >= -0.20:     # strong recovery
                recovery_score = 25
            elif current_dd >= -0.35:     # partial recovery (was 0 before fix)
                recovery_score = 12
            elif current_dd >= -0.50:     # early recovery (stopped worsening)
                recovery_score = 5
        elif max_dd <= -0.20:
            if current_dd >= -0.05:       # near-full recovery
                recovery_score = 25
            elif current_dd >= -0.10:     # strong recovery
                recovery_score = 15
            elif current_dd >= -0.20:     # partial recovery (was 0 before fix)
                recovery_score = 7
        elif max_dd <= -0.10:
            if current_dd >= -0.03:       # near-full recovery
                recovery_score = 10
            elif current_dd >= -0.08:     # partial recovery (was 0 before fix)
                recovery_score = 4

        # 3. Volume on red days vs green days — 30 pts
        red_vols, green_vols = [], []
        for i in range(1, len(closes)):
            if closes[i] < closes[i-1]:
                red_vols.append(volumes[i])
            else:
                green_vols.append(volumes[i])
        red_score = 0
        if red_vols and green_vols:
            ratio = np.mean(red_vols) / max(np.mean(green_vols), 1)
            if ratio >= 1.30:     red_score = 30   # حجم سنگین روزهای قرمز
            elif ratio >= 1.10:   red_score = 20
            elif ratio >= 0.90:   red_score = 10
            else:                 red_score = 0

        total = vol_score + recovery_score + red_score
        return {
            "score":         total,
            "volatility":    round(vol, 3),
            "max_dd":        round(max_dd * 100, 1),
            "current_dd":    round(current_dd * 100, 1),
            "components": {
                "vol_pts":       vol_score,
                "recovery_pts":  recovery_score,
                "red_vol_pts":   red_score,
            },
        }

    # ── Main Hunt ────────────────────────────────────────────────────────────

    def find_gems(self) -> pd.DataFrame:
        # 1. memory cache
        if self._cached_df is not None:
            return self._cached_df

        # 2. disk cache (TTL 6h)
        disk = self._load_disk_cache()
        if disk is not None:
            self._cached_df = disk
            return disk

        # 3. Fresh hunt — reset trackers
        self._rejections = self._fresh_rejection_dict()
        self._total_scanned = 0

        # Header: همیشه فیلترهای فعال رو نشون بده
        print(f"  [CoinHunter] {self.filter_settings_str()}")
        print("  [CoinHunter] Phase 1: fetching low-cap candidates...")
        coins = self._fetch_low_cap_coins()
        self._total_scanned = len(coins)
        if not coins:
            print("  [CoinHunter] 0 coins fetched from CoinGecko (API issue).")
            return pd.DataFrame()

        # ── PHASE 1: cheap hard filters (no API calls, with rejection counting) ──
        pre_filtered = []
        for c in coins:
            mc   = float(c.get("market_cap", 0) or 0)
            vol  = float(c.get("total_volume", 0) or 0)
            sym  = c.get("symbol", "").upper()
            name = c.get("name", "").lower()

            # (a) Blacklist (stock/wrapped/stable) — اول، چون cheap‌ترینه
            if any(x in sym for x in self.BLACKLIST_SUBSTRINGS):
                self._rejections["blacklist"] += 1
                continue
            if "xstock" in name or "stock" in name:
                self._rejections["blacklist"] += 1
                continue

            # (b) Market cap floor و ceiling
            if mc < self.MIN_MARKET_CAP:
                self._rejections["mcap_low"] += 1
                continue
            if mc > self.MAX_MARKET_CAP:
                self._rejections["mcap_high"] += 1
                continue

            # (c) Listing check FIRST — must be on Bybit or Binance USDT spot
            #     so the real-volume lookup has a chance of returning data
            if sym not in self._bybit_symbols and sym not in self._binance_symbols:
                self._rejections["not_listed"] += 1
                continue

            # (d) REAL liquidity floor (Bybit/Binance native, NOT CG-aggregated).
            #     Fix A: the old gate compared CG's total_volume (which can be
            #     5-10x inflated by wash-trading venues) against a $150K floor.
            #     This gate uses turnover24h / quoteVolume directly from the
            #     exchange APIs — what the actual order book is doing.
            real_vol = self._real_volumes.get(sym, 0)
            if real_vol < self.MIN_REAL_VOL_24H:
                self._rejections["low_liquidity"] += 1
                continue

            # Attach real volume to the dict so Phase 2 + results can use it
            c["_real_vol_24h"] = real_vol
            pre_filtered.append(c)

        print(f"  [CoinHunter] Phase 1 survivors: {len(pre_filtered)} / "
              f"{self._total_scanned} candidates")

        if not pre_filtered:
            # هیچ کوینی از pre-filter نگذشت — اینم یه نتیجه معتبره
            self._cached_df = pd.DataFrame()
            self._save_disk_cache(pd.DataFrame())
            return pd.DataFrame()

        # ── CryptoQuant BTC macro signal (یه بار per run، قبل از Phase 2) ────
        print("  [CoinHunter] CryptoQuant BTC macro signal...")
        macro_cq = self._cryptoquant_macro_signal()
        if macro_cq.get("available"):
            print(f"  [CoinHunter] CQ BTC → {macro_cq['trend']} "
                  f"| 14d avg: {macro_cq['avg_14d']:+.0f} BTC "
                  f"| 3d avg: {macro_cq['recent_3d']:+.0f} BTC "
                  f"| macro score: {macro_cq['score']}")
        else:
            print("  [CoinHunter] CQ BTC macro: not available (neutral 50)")

        # Top N for deep analysis — sort by ATH recency first (newer ATH = likely new coin)
        # then vol/mcap as tiebreaker so actively-traded new coins come first
        def _ath_age(c: Dict) -> int:
            s = c.get("ath_date", "")
            if s:
                try:
                    return (date.today() -
                            datetime.strptime(s[:10], "%Y-%m-%d").date()).days
                except Exception:
                    pass
            return 9999

        pre_filtered.sort(key=lambda c: (
            _ath_age(c),                                               # اول: جدیدترین ATH
            -(float(c.get("total_volume", 0) or 0)                    # بعد: بالاترین vol/mcap
              / max(float(c.get("market_cap", 1) or 1), 1)),
        ))
        candidates = pre_filtered[:self.TOP_N_FOR_DETAIL]

        # ── PHASE 2: age check (requires detail call) + scoring ─────────────
        print(f"  [CoinHunter] Phase 2: age+score on top {len(candidates)}...")
        results = []
        for i, c in enumerate(candidates):
            coin_id = c["id"]
            sym     = c["symbol"].upper()
            print(f"    [{i+1}/{len(candidates)}] {sym}...", end=" ")

            detail = self._fetch_coin_detail(coin_id)
            time.sleep(self.CG_SLEEP_DETAIL)
            if detail is None:
                self._rejections["no_detail"] += 1
                print("no detail")
                # P5: log exit so disappearances are traceable across cycles
                self._log_filter_exit(sym, "no_detail", "CoinGecko detail call returned None")
                continue

            # AGE check (HARD filter)
            age = self._coin_age_days(detail)
            if age is None:
                md = detail.get("market_data") or {}
                ath_date = (md.get("ath_date") or {}).get("usd")
                if ath_date:
                    try:
                        d = datetime.strptime(ath_date[:10], "%Y-%m-%d").date()
                        age = (date.today() - d).days
                    except Exception:
                        age = None
            if age is None:
                self._rejections["no_detail"] += 1
                print("age unknown")
                self._log_filter_exit(sym, "age_unknown", "genesis_date and ath_date both missing")
                continue
            if age > self.MAX_AGE_DAYS:
                self._rejections["age_too_old"] += 1
                print(f"age={age}d — too old")
                # P5: log so we know WHEN a coin crossed the age ceiling
                self._log_filter_exit(sym, "age_too_old",
                                      f"age={age}d > MAX_AGE_DAYS={self.MAX_AGE_DAYS}")
                continue
            if age < self.MIN_AGE_DAYS:
                self._rejections["age_too_new"] += 1
                print(f"age={age}d — too new")
                self._log_filter_exit(sym, "age_too_new",
                                      f"age={age}d < MIN_AGE_DAYS={self.MIN_AGE_DAYS}")
                continue

            # SURVIVAL score (premine + github + distribution + exchange)
            surv = self._survival_score(detail, c)

            # ANTIFRAGILITY score (vol + recovery + red-day volume)
            anti = self._antifragility_score(sym)

            # ─── External paid APIs ─────────────────────────────────────────
            lc  = self._lunarcrush_score(sym)             # LunarCrush social
            cq  = self._cryptoquant_onchain(sym)          # CQ per-coin (BTC/ETH)
            cal = self._coinalyze_derivatives(sym)        # Coinalyze derivatives

            # ── Scoring weights (Phase 4.3 revised) ──────────────────────────────
            # derivs_score (perp OI/funding) demoted from 0.13→0.07 for altcoins.
            # Rationale: perp OI is a speculation signal, not a survival signal.
            # In the survival-accumulation thesis, a coin's ability to survive drawdowns
            # (antifragility) and maintain exchange presence (survival) are primary.
            # High OI drove ICNT (surv=37.9, social=MISSING) to final=43 above
            # coins with better survival fundamentals — inverting the thesis priority.
            # The freed 0.06 weight redistributes to survival (0.04) and antifragility (0.02).
            # Calibration: ICNT final drops from 43.1 → ~37 (surv=37.9 correctly drags);
            # OPG (surv=52, anti=49) relative rank improves vs deriv-heavy coins.
            #
            # Weight table (altcoins, no CQ per-coin data):
            #   surv   0.34  (was 0.30) — primary survival signal
            #   anti   0.27  (was 0.25) — recovery/antifragility
            #   lc     0.20  (was 0.20) — social (redistributed away if MISSING)
            #   cal    0.07  (was 0.14) — derivatives (halved — speculation signal)
            #   macro  0.12  (was 0.11) — BTC macro regime
            #   cq     0.00  (no per-coin CQ for altcoins)

            if cq.get("available"):
                # BTC/ETH with per-coin CQ data — original weights preserved
                w_surv, w_anti, w_lc, w_cal, w_cq, w_macro = 0.28, 0.23, 0.18, 0.13, 0.08, 0.10
            else:
                # Altcoins: Phase 4.3 revised weights
                w_surv  = 0.34
                w_anti  = 0.27
                w_lc    = 0.20
                w_cal   = 0.07  # derivs demoted: speculation signal, not survival
                w_cq    = 0.0
                w_macro = 0.12

            # P1 FIX: When LunarCrush data unavailable (coin not indexed — common for
            # early-stage tokens <90d), redistribute the social weight proportionally
            # to the other available components instead of penalising the coin with a
            # guaranteed 0 contribution on a 20%-weight signal.
            # lc_unreliable=True (spam guard fired) still gets score=0 deliberately.
            if not lc.get("available", False):
                _lc_w = w_lc
                _rest  = w_surv + w_anti + w_cal + w_cq + w_macro
                if _rest > 0:
                    _scale = (_rest + _lc_w) / _rest
                    w_surv  = round(w_surv  * _scale, 6)
                    w_anti  = round(w_anti  * _scale, 6)
                    w_cal   = round(w_cal   * _scale, 6)
                    w_cq    = round(w_cq    * _scale, 6)
                    w_macro = round(w_macro * _scale, 6)
                w_lc = 0.0

            final_score = (
                surv["score"]       * w_surv +
                anti["score"]       * w_anti +
                lc["score"]         * w_lc +
                cal["score"]        * w_cal +
                cq["score"]         * w_cq +
                macro_cq["score"]   * w_macro
            )

            results.append({
                "symbol":         sym,
                "name":           c.get("name", ""),
                "age_days":       age,
                "market_cap":     float(c.get("market_cap", 0) or 0),
                "volume_24h":     float(c.get("total_volume", 0) or 0),     # CG aggregated (kept for comparison)
                "real_vol_24h":   float(c.get("_real_vol_24h", 0) or 0),    # Fix A: native Bybit/Binance USDT spot
                "vol_mcap_pct":   round(float(c.get("total_volume", 0) or 0)
                                        / max(float(c.get("market_cap", 1) or 1), 1) * 100, 1),
                "price_7d_pct":   round(float(c.get("price_change_percentage_7d_in_currency", 0) or 0), 1),
                "price_30d_pct":  round(float(c.get("price_change_percentage_30d_in_currency", 0) or 0), 1),
                "survival_score": round(surv["score"], 1),
                "antifragile":    round(anti["score"], 1),
                "social_score":        round(lc["score"], 1),
                "social_contribution": round(lc["score"] * w_lc, 2),  # pts social added to final_score
                # P-A tri-state: MEASURED / MISSING / UNRELIABLE
                # VetoEngine reads this before firing SOCIAL_ZERO
                "social_status": (
                    "MISSING"     if not lc.get("available", False) and not lc.get("lc_unreliable", False)
                    else "UNRELIABLE" if lc.get("lc_unreliable", False)
                    else "MEASURED"
                ),
                "derivs_score":   round(cal["score"], 1),
                "onchain_score":  round(cq["score"], 1),
                "final_score":    round(final_score, 1),
                "github_pts":     surv["components"]["github"],
                "premine_pts":    surv["components"]["premine"],
                "distrib_pts":    surv["components"]["distribution"],
                "exchange_pts":   surv["components"]["exchange"],
                "max_dd_pct":     anti.get("max_dd", 0),
                "volatility":     anti.get("volatility", 0),
                "lc_galaxy":             lc.get("galaxy_score", 0),
                "lc_rank":              lc.get("alt_rank", 0),
                "lc_available":         lc.get("available", False),
                "lc_sentiment":         lc.get("sentiment", 0.0),
                "lc_spam_ratio":        lc.get("lc_spam_ratio", 0.0),
                "lc_posts_per_contrib": lc.get("lc_posts_per_contributor", 0.0),
                "lc_unreliable":        lc.get("lc_unreliable", False),
                "oi_change_30d":  cal.get("oi_change_30d", 0),
                "funding_bp":     cal.get("funding_avg_bp", 0),
                "cal_available":  cal.get("available", False),
                "cq_outflow":     cq.get("avg_outflow_7d", 0),
                "cq_available":   cq.get("available", False),
                # ── CryptoQuant macro (BTC market health) ──────────────────
                "macro_cq_score": round(macro_cq["score"], 1),
                "btc_trend":      macro_cq.get("trend", "UNKNOWN"),
                "btc_avg14d":     macro_cq.get("avg_14d", 0),
                # ── Asset type (set to UNKNOWN here; ScoutForensics refines) ──
                "asset_type":     "UNKNOWN",
                "on_bybit":       surv["on_bybit"],
                "on_binance":     surv["on_binance"],
            })
            srcs = []
            if lc.get("available"):          srcs.append("LC")
            if cal.get("available"):         srcs.append("CAL")
            if cq.get("available"):          srcs.append("CQ")
            if macro_cq.get("available"):    srcs.append("CQmacro")
            src_str = "+".join(srcs) if srcs else "none"
            print(f"age={age}d  surv={surv['score']:.0f}  "
                  f"anti={anti['score']:.0f}  social={lc['score']:.0f}  "
                  f"deriv={cal['score']:.0f}  macro={macro_cq['score']:.0f}  "
                  f"final={final_score:.0f}  [{src_str}]")

        # Empty result handling
        if not results:
            empty = pd.DataFrame()
            self._cached_df = empty
            self._save_disk_cache(empty)
            self._save_detail_cache()
            return empty

        df = pd.DataFrame(results).sort_values("final_score", ascending=False)
        result = df.head(self.TOP_N_OUTPUT).reset_index(drop=True)
        self._cached_df = result
        self._save_disk_cache(result)
        self._save_detail_cache()
        return result

    # ── Reporting helpers ─────────────────────────────────────────────────────

    def last_rejections(self) -> Dict[str, int]:
        return dict(self._rejections)

    def last_scanned_count(self) -> int:
        return self._total_scanned
