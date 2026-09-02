# Lane LB tests — proposal destiny (scenarios 6, 7, 8, 14 + hard rules).
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ofn.doctor.destiny import (  # noqa: E402
    DestinyEngine, InvalidProposalError, OUTCOMES, Proposal,
)


def _engine(tmp_path) -> DestinyEngine:
    return DestinyEngine(tmp_path / "journal.jsonl")


def _prop(**kw) -> Proposal:
    base = dict(id="P-1", title="do a thing", target_path="ofn/doctor/x.py",
                action="code_change", reversible=True, evidence_refs=["findings.json#F-1"])
    base.update(kw)
    return Proposal(**base)


def test_06_valid_proposal_reaches_an_outcome(tmp_path):
    eng = _engine(tmp_path)
    d = eng.assign(_prop())
    assert d.outcome in OUTCOMES
    assert eng.outcomes()["P-1"] == d.outcome
    assert eng.orphan_count() == 0


def test_07_invalid_proposal_is_rejected_with_reason(tmp_path):
    eng = _engine(tmp_path)
    d = eng.assign(_prop(evidence_refs=[]))          # no evidence → invalid
    assert d.outcome == "REJECTED_WITH_REASON"
    assert "evidence" in d.reason
    assert eng.outcomes()["P-1"] == "REJECTED_WITH_REASON"
    # direct misuse of decide() still raises (API honesty)
    with pytest.raises(InvalidProposalError):
        eng.decide(_prop(evidence_refs=[], id="P-2"))


def test_08_sensitive_proposal_escalates_to_owner(tmp_path):
    eng = _engine(tmp_path)
    d = eng.assign(_prop(id="P-S", target_path=".github/workflows/ci.yml"))
    assert d.outcome == "ESCALATED_TO_OWNER"
    assert any("forbidden_target" in t for t in d.rule_trace)


def test_irreversible_proposal_escalates(tmp_path):
    eng = _engine(tmp_path)
    d = eng.assign(_prop(id="P-IR", reversible=False))
    assert d.outcome == "ESCALATED_TO_OWNER"


def test_forbidden_targets_escalate(tmp_path):
    eng = _engine(tmp_path)
    for i, target in enumerate([".env", "_ops/state/x.json", "owner-key.enc",
                                 "flags.cmd", "CODEOWNERS"]):
        d = eng.assign(_prop(id=f"P-F{i}", target_path=target))
        assert d.outcome == "ESCALATED_TO_OWNER", target


def test_shared_surface_proposal_is_queued_not_written(tmp_path):
    eng = _engine(tmp_path)
    d = eng.assign(_prop(id="P-Q", target_path="VERDICT_QUEUE.md", action="append"))
    assert d.outcome == "QUEUED_WITH_REASON"
    assert "payload" in d.reason.lower()


def test_merge_is_never_an_outcome(tmp_path):
    assert "MERGE" not in OUTCOMES and "MERGED" not in OUTCOMES
    eng = _engine(tmp_path)
    d = eng.assign(_prop(id="P-M"))
    assert d.outcome == "PR_CREATED"                 # merge stays human, always


def test_executor_failure_escalates_without_retry(tmp_path):
    eng = _engine(tmp_path)
    calls = []

    def boom(_prop):
        calls.append(1)
        raise RuntimeError("gh down")

    d = eng.assign(_prop(id="P-E"), executor=boom)
    assert d.outcome == "ESCALATED_TO_OWNER"
    assert d.rule_trace[-1] == "executor_failed"
    assert len(calls) == 1                           # security rule: no auto-retry


def test_14_crash_mid_proposal_leaves_no_pending(tmp_path):
    journal = tmp_path / "journal.jsonl"
    # simulate a crash: STARTED written, DONE never happened
    from ofn.doctor.receipts import canonical_json, sha256_text
    row = {"ts": "2026-09-02T00:00:00Z", "proposal_id": "P-CRASH",
           "phase": "STARTED", "outcome_plan": "PR_CREATED"}
    row["line_sha256"] = sha256_text(canonical_json(row))
    journal.write_text(canonical_json(row) + "\n", encoding="utf-8")

    eng = DestinyEngine(journal)                     # load → recover
    outcomes = eng.outcomes()
    assert outcomes["P-CRASH"] == "ESCALATED_TO_OWNER"
    assert eng.orphan_count() == 0
    # PENDING is not representable in the outcome space
    assert "PENDING" not in OUTCOMES
    assert all(o in OUTCOMES for o in outcomes.values())


def test_incident_rule_on_deny_touch(tmp_path):
    eng = _engine(tmp_path)
    eng.assign(_prop(id="P-SEC", target_path="_ops/state/ledger.json"))
    rows = eng._load()
    started = [r for r in rows if r["proposal_id"] == "P-SEC" and r["phase"] == "STARTED"]
    done = [r for r in rows if r["proposal_id"] == "P-SEC" and r["phase"] == "DONE"]
    assert started and done
    assert done[0]["outcome"] == "ESCALATED_TO_OWNER"
    assert all(r.get("line_sha256") for r in rows)   # evidence preserved append-only
