#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_octopus_parity_modules.py — تست‌های واحد برای سه ماژولِ الهام‌گرفته از OMEGA-PARITY.

سه ماژول:
  · budget_frustration (شاخصِ ناامیدیِ بودجه)
  · organism_syndrome (سندرمِ cross-leg)
  · test_audit (رده‌بندِ green-lie)
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
for _p in (str(_OPS), str(_HERE), str(_OPS / "budget"), str(_OPS / "legs")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import harness  # noqa: E402
ENV = harness.setup("parity-modules")

import budget_frustration  # noqa: E402
import organism_syndrome  # noqa: E402
import test_audit  # noqa: E402


# ─── budget_frustration ────────────────────────────────────────────────────────

def t_frustration_snapshot_empty_log_is_honest():
    with tempfile.TemporaryDirectory() as d:
        snap = budget_frustration.frustration_snapshot(Path(d) / "nope.jsonl", 24.0)
    assert snap["ok"] is True
    assert snap["signal"] == "no_log_file"


def t_frustration_snapshot_aggregates_real_rows():
    with tempfile.TemporaryDirectory() as d:
        log = Path(d) / "log.jsonl"
        rows = [
            {"ts": "2099-01-01T00:00:00Z", "op": "reserve", "organ": "X",
             "est_usd": 1.0, "task": "t", "allow": True, "reserved": 1.0},
            {"ts": "2099-01-01T00:01:00Z", "op": "reserve", "organ": "X",
             "est_usd": 2.0, "task": "t", "allow": False, "reason": "cap:30"},
            {"ts": "2099-01-01T00:02:00Z", "op": "settle", "organ": "X",
             "est_usd": 1.0, "task": "t", "ok": True, "actual_usd": 0.5},
        ]
        log.write_text("\n".join(json.dumps(r) for r in rows) + "\n", "utf-8")
        # use a far-future now so rows are "recent"
        from datetime import datetime, timezone
        future = datetime(2099, 1, 2, tzinfo=timezone.utc)
        snap = budget_frustration.frustration_snapshot(log, 240.0, _now=future)
    x = snap["organs"]["X"]
    # reserve count = 2 (settle should NOT count as a request)
    assert x["requested_count"] == 2, x
    assert x["allowed_count"] == 1 and x["denied_count"] == 1, x
    assert x["denied_usd"] == 2.0, x
    assert x["denial_rate"] == 0.5, x


def t_frustration_index_zero_when_no_denial():
    snap = {"ok": True, "organs": {"X": {"requested_usd": 10.0, "denied_usd": 0.0}}}
    assert budget_frustration.frustration_index(snap) == 0.0


def t_frustration_index_proportional_to_denied_share():
    snap = {"ok": True, "organs": {"X": {"requested_usd": 10.0, "denied_usd": 3.0}}}
    assert abs(budget_frustration.frustration_index(snap) - 0.3) < 1e-9


def t_frustration_handles_corrupt_row_fail_soft():
    with tempfile.TemporaryDirectory() as d:
        log = Path(d) / "log.jsonl"
        log.write_text('{"valid": "row", "op": "reserve", "organ": "Y", "est_usd": 1.0, "allow": true, "ts": "2099-01-01T00:00:00Z"}\n{CORRUPT JSON\n', "utf-8")
        from datetime import datetime, timezone
        snap = budget_frustration.frustration_snapshot(log, 240.0, _now=datetime(2099, 1, 2, tzinfo=timezone.utc))
    assert snap["ok"] is True
    assert snap["rows_unparseable"] == 1
    assert "Y" in snap["organs"]


# ─── organism_syndrome ─────────────────────────────────────────────────────────

def _write_state(d, organ_state, budget_state):
    os.environ["BUDGET_STATE"] = str(Path(d) / "budget-state.json")
    # organ_state path is ORGAN_STATE from opslib — patch via env not available;
    # instead monkeypatch the module constant.
    op = Path(d) / "organ-state.json"
    op.write_text(json.dumps(organ_state), "utf-8")
    bp = Path(d) / "budget-state.json"
    bp.write_text(json.dumps(budget_state), "utf-8")
    return op, bp


def t_syndrome_budget_integrity_ok_when_matching():
    with tempfile.TemporaryDirectory() as d:
        op, bp = _write_state(d, {"organs": {"X": {"spent_month_musd": 0}}}, {"spent_month_aud": 0.0})
        organism_syndrome.ORGAN_STATE = op
        organism_syndrome.BUDGET_STATE = bp
        r = organism_syndrome.check_budget_integrity()
    assert r["ok"] is True, r


def t_syndrome_budget_integrity_flags_large_gap():
    with tempfile.TemporaryDirectory() as d:
        # organ spent a lot, global says zero → big gap
        op, bp = _write_state(d, {"organs": {"X": {"spent_month_musd": 50_000_000}}}, {"spent_month_aud": 0.0})
        organism_syndrome.ORGAN_STATE = op
        organism_syndrome.BUDGET_STATE = bp
        r = organism_syndrome.check_budget_integrity()
    assert r["ok"] is False, r
    assert r["gap_aud"] > 1.0, r


def t_syndrome_missing_source_is_unknown_not_ok():
    with tempfile.TemporaryDirectory() as d:
        organism_syndrome.ORGAN_STATE = Path(d) / "nope.json"
        organism_syndrome.BUDGET_STATE = Path(d) / "budget-state.json"
        (Path(d) / "budget-state.json").write_text('{"spent_month_aud": 0.0}', "utf-8")
        s = organism_syndrome.organism_syndrome()
    # I1 should be unknown (None) because organ_state missing
    assert s["syndrome_vector"]["I1_budget_integrity"] is None, s


def t_syndrome_never_returns_fail_open_on_missing():
    # missing both → unknowns, not ok=True
    with tempfile.TemporaryDirectory() as d:
        organism_syndrome.ORGAN_STATE = Path(d) / "nope1.json"
        organism_syndrome.BUDGET_STATE = Path(d) / "nope2.json"
        s = organism_syndrome.organism_syndrome()
    assert len(s["unknowns"]) >= 1, s


# ─── test_audit ────────────────────────────────────────────────────────────────

def t_audit_classifies_real_unittest():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "test_x.py"
        p.write_text('import harness\nENV=harness.setup("x")\ndef t_one():\n    assert 1==1\nif __name__=="__main__":\n    pass\n', "utf-8")
        r = test_audit.classify_test_file(p)
    assert r["kind"] == "real_unittest", r


def t_audit_classifies_no_op_bare():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "test_y.py"
        p.write_text('# just a comment, nothing else\n', "utf-8")
        r = test_audit.classify_test_file(p)
    assert r["kind"] == "no_op_or_bare", r
    assert r["green_lie_risk"] is True


def t_audit_classifies_pytest_fixture():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "test_z.py"
        p.write_text('import pytest\n@pytest.fixture\ndef x():\n    return 1\ndef test_thing(x):\n    assert x\n', "utf-8")
        r = test_audit.classify_test_file(p)
    assert r["kind"] == "real_pytest", r


def t_audit_never_crashes_on_garbage():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "test_w.py"
        p.write_text('\x00\x01garbage no defs\n', "utf-8", errors="ignore") if False else p.write_text('garbage no defs\n', "utf-8")
        r = test_audit.classify_test_file(p)
    assert "kind" in r


CHECKS = [
    ("frustration: empty log honest", t_frustration_snapshot_empty_log_is_honest),
    ("frustration: aggregates rows", t_frustration_snapshot_aggregates_real_rows),
    ("frustration: index zero no denial", t_frustration_index_zero_when_no_denial),
    ("frustration: index proportional", t_frustration_index_proportional_to_denied_share),
    ("frustration: corrupt row fail-soft", t_frustration_handles_corrupt_row_fail_soft),
    ("syndrome: integrity ok matching", t_syndrome_budget_integrity_ok_when_matching),
    ("syndrome: flags large gap", t_syndrome_budget_integrity_flags_large_gap),
    ("syndrome: missing source unknown", t_syndrome_missing_source_is_unknown_not_ok),
    ("syndrome: never fail-open missing", t_syndrome_never_returns_fail_open_on_missing),
    ("audit: classifies real unittest", t_audit_classifies_real_unittest),
    ("audit: classifies no-op bare", t_audit_classifies_no_op_bare),
    ("audit: classifies pytest fixture", t_audit_classifies_pytest_fixture),
    ("audit: never crashes garbage", t_audit_never_crashes_on_garbage),
]


if __name__ == "__main__":
    failed = harness.run(CHECKS)
    print(f"\n{'✅' if not failed else '❌'} test_octopus_parity_modules: {len(CHECKS) - failed}/{len(CHECKS)} passed")
    sys.exit(1 if failed else 0)
