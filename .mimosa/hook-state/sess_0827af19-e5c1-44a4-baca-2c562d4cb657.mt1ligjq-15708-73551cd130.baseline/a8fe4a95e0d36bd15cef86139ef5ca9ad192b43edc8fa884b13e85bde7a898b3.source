"""
SENTINEL — signal_library.py
کتابخانه‌ی سیگنال‌ها با رابط یکنواخت (Two Sigma style)

هر تابع:
  ورودی:  df — DataFrame با ستون‌های خام از DataStore
  خروجی: pd.Series با همان ایندکس، مقادیر در [-1, +1]
          NaN = داده کافی نیست یا سیگنال نامعتبر

اصول:
  - هر سیگنال مستقل است — هیچ سیگنالی به دیگری متکی نیست
  - کلیپ به [-1, +1] قبل از بازگشت
  - هیچ lookahead bias: فقط از داده‌های t و قبل استفاده می‌شود
  - تمام توابع با rolling محاسبه می‌کنند نه یک عدد واحد

ستون‌های مورد نیاز هر سیگنال:
  creator_growth   → creator_count (lc timeseries)
  galaxy_momentum  → galaxy_score  (lc timeseries)
  spam_penalty     → spam_pct      (lc timeseries)
  whale_pressure   → whale_ratio   (cq whale_ratio)
  stablecoin_inflow→ stable_netflow_usd (cq stablecoin_flows)
  miner_flow       → miner_to_exchange_usd (cq miner_flows)
  sector_narrative → sector_galaxy_score (lc sectors)

نحوه استفاده:
  from signal_library import SIGNAL_REGISTRY, compute_signals
  df = ds.read("lunarcrush/ts/BTC_daily.parquet")
  signals = compute_signals(df, ["galaxy_momentum", "spam_penalty"])
"""

from __future__ import annotations

import logging
from typing import Callable, Dict, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ─── ثابت‌های نرمال‌سازی ───────────────────────────────────
_STABLE_THRESHOLD_USD   = 500_000_000   # 500M — ورودی stablecoin قوی
_MINER_THRESHOLD_USD    =  50_000_000   # 50M  — جریان ماینر به صرافی
_GALAXY_SCORE_MAX       = 100.0
_WHALE_MAX_RATIO        = 0.85          # بالاتر = تسلط نهنگ‌ها
_CREATOR_LOOKBACK       = 7             # روز
_MOMENTUM_LOOKBACK      = 14            # روز برای مشتق galaxy_score
_SPAM_LOOKBACK          = 7
_SECTOR_LOOKBACK        = 7


# ═══════════════════════════════════════════════════════════════
#  ۱. Creator Growth — نرخ رشد سازنده‌ی محتوا
# ═══════════════════════════════════════════════════════════════
def signal_creator_growth(df: pd.DataFrame) -> pd.Series:
    """
    نرخ رشد تعداد کریتورها در ۷ روز.
    سیگنال قوی: رشد > ۱۵٪ در ۷ روز — علاقه‌ی واقعی، نه هایپ قیمتی.
    سیگنال ضعیف: کاهش کریتور = خستگی روایت.

    فرمول:
      growth_7d = (creator_count[t] / creator_count[t-7]) - 1
      signal = clip(growth_7d / 0.30, -1, 1)
      نرمال‌سازی: ۳۰٪ رشد → سیگنال ۱.۰ (بالاترین)
    """
    col = "creator_count"
    if col not in df.columns:
        logger.debug(f"signal_creator_growth: ستون '{col}' پیدا نشد")
        return pd.Series(np.nan, index=df.index, name="creator_growth")

    creator = df[col].copy().astype(float)
    shifted = creator.shift(_CREATOR_LOOKBACK)

    growth = (creator / shifted.replace(0, np.nan)) - 1.0
    signal = (growth / 0.30).clip(-1.0, 1.0)

    # اگر creator_count خیلی کم باشد (< 10) سیگنال قابل اعتماد نیست
    mask = creator < 10
    signal[mask] = np.nan

    signal.name = "creator_growth"
    return signal


# ═══════════════════════════════════════════════════════════════
#  ۲. Galaxy Momentum — شتاب Galaxy Score (مشتق ۱۴ روزه)
# ═══════════════════════════════════════════════════════════════
def signal_galaxy_momentum(df: pd.DataFrame) -> pd.Series:
    """
    شتاب Galaxy Score: تفاضل ۱۴ روزه‌ی نرمال‌شده.
    Galaxy Score از LunarCrush — ترکیبی از قیمت + سوشال.
    سیگنال: نه سطح مطلق، بلکه تغییر سرعت (مشتق اول).

    فرمول:
      delta_14d = galaxy_score[t] - galaxy_score[t-14]
      signal = clip(delta_14d / 20.0, -1, 1)
      نرمال‌سازی: تغییر ۲۰ امتیاز در ۱۴ روز → سیگنال ۱.۰
    """
    col = "galaxy_score"
    if col not in df.columns:
        logger.debug(f"signal_galaxy_momentum: ستون '{col}' پیدا نشد")
        return pd.Series(np.nan, index=df.index, name="galaxy_momentum")

    gs = df[col].copy().astype(float)
    delta = gs - gs.shift(_MOMENTUM_LOOKBACK)
    signal = (delta / 20.0).clip(-1.0, 1.0)

    signal.name = "galaxy_momentum"
    return signal


# ═══════════════════════════════════════════════════════════════
#  ۳. Spam Penalty — جریمه‌ی محتوای اسپم
# ═══════════════════════════════════════════════════════════════
def signal_spam_penalty(df: pd.DataFrame) -> pd.Series:
    """
    وقتی درصد محتوای اسپم بالاست، سیگنال‌های سوشال قابل اعتماد نیستند.
    spam_pct بالا = بازاریابی مصنوعی، نه علاقه‌ی واقعی.

    فرمول:
      avg_spam_7d = rolling mean spam_pct در ۷ روز
      penalty = clip(-avg_spam_7d / 20.0, -1, 0)
      نرمال‌سازی: ۲۰٪ spam → penalty -1.0 (بدترین)
      سیگنال همیشه ≤ 0 (فقط جریمه، نه پاداش)
    """
    col = "spam_pct"
    if col not in df.columns:
        logger.debug(f"signal_spam_penalty: ستون '{col}' پیدا نشد")
        return pd.Series(np.nan, index=df.index, name="spam_penalty")

    spam = df[col].copy().astype(float)
    avg_spam = spam.rolling(_SPAM_LOOKBACK, min_periods=3).mean()
    signal = (-avg_spam / 20.0).clip(-1.0, 0.0)

    signal.name = "spam_penalty"
    return signal


# ═══════════════════════════════════════════════════════════════
#  ۴. Whale Pressure — فشار نهنگ‌ها بر بازار
# ═══════════════════════════════════════════════════════════════
def signal_whale_pressure(df: pd.DataFrame) -> pd.Series:
    """
    نسبت تراکنش‌های نهنگ به کل تراکنش‌ها (whale_ratio از CryptoQuant).
    whale_ratio پایین = توزیع قدرت خرید — سیگنال مثبت
    whale_ratio بالا = تسلط نهنگ‌ها — احتمال دستکاری

    فرمول:
      signal = clip(1 - (whale_ratio / 0.85), -1, 1) * 2 - 1
      → whale_ratio=0.0 → signal=+1.0 (بهترین)
      → whale_ratio=0.85 → signal=-1.0 (بدترین)
      → whale_ratio=0.425 → signal=0.0 (خنثی)

    ساده‌سازی:
      normalized = (whale_ratio - 0.425) / 0.425
      signal = clip(-normalized, -1, 1)
    """
    col = "whale_ratio"
    if col not in df.columns:
        logger.debug(f"signal_whale_pressure: ستون '{col}' پیدا نشد")
        return pd.Series(np.nan, index=df.index, name="whale_pressure")

    wr = df[col].copy().astype(float)
    # نرمال‌سازی: 0.0→+1, 0.425→0, 0.85→-1
    midpoint = _WHALE_MAX_RATIO / 2.0   # 0.425
    normalized = (wr - midpoint) / midpoint
    signal = (-normalized).clip(-1.0, 1.0)

    signal.name = "whale_pressure"
    return signal


# ═══════════════════════════════════════════════════════════════
#  ۵. Stablecoin Inflow — ورود نقدینگی جدید
# ═══════════════════════════════════════════════════════════════
def signal_stablecoin_inflow(df: pd.DataFrame) -> pd.Series:
    """
    جریان خالص stablecoin به صرافی‌ها.
    inflow مثبت = نقدینگی جدید در حال ورود → پتانسیل خرید.
    outflow = نقدینگی در حال خروج → احتمال فروش یا خروج از بازار.

    ستون: stable_netflow_usd (مجموع USDT + USDC netflow)
    فرمول:
      rolling_7d = rolling sum stable_netflow_usd در ۷ روز
      signal = clip(rolling_7d / 500M, -1, 1)
      نرمال‌سازی: +500M ورود → سیگنال +1.0
    """
    col = "stable_netflow_usd"
    if col not in df.columns:
        # تلاش برای ستون‌های جایگزین
        for alt in ["netflow_usd", "stablecoin_netflow"]:
            if alt in df.columns:
                col = alt
                break
        else:
            logger.debug("signal_stablecoin_inflow: ستون stable_netflow_usd پیدا نشد")
            return pd.Series(np.nan, index=df.index, name="stablecoin_inflow")

    netflow = df[col].copy().astype(float)
    rolling_sum = netflow.rolling(7, min_periods=3).sum()
    signal = (rolling_sum / _STABLE_THRESHOLD_USD).clip(-1.0, 1.0)

    signal.name = "stablecoin_inflow"
    return signal


# ═══════════════════════════════════════════════════════════════
#  ۶. Miner Flow — فشار فروش ماینرها
# ═══════════════════════════════════════════════════════════════
def signal_miner_flow(df: pd.DataFrame) -> pd.Series:
    """
    جریان BTC از ماینرها به صرافی‌ها.
    جریان بالا = ماینرها در حال فروش → فشار نزولی.
    جریان پایین = ماینرها نگه می‌دارند → انتظار قیمت بالاتر.

    ستون: miner_to_exchange_usd
    فرمول:
      rolling_7d = rolling mean miner_to_exchange_usd
      signal = clip(1 - (rolling_7d / 50M), -1, 1)
      → 0 → +1.0 (ماینر نمی‌فروشد — خوب)
      → 50M+ → -1.0 (ماینر به شدت می‌فروشد — بد)
    """
    col = "miner_to_exchange_usd"
    if col not in df.columns:
        for alt in ["miner_outflow_usd", "miner_netflow"]:
            if alt in df.columns:
                col = alt
                break
        else:
            logger.debug("signal_miner_flow: ستون miner_to_exchange_usd پیدا نشد")
            return pd.Series(np.nan, index=df.index, name="miner_flow")

    miner = df[col].copy().astype(float).abs()   # abs: ما به حجم جریان اهمیت می‌دهیم
    rolling_avg = miner.rolling(7, min_periods=3).mean()
    signal = (1.0 - rolling_avg / _MINER_THRESHOLD_USD).clip(-1.0, 1.0)

    signal.name = "miner_flow"
    return signal


# ═══════════════════════════════════════════════════════════════
#  ۷. Sector Narrative — مومنتوم روایت سکتور
# ═══════════════════════════════════════════════════════════════
def signal_sector_narrative(df: pd.DataFrame) -> pd.Series:
    """
    مومنتوم Galaxy Score در سطح سکتور (privacy / defi / ai-agents).
    اگر سکتور در حال رشد است، کوین‌های داخل آن هم بهتر عمل می‌کنند.

    ستون: sector_galaxy_score (از lc sectors / topics)
    فرمول:
      delta_7d = sector_galaxy_score[t] - sector_galaxy_score[t-7]
      signal = clip(delta_7d / 15.0, -1, 1)
      نرمال‌سازی: تغییر ۱۵ امتیاز در ۷ روز → سیگنال ۱.۰
    """
    col = "sector_galaxy_score"
    if col not in df.columns:
        # جایگزین‌های احتمالی
        for alt in ["topic_galaxy_score", "sector_score"]:
            if alt in df.columns:
                col = alt
                break
        else:
            logger.debug("signal_sector_narrative: ستون sector_galaxy_score پیدا نشد")
            return pd.Series(np.nan, index=df.index, name="sector_narrative")

    score = df[col].copy().astype(float)
    delta = score - score.shift(_SECTOR_LOOKBACK)
    signal = (delta / 15.0).clip(-1.0, 1.0)

    signal.name = "sector_narrative"
    return signal


# ═══════════════════════════════════════════════════════════════
#  Registry — فهرست رسمی سیگنال‌ها
# ═══════════════════════════════════════════════════════════════
SIGNAL_REGISTRY: Dict[str, Callable[[pd.DataFrame], pd.Series]] = {
    "creator_growth":    signal_creator_growth,
    "galaxy_momentum":   signal_galaxy_momentum,
    "spam_penalty":      signal_spam_penalty,
    "whale_pressure":    signal_whale_pressure,
    "stablecoin_inflow": signal_stablecoin_inflow,
    "miner_flow":        signal_miner_flow,
    "sector_narrative":  signal_sector_narrative,
}

# وزن‌های پیش‌فرض برای ترکیب (مجموع = ۱.۰)
# قابل تنظیم بر اساس IC واقعی در signal_eval.py
SIGNAL_WEIGHTS: Dict[str, float] = {
    "creator_growth":    0.15,
    "galaxy_momentum":   0.20,
    "spam_penalty":      0.10,
    "whale_pressure":    0.20,
    "stablecoin_inflow": 0.20,
    "miner_flow":        0.10,
    "sector_narrative":  0.05,
}


# ═══════════════════════════════════════════════════════════════
#  توابع کمکی
# ═══════════════════════════════════════════════════════════════

def compute_signals(
    df: pd.DataFrame,
    signal_names: Optional[List[str]] = None,
) -> pd.DataFrame:
    """
    محاسبه‌ی چندین سیگنال روی یک DataFrame.

    Args:
        df: DataFrame با ستون‌های خام
        signal_names: لیست نام سیگنال‌ها (None = همه)

    Returns:
        DataFrame با یک ستون برای هر سیگنال
    """
    names = signal_names or list(SIGNAL_REGISTRY.keys())
    results: Dict[str, pd.Series] = {}

    for name in names:
        if name not in SIGNAL_REGISTRY:
            logger.warning(f"سیگنال ناشناخته: '{name}'")
            continue
        try:
            s = SIGNAL_REGISTRY[name](df)
            results[name] = s
        except Exception as e:
            logger.error(f"سیگنال '{name}' خطا داد: {e}")
            results[name] = pd.Series(np.nan, index=df.index, name=name)

    return pd.DataFrame(results, index=df.index)


def composite_signal(
    df: pd.DataFrame,
    weights: Optional[Dict[str, float]] = None,
    signal_names: Optional[List[str]] = None,
) -> pd.Series:
    """
    سیگنال ترکیبی وزن‌دار.
    وزن‌ها به‌صورت خودکار نرمال می‌شوند (مجموع = ۱.۰).
    NaN‌ها نادیده گرفته می‌شوند (وزن باقی‌مانده توزیع می‌شود).

    Args:
        df:            DataFrame خام
        weights:       dict نام→وزن (None = SIGNAL_WEIGHTS پیش‌فرض)
        signal_names:  زیرمجموعه‌ای از سیگنال‌ها (None = همه‌ی موجود در weights)

    Returns:
        pd.Series مقادیر [-1, +1] — سیگنال نهایی ترکیبی
    """
    w = weights or SIGNAL_WEIGHTS
    names = signal_names or list(w.keys())
    signals_df = compute_signals(df, names)

    composite = pd.Series(0.0, index=df.index)
    total_weight = pd.Series(0.0, index=df.index)

    for name in names:
        if name not in signals_df.columns:
            continue
        weight = w.get(name, 0.0)
        s = signals_df[name]
        valid = s.notna()
        composite[valid] += s[valid] * weight
        total_weight[valid] += weight

    # نرمال‌سازی برای NaN‌ها: تقسیم بر وزن واقعی موجود
    safe_weight = total_weight.replace(0, np.nan)
    result = (composite / safe_weight).clip(-1.0, 1.0)
    result.name = "composite"
    return result


def describe_signals() -> str:
    """توضیح مختصر همه‌ی سیگنال‌ها برای لاگ یا Telegram."""
    lines = ["📊 Signal Library / کتابخانه‌ی سیگنال‌ها\n"]
    descriptions = {
        "creator_growth":    "نرخ رشد کریتور ۷ روزه — علاقه‌ی واقعی، نه هایپ",
        "galaxy_momentum":   "شتاب Galaxy Score ۱۴ روزه — تغییر سرعت سوشال",
        "spam_penalty":      "جریمه‌ی spam — محتوای مصنوعی را تنبیه می‌کند",
        "whale_pressure":    "فشار نهنگ — whale_ratio پایین بهتر است",
        "stablecoin_inflow": "ورود نقدینگی — stablecoin به صرافی می‌رود؟",
        "miner_flow":        "جریان ماینر — ماینرها می‌فروشند؟",
        "sector_narrative":  "مومنتوم سکتور — روایت privacy/defi داغ است؟",
    }
    for name, desc in descriptions.items():
        w = SIGNAL_WEIGHTS.get(name, 0)
        lines.append(f"  {name:<20} w={w:.2f}  {desc}")
    return "\n".join(lines)


# ─── اجرای مستقیم: نمایش توضیح ───
if __name__ == "__main__":
    print(describe_signals())
    print()
    print("تست سریع با داده‌ی مصنوعی...")

    # ساخت یک DataFrame آزمایشی
    idx = pd.date_range("2024-01-01", periods=60, freq="D")
    rng = np.random.default_rng(42)
    mock_df = pd.DataFrame({
        "creator_count":          rng.integers(100, 500, 60).astype(float),
        "galaxy_score":           rng.uniform(30, 80, 60),
        "spam_pct":               rng.uniform(2, 25, 60),
        "whale_ratio":            rng.uniform(0.2, 0.8, 60),
        "stable_netflow_usd":     rng.uniform(-600e6, 800e6, 60),
        "miner_to_exchange_usd":  rng.uniform(5e6, 80e6, 60),
        "sector_galaxy_score":    rng.uniform(40, 75, 60),
    }, index=idx)

    sig_df = compute_signals(mock_df)
    comp = composite_signal(mock_df)

    print(f"\nسیگنال‌های ۵ روز آخر:")
    print(sig_df.tail(5).round(3).to_string())
    print(f"\nسیگنال ترکیبی ۵ روز آخر:")
    print(comp.tail(5).round(3).to_string())
    print("\n✅ signal_library آماده است")
