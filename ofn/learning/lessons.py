#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lessons — LessonExtractor: honest lessons from thin evidence.

Iron rules (owner order B3), enforced here in code:
  - no general conclusion from a single payment;
  - correlation never written as causation;
  - every lesson carries supporting AND contradicting evidence;
  - zero-payment is a valid lesson but never a success;
  - local failure stays OPEN until a differing parameter is found.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
from dataclasses import dataclass, field

from .scorer import OutcomeScore

__all__ = ["Lesson", "LessonExtractor"]

CAUSATION_WORDS = ("caused", "because of", "led to", "نتیجهٔ مستقیم", "باعث")


def _utcnow() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _recheck_after(days: int) -> str:
    d = _dt.datetime.now(_dt.timezone.utc) + _dt.timedelta(days=days)
    return d.strftime("%Y-%m-%d")


@dataclass
class Lesson:
    lesson_id: str
    lesson: str
    supporting_evidence: list
    contradicting_evidence: list
    confidence: str            # low | medium  (high is not reachable from thin data)
    sample_size: int
    status: str                # OPEN | CONFIRMED (CONFIRMED needs owner-reviewed stats)
    recheck_at: str
    campaign_id: str = ""
    success: bool = False

    def as_dict(self) -> dict:
        return {k: getattr(self, k) for k in (
            "lesson_id", "lesson", "supporting_evidence", "contradicting_evidence",
            "confidence", "sample_size", "status", "recheck_at", "campaign_id",
            "success")}


class LessonExtractor:
    def extract(self, score: OutcomeScore, evidence: list[dict]) -> list[Lesson]:
        lessons: list[Lesson] = []
        n = len({e.get("ref", "") for e in evidence if e.get("kind") == "contact"})
        supp = [f"{e.get('kind')}:{e.get('ref')}" for e in evidence
                if e.get("kind") in ("contact", "response", "quote", "payment")]
        contra = [f"{e.get('kind')}:{e.get('ref')}" for e in evidence
                  if e.get("kind") == "counter_evidence"]

        if score.level == "VERIFIED_REVENUE":
            lessons.append(Lesson(
                lesson_id=self._lid(score, "verified-revenue"),
                lesson=(f"campaign {score.campaign_id}: verified payment observed "
                        f"after contact→response→quote — CORRELATION ONLY, no causal "
                        f"claim (n={max(n, 1)})"),
                supporting_evidence=supp, contradicting_evidence=contra or ["none recorded"],
                confidence="low", sample_size=max(n, 1),
                status="OPEN", recheck_at=_recheck_after(14),
                campaign_id=score.campaign_id, success=True))
        elif score.level in ("QUOTE_SIGNAL", "RESPONSE_SIGNAL"):
            lessons.append(Lesson(
                lesson_id=self._lid(score, "intermediate-signal"),
                lesson=(f"campaign {score.campaign_id}: {score.level.lower()} without "
                        f"verified payment — intermediate signal, not revenue "
                        f"(n={max(n, 1)}); continue observing"),
                supporting_evidence=supp, contradicting_evidence=contra or ["none recorded"],
                confidence="low", sample_size=max(n, 1),
                status="OPEN", recheck_at=_recheck_after(7),
                campaign_id=score.campaign_id, success=False))
        else:
            # includes zero-payment and no-response: valid economic data,
            # explicitly NOT success, and an OPEN informational failure that
            # stays open until a differing parameter is tested.
            lessons.append(Lesson(
                lesson_id=self._lid(score, "zero-payment-open"),
                lesson=(f"campaign {score.campaign_id}: no verified payment "
                        f"(payment_received_verified=false) — zero-payment is a valid "
                        f"economic observation, not success; local failure stays OPEN "
                        f"until a differing parameter is tested (n={max(n, 1)})"),
                supporting_evidence=supp or ["no positive economic evidence recorded"],
                contradicting_evidence=contra or ["none recorded"],
                confidence="low", sample_size=max(n, 1),
                status="OPEN", recheck_at=_recheck_after(7),
                campaign_id=score.campaign_id, success=False))
        return lessons

    @staticmethod
    def _lid(score: OutcomeScore, tag: str) -> str:
        digest = hashlib.sha256(f"{score.campaign_id}:{score.lead_id}:{tag}".encode()).hexdigest()[:8]
        return f"LES-{tag[:14]}-{digest}"
