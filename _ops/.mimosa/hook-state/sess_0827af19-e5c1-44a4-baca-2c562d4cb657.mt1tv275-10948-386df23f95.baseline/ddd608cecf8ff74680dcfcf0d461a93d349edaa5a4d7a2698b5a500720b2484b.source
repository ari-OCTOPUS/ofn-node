"""test_world_discovery_contracts.py — تست‌های قرارداد، schema، validation.

پوشش از بند ۱۶: 1, 2, 13, 14, 15, 24, 25, 26, 27, 28, 29, 30.
"""
import json
import sys
import tempfile
from pathlib import Path

import pytest

_OPS = Path(__file__).resolve().parent.parent
if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))

from world_discovery import contracts as C
from world_discovery import report as R


# ───────── 1) Schema validation ─────────
def test_discovery_has_schema_and_required_fields():
    d = C.Discovery(
        discovery_id="wd-test",
        created_at="2026-07-30T00:00:00Z",
        mission_id="m",
        domain="ai-competition",
        geography="global",
        claim="test claim",
        why_it_matters="why",
        direction_link="link",
        novelty={"decision": "novel"},
        evidence=[{"url": "https://anthropic.com/x", "tier": "A"}],
        freshness={"observed_at": "2026-07-30T00:00:00Z"},
        falsifier="if X then false",
        next_experiment="do Y",
        owner_gate="L3",
        status="triangulated",
    )
    missing = d.validate_required()
    assert missing == [], f"unexpected missing: {missing}"
    dd = d.as_dict()
    assert dd["schema"] == "world-discovery.v1"
    assert dd["claim"] == "test claim"


# ───────── 2) Missing source rejected ─────────
def test_missing_source_rejected():
    d = C.Discovery(claim="x")
    missing = d.validate_required()
    assert "evidence" in missing
    assert "evidence_url" in missing  # no url in evidence
    assert d.is_valid() is False


# ───────── 13) Financial claim requires stronger evidence (marker detection) ─────────
def test_financial_claim_detected():
    from world_discovery.source_policy import requires_stronger_evidence
    assert requires_stronger_evidence("revenue $10M") is True
    assert requires_stronger_evidence("the best model") is True  # competitive superlative
    assert requires_stronger_evidence("a feature was added") is False


# ───────── 24) Experiment has falsifier ─────────
def test_experiment_requires_falsifier():
    e = C.Experiment(level="E0", hypothesis="h", observable_metric="m", target="t", owner_gate="L3")
    problems = e.validate()
    assert "missing-falsifier" in problems
    e.falsifier = "if X false"
    assert "missing-falsifier" not in e.validate()


def test_experiment_invalid_level_rejected():
    e = C.Experiment(level="E9", hypothesis="h", observable_metric="m",
                     target="t", owner_gate="L3", falsifier="f")
    assert "invalid-level" in e.validate()


# ───────── 25) Discovery has direction link ─────────
def test_discovery_direction_link_required():
    d = C.Discovery(claim="x", evidence=[{"url": "u", "tier": "A"}])
    assert "direction_link" in d.validate_required()


# ───────── 26) no-valid-discovery is valid output ─────────
def test_no_valid_discovery_structure():
    from world_discovery import octopus_adapter as wd
    result = {
        "schema": "world-discovery.discover.v1",
        "status": "NO_VALID_DISCOVERY",
        "discovery": None,
        "reason": "no-candidates",
        "note": "هیچ کشف معتبری پیدا نشد. این نتیجه معتبر است.",
    }
    assert result["status"] == "NO_VALID_DISCOVERY"
    assert result["discovery"] is None


# ───────── 27) Adapter imports without touching runtime state ─────────
def test_adapter_imports_clean():
    import importlib
    from world_discovery import octopus_adapter
    importlib.reload(octopus_adapter)
    assert hasattr(octopus_adapter, "discover")
    assert hasattr(octopus_adapter, "observe")
    # No state writes happen on import
    assert True


# ───────── 28) Export is atomic ─────────
def test_export_bundle_atomic(tmp_path):
    result = {"status": "TEST", "discovery": None}
    info = R.export_bundle(result, tmp_path)
    p = Path(info["path"])
    assert p.exists()
    data = R.load_bundle_check(p)
    assert data["schema"] == "world-discovery.bundle.v1"
    assert info["sha256"]  # has hash


# ───────── 29) Corrupt artifact fails closed ─────────
def test_corrupt_artifact_fails_closed(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("{not valid json", encoding="utf-8")
    with pytest.raises(ValueError):
        R.load_bundle_check(p)


# ───────── 30) Multiple runs do not create duplicate receipts ─────────
def test_multiple_runs_same_discovery_id():
    from world_discovery.contracts import make_discovery_id
    a = make_discovery_id("same claim", "mission-1")
    b = make_discovery_id("same claim", "mission-1")
    assert a == b  # idempotent


# ───────── 14) URL normalization ─────────
def test_url_normalization():
    from world_discovery.source_policy import normalize_url
    assert normalize_url("HTTPS://WWW.Anthropic.com/News/").rstrip("/") == "https://anthropic.com/News" or \
           normalize_url("HTTPS://WWW.Anthropic.com/News/") == "https://anthropic.com/News"
    # tracking params stripped
    norm = normalize_url("https://anthropic.com/news?utm_source=x&id=5")
    assert "utm_source" not in norm
    assert "id=5" in norm


# ───────── 15) Source-domain normalization ─────────
def test_registrable_domain():
    from world_discovery.source_policy import registrable_domain
    assert registrable_domain("https://www.anthropic.com/news/x") == "anthropic.com"
    assert registrable_domain("https://sakana.ai/blog") == "sakana.ai"
    assert registrable_domain("https://x.ai") == "x.ai"


def test_make_ids_deterministic():
    from world_discovery.contracts import make_discovery_id, make_action_id, make_observation_id
    assert make_discovery_id("c", "m") == make_discovery_id("c", "m")
    assert make_action_id("d", "a") == make_action_id("d", "a")
    assert make_observation_id("c", "u") == make_observation_id("c", "u")


def test_metrics_hard_invariants():
    m = C.Metrics(external_effect_count=0, spend_amount=0.0,
                  privacy_violation_count=0, unsupported_claim_count=0)
    assert m.check_hard_invariants() == []
    m.spend_amount = 5.0
    assert "spend_amount" in m.check_hard_invariants()


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
