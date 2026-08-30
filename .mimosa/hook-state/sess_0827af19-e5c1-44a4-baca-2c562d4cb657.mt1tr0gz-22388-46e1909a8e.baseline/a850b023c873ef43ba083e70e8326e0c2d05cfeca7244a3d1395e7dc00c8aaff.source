#!/usr/bin/env python3
"""Ziman biology integration: heart + nerves + evolutionary doctor, offline."""
from __future__ import annotations

import sys
from pathlib import Path

_OPS = Path(__file__).resolve().parents[1]
for p in (_OPS, _OPS / "budget", _OPS / "legs", _OPS / "neural", _OPS / "doctor"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from ziman_biology import (  # noqa: E402
    biology_beat, collect_neural_snapshot, doctor_trace,
    health_assessment, heart_readmodel)
from ziman_leg import ZimanLeg  # noqa: E402


def _status(**over):
    base = {
        "leg_id": "ziman-gallery", "organ": "ZIMAN", "money_link": "active",
        "capacity_ceiling_per_week": 30, "capacity_evidence_class": "CONFLICT",
        "inventory_hint": None, "drafts_count": 0, "autonomy": "propose-only",
        "execution_state": "ZERO outward execution — drafts only",
    }
    base.update(over)
    return base


def test_heart_readmodel_has_no_write_authority():
    h = heart_readmodel()
    assert h["authority"] == "rhythm_only"
    assert h["ziman_can_write_heart"] is False


def test_unverified_capacity_becomes_anomaly():
    a = health_assessment(_status(), heart={"sigma_now": 0.5})
    assert any(x["code"] == "CAPACITY_UNVERIFIED" for x in a["anomalies"])


def test_sigma_over_one_is_critical():
    a = health_assessment(_status(capacity_evidence_class="VERIFIED_FACT"),
                          heart={"sigma_now": 1.01})
    assert a["critical"] is True
    assert a["protective_mode"] is True
    assert any(x["code"] == "SIGMA_CANCER_RISK" for x in a["anomalies"])


def test_autonomy_drift_is_critical():
    a = health_assessment(_status(autonomy="execute"), heart={"sigma_now": 0.1})
    assert a["critical"] is True
    assert any(x["code"] == "AUTONOMY_DRIFT" for x in a["anomalies"])


def test_doctor_trace_is_content_free():
    a = health_assessment(_status(), heart={"sigma_now": 0.2})
    t = doctor_trace(a)
    assert t["scope"] == "ZIMAN"
    assert "customer" not in str(t).lower()
    assert "address" not in str(t).lower()


def test_neural_snapshot_is_advisory_only():
    status = _status()
    heart = {"period_s": 60, "sigma_now": 0.2}
    assessment = health_assessment(status, heart)
    n = collect_neural_snapshot(1, status, heart, assessment)
    assert n["advisory_only"] is True
    assert n["beat"] == 1
    assert n["sensory"]["organ"] == "ZIMAN"


def test_biology_beat_no_doctor_is_safe():
    leg = ZimanLeg(organ_table={"ZIMAN": {}}, capacity_ceiling=30)
    out = biology_beat(leg, beat=1, doctor=None, doctor_every_n=0)
    assert out["schema"] == "ziman-biology.v1"
    assert out["nerves"]["connected"] is True
    assert out["doctor"]["connected"] is False
    assert out["outward_execution"] is False
    assert out["ziman_can_write_heart"] is False


def test_biology_beat_doctor_receives_trace_only():
    class FakeDoctor:
        def __init__(self):
            self.trace = None
        def run_cycle(self, beat=0, trace=None):
            self.trace = trace
            return {"rfc_id": "RFC-test", "status": "submitted-no-channel"}

    doc = FakeDoctor()
    leg = ZimanLeg(organ_table={"ZIMAN": {}}, capacity_ceiling=30)
    out = biology_beat(leg, beat=1, doctor=doc, doctor_every_n=0)
    assert out["doctor"]["connected"] is True
    assert out["doctor"]["auto_merge"] is False
    assert out["doctor"]["human_append_required"] is True
    assert doc.trace["scope"] == "ZIMAN"


def test_leg_accepts_only_safe_biology_schema():
    leg = ZimanLeg(organ_table={"ZIMAN": {}}, capacity_ceiling=30)
    assert leg.accept_biology_status({"schema": "wrong"}) is False
    assert leg.accept_biology_status({
        "schema": "ziman-biology.v1", "outward_execution": True,
        "ziman_can_write_heart": False}) is False
    safe = {"schema": "ziman-biology.v1", "outward_execution": False,
            "ziman_can_write_heart": False}
    assert leg.accept_biology_status(safe) is True
    assert leg.status_snapshot()["biology"] == safe


def test_no_effector_methods_on_biology_or_leg():
    leg = ZimanLeg(organ_table={"ZIMAN": {}}, capacity_ceiling=30)
    for name in ("send", "publish", "pay", "deploy", "change_heart"):
        assert not hasattr(leg, name)
