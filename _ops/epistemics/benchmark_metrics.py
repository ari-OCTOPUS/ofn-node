"""benchmark_metrics.py — متریک‌های benchmarkِ A/B/C (ADR-039 §10، Phase 2.6).

بازبینیِ Hypothesis-Ledger فهرستِ کاملی از متریک‌ها داد. این‌ها pure functions
هستند که روی خروجیِ benchmark کار می‌کنند — هیچ I/O، هیچ side-effect. Go/No-Go
با ترکیبِ این‌ها تصمیم گرفته می‌شود (تابعِ go_no_go).

نکتهٔ مهم: «useful outcome» باید **قبل از آزمون** تعریف شود؛ اگر بعداً با نگاه به
نتیجه تعریفش کنید، metric قابل‌اعتماد نیست (invariant #6 generated!=sourced).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Sequence


@dataclass(frozen=True)
class Outcome:
    """یک موردِ benchmark."""
    case_id: str
    arm: str                       # "A" | "B" | "C"
    predicted_prob: float = 0.0    # اعتمادِ گزارش‌شده ∈ [0,1]
    actual_outcome: float = 0.0    # 0.0 یا 1.0 (یا میانگین روی seeds)
    had_useful_finding: bool = False   # predeclared
    claim_count: int = 0
    unsupported_claims: int = 0    # claimهای بدون evidence
    pursued_false_hypotheses: int = 0
    useful_from_false: int = 0     # UFBR numerator
    label_leakage_events: int = 0  # HYPOTHESIS → FACT در response
    cost: float = 0.0
    had_external_effect: bool = False


# ---------------------------------------------------------------------------
# متریک‌های پایه
# ---------------------------------------------------------------------------
def brier_score(outcomes: Sequence[Outcome]) -> float:
    """Brier = mean( (p - o)^2 ). کمتر = بهتر؛ ۰ کامل، ۰.۲۵ تصادفی روی balanced."""
    if not outcomes:
        return float("nan")
    return sum((o.predicted_prob - o.actual_outcome) ** 2 for o in outcomes) / len(outcomes)


def calibration_error(outcomes: Sequence[Outcome], *, n_bins: int = 5) -> float:
    """اختلافِ میانگینِ |confidence − frequency| در bins.

    confidence‌ها به n_bins مساوی تقسیم می‌شوند؛ در هر bin میانگینِ p و o حساب
    می‌شود؛ خروجی میانگینِ وزن‌دارِ اختلاف. کمتر = کالیبره‌تر."""
    if not outcomes or n_bins < 1:
        return float("nan")
    bins: List[List[Outcome]] = [[] for _ in range(n_bins)]
    for o in outcomes:
        idx = min(n_bins - 1, max(0, int(o.predicted_prob * n_bins)))
        bins[idx].append(o)
    total, weighted = 0, 0.0
    for b in bins:
        if not b:
            continue
        mean_p = sum(x.predicted_prob for x in b) / len(b)
        mean_o = sum(x.actual_outcome for x in b) / len(b)
        w = len(b)
        weighted += abs(mean_p - mean_o) * w
        total += w
    return weighted / total if total else float("nan")


def unsupported_claim_rate(outcomes: Sequence[Outcome]) -> float:
    """نسبتِ claimهای بدون evidence بر کلِ claimها. کمتر = بهتر؛ Go: C <= A."""
    tot = sum(o.claim_count for o in outcomes)
    if tot == 0:
        return 0.0
    return sum(o.unsupported_claims for o in outcomes) / tot


def claim_precision(outcomes: Sequence[Outcome]) -> float:
    """نسبتِ claimهایی که واقعاً با evidence پشتیبانی می‌شوند. (۱ − unsupported_rate)"""
    return 1.0 - unsupported_claim_rate(outcomes)


def falsifier_coverage(claims_with_falsifier: int, total_claims: int) -> float:
    """نسبتِ فرضیه‌هایی که falsifier دارند."""
    if total_claims <= 0:
        return 0.0
    return claims_with_falsifier / total_claims


def discovery_yield(outcomes: Sequence[Outcome], *, budget: float = 1.0) -> float:
    """تعدادِ یافته‌های مفید به‌ازای budget. useful_finding قبل از آزمون تعریف شده."""
    if budget <= 0:
        return float("nan")
    return sum(1 for o in outcomes if o.had_useful_finding) / budget


def ufbr(outcomes: Sequence[Outcome]) -> float:
    """Useful-Findings-from-False-hypotheses Rate.

    بازبینی: UFBR = #(useful outcomes caused by a false hypothesis) /
                    #(pursued false hypotheses). useful outcome باید predeclared باشد."""
    pursued = sum(o.pursued_false_hypotheses for o in outcomes)
    useful = sum(o.useful_from_false for o in outcomes)
    if pursued == 0:
        return 0.0   # صادقانه: صفر pursued → صفر ratio (نه NaN)
    return useful / pursued


def leakage_rate(outcomes: Sequence[Outcome]) -> float:
    """نسبتِ مواردی که labelِ HYPOTHESIS در پاسخ به FACT تبدیل شده.

    Go criterion: C باید ۰ باشد در benchmark (هیچ نشتیِ label)."""
    tot = sum(o.claim_count for o in outcomes)
    if tot == 0:
        events = len(outcomes)
        return 0.0 if events == 0 else (
            sum(o.label_leakage_events for o in outcomes) / events)
    return sum(o.label_leakage_events for o in outcomes) / tot


def hypothesis_churn(created: int, refuted: int, revised: int, *, accumulated: int) -> dict:
    """سلامتِ چرخهٔ فرضیه: ایجاد/رد/بازنگری در برابرِ انباشتِ بی‌هدف.

    Churn سالم = created ≈ refuted+revised؛ انباشتِ بی‌هدف = created >>处置."""
    disposed = refuted + revised
    ratio = disposed / created if created > 0 else 0.0
    return {
        "created": created, "refuted": refuted, "revised": revised,
        "accumulated": accumulated,
        "disposition_ratio": round(ratio, 4),
        "healthy": ratio >= 0.3 and accumulated < created * 2,
    }


# ---------------------------------------------------------------------------
# Go/No-Go (بازبینیِ Hypothesis-Ledger، پیش‌ثبت‌شده)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class GoVerdict:
    ok: bool
    criteria: dict = field(default_factory=dict)
    reason: str = ""


def go_no_go(
    *,
    arm_a: Sequence[Outcome],
    arm_c: Sequence[Outcome],
    success_threshold: float = 0.05,
    budget_ceiling: float = 1.0,
) -> GoVerdict:
    """Go criteria (همه باید برقرار باشند):

      - C task success > A by predeclared threshold  (هیچ‌کدام منفی نباید باشد)
      - C unsupported-claim rate <= A
      - C leakage rate == 0
      - C cost <= budget ceiling
      - C no external effects == 0 events

    نکتهٔ صادقانه: «task success» اینجا useful-finding rate است (predeclared).
    threshold پیش‌فرض ۰.۰۵ است؛ مالک قبل از benchmark آن را تثبیت می‌کند.
    """
    a_success = discovery_yield(arm_a)
    c_success = discovery_yield(arm_c)
    a_unsupp = unsupported_claim_rate(arm_a)
    c_unsupp = unsupported_claim_rate(arm_c)
    c_leak = leakage_rate(arm_c)
    c_cost = sum(o.cost for o in arm_c)
    c_ext = sum(1 for o in arm_c if o.had_external_effect)

    criteria = {
        "c_success_gt_a_by_threshold": c_success - a_success >= success_threshold,
        "c_success": round(c_success, 4),
        "a_success": round(a_success, 4),
        "delta": round(c_success - a_success, 4),
        "threshold": success_threshold,
        "c_unsupported_le_a": c_unsupp <= a_unsupp + 1e-9,
        "c_unsupported": round(c_unsupp, 4),
        "a_unsupported": round(a_unsupp, 4),
        "c_leakage_zero": c_leak == 0.0,
        "c_leakage": round(c_leak, 4),
        "c_cost_within_budget": c_cost <= budget_ceiling + 1e-9,
        "c_cost": round(c_cost, 4),
        "budget_ceiling": budget_ceiling,
        "c_no_external_effects": c_ext == 0,
        "c_external_events": c_ext,
    }
    ok = all(v is True for k, v in criteria.items()
             if isinstance(v, bool))
    failed = [k for k, v in criteria.items() if v is False]
    reason = "all criteria met" if ok else "failed: " + ", ".join(failed)
    return GoVerdict(ok, criteria, reason)
