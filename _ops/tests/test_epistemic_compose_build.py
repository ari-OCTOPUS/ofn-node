#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_epistemic_compose_build.py — dual-channel composer + cortex claim-builder."""
from __future__ import annotations

import sys
from pathlib import Path

_OPS = Path(__file__).resolve().parents[1]
if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))

from epistemics import compose as CP  # noqa: E402
from epistemics import claim_builder as CB  # noqa: E402


# ---------------------------------------------------------------------------
# dual-channel composer
# ---------------------------------------------------------------------------
def t_facts_and_hypotheses_separated():
    comp = CP.compose(
        observed=["beat=33613", "halted=False"],
        runtime_truth="coherence=0.96",
        claims=[{"claim_id": "h1", "world_mode": "hypothesis",
                 "epistemic_status": "unverified", "confidence": 0.3,
                 "prediction": "X increases Y"}])
    assert len(comp.observed_facts) == 3   # 2 observed + runtime_truth
    assert len(comp.hypotheses) == 1
    assert comp.hypotheses[0]["world_mode"] == "hypothesis"
    assert comp.has_leakage is False


def t_reality_claim_flagged_as_leakage():
    """invariant #4: claim با world_mode=reality در facts رفته → leakage flag."""
    comp = CP.compose(claims=[{"claim_id": "h2", "world_mode": "reality",
                               "epistemic_status": "supported"}])
    assert comp.has_leakage is True
    assert len(comp.hypotheses) == 0   # reality claim مسدود شد
    assert "leakage" in CP.render_text(comp).lower() or "WARNING" in CP.render_text(comp)


def t_disclosure_picks_strongest_non_reality():
    comp = CP.compose(claims=[
        {"world_mode": "hypothesis"}, {"world_mode": "simulation"}])
    assert comp.disclosure == "simulation"
    comp2 = CP.compose(claims=[{"world_mode": "counterfactual"}])
    assert comp2.disclosure == "counterfactual"


def t_render_text_handles_empty():
    txt = CP.render_text(CP.compose())
    assert "هیچ" in txt or "—" in txt or txt.strip() != ""


# ---------------------------------------------------------------------------
# cortex claim-builder
# ---------------------------------------------------------------------------
def t_draft_from_metric_snapshot():
    draft = CB.draft_from_telemetry({"coherence": 0.96, "beat": 33613})
    assert draft is not None
    assert draft["metric"] == "coherence"
    assert draft["world_mode"] == "hypothesis"
    assert draft["may_execute"] is False
    assert CB.is_runnable_draft(draft) is True


def t_draft_none_when_no_metric():
    assert CB.draft_from_telemetry({"status": "ok"}) is None
    assert CB.draft_from_telemetry({}) is None
    assert CB.draft_from_telemetry("not-a-dict") is None


def t_draft_never_reality():
    """invariant #4: draft همیشه hypothesis است، هرگز reality."""
    draft = CB.draft_from_telemetry({"pain": 0.4})
    assert draft is not None
    assert draft["world_mode"] != "reality"


def test_is_runnable_rejects_missing():
    assert CB.is_runnable_draft({}) is False
    assert CB.is_runnable_draft({"operational_definition": "x"}) is False


TESTS = [
    t_facts_and_hypotheses_separated,
    t_reality_claim_flagged_as_leakage,
    t_disclosure_picks_strongest_non_reality,
    t_render_text_handles_empty,
    t_draft_from_metric_snapshot,
    t_draft_none_when_no_metric,
    t_draft_never_reality,
    test_is_runnable_rejects_missing,
]

if __name__ == "__main__":
    failed = 0
    for _t in TESTS:
        try:
            _t()
            print(f"  PASS  {_t.__name__}")
        except Exception as exc:
            print(f"  FAIL  {_t.__name__}: {exc}")
            failed += 1
    print(f"\n{len(TESTS) - failed}/{len(TESTS)} passed")
    sys.exit(failed)
