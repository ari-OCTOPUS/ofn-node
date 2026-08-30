"""competitor_intel.py — تحلیل رقابت شرکت‌های بزرگ + مزیت نامتقارن.

بند ۱۰: شرکت‌های بزرگ را با لوگو و شهرت مقایسه نکن. قابلیت واقعی را مقایسه کن.

فرمول مزیت نامتقارن:
  مزیت رقیب × نقطه‌ضعف ساختاری او × مزیت محلی/شخصی اختاپوس = فرصت رقابتی

برای هر مزیت پیشنهادی، شاهد یا آزمایش لازم است. صفت بدون سنجه ممنوع.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from .contracts import CompetitorRow, Source
from .source_policy import classify_tier, is_confirming

# ابعاد ارزیابی (بند ۱۰)
COMPETITION_DIMS = [
    "model-power", "product-velocity", "agent-architecture",
    "memory-personalization", "tool-use", "multimodality", "reliability",
    "safety-governance", "distribution", "data-moat", "pricing",
    "customer-ownership", "integrations", "local-market-depth", "latency",
    "transparency", "switching-cost", "operational-execution",
    "real-use-evidence",
]


@dataclass
class AsymmetryHypothesis:
    """فرضیهٔ مزیت نامتقارن اختاپوس."""

    asymmetry_id: str
    competitor_advantage: str
    competitor_structural_weakness: str
    octopus_local_advantage: str
    opportunity: str
    evidence_needed: str
    confidence: float = 0.0

    def as_dict(self) -> dict:
        return {
            "asymmetry_id": self.asymmetry_id,
            "competitor_advantage": self.competitor_advantage,
            "competitor_structural_weakness": self.competitor_structural_weakness,
            "octopus_local_advantage": self.octopus_local_advantage,
            "opportunity": self.opportunity,
            "evidence_needed": self.evidence_needed,
            "confidence": round(self.confidence, 3),
        }


def build_competitor_row(
    company: str,
    *,
    strengths: list[str],
    weaknesses: list[str],
    evidence: list[Source | dict],
    learn_for_octopus: list[str] | None = None,
    do_not_imitate: list[str] | None = None,
) -> CompetitorRow:
    """ساخت یک ردیف ماتریس رقابت با validation source-aware."""
    ev_dicts = [s.as_dict() if hasattr(s, "as_dict") else s for s in evidence]
    real_use = any(is_confirming(s) for s in ev_dicts)
    # novelty: اگر همه evidence‌ها از همان دامنهٔ شرکت باشند → "low"
    domains = {_domain_of(s) for s in ev_dicts}
    novelty = "low" if len(domains) <= 1 else "medium"

    return CompetitorRow(
        company=company,
        strengths=strengths,
        weaknesses=weaknesses,
        evidence=ev_dicts,
        novelty=novelty,
        learn_for_octopus=learn_for_octopus or [],
        do_not_imitate=do_not_imitate or [],
        real_use_evidence=real_use,
    )


def _domain_of(s: Source | dict) -> str:
    if isinstance(s, dict):
        from .source_policy import registrable_domain
        return registrable_domain(s.get("url", ""))
    from .source_policy import registrable_domain
    return registrable_domain(s.url)


def propose_asymmetry(
    competitor_rows: list[CompetitorRow],
) -> list[AsymmetryHypothesis]:
    """تولید فرضیه‌های مزیت نامتقارن از ماتریس رقابت.

    الگوریتم ساده: برای هر رقیب، هر «strength» را با هر «weakness» جفت کن و
    یک فرضیهٔ نامتقارن بساز. این فقط hypothesis است، نه claim نهایی.
    """
    hypotheses: list[AsymmetryHypothesis] = []
    counter = 0
    for row in competitor_rows:
        for strength in (row.strengths or []):
            for weakness in (row.weaknesses or []):
                counter += 1
                # مزیت محلی فرضی اختاپوس (الگوهای شناخته‌شده از charter)
                local = _guess_local_advantage(weakness)
                opp = (
                    f"اگر اختاپوس بتواند {local} را در جایی که {row.company} "
                    f"{weakness} دارد، به‌کار گیرد، می‌تواند در آن niche جلو بیفتد."
                )
                h = AsymmetryHypothesis(
                    asymmetry_id=f"asym-{counter:03d}",
                    competitor_advantage=strength,
                    competitor_structural_weakness=weakness,
                    octopus_local_advantage=local,
                    opportunity=opp,
                    evidence_needed=(
                        f"نشان بده که {row.company} واقعاً {weakness} (شاهد اولیه)، "
                        f"و اختاپوس می‌تواند {local} را در عمل پیاده کند (آزمایش E1)."
                    ),
                    confidence=0.0,  # بدون شاهد → ۰
                )
                hypotheses.append(h)
    return hypotheses


# مزیت‌های محلی فرضی اختاپوس (از charter بند ۱۰ + GOALS)
_OCTOPUS_LOCAL_ADVANTAGES = {
    "personalization": "شخصی‌سازی عمیق برای یک مالک",
    "memory": "حافظهٔ طولانی و محلی",
    "local-ops": "اتصال به عملیات واقعی یک کسب‌وکار",
    "arch-speed": "سرعت تغییر معماری",
    "australia": "زمینهٔ محلی استرالیا",
    "workflow": "workflow اختصاصی",
    "niche-cost": "هزینهٔ پایین برای niche مشخص",
    "data-ownership": "مالکیت داده",
    "multi-organ": "ترکیب چند اندام تخصصی",
    "continuous-decisions": "تصمیم‌های پیوسته و حافظه‌دار",
    "narrow-problem": "حل یک مسئلهٔ بسیار باریک بهتر از محصول عمومی",
}


def _guess_local_advantage(weakness: str) -> str:
    """حدس اینکه کدام مزیت محلی اختاپوس با این ضعف رقیب تناسب دارد."""
    low = (weakness or "").lower()
    if any(k in low for k in ("personal", "custom", "memory", "context")):
        return _OCTOPUS_LOCAL_ADVANTAGES["personalization"]
    if any(k in low for k in ("slow", "rigid", "bureaucra", "enterprise")):
        return _OCTOPUS_LOCAL_ADVANTAGES["arch-speed"]
    if any(k in low for k in ("expensive", "cost", "price", "overkill")):
        return _OCTOPUS_LOCAL_ADVANTAGES["niche-cost"]
    if any(k in low for k in ("local", "geography", "australia", "region")):
        return _OCTOPUS_LOCAL_ADVANTAGES["australia"]
    if any(k in low for k in ("general", "broad", "generic", "one-size")):
        return _OCTOPUS_LOCAL_ADVANTAGES["narrow-problem"]
    if any(k in low for k in ("data", "privacy", "ownership")):
        return _OCTOPUS_LOCAL_ADVANTAGES["data-ownership"]
    # default
    return _OCTOPUS_LOCAL_ADVANTAGES["multi-organ"]


def competitor_matrix_summary(rows: list[CompetitorRow]) -> dict:
    """خلاصهٔ ماتریس رقابت برای گزارش."""
    return {
        "competitors": [r.company for r in rows],
        "with_real_use_evidence": [r.company for r in rows if r.real_use_evidence],
        "coverage": round(len([r for r in rows if r.evidence]) / max(len(rows), 1), 3),
        "total_strengths": sum(len(r.strengths) for r in rows),
        "total_weaknesses": sum(len(r.weaknesses) for r in rows),
        "rows": [r.as_dict() for r in rows],
    }
