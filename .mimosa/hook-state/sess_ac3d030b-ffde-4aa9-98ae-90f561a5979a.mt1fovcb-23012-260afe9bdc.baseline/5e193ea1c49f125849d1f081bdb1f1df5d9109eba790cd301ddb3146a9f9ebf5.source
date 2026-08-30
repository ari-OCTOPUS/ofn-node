"""
SENTINEL — signal_eval.py
ارزیابی آماری سیگنال‌ها: IC، IC IR، Deflated Sharpe

اصل AQR/DE Shaw: سیگنالی که IC ≥ 0.05 و IC IR ≥ 0.5 نداشته باشد
                 بهتر است در production نرود.

متریک‌ها:
  IC (Information Coefficient)
    = Spearman corr(signal[t], forward_return[t+k])
    محدوده: [-1, +1] — بالاتر = سیگنال بهتر پیش‌بینی می‌کند
    هدف مینیمال: IC > 0.05 (بر اساس 100+ نمونه)

  IC IR (IC Information Ratio)
    = mean(IC) / std(IC)
    پایداری سیگنال در طول زمان
    هدف: IC IR ≥ 0.5

  Deflated Sharpe Ratio (DSR)
    برای جلوگیری از data-mining: Sharpe واقعی را با تعداد آزمایش‌ها تنبیه می‌کند.
    فرمول Bailey & Lopez de Prado (2014):
      DSR = Φ( (SR - E[SR_max]) / sqrt(V[SR_max]) )
      که Φ توزیع نرمال، E[SR_max] = بهترین SR تصادفی انتظاری است

  Turnover
    درصد تغییر موضع هر دوره — بالا = هزینه‌ی معاملاتی بالا

نحوه استفاده:
  from signal_eval import SignalEvaluator
  ev = SignalEvaluator(signals_df, prices_df)
  report = ev.evaluate_all(forward_days=7)
  ev.print_report(report)
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from scipy import stats as scipy_stats

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
#  ساختار نتیجه‌ی ارزیابی یک سیگنال
# ═══════════════════════════════════════════════════════════════
@dataclass
class SignalMetrics:
    name:               str
    n_obs:              int         # تعداد مشاهدات معتبر
    ic_mean:            float       # میانگین IC در پنجره‌های rolling
    ic_std:             float       # انحراف معیار IC
    ic_ir:              float       # IC IR = ic_mean / ic_std
    ic_t_stat:          float       # t-statistic: ic_mean / (ic_std/sqrt(n))
    ic_pvalue:          float       # p-value یک‌طرفه (H1: IC > 0)
    sharpe:             float       # Sharpe نهایی استراتژی
    deflated_sharpe:    float       # DSR — تنبیه‌شده برای تعداد آزمایش‌ها
    turnover_mean:      float       # میانگین turnover
    max_drawdown:       float       # بدترین drawdown استراتژی
    is_significant:     bool        # آیا سیگنال واقعی است؟
    verdict:            str         # "✅ Real Alpha" | "⚠️ Weak" | "❌ Noise"


# ═══════════════════════════════════════════════════════════════
#  کلاس اصلی ارزیابی
# ═══════════════════════════════════════════════════════════════
class SignalEvaluator:
    """
    ارزیابی آماری سیگنال‌ها با IC، IC IR، و Deflated Sharpe.

    Args:
        signals_df:   DataFrame با ایندکس تاریخ و یک ستون برای هر سیگنال
        prices_df:    DataFrame با ستون‌های قیمت برای هر دارایی
                      یا یک Series برای یک دارایی
        ic_window:    طول پنجره‌ی rolling برای محاسبه‌ی IC (روز)
        min_obs:      حداقل مشاهدات معتبر برای ارزیابی
    """

    # آستانه‌های تصمیم
    IC_MIN          = 0.05    # حداقل IC برای "معنی‌دار"
    ICIR_MIN        = 0.50    # حداقل IC IR
    PVALUE_MAX      = 0.05    # سطح معنی‌داری
    MIN_OBS         = 30      # حداقل نمونه

    def __init__(
        self,
        signals_df: pd.DataFrame,
        prices: pd.DataFrame | pd.Series,
        ic_window: int = 20,
        min_obs: int = 30,
    ):
        self.signals = signals_df.copy()
        if isinstance(prices, pd.Series):
            self.prices = prices.to_frame("price")
        else:
            self.prices = prices.copy()
        self.ic_window = ic_window
        self.min_obs = min_obs

    # ─── ۱. محاسبه‌ی بازده forward ─────────────────────────────
    def _forward_return(self, price_col: str, forward_days: int) -> pd.Series:
        """بازده k روز آینده."""
        p = self.prices[price_col].astype(float)
        fwd = p.shift(-forward_days) / p - 1.0
        return fwd

    # ─── ۲. IC (Spearman) ───────────────────────────────────────
    def _compute_ic_series(
        self,
        signal: pd.Series,
        forward_ret: pd.Series,
        window: int,
    ) -> pd.Series:
        """
        Rolling Spearman IC در پنجره‌ای به اندازه‌ی window.
        از رتبه‌بندی rolling استفاده می‌کند برای سرعت بیشتر.
        """
        # align
        df = pd.DataFrame({"s": signal, "r": forward_ret}).dropna()
        if len(df) < window:
            return pd.Series(dtype=float, name="ic")

        ic_list = []
        dates = []
        for i in range(window - 1, len(df)):
            window_df = df.iloc[i - window + 1: i + 1]
            if len(window_df) < 10:
                continue
            corr, _ = scipy_stats.spearmanr(window_df["s"], window_df["r"])
            ic_list.append(corr if not np.isnan(corr) else np.nan)
            dates.append(df.index[i])

        return pd.Series(ic_list, index=dates, name="ic")

    # ─── ۳. Deflated Sharpe Ratio (Bailey & Lopez de Prado 2014) ─
    @staticmethod
    def deflated_sharpe(
        observed_sr: float,
        n_trials: int,
        n_obs: int,
        skewness: float = 0.0,
        kurtosis: float = 3.0,
    ) -> float:
        """
        محاسبه‌ی Deflated Sharpe Ratio.

        مرجع: Bailey & Lopez de Prado — "The Deflated Sharpe Ratio" (2014)

        فرمول:
          SR_max = sqrt(V[max_SR]) * E[max_SR] (تقریباً)
          E[SR_max] ≈ (1 - γ) * Z^{-1}(1 - 1/T) + γ * Z^{-1}(1 - 1/(T*e))
          که γ ≈ 0.5772 (ثابت Euler-Mascheroni)

        Args:
          observed_sr:  Sharpe ratio مشاهده‌شده (بدون annualize)
          n_trials:     تعداد استراتژی‌هایی که آزمایش شده‌اند
          n_obs:        تعداد مشاهدات (طول سری زمانی)
          skewness:     چولگی بازده‌ها
          kurtosis:     کشیدگی بازده‌ها (3 = نرمال)
        """
        from scipy.special import gamma as gamma_func
        from scipy.stats import norm

        if n_trials <= 1 or n_obs < 2:
            return float(norm.cdf(observed_sr))

        # euler-mascheroni constant
        euler_gamma = 0.5772156649

        # E[max SR] تخمینی
        e_max_sr = (
            (1 - euler_gamma) * norm.ppf(1 - 1.0 / n_trials)
            + euler_gamma * norm.ppf(1 - 1.0 / (n_trials * math.e))
        )

        # V[SR]: تصحیح برای non-normality
        # var_sr = (1 - skewness*SR + (kurtosis-1)/4 * SR^2) / (n-1)
        var_sr = (
            1 - skewness * observed_sr
            + (kurtosis - 1) / 4.0 * observed_sr**2
        ) / max(n_obs - 1, 1)
        std_sr = math.sqrt(max(var_sr, 1e-8))

        z = (observed_sr - e_max_sr) / std_sr
        return float(norm.cdf(z))

    # ─── ۴. Turnover ────────────────────────────────────────────
    @staticmethod
    def _turnover(positions: pd.Series) -> pd.Series:
        """
        Turnover: |Δposition| هر روز.
        position = sign(signal) برای long/short.
        """
        pos = np.sign(positions.fillna(0))
        return pos.diff().abs()

    # ─── ۵. Max Drawdown ────────────────────────────────────────
    @staticmethod
    def _max_drawdown(pnl_series: pd.Series) -> float:
        """
        بدترین drawdown استراتژی (از اوج به کف).
        پارامتر: سری PnL تجمعی (cumulative returns).
        """
        cumulative = (1 + pnl_series.fillna(0)).cumprod()
        rolling_max = cumulative.expanding().max()
        drawdown = (cumulative - rolling_max) / rolling_max
        return float(drawdown.min())

    # ─── ۶. ارزیابی یک سیگنال ───────────────────────────────────
    def evaluate(
        self,
        signal_name: str,
        price_col: Optional[str] = None,
        forward_days: int = 7,
        n_trials: int = 7,   # تعداد کل سیگنال‌های آزمایش‌شده
    ) -> Optional[SignalMetrics]:
        """
        ارزیابی کامل یک سیگنال.

        Args:
          signal_name:   نام ستون در signals_df
          price_col:     نام ستون قیمت (None = اولین ستون prices)
          forward_days:  افق پیش‌بینی (روز)
          n_trials:      تعداد کل سیگنال‌های آزمایش‌شده (برای DSR)
        """
        if signal_name not in self.signals.columns:
            logger.warning(f"سیگنال '{signal_name}' در signals_df پیدا نشد")
            return None

        pcol = price_col or self.prices.columns[0]
        if pcol not in self.prices.columns:
            logger.warning(f"ستون قیمت '{pcol}' پیدا نشد")
            return None

        signal = self.signals[signal_name].astype(float)
        fwd_ret = self._forward_return(pcol, forward_days)

        # align روی ایندکس مشترک
        aligned = pd.DataFrame({"signal": signal, "fwd": fwd_ret}).dropna()
        n_obs = len(aligned)

        if n_obs < self.min_obs:
            logger.info(f"'{signal_name}': فقط {n_obs} نمونه — کمتر از حداقل {self.min_obs}")
            return None

        # ─── IC rolling ───
        ic_series = self._compute_ic_series(
            aligned["signal"], aligned["fwd"], self.ic_window
        )

        if ic_series.empty or ic_series.dropna().empty:
            logger.info(f"'{signal_name}': IC series خالی است")
            return None

        ic_vals = ic_series.dropna()
        ic_mean = float(ic_vals.mean())
        ic_std  = float(ic_vals.std(ddof=1)) if len(ic_vals) > 1 else 0.0
        n_ic    = len(ic_vals)

        # IC IR
        ic_ir = ic_mean / ic_std if ic_std > 1e-9 else 0.0

        # t-test: H0: IC = 0
        ic_t = ic_mean / (ic_std / math.sqrt(n_ic)) if ic_std > 1e-9 else 0.0
        ic_pvalue = float(scipy_stats.t.sf(abs(ic_t), df=n_ic - 1))  # یک‌طرفه

        # ─── Sharpe استراتژی ───
        # استراتژی ساده: موضع = sign(signal)، بازده = sign(signal) × fwd_ret
        position = np.sign(aligned["signal"])
        strategy_ret = position * aligned["fwd"]

        sr_daily = (
            strategy_ret.mean() / strategy_ret.std(ddof=1)
            if strategy_ret.std() > 1e-9 else 0.0
        )

        sk = float(scipy_stats.skew(strategy_ret.dropna()))
        kt = float(scipy_stats.kurtosis(strategy_ret.dropna(), fisher=False))  # regular kurtosis

        dsr = self.deflated_sharpe(sr_daily, n_trials, n_obs, sk, kt)

        # ─── Turnover ───
        tv = self._turnover(position)
        turnover_mean = float(tv.mean())

        # ─── Max Drawdown ───
        mdd = self._max_drawdown(strategy_ret)

        # ─── Verdict ───
        is_sig = (
            ic_mean >= self.IC_MIN
            and ic_ir  >= self.ICIR_MIN
            and ic_pvalue <= self.PVALUE_MAX
            and dsr >= 0.95
        )

        if ic_mean >= self.IC_MIN and ic_ir >= self.ICIR_MIN:
            verdict = "✅ Real Alpha"
        elif ic_mean >= self.IC_MIN * 0.5:
            verdict = "⚠️ Weak Signal"
        else:
            verdict = "❌ Noise"

        return SignalMetrics(
            name=signal_name,
            n_obs=n_obs,
            ic_mean=round(ic_mean, 4),
            ic_std=round(ic_std, 4),
            ic_ir=round(ic_ir, 3),
            ic_t_stat=round(ic_t, 3),
            ic_pvalue=round(ic_pvalue, 4),
            sharpe=round(float(sr_daily * math.sqrt(252)), 3),   # annualized
            deflated_sharpe=round(dsr, 3),
            turnover_mean=round(turnover_mean, 3),
            max_drawdown=round(mdd, 4),
            is_significant=is_sig,
            verdict=verdict,
        )

    # ─── ۷. ارزیابی همه‌ی سیگنال‌ها ────────────────────────────
    def evaluate_all(
        self,
        price_col: Optional[str] = None,
        forward_days: int = 7,
    ) -> Dict[str, SignalMetrics]:
        """
        ارزیابی تمام سیگنال‌های موجود در signals_df.
        n_trials به‌صورت خودکار = تعداد ستون‌های سیگنال.
        """
        n_trials = len(self.signals.columns)
        results = {}
        for name in self.signals.columns:
            m = self.evaluate(name, price_col, forward_days, n_trials)
            if m is not None:
                results[name] = m
        return results

    # ─── ۸. گزارش ───────────────────────────────────────────────
    @staticmethod
    def print_report(
        metrics: Dict[str, SignalMetrics],
        sort_by: str = "ic_ir",
    ):
        """نمایش گزارش ارزیابی به‌صورت جدول."""
        if not metrics:
            print("هیچ سیگنالی برای گزارش وجود ندارد")
            return

        rows = sorted(metrics.values(), key=lambda m: getattr(m, sort_by, 0), reverse=True)

        print("\n" + "═" * 90)
        print("  SENTINEL — Signal Evaluation Report")
        print("═" * 90)
        print(
            f"  {'Signal':<22} {'N':>5} {'IC':>7} {'IC_IR':>7} "
            f"{'p-val':>7} {'Sharpe':>7} {'DSR':>6} {'MDD':>7}  Verdict"
        )
        print("  " + "─" * 87)
        for m in rows:
            print(
                f"  {m.name:<22} {m.n_obs:>5} {m.ic_mean:>7.4f} {m.ic_ir:>7.3f} "
                f"{m.ic_pvalue:>7.4f} {m.sharpe:>7.3f} {m.deflated_sharpe:>6.3f} "
                f"{m.max_drawdown:>7.4f}  {m.verdict}"
            )
        print("═" * 90)

        real_alpha = [m for m in rows if m.verdict.startswith("✅")]
        weak       = [m for m in rows if m.verdict.startswith("⚠️")]
        noise      = [m for m in rows if m.verdict.startswith("❌")]

        print(f"\n  خلاصه: {len(real_alpha)} Real Alpha | {len(weak)} Weak | {len(noise)} Noise")
        if real_alpha:
            print(f"  بهترین سیگنال‌ها: {', '.join(m.name for m in real_alpha)}")
        print()

    @staticmethod
    def to_dataframe(metrics: Dict[str, SignalMetrics]) -> pd.DataFrame:
        """تبدیل نتایج به DataFrame برای ذخیره‌سازی."""
        rows = [
            {
                "signal": m.name,
                "n_obs": m.n_obs,
                "ic_mean": m.ic_mean,
                "ic_std": m.ic_std,
                "ic_ir": m.ic_ir,
                "ic_t_stat": m.ic_t_stat,
                "ic_pvalue": m.ic_pvalue,
                "sharpe_annual": m.sharpe,
                "deflated_sharpe": m.deflated_sharpe,
                "turnover_mean": m.turnover_mean,
                "max_drawdown": m.max_drawdown,
                "is_significant": m.is_significant,
                "verdict": m.verdict,
            }
            for m in metrics.values()
        ]
        return pd.DataFrame(rows).set_index("signal")


# ─── اجرای مستقیم: تست با داده‌ی مصنوعی ───
if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    from signal_library import compute_signals

    print("تست signal_eval با داده‌ی مصنوعی...")
    rng = np.random.default_rng(42)
    n = 300
    idx = pd.date_range("2023-01-01", periods=n, freq="D")

    # قیمت واقعی‌تر: GBM
    log_returns = rng.normal(0.0005, 0.025, n)
    prices = pd.Series(100.0 * np.exp(np.cumsum(log_returns)), index=idx, name="price")

    # داده‌ی خام با همبستگی واقعی با بازده
    future_ret = prices.pct_change().shift(-7)   # بازده ۷ روز آینده

    mock_df = pd.DataFrame({
        "creator_count":         rng.integers(100, 500, n).astype(float),
        "galaxy_score":          50 + 20 * future_ret.fillna(0) * 10 + rng.normal(0, 5, n),
        "spam_pct":              rng.uniform(2, 20, n),
        "whale_ratio":           rng.uniform(0.2, 0.8, n),
        "stable_netflow_usd":    rng.uniform(-600e6, 800e6, n),
        "miner_to_exchange_usd": rng.uniform(5e6, 80e6, n),
        "sector_galaxy_score":   rng.uniform(40, 75, n),
    }, index=idx)

    signals_df = compute_signals(mock_df)
    prices_df = prices.to_frame("price")

    ev = SignalEvaluator(signals_df, prices_df, ic_window=20)
    report = ev.evaluate_all(forward_days=7)
    SignalEvaluator.print_report(report)
