"""
SENTINEL — signal_fusion.py
ادغام social_signal × macro_regime → ماتریس ۲×۲ + Kelly coefficient

دو متغیر:
  social_signal  ∈ [-1, +1]  از LunarCrush (lc_client.compute_social_signal)
  macro_regime   ∈ [-1, +1]  از CryptoQuant (cq_client.compute_macro_regime)

ماتریس ۲×۲:
                  social < 0 (quiet)     social > 0 (hot)
  macro > 0  │  ACCUMULATE ⭐⭐⭐⭐    │  DEPLOY ⭐⭐⭐⭐⭐  │
  (risk-on)  │  پول وارد، هنوز هایپ نیست │  بالاترین conviction    │
  ───────────┼──────────────────────────┼────────────────────────│
  macro < 0  │  WAIT ⭐⭐             │  TRAP ⚠️              │
  (risk-off) │  ماندن روی ماین           │  احتمال قله، نخر       │

Kelly coefficient:
  ACCUMULATE: kelly_frac = 0.6  (نزدیک‌ترین به سقف بدون هایپ)
  DEPLOY:     kelly_frac = 0.8  (اوج conviction)
  WAIT:       kelly_frac = 0.2
  TRAP:       kelly_frac = 0.0  (نخر)

نحوه استفاده:
  from signal_fusion import SignalFusion, FusionResult
  from lc_client import LunarCrushClient
  from cq_client import CryptoQuantClient

  lc = LunarCrushClient(mock_mode=True)
  cq = CryptoQuantClient(mock_mode=True)
  fusion = SignalFusion(lc, cq)

  result = fusion.compute("CORE")
  print(result.quadrant, result.kelly_frac, result.score_modifier)
"""

import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class FusionResult:
    symbol:          str
    social_signal:   Optional[float]   # -1..+1
    macro_regime:    Optional[float]   # -1..+1
    quadrant:        str               # ACCUMULATE | DEPLOY | WAIT | TRAP
    kelly_frac:      float             # 0..1
    score_modifier:  float             # امتیازی که به SENTINEL scorer اضافه می‌شود
    conviction:      str               # توضیح فارسی/انگلیسی برای سیگنال تلگرام
    timestamp:       Optional[int]     # unix timestamp محاسبه


class SignalFusion:
    """
    ماتریس fusion signal برای ترکیب LunarCrush + CryptoQuant.
    """

    # آستانه‌های تقسیم‌بندی ماتریس
    SOCIAL_THRESHOLD  = 0.05   # نزدیک به صفر = خنثی
    REGIME_THRESHOLD  = 0.05

    # حداکثر تأثیر بر امتیاز SENTINEL (در کنار Big Scenarios)
    MAX_SCORE_MODIFIER = 12.0

    def __init__(self, lc_client=None, cq_client=None):
        self.lc = lc_client
        self.cq = cq_client

    def compute(self, symbol: str) -> FusionResult:
        """
        محاسبه‌ی کامل fusion برای یک symbol.
        اگر یک کلاینت None بود، فقط از آن دیگری استفاده می‌کند.
        """
        import time as _time

        social = None
        if self.lc is not None:
            try:
                social = self.lc.compute_social_signal(symbol)
            except Exception as e:
                logger.warning(f"social_signal برای {symbol} شکست خورد: {e}")

        macro = None
        if self.cq is not None:
            try:
                macro = self.cq.compute_macro_regime(symbol)
            except Exception as e:
                logger.warning(f"macro_regime برای {symbol} شکست خورد: {e}")

        quadrant, kelly, modifier, conviction = self._classify(social, macro, symbol)

        return FusionResult(
            symbol=symbol,
            social_signal=social,
            macro_regime=macro,
            quadrant=quadrant,
            kelly_frac=kelly,
            score_modifier=modifier,
            conviction=conviction,
            timestamp=int(_time.time()),
        )

    def _classify(self, social: Optional[float], macro: Optional[float],
                  symbol: str) -> tuple:
        """
        تعیین quadrant و پارامترهای مربوطه.
        اگر یک سیگنال None باشد، از سیگنال دیگر با وزن کاهش‌یافته استفاده می‌کند.
        """
        # ─── هر دو None → نمی‌توانیم fusion کنیم ───
        if social is None and macro is None:
            return ("UNKNOWN", 0.3, 0.0,
                    "هر دو API در دسترس نیستند — امتیاز بدون تعدیل fusion")

        # ─── فقط یکی موجود است ───
        if social is None:
            # فقط macro
            if macro > self.REGIME_THRESHOLD:
                return ("MACRO_ONLY_BULL", 0.5, +self.MAX_SCORE_MODIFIER * 0.5 * macro,
                        f"Risk-on (فقط داده ماکرو) — macro={macro:+.2f}")
            else:
                return ("MACRO_ONLY_BEAR", 0.2, self.MAX_SCORE_MODIFIER * 0.5 * macro,
                        f"Risk-off (فقط داده ماکرو) — macro={macro:+.2f}")

        if macro is None:
            # فقط social
            if social > self.SOCIAL_THRESHOLD:
                return ("SOCIAL_ONLY_HOT", 0.4, +self.MAX_SCORE_MODIFIER * 0.4 * social,
                        f"Social گرم (فقط LunarCrush) — social={social:+.2f}")
            else:
                return ("SOCIAL_ONLY_QUIET", 0.35, 0.0,
                        f"Social آرام (فقط LunarCrush) — social={social:+.2f}")

        # ─── هر دو موجود → ماتریس ۲×۲ ───
        s_pos = social >  self.SOCIAL_THRESHOLD
        s_neg = social < -self.SOCIAL_THRESHOLD
        m_pos = macro  >  self.REGIME_THRESHOLD
        m_neg = macro  < -self.REGIME_THRESHOLD

        modifier_raw = (0.55 * macro + 0.45 * social) * self.MAX_SCORE_MODIFIER

        if m_pos and not s_pos:
            # risk-on + social quiet → بهترین ورود بلندمدت
            kelly = 0.6
            modifier = round(modifier_raw * 0.9, 1)
            conviction = (
                f"⭐⭐⭐⭐ ACCUMULATE — پول واقعی وارد می‌شود، هنوز هایپ نیست\n"
                f"macro={macro:+.2f} · social={social:+.2f}"
            )
            return ("ACCUMULATE", kelly, modifier, conviction)

        elif m_pos and s_pos:
            # risk-on + social hot → بالاترین conviction
            kelly = 0.8
            modifier = round(modifier_raw, 1)
            conviction = (
                f"⭐⭐⭐⭐⭐ DEPLOY — بالاترین conviction\n"
                f"macro={macro:+.2f} · social={social:+.2f}"
            )
            return ("DEPLOY", kelly, modifier, conviction)

        elif m_neg and not s_pos:
            # risk-off + social quiet → صبر کن
            kelly = 0.2
            modifier = round(modifier_raw * 0.8, 1)
            conviction = (
                f"⭐⭐ WAIT — فعلاً ماین کن، بازار هنوز آماده نیست\n"
                f"macro={macro:+.2f} · social={social:+.2f}"
            )
            return ("WAIT", kelly, modifier, conviction)

        elif m_neg and s_pos:
            # risk-off + social hot → تله
            kelly = 0.0
            modifier = round(modifier_raw * 0.5, 1)   # modifier منفی احتمالاً
            conviction = (
                f"⚠️ TRAP — هایپ بدون پشتوانه‌ی ماکرو، احتمال قله\n"
                f"macro={macro:+.2f} · social={social:+.2f}"
            )
            return ("TRAP", kelly, modifier, conviction)

        else:
            # خنثی — نزدیک به صفر
            kelly = 0.35
            modifier = round(modifier_raw * 0.3, 1)
            conviction = (
                f"⭐⭐⭐ NEUTRAL — بازار خنثی، DCA عادی\n"
                f"macro={macro:+.2f} · social={social:+.2f}"
            )
            return ("NEUTRAL", kelly, modifier, conviction)

    def compute_all(self, symbols: list) -> list:
        """محاسبه برای همه symbols و ذخیره در DataStore."""
        results = []
        for sym in symbols:
            r = self.compute(sym)
            results.append(r)
            logger.info(
                f"{sym}: {r.quadrant} | kelly={r.kelly_frac:.1f} "
                f"| modifier={r.score_modifier:+.1f} "
                f"| social={r.social_signal} | macro={r.macro_regime}"
            )
        return results

    def to_records(self, results: list) -> list:
        """تبدیل لیست FusionResult به لیست dict برای ذخیره در DataStore."""
        return [
            {
                "timestamp": r.timestamp,
                "symbol": r.symbol,
                "social_signal": r.social_signal,
                "macro_regime": r.macro_regime,
                "quadrant": r.quadrant,
                "kelly_frac": r.kelly_frac,
                "score_modifier": r.score_modifier,
                "conviction": r.conviction,
            }
            for r in results
        ]

    @staticmethod
    def describe_matrix() -> str:
        """توضیح ماتریس برای لاگ یا Telegram."""
        return (
            "📊 Fusion Matrix / ماتریس ترکیبی\n"
            "\n"
            "                  Social آرام     Social گرم\n"
            "  Macro Risk-on │ ⭐⭐⭐⭐ ACCUM │ ⭐⭐⭐⭐⭐ DEPLOY │\n"
            "  Macro Risk-off│ ⭐⭐ WAIT     │ ⚠️  TRAP       │\n"
            "\n"
            "ACCUMULATE = قبل از جمعیت می‌خری (بهترین)\n"
            "DEPLOY     = بالاترین اطمینان\n"
            "WAIT       = فعلاً ماین کن\n"
            "TRAP       = نخر — هایپ بدون پشتوانه"
        )
