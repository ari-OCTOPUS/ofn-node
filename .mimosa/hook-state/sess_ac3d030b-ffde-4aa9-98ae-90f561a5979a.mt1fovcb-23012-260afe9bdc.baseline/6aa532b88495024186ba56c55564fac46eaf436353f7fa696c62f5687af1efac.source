"""
SENTINEL — universe.py
تعریف رسمی universe: الگوریتم اول، فرضیه دوم، دیتا سوم

اصل: هر کوینی که وارد universe می‌شود باید:
  ۱. یک فیلتر کمی رد کند (الگوریتم، عمر، مارکت‌کپ، premine)
  ۲. یک فرضیه‌ی صریح داشته باشد (چرا این کوین بهتر از میانگین است؟)
  ۳. متادیتا برای ردیابی IC بعداً

فرضیه مانع data-mining کور می‌شود.
اگر IC پایین بود، می‌دانی کدام *فرضیه* اشتباه بود.

نحوه استفاده:
  from universe import UniverseManager, CoinCandidate
  um = UniverseManager()
  candidates = um.screen_from_lc_universe(lc_rows)
  um.print_universe()
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Dict

logger = logging.getLogger(__name__)


# ─── تعریف الگوریتم‌های قابل قبول ────────────────────────
ALLOWED_ALGOS = {
    "RandomX",    # XMR، XEL (DAG-RandomX)
    "Yespower",   # PoW سبک، Pi-friendly
    "Equihash",   # ZEC
    "DPoS",       # CORE (Delegated PoS + BTC staking)
    "PoS",        # TAO، stablecoins
    "Unknown",    # کوین‌هایی که الگوریتمشان ثبت نشده (DIL و دیگران)
}

# ─── فرضیه‌های از پیش تعریف‌شده برای دارایی‌های SENTINEL ─
SENTINEL_HYPOTHESES: Dict[str, str] = {
    "CORE": (
        "BTC-correlated L1 با native BTC staking. سه موتور: ۱) BTC بره ۲۰۰K → CORE "
        "خودبخود بالا. ۲) staking yield از روز اول. ۳) نقدینگی بالا. "
        "سیگنال: social_signal مثبت + macro_regime صعودی (BTC exchange_netflow منفی)."
    ),
    "XEL": (
        "DAG-based privacy chain با RandomX PoW. Catalyst-dependent: listing بزرگ → 5x-8x. "
        "سیگنال: galaxy_score_momentum مثبت + حجم ناگهانی > ۳x میانگین ۷ روزه. "
        "بدون catalyst → sideways. ریسک delisting در regulatory_crackdown."
    ),
    "XMR": (
        "Privacy premium: وقتی regulatory_crackdown در حال ظهور است و "
        "creator_growth در ۷ روز > ۵٪ باشد، XMR رفتار متفاوت از بازار عمومی دارد."
    ),
    "ZEC": (
        "ZEC proxy برای XMR است. سیگنال اصلی: galaxy_score_momentum (مشتق ۱۴ روزه) "
        "مثبت + spam_pct < ۱۰٪. ریسک delisting باید در score تخفیف داشته باشد."
    ),
    "TAO": (
        "Decentralized AI network با subnet ecosystem. AI narrative-driven — social_score "
        "وزن ۵۰٪ دارد. سیگنال: social_signal قوی + subnet growth مثبت. "
        "volatility بالا — DCA با ۳ پله."
    ),
    "DIL": (
        "Quantum-resistant narrative play برای افق ۲۰۳۰. sideways در ۶ ماه محتمل است. "
        "سیگنال اصلی: quantum_threat سناریو + رشد social تدریجی. "
        "ورود زودرس — پله‌های کوچک."
    ),
}


@dataclass
class CoinCandidate:
    """
    یک کوین در universe با فیلتر کمی و فرضیه‌ی کیفی.
    """
    symbol:       str
    name:         str
    algo:         str                   # الگوریتم PoW یا "PoS" یا "Unknown"
    market_cap:   float                 # USD
    age_days:     int                   # روز از لانچ
    premine_pct:  float                 # درصد premine (۰ اگر نامشخص)
    hypothesis:   str                   # فرضیه‌ی صریح — الزامی
    role:         str = "speculative"   # "core" | "satellite" | "speculative" | "watch"
    watch_only:   bool = False
    added_date:   str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    notes:        str = ""

    def is_valid(self) -> tuple[bool, str]:
        """بررسی فیلترهای کمی. برمی‌گرداند (valid, reason)."""
        if not self.hypothesis.strip():
            return False, "فرضیه خالی است — بدون فرضیه، universe مجاز نیست"
        if self.algo not in ALLOWED_ALGOS:
            return False, f"الگوریتم {self.algo} در لیست مجاز نیست"
        if self.premine_pct > 30:
            return False, f"premine {self.premine_pct}٪ بیش از حد بالا است"
        return True, "ok"


class UniverseManager:
    """
    مدیریت universe — تعریف، فیلتر، و ردیابی فرضیه‌ها.
    """

    # ─── فیلترهای پیش‌فرض (قابل تنظیم) ───────────────────
    MIN_MARKET_CAP  = 50_000          # USD — زیر این = بیش از حد کوچک
    MAX_MARKET_CAP  = 50_000_000_000  # USD — بالاتر = large cap مستقر
    MIN_AGE_DAYS    = 90              # کوین‌های خیلی جدید = ریسک بالا
    MAX_PREMINE_PCT = 30.0            # بیش از ۳۰٪ premine مشکوک

    def __init__(self, universe_file: str = "universe.json"):
        self.universe_file = Path(universe_file)
        self._coins: Dict[str, CoinCandidate] = {}
        self._load()

    def _load(self):
        """لود universe از فایل JSON اگر وجود داشت."""
        if self.universe_file.exists():
            try:
                with open(self.universe_file, encoding="utf-8") as f:
                    data = json.load(f)
                for item in data.get("coins", []):
                    c = CoinCandidate(**item)
                    self._coins[c.symbol] = c
                logger.info(f"Universe لود شد: {len(self._coins)} کوین")
            except Exception as e:
                logger.error(f"خواندن universe.json شکست خورد: {e}")

    def save(self):
        """ذخیره‌ی universe در فایل JSON."""
        data = {"coins": [asdict(c) for c in self._coins.values()]}
        with open(self.universe_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"Universe ذخیره شد: {self.universe_file}")

    def add(self, coin: CoinCandidate, force: bool = False) -> bool:
        """
        اضافه کردن یک کوین به universe.
        بدون فرضیه‌ی صریح → رد می‌شود (مگر force=True).
        """
        valid, reason = coin.is_valid()
        if not valid and not force:
            logger.warning(f"رد شد [{coin.symbol}]: {reason}")
            return False
        self._coins[coin.symbol] = coin
        logger.info(f"✅ [{coin.symbol}] به universe اضافه شد: {coin.hypothesis[:60]}...")
        return True

    def remove(self, symbol: str, reason: str = ""):
        """حذف یک کوین از universe."""
        if symbol in self._coins:
            del self._coins[symbol]
            logger.info(f"🗑️ [{symbol}] از universe حذف شد: {reason}")

    def get(self, symbol: str) -> Optional[CoinCandidate]:
        return self._coins.get(symbol)

    def all_active(self) -> List[CoinCandidate]:
        """همه کوین‌های غیر watch_only."""
        return [c for c in self._coins.values() if not c.watch_only]

    def all_symbols(self) -> List[str]:
        return list(self._coins.keys())

    def screen_from_lc_universe(self, lc_rows: List[dict],
                                 min_cap: float = None,
                                 max_cap: float = None) -> List[CoinCandidate]:
        """
        فیلتر کوین‌های LunarCrush universe بر اساس معیارهای کمی.
        برای کشف کاندیدهای جدید — فرضیه باید دستی اضافه شود.
        """
        min_cap = min_cap or self.MIN_MARKET_CAP
        max_cap = max_cap or self.MAX_MARKET_CAP

        candidates = []
        for row in lc_rows:
            sym = row.get("symbol", "")
            cap = row.get("market_cap", 0) or 0
            if not (min_cap <= cap <= max_cap):
                continue
            if sym in self._coins:
                continue  # قبلاً داریم

            c = CoinCandidate(
                symbol=sym,
                name=row.get("name", sym),
                algo="Unknown",       # باید دستی پر شود
                market_cap=cap,
                age_days=0,           # باید دستی پر شود
                premine_pct=0.0,
                hypothesis="⚠️ فرضیه هنوز تعریف نشده — قبل از اضافه کردن به universe الزامی است",
                role="speculative",
                watch_only=True,      # تا فرضیه تعریف نشود: watch_only
            )
            candidates.append(c)

        logger.info(f"screen: {len(candidates)} کاندیدای جدید پیدا شد")
        return candidates

    def print_universe(self):
        """نمایش ساختار universe به‌صورت جدول."""
        print("\n" + "═"*70)
        print("  SENTINEL Universe")
        print("═"*70)
        print(f"  {'Symbol':<10} {'Role':<12} {'Algo':<12} {'MCap($B)':<10} {'Watch':<6}")
        print("  " + "─"*65)
        for sym, c in self._coins.items():
            mcap_b = c.market_cap / 1e9 if c.market_cap else 0
            w = "✓" if c.watch_only else ""
            print(f"  {sym:<10} {c.role:<12} {c.algo:<12} {mcap_b:<10.2f} {w:<6}")
            # فرضیه را کوتاه نشان بده
            hyp_short = c.hypothesis[:65] + "..." if len(c.hypothesis) > 65 else c.hypothesis
            print(f"    ↳ {hyp_short}")
        print("═"*70 + "\n")

    @classmethod
    def build_sentinel_universe(cls, save: bool = True) -> "UniverseManager":
        """
        ساخت universe پایه‌ی SENTINEL از صفر.
        این تابع را یک بار اجرا کن — بعداً از universe.json بارگذاری می‌شود.
        """
        um = cls()

        # ─── دارایی‌های اصلی SENTINEL (نسخه ۲.۰) ───
        core_assets = [
            CoinCandidate(
                symbol="CORE", name="CoreDAO",
                algo="DPoS", market_cap=800_000_000,
                age_days=800, premine_pct=0.0,
                hypothesis=SENTINEL_HYPOTHESES["CORE"],
                role="core",
            ),
            CoinCandidate(
                symbol="XEL", name="Xelis",
                algo="RandomX", market_cap=15_000_000,
                age_days=400, premine_pct=5.0,
                hypothesis=SENTINEL_HYPOTHESES["XEL"],
                role="satellite",
            ),
            CoinCandidate(
                symbol="XMR", name="Monero",
                algo="RandomX", market_cap=3_500_000_000,
                age_days=3700, premine_pct=0.0,
                hypothesis=SENTINEL_HYPOTHESES["XMR"],
                role="satellite",
            ),
            CoinCandidate(
                symbol="ZEC", name="Zcash",
                algo="Equihash", market_cap=510_000_000,
                age_days=2800, premine_pct=10.0,  # Founders' Reward
                hypothesis=SENTINEL_HYPOTHESES["ZEC"],
                role="satellite",
            ),
            CoinCandidate(
                symbol="TAO", name="Bittensor",
                algo="PoS", market_cap=4_000_000_000,
                age_days=800, premine_pct=0.0,
                hypothesis=SENTINEL_HYPOTHESES["TAO"],
                role="satellite",
            ),
            CoinCandidate(
                symbol="DIL", name="Dilithion",
                algo="Unknown", market_cap=5_000_000,
                age_days=300, premine_pct=0.0,
                hypothesis=SENTINEL_HYPOTHESES["DIL"],
                role="speculative",
            ),
            CoinCandidate(
                symbol="USDC", name="USD Coin",
                algo="PoS", market_cap=32_000_000_000,
                age_days=2200, premine_pct=100.0,
                hypothesis="پارکینگ نقدینگی — سیگنال ورود ندارد. نرخ ورود stablecoin به صرافی‌ها سیگنال ماکرو است.",
                role="core",
                watch_only=False,
            ),
            CoinCandidate(
                symbol="USDT", name="Tether",
                algo="PoS", market_cap=113_000_000_000,
                age_days=3600, premine_pct=100.0,
                hypothesis="پارکینگ ثانویه. ریسک counterparty را رصد کن. regulatory_crackdown → USDC جایگزین.",
                role="core",
                watch_only=False,
            ),
        ]

        for coin in core_assets:
            um.add(coin, force=True)  # core assets همیشه قبول می‌شوند

        if save:
            um.save()

        return um
