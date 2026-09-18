"""Paired test for the exported A1 gate flip (RUNTIME-EXPORT PR).

Red against canonical (hold_external=True), green with the exported runtime
file. Pins the whole fail-closed posture, not just the one flipped field: the
release was ordered for the legacy package's EXTERNAL hold only.
"""
from ofn.ziman_cycle import gates


def test_hold_external_released():
    assert gates.GatePolicy().hold_external is False


def test_fail_closed_posture_unchanged():
    p = gates.GatePolicy()
    assert p.publish is False
    assert p.external_send == "none"
    assert p.use_llm is False
    assert p.safe_to_claim is False
