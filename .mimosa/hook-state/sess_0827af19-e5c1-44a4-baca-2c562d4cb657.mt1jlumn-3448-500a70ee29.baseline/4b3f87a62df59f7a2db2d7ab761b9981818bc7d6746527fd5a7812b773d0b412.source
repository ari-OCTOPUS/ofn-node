#!/usr/bin/env python3
"""Five-trial, side-effect-free discovery claim evaluator.

A candidate is accepted only when the same digest is observed in at least three
of the five fixed trials and every counted observation is novel, useful and
policy-compliant. This is an evaluation contract, not an AGI claim.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any, Callable, Iterable, Mapping

from .trace_schema import digest

FIXED_TRIALS = (11, 23, 37, 53, 71)


@dataclass(frozen=True)
class DiscoveryVerdict:
    accepted: bool
    candidate_digest: str
    repeat_count: int
    trial_count: int
    novel: bool
    useful: bool
    policy_compliant: bool
    repeatable: bool
    reason: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "accepted": self.accepted,
            "candidate_digest": self.candidate_digest,
            "repeat_count": self.repeat_count,
            "trial_count": self.trial_count,
            "novel": self.novel,
            "useful": self.useful,
            "policy_compliant": self.policy_compliant,
            "repeatable": self.repeatable,
            "reason": self.reason,
        }


def run_trials(candidate_fn: Callable[[int], Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Run exactly five fixed integer trials; the callback owns no effect port."""
    rows: list[dict[str, Any]] = []
    for trial in FIXED_TRIALS:
        raw = dict(candidate_fn(trial) or {})
        rows.append({
            "trial": trial,
            "observed": bool(raw.get("observed")),
            "candidate_digest": digest(raw.get("candidate")),
            "novel": bool(raw.get("novel")),
            "useful": bool(raw.get("useful")),
            "policy_compliant": bool(raw.get("policy_compliant")),
        })
    return rows


def evaluate(rows: Iterable[Mapping[str, Any]], *, minimum_repeat: int = 3) -> DiscoveryVerdict:
    data = [dict(row) for row in rows]
    trials = [row.get("trial") for row in data]
    if len(data) != 5 or tuple(trials) != FIXED_TRIALS:
        return DiscoveryVerdict(False, digest(None), 0, len(data), False, False,
                                False, False, "requires-exact-fixed-five-trials")

    observed = [row for row in data if bool(row.get("observed"))]
    counts = Counter(str(row.get("candidate_digest")) for row in observed)
    candidate_digest, repeat_count = counts.most_common(1)[0] if counts else (digest(None), 0)
    matching = [row for row in observed
                if str(row.get("candidate_digest")) == candidate_digest]
    novel = bool(matching) and all(bool(row.get("novel")) for row in matching)
    useful = bool(matching) and all(bool(row.get("useful")) for row in matching)
    compliant = bool(matching) and all(bool(row.get("policy_compliant")) for row in matching)
    repeatable = repeat_count >= int(minimum_repeat)
    accepted = novel and useful and compliant and repeatable
    reason = "accepted" if accepted else "predicate-or-repeatability-failed"
    return DiscoveryVerdict(accepted, candidate_digest, repeat_count, len(data),
                            novel, useful, compliant, repeatable, reason)
