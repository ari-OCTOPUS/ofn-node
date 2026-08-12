#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""talk_gate.py — Talk Discovery → ADR-033 PolicyGate bridge.

Preserves TalkDiscoveryPolicy API while routing through fail-closed PolicyGate
and appending durable events. Allowed path: retrieve_context / respond_draft only.
"""
from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from policy.policy_gate import (
    TALK_DISCOVERY_POLICY,
    Decision,
    GateResult,
    PolicyGate,
    RequestContext,
)


@dataclass(frozen=True)
class TalkGateDecision:
    allowed: bool
    reason: str
    decision: str
    requires_owner_approval: bool = False
    event_id: str | None = None
    policy_version: str = TALK_DISCOVERY_POLICY.version


def _kill_switch() -> bool:
    return os.environ.get("OCTOPUS_KILL_SWITCH", "0") == "1"


def evaluate_talk_action(
    action: str,
    *,
    actor: str = "talk_discovery",
    trust_level: str = "untrusted",
    provenance_id: str | None = "talk-discovery-session",
    approval_id: str | None = None,
    idempotency_key: str | None = None,
    run_id: str | None = None,
    checkpoint_id: str = "cp-live",
    state_version: int = 0,
    collab_enabled: bool = True,
    emit_event: bool = True,
) -> TalkGateDecision:
    if not collab_enabled:
        return TalkGateDecision(False, "collaborator disabled", Decision.DENY.value)

    ctx = RequestContext(
        run_id=run_id or f"run-{uuid4().hex[:12]}",
        checkpoint_id=checkpoint_id,
        state_version=state_version,
        policy_version=TALK_DISCOVERY_POLICY.version,
        actor=actor,
        action=action,
        trust_level=trust_level,
        provenance_id=provenance_id,
        approval_id=approval_id,
        idempotency_key=idempotency_key,
        kill_switch_engaged=_kill_switch(),
    )
    result: GateResult = PolicyGate().decide(ctx, TALK_DISCOVERY_POLICY)
    event_id = None
    if emit_event:
        try:
            from evidence_plane.event_log import append_event
            event_id = append_event(
                event_type=f"policy.{result.decision.value}",
                run_id=ctx.run_id,
                checkpoint_id=ctx.checkpoint_id,
                policy_version=ctx.policy_version,
                state_version=ctx.state_version,
                actor=ctx.actor,
                action=ctx.action,
                decision=result.decision.value,
                reason_code=result.reason,
                payload_digest="sha256:" + hashlib.sha256(
                    f"{ctx.action}|{ctx.trust_level}".encode()
                ).hexdigest()[:16],
            )
        except Exception:  # noqa: BLE001 — gate must not fail open on log miss
            pass

    requires = action == "write_episodic_memory"
    return TalkGateDecision(
        allowed=result.allowed,
        reason=result.reason,
        decision=result.decision.value,
        requires_owner_approval=requires,
        event_id=event_id,
    )


def guard_talk_discovery_draft(text: str) -> dict[str, Any]:
    """Single choke-point for collaborator draft path. Returns auth metadata."""
    digest = hashlib.sha256(str(text or "").encode("utf-8")).hexdigest()[:16]
    d = evaluate_talk_action(
        "respond_draft",
        trust_level="untrusted",
        provenance_id=f"owner-input:{digest}",
        run_id=f"talk-{digest}",
    )
    # Always re-check hard forbid of external_send (defense in depth).
    deny = evaluate_talk_action(
        "external_send",
        trust_level="verified",
        provenance_id=f"owner-input:{digest}",
        approval_id="would-not-matter",
        idempotency_key="deny-check",
        run_id=f"talk-{digest}-deny",
    )
    return {
        "draft": d,
        "external_send_denied": not deny.allowed,
        "policy_version": TALK_DISCOVERY_POLICY.version,
    }
