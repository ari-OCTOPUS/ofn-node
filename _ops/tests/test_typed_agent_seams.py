#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""W9 — typed agent seams: critic ≠ builder, required fields, no shared lease."""
from pathlib import Path
import sys

_OPS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_OPS))
sys.path.insert(0, str(_OPS / "runtime"))

from typed_agent import AgentContract, separate_contexts  # noqa: E402


def _c(role, tools, lease="lease-a", aid=None):
    return AgentContract(
        agent_id=aid or f"{role}-1",
        role=role,
        capabilities=frozenset({"read"}),
        allowed_tools=frozenset(tools),
        allowed_paths=frozenset({"_ops/tests/"}),
        forbidden_paths=frozenset({".git", "_ops/telegram_center/center.py"}),
        budget={"usd": 0.0, "seconds": 30},
        lease=lease,
        expected_artifact="receipt.json",
        acceptance_tests=("test_typed_agent_seams.py",),
        failure_state="held",
    )


def test_builder_critic_separate_leases():
    b = _c("builder", ["apply_patch"], lease="L-build", aid="builder-1")
    k = _c("critic", ["review"], lease="L-crit", aid="critic-1")
    separate_contexts(b, k)


def test_shared_lease_rejected():
    b = _c("builder", ["apply_patch"], lease="SAME", aid="builder-1")
    k = _c("critic", ["review"], lease="SAME", aid="critic-1")
    try:
        separate_contexts(b, k)
        raise AssertionError("shared lease must fail")
    except ValueError:
        pass


def test_critic_cannot_apply_patch():
    try:
        _c("critic", ["apply_patch"], aid="critic-bad")
        raise AssertionError("critic+apply_patch must fail")
    except ValueError:
        pass


def test_only_release_guardian_prepares_promotion():
    AgentContract(
        agent_id="rg-1", role="release_guardian",
        capabilities=frozenset({"promote_prep"}),
        allowed_tools=frozenset({"promote_release"}),
        allowed_paths=frozenset({"_ops/state/debug/"}),
        forbidden_paths=frozenset({".git"}),
        budget={"usd": 0.0, "seconds": 10},
        lease="L-rg", expected_artifact="promotion-packet.json",
        acceptance_tests=(), failure_state="held",
    )
    try:
        _c("builder", ["promote_release"], aid="builder-bad")
        raise AssertionError("builder must not promote")
    except ValueError:
        pass
