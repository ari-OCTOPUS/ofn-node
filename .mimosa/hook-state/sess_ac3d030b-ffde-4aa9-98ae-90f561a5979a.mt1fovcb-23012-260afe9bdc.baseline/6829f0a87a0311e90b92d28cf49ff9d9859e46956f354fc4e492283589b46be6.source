"""
agents/base.py — Base agent class.

Every agent (Orchestrator, W0-W3) inherits from this. The contract:
    objective  — what the agent does
    inputs     — what it receives
    outputs    — what it must return
    boundary   — what it must NOT do

Agents never talk to each other directly. The Orchestrator dispatches them.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from llm.router import LLMRouter, get_router
from knowledge.ledger import build_system_prompt


@dataclass
class AgentResult:
    """Standard output format for every agent run."""
    agent_name: str
    role: str
    findings: dict = field(default_factory=dict)
    narrative: str = ""
    status: str = "ok"       # "ok", "warning", "fail"
    discrepancies: list = field(default_factory=list)

    def __repr__(self):
        return f"[{self.agent_name}] status={self.status} findings={list(self.findings.keys())}"


class BaseAgent(ABC):
    """
    Base class. Each subclass defines:
        name, role, task_type (for LLM routing)
        and implements run(inputs) -> AgentResult
    """
    name: str = "base"
    role: str = "general"
    task_type: str = "analysis"    # "verify", "geometry", etc.

    def __init__(self, router: LLMRouter | None = None):
        self.router = router or get_router()

    @property
    def system_prompt(self) -> str:
        return build_system_prompt(self.role)

    def llm(self, prompt: str, temperature: float = 0.7) -> str:
        """Call the LLM with this agent's system prompt prepended."""
        return self.router.ask(
            prompt,
            system=self.system_prompt,
            task=self.task_type,
            temperature=temperature,
        )

    @abstractmethod
    def run(self, inputs: dict) -> AgentResult:
        """Execute the agent's task. Must return an AgentResult."""
        ...

    def _make_result(self, findings: dict, narrative: str,
                     status: str = "ok", discrepancies: list = None) -> AgentResult:
        return AgentResult(
            agent_name=self.name,
            role=self.role,
            findings=findings,
            narrative=narrative,
            status=status,
            discrepancies=discrepancies or [],
        )
