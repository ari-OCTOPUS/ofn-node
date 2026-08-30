#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""swap_consistency.py — ابزار سنجش سازگاری جایگاه (position/swap consistency).

این ماژول اندازهگیری را بهعنوان ابزار سنجش میسازد (فاز «ابزار سنجش»
MEGA-FINISH-ALL-v1) و عمداً هیچ تابعی برچسب VERIFIED تولید نمیکند؛
حداکثر MEASURED. سه محافظ قراردادی:

  1. هیچ تابعی «VERIFIED» برچسب نمیدهد (حداکثر MEASURED / OBSERVED).
  2. پیکربندی dataclass با frozen=True است — آستانهها پیش از دیدن داده ثبت
     میشوند و پس از دیدن نتیجه قابل تغییر نیستند (LAW-07).
  3. هر VOID با دلیل ثبت میشود؛ هرگز حذف یا بهعنوان معتبر شمرده نمیشود
     (LAW-03, R10).

اعداد مبنای این ماژول (روش مستقل، timestamp ثبت میشود):
  - نرخ VOID مشاهدهشده = 8/59 ≈ 13.56٪ (path: 06-EVIDENCE/.../live4 + GATE3)
  - احتمال دیدن ۰/۲۰ با نرخ واقعی 13.56٪ = (1-p)^20 ≈ 5.42٪
  - کران بالای ۹۵٪ برای ۰/۲۰: Wilson ≈ 16.1٪ ؛ Clopper-Pearson یکطرفه ≈ 13.9٪
  - سایزینگ ۹۵٪ اطمینان (نه انتظاری) برای ۳۰ معتبر: 39 تلاش (p=13.56٪)، 46 (24.5٪)

stdlib-only · fail-soft · هیچ شبکهای · هیچ نوشتنی جز receipt صریح.
"""
from __future__ import annotations

import hashlib
import json
import math
import time
from dataclasses import dataclass
from typing import Iterable

SCHEMA = "swap-consistency.v1"
JUDGE_CONTRACT_VERSION = "v4a-single-token-plus-fallback"
GRADE_MAX = "MEASURED"  # هیچ خروجی بالاتر از MEASURED نیست


@dataclass(frozen=True)
class SwapConfig:
    """آستانههای پیشثبتشده — frozen=True؛ تغییر پس از دیدن نتیجه ممنوع."""
    rs_min: float = 0.9            # کمینهٔ نرخ سازگاری برای «پایدار»
    alpha: float = 0.005           # سطح معناداری یکدستی تصادفی → k_min=9
    wilson_z: float = 1.96         # 95% CI
    required_confidence: float = 0.95
    schema: str = SCHEMA


def wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """فاصلهٔ اطمینان Wilson برای نسبت. n=0 → (0,0)."""
    if n <= 0:
        return (0.0, 0.0)
    k = max(0, min(int(k), int(n)))
    z2 = z * z
    center = (k + z2 / 2.0) / (n + z2)
    half = (z / (n + z2)) * math.sqrt(k * (n - k) / n + z2 / 4.0)
    return (max(0.0, center - half), min(1.0, center + half))


def unanimity_p_value(k: int) -> float:
    """احتمال یکدستی دوطرفه زیر سکهٔ منصف: 2^(1-k). k=5→6.25٪ · k=9→0.39٪ · k=11→0.098٪."""
    return 2.0 ** (1 - max(0, int(k)))


def min_k_for_alpha(alpha: float) -> int:
    """کوچکترین K که یکدستی تصادفی را زیر alpha میبرد."""
    k = 1
    while unanimity_p_value(k) > alpha:
        k += 1
    return k


def _binom_sf_at_least(target: int, n: int, p: float) -> float:
    """P(X >= target | X~Bin(n,p)) — جمع دقیق با comb (n کوچک)."""
    if target <= 0:
        return 1.0
    if n < target:
        return 0.0
    total = 0.0
    for k in range(target, n + 1):
        total += math.comb(n, k) * (p ** k) * ((1 - p) ** (n - k))
    return total


def required_attempts(valid_target: int, void_rate: float,
                      confidence: float = 0.95) -> int:
    """تعداد تلاش لازم برای رسیدن به valid_target نمونهٔ معتبر با اطمینان confidence.

    روش: binomial؛ نه مقدار انتظاری (انتظاری فقط ~50٪ شانس میدهد).
    خروجی = کمینهٔ n با P(>=target معتبر) >= confidence.
    """
    conf = float(confidence)
    p_ok = 1.0 - float(void_rate)
    if p_ok <= 0.0:
        return math.inf
    n = int(valid_target)
    while _binom_sf_at_least(valid_target, n, p_ok) < conf:
        n += 1
    return n


@dataclass(frozen=True)
class ReliabilityGate:
    """دروازهٔ اجباری پیش از هر طبقهبندی جایگاه."""
    cfg: SwapConfig = SwapConfig()

    def evaluate(self, rs_ab: float, k_ab: int, rs_ba: float, k_ba: int) -> dict:
        """خروجی: {ok, verdict, reason, k_min, details}.

        verdict ∈ {STABLE, INSTABILITY_SIGNIFICANT, RANDOMNESS_UNRESOLVED}.
        """
        k_min = min_k_for_alpha(self.cfg.alpha)
        if k_ab < k_min or k_ba < k_min:
            return {
                "ok": False, "verdict": "RANDOMNESS_UNRESOLVED",
                "reason": f"underpowered: k_ab={k_ab}, k_ba={k_ba} < k_min={k_min} "
                          f"(یکدستی تصادفی با K={k_min} ≈ {unanimity_p_value(k_min):.4%})",
                "k_min": k_min,
                "rs_ab": float(rs_ab), "rs_ba": float(rs_ba),
            }
        low = []
        if rs_ab < self.cfg.rs_min:
            low.append(f"rs_ab={rs_ab} < {self.cfg.rs_min}")
        if rs_ba < self.cfg.rs_min:
            low.append(f"rs_ba={rs_ba} < {self.cfg.rs_min}")
        if low:
            return {
                "ok": True, "verdict": "INSTABILITY_SIGNIFICANT",
                "reason": "؛ ".join(low), "k_min": k_min,
                "rs_ab": float(rs_ab), "rs_ba": float(rs_ba),
            }
        return {
            "ok": True, "verdict": "STABLE", "reason": "both orders above threshold",
            "k_min": k_min, "rs_ab": float(rs_ab), "rs_ba": float(rs_ba),
        }


def swap_consistency_rate(consistent: int, total: int,
                          cfg: SwapConfig = SwapConfig()) -> dict:
    """نرخ سازگاری با نگاشت برنده به بازوی اصلی + Wilson CI + برچسب MEASURED."""
    rate = (consistent / total) if total > 0 else None
    lo, hi = wilson_ci(consistent, total, cfg.wilson_z)
    return {
        "schema": SCHEMA, "grade": GRADE_MAX,
        "consistent": int(consistent), "total": int(total),
        "rate": rate, "wilson_95_ci": [round(lo, 4), round(hi, 4)],
        "label": "MEASURED", "method": "winner-mapped-to-base-arm",
    }


def classify_swap(ab_consistent: int, ab_total: int,
                  ba_consistent: int, ba_total: int,
                  cfg: SwapConfig = SwapConfig()) -> dict:
    """جدول چهارحالتهٔ سازگاری جایگاه.

    CONSISTENT            — برنده در هر دو ترتیب یکی است و گیت رد نشده.
    SECOND_POSITION_BIAS  — برنده با جایگاه عوض میشود (وابسته به جایگاه دوم).
    FIRST_POSITION_BIAS   — وابسته به جایگاه اول.
    RANDOMNESS_UNRESOLVED — گیت قابلیتاطمینان رد شد (K کم یا نرخ پایینِ شاهد).
    فقط دو حالت bias پس از عبور از گیت صادر میشوند.
    """
    rs_ab = (ab_consistent / ab_total) if ab_total else None
    rs_ba = (ba_consistent / ba_total) if ba_total else None
    gate = ReliabilityGate(cfg).evaluate(
        rs_ab if rs_ab is not None else 0.0, int(ab_total),
        rs_ba if rs_ba is not None else 0.0, int(ba_total))
    # فقط گیتِ «بیاطلاعی» طبقهبندی را میبندد؛ ناپایداریِ معنادار (K کافی با
    # rs پایین) خودش شاهدِ وابستگیِ جایگاه است و مجوزِ bias است (بازبینی: RS_BA
    # پایین با K کافی = شاهد معنادارِ ناپایداری).
    if gate["verdict"] == "RANDOMNESS_UNRESOLVED":
        return {
            "schema": SCHEMA, "grade": GRADE_MAX,
            "verdict": "RANDOMNESS_UNRESOLVED",
            "gate": gate, "rs_ab": rs_ab, "rs_ba": rs_ba,
            "method": "classify_swap",
        }
    if rs_ab is None or rs_ba is None or rs_ab == rs_ba:
        verdict = "CONSISTENT"
    elif rs_ab > rs_ba:
        verdict = "SECOND_POSITION_BIAS"
    else:
        verdict = "FIRST_POSITION_BIAS"
    return {
        "schema": SCHEMA, "grade": GRADE_MAX, "verdict": verdict,
        "gate": gate, "rs_ab": rs_ab, "rs_ba": rs_ba,
        "method": "classify_swap",
    }


def void_breakdown(rows: Iterable[dict]) -> dict:
    """VOID تفکیکشده به format/judge/provider/fallback — یک عدد کل شکنندگی را پنهان میکند."""
    out = {"format_void": 0, "judge_void": 0, "provider_void": 0,
           "fallback_void": 0, "other_void": 0, "total_void": 0, "rows_scanned": 0}
    for r in rows:
        out["rows_scanned"] += 1
        reason = str((r or {}).get("void_reason") or (r or {}).get("reason") or "").lower()
        if "format" in reason or "parse" in reason or "json" in reason:
            out["format_void"] += 1
        elif "judge" in reason:
            out["judge_void"] += 1
        elif "provider" in reason or "upstream" in reason or "network" in reason:
            out["provider_void"] += 1
        elif "fallback" in reason:
            out["fallback_void"] += 1
        else:
            out["other_void"] += 1
        out["total_void"] += 1
    return {"schema": SCHEMA, "grade": GRADE_MAX, "method": "void_breakdown", **out}


def receipt(*, caller: str, inputs: dict, seed: str = "", judge_version: str = "") -> dict:
    """رسید هر فراخوانی: هش ورودی، K، نسخهٔ قرارداد داور، timestamp — برای replay."""
    canonical = json.dumps({"caller": caller, "inputs": inputs, "seed": seed,
                            "judge_version": judge_version or JUDGE_CONTRACT_VERSION},
                           ensure_ascii=False, sort_keys=True)
    return {
        "schema": SCHEMA, "grade": GRADE_MAX,
        "caller": caller, "seed": seed,
        "judge_contract_version": judge_version or JUDGE_CONTRACT_VERSION,
        "input_hash": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        "ts": time.time(), "ts_iso": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }


if __name__ == "__main__":
    import sys
    demo = {
        "ab_consistent": 4, "ab_total": 5, "ba_consistent": 3, "ba_total": 5,
        "void_rate": 8 / 59,
    }
    print(json.dumps(classify_swap(demo["ab_consistent"], demo["ab_total"],
                                   demo["ba_consistent"], demo["ba_total"]),
                     ensure_ascii=False, indent=1))
    print("required_attempts(30, 13.56%) =",
          required_attempts(30, demo["void_rate"]))
    print("required_attempts(30, 24.5%)  =",
          required_attempts(30, 0.245))
    sys.exit(0)
