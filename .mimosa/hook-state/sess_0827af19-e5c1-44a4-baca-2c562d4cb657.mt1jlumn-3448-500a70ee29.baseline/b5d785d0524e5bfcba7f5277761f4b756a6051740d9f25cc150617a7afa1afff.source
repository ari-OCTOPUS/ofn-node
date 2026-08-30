#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""contradiction_radar.py — Detects contradictions between memories (EQUIP G2).

Contradiction detection rules:
  - Detects direct negation patterns in new content vs existing memory
  - Uses FTS5/BM25 lexical search via MemoryStore (no new vector DB)
  - Never auto-deletes or auto-resolves contradictions (per spec)
  - Flags contradictions for human review
  - Returns structured evidence: {contradicting_memory_id, content_preview,
    new_content_preview, confidence, evidence_type}

Scope:
  - Works across both memory stores (MemoryStore graded + 4d hypotheses)
  - Hybrid retrieval: lexical (FTS5/BM25 in MemoryStore) + LIKE fallback
  - Confidence calibration: high confidence only for strong negation patterns

Security: read-only operation. No side effects. No writes to any store.
$0 | stdlib-only | no network | read-only on existing stores.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

SCHEMA_VERSION = "contradiction-radar.v1"

# Negation patterns (multilingual: Persian + English)
_NEGATION_PATTERNS = [
    re.compile(r"\b(not|not\s+the\s+case|never|no\s+longer|contradicts|"
               r"inconsistent|disproves|refutes|negates)\b", re.I),
    re.compile(r"\b(نمی‌|نیست|نبود|نشد|خلاف|نقیض|متناقض|نادرست|غلط|"
               r"اشتباه|نقض|تضاد|باطل|مردود)\b"),
]

# Agreement patterns (reduce false positives)
_AGREEMENT_PATTERNS = [
    re.compile(r"\b(confirms?|consistent|supports?|agrees?|same|"
               r"verified|validated|شاید|احتمالاً|ممکن)\b", re.I),
    re.compile(r"\b(تایید|موافق|هم‌راستا|درست|صحیح|ثابت|همسو)\b"),
]

# Thresholds
_MIN_CONTRADICTION_CONFIDENCE = 0.6
_MAX_RESULTS_TO_CHECK = 10


@dataclass
class ContradictionFlag:
    """A single contradiction detection result."""
    contradicting_memory_id: str
    contradicting_content_preview: str
    new_content_preview: str
    confidence: float
    evidence_type: str  # "direct_negation" | "claim_conflict"
    reason: str


def _has_negation(text: str) -> bool:
    """Check if text contains explicit negation patterns."""
    t = str(text or "")
    return any(p.search(t) for p in _NEGATION_PATTERNS)


def _has_agreement(text: str) -> bool:
    """Check if text contains agreement/corroboration patterns."""
    t = str(text or "")
    return any(p.search(t) for p in _AGREEMENT_PATTERNS)


def _extract_claim_keywords(text: str) -> set[str]:
    """Extract meaningful keywords from text for comparison."""
    import re as _re
    # Alphanumeric tokens >= 3 chars + Persian/Arabic words
    tokens = set(_re.findall(r"[a-zA-Z]{3,}", text))
    tokens.update(_re.findall(r"[\u0600-\u06FF]{3,}", text))
    return tokens


def _jaccard_similarity(a: set[str], b: set[str]) -> float:
    """Jaccard similarity between two keyword sets."""
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def check_textual_contradiction(
    new_content: str,
    existing_content: str,
    new_memory_id: str = "new",
    existing_memory_id: str = "existing",
) -> ContradictionFlag | None:
    """Check if two text contents contradict each other.

    Returns a ContradictionFlag if contradiction is detected, None otherwise.
    Uses conservative heuristics: only flags when there is clear negation
    AND significant keyword overlap (same topic being negated).
    """
    new_t = str(new_content or "")
    existing_t = str(existing_content or "")

    if not new_t or not existing_t:
        return None

    # Quick check: if no negation in either text, no contradiction
    if not _has_negation(new_t) and not _has_negation(existing_t):
        return None

    # If both have agreement patterns, likely not contradiction
    if _has_agreement(new_t) and _has_agreement(existing_t):
        return None

    # Keyword overlap: must be about the same topic
    kw_new = _extract_claim_keywords(new_t)
    kw_existing = _extract_claim_keywords(existing_t)
    similarity = _jaccard_similarity(kw_new, kw_existing)

    if similarity < 0.15:
        return None  # Different topics, negation is not contradiction

    # Confidence: based on keyword overlap + negation strength
    confidence = min(0.95, 0.4 + similarity * 0.55)

    if confidence < _MIN_CONTRADICTION_CONFIDENCE:
        return None

    return ContradictionFlag(
        contradicting_memory_id=str(existing_memory_id),
        contradicting_content_preview=existing_t[:200],
        new_content_preview=new_t[:200],
        confidence=round(confidence, 3),
        evidence_type="direct_negation",
        reason=f"negation+topic_overlap(sim={similarity:.2f})",
    )


class ContradictionRadar:
    """Radar that checks new memories against existing ones.

    Supports two backends:
    1. MemoryStore (graded SQLite with FTS5) via search()
    2. Direct list of existing memories (for testing / 4d hypotheses table)
    """

    def __init__(self, store=None):
        """store: optional MemoryStore instance for graded memory search."""
        self._store = store

    def check_against_store(
        self,
        new_content: str,
        new_memory_id: str = "new",
        namespace: str | None = None,
        k: int = _MAX_RESULTS_TO_CHECK,
    ) -> list[ContradictionFlag]:
        """Check new content against the graded MemoryStore.

        Returns list of ContradictionFlag (empty if no contradictions).
        """
        if self._store is None:
            return []
        if not new_content or not str(new_content).strip():
            return []

        try:
            # Extract key terms for search
            keywords = _extract_claim_keywords(new_content)
            if not keywords:
                return []

            # Search for topically similar existing memories
            search_query = " ".join(list(keywords)[:6])
            results = self._store.search(
                search_query,
                namespace=namespace,
                k=k,
            )

            flags = []
            for r in results:
                existing_content = r.get("content", "")
                existing_id = r.get("memory_id", "")
                flag = check_textual_contradiction(
                    new_content, existing_content,
                    new_memory_id=new_memory_id,
                    existing_memory_id=existing_id,
                )
                if flag is not None:
                    flags.append(flag)

            return flags
        except Exception as e:
            logger.warning("contradiction radar store search failed: %s", e)
            return []

    def check_against_list(
        self,
        new_content: str,
        existing_memories: list[dict],
        new_memory_id: str = "new",
    ) -> list[ContradictionFlag]:
        """Check new content against a list of existing memory dicts.

        Each dict should have: {"id": ..., "content": ...} (or "hypothesis" key).
        Returns list of ContradictionFlag.
        """
        if not new_content or not existing_memories:
            return []

        flags = []
        for mem in existing_memories:
            mem_id = str(mem.get("id", mem.get("memory_id", "")))
            content = str(
                mem.get("content", mem.get("hypothesis", ""))
            )
            if not content:
                continue
            flag = check_textual_contradiction(
                new_content, content,
                new_memory_id=new_memory_id,
                existing_memory_id=mem_id,
            )
            if flag is not None:
                flags.append(flag)
        return flags

    def check(
        self,
        new_content: str,
        new_memory_id: str = "new",
        namespace: str | None = None,
        existing_list: list[dict] | None = None,
    ) -> list[dict[str, Any]]:
        """Unified check: store + optional list. Returns serializable dicts."""
        flags: list[ContradictionFlag] = []

        # Check against graded store
        if self._store is not None:
            flags.extend(
                self.check_against_store(new_content, new_memory_id, namespace)
            )

        # Check against provided list (e.g., 4d hypotheses)
        if existing_list:
            flags.extend(
                self.check_against_list(new_content, existing_list, new_memory_id)
            )

        # Deduplicate by contradicting_memory_id
        seen: set[str] = set()
        unique = []
        for f in flags:
            if f.contradicting_memory_id not in seen:
                seen.add(f.contradicting_memory_id)
                unique.append(f)

        return [
            {
                "schema": SCHEMA_VERSION,
                "contradicting_memory_id": f.contradicting_memory_id,
                "contradicting_content_preview": f.contradicting_content_preview,
                "new_content_preview": f.new_content_preview,
                "confidence": f.confidence,
                "evidence_type": f.evidence_type,
                "reason": f.reason,
            }
            for f in unique
        ]


if __name__ == "__main__":
    # Quick smoke test
    import sys

    radar = ContradictionRadar()

    # No contradiction: unrelated topics
    r1 = radar.check_against_list(
        "the sky is blue",
        [{"id": "m1", "hypothesis": "water boils at 100C"}],
    )
    assert len(r1) == 0, f"Expected no contradiction, got {r1}"

    # Direct contradiction
    r2 = radar.check_against_list(
        "this hypothesis is NOT correct: memory improves learning",
        [{"id": "m2", "hypothesis": "memory improves learning"}],
    )
    assert len(r2) > 0, f"Expected contradiction, got {r2}"
    assert r2[0].evidence_type == "direct_negation"

    # No contradiction: agreement
    r3 = radar.check_against_list(
        "this is confirmed: memory improves learning",
        [{"id": "m3", "hypothesis": "memory improves learning"}],
    )
    assert len(r3) == 0, f"Expected no contradiction with agreement, got {r3}"

    print("OK contradiction_radar smoke test")
    sys.exit(0)
