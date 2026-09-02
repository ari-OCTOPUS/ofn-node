# Lane LB tests — self-backlog (scenario 13 + field contract).
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ofn.doctor.backlog import BACKLOG_FIELDS, SelfBacklog  # noqa: E402


def test_13_backlog_no_duplicates_on_upsert(tmp_path):
    bl = SelfBacklog(tmp_path / "self-backlog.json")
    gaps = [{"area": "flow", "item": "novelty_gate::independent_novelty_evaluator",
             "status": "NOT_IMPLEMENTED"}]
    first = bl.upsert_from_gaps(gaps)
    assert first["added"] == 1
    second = bl.upsert_from_gaps(gaps)
    assert second["added"] == 0
    assert len(bl.items()) == 1                     # no duplicate across reruns


def test_items_carry_exactly_the_nine_owner_fields(tmp_path):
    bl = SelfBacklog(tmp_path / "self-backlog.json")
    bl.upsert("lab", "hard_sandbox.cpu_limit", evidence="contract status=UNKNOWN_NOT_VERIFIED",
              severity="HIGH", proposed_action="design negative tests (lane C)")
    item = bl.items()[0]
    assert set(item.keys()) == set(BACKLOG_FIELDS)
    assert item["owner_ruling_required"] is True    # policy surface → owner rules
    assert item["test_required"] is True
    assert item["status"] == "open"


def test_engineering_area_can_be_owner_flagged_explicitly(tmp_path):
    bl = SelfBacklog(tmp_path / "self-backlog.json")
    bl.upsert("ofn", "dead-ref repair", evidence="findings.json", severity="MEDIUM",
              proposed_action="repair refs via PR", owner_ruling_required=False)
    assert bl.items()[0]["owner_ruling_required"] is False


def test_state_file_round_trips(tmp_path):
    state = tmp_path / "self-backlog.json"
    SelfBacklog(state).upsert("gate", "gate_4:doctor_prescriptions",
                              evidence="status=NOT_STARTED", severity="MEDIUM",
                              proposed_action="three falsifiable prescriptions")
    data = json.loads(state.read_text(encoding="utf-8"))
    assert data["count"] == len(data["items"]) == 1
    again = SelfBacklog(state)
    assert len(again.items()) == 1                  # reload keeps items, ids stable


def test_bad_severity_is_rejected(tmp_path):
    bl = SelfBacklog(tmp_path / "b.json")
    with pytest.raises(ValueError):
        bl.upsert("x", "y", evidence="e", severity="CATASTROPHIC",
                  proposed_action="p")
