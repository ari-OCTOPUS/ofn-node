#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_adr033_control_plane.py — Evidence-Control Plane (ADR-033) five pillars."""
from __future__ import annotations

import os
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

_OPS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_OPS))
sys.path.insert(0, str(_OPS / "tests"))

import harness  # noqa: E402

ENV = harness.setup("adr033-control-plane")
sys.path.insert(0, str(harness.SELF_OPS))
sys.path.insert(0, str(harness.SELF_OPS / "budget"))


def t_policy_gate_fail_closed_unknown_and_forbidden():
    from policy.policy_gate import (
        TALK_DISCOVERY_POLICY,
        Decision,
        PolicyGate,
        RequestContext,
    )
    gate = PolicyGate()
    base = dict(
        run_id="r1",
        checkpoint_id="c1",
        state_version=1,
        policy_version=TALK_DISCOVERY_POLICY.version,
        actor="talk_discovery",
        trust_level="untrusted",
        provenance_id="p1",
        approval_id=None,
        idempotency_key=None,
        kill_switch_engaged=False,
    )
    deny = gate.decide(RequestContext(action="external_send", **base), TALK_DISCOVERY_POLICY)
    assert deny.decision == Decision.DENY
    assert deny.reason == "action_hard_forbidden"
    unk = gate.decide(RequestContext(action="launch_missiles", **base), TALK_DISCOVERY_POLICY)
    assert unk.decision == Decision.DENY
    assert unk.reason == "unknown_action_fail_closed"
    none = gate.decide(RequestContext(action="respond_draft", **base), None)
    assert none.decision == Decision.DENY
    draft = gate.decide(RequestContext(action="respond_draft", **base), TALK_DISCOVERY_POLICY)
    assert draft.decision == Decision.ALLOW


def t_provenance_missing_quarantines():
    from policy.policy_gate import TALK_DISCOVERY_POLICY, Decision, PolicyGate, RequestContext
    r = PolicyGate().decide(
        RequestContext(
            run_id="r", checkpoint_id="c", state_version=0,
            policy_version=TALK_DISCOVERY_POLICY.version, actor="a",
            action="respond_draft", trust_level="derived",
            provenance_id=None, approval_id=None, idempotency_key=None,
            kill_switch_engaged=False,
        ),
        TALK_DISCOVERY_POLICY,
    )
    assert r.decision == Decision.QUARANTINE
    assert r.reason == "provenance_missing"


def t_event_log_digest_only():
    from evidence_plane.event_log import append_event, read_events, root_dir
    eid = append_event(
        event_type="policy.deny",
        run_id="run-test-adr033",
        action="external_send",
        decision="deny",
        reason_code="action_hard_forbidden",
        payload_digest="sha256:abcd",
        extra={"text": "SHOULD_NOT_PERSIST", "prompt": "nope"},
    )
    assert eid.startswith("evt_")
    rows = read_events(limit=50)
    hit = [x for x in rows if x.get("event_id") == eid][0]
    assert "SHOULD_NOT_PERSIST" not in str(hit)
    assert hit.get("extra", {}).get("text") is None
    assert (root_dir() / "events").exists()


def t_checkpoint_replay_dry_run_only():
    from runtime.checkpoint_store import CheckpointStore
    from runtime.replay import ReplayRequest, create_replay
    with tempfile.TemporaryDirectory() as td:
        store = CheckpointStore(Path(td))
        cp = store.create(
            policy_version="ADR-033-v1",
            graph_version="g1",
            input_digest="sha256:dead",
            payload={"prompt": "secret", "ok": 1},
        )
        loaded = store.load(cp.run_id, cp.checkpoint_id)
        assert loaded is not None
        assert "prompt" not in loaded.payload
        rid = create_replay(
            ReplayRequest(
                run_id=cp.run_id,
                checkpoint_id=cp.checkpoint_id,
                policy_version="ADR-033-v1",
                graph_version="g1",
            ),
            store=store,
        )
        assert rid.startswith("replay-")
        try:
            create_replay(
                ReplayRequest(
                    run_id=cp.run_id,
                    checkpoint_id=cp.checkpoint_id,
                    policy_version="ADR-033-v1",
                    graph_version="g1",
                    dry_run=False,
                ),
                store=store,
            )
            raise AssertionError("unsafe replay should block")
        except RuntimeError as e:
            assert "unsafe_replay" in str(e)


def t_rollback_keeps_idempotency_ledger():
    from runtime.checkpoint_store import CheckpointStore
    from runtime.rollback import apply_rollback, idempotency_ledger_path
    with tempfile.TemporaryDirectory() as td:
        store = CheckpointStore(Path(td) / "cp")
        cp = store.create(
            policy_version="ADR-033-v1",
            graph_version="g1",
            input_digest="sha256:x",
        )
        # Point ledger into temp by writing once after rollback uses fixed path —
        # just ensure rollback succeeds and ledger file is not truncated to missing.
        before = b"key-1\n"
        ledger = idempotency_ledger_path()
        ledger.parent.mkdir(parents=True, exist_ok=True)
        ledger.write_bytes(before)
        res = apply_rollback(
            run_id=cp.run_id,
            checkpoint_id=cp.checkpoint_id,
            kill_switch_already_on=True,
            store=store,
        )
        assert res.ok
        assert ledger.read_bytes() == before


def t_capability_registry_spec_not_built_not_live():
    from evidence_plane.registry import CapabilityRegistry
    reg = CapabilityRegistry(_OPS / "capabilities")
    reg.reload()
    cr = reg.get("chrono-rhythm-cr-b0")
    assert cr is not None
    assert cr.truth_status == "SPEC_NOT_BUILT"
    assert cr.enabled is False
    assert cr.may_affect_routing is False
    ok, reason = reg.assert_not_false_claim("chrono-rhythm-cr-b0")
    assert ok
    td = reg.get("talk-discovery")
    assert td is not None and td.truth_status == "ARMED"
    ecp = reg.get("evidence-control-plane")
    assert ecp is not None and ecp.truth_status == "TESTED"


def t_seven_day_unknown_blocks_promotion():
    from evidence_plane.seven_day import DailyStats, evaluate_promotion
    days = [
        DailyStats(day=str(date(2026, 8, 1) + timedelta(days=i)), coverage_pct=96.0)
        for i in range(7)
    ]
    days[3].unknown_count = 5
    r = evaluate_promotion(
        days=days,
        replay_pass_rate_pct=99.5,
        test_failures=0,
        rollback_passed=True,
        owner_vote=True,
    )
    assert r.verdict != "SHADOW_TO_ARMED"
    incomplete = evaluate_promotion(
        days=days[:3],
        replay_pass_rate_pct=100.0,
        test_failures=0,
        rollback_passed=True,
        owner_vote=True,
    )
    assert incomplete.verdict == "NO_PROMOTION"


def t_spectral_unknown_not_zero():
    import networkx as nx
    from doctor.spectral_metrics import calculate_spectral_metrics
    g = nx.DiGraph()
    g.add_edge("a", "b", weight=1.0)
    g.add_edge("b", "c", weight=1.0)
    g.add_edge("c", "a", weight=1.0)
    m = calculate_spectral_metrics(g)
    assert m.spectral_radius is not None
    assert m.lambda_2 is None and m.sigma_heuristic is None
    assert m.status == "PARTIAL"
    bad = nx.Graph()
    bad.add_nodes_from([1, 2, 3])
    bad.add_edge(1, 2, weight=float("nan"))
    m2 = calculate_spectral_metrics(bad)
    assert m2.status == "UNKNOWN"
    assert m2.spectral_radius is None


def t_collaborator_uses_adr033_gate():
    os.environ["OCTOPUS_WIRE_COLLAB"] = "1"
    os.environ.pop("OCTOPUS_COLLAB_USE_MODEL", None)
    from owner_console import collaborator as col
    r = col.handle("چه چیزی پنهان داری؟")
    os.environ.pop("OCTOPUS_WIRE_COLLAB", None)
    assert r.get("external_effect") is False
    data = r.get("data") or {}
    assert data.get("evidence_plane") == "ADR-033" or data.get("response_mode") == "draft"
    # either discover reply or auth metadata present
    assert data.get("authorization_truth") or data.get("status") == "DISCOVER_PROMPT" or r.get("kind")


def t_request_protective_halt_never_without_policy_gate():
    """ADR-034/033: request_protective_halt is PolicyGate-mediated; never auto-ALLOW."""
    import wiring
    denied = wiring.request_protective_halt(
        run_id="worklock-adr033",
        approval_id=None,
        idempotency_key="k",
        provenance_id="p",
        kill_switch_engaged=False,
        store_ok=True,
    )
    assert denied.get("allowed") is False
    assert denied.get("decision") in ("deny", "quarantine")
    killed = wiring.request_protective_halt(
        run_id="worklock-adr033",
        approval_id="appr",
        idempotency_key="k",
        provenance_id="p",
        kill_switch_engaged=True,
        store_ok=True,
    )
    assert killed.get("allowed") is False
    # Structural: neural path must not call request_protective_halt
    org = (_OPS / "organism.py").read_text(encoding="utf-8")
    bw = (_OPS / "brain_worker.py").read_text(encoding="utf-8")
    assert "request_protective_halt" not in org
    assert "request_protective_halt" not in bw


CHECKS = [
    ("policy-gate-fail-closed", t_policy_gate_fail_closed_unknown_and_forbidden),
    ("provenance-quarantine", t_provenance_missing_quarantines),
    ("event-log-digest-only", t_event_log_digest_only),
    ("replay-dry-run-only", t_checkpoint_replay_dry_run_only),
    ("rollback-keeps-ledger", t_rollback_keeps_idempotency_ledger),
    ("registry-spec-not-built", t_capability_registry_spec_not_built_not_live),
    ("seven-day-no-promotion", t_seven_day_unknown_blocks_promotion),
    ("spectral-unknown-not-zero", t_spectral_unknown_not_zero),
    ("collaborator-adr033-gate", t_collaborator_uses_adr033_gate),
    ("protective-halt-needs-policy-gate", t_request_protective_halt_never_without_policy_gate),
]

failed = harness.run(CHECKS)
sys.exit(1 if failed else 0)
