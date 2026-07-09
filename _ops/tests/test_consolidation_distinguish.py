#!/usr/bin/env python3
"""test_consolidation_distinguish.py — تستِ تمایزِ return value در canonical_consolidation.

Phase 1: None = precondition failure / exception، ConsolidatedInsight = ran.
"""
import sys
from pathlib import Path
from unittest.mock import MagicMock

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
import harness

from neural.consolidation import ConsolidatedInsight


def _make_fake_consolidation_cycle(**kwargs):
    """consolidation.run() mock با خروجی ConsolidatedInsight."""
    cycle = MagicMock()
    default = {"insights": ["learning detected"],
               "verified_sources": ["acquisition"],
               "discarded_sources": []}
    default.update(kwargs)
    cycle.run.return_value = ConsolidatedInsight(
        cycle=1,
        insights=default["insights"],
        verified_sources=default["verified_sources"],
        discarded_sources=default["discarded_sources"])
    return cycle


def _import_wiring():
    """lazy import wiring (که خودش lazy import consolidation دارد)."""
    import wiring
    return wiring


def t_none_when_neural_stack_is_none():
    """neural_stack=None → None (precondition failure)."""
    wiring = _import_wiring()
    result = wiring.canonical_consolidation(None)
    assert result is None, "neural_stack=None باید None برگرداند"


def t_bare_object_when_no_sources():
    """neural_stack موجود ولی منابع خالی → ConsolidatedInsight با insights=[]"""
    from wiring import canonical_consolidation
    fake_cycle = _make_fake_consolidation_cycle()
    stack = {"consolidation": fake_cycle}
    result = canonical_consolidation(stack,
                                      acquisition_data={},
                                      doctor_archive=[],
                                      school_bridge=None)
    assert result is not None, "no sources باید bare object برگرداند نه None"
    assert isinstance(result, ConsolidatedInsight), f"expected ConsolidatedInsight, got {type(result)}"
    assert result.insights == [], f"expected empty insights, got {result.insights}"
    # run() نباید صدا زده شود چون sources خالی بود
    fake_cycle.run.assert_not_called()


def t_real_consolidation_when_sources_exist():
    """آماده‌سازی منابع → consolidation.run() صدا زده می‌شود."""
    from wiring import canonical_consolidation
    fake_cycle = _make_fake_consolidation_cycle()
    stack = {"consolidation": fake_cycle}
    result = canonical_consolidation(stack,
                                      acquisition_data={"revenue": 42.0},
                                      doctor_archive=None,
                                      school_bridge=None)
    assert result is not None
    assert isinstance(result, ConsolidatedInsight)
    assert len(result.verified_sources) == 1
    fake_cycle.run.assert_called_once()


def t_none_on_exception():
    """exception در consolidation.run → None."""
    from wiring import canonical_consolidation
    bad_cycle = MagicMock()
    bad_cycle.run.side_effect = RuntimeError("consolidation crashed")
    stack = {"consolidation": bad_cycle}
    result = canonical_consolidation(stack,
                                      acquisition_data={"rev": 10.0})
    assert result is None, "exception باید None برگرداند"


def t_unverified_sources_filtered():
    """acquisition_data با مقادیر نامعتبر → فیلتر شوند، bare object برگردد."""
    from wiring import canonical_consolidation
    fake_cycle = _make_fake_consolidation_cycle()
    stack = {"consolidation": fake_cycle}
    # همه مقادیر نامعتبر: string، negative، zero
    result = canonical_consolidation(stack,
                                      acquisition_data={"bad": "not-numeric",
                                                        "zero": 0, "neg": -5.0})
    assert result is not None
    assert result.insights == [], "sources نامعتبر باید فیلتر شوند → empty"
    fake_cycle.run.assert_not_called()


if __name__ == "__main__":
    failed = harness.run([
        ("None وقتی neural_stack=None", t_none_when_neural_stack_is_none),
        ("bare object وقتی منابع خالی", t_bare_object_when_no_sources),
        ("real consolidation با منابع معتبر", t_real_consolidation_when_sources_exist),
        ("None روی exception", t_none_on_exception),
        ("فیلتر منابع نامعتبر", t_unverified_sources_filtered),
    ])
    sys.exit(1 if failed else 0)
