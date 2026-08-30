"""
SENTINEL — backtest_wf.py
Walk-Forward Backtesting با پنجره‌ی لغزنده

اصل Two Sigma/DE Shaw: سیگنال باید در out-of-sample (OOS) هم کار کند.
  - آموزش روی ماه‌های ۱-۳ (in-sample)
  - آزمایش روی ماه ۴ (out-of-sample)
  - سُر دادن به جلو و تکرار

ساختار walk-forward:
  |─────── Train ───────|── Test ──|
                        |─────── Train ───────|── Test ──|
                                              |─────── Train ───────|── Test ──|

متریک‌ها هر دوره:
  - MAR Ratio (CAGR / Max Drawdown) — پایداری بازده در برابر ریسک
  - Expectancy — میانگین سود به ازای هر معامله
  - Max Drawdown — بدترین افت از اوج
  - Win Rate — درصد معاملات سودده
  - Hit Rate — درصد روزهایی که سیگنال درست بود

نحوه استفاده:
  from backtest_wf import WalkForward
  wf = WalkForward(signals_df, prices_df, train_months=3, test_months=1)
  results = wf.run(signal_name="galaxy_momentum")
  wf.print_report(results)
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
#  ساختار نتیجه‌ی یک دوره‌ی test
# ═══════════════════════════════════════════════════════════════
@dataclass
class PeriodResult:
    period_idx:     int
    train_start:    str
    train_end:      str
    test_start:     str
    test_end:       str
    n_test:         int             # تعداد روزهای test
    total_return:   float           # بازده کل دوره‌ی test
    cagr:           float           # CAGR annualized
    max_drawdown:   float           # بدترین drawdown
    mar_ratio:      float           # CAGR / |MDD|
    win_rate:       float           # درصد روزهای مثبت
    hit_rate:       float           # درصد سیگنال‌های درست
    expectancy:     float           # میانگین P&L هر معامله
    sharpe:         float           # Sharpe annualized دوره
    n_trades:       int             # تعداد تغییر موضع
    notes:          str = ""


@dataclass
class WalkForwardReport:
    signal_name:        str
    forward_days:       int
    n_periods:          int
    periods:            List[PeriodResult]
    # متریک‌های ترکیبی روی همه‌ی دوره‌های OOS
    oos_total_return:   float
    oos_cagr:           float
    oos_max_drawdown:   float
    oos_mar_ratio:      float
    oos_sharpe:         float
    oos_win_rate:       float
    oos_hit_rate:       float
    consistency:        float       # درصد دوره‌هایی با بازده مثبت
    verdict:            str         # "✅ Deploy" | "⚠️ Monitor" | "❌ Reject"


# ═══════════════════════════════════════════════════════════════
#  کلاس اصلی Walk-Forward
# ═══════════════════════════════════════════════════════════════
class WalkForward:
    """
    Walk-Forward backtesting با پنجره‌ی لغزنده.

    Args:
        signals_df:     DataFrame با ایندکس تاریخ، ستون‌ها = سیگنال‌ها
        prices:         DataFrame یا Series با قیمت‌ها
        train_months:   طول دوره‌ی آموزش (ماه)
        test_months:    طول دوره‌ی آزمایش (ماه)
        min_train_obs:  حداقل روز برای آموزش معتبر
    """

    MAR_TARGET     = 1.0    # MAR ≥ 1 = CAGR حداقل برابر MDD
    SHARPE_TARGET  = 0.5    # Sharpe annualized ≥ 0.5
    CONSIST_TARGET = 0.60   # ۶۰٪ دوره‌ها باید مثبت باشند

    def __init__(
        self,
        signals_df: pd.DataFrame,
        prices: pd.DataFrame | pd.Series,
        train_months: int = 3,
        test_months: int = 1,
        min_train_obs: int = 30,
    ):
        self.signals = signals_df.copy()
        if isinstance(prices, pd.Series):
            self.prices = prices.to_frame(prices.name or "price")
        else:
            self.prices = prices.copy()
        self.train_months = train_months
        self.test_months  = test_months
        self.min_train_obs = min_train_obs

    # ─── اطمینان از ایندکس datetime ────────────────────────────
    def _ensure_datetime(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)
        return df.sort_index()

    # ─── ساخت پنجره‌های train/test ───────────────────────────────
    def _make_windows(self, index: pd.DatetimeIndex) -> List[Dict]:
        """پنجره‌های لغزنده را می‌سازد."""
        windows = []
        start = index[0]
        end   = index[-1]

        period_idx = 0
        while True:
            train_end = start + pd.DateOffset(months=self.train_months)
            test_end  = train_end + pd.DateOffset(months=self.test_months)

            if test_end > end:
                break

            windows.append({
                "idx":        period_idx,
                "train_s":    start,
                "train_e":    train_end,
                "test_s":     train_end,
                "test_e":     test_end,
            })

            start = start + pd.DateOffset(months=self.test_months)
            period_idx += 1

        return windows

    # ─── متریک‌های استراتژی ─────────────────────────────────────
    @staticmethod
    def _strategy_metrics(
        signal: pd.Series,
        fwd_ret: pd.Series,
    ) -> Dict:
        """
        محاسبه‌ی متریک‌ها برای یک دوره.
        استراتژی: موضع = sign(signal)، بازده روزانه = sign × fwd_ret
        """
        df = pd.DataFrame({"s": signal, "r": fwd_ret}).dropna()
        if len(df) < 5:
            return {"error": "کمتر از ۵ نمونه"}

        position = np.sign(df["s"])
        strategy_ret = position * df["r"]

        # بازده کل
        total_ret = float((1 + strategy_ret).prod() - 1)

        # CAGR
        n_days = len(strategy_ret)
        cagr = float((1 + total_ret) ** (252.0 / max(n_days, 1)) - 1)

        # Max Drawdown
        cumret = (1 + strategy_ret).cumprod()
        rolling_max = cumret.expanding().max()
        dd = (cumret - rolling_max) / rolling_max
        mdd = float(dd.min())

        # MAR
        mar = cagr / abs(mdd) if mdd < -1e-6 else (10.0 if cagr > 0 else 0.0)

        # Win Rate
        win_rate = float((strategy_ret > 0).mean())

        # Hit Rate: درصدی که سیگنال جهت درست را پیش‌بینی کرد
        correct = (np.sign(df["s"]) == np.sign(df["r"]))
        hit_rate = float(correct.mean())

        # Expectancy
        expectancy = float(strategy_ret.mean())

        # Sharpe
        sr_std = float(strategy_ret.std(ddof=1))
        sharpe = float(strategy_ret.mean() / sr_std * math.sqrt(252)) if sr_std > 1e-9 else 0.0

        # تعداد تغییر موضع
        pos_change = position.diff().abs()
        n_trades = int((pos_change > 0).sum())

        return {
            "n_test":       n_days,
            "total_return": round(total_ret, 4),
            "cagr":         round(cagr, 4),
            "max_drawdown": round(mdd, 4),
            "mar_ratio":    round(mar, 3),
            "win_rate":     round(win_rate, 3),
            "hit_rate":     round(hit_rate, 3),
            "expectancy":   round(expectancy, 5),
            "sharpe":       round(sharpe, 3),
            "n_trades":     n_trades,
        }

    # ─── اجرای یک walk-forward ───────────────────────────────────
    def run(
        self,
        signal_name: str,
        price_col: Optional[str] = None,
        forward_days: int = 7,
    ) -> Optional[WalkForwardReport]:
        """
        اجرای کامل walk-forward برای یک سیگنال.

        Args:
          signal_name:   نام سیگنال در signals_df
          price_col:     نام ستون قیمت (None = اول)
          forward_days:  افق پیش‌بینی (روز)
        """
        if signal_name not in self.signals.columns:
            logger.error(f"سیگنال '{signal_name}' پیدا نشد")
            return None

        pcol = price_col or self.prices.columns[0]
        signals = self._ensure_datetime(self.signals)
        prices  = self._ensure_datetime(self.prices)

        # بازده forward
        p = prices[pcol].astype(float)
        fwd_ret = p.shift(-forward_days) / p - 1.0

        # اطمینان از ایندکس مشترک
        common = signals.index.intersection(fwd_ret.index)
        signal_s = signals.loc[common, signal_name]
        fwd_ret   = fwd_ret.loc[common]

        windows = self._make_windows(common)
        if not windows:
            logger.warning("تعداد داده‌ها برای walk-forward کافی نیست")
            return None

        period_results = []

        for w in windows:
            # ─── Train slice ───
            train_mask = (common >= w["train_s"]) & (common < w["train_e"])
            train_sig  = signal_s[train_mask]
            # (در این پیاده‌سازی ساده از train فقط برای اعتبارسنجی استفاده می‌کنیم)
            if train_sig.dropna().__len__() < self.min_train_obs:
                logger.debug(f"دوره {w['idx']}: train کافی نیست ({len(train_sig.dropna())} روز)")
                continue

            # ─── Test slice ───
            test_mask = (common >= w["test_s"]) & (common < w["test_e"])
            test_sig  = signal_s[test_mask]
            test_ret  = fwd_ret[test_mask]

            metrics = self._strategy_metrics(test_sig, test_ret)
            if "error" in metrics:
                continue

            pr = PeriodResult(
                period_idx   = w["idx"],
                train_start  = str(w["train_s"].date()),
                train_end    = str(w["train_e"].date()),
                test_start   = str(w["test_s"].date()),
                test_end     = str(w["test_e"].date()),
                **metrics,
            )
            period_results.append(pr)

        if not period_results:
            logger.warning(f"'{signal_name}': هیچ دوره‌ای قابل ارزیابی نبود")
            return None

        # ─── متریک‌های ترکیبی OOS ───
        oos_ret_series = []
        for w, pr in zip(windows[:len(period_results)], period_results):
            test_mask = (common >= pd.Timestamp(pr.test_start)) & \
                        (common < pd.Timestamp(pr.test_end))
            pos = np.sign(signal_s[test_mask].fillna(0))
            oos_ret_series.append(pos * fwd_ret[test_mask])

        if oos_ret_series:
            oos_all = pd.concat(oos_ret_series).sort_index()
            oos_total  = float((1 + oos_all).prod() - 1)
            n_oos      = len(oos_all)
            oos_cagr   = float((1 + oos_total) ** (252.0 / max(n_oos, 1)) - 1)
            cumoos     = (1 + oos_all).cumprod()
            rm         = cumoos.expanding().max()
            oos_mdd    = float(((cumoos - rm) / rm).min())
            oos_mar    = oos_cagr / abs(oos_mdd) if oos_mdd < -1e-6 else (5.0 if oos_cagr > 0 else 0.0)
            oos_std    = float(oos_all.std(ddof=1))
            oos_sharpe = float(oos_all.mean() / oos_std * math.sqrt(252)) if oos_std > 1e-9 else 0.0
            oos_win    = float((oos_all > 0).mean())
            oos_hit    = float(
                (np.sign(signal_s[signal_s.index.isin(oos_all.index)].fillna(0)) ==
                 np.sign(fwd_ret[fwd_ret.index.isin(oos_all.index)])).mean()
            )
        else:
            oos_total = oos_cagr = oos_mdd = oos_mar = oos_sharpe = oos_win = oos_hit = 0.0

        consistency = float(
            sum(1 for p in period_results if p.total_return > 0) / len(period_results)
        )

        # ─── Verdict ───
        if (oos_mar >= self.MAR_TARGET
                and oos_sharpe >= self.SHARPE_TARGET
                and consistency >= self.CONSIST_TARGET):
            verdict = "✅ Deploy"
        elif consistency >= 0.5 or oos_sharpe >= 0.2:
            verdict = "⚠️ Monitor"
        else:
            verdict = "❌ Reject"

        return WalkForwardReport(
            signal_name       = signal_name,
            forward_days      = forward_days,
            n_periods         = len(period_results),
            periods           = period_results,
            oos_total_return  = round(oos_total, 4),
            oos_cagr          = round(oos_cagr, 4),
            oos_max_drawdown  = round(oos_mdd, 4),
            oos_mar_ratio     = round(oos_mar, 3),
            oos_sharpe        = round(oos_sharpe, 3),
            oos_win_rate      = round(oos_win, 3),
            oos_hit_rate      = round(oos_hit, 3),
            consistency       = round(consistency, 3),
            verdict           = verdict,
        )

    # ─── اجرای همه‌ی سیگنال‌ها ──────────────────────────────────
    def run_all(
        self,
        price_col: Optional[str] = None,
        forward_days: int = 7,
    ) -> Dict[str, WalkForwardReport]:
        """Walk-forward برای همه‌ی سیگنال‌های موجود."""
        results = {}
        for name in self.signals.columns:
            r = self.run(name, price_col, forward_days)
            if r is not None:
                results[name] = r
        return results

    # ─── گزارش ──────────────────────────────────────────────────
    @staticmethod
    def print_report(
        report: WalkForwardReport,
        show_periods: bool = True,
    ):
        """نمایش گزارش walk-forward برای یک سیگنال."""
        print("\n" + "═" * 75)
        print(f"  Walk-Forward: {report.signal_name}  |  افق: {report.forward_days} روز")
        print("═" * 75)

        if show_periods:
            print(f"\n  {'دوره':<5} {'Test Start':<12} {'Test End':<12} "
                  f"{'Return':>8} {'CAGR':>7} {'MDD':>7} {'MAR':>6} {'Sharpe':>7}")
            print("  " + "─" * 72)
            for p in report.periods:
                print(
                    f"  {p.period_idx:<5} {p.test_start:<12} {p.test_end:<12} "
                    f"{p.total_return:>8.2%} {p.cagr:>7.2%} {p.max_drawdown:>7.2%} "
                    f"{p.mar_ratio:>6.2f} {p.sharpe:>7.3f}"
                )

        print("\n  ─── نتیجه‌ی Out-Of-Sample کل ───")
        print(f"  دوره‌های OOS:        {report.n_periods}")
        print(f"  Consistency:        {report.consistency:.0%} دوره‌ها مثبت")
        print(f"  OOS Total Return:   {report.oos_total_return:.2%}")
        print(f"  OOS CAGR:           {report.oos_cagr:.2%}")
        print(f"  OOS Max Drawdown:   {report.oos_max_drawdown:.2%}")
        print(f"  OOS MAR Ratio:      {report.oos_mar_ratio:.3f}")
        print(f"  OOS Sharpe:         {report.oos_sharpe:.3f}")
        print(f"  OOS Win Rate:       {report.oos_win_rate:.1%}")
        print(f"  OOS Hit Rate:       {report.oos_hit_rate:.1%}")
        print(f"\n  ━━━ Verdict: {report.verdict} ━━━")
        print("═" * 75 + "\n")

    @staticmethod
    def print_summary(
        reports: Dict[str, WalkForwardReport],
        sort_by: str = "oos_mar_ratio",
    ):
        """خلاصه‌ی همه‌ی سیگنال‌ها در یک جدول."""
        if not reports:
            print("هیچ نتیجه‌ای برای نمایش وجود ندارد")
            return

        rows = sorted(reports.values(), key=lambda r: getattr(r, sort_by, 0), reverse=True)

        print("\n" + "═" * 90)
        print("  SENTINEL — Walk-Forward Summary")
        print("═" * 90)
        print(
            f"  {'Signal':<22} {'N':>4} {'Consist':>8} {'OOS_Ret':>9} "
            f"{'OOS_MAR':>8} {'OOS_SR':>7} {'HitRate':>8}  Verdict"
        )
        print("  " + "─" * 87)
        for r in rows:
            print(
                f"  {r.signal_name:<22} {r.n_periods:>4} {r.consistency:>8.0%} "
                f"{r.oos_total_return:>9.2%} {r.oos_mar_ratio:>8.3f} "
                f"{r.oos_sharpe:>7.3f} {r.oos_hit_rate:>8.1%}  {r.verdict}"
            )
        print("═" * 90)

        deploy  = [r for r in rows if r.verdict.startswith("✅")]
        monitor = [r for r in rows if r.verdict.startswith("⚠️")]
        reject  = [r for r in rows if r.verdict.startswith("❌")]

        print(f"\n  نتیجه: {len(deploy)} Deploy | {len(monitor)} Monitor | {len(reject)} Reject")
        if deploy:
            print(f"  سیگنال‌های آماده: {', '.join(r.signal_name for r in deploy)}")
        print()


# ─── اجرای مستقیم ───
if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    from signal_library import compute_signals

    print("Walk-Forward Backtest — داده‌ی مصنوعی...")
    rng = np.random.default_rng(42)
    n   = 500
    idx = pd.date_range("2022-06-01", periods=n, freq="D")

    # GBM با drift کوچک
    log_ret = rng.normal(0.0003, 0.028, n)
    prices  = pd.Series(100.0 * np.exp(np.cumsum(log_ret)), index=idx, name="BTC")

    fwd = prices.pct_change().shift(-7).fillna(0)

    mock_df = pd.DataFrame({
        "creator_count":         rng.integers(100, 500, n).astype(float),
        # galaxy_score با ارتباط کوچک به بازده آینده
        "galaxy_score":          50 + 15 * fwd * 8 + rng.normal(0, 8, n),
        "spam_pct":              rng.uniform(3, 18, n),
        "whale_ratio":           0.5 - 0.3 * fwd * 5 + rng.normal(0, 0.1, n),
        "stable_netflow_usd":    fwd * 1e10 + rng.normal(0, 3e8, n),
        "miner_to_exchange_usd": rng.uniform(10e6, 70e6, n),
        "sector_galaxy_score":   rng.uniform(45, 70, n),
    }, index=idx)

    signals_df = compute_signals(mock_df)
    prices_df  = prices.to_frame("BTC")

    wf = WalkForward(signals_df, prices_df, train_months=3, test_months=1)
    all_reports = wf.run_all(forward_days=7)
    WalkForward.print_summary(all_reports)

    if "galaxy_momentum" in all_reports:
        WalkForward.print_report(all_reports["galaxy_momentum"])
