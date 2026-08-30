"""contradiction.py — موتور تناقض و ابطال.

بند ۹: برای هر claim، فعالانه دنبال مدرک مخالف بگرد.
نباید فقط منابع تأییدکننده جمع کنی.

وضعیت‌های اجباری: TRIANGULATED / CONTESTED / FALSIFIED / INSUFFICIENT-EVIDENCE
کشف contested را actionable اعلام نکن، مگر آزمایش بعدی دقیقاً برای حل تناقض باشد.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable, Optional

from .contracts import Contradiction, Source

# نشانه‌های مخالفت در متن
_NEGATION_MARKERS_EN = [
    "not", "no longer", "denied", "disput", "contradict", "false", "wrong",
    "debunk", "refute", "fail", "failed", "does not", "did not", "cannot",
    "untrue", "mislead", "overstat", "exaggerat",
]
_NEGATION_MARKERS_FA = [
    "نه", "نمی", "رد", "نقص", "اشتباه", "غلط", "دروغ", "تعارض",
    "تناقض", "نادرست", "اغراق", "رد کرد", "نپذیرفت",
]
_CONTEST_MARKERS_EN = [
    "however", "but", "although", "while", "despite", "on the contrary",
    "critics", "skeptics", "questioned",
]
_CONTEST_MARKERS_FA = [
    "اما", "ولی", "گرچه", "با این حال", "در مقابل", "منتقدان", "شکاک",
]


@dataclass
class ContradictionResult:
    contradictions: list[Contradiction] = field(default_factory=list)
    status: str = "INSUFFICIENT-EVIDENCE"   # TRIANGULATED|CONTESTED|INSUFFICIENT-EVIDENCE
    notes: str = ""

    def as_dict(self) -> dict:
        return {
            "contradictions": [c.as_dict() for c in self.contradictions],
            "status": self.status,
            "notes": self.notes,
        }


def _has_negation(text: str) -> bool:
    low = (text or "").lower()
    markers = _NEGATION_MARKERS_EN + _NEGATION_MARKERS_FA
    return any(m in low for m in markers)


def _has_contest(text: str) -> bool:
    low = (text or "").lower()
    markers = _CONTEST_MARKERS_EN + _CONTEST_MARKERS_FA
    return any(m in low for m in markers)


def search_contradictions(
    claim: str,
    *,
    retriever: Optional[Callable[[str], list[dict]]] = None,
    competitor: str = "",
    max_queries: int = 2,
) -> ContradictionResult:
    """جست‌وجوی فعال برای شواهد مخالف claim.

    از retriever قابل‌تزریق استفاده می‌کند. query‌های مخالف می‌سازد:
      - "<claim> criticism"
      - "<claim> debunked"
      - "<claim> false"
    """
    result = ContradictionResult()
    if retriever is None:
        result.notes = "no-retriever; contradiction search skipped (cannot PASS)"
        return result

    contras: list[Contradiction] = []
    claim_short = claim[:120]
    queries = [
        f"{claim_short} criticism debunked",
        f"{claim_short} false wrong disputed",
        f"not true {claim_short}",
    ][:max_queries]

    for q in queries:
        try:
            hits = retriever(q) or []
        except Exception:
            hits = []
        for hit in hits[:5]:
            snippet = str(hit.get("snippet", ""))
            title = str(hit.get("title", ""))
            combined = f"{title} {snippet}"
            if _has_negation(combined) or _has_contest(combined):
                src = Source(
                    url=str(hit.get("url", "")),
                    title=title[:200],
                    tier="B",
                    snippet=snippet[:500],
                    publisher=hit.get("source", ""),
                    notes="contradiction-source",
                )
                contra = Contradiction(
                    claim=claim_short,
                    counter_claim=snippet[:300],
                    source=src,
                    severity="major" if _has_negation(combined) else "minor",
                    notes="auto-detected counter-evidence",
                )
                contras.append(contra)

    result.contradictions = _dedup_contras(contras)

    # تعیین وضعیت
    if not contras:
        result.status = "TRIANGULATED"  # هیچ مخالفت پیدا نشد → تأیید چندمنبعی ممکن
        result.notes = "no counter-evidence found in contradiction search"
    else:
        majors = [c for c in result.contradictions if c.severity == "major"]
        if majors:
            result.status = "CONTESTED"
            result.notes = f"{len(majors)} major contradiction(s) found → actionable نه"
        else:
            result.status = "CONTESTED"
            result.notes = f"{len(result.contradictions)} minor contradiction(s) → review needed"

    return result


def _dedup_contras(contras: list[Contradiction]) -> list[Contradiction]:
    """حذف contradictions تکراری (بر اساس counter_claim + url)."""
    seen = set()
    out = []
    for c in contras:
        key = (c.counter_claim[:80], c.source.url)
        if key not in seen:
            seen.add(key)
            out.append(c)
    return out


def reconcile_status(
    *,
    contradiction_result: ContradictionResult,
    evidence_sufficient: bool,
) -> str:
    """تصمیم نهایی وضعیت discovery بر اساس contradiction + evidence."""
    status = contradiction_result.status
    if status == "CONTESTED":
        return "contested"
    if status == "TRIANGULATED" and evidence_sufficient:
        return "triangulated"
    if status == "TRIANGULATED" and not evidence_sufficient:
        return "candidate"  # هنوز شواهد کافی نیست
    # INSUFFICIENT-EVIDENCE (retriever نبود)
    return "candidate"
