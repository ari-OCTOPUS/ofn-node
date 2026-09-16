#!/usr/bin/env python3
"""G4: shadow control-law is observable, never live-authoritative.

All state is pinned by harness before importing pulse_arbiter. No test writes the
live vault. The gate removes authority only and holds the last valid live period
so removing a slow invalid vote cannot accelerate the organism.
"""
from __future__ import annotations

import json
import math
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("pulse-arbiter-authority")
_OPS = harness.SELF_OPS
for _p in (str(_OPS), str(_OPS / "budget"), str(_OPS / "heart")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib  # noqa: E402
from heart import pulse_arbiter as pa  # noqa: E402

_ROOT = str(Path(ENV["root"]).resolve())
_FLAG_BIO = "OCTOPUS_WIRE_BIO"


def _shadow(period=244.4, *, open_wire=False, gate0=False,
            provenance="UNVERIFIABLE", ts=None, braking=False):
    return {
        "ts": ts or opslib.now_iso(),
        "beat": 48965,
        "period_s": period,
        "mode": "shadow",
        "gate0_live_producer": gate0,
        "production_wire": {"open": open_wire, "reasons": []},
        "sog_provenance": provenance,
        "telemetry": {"gates": {
            "precision": 0.8,
            "fail_closed_reason": "test-brake" if braking else None,
            "drift_flag": False,
        }},
    }


def _views(control=244.4, cardiac=42.4264, rhythm=80.3):
    return {
        "cardiac_snapshot": {
            "enabled": True,
            "bio_rhythm": {"period_s": cardiac, "pace": "mice", "mass": 1.0},
            "budget": {"depleted": False},
            "baroreflex_factor": None,
        },
        "heart_shadow": _shadow(control),
        "rhythm_state": {
            "mode_color": "GREEN", "T_beat": rhythm,
            "hrv": 0.42, "mode_focus": "STEADY",
        },
    }


def _previous(period=96.32):
    return {
        "schema": pa.SCHEMA,
        "effective_period_s": period,
        "wire_open": True,
        "written": True,
    }


def _candidate(period, driver="consensus"):
    return {
        "schema": pa.SCHEMA,
        "effective_period_s": period,
        "candidate_period_s": period,
        "driver": driver,
        "candidate_driver": driver,
        "reasons": [],
        "wire_requested_open": True,
        "wire_open": False,
        "wire_reasons": [],
        "wire_reasons_n": 0,
    }


def _reset_wire():
    os.environ.pop(pa.FLAG_ENV, None)
    os.environ.pop(_FLAG_BIO, None)
    if pa.ACT_ARBITER.exists():
        pa.ACT_ARBITER.unlink()


def _arm_wire():
    os.environ[pa.FLAG_ENV] = "1"
    os.environ[_FLAG_BIO] = "1"
    pa.ACT_ARBITER.parent.mkdir(parents=True, exist_ok=True)
    pa.ACT_ARBITER.write_text("owner-created test fixture\n", encoding="utf-8")


def t_paths_are_sandboxed():
    for path in (pa.LATEST, pa.SINK, pa.ACT_ARBITER, opslib.STATE_DIR):
        assert str(Path(path).resolve()).startswith(_ROOT), path


def t_closed_shadow_is_observed_but_ineligible():
    vote = pa._control_vote(_shadow())
    assert vote["present"] is False
    assert vote["eligible_for_live"] is False
    assert vote["authority"] == "SHADOW_ONLY"
    assert math.isclose(vote["period_s"], 244.4)
    assert math.isclose(vote["observed_period_s"], 244.4)
    assert vote["braking"] is False
    assert vote["authority_reasons"]


def t_self_reported_open_shadow_still_grants_no_authority():
    vote = pa._control_vote(_shadow(open_wire=True, gate0=True,
                                   provenance="VERIFIED"))
    assert vote["present"] is False
    assert vote["eligible_for_live"] is False
    assert vote["authority"] == "SHADOW_ONLY"
    assert any("Gate 1" in reason for reason in vote["authority_reasons"])


def t_missing_authority_fields_fail_closed():
    vote = pa._control_vote({
        "ts": opslib.now_iso(), "period_s": 60.0,
        "telemetry": {"gates": {}},
    })
    assert vote["present"] is False
    assert vote["authority"] == "SHADOW_ONLY"
    assert len(vote["authority_reasons"]) >= 4


def t_pure_compute_fallback_is_advisory_only():
    vote = pa._control_vote({})
    assert vote["present"] is False
    assert vote["eligible_for_live"] is False
    assert vote["authority"] == "ADVISORY_COMPUTE"
    assert vote["period_s"] is None or math.isfinite(vote["period_s"])


def t_malformed_control_observation_is_ineligible():
    for value in ("not-a-record", [], 7):
        vote = pa._control_vote(value)
        assert vote["present"] is False
        assert vote["eligible_for_live"] is False
        assert vote["authority"] == "MALFORMED_INPUT"


def t_invalid_periods_never_become_live_votes():
    for value in (float("nan"), float("inf"), 0, -1, "bad"):
        vote = pa._control_vote(_shadow(value))
        assert vote["present"] is False
        assert vote["eligible_for_live"] is False
        assert vote["period_s"] is None
        assert vote["observed_period_s"] is None


def t_stale_shadow_remains_ineligible():
    vote = pa._control_vote(_shadow(ts="2026-08-03T00:00:00"))
    assert vote["mode"] in ("HELD", "UNKNOWN")
    assert vote["present"] is False
    assert vote["eligible_for_live"] is False


def t_shadow_brake_cannot_brake_live_math():
    control = pa._control_vote(_shadow(900.0, braking=True))
    assert control["braking"] is True and control["present"] is False
    result = pa.arbitrate([
        pa._mark_live_authority(pa._vote("cardiac", 60, False, 1.0),
                                "CARDIAC_RUNTIME"),
        control,
        pa._mark_live_authority(pa._vote("rhythm", 70, False, 0.7),
                                "RHYTHM_RUNTIME"),
    ])
    assert result["n_present"] == 2
    assert result["n_braking"] == 0
    assert not result["driver"].startswith("brake")
    assert result["color"] == "GREEN"


def t_valid_brake_still_wins():
    control = pa._control_vote(_shadow(30.0))
    cardiac = pa._mark_live_authority(
        pa._vote("cardiac", 40, True, 1.0, "AMBER"), "CARDIAC_RUNTIME")
    result = pa.arbitrate([cardiac, control])
    assert result["driver"].startswith("brake:cardiac")
    assert result["n_braking"] == 1


def t_precision_missing_authority_is_fail_closed():
    os.environ[pa.FLAG_PRECISION] = "1"
    pa._period_hist.clear()
    try:
        handmade = {
            "heart": "handmade", "present": True, "period_s": 60.0,
            "precision": 0.7, "braking": False, "color": "GREEN", "mode": "LIVE",
        }
        out = pa._apply_precision([handmade])[0]
        assert "handmade" not in pa._period_hist
        assert "precision_src" not in out
    finally:
        os.environ.pop(pa.FLAG_PRECISION, None)
        pa._period_hist.clear()


def t_arbitrate_missing_authority_is_fail_closed():
    legacy = {
        "heart": "legacy", "present": True, "period_s": 900.0,
        "braking": True, "precision": 1.0, "color": "RED", "mode": "LIVE",
    }
    result = pa.arbitrate([legacy])
    assert result["n_present"] == 0
    assert result["n_braking"] == 0
    assert result["driver"] == "abstain"
    for key in ("n_moving", "n_held", "n_constant", "n_unknown_mode"):
        assert result[key] == 0


def t_arbitrate_defense_in_depth_excludes_ineligible_present_vote():
    forged = pa._vote("control_law", 900, True, 1.0, "RED")
    forged["eligible_for_live"] = False
    result = pa.arbitrate([forged, pa._vote("rhythm", 60, False, 1.0)])
    assert result["n_present"] == 1
    assert result["n_braking"] == 0
    assert result["color"] == "GREEN"


def t_gather_views_has_two_live_votes_not_three():
    votes = pa.gather_views(**_views())
    control = next(v for v in votes if v["heart"] == "control_law")
    assert control["period_s"] == 244.4
    assert control["present"] is False
    result = pa.arbitrate(votes)
    assert result["n_present"] == 2
    assert result["n_moving"] == 1
    assert result["driver"] == "solo:rhythm"


def t_faster_candidate_is_held_at_previous_live_period():
    out = pa._apply_live_authority(_candidate(55.0), _previous(96.32))
    assert out["wire_open"] is True
    assert out["candidate_period_s"] == 55.0
    assert out["effective_period_s"] == 96.32
    assert out["authority_floor_s"] == 96.32
    assert out["authority_hold_applied"] is True
    assert out["driver"] == "authority-hold"
    assert out["authority_status"] == "HELD_NO_ACCELERATION"


def t_slower_candidate_is_allowed():
    out = pa._apply_live_authority(_candidate(120.0), _previous(96.32))
    assert out["wire_open"] is True
    assert out["effective_period_s"] == 120.0
    assert out["authority_floor_s"] == 96.32
    assert out["authority_hold_applied"] is False
    assert out["driver"] == "consensus"
    assert out["authority_status"] == "CANDIDATE_SLOWER_OR_EQUAL"


def t_transient_slow_candidate_does_not_ratchet_the_fixed_anchor():
    first = pa._apply_live_authority(_candidate(120.0), _previous(96.32))
    assert first["effective_period_s"] == 120.0
    assert first["authority_floor_s"] == 96.32
    first["written"] = True
    second = pa._apply_live_authority(_candidate(70.0), first)
    assert second["authority_floor_s"] == 96.32
    assert second["effective_period_s"] == 96.32
    assert second["effective_period_s"] != 120.0
    assert second["authority_hold_applied"] is True


def t_hold_persists_across_later_beats_and_restart():
    first = pa._apply_live_authority(_candidate(55.0), _previous(96.32))
    first["written"] = True
    second = pa._apply_live_authority(_candidate(60.0), first)
    assert second["effective_period_s"] == 96.32
    assert second["authority_floor_s"] == 96.32
    assert second["authority_hold_applied"] is True
    second["written"] = True
    third = pa._apply_live_authority(_candidate(70.0), second)
    assert third["effective_period_s"] == 96.32
    assert third["authority_floor_s"] == 96.32


def t_temporarily_closed_wire_preserves_fixed_anchor():
    closed = pa._apply_live_authority(
        dict(_candidate(55.0), wire_requested_open=False), _previous(96.32))
    assert closed["wire_open"] is False
    assert closed["authority_floor_s"] == 96.32
    closed["written"] = True
    reopened = pa._apply_live_authority(_candidate(55.0), closed)
    assert reopened["wire_open"] is True
    assert reopened["authority_floor_s"] == 96.32
    assert reopened["effective_period_s"] == 96.32


def t_invalid_previous_record_cannot_create_a_floor():
    invalids = [
        {},
        {"schema": "wrong", "effective_period_s": 96.32,
         "wire_open": True, "written": True},
        {"schema": pa.SCHEMA, "effective_period_s": float("nan"),
         "wire_open": True, "written": True},
        {"schema": pa.SCHEMA, "effective_period_s": 96.32,
         "wire_open": False, "written": True},
        {"schema": pa.SCHEMA, "effective_period_s": 96.32,
         "wire_open": True, "written": False},
    ]
    for previous in invalids:
        out = pa._apply_live_authority(_candidate(55.0), previous)
        assert out["wire_open"] is False
        assert out["applied_period_known"] is False
        assert out["authority_status"] == "NO_VALID_BASELINE"
        assert out["authority_floor_source"] == "INVALID_OR_MISSING"


def t_snapshot_separates_candidate_from_applied_period():
    _reset_wire()
    snap = pa.arbiter_snapshot(**_views(), beat=8)
    assert snap["advisory_only"] is True
    assert snap["applied_period_known"] is False
    assert snap["candidate_period_s"] == snap["effective_period_s"]
    assert snap["wire_open"] is False
    assert snap["authority_status"] == "ADVISORY_CANDIDATE"


def t_live_baseline_fixture_removes_shadow_without_acceleration():
    _reset_wire()
    try:
        _arm_wire()
        candidate = pa.arbiter_snapshot(**_views(), beat=48968)
        applied = pa._apply_live_authority(candidate, _previous(96.32))
        control = next(v for v in applied["votes"] if v["heart"] == "control_law")
        assert control["period_s"] == 244.4
        assert control["present"] is False
        assert applied["n_present"] == 2
        assert applied["candidate_period_s"] < 96.32
        assert applied["effective_period_s"] == 96.32
        assert applied["wire_open"] is True
    finally:
        _reset_wire()


def t_gate_is_rechecked_at_the_locked_commit_point():
    _reset_wire()
    try:
        _arm_wire()
        pa.LATEST.parent.mkdir(parents=True, exist_ok=True)
        pa.LATEST.write_text(json.dumps(_previous(96.32)), encoding="utf-8")
        original_wire = pa.wire_open
        calls = [0]

        def _wire_sequence():
            calls[0] += 1
            return ((True, []) if calls[0] == 1
                    else (False, ["activation removed before commit"]))

        pa.wire_open = _wire_sequence
        try:
            out = pa.persist(**_views(), beat=48973)
        finally:
            pa.wire_open = original_wire
        assert calls[0] >= 2
        assert out["written"] is True
        assert out["wire_open"] is False
        assert out["authority_status"] == "WIRE_CLOSED"
        disk = pa.read_latest()
        assert disk["wire_open"] is False
        assert disk["wire_requested_open"] is False
    finally:
        _reset_wire()


def t_primary_write_failure_closes_live_wire_and_preserves_previous():
    _reset_wire()
    try:
        _arm_wire()
        pa.LATEST.parent.mkdir(parents=True, exist_ok=True)
        before = _previous(96.32)
        pa.LATEST.write_text(json.dumps(before), encoding="utf-8")
        original_write = opslib.LockedJson.write
        opslib.LockedJson.write = lambda self, data: (_ for _ in ()).throw(
            OSError("primary-write-failed"))
        try:
            out = pa.persist(**_views(), beat=48970)
        finally:
            opslib.LockedJson.write = original_write
        assert out["written"] is False
        assert out["wire_open"] is False
        assert out["applied_period_known"] is False
        assert out["authority_status"] == "PERSIST_FAILED"
        assert json.loads(pa.LATEST.read_text(encoding="utf-8")) == before
    finally:
        _reset_wire()


def t_secondary_sink_failure_does_not_uncommit_latest():
    _reset_wire()
    try:
        _arm_wire()
        pa.LATEST.parent.mkdir(parents=True, exist_ok=True)
        pa.LATEST.write_text(json.dumps(_previous(96.32)), encoding="utf-8")
        original_append = opslib.append_jsonl
        opslib.append_jsonl = lambda *a, **k: (_ for _ in ()).throw(
            OSError("secondary-sink-failed"))
        try:
            out = pa.persist(**_views(), beat=48971)
        finally:
            opslib.append_jsonl = original_append
        assert out["written"] is True
        assert out["wire_open"] is True
        assert out["sink_written"] is False
        disk = pa.read_latest()
        assert disk["written"] is True and disk["wire_open"] is True
    finally:
        _reset_wire()


def t_stop_and_halt_close_both_live_entry_points():
    _reset_wire()
    try:
        _arm_wire()
        pa.LATEST.parent.mkdir(parents=True, exist_ok=True)
        pa.LATEST.write_text(json.dumps(_previous(96.32)), encoding="utf-8")
        opslib.STOP_ORGANISM.write_text("stop", encoding="utf-8")
        try:
            persisted = pa.persist(**_views(), beat=48972)
            period, direct = pa.effective_period_if_open(300.0, **_views())
        finally:
            opslib.STOP_ORGANISM.unlink()
        assert persisted["wire_open"] is False
        assert persisted["authority_status"] == "HALTED"
        assert period == 300.0
        assert direct["wire_open"] is False
        assert direct["authority_status"] == "HALTED"
    finally:
        _reset_wire()


def t_persist_and_effective_api_share_the_same_hold():
    _reset_wire()
    try:
        _arm_wire()
        pa.LATEST.parent.mkdir(parents=True, exist_ok=True)
        pa.LATEST.write_text(json.dumps(_previous(96.32)), encoding="utf-8")
        persisted = pa.persist(**_views(), beat=48969)
        assert persisted["written"] is True
        assert persisted["wire_open"] is True
        assert persisted["effective_period_s"] == 96.32
        assert persisted["candidate_period_s"] < 96.32
        period, snap = pa.effective_period_if_open(300.0, **_views())
        assert period == 96.32
        assert snap["effective_period_s"] == 96.32
        assert snap["authority_hold_applied"] is True
        disk = pa.read_latest()
        assert disk["authority_policy"] == pa.AUTHORITY_POLICY
        assert disk["written"] is True
    finally:
        _reset_wire()


if __name__ == "__main__":
    checks = [(name, fn) for name, fn in sorted(globals().items())
              if name.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'OK' if not failed else 'FAIL'} test_pulse_arbiter_authority: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
