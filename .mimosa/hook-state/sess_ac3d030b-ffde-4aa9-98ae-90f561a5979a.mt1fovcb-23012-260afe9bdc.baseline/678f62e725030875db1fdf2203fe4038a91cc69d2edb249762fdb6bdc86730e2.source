#!/usr/bin/env python3
"""Standalone test: python tools/test_sensitivity_grade.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sensitivity_grade import grade, EXAMPLES, HARD_HIGH   # noqa: E402


def test_examples_match():
    for desc, act, expected in EXAMPLES:
        g = grade(act)
        assert g["tier"] == expected, f"{desc!r}: got {g['tier']}, want {expected}"


def test_hard_high_always_escalates():
    # every hard trigger, alone, must yield HIGH + auto False, even if the
    # action otherwise looks trivial.
    for trig in HARD_HIGH:
        g = grade({trig: True})
        assert g["tier"] == "HIGH" and g["auto"] is False, f"{trig} not escalated"


def test_hard_high_overrides_low_score():
    # a body write with zero soft score is still HIGH (grader can't downgrade)
    g = grade({"body_write": True})
    assert g["tier"] == "HIGH" and g["auto"] is False


def test_empty_is_low_auto():
    g = grade({})
    assert g["tier"] == "LOW" and g["auto"] is True and g["rollback_required"] is False


def test_medium_needs_rollback_note():
    g = grade({"shared_file": True})
    assert g["tier"] == "MEDIUM" and g["auto"] is True and g["rollback_required"] is True


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    bad = 0
    for fn in fns:
        try:
            fn(); print(f"PASS  {fn.__name__}")
        except AssertionError as e:
            bad += 1; print(f"FAIL  {fn.__name__}: {e}")
    print(f"\n{len(fns) - bad}/{len(fns)} tests passed")
    sys.exit(1 if bad else 0)
