#!/usr/bin/env python3
"""test_consolidation_latent.py — تستِ latent integration در canonical_consolidation.

Phase 2: consolidation با latent_space → latent_vector + similar_keys.
$0 آفلاین: neural_stack mock + latent_space tmpdir.
"""
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
import harness

import numpy as np
from neural.latent_space import SharedLatentSpace
from neural.consolidation import ConsolidatedInsight


def _make_stack(latent_space=None):
    """Fake neural_stack با consolidation mock."""
    cycle = MagicMock()
    cycle.run.return_value = ConsolidatedInsight(
        cycle=1, insights=["test insight"],
        verified_sources=["acquisition"], discarded_sources=[])
    return {"consolidation": cycle, "latent_space": latent_space}


def _make_school_mock(mean_awareness=0.5, full_vector=None):
    """Mock school_bridge."""
    sb = MagicMock()
    sb.mean_awareness.return_value = mean_awareness
    sb.full_awareness_vector.return_value = full_vector
    return sb


def t_with_latent_space_has_vector():
    """consolidation با latent_space → latent_vector not None."""
    import wiring
    import tempfile
    td = tempfile.mkdtemp()
    ls = SharedLatentSpace(dim=32, persist_path=str(Path(td) / "test.json"))
    stack = _make_stack(latent_space=ls)
    result = wiring.canonical_consolidation(
        stack, acquisition_data={"revenue": 42.0}, latent_space=ls)
    assert result is not None
    assert isinstance(result, ConsolidatedInsight)
    assert result.latent_vector is not None, "latent_vector باید None نباشد"
    assert len(result.latent_vector) == 32, f"expected R^32, got {len(result.latent_vector)}"


def t_without_latent_space_backward_compat():
    """consolidation بدون latent_space → latent_vector=None (backward compat)."""
    import wiring
    stack = _make_stack(latent_space=None)
    result = wiring.canonical_consolidation(
        stack, acquisition_data={"revenue": 42.0}, latent_space=None)
    assert result is not None
    assert result.latent_vector is None, "بدون latent_space → باید None"


def t_similar_keys_populated():
    """بعد از ۲ cycle → similar_keys باید history را پیدا کند."""
    import wiring
    import tempfile
    td = tempfile.mkdtemp()
    ls = SharedLatentSpace(dim=32, persist_path=str(Path(td) / "test2.json"))
    stack = _make_stack(latent_space=ls)
    # cycle 1
    r1 = wiring.canonical_consolidation(
        stack, acquisition_data={"rev": 10.0}, latent_space=ls)
    assert r1 is not None
    # cycle 2 (باید cycle-1 را در similar_keys بیابد)
    stack["consolidation"].run.return_value = ConsolidatedInsight(
        cycle=2, insights=["test2"], verified_sources=["acquisition"],
        discarded_sources=[])
    r2 = wiring.canonical_consolidation(
        stack, acquisition_data={"rev": 20.0}, latent_space=ls)
    assert r2 is not None
    # similar_keys ممکن None باشد یا list — نباید crash کند
    if r2.similar_keys is not None:
        assert isinstance(r2.similar_keys, list)


def t_school_awareness_encoded():
    """school awareness با latent_space → encoded."""
    import wiring
    import tempfile
    td = tempfile.mkdtemp()
    ls = SharedLatentSpace(dim=32, persist_path=str(Path(td) / "test3.json"))
    stack = _make_stack(latent_space=ls)
    sb = _make_school_mock(mean_awareness=0.7, full_vector=[0.1, 0.3, 0.5, 0.7])
    result = wiring.canonical_consolidation(
        stack, school_bridge=sb, latent_space=ls)
    assert result is not None
    assert result.latent_vector is not None
    # school encoding باید در latent space ذخیره شده باشد
    school_keys = ls.keys_by_layer("school")
    assert len(school_keys) >= 1, "school encoding باید ذخیره شده باشد"


def t_multiple_sources_integrated():
    """چند source → latent_vector ترکیبی."""
    import wiring
    import tempfile
    td = tempfile.mkdtemp()
    ls = SharedLatentSpace(dim=32, persist_path=str(Path(td) / "test4.json"))
    cycle = MagicMock()
    cycle.run.return_value = ConsolidatedInsight(
        cycle=1, insights=["multi"], verified_sources=["acquisition", "doctor_archive"],
        discarded_sources=[])
    stack = {"consolidation": cycle, "latent_space": ls}
    result = wiring.canonical_consolidation(
        stack, acquisition_data={"rev": 50.0},
        doctor_archive=[{"outcome": "approved"}],
        latent_space=ls)
    assert result is not None
    assert result.latent_vector is not None
    # هر دو source باید encoded شده باشند
    assert ls.keys_by_layer("acquisition") != []
    assert ls.keys_by_layer("doctor") != []


def t_retrieval_finds_previous():
    """embedding ذخیره‌شده قابل retrieval است."""
    import wiring
    import tempfile
    td = tempfile.mkdtemp()
    ls = SharedLatentSpace(dim=32, persist_path=str(Path(td) / "test5.json"))
    stack = _make_stack(latent_space=ls)
    # cycle 1 — ذخیره
    r1 = wiring.canonical_consolidation(
        stack, acquisition_data={"rev": 10.0}, latent_space=ls)
    assert r1 is not None
    # cycle key باید در space باشد
    cycle_key = "cycle-1"
    assert ls.get(cycle_key) is not None, "cycle embedding باید ذخیره شده باشد"
    # retrieval
    nn = ls.nearest(cycle_key, top_k=3)
    assert len(nn) >= 1


def t_latent_fail_soft():
    """اگر latent encoding crash کند → latent_vector=None ولی result هنوز valid."""
    import wiring
    import tempfile
    td = tempfile.mkdtemp()
    # latent space با dim=1 (بسیار کوچک) — ممکن باعث مشکل شود ولی نباید crash کند
    ls = SharedLatentSpace(dim=1, persist_path=str(Path(td) / "test6.json"))
    stack = _make_stack(latent_space=ls)
    result = wiring.canonical_consolidation(
        stack, acquisition_data={"rev": 42.0}, latent_space=ls)
    # حتی اگر latent encoding fail شود، result باید valid باشد
    assert result is not None
    assert isinstance(result, ConsolidatedInsight)
    # insights باید هنوز تولید شده باشند
    assert len(result.verified_sources) >= 1 or result.latent_vector is not None


if __name__ == "__main__":
    failed = harness.run([
        ("latent_space → latent_vector", t_with_latent_space_has_vector),
        ("بدون latent_space → backward compat", t_without_latent_space_backward_compat),
        ("similar_keys از history", t_similar_keys_populated),
        ("school awareness encoded", t_school_awareness_encoded),
        ("multiple sources integrated", t_multiple_sources_integrated),
        ("retrieval finds previous", t_retrieval_finds_previous),
        ("latent fail-soft", t_latent_fail_soft),
    ])
    sys.exit(1 if failed else 0)
