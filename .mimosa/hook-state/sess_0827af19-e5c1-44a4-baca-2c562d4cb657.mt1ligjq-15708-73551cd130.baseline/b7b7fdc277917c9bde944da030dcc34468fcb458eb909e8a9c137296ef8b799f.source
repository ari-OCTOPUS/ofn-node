# -*- coding: utf-8 -*-
"""نرمال‌سازِ مشاهده — «کلمات/لاگ/تست → Observation ساخت‌یافته».

هیچ چیزِ این‌جا LLM صدا نمی‌زند (آن کارِ adapters/llm_adapter است).
"""
from __future__ import annotations

import re

from .schemas import Observation, clamp01

_SECRET_HINTS = re.compile(r"(api[_-]?key|token|password|secret|BEGIN [A-Z ]*PRIVATE KEY)",
                           re.IGNORECASE)
_MAX_SUMMARY = 400


def scrub_summary(text: str) -> str:
    """خلاصهٔ امن: کوتاه، بدونِ الگوی secret (جایگزینی با [REDACTED])."""
    t = (text or "").strip().replace("\r", " ")
    t = _SECRET_HINTS.sub("[REDACTED]", t)
    return t[:_MAX_SUMMARY]


def from_test_result(name: str, passed: bool, detail: str = "",
                     mission_id: str = "") -> Observation:
    return Observation(
        source_type="test", source_ref=name,
        payload_summary=scrub_summary(f"{'PASS' if passed else 'FAIL'}: {detail}"),
        evidence_strength=0.9 if passed is not None else 0.3,
        mission_id=mission_id, provenance="test-runner",
    )


def from_log(path_or_ref: str, line: str, mission_id: str = "",
             strength: float = 0.6) -> Observation:
    return Observation(
        source_type="log", source_ref=path_or_ref,
        payload_summary=scrub_summary(line),
        evidence_strength=clamp01(strength, 0.5),
        mission_id=mission_id, provenance="log-reader",
    )


def from_manual(text: str, who: str = "owner", mission_id: str = "") -> Observation:
    return Observation(
        source_type="manual", source_ref=f"manual:{who}",
        payload_summary=scrub_summary(text), evidence_strength=0.7,
        mission_id=mission_id, provenance=who,
    )


def mark_contradiction(a: Observation, b: Observation) -> None:
    """دو مشاهدهٔ ناسازگار را دوطرفه علامت بزن (idempotent)."""
    if b.observation_id not in a.contradictions:
        a.contradictions.append(b.observation_id)
    if a.observation_id not in b.contradictions:
        b.contradictions.append(a.observation_id)


def count_contradictions(observations: list) -> int:
    seen = set()
    for ob in observations or []:
        for cid in getattr(ob, "contradictions", []) or []:
            pair = tuple(sorted((ob.observation_id, cid)))
            seen.add(pair)
    return len(seen)
