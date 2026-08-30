"""candidate_miner.py — ساخت کاندیداهای خام از observations.

از مشاهده‌های خام، claim‌های متمایز استخراج می‌کند، dedup می‌کند، و
کاندیداهای ranking-ready می‌سازد. هنوز تأیید نشده — فقط candidate.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable

from .contracts import Observation, Source
from .freshness import extract_date
from .source_policy import (
    are_independent,
    classify_tier,
    count_independent,
    is_confirming,
)


@dataclass
class Candidate:
    """یک کاندیدای کشف (قبل از triangulation)."""

    candidate_id: str
    claim: str
    observations: list[Observation] = field(default_factory=list)
    competitors: list[str] = field(default_factory=list)
    raw_kind: str = ""
    confirming_sources: int = 0
    independent_sources: int = 0
    has_date: bool = False
    has_primary: bool = False
    injection_flags: int = 0
    score_hint: float = 0.0

    def as_dict(self) -> dict:
        return {
            "candidate_id": self.candidate_id,
            "claim": self.claim,
            "competitors": self.competitors,
            "raw_kind": self.raw_kind,
            "confirming_sources": self.confirming_sources,
            "independent_sources": self.independent_sources,
            "has_date": self.has_date,
            "has_primary": self.has_primary,
            "injection_flags": self.injection_flags,
            "score_hint": round(self.score_hint, 3),
            "evidence_urls": [o.source.url for o in self.observations],
        }

    def as_dict_with_sources(self) -> dict:
        """نسخهٔ as_dict که observations/sources را هم شامل می‌شود (برای triangulate)."""
        d = self.as_dict()
        d["observations"] = [o.as_dict() for o in self.observations]
        d["sources"] = [o.source.as_dict() for o in self.observations]
        return d


def _normalize_claim(text: str) -> str:
    """نرمال‌سازی claim برای dedup: lowercase، حذف punctuation/تاریخ، فشرده‌سازی.

    مهم: تاریخ‌ها (ISO/loose) حذف می‌شوند چون دو شاهد که یک ادعا را با
    تاریخ گزارش/مشاهدهٔ متفاوت گزارش می‌کنند باید یک candidate باشند.
    """
    if not text:
        return ""
    low = text.lower().strip()
    # حذف تاریخ‌های ISO و loose (قبل از هر چیز، تا در identity اثر نگذارند)
    low = re.sub(r"\b(19|20)\d{2}[-/.](0[1-9]|1[0-2])[-/.](0[1-9]|[12]\d|3[01])\b", " ", low)
    # حذف سال‌های تنها (2026 و غیره) اگر همراه با کلمهٔ temporal نبودند → خطرناک
    # فقط سال‌های مستقل را حذف نکنیم چون ممکن است بخش معنایی باشند؛ ولی
    # تاریخ کامل را حذف می‌کنیم.
    # حذف whitespace‌های چندگانه
    low = re.sub(r"\s+", " ", low)
    # حذف نقل‌قول‌ها و براکت‌ها برای تطبیق بهتر
    low = re.sub(r"[\"'\[\](){}]", "", low)
    # truncation
    return low[:200].strip()


def mine_candidates(observations: Iterable[Observation]) -> list[Candidate]:
    """گروه‌بندی observations بر اساس شباهت claim (نه تطابق دقیق) → candidates.

    از تطبیق توکن‌های مشترک استفاده می‌کند تا دو منبعی که با واژه‌بندی کمی متفاوت
    همان ادعا را گزارش می‌کنند، در یک کاندیدای واحد گروه‌بندی شوند.
    """
    obs_list = list(observations)

    # مرحلهٔ ۱: نرمال‌سازی دقیق برای گروه‌های ابتدایی
    # مرحلهٔ ۲: ادغام گروه‌هایی که هم‌پوشانی توکنی بالایی دارند
    raw_groups: list[list[Observation]] = []
    raw_keys: list[str] = []
    for o in obs_list:
        key = _normalize_claim(o.claim)
        if not key:
            key = f"__raw_{o.observation_id}"
        # تلاش برای افزودن به گروه موجود با هم‌پوشانی توکنی بالا
        merged = False
        o_toks = _claim_tokens(key)
        for gi, gkey in enumerate(raw_keys):
            g_toks = _claim_tokens(gkey)
            if _token_overlap(o_toks, g_toks) >= 0.6:
                raw_groups[gi].append(o)
                merged = True
                break
        if not merged:
            raw_groups.append([o])
            raw_keys.append(key)

    candidates = []
    for group in raw_groups:
        if not group:
            continue
        # claim نمایشی: طولانی‌ترین claim گروه (احتمالاً کامل‌ترین)
        display_claim = max((o.claim for o in group), key=len)
        sources = [o.source for o in group]
        confirming = [s for s in sources if is_confirming(s)]
        competitors = sorted({o.competitor for o in group if o.competitor})
        inj = sum(1 for o in group if o.injection_risk)
        has_date = any(o.source.source_date for o in group)
        has_primary = any(classify_tier(s) == "A" for s in sources)
        key = _normalize_claim(display_claim)

        cand = Candidate(
            candidate_id="cand-" + (key[:12].replace(" ", "-") or "unknown"),
            claim=display_claim[:300],
            observations=group,
            competitors=competitors,
            raw_kind=group[0].raw_kind,
            confirming_sources=len(confirming),
            independent_sources=count_independent(confirming),
            has_date=has_date,
            has_primary=has_primary,
            injection_flags=inj,
            score_hint=_rank_hint(group),
        )
        candidates.append(cand)

    # sort: score_hint نزولی
    candidates.sort(key=lambda c: c.score_hint, reverse=True)
    return candidates


def _claim_tokens(normalized: str) -> set[str]:
    """توکن‌های claim نرمال‌شده برای تطبیق هم‌پوشانی."""
    toks = set(re.findall(r"[a-z0-9\u0600-\u06FF]{3,}", normalized or ""))
    return {t for t in toks if len(t) >= 3}


def _token_overlap(a: set[str], b: set[str]) -> float:
    """هم‌پوشانی Jaccard بین دو مجموعه توکن."""
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _rank_hint(group: list[Observation]) -> float:
    """امتیاز اولیه برای ranking کاندیداها (قبل از scoring کامل)."""
    score = 0.0
    sources = [o.source for o in group]
    confirming = [s for s in sources if is_confirming(s)]
    # تعداد منابع مستقل confirming
    score += count_independent(confirming) * 1.0
    # presence of primary source
    if any(classify_tier(s) == "A" for s in sources):
        score += 0.5
    # presence of date
    if any(o.source.source_date for o in group):
        score += 0.3
    # penalty for injection flags
    inj = sum(1 for o in group if o.injection_risk)
    score -= inj * 0.5
    # variety of competitors mentioned
    comps = {o.competitor for o in group if o.competitor}
    score += min(len(comps), 3) * 0.1
    return max(score, 0.0)


def dedupe_observations(observations: list[Observation]) -> list[Observation]:
    """حذف observations با URL یکسان (نرمال‌شده)."""
    seen = set()
    out = []
    for o in observations:
        if o.source.url in seen:
            continue
        seen.add(o.source.url)
        out.append(o)
    return out
