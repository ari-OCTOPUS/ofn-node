#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P0 MERGE-EFFECT: owner [merge]/[reject] human-append must affect apply_merge + gate.

Fixture-only. No live Telegram send. No auto-merge without simulated human-append.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
for _p in (str(_OPS), str(_OPS / "doctor"), str(_OPS / "budget"), str(_OPS / "cortex")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import harness  # noqa: E402
ENV = harness.setup("merge-effect-p0")

import doctor as _docmod  # noqa: E402
import lab_bridge as _lb  # noqa: E402
import self_audit as sa  # noqa: E402


class _VerdictChan:
    """Simulated human-append channel (claim/ack). One verdict, then empty."""

    def __init__(self, rfc_id: str, verdict: str):
        self._v = [(rfc_id, verdict, 1)]
        self.begin_calls = []
        self.ack_calls = []

    def claim_rfc_verdicts(self, worker_id, lease_s=300):
        v, self._v = self._v, []
        return v

    def begin_rfc_apply(self, rfc_id, revision, operation_key):
        self.begin_calls.append((rfc_id, revision, operation_key))
        return True

    def ack_rfc_verdict(self, rfc_id, revision, *, applied, receipt_id=""):
        self.ack_calls.append(
            {"rfc_id": rfc_id, "revision": revision,
             "applied": applied, "receipt_id": receipt_id})
        return True


def _doctor(chan):
    return _docmod.Doctor(state_dir=str(Path(ENV["ops"]) / "state"),
                          approval_channel=chan)


def _mk_evidence(root: Path, name: str = "proof.json") -> Path:
    p = root / name
    p.write_text(json.dumps({"schema": "merge-effect-proof/1", "ok": True}),
                 encoding="utf-8")
    return p


def t_merge_with_proofs_calls_apply_merge_and_gate():
    """Simulated [merge] human-append with proofs -> apply_merge + gate ok."""
    root = Path(tempfile.mkdtemp(prefix="merge-effect-ok-"))
    evidence = _mk_evidence(root)
    chan = _VerdictChan("rfc-merge-ok", "merge-approved")
    d = _doctor(chan)
    rfc = _docmod.RFC(
        rfc_id="rfc-merge-ok", bottleneck="b", fix="f", expected_lift="x",
        status="submitted", rollback="revert proof fixture",
        sandbox_result={
            "test_ok": True,
            "test_outcome": "pass",
            "evidence_path": str(evidence),
            "rollback_plan": "revert proof fixture",
            "experiment_id": "exp-merge-ok",
        },
    )
    d._rfcs["rfc-merge-ok"] = rfc
    calls = {"n": 0}
    real_apply = d.apply_merge

    def _wrap(r):
        calls["n"] += 1
        return real_apply(r)

    d.apply_merge = _wrap  # type: ignore[method-assign]
    os.environ["OCTOPUS_WIRE_APPLY_MERGE"] = "1"
    try:
        d.run_cycle(beat=1)
    finally:
        os.environ.pop("OCTOPUS_WIRE_APPLY_MERGE", None)
    assert calls["n"] == 1, calls
    assert d._rfcs["rfc-merge-ok"].status == "merged", d._rfcs["rfc-merge-ok"].status
    assert chan.begin_calls, "begin_rfc_apply must run before apply"
    assert chan.ack_calls and chan.ack_calls[0]["applied"] is True


def t_merge_without_proofs_refuses_promote():
    """Simulated [merge] with incomplete proofs -> gate refuse, no promote."""
    chan = _VerdictChan("rfc-merge-bad", "merge-approved")
    d = _doctor(chan)
    rfc = _docmod.RFC(
        rfc_id="rfc-merge-bad", bottleneck="b", fix="f", expected_lift="x",
        status="submitted",
        sandbox_result={
            "test_ok": False,
            "evidence_path": "",
            "rollback_plan": "",
            "experiment_id": "exp-merge-bad",
        },
    )
    d._rfcs["rfc-merge-bad"] = rfc
    calls = {"n": 0}
    real_apply = d.apply_merge

    def _wrap(r):
        calls["n"] += 1
        return real_apply(r)

    d.apply_merge = _wrap  # type: ignore[method-assign]
    os.environ["OCTOPUS_WIRE_APPLY_MERGE"] = "1"
    try:
        d.run_cycle(beat=1)
    finally:
        os.environ.pop("OCTOPUS_WIRE_APPLY_MERGE", None)
    assert calls["n"] == 0, "gate must refuse apply_merge when proofs fail"
    assert d._rfcs["rfc-merge-bad"].status == "submitted"
    assert chan.ack_calls and chan.ack_calls[0]["applied"] is False


def t_reject_does_not_promote_or_apply_merge():
    """Simulated [reject] human-append -> human-rejected, never apply_merge."""
    chan = _VerdictChan("rfc-rej", "denied")
    d = _doctor(chan)
    rfc = _docmod.RFC(
        rfc_id="rfc-rej", bottleneck="b", fix="f", expected_lift="x",
        status="submitted",
        sandbox_result={
            "test_ok": True,
            "evidence_path": str(_mk_evidence(Path(tempfile.mkdtemp()), "r.json")),
            "rollback_plan": "n/a",
        },
    )
    d._rfcs["rfc-rej"] = rfc
    calls = {"n": 0}
    real_apply = d.apply_merge

    def _wrap(r):
        calls["n"] += 1
        return real_apply(r)

    d.apply_merge = _wrap  # type: ignore[method-assign]
    os.environ["OCTOPUS_WIRE_APPLY_MERGE"] = "1"
    try:
        d.run_cycle(beat=1)
    finally:
        os.environ.pop("OCTOPUS_WIRE_APPLY_MERGE", None)
    assert calls["n"] == 0, "reject must never call apply_merge"
    assert d._rfcs["rfc-rej"].status == "human-rejected"
    assert not chan.begin_calls


def t_lab_bridge_unit_merge_and_reject():
    """Direct apply_owner_verdict: merge promotes with proofs; reject never does."""
    root = Path(tempfile.mkdtemp(prefix="merge-effect-unit-"))
    evidence = _mk_evidence(root)
    seen = []

    def _fake_apply(rfc):
        seen.append(getattr(rfc, "rfc_id", rfc))
        if hasattr(rfc, "status"):
            rfc.status = "merged"
        return True

    rfc = _docmod.RFC(rfc_id="u1", bottleneck="b", fix="f", expected_lift="x",
                      status="submitted")
    ok = _lb.apply_owner_verdict(
        verb="[merge]", apply_merge_fn=_fake_apply, rfc=rfc,
        test_ok=True, evidence_path=str(evidence),
        rollback_plan="roll back u1")
    assert ok.get("applied") and ok.get("promoted") and ok.get("gate", {}).get("ok")
    assert seen == ["u1"]

    seen.clear()
    rfc2 = _docmod.RFC(rfc_id="u2", bottleneck="b", fix="f", expected_lift="x",
                       status="submitted")
    rej = _lb.apply_owner_verdict(
        verb="[reject]", apply_merge_fn=_fake_apply, rfc=rfc2,
        test_ok=True, evidence_path=str(evidence),
        rollback_plan="roll back u2")
    assert rej.get("applied") is False and rej.get("promoted") is False
    assert seen == []
    assert rfc2.status == "human-rejected"

    refused = _lb.apply_owner_verdict(
        verb="merge", apply_merge_fn=_fake_apply, rfc=rfc2,
        test_ok=False, evidence_path=None, rollback_plan=None,
        require_gate=True)
    assert refused.get("refused") is True
    assert refused.get("promoted") is False
    assert seen == []


def t_self_audit_probe_evidence_bound_done():
    from unittest import mock
    real_doc = _OPS / "doctor" / "doctor.py"
    real_lb = _OPS / "doctor" / "lab_bridge.py"
    with mock.patch.object(sa, "_doctor_py_path", return_value=real_doc):
        with mock.patch.object(sa, "_lab_bridge_py_path", return_value=real_lb):
            item = sa._probe_owner_verdict_effect()
    assert item.get("evidence_bound") is True, item
    assert item["status"] == "Done", item
    assert "apply_merge" in item["evidence"]
    assert "gate" in item["evidence"].lower() or "gate_promote" in item["evidence"]


def t_legacy_merge_without_lab_proofs_still_applies():
    """No sandbox proofs -> legacy path still calls apply_merge (knob tests)."""
    chan = _VerdictChan("rfc-legacy", "merge-approved")
    d = _doctor(chan)
    d._rfcs["rfc-legacy"] = _docmod.RFC(
        rfc_id="rfc-legacy", bottleneck="b", fix="f", expected_lift="x",
        status="submitted")
    os.environ["OCTOPUS_WIRE_APPLY_MERGE"] = "1"
    try:
        d.run_cycle(beat=1)
    finally:
        os.environ.pop("OCTOPUS_WIRE_APPLY_MERGE", None)
    assert d._rfcs["rfc-legacy"].status == "merged"


def main() -> int:
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("t_") and callable(v)]
    failed = 0
    for fn in tests:
        try:
            fn()
            print("PASS", fn.__name__)
        except Exception as exc:
            failed += 1
            print("FAIL", fn.__name__, type(exc).__name__ + ":", exc)
    print("RESULT", "failed=" + str(failed), "passed=" + str(len(tests) - failed))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
