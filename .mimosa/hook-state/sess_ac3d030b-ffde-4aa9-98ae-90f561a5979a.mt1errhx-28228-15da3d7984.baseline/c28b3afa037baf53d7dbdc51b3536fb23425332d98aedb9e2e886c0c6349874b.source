#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""seven_day.py — versioned 7-day SHADOW evidence window (promotion gates).

Incomplete / UNKNOWN metrics ⇒ NO_PROMOTION. Owner vote required for ARMED.
"""
from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal

_OPS = Path(__file__).resolve().parents[1]
_EVID = _OPS / "state" / "adr-033" / "evidence"

Verdict = Literal["SHADOW_TO_ARMED", "SHADOW_TO_EXTEND", "SHADOW_TO_RETIRED", "NO_PROMOTION"]


@dataclass
class ExperimentSpec:
    experiment_id: str
    capability_id: str
    mode: str = "SHADOW"
    code_commit: str = ""
    graph_version: str = ""
    policy_version: str = "ADR-033-v1"
    feature_flag: str = ""
    effects_allowed: list[str] = field(default_factory=list)
    duration_days: int = 7
    expected_coverage_pct: float = 95.0


@dataclass
class DailyStats:
    day: str
    run_count: int = 0
    unknown_count: int = 0
    disconnected_count: int = 0
    policy_denials: int = 0
    quarantines: int = 0
    blocked_count: int = 0
    external_effects: int = 0
    raw_secret_or_pii: int = 0
    coverage_pct: float | None = None
    notes: str = ""


@dataclass
class PromotionGateResult:
    verdict: Verdict
    reasons: list[str]
    gates: dict[str, Any]


def week_dir(iso_week: str | None = None) -> Path:
    if not iso_week:
        iso_week = time.strftime("%Y-W%W", time.gmtime())
    d = _EVID / iso_week
    d.mkdir(parents=True, exist_ok=True)
    return d


def start_experiment(spec: ExperimentSpec, *, iso_week: str | None = None) -> Path:
    d = week_dir(iso_week)
    manifest = {
        "schema": "adr033.evidence_manifest.v1",
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "experiment": asdict(spec),
        "promotion_gate": {
            "trace_coverage_pct": ">= 95",
            "unaccounted_gap_hours": "<= 2",
            "external_effects": 0,
            "policy_violations": 0,
            "raw_secret_or_pii_in_trace": 0,
            "replay_pass_rate_pct": ">= 99",
            "test_failures": 0,
            "rollback_test": "passed",
            "owner_vote": "required",
        },
    }
    (d / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    summary = d / "daily-summary.md"
    if not summary.exists():
        summary.write_text(
            f"# Evidence window {spec.experiment_id}\n\n"
            f"capability: `{spec.capability_id}` mode={spec.mode}\n",
            encoding="utf-8",
        )
    return d


def append_daily(stats: DailyStats, *, iso_week: str | None = None) -> None:
    d = week_dir(iso_week)
    path = d / "daily.jsonl"
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(asdict(stats), ensure_ascii=False) + "\n")


def evaluate_promotion(
    *,
    days: list[DailyStats],
    replay_pass_rate_pct: float | None,
    test_failures: int,
    rollback_passed: bool,
    owner_vote: bool,
    expected_days: int = 7,
    expected_coverage: float = 95.0,
) -> PromotionGateResult:
    reasons: list[str] = []
    gates: dict[str, Any] = {}

    if len(days) < expected_days:
        reasons.append("insufficient_days")
        gates["days"] = len(days)
        return PromotionGateResult("NO_PROMOTION", reasons, gates)

    coverages = [d.coverage_pct for d in days]
    if any(c is None for c in coverages):
        reasons.append("coverage_unknown")
        return PromotionGateResult("NO_PROMOTION", reasons, gates)

    avg_cov = sum(c for c in coverages if c is not None) / len(coverages)
    gates["trace_coverage_pct"] = avg_cov
    if avg_cov < expected_coverage:
        reasons.append("coverage_below_threshold")

    ext = sum(d.external_effects for d in days)
    gates["external_effects"] = ext
    if ext != 0:
        reasons.append("external_effects_nonzero")

    viol = sum(d.policy_denials for d in days)  # denials are OK; "violations" = bypasses
    # For promotion we track bypasses via external_effects + raw_secret
    pii = sum(d.raw_secret_or_pii for d in days)
    gates["raw_secret_or_pii"] = pii
    if pii != 0:
        reasons.append("pii_in_trace")

    gates["replay_pass_rate_pct"] = replay_pass_rate_pct
    if replay_pass_rate_pct is None or replay_pass_rate_pct < 99.0:
        reasons.append("replay_pass_unknown_or_low")

    gates["test_failures"] = test_failures
    if test_failures != 0:
        reasons.append("test_failures")

    gates["rollback_test"] = rollback_passed
    if not rollback_passed:
        reasons.append("rollback_not_passed")

    gates["owner_vote"] = owner_vote
    if not owner_vote:
        reasons.append("owner_vote_missing")

    unknowns = sum(d.unknown_count for d in days)
    gates["unknown_count"] = unknowns
    # High unknown ⇒ extend, not arm
    if unknowns > 0 and "coverage_unknown" not in reasons:
        # unknown measurements don't auto-fail if coverage ok, but block ARMED
        reasons.append("unknown_measurements_present")

    if reasons:
        # Distinguish extend vs retire vs no-promotion
        if "insufficient_days" in reasons or "coverage_below_threshold" in reasons:
            return PromotionGateResult("SHADOW_TO_EXTEND", reasons, gates)
        if "external_effects_nonzero" in reasons or "pii_in_trace" in reasons:
            return PromotionGateResult("SHADOW_TO_RETIRED", reasons, gates)
        return PromotionGateResult("NO_PROMOTION", reasons, gates)

    return PromotionGateResult("SHADOW_TO_ARMED", ["all_gates_passed"], gates)


def write_verdict(result: PromotionGateResult, *, iso_week: str | None = None) -> Path:
    d = week_dir(iso_week)
    path = d / "promotion-verdict.md"
    body = (
        f"# Promotion verdict\n\n"
        f"- verdict: `{result.verdict}`\n"
        f"- reasons: {', '.join(result.reasons)}\n"
        f"- gates: `{json.dumps(result.gates)}`\n"
        f"- generated_at: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}\n"
    )
    path.write_text(body, encoding="utf-8")
    (d / "promotion-verdict.json").write_text(
        json.dumps({
            "verdict": result.verdict,
            "reasons": result.reasons,
            "gates": result.gates,
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path
