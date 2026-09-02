#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""experiments — ExperimentProposer: propose, never execute.

Every experiment requires owner approval — that field is not configurable.
Sensitive targets (vocabulary/policy/gates/outbound) are escalated, never
queued as ordinary work.
"""
from __future__ import annotations

from dataclasses import dataclass, field

__all__ = ["Experiment", "ExperimentProposer", "SENSITIVE_MARKERS", "OUTCOMES"]

OUTCOMES = ("PR_CREATED", "QUEUED_WITH_REASON", "REJECTED_WITH_REASON",
            "ESCALATED_TO_OWNER")

SENSITIVE_MARKERS = ("kernel", "events.py", "vocabulary", "send", "outbound",
                     "wal", "policy", "gate", "owner", "consent", "payment-vocab")


@dataclass
class Experiment:
    experiment_id: str
    hypothesis: str
    treatment: str
    control: str
    metric: str
    stop_condition: str
    rollback: str
    owner_approval_required: bool = True   # structural: never False

    def as_dict(self) -> dict:
        return {"experiment_id": self.experiment_id, "hypothesis": self.hypothesis,
                "treatment": self.treatment, "control": self.control,
                "metric": self.metric, "stop_condition": self.stop_condition,
                "rollback": self.rollback,
                "owner_approval_required": self.owner_approval_required}


@dataclass
class Proposal:
    proposal_id: str
    title: str
    target: str
    experiment: Experiment | None = None
    outcome: str = ""
    reason: str = ""


class ExperimentProposer:
    def propose_from_lesson(self, lesson) -> Proposal:
        if lesson.status != "OPEN":
            return Proposal("", f"lesson {lesson.lesson_id} not OPEN", target="",
                            outcome="REJECTED_WITH_REASON",
                            reason="only OPEN lessons spawn experiments")
        if lesson.success and lesson.sample_size < 3:
            return Proposal(
                f"EXP-{lesson.lesson_id}", 
                "accumulate samples before revenue experiments",
                target="ofn/learning/",
                outcome="QUEUED_WITH_REASON",
                reason=f"n={lesson.sample_size} below 3 — underpowered, no experiment yet")
        text = lesson.lesson.lower()
        if any(m in text for m in ("payment_received", "vocabulary", "kernel")):
            return Proposal(
                f"EXP-{lesson.lesson_id}",
                "extend runtime vocabulary with VERIFIED economic outcome states",
                target="ofn/kernel/events.py",
                outcome="ESCALATED_TO_OWNER",
                reason="kernel vocabulary is a sealed policy surface "
                       "(quote_sent-class names are FORBIDDEN_EFFECT_KINDS by design); "
                       "adapter-level verified outcomes already recorded in this lane")
        if lesson.success:
            return Proposal(
                f"EXP-{lesson.lesson_id}",
                "vary one outreach parameter against control on next campaign batch",
                target="ofn/learning/",
                outcome="QUEUED_WITH_REASON",
                reason="experiment design ready; execution requires owner approval + "
                       "send authorization which this lane never produces")
        return Proposal(
            f"EXP-{lesson.lesson_id}",
            "test a differing outreach parameter (subject line / timing) on the "
            "silent segment",
            target="ofn/learning/",
            outcome="QUEUED_WITH_REASON",
            reason="differing-parameter test design ready; owner approval + send "
                   "authorization required (never produced here)")

    def decide_target(self, target: str) -> str:
        low = target.lower()
        if any(m in low for m in SENSITIVE_MARKERS):
            return "ESCALATED_TO_OWNER"
        if low.startswith(("ofn/learning/", "tests/test_economic_learning",
                           "docs/lanes/ECONOMIC-LEARNING", "09-LANES/ECONOMIC-LEARNING")):
            return "PR_CREATED"
        return "QUEUED_WITH_REASON"
