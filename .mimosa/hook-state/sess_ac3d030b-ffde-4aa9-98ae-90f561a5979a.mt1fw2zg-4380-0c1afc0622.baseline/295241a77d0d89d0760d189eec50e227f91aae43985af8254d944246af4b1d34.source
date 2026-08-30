#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""context_bundle — narrow, typed handoff/context packets for specialist agents.

Implements Reduce + Delegate + Offload + Isolate. The packet carries references
and compact evidence, never a conversation dump or chain-of-thought. Pure,
stdlib-only, and safe to use for MCP/A2A adapters later.
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass, field
from typing import Dict, List

SCHEMA = "octopus-context-bundle.v1"
_ALLOWED_PHASES = ("plan", "act", "verify", "commit")
_MAX_FACTS = 24
_MAX_REFS = 48
_MAX_TEXT = 1200


def _clean(s, cap=_MAX_TEXT) -> str:
    return " ".join(str(s or "").split())[:cap]


@dataclass(frozen=True)
class EvidenceRef:
    ref: str
    summary: str
    trust: str = "UNKNOWN"
    freshness_ts: float = 0.0


@dataclass(frozen=True)
class ContextBundle:
    bundle_id: str
    mission_id: str
    task_id: str
    trace_id: str
    tenant_id: str
    project_id: str
    agent_role: str
    phase: str
    objective: str
    constraints: List[str] = field(default_factory=list)
    verified_facts: List[str] = field(default_factory=list)
    evidence: List[EvidenceRef] = field(default_factory=list)
    tool_allowlist: List[str] = field(default_factory=list)
    memory_scopes: List[str] = field(default_factory=lambda: ["project", "verified_shared"])
    failure_modes: List[str] = field(default_factory=list)
    output_contract: Dict[str, str] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    expires_at: float = 0.0
    schema: str = SCHEMA

    @classmethod
    def create(cls, *, mission_id: str, task_id: str, trace_id: str,
               tenant_id: str, project_id: str, agent_role: str, phase: str,
               objective: str, constraints=None, verified_facts=None, evidence=None,
               tool_allowlist=None, memory_scopes=None, failure_modes=None,
               output_contract=None, ttl_s: int = 1800) -> "ContextBundle":
        now = time.time()
        seed = f"{mission_id}|{task_id}|{trace_id}|{agent_role}|{phase}|{now}"
        bid = "cb_" + hashlib.sha256(seed.encode()).hexdigest()[:16]
        return cls(bid, mission_id, task_id, trace_id, tenant_id, project_id,
                   agent_role, phase, _clean(objective),
                   [_clean(x, 400) for x in list(constraints or [])[:_MAX_FACTS]],
                   [_clean(x, 400) for x in list(verified_facts or [])[:_MAX_FACTS]],
                   list(evidence or [])[:_MAX_REFS],
                   [_clean(x, 100) for x in list(tool_allowlist or [])[:_MAX_REFS]],
                   [_clean(x, 40) for x in list(memory_scopes or ["project", "verified_shared"])],
                   [_clean(x, 300) for x in list(failure_modes or [])[:_MAX_FACTS]],
                   dict(output_contract or {}), now, now + max(1, int(ttl_s)))

    def validate(self, now=None) -> List[str]:
        e: List[str] = []
        for k in ("bundle_id", "mission_id", "task_id", "trace_id", "tenant_id",
                  "project_id", "agent_role", "objective"):
            if not str(getattr(self, k, "") or "").strip():
                e.append(f"{k} required")
        if self.phase not in _ALLOWED_PHASES:
            e.append("invalid phase")
        if self.expires_at <= (time.time() if now is None else now):
            e.append("bundle expired")
        if len(self.verified_facts) > _MAX_FACTS or len(self.evidence) > _MAX_REFS:
            e.append("bundle exceeds evidence limits")
        if "personal_core" in self.memory_scopes and self.agent_role not in ("owner_interface", "core"):
            e.append("agent role cannot access personal_core")
        return e

    def compact_json(self) -> str:
        """Machine handoff. No private scratchpad/reasoning field exists by construction."""
        return json.dumps(asdict(self), ensure_ascii=False, sort_keys=True,
                          separators=(",", ":"), default=str)
