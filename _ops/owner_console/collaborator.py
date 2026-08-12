#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""collaborator.py — collaborator engine (WP-E3 + Talk Discovery Phase A).

Wraps/extends conversation.py, does NOT replace it.
Default deterministic stub ($0, no network).
Real model behind OCTOPUS_COLLAB_USE_MODEL → collab_model_adapter → model_router.

Contract:
  schema: owner-console.reply.v1
  external_effect = false
  send_attempted = false
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent

import sys
if str(HERE.parent) not in sys.path:
    sys.path.insert(0, str(HERE.parent))
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from owner_console import conversation, collab_memory  # noqa: E402
from owner_console import collab_model_adapter as _model  # noqa: E402


def _is_enabled() -> bool:
    return os.environ.get("OCTOPUS_WIRE_COLLAB", "0") == "1"


def _use_model() -> bool:
    return os.environ.get("OCTOPUS_COLLAB_USE_MODEL", "0") == "1"


def _turn_id(owner_text: str) -> str:
    """Deterministic turn ID from owner text for replay-safe idempotency."""
    return hashlib.sha256(str(owner_text).encode("utf-8")).hexdigest()[:16]


def _stub_enhance(base_reply: dict, owner_text: str) -> dict:
    """Deterministic stub enhancement — rationale + model_source stub."""
    enhanced = dict(base_reply)
    data = dict(enhanced.get("data") or {})
    kind = enhanced.get("kind", "")
    if kind == "clarify":
        data["rationale"] = "stub: input ambiguous — needs narrower intent specification"
    elif kind == "intro":
        data["rationale"] = "stub: structural owner intro"
    elif kind == "capabilities":
        data["rationale"] = "stub: catalog lookup from capability manifest"
    elif kind == "runtime":
        data["rationale"] = "stub: live_snapshot read-only truth"
    elif kind == "blockers":
        data["rationale"] = "stub: health snapshot blockers"
    else:
        data["rationale"] = f"stub: deterministic reply for kind={kind}"
    enhanced["data"] = data
    enhanced["model_source"] = "deterministic-stub"
    return enhanced


# LLM may enrich talk turns; discover stays deterministic (journal/pulse evidence).
_LLM_KINDS = frozenset({"intro", "clarify", "chat"})


def _model_enhance(base_reply: dict, owner_text: str) -> dict:
    """Call model_router via adapter; on failure fall back to stub honestly."""
    kind = str(base_reply.get("kind") or "")
    if kind not in _LLM_KINDS:
        return _stub_enhance(base_reply, owner_text)

    result = _model.complete(owner_text, kind_hint=kind)
    if not result.get("ok"):
        enhanced = _stub_enhance(base_reply, owner_text)
        enhanced["model_source"] = "model-fallback-stub"
        data = dict(enhanced.get("data") or {})
        data["warning"] = f"model_call_failed:{result.get('reason') or 'unknown'}"
        enhanced["data"] = data
        return enhanced

    enhanced = dict(base_reply)
    data = dict(enhanced.get("data") or {})
    data["rationale"] = "model: model_router via collab_model_adapter"
    data["tier"] = result.get("tier")
    enhanced["data"] = data
    enhanced["text"] = result["text"]
    if kind == "clarify":
        enhanced["kind"] = "chat"
    enhanced["model_source"] = result.get("model_source") or "model"
    enhanced["estimated_cost"] = float(result.get("cost_usd") or 0.0)
    return enhanced


def handle(text: str, *, state_dir: Path | None = None) -> dict:
    """Handle owner input with collaborator enhancement.

    Default: deterministic stub ($0, no network).
    If OCTOPUS_COLLAB_USE_MODEL=1: collab_model_adapter → model_router.

    Policy: draft responses only — never external_effect / send.
    Content-free episodic digests (sha256 markers) are not WRITE_EPISODIC_MEMORY.
    """
    if not _is_enabled():
        return {
            "schema": "owner-console.reply.v1",
            "kind": "disabled",
            "text": "🚫 Collaborator غیرفعال است (OCTOPUS_WIRE_COLLAB=0).",
            "keyboard": [],
            "data": {"status": "DISABLED"},
            "external_effect": False,
            "estimated_cost": 0,
            "send_attempted": False,
            "authorization": None,
        }

    # ADR-033 Evidence-Control Plane: quarantine + PolicyGate (fail-closed).
    # Allowed path only: retrieve → reason → draft → display.
    auth_meta: dict = {}
    try:
        from evidence_plane.quarantine import admit, may_draft_reply
        from policy.talk_gate import guard_talk_discovery_draft

        envelope = admit(
            text=text,
            source_kind="user",
            trust_level="untrusted",
            injection_signals=False,
        )
        if not may_draft_reply(envelope):
            return {
                "schema": "owner-console.reply.v1",
                "kind": "blocked",
                "text": "🔐 ContextQuarantine: ورودی قابل مصرف عملیاتی نیست.",
                "keyboard": [],
                "data": {
                    "status": "QUARANTINED",
                    "provenance_id": envelope.provenance_id,
                },
                "external_effect": False,
                "estimated_cost": 0,
                "send_attempted": False,
                "authorization": None,
            }

        gate = guard_talk_discovery_draft(text)
        draft = gate["draft"]
        auth_meta = {
            "policy_version": gate["policy_version"],
            "gate_decision": draft.decision,
            "gate_reason": draft.reason,
            "event_id": draft.event_id,
            "provenance_id": envelope.provenance_id,
            "context_status": envelope.status.value,
            "external_send_denied": gate["external_send_denied"],
        }
        if not draft.allowed:
            return {
                "schema": "owner-console.reply.v1",
                "kind": "blocked",
                "text": f"🔐 PolicyGate: {draft.reason}",
                "keyboard": [],
                "data": {"status": "POLICY_BLOCKED", **auth_meta},
                "external_effect": False,
                "estimated_cost": 0,
                "send_attempted": False,
                "authorization": None,
            }
        assert gate["external_send_denied"] is True
    except Exception:  # noqa: BLE001 — import miss must not open effects
        # Fail closed on side-effects; still allow draft via legacy policy if present.
        try:
            from collab.talk_discovery_policy import TalkAction, TalkDiscoveryPolicy
            decision = TalkDiscoveryPolicy().decide(
                TalkAction.RESPOND_DRAFT,
                collab_enabled=True,
                untrusted_instruction=True,
                owner_approval_id=None,
            )
            if not decision.allowed:
                return {
                    "schema": "owner-console.reply.v1",
                    "kind": "blocked",
                    "text": f"🔐 PolicyGate: {decision.reason}",
                    "keyboard": [],
                    "data": {"status": "POLICY_BLOCKED", "reason": decision.reason},
                    "external_effect": False,
                    "estimated_cost": 0,
                    "send_attempted": False,
                    "authorization": None,
                }
        except Exception:
            pass

    base_reply = conversation.handle(text)

    if _use_model():
        enhanced = _model_enhance(base_reply, text)
    else:
        enhanced = _stub_enhance(base_reply, text)

    turn_id = _turn_id(text)
    # Content-free digest only (sha256) — not semantic episodic write.
    mem_result = collab_memory.append(
        turn_id=turn_id,
        role="owner",
        intent=enhanced.get("kind", "unknown"),
        summary=(f"owner_input_sha256={hashlib.sha256(str(text).encode('utf-8')).hexdigest()};"
                 f"reply_kind={enhanced.get('kind', '?')}"),
        state_dir=state_dir,
    )
    if mem_result.get("ok"):
        data = dict(enhanced.get("data") or {})
        data["memory_turn_id"] = turn_id
        data["memory_kind"] = "content_free_digest"
        enhanced["data"] = data

    enhanced["external_effect"] = False
    if "estimated_cost" not in enhanced:
        enhanced["estimated_cost"] = 0
    enhanced["send_attempted"] = False
    data = dict(enhanced.get("data") or {})
    data["policy_version"] = auth_meta.get("policy_version") or "ADR-033-v1"
    data["response_mode"] = "draft"
    data["evidence_plane"] = "ADR-033"
    if auth_meta:
        data["authorization_truth"] = auth_meta
    enhanced["data"] = data
    return enhanced


def callback(data: str, *, state_dir: Path | None = None) -> dict:
    """Handle callback data (button presses) through collaborator."""
    if not _is_enabled():
        return {
            "schema": "owner-console.reply.v1",
            "kind": "disabled",
            "text": "🚫 Collaborator غیرفعال است.",
            "data": {"status": "DISABLED"},
            "external_effect": False, "estimated_cost": 0,
            "send_attempted": False, "authorization": None,
        }
    base_reply = conversation.callback(data)
    enhanced = _stub_enhance(base_reply, data)
    enhanced["external_effect"] = False
    enhanced["estimated_cost"] = 0
    enhanced["send_attempted"] = False
    return enhanced
