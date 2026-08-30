"""test_world_discovery_competitors.py — تست‌های competitor intel + scoring."""
import sys
from pathlib import Path

import pytest

_OPS = Path(__file__).resolve().parent.parent
if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))

from world_discovery import competitor_intel as CI
from world_discovery import opportunity as OPP
from world_discovery import scorer
from world_discovery.contracts import Opportunity


def test_competitor_row_built():
    row = CI.build_competitor_row(
        "Anthropic",
        strengths=["agent architecture", "safety"],
        weaknesses=["expensive", "enterprise-rigid"],
        evidence=[{"url": "https://anthropic.com/x", "tier": "A"},
                  {"url": "https://techcrunch.com/y", "tier": "B"}],
        learn_for_octopus=["memory persistence"],
        do_not_imitate=["pricing"],
    )
    assert row.company == "Anthropic"
    assert row.real_use_evidence is True
    assert "agent architecture" in row.strengths


def test_asymmetry_hypothesis_generated():
    row = CI.build_competitor_row(
        "xAI",
        strengths=["fast product velocity"],
        weaknesses=["no personalization"],
        evidence=[],
    )
    hyps = CI.propose_asymmetry([row])
    assert len(hyps) >= 1
    assert all(h.evidence_needed for h in hyps)  # every hypothesis needs evidence


def test_asymmetry_confidence_zero_without_evidence():
    row = CI.build_competitor_row(
        "Sakana", strengths=["s"], weaknesses=["w"], evidence=[]
    )
    hyps = CI.propose_asymmetry([row])
    assert all(h.confidence == 0.0 for h in hyps)  # no evidence → 0 confidence


def test_opportunity_classification():
    assert OPP.classify_opportunity_type("pricing is too high", None) == "ai-architecture-insight"
    asym = CI.AsymmetryHypothesis(
        asymmetry_id="a", competitor_advantage="x",
        competitor_structural_weakness="expensive pricing",
        octopus_local_advantage="low cost",
        opportunity="opp", evidence_needed="e",
    )
    assert OPP.classify_opportunity_type("pricing anomaly", asym) == "pricing-anomaly"


def test_opportunity_build():
    asym = CI.AsymmetryHypothesis(
        asymmetry_id="a1", competitor_advantage="strong model",
        competitor_structural_weakness="rigid enterprise focus",
        octopus_local_advantage="architectural speed",
        opportunity="opp", evidence_needed="ev",
    )
    seed = OPP.OpportunitySeed(
        claim="test claim", opp_type="", discovery_id="d",
        asymmetry=asym, time_to_test_days=7,
    )
    opp = OPP.build_opportunity(seed)
    assert opp.type == "competitor-weakness"  # default for asymmetry
    assert "نامتقارن" in opp.asymmetry


def test_scorer_evidence_strength():
    # 0 independent → 0
    assert scorer.score_evidence_strength([]) == 0
    # 1 → 2
    assert scorer.score_evidence_strength([{"url": "https://anthropic.com/a", "tier": "A"}]) == 2
    # 2 independent → 3
    two = [{"url": "https://anthropic.com/a", "tier": "A"},
           {"url": "https://techcrunch.com/b", "tier": "B"}]
    assert scorer.score_evidence_strength(two) == 3


def test_scorer_novelty():
    assert scorer.score_novelty("novel") == 5
    assert scorer.score_novelty("known") == 0
    assert scorer.score_novelty("partially-novel") == 3


def test_scorer_reversibility():
    assert scorer.score_reversibility("high") == 5
    assert scorer.score_reversibility("low") == 1


def test_score_opportunity_full():
    opp = Opportunity(type="ai-architecture-insight", claim="test claim about agents",
                      reversibility="high")
    sources = [{"url": "https://anthropic.com/a", "tier": "A", "source_date": "2026-07-01"},
               {"url": "https://techcrunch.com/b", "tier": "B", "source_date": "2026-07-02"}]
    opp, breakdown = scorer.score_opportunity(
        opp,
        sources=sources,
        novelty_decision="novel",
        direction_keywords=["agent", "memory"],
        horizon_days=7,
        action_level="L3",
        freshness_dict={"stale": False},
        injection_flags=0,
    )
    assert opp.evidence_strength == 3
    assert opp.novelty == 5
    assert 0.0 <= opp.confidence <= 1.0
    assert breakdown.formula_version == "world-discovery.scorer.v1"
    assert "weights" in breakdown.components


def test_scorer_penalty_for_stale_and_injection():
    opp = Opportunity(type="ai-architecture-insight", claim="x", reversibility="high")
    sources = [{"url": "https://anthropic.com/a", "tier": "A"}]
    opp, _ = scorer.score_opportunity(
        opp, sources=sources, novelty_decision="unknown",
        direction_keywords=[], horizon_days=7, action_level="L3",
        freshness_dict={"stale": True}, injection_flags=2,
    )
    assert opp.uncertainty_penalty >= 2


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
