"""Explainable decision primitives.

These functions are deterministic and side-effect free. They intentionally do
not call models, connectors or storage so every safety boundary can test them
without secrets or network access.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


def clamp01(value: float | int | None, default: float = 0.5) -> float:
    """Normalize an already-scaled value into [0, 1]. Missing -> neutral.

    Neutral missing data is safe only because callers also get an
    `incomplete` flag from the score functions. High-risk missing data must be
    blocked by policy; scoring alone never grants permission to act.
    """
    if value is None:
        return default
    try:
        v = float(value)
    except (TypeError, ValueError):
        return default
    return max(0.0, min(1.0, v))


@dataclass(frozen=True)
class ScoreResult:
    score: float
    incomplete: bool
    components: Mapping[str, float]
    weights: Mapping[str, float]
    explanation: tuple[str, ...]
    recommendation: str = ""


def _missing(inputs: Mapping[str, object], keys: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(k for k in keys if inputs.get(k) is None)


def _weighted(parts: Mapping[str, float], weights: Mapping[str, float], positive: tuple[str, ...], negative: tuple[str, ...]) -> float:
    raw = sum(weights.get(k, 0.0) * parts[k] for k in positive)
    raw -= sum(weights.get(k, 0.0) * parts[k] for k in negative)
    # Weights are chosen so this is usually already [0,1]. Clamp anyway so UI
    # cannot show impossible numbers if an owner edits weights later.
    return clamp01(raw, 0.0)


LEAD_WEIGHTS = {"V": 0.22, "I": 0.22, "G": 0.15, "T": 0.13, "Q": 0.13, "R": 0.10, "C": 0.05}
SOURCE_WEIGHTS = {"I": 0.24, "X": 0.16, "E": 0.16, "O": 0.14, "A": 0.12, "C": 0.08, "R": 0.10}
STRATA_WEIGHTS = {"P": 0.30, "G": 0.20, "M": 0.20, "E": 0.15, "R": 0.15, "risk": 0.18, "cost": 0.07}
FITOUT_WEIGHTS = {"V": 0.25, "D": 0.25, "F": 0.20, "C": 0.15, "E": 0.15, "risk": 0.18, "cost": 0.07}
TENDER_WEIGHTS = {"P": 0.20, "G": 0.15, "E": 0.16, "D": 0.14, "M": 0.15, "Q": 0.12, "R": 0.12, "C": 0.06}


def lead_priority(values: Mapping[str, object], weights: Mapping[str, float] | None = None) -> ScoreResult:
    keys = ("V", "I", "G", "T", "Q", "R", "C")
    w = dict(weights or LEAD_WEIGHTS)
    p = {k: clamp01(values.get(k)) for k in keys}
    score = _weighted(p, w, ("V", "I", "G", "T", "Q"), ("R", "C"))
    miss = _missing(values, keys)
    exp = [f"امتیاز لید {round(score * 100)} از ۱۰۰ است."]
    if miss:
        exp.append("داده ناقص: " + ", ".join(miss) + " با مقدار خنثی حساب شد.")
    if p["R"] >= 0.70:
        exp.append("ریسک بالا است؛ اقدام بیرونی باید به مالک ارجاع شود.")
    if p["I"] >= 0.70 and p["G"] >= 0.60:
        exp.append("نیت خرید و تناسب جغرافیایی خوب است.")
    return ScoreResult(score, bool(miss), p, w, tuple(exp), _lead_rec(score, p["R"]))


def source_quality(values: Mapping[str, object], weights: Mapping[str, float] | None = None) -> ScoreResult:
    keys = ("I", "X", "E", "O", "A", "C", "R")
    w = dict(weights or SOURCE_WEIGHTS)
    p = {k: clamp01(values.get(k)) for k in keys}
    score = _weighted(p, w, ("I", "X", "E", "O", "A"), ("C", "R"))
    miss = _missing(values, keys)
    exp = [f"کیفیت منبع {round(score * 100)} از ۱۰۰ است."]
    if p["R"] >= 0.60:
        exp.append("ریسک consent/platform بالاست؛ فقط research یا owner-approved workflow.")
    if miss:
        exp.append("داده ناقص: " + ", ".join(miss))
    return ScoreResult(score, bool(miss), p, w, tuple(exp), _source_rec(score, p["R"]))


def b2b_account_score(segment: str, values: Mapping[str, object]) -> ScoreResult:
    seg = (segment or "strata").lower()
    if seg in {"fitout", "builder", "commercial_fitout"}:
        keys = ("V", "D", "F", "C", "E", "risk", "cost")
        w = FITOUT_WEIGHTS
        positive = ("V", "D", "F", "C", "E")
    else:
        keys = ("P", "G", "M", "E", "R", "risk", "cost")
        w = STRATA_WEIGHTS
        positive = ("P", "G", "M", "E", "R")
    p = {k: clamp01(values.get(k)) for k in keys}
    score = _weighted(p, w, positive, ("risk", "cost"))
    miss = _missing(values, keys)
    exp = [f"امتیاز حساب B2B {round(score * 100)} از ۱۰۰ است."]
    if seg in {"fitout", "builder", "commercial_fitout"}:
        exp.append("مدل fit-out روی ارزش پروژه، deadline، scope-fit، ظرفیت و evidence وزن می‌دهد.")
    else:
        exp.append("مدل strata/property روی portfolio، جغرافیا، maintenance-fit، evidence و repeat potential وزن می‌دهد.")
    if miss:
        exp.append("داده ناقص: " + ", ".join(miss))
    if p.get("risk", 0.0) >= 0.65:
        exp.append("ریسک policy/داده بالاست؛ outreach مجاز نیست.")
    return ScoreResult(score, bool(miss), p, w, tuple(exp), _account_rec(score, p.get("risk", 0.0)))


def tender_score(values: Mapping[str, object]) -> ScoreResult:
    keys = ("P", "G", "E", "D", "M", "Q", "R", "C")
    w = TENDER_WEIGHTS
    p = {k: clamp01(values.get(k)) for k in keys}
    score = _weighted(p, w, ("P", "G", "E", "D", "M", "Q"), ("R", "C"))
    miss = _missing(values, keys)
    if score >= 0.72 and p["R"] < 0.65:
        rec = "BID"
    elif score >= 0.48:
        rec = "CONSIDER"
    else:
        rec = "SKIP"
    exp = [f"Tender {rec}: امتیاز {round(score * 100)} از ۱۰۰."]
    if p["D"] < 0.35:
        exp.append("deadline tight/uncertain؛ آماده‌سازی bid ممکن است نرسد.")
    if p["R"] >= 0.65:
        exp.append("ریسک قراردادی/اطلاعاتی بالاست؛ owner review اجباری است.")
    if miss:
        exp.append("داده ناقص: " + ", ".join(miss))
    return ScoreResult(score, bool(miss), p, w, tuple(exp), rec)


def agent_utility(*, capability: float, trust: float, expected_value: float, cost: float, risk: float, risk_threshold: float = 0.65) -> ScoreResult:
    p = {"capability": clamp01(capability), "trust": clamp01(trust), "expected_value": clamp01(expected_value), "cost": clamp01(cost), "risk": clamp01(risk)}
    allowed = p["risk"] <= risk_threshold
    score = clamp01(p["capability"] * p["trust"] * p["expected_value"] - p["cost"] - p["risk"], 0.0)
    exp = [f"utility={score:.3f}"]
    if not allowed:
        exp.append("ریسک از آستانه بالاتر است؛ اجرا نمی‌شود و به مالک ارجاع می‌شود.")
    return ScoreResult(score, False, p, {}, tuple(exp), "EXECUTE" if allowed and score > 0 else "ESCALATE")


def update_trust(current: float, outcome_quality: float, *, alpha: float = 0.08, sample_count: int = 0, min_samples: int = 20) -> ScoreResult:
    cur = clamp01(current)
    oq = clamp01(outcome_quality)
    a = max(0.0, min(0.15, float(alpha)))
    new = clamp01((1.0 - a) * cur + a * oq)
    exp = [f"trust {cur:.2f} -> {new:.2f} با alpha={a:.2f}."]
    if sample_count < min_samples:
        exp.append("نمونه کافی نیست؛ فقط ثبت تاریخچه، نه تغییر routing.")
    return ScoreResult(new, False, {"current": cur, "outcome_quality": oq, "alpha": a}, {}, tuple(exp), "HISTORY_ONLY" if sample_count < min_samples else "ROUTING_ELIGIBLE")


def _lead_rec(score: float, risk: float) -> str:
    if risk >= 0.70:
        return "OWNER_REVIEW"
    if score >= 0.72:
        return "HOT"
    if score >= 0.45:
        return "WARM"
    return "NURTURE"


def _source_rec(score: float, risk: float) -> str:
    if risk >= 0.70:
        return "RESEARCH_ONLY"
    if score >= 0.70:
        return "PRIORITY_TEST"
    if score >= 0.45:
        return "WATCH"
    return "LOW_PRIORITY"


def _account_rec(score: float, risk: float) -> str:
    if risk >= 0.70:
        return "RESEARCH_ONLY"
    if score >= 0.78:
        return "HIGH_FIT"
    if score >= 0.52:
        return "QUALIFY"
    return "BACKLOG"
