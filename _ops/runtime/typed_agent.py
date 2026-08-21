#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Typed agent seams — no free-form chatting agents.

Builder and Critic are separate execution contexts. Release Guardian is the
only role allowed to *prepare* promotion; promotion itself stays owner-gated.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, FrozenSet

ROLES = (
    "observer",
    "memory_curator",
    "goal_manager",
    "planner",
    "specialist_worker",
    "critic",
    "architect",
    "release_guardian",
    "builder",
)


@dataclass(frozen=True)
class AgentContract:
    agent_id: str
    role: str
    capabilities: FrozenSet[str]
    allowed_tools: FrozenSet[str]
    allowed_paths: FrozenSet[str]
    forbidden_paths: FrozenSet[str]
    budget: dict[str, Any]
    lease: str
    expected_artifact: str
    acceptance_tests: tuple[str, ...]
    failure_state: str

    def __post_init__(self) -> None:
        if self.role not in ROLES:
            raise ValueError(f"unknown role: {self.role}")
        if not self.agent_id or not self.lease:
            raise ValueError("agent_id and lease required")
        if self.role == "critic" and "apply_patch" in self.allowed_tools:
            raise ValueError("critic must not hold apply_patch")
        if self.role == "builder" and "promote_release" in self.allowed_tools:
            raise ValueError("builder must not promote")
        if self.role != "release_guardian" and "promote_release" in self.allowed_tools:
            raise ValueError("only release_guardian may prepare promotion")


@dataclass
class AgentTask:
    contract: AgentContract
    input_snapshot: dict[str, Any]
    memory_context_id: str = ""
    artifact: dict[str, Any] = field(default_factory=dict)


def separate_contexts(builder: AgentContract, critic: AgentContract) -> None:
    if builder.lease == critic.lease:
        raise ValueError("builder and critic cannot share a lease")
    if builder.agent_id == critic.agent_id:
        raise ValueError("builder and critic cannot share agent_id")
    overlap = builder.allowed_tools & critic.allowed_tools
    if "apply_patch" in overlap:
        raise ValueError("apply_patch cannot be shared")
