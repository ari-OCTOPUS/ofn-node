#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_approval_state.py — Talk Discovery approval gates (hash/expiry/forbidden)."""
from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

_OPS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_OPS))
sys.path.insert(0, str(_OPS / "tests"))

import harness  # noqa: E402
from collab.approval_state import (  # noqa: E402
    ApprovalStatus,
    TalkProposal,
    approve_or_block,
    can_approve,
    clear_idempotency_registry,
    proposal_fingerprint,
)


def _prop(**kw) -> TalkProposal:
    base = dict(
        proposal_id="p1",
        action="respond_draft",
        payload_digest="deadbeef",
        policy_version="talk-discovery-policy.v2",
        state_version=1,
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        idempotency_key="idem-unique-1",
    )
    base.update(kw)
    return TalkProposal(**base)


def test_mutated_proposal_cannot_reuse_approval():
    clear_idempotency_registry()
    p = _prop()
    fp = proposal_fingerprint(p)
    ok, _ = can_approve(
        p, signed_fingerprint=fp, current_policy_version=p.policy_version
    )
    assert ok
    mutated = TalkProposal(
        proposal_id=p.proposal_id,
        action=p.action,
        payload_digest="MUTATED",
        policy_version=p.policy_version,
        state_version=p.state_version,
        expires_at=p.expires_at,
        idempotency_key=p.idempotency_key,
    )
    ok2, reason = can_approve(
        mutated, signed_fingerprint=fp, current_policy_version=p.policy_version
    )
    assert ok2 is False
    assert reason == "proposal_changed_after_approval"


def test_expired_owner_approval_is_blocked():
    clear_idempotency_registry()
    p = _prop(expires_at=datetime.now(UTC) - timedelta(seconds=1))
    fp = proposal_fingerprint(p)
    status, reason = approve_or_block(
        p, signed_fingerprint=fp, current_policy_version=p.policy_version
    )
    assert status == ApprovalStatus.EXPIRED
    assert reason == "proposal_expired"


def test_external_send_allowed_with_valid_owner_approval():
    """2026-08-12: hard-forbidden emptied; fingerprint/expiry still gate."""
    clear_idempotency_registry()
    p = _prop(action="external_send", policy_version="talk-discovery-policy.v2")
    fp = proposal_fingerprint(p)
    ok, reason = can_approve(
        p, signed_fingerprint=fp, current_policy_version="talk-discovery-policy.v2"
    )
    assert ok is True
    assert reason == "approved"


def test_policy_version_change_invalidates_approval():
    clear_idempotency_registry()
    p = _prop(policy_version="talk-discovery-policy.v1")
    fp = proposal_fingerprint(p)
    ok, reason = can_approve(
        p, signed_fingerprint=fp, current_policy_version="talk-discovery-policy.v2"
    )
    assert ok is False
    assert reason == "policy_version_mismatch"


def test_store_failure_returns_blocked_not_allowed():
    clear_idempotency_registry()
    p = _prop()
    fp = proposal_fingerprint(p)
    status, reason = approve_or_block(
        p,
        signed_fingerprint=fp,
        current_policy_version=p.policy_version,
        store_ok=False,
    )
    assert status == ApprovalStatus.BLOCKED
    assert reason == "store_failure_blocked"


def test_duplicate_idempotency_key_is_rejected():
    clear_idempotency_registry()
    p = _prop(idempotency_key="dup-key")
    fp = proposal_fingerprint(p)
    s1, _ = approve_or_block(
        p, signed_fingerprint=fp, current_policy_version=p.policy_version
    )
    assert s1 == ApprovalStatus.APPROVED
    p2 = _prop(
        proposal_id="p2",
        idempotency_key="dup-key",
        payload_digest="other",
    )
    fp2 = proposal_fingerprint(p2)
    ok, reason = can_approve(
        p2, signed_fingerprint=fp2, current_policy_version=p2.policy_version
    )
    assert ok is False
    assert reason == "duplicate_idempotency_key"


def test_spectral_disconnected_no_sigma_theater():
    import networkx as nx
    from doctor.spectral_metrics import calculate_spectral_metrics

    g = nx.Graph()
    g.add_nodes_from(["a", "b", "c", "d"])
    g.add_edge("a", "b", weight=1.0)
    g.add_edge("c", "d", weight=1.0)
    m = calculate_spectral_metrics(g)
    assert m.graph_disconnected is True
    assert m.sigma_heuristic is None
    assert m.reason == "graph_disconnected"


def test_discover_facade_v2_provenance():
    from discovery.sources import default_reply
    from discovery.discover_facade import DiscoveryReply

    reply = default_reply("کشف پنهان")
    assert isinstance(reply, DiscoveryReply)
    assert reply.schema == "DiscoveryReply.v1"
    assert reply.external_effect is False
    kinds = {f.provenance.source_kind for f in reply.facts}
    assert "world_discovery" in kinds or any(
        f.provenance.trust == "stale" for f in reply.facts
    ) or "journal" in kinds or "catalog" in kinds
    # World Discovery historical report must surface as stale when present
    wd = [f for f in reply.facts if f.provenance.source_kind == "world_discovery"]
    if wd:
        assert wd[0].provenance.trust == "stale"
    src = reply.sources_text()
    assert "Sources" in src or "شواهد" in src
    assert "digest=" in src or "digest" in src.lower() or "digest=" in "\n".join(
        reply.limitations
    )


CHECKS = [
    ("mutated-proposal-blocks", test_mutated_proposal_cannot_reuse_approval),
    ("expired-approval-blocked", test_expired_owner_approval_is_blocked),
    ("external-send-approvable", test_external_send_allowed_with_valid_owner_approval),
    ("policy-version-mismatch", test_policy_version_change_invalidates_approval),
    ("store-failure-blocked", test_store_failure_returns_blocked_not_allowed),
    ("duplicate-idempotency", test_duplicate_idempotency_key_is_rejected),
    ("spectral-disconnected", test_spectral_disconnected_no_sigma_theater),
    ("discover-facade-v2", test_discover_facade_v2_provenance),
]

failed = harness.run(CHECKS)
sys.exit(1 if failed else 0)
