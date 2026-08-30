"""
SENTINEL — sector_scanner.py
رصد ۵ حوزه‌ی رشدی: Privacy، DePIN، RWA، Oracle/Infrastructure، AI

این ماژول فقط رصد و سیگنال‌دهی است.
هیچ‌چیزی در تخصیص سرمایه، منطق ریسک، یا ساختار barbell تغییر نمی‌کند.

جریان اجرا برای هر کوین:
  CoinCandidate.is_valid() → sector_filter() → EntryScorer(sector_signals) → SignalFusion

نکات طراحی:
  - هیچ API key جدیدی لازم نیست
  - DefiLlama بدون کلید (رایگان)
  - graceful degradation در همه‌ی لایه‌ها
  - SENTINEL_MOCK_MODE=1 کاملاً پشتیبانی می‌شود
  - XMR/ZEC که در universe موجودند اینجا تکرار نمی‌شوند

نحوه استفاده:
  from sector_scanner import SectorScanner
  scanner = SectorScanner(cfg, lc_client, cq_client, data_store)
  results = scanner.scan_all()
  # results: List[SectorResult]
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import requests

logger = logging.getLogger(__name__)

# ─── تعریف حوزه‌ها ───────────────────────────────────────────
KNOWN_SECTORS = ("Privacy", "DePIN", "RWA", "Oracle", "AI")

# آستانه‌های فیلتر ورود
FILTER_MIN_VOLUME_24H  = 500_000     # USD
FILTER_MIN_MARKET_CAP  = 10_000_000  # USD
FILTER_MIN_AGE_DAYS    = 90

# ─── ثابت‌های DefiLlama ─────────────────────────────────────
DEFILLAMA_BASE       = "https://api.llama.fi"
DEFILLAMA_TIMEOUT    = 10           # ثانیه
DEFILLAMA_MIN_TVL    = 1_000_000   # USD — TVL زیر این = بی‌ربط
DEFILLAMA_NORM_TVL   = 500_000_000 # USD — TVL معادل امتیاز ۱۰۰


# ═══════════════════════════════════════════════════════════════
#  ساختار نتیجه
# ═══════════════════════════════════════════════════════════════
@dataclass
class SectorResult:
    timestamp:       int
    symbol:          str
    sector:          str
    entry_score:     Optional[float]   # 0-100 از EntryScorer
    label:           str               # strong_entry / moderate / weak / watch_only
    quadrant:        str               # DEPLOY / ACCUMULATE / WAIT / TRAP / ...
    kelly_frac:      float
    score_modifier:  float
    late_entry_risk: bool
    late_entry_pct:  Optional[float]   # ٪ رشد ۱۴ روزه اگر > 40٪
    data_notes:      List[str] = field(default_factory=list)
    conviction:      str = ""


# ═══════════════════════════════════════════════════════════════
#  ۱. فیلتر ورود
# ═══════════════════════════════════════════════════════════════
def sector_filter(coin: dict) -> bool:
    """
    فیلتر کمی برای کوین‌های جدید حوزه‌ای.
    مکمل CoinCandidate.is_valid() است، نه جایگزین آن.
    ترتیب اجرا: ابتدا CoinCandidate.is_valid()، سپس این تابع.

    Quantitative filter for new sector coins.
    Complements CoinCandidate.is_valid() — not a replacement.

    Returns:
        True  = کوین از فیلتر رد شد و می‌تواند امتیاز بگیرد
        False = رد شد (لاگ می‌شود)
    """
    symbol = coin.get("symbol", "UNKNOWN")

    # ─── volume ───
    vol = coin.get("volume_24h")
    if vol is None:
        logger.debug(f"[filter] {symbol}: volume_24h موجود نیست → رد")
        return False
    if vol < FILTER_MIN_VOLUME_24H:
        logger.debug(f"[filter] {symbol}: volume_24h={vol:,.0f} < {FILTER_MIN_VOLUME_24H:,} → رد")
        return False

    # ─── market cap ───
    cap = coin.get("market_cap")
    if cap is None:
        logger.debug(f"[filter] {symbol}: market_cap موجود نیست → رد")
        return False
    if cap < FILTER_MIN_MARKET_CAP:
        logger.debug(f"[filter] {symbol}: market_cap={cap:,.0f} < {FILTER_MIN_MARKET_CAP:,} → رد")
        return False

    # ─── age ───
    age = coin.get("age_days")
    if age is None:
        logger.debug(f"[filter] {symbol}: age_days موجود نیست → رد")
        return False
    if age < FILTER_MIN_AGE_DAYS:
        logger.debug(f"[filter] {symbol}: age_days={age} < {FILTER_MIN_AGE_DAYS} → رد")
        return False

    return True


# ═══════════════════════════════════════════════════════════════
#  ۲. کلاینت DefiLlama (بدون API key — رایگان)
# ═══════════════════════════════════════════════════════════════
class DefiLlamaClient:
    """
    کلاینت ساده برای DefiLlama API.
    بدون کلید API — همه‌ی endpoint‌ها عمومی هستند.
    فقط برای TVL دارایی‌های RWA استفاده می‌شود.

    Simple client for DefiLlama public API (no key required).
    Used only for RWA TVL data.
    """

    def __init__(self, mock_mode: bool = False):
        self.mock_mode = mock_mode
        self._cache: Dict[str, float] = {}

    def get_protocol_tvl(self, protocol_slug: str) -> Optional[float]:
        """
        TVL یک پروتکل را برمی‌گرداند (USD).
        protocol_slug: نام slug در DefiLlama (مثلاً "ondo-finance")

        Returns TVL in USD, or None on failure.
        """
        if self.mock_mode:
            # داده‌ی mock برای تست
            mock_tvl = {
                "ondo-finance":   350_000_000,
                "maple-finance":  180_000_000,
                "centrifuge":     120_000_000,
                "goldfinch":       80_000_000,
            }
            tvl = mock_tvl.get(protocol_slug, 50_000_000)
            logger.debug(f"[DefiLlama mock] {protocol_slug}: TVL={tvl:,.0f}")
            return float(tvl)

        if protocol_slug in self._cache:
            return self._cache[protocol_slug]

        try:
            url = f"{DEFILLAMA_BASE}/tvl/{protocol_slug}"
            resp = requests.get(url, timeout=DEFILLAMA_TIMEOUT)
            resp.raise_for_status()
            tvl = float(resp.json())
            self._cache[protocol_slug] = tvl
            logger.debug(f"[DefiLlama] {protocol_slug}: TVL={tvl:,.0f}")
            return tvl
        except Exception as e:
            logger.warning(f"[DefiLlama] {protocol_slug} شکست خورد: {e}")
            return None

    def tvl_to_score(self, tvl: Optional[float]) -> Optional[float]:
        """
        TVL را به امتیاز ۰–۱۰۰ تبدیل می‌کند.
        DEFILLAMA_NORM_TVL USD → امتیاز ۱۰۰
        زیر DEFILLAMA_MIN_TVL → None (بی‌ربط)

        Converts TVL to a 0-100 score.
        """
        if tvl is None or tvl < DEFILLAMA_MIN_TVL:
            return None
        import math
        # log-scale: TVL از 1M تا 500M → 0 تا 100
        score = min(100.0, math.log10(tvl / DEFILLAMA_MIN_TVL) /
                    math.log10(DEFILLAMA_NORM_TVL / DEFILLAMA_MIN_TVL) * 100)
        return round(score, 1)


# ═══════════════════════════════════════════════════════════════
#  ۳. کلاس اصلی SectorScanner
# ═══════════════════════════════════════════════════════════════
class SectorScanner:
    """
    رصد ۵ حوزه‌ی رشدی و تولید سیگنال برای هر کوین.

    ادغام با SENTINEL:
      - universe.py: CoinCandidate.is_valid() اجرا می‌شود
      - scorer.py: EntryScorer.score(sector_signals=...) صدا زده می‌شود
      - signal_fusion.py: SignalFusion.compute() خروجی تولید می‌کند
      - data_store.py: نتایج در sector_signals.parquet ذخیره می‌شوند

    Integrates with SENTINEL's existing pipeline — no standalone scoring.
    """

    def __init__(self, config: dict, lc_client=None, cq_client=None, data_store=None):
        self.cfg     = config
        self.lc      = lc_client
        self.cq      = cq_client
        self.ds      = data_store
        self.mock    = bool(os.getenv("SENTINEL_MOCK_MODE")) or (
            lc_client is not None and getattr(lc_client, "mock_mode", False)
        )
        self.defillama = DefiLlamaClient(mock_mode=self.mock)
        self._max_coins = config.get("max_active_sector_coins", 20)

    # ─── لیست کوین‌های هر حوزه از config ───────────────────────
    def _sector_coins(self) -> Dict[str, List[dict]]:
        """
        لیست کوین‌ها را از config.yaml می‌خواند.
        ساختار: sectors → Privacy/DePIN/... → [{"symbol":...,"market_cap":...}]

        Returns dict of sector → list of coin dicts from config.
        """
        raw = self.cfg.get("sectors", {})
        result: Dict[str, List[dict]] = {}
        for sector in KNOWN_SECTORS:
            coins = raw.get(sector, [])
            if isinstance(coins, list):
                result[sector] = coins
            else:
                result[sector] = []
        return result

    # ─── محدودیت سخت‌افزاری ─────────────────────────────────────
    def _apply_cap(self, all_coins: List[tuple]) -> List[tuple]:
        """
        اگر تعداد کوین‌ها از max_active_sector_coins بیشتر شد،
        فقط پرحجم‌ترین‌ها نگه می‌دارد.

        (sector, coin_dict) tuples → pruned list
        """
        if len(all_coins) <= self._max_coins:
            return all_coins

        sorted_coins = sorted(
            all_coins,
            key=lambda x: x[1].get("volume_24h", 0) or 0,
            reverse=True,
        )
        skipped = len(all_coins) - self._max_coins
        logger.warning(
            f"exceeded max_active_sector_coins ({self._max_coins}): "
            f"{skipped} کوین skip شد. فقط پرحجم‌ترین‌ها رصد می‌شوند."
        )
        return sorted_coins[: self._max_coins]

    # ─── تشخیص late entry risk ──────────────────────────────────
    @staticmethod
    def _check_late_entry(coin: dict) -> tuple[bool, Optional[float]]:
        """
        بررسی رشد ۱۴ روزه.
        Returns: (is_late_entry, gain_14d_as_fraction)
        """
        gain = coin.get("gain_14d") or coin.get("price_change_14d")
        if gain is None:
            return False, None
        # اگر به‌صورت درصد آمده (مثلاً ۴۵.۳)
        if abs(gain) > 3:   # احتمالاً درصده نه fraction
            gain = gain / 100.0
        if gain > 0.40:
            return True, round(gain, 4)
        return False, None

    # ─── LunarCrush social signal برای یک symbol ────────────────
    def _get_social(self, symbol: str) -> tuple[Optional[float], List[str]]:
        """
        social_signal [-1,+1] را از LunarCrush می‌گیرد.
        Returns: (social_signal, notes)
        """
        notes = []
        if self.lc is None:
            notes.append("LunarCrush client موجود نیست — social بدون داده")
            return None, notes
        try:
            sig = self.lc.compute_social_signal(symbol)
            return sig, notes
        except Exception as e:
            logger.warning(f"[sector] social_signal {symbol}: {e}")
            notes.append(f"LunarCrush شکست خورد برای {symbol} — social=None")
            return None, notes

    # ─── امتیازدهی sector-specific ──────────────────────────────
    def _build_sector_signals(self, sector: str, coin: dict) -> dict:
        """
        سیگنال‌های اختصاصی هر حوزه را می‌سازد.
        خروجی: dict که به EntryScorer.score(sector_signals=...) پاس می‌شود.

        Builds sector-specific signals dict for EntryScorer.
        """
        notes = []
        result: dict = {"sector": sector, "data_notes": notes}

        # ─── Late entry risk ───
        late, gain = self._check_late_entry(coin)
        result["gain_14d"] = coin.get("gain_14d") or coin.get("price_change_14d")
        result["late_entry_risk"] = late
        result["late_entry_pct"] = gain

        # ─── RWA: TVL از DefiLlama ───
        if sector == "RWA":
            protocol_slug = coin.get("defillama_protocol")
            if protocol_slug:
                tvl = self.defillama.get_protocol_tvl(protocol_slug)
                tvl_score = self.defillama.tvl_to_score(tvl)
                result["tvl_usd"]   = tvl
                result["tvl_score"] = tvl_score
                if tvl_score is None:
                    notes.append("TVL زیر حداقل یا نامعلوم — امتیاز TVL حذف شد")
            else:
                result["tvl_score"] = None
                notes.append(
                    "defillama_protocol در config تعریف نشده — "
                    "RWA فقط با social سیگنال می‌دهد"
                )

        # ─── DePIN: داده‌ی استفاده‌ی واقعی ───
        elif sector == "DePIN":
            usage = coin.get("active_nodes") or coin.get("active_devices")
            if usage is not None:
                # نرمال‌سازی: ۱۰۰۰ نود → ۵۰ امتیاز
                import math
                usage_score = min(100.0, math.log10(max(usage, 1)) / 3 * 100)
                result["usage_score"] = round(usage_score, 1)
            else:
                result["usage_score"] = None
                notes.append(
                    "داده‌ی استفاده‌ی واقعی (active_nodes/devices) موجود نیست "
                    "— DePIN فقط با social سیگنال می‌دهد"
                )

        # ─── AI: social-heavy — نیازی به داده‌ی اضافه نیست ───
        elif sector == "AI":
            notes.append("AI: social-heavy — وزن Galaxy Score بالاتر اعمال می‌شود")

        # ─── Oracle/Infra: CryptoQuant اگر موجود بود ───
        elif sector == "Oracle":
            # اکثر Oracle coinها (LINK, BAND) داده‌ی CryptoQuant دارند
            # اما برای symbol‌های ناشناخته graceful degrade می‌کنیم
            notes.append(
                "Oracle: on-chain از CryptoQuant اگر موجود باشد "
                "در EntryScorer لحاظ می‌شود"
            )

        # ─── Privacy جدید (نه XMR/ZEC که در universe موجودند) ───
        elif sector == "Privacy":
            notes.append("Privacy جدید — XMR/ZEC در universe اصلی رصد می‌شوند")

        return result

    # ─── وزن‌های sector از config ───────────────────────────────
    def _sector_weights(self, sector: str) -> Optional[dict]:
        """
        وزن‌های اختصاصی sector را از config می‌خواند.
        اگر تعریف نشده بود → None (EntryScorer از پیش‌فرض استفاده می‌کند)
        """
        return (
            self.cfg.get("scoring_weights", {})
                    .get("sectors", {})
                    .get(sector)
        )

    # ─── اجرای scan برای یک کوین ────────────────────────────────
    def _scan_coin(self, sector: str, coin: dict) -> Optional[SectorResult]:
        """
        pipeline کامل برای یک کوین یک حوزه.

        Full pipeline for a single sector coin:
        1. CoinCandidate.is_valid()
        2. sector_filter()
        3. build_sector_signals()
        4. EntryScorer.score()
        5. SignalFusion.compute()

        Returns SectorResult or None if filtered out.
        """
        from universe import CoinCandidate, ALLOWED_ALGOS
        from scorer import EntryScorer
        from signal_fusion import SignalFusion

        symbol = coin.get("symbol", "UNKNOWN")

        # ─── مرحله ۱: CoinCandidate.is_valid() ───
        candidate = CoinCandidate(
            symbol      = symbol,
            name        = coin.get("name", symbol),
            algo        = coin.get("algo", "Unknown"),
            market_cap  = coin.get("market_cap", 0) or 0,
            age_days    = coin.get("age_days", 0) or 0,
            premine_pct = coin.get("premine_pct", 0) or 0,
            hypothesis  = coin.get("hypothesis", ""),
        )
        valid, reason = candidate.is_valid()
        if not valid:
            logger.info(f"[sector] {symbol} رد شد توسط CoinCandidate: {reason}")
            return None

        # ─── مرحله ۲: sector_filter() ───
        if not sector_filter(coin):
            return None

        # ─── مرحله ۳: سیگنال‌های اختصاصی ───
        sec_signals = self._build_sector_signals(sector, coin)
        notes = sec_signals.get("data_notes", [])

        # ─── مرحله ۴: EntryScorer ───
        scorer = EntryScorer(self.cfg)

        # ساخت market_data مینیمال از داده‌های coin
        social_val, social_notes = self._get_social(symbol)
        notes.extend(social_notes)

        price_14d_gain = sec_signals.get("gain_14d")
        market_data = {
            "price": {
                "price":                 coin.get("price", 0),
                "drawdown_from_90d_high": coin.get("drawdown_from_90d_high", 0.1),
                "ma50":                  coin.get("ma50"),
                "ma200":                 coin.get("ma200"),
                "gain_14d":              price_14d_gain,
            },
            "fear_greed":     None,   # Fear&Greed برای کل بازار نه کوین خاص
            "social":         {"sentiment": 0.5 + (social_val or 0) * 0.3,
                               "galaxy_score": coin.get("galaxy_score", 50)}
                              if social_val is not None else None,
            "onchain":        None,   # فقط BTC/ETH در CryptoQuant دارند
            "available_signals": ["social"] if social_val is not None else [],
        }

        # وزن‌های sector اگر در config بود
        weights_override = self._sector_weights(sector)
        if weights_override:
            # موقتاً scoring_weights.XMR_ZEC را override می‌کنیم
            # (sector coins همان مسیر limited را طی می‌کنند)
            original = self.cfg["scoring_weights"].get("XMR_ZEC", {})
            self.cfg["scoring_weights"]["XMR_ZEC"] = weights_override
            score_result = scorer.score(symbol, market_data, sector_signals=sec_signals)
            self.cfg["scoring_weights"]["XMR_ZEC"] = original
        else:
            score_result = scorer.score(symbol, market_data, sector_signals=sec_signals)

        entry_score = score_result.get("score")
        label       = score_result.get("label", "watch_only")
        late_risk   = score_result.get("late_entry_risk", False)
        late_pct    = score_result.get("late_entry_pct")

        # ─── مرحله ۵: SignalFusion ───
        fusion = SignalFusion(self.lc, None)   # cq=None برای sector coins
        fusion_result = fusion.compute(symbol)

        return SectorResult(
            timestamp       = int(time.time()),
            symbol          = symbol,
            sector          = sector,
            entry_score     = entry_score,
            label           = label,
            quadrant        = fusion_result.quadrant,
            kelly_frac      = fusion_result.kelly_frac,
            score_modifier  = fusion_result.score_modifier,
            late_entry_risk = late_risk,
            late_entry_pct  = round(late_pct * 100, 1) if late_pct else None,
            data_notes      = notes,
            conviction      = fusion_result.conviction,
        )

    # ─── اجرای کامل همه‌ی حوزه‌ها ──────────────────────────────
    def scan_all(self) -> List[SectorResult]:
        """
        رصد همه‌ی حوزه‌ها و همه‌ی کوین‌های تعریف‌شده در config.

        Scans all sectors and coins defined in config.yaml → sectors.
        Returns list of SectorResult for storage and Telegram.
        """
        sector_coins = self._sector_coins()
        all_pairs: List[tuple] = []
        for sector, coins in sector_coins.items():
            for coin in coins:
                if isinstance(coin, str):
                    # کاربر فقط symbol نوشته بود
                    coin = {"symbol": coin}
                all_pairs.append((sector, coin))

        if not all_pairs:
            logger.info("[sector] هیچ کوینی در sectors تعریف نشده — scan رد شد")
            return []

        # ─── اعمال سقف سخت‌افزاری ───
        all_pairs = self._apply_cap(all_pairs)

        results = []
        for sector, coin in all_pairs:
            sym = coin.get("symbol", "?")
            try:
                r = self._scan_coin(sector, coin)
                if r:
                    results.append(r)
                    logger.info(
                        f"[sector] {sym} ({sector}): "
                        f"{r.label} {r.entry_score} | {r.quadrant}"
                        + (f" ⚠️ LATE ENTRY +{r.late_entry_pct:.0f}%" if r.late_entry_risk else "")
                    )
            except Exception as e:
                logger.error(f"[sector] {sym} خطا: {e}", exc_info=True)

        logger.info(f"[sector] scan کامل: {len(results)} نتیجه")
        return results

    # ─── تبدیل به records برای DataStore ────────────────────────
    @staticmethod
    def to_records(results: List[SectorResult]) -> List[dict]:
        """
        تبدیل SectorResult به dict برای ذخیره‌ی Parquet.

        Converts SectorResult list to dicts for DataStore.append().
        """
        return [
            {
                "timestamp":       r.timestamp,
                "symbol":          r.symbol,
                "sector":          r.sector,
                "entry_score":     r.entry_score,
                "label":           r.label,
                "quadrant":        r.quadrant,
                "kelly_frac":      r.kelly_frac,
                "score_modifier":  r.score_modifier,
                "late_entry_risk": r.late_entry_risk,
                "late_entry_pct":  r.late_entry_pct,
                "data_notes":      " | ".join(r.data_notes),
                "conviction":      r.conviction[:200] if r.conviction else "",
            }
            for r in results
        ]

    # ─── فرمت Telegram ──────────────────────────────────────────
    @staticmethod
    def format_telegram(results: List[SectorResult]) -> str:
        """
        پیام Telegram برای سیگنال‌های sector.

        Telegram message for sector signals.
        """
        if not results:
            return ""

        QUADRANT_EMOJI = {
            "DEPLOY": "🚀", "ACCUMULATE": "⭐",
            "WAIT": "⏳", "TRAP": "⚠️", "NEUTRAL": "➡️",
        }
        LABEL_EMOJI = {
            "strong_entry": "🟢", "moderate_entry": "🟡",
            "weak_entry": "🟠", "watch_only": "🔴",
        }

        lines = ["📡 <b>Sector Scan — رصد حوزه‌های رشدی</b>\n"]

        by_sector: Dict[str, List[SectorResult]] = {}
        for r in results:
            by_sector.setdefault(r.sector, []).append(r)

        for sector, coins in by_sector.items():
            lines.append(f"\n<b>{sector}</b>")
            for r in sorted(coins, key=lambda x: x.entry_score or 0, reverse=True):
                q_emoji = QUADRANT_EMOJI.get(r.quadrant, "❓")
                l_emoji = LABEL_EMOJI.get(r.label, "⚪")
                score_str = f"{r.entry_score:.0f}" if r.entry_score else "—"
                late_str = f" ⚠️ LATE ENTRY +{r.late_entry_pct:.0f}%" if r.late_entry_risk and r.late_entry_pct else ""
                lines.append(
                    f"  {l_emoji} <b>{r.symbol}</b>  {score_str}/100"
                    f"  {q_emoji}{r.quadrant}{late_str}"
                )
                if r.data_notes:
                    for note in r.data_notes[:2]:   # حداکثر ۲ یادداشت
                        lines.append(f"    <i>ℹ️ {note}</i>")

        lines.append(
            "\n<i>این رصد صرفاً اطلاعاتی است — "
            "تخصیص سرمایه تغییر نمی‌کند</i>"
        )
        return "\n".join(lines)


# ─── اجرای مستقیم: تست mock ─────────────────────────────────
if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))

    os.environ["SENTINEL_MOCK_MODE"] = "1"

    import yaml
    from lc_client import LunarCrushClient
    from cq_client import CryptoQuantClient
    from data_store import DataStore

    cfg_path = Path(__file__).parent / "config.yaml"
    with open(cfg_path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    # ─── چند کوین نمونه برای تست ───
    cfg["sectors"] = {
        "AI": [
            {
                "symbol": "FET", "name": "Fetch.ai",
                "algo": "Unknown", "age_days": 1800,
                "market_cap": 3_200_000_000, "volume_24h": 80_000_000,
                "premine_pct": 15.0,
                "hypothesis": "AI narrative overflow از هوش مصنوعی سنتی به crypto می‌آید",
                "price": 2.1, "drawdown_from_90d_high": 0.38,
                "galaxy_score": 62, "gain_14d": 0.55,   # ← LATE ENTRY TEST
            },
            {
                "symbol": "JUNK", "name": "Junk Coin",
                "algo": "Unknown", "age_days": 30,
                "market_cap": 500_000, "volume_24h": 10_000,  # ← باید رد شود
                "premine_pct": 5.0,
                "hypothesis": "test",
                "price": 0.001,
            },
        ],
        "RWA": [
            {
                "symbol": "ONDO", "name": "Ondo Finance",
                "algo": "Unknown", "age_days": 600,
                "market_cap": 1_400_000_000, "volume_24h": 45_000_000,
                "premine_pct": 20.0,
                "hypothesis": "RWA tokenization: اگر TVL بالای 100M باشد، adoption واقعی دارد",
                "defillama_protocol": "ondo-finance",
                "price": 1.08, "drawdown_from_90d_high": 0.22,
            },
        ],
        "DePIN": [
            {
                "symbol": "HNT", "name": "Helium",
                "algo": "Unknown", "age_days": 2200,
                "market_cap": 820_000_000, "volume_24h": 18_000_000,
                "premine_pct": 0.0,
                "hypothesis": "DePIN: اگر active_nodes رشد کند و قیمت هنوز از قله فاصله دارد",
                "active_nodes": 50_000,
                "price": 5.4, "drawdown_from_90d_high": 0.44,
            },
        ],
    }

    lc = LunarCrushClient(api_key="", mock_mode=True)
    cq = CryptoQuantClient(api_key="", mock_mode=True)
    ds = DataStore(base_dir="/tmp/sentinel_sector_test")

    scanner = SectorScanner(cfg, lc, cq, ds)
    results = scanner.scan_all()

    print("\n" + "="*60)
    print("نتایج Sector Scan (mock)")
    print("="*60)
    for r in results:
        late = f" ⚠️ LATE +{r.late_entry_pct:.0f}%" if r.late_entry_risk else ""
        print(f"  {r.symbol:<8} [{r.sector:<8}] {r.label:<15} "
              f"{r.quadrant:<20} score={r.entry_score}{late}")
        for n in r.data_notes:
            print(f"    ℹ️ {n}")

    print()
    print(SectorScanner.format_telegram(results))
    print()
    print("✅ sector_scanner آماده")
