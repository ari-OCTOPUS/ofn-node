import pytest

from mining_preexec_mvp.governance import assert_action_allowed, GovernanceError, verdict_queue_gate
from mining_preexec_mvp.models import VerdictItem, DecisionStatus


def test_hard_gated_action_rejected():
    with pytest.raises(GovernanceError):
        assert_action_allowed("ssh_to_node")


def test_report_action_not_rejected():
    assert_action_allowed("read_status")


def test_verdict_queue_gate_fails_when_open():
    result = verdict_queue_gate([VerdictItem("MIN-V1", "x", DecisionStatus.OPEN)])
    assert not result.passed
    assert result.risk.value == "red"


def test_verdict_queue_gate_passes_when_closed():
    result = verdict_queue_gate([VerdictItem("MIN-V1", "x", DecisionStatus.APPROVED)])
    assert result.passed
