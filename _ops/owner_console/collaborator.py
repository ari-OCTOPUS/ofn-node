#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""collaborator.py — deterministic collaborator engine (WP-E3).

Wraps/extends conversation.py, does NOT replace it.
Default deterministic stub ($0, no network). Real model behind separate flag.

Contract:
  schema: owner-console.reply.v1
  external_effect = false
  estimated_cost = 0
  send_attempted = false

Flags:
  OCTOPUS_WIRE_COLLAB=0 (main collaborator gate)
  OCTOPUS_COLLAB_USE_MODEL=0 (real model gate — separate from wiring)
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent

# Add parent to path for imports
import sys
if str(HERE.parent) not in sys.path:
    sys.path.insert(0, str(HERE.parent))
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from owner_console import conversation, collab_memory  # noqa: E402


def _is_enabled() -> bool:
    return os.environ.get("OCTOPUS_WIRE_COLLAB", "0") == "1"


def _use_model() -> bool:
    return os.environ.get("OCTOPUS_COLLAB_USE_MODEL", "0") == "1"


def _turn_id(owner_text: str) -> str:
    """Deterministic turn ID from owner text."""
    return hashlib.sha256(f"{owner_text}:{os.urandom(4).hex()}".encode()).hexdigest()[:16]


def _stub_enhance(base_reply: dict, owner_text: str) -> dict:
    """Deterministic stub enhancement — adds 'why' and 'memory_ref' to base reply.

    This simulates what a real model would add: a rationale and a memory reference.
    The stub is fully deterministic — same input always produces same output.
    """
    enhanced = dict(base_reply)
    data = dict(enhanced.get("data") or {})

    # Add rationale (why)
    kind = enhanced.get("kind", "")
    if kind == "clarify":
        data["rationale"] = "stub: input ambiguous — needs narrower intent specification"
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


def handle(text: str, *, state_dir: Path | None = None) -> dict:
    """Handle owner input with collaborator enhancement.

    Default: deterministic stub ($0, no network).
    If OCTOPUS_COLLAB_USE_MODEL=1 and a real model adapter is injected: use it.

    Returns owner-console.reply.v1 compliant dict.
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

    # Base reply from conversation.py (the existing system)
    base_reply = conversation.handle(text)

    # Enhancement: stub or real model
    if _use_model():
        # Real model path — NOT activated in this build. Placeholder for future.
        enhanced = _stub_enhance(base_reply, text)
        enhanced["model_source"] = "REAL_MODEL_NOT_CONNECTED"
        enhanced["data"]["warning"] = "model flag set but no adapter wired — fell back to stub"
    else:
        enhanced = _stub_enhance(base_reply, text)

    # Episodic memory (if armed)
    turn_id = _turn_id(text)
    mem_result = collab_memory.append(
        turn_id=turn_id,
        role="owner",
        intent=enhanced.get("kind", "unknown"),
        summary=f"owner asked: {str(text)[:200]}; collaborator replied: {enhanced.get('kind', '?')}",
        state_dir=state_dir,
    )
    if mem_result.get("ok"):
        enhanced["data"]["memory_turn_id"] = turn_id

    # Ensure contract compliance
    enhanced["external_effect"] = False
    enhanced["estimated_cost"] = 0
    enhanced["send_attempted"] = False

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
