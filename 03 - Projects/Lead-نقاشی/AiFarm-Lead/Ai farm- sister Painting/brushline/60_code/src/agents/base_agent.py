"""
BaseAgent — the formal contract every Worker A-F must speak.

Closes E25 (revised synthesis, 2026-07-12): the six agents were ad-hoc classes
with no shared base, no enforced interface, no declared authority boundary.
This meant:
  - the orchestrator could break at runtime (not import-time) if a method
    signature drifted;
  - there was no single place that said what each agent MAY and MAY NOT do;
  - the OLP-1 "Role Card" concept lived only in prose, not in code.

Design (additive, non-breaking):
  - BaseAgent is an ABC with @abstractmethod declarations for the COMMON
    surface every agent shares (identity, authority, capability, health).
  - Each agent's domain-specific methods (search_suburb, draft_speed_to_lead,
    sync_to_servicem8, ...) stay on the concrete class untouched — we do NOT
    force a uniform run() signature, because the six agents do very different
    things and a fake-uniform interface would be worse than none.
  - Migration is opt-in: an agent inherits BaseAgent and implements the few
    abstract methods; until then it still works as before (duck typing).

The contract mirrors OLP-1 §5 (Role Card) in executable form:

    Role Card field        →  BaseAgent property
    ──────────────────────────────────────────────
    role_id                →  AGENT_ID
    role_name              →  role_name
    qualification_status   →  qualification_status
    authority.allowed      →  ALLOWED_ACTIONS
    authority.forbidden    →  FORBIDDEN_ACTIONS
    inputs.required        →  required_inputs
    outputs.artifact_types →  produces
    risk.default_level     →  risk_level
    metrics                →  metrics

Governance invariant: every BaseAgent declares FORBIDDEN_ACTIONS at the class
level. This is the executable form of the OLP-1 hard-gate list — a place a
human or evaluator can grep to answer "can Worker C publish on its own?"
without reading 700 lines of content.py.

Status: NEW 2026-07-12. All names provisional, owner veto retained.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import ClassVar


# ── Enums mirroring OLP-1 ───────────────────────────────────────────────────

class RiskLevel(str, Enum):
    """OLP-1 risk ladder, per-role default."""
    GREEN = "green"    # read / classify / analyse / draft / offline test
    YELLOW = "yellow"  # low-risk proposal / experiment draft / prompt candidate
    ORANGE = "orange"  # contract change / API connection / prompt activation
    RED = "red"        # external action / money / customer commitment / deploy


class QualificationStatus(str, Enum):
    """OLP-1 §14 qualification ladder."""
    TRAINEE = "trainee"                       # <70% on suite
    SHADOW_QUALIFIED = "shadow_qualified"     # 70-89%
    PROPOSAL_QUALIFIED = "proposal_qualified" # >=90%, safety passed
    PRODUCTION_QUALIFIED = "production_qualified"  # + owner-approved + outcomes
    SUSPENDED = "suspended"                   # any critical safety failure


# ── Capability descriptor (what the agent can do, in code) ─────────────────

@dataclass(frozen=True)
class AgentCapability:
    """One capability an agent offers. OLP-1 outputs.artifact_types, executable."""
    name: str                 # e.g. "draft_speed_to_lead"
    artifact_type: str        # e.g. "Draft", "ResearchResult", "SyncJob"
    external_action: bool = False  # does this touch the outside world?
    pii_handling: str = "none"     # "none" | "local-only" | "external-whitelisted"


@dataclass(frozen=True)
class AgentContract:
    """
    The full declared contract of one agent.
    Materialised by BaseAgent.declare() and used by:
      - the orchestrator (to route safely),
      - the evaluator (qualification suite),
      - the audit log (to record which authority boundary an action sat in),
      - a future /agents_status Telegram command.
    """
    agent_id: str
    role_name: str
    risk_level: RiskLevel
    qualification_status: QualificationStatus
    allowed_actions: frozenset[str]
    forbidden_actions: frozenset[str]
    required_inputs: frozenset[str]
    produces: tuple[AgentCapability, ...]
    parent_system: str = "BRUSHLINE"
    may_execute_external: bool = False
    metrics: tuple[str, ...] = (
        "factual_accuracy", "evidence_coverage", "constraint_compliance",
        "usefulness", "owner_correction_rate", "cost", "latency",
    )


# ── The base contract every Worker A-F must implement ───────────────────────

class BaseAgent(ABC):
    """
    Formal contract for all Brushline workers.

    Concrete agents (Researcher, AudienceAgent, ContentAgent, AssetAgent,
    ChannelAgent, LeadCaptureAgent) inherit this and implement:
      - role_name, qualification_status (class attrs/properties)
      - risk_level, required_inputs, capabilities (class attrs/properties)
      - declare() → AgentContract
      - health() → dict

    The ALLOWED_ACTIONS / FORBIDDEN_ACTIONS / AGENT_ID ClassVars let each
    agent state its authority boundary in ONE place, grep-able by humans and
    machines. This is the executable Role Card.
    """

    # ── identity (must override) ────────────────────────────────────────────
    AGENT_ID: ClassVar[str] = "base"  # each subclass overrides

    # ── authority boundary (OLP-1 hard-gate list, per-role) ─────────────────
    # These are the DEFAULT most-restrictive set; agents widen ALLOWED only
    # for actions they genuinely perform.
    ALLOWED_ACTIONS: ClassVar[frozenset[str]] = frozenset({
        "read", "analyse", "draft", "propose", "create_memory_candidate",
    })
    FORBIDDEN_ACTIONS: ClassVar[frozenset[str]] = frozenset({
        "publish", "send", "spend", "pay", "alter_policy", "alter_permissions",
        "write_canonical_memory", "expose_pii", "access_secrets",
    })

    # ── abstract surface ────────────────────────────────────────────────────
    @property
    @abstractmethod
    def role_name(self) -> str:
        """Human-readable role, e.g. 'Worker A — Researcher'."""
        ...

    @property
    @abstractmethod
    def qualification_status(self) -> QualificationStatus:
        """Current OLP-1 §14 qualification status (starts TRAINEE)."""
        ...

    @property
    @abstractmethod
    def risk_level(self) -> RiskLevel:
        """Default risk level for this role's work."""
        ...

    @property
    @abstractmethod
    def required_inputs(self) -> frozenset[str]:
        """Artifact types this agent needs to function (e.g. {'lead', 'research'}).
        Used by the orchestrator to verify inputs exist before dispatch."""
        ...

    @property
    @abstractmethod
    def capabilities(self) -> tuple[AgentCapability, ...]:
        """What this agent can produce. Drives routing + the /agents_status view."""
        ...

    # ── materialise the full contract ───────────────────────────────────────
    def declare(self) -> AgentContract:
        """
        Build the full AgentContract from this instance's declared attrs.
        Called by the orchestrator on boot and by the evaluator on demand.
        """
        caps = self.capabilities
        return AgentContract(
            agent_id=self.AGENT_ID,
            role_name=self.role_name,
            risk_level=self.risk_level,
            qualification_status=self.qualification_status,
            allowed_actions=self.ALLOWED_ACTIONS,
            forbidden_actions=self.FORBIDDEN_ACTIONS,
            required_inputs=self.required_inputs,
            produces=caps,
            may_execute_external=any(c.external_action for c in caps),
        )

    # ── runtime health probe ────────────────────────────────────────────────
    @abstractmethod
    def health(self) -> dict:
        """
        Lightweight self-check: is this agent ready to do its job?
        Returns {ready: bool, detail: str}. Must NOT raise, must NOT spend.
        The orchestrator calls this before dispatching a task.
        """
        ...

    # ── authority enforcement helper ────────────────────────────────────────
    def assert_may(self, action: str) -> None:
        """
        Raise PermissionError if `action` is forbidden for this agent.
        This is the executable OLP-1 hard-gate. Agents call it at the top of
        any method that touches a sensitive verb.

        Example (in ChannelAgent.publish):
            self.assert_may("publish")  # raises unless ALLOWED_ACTIONS widened
        """
        if action in self.FORBIDDEN_ACTIONS:
            raise PermissionError(
                f"{self.AGENT_ID}: action {action!r} is forbidden by contract "
                f"(FORBIDDEN_ACTIONS). OLP-1 hard-gate violation."
            )
        # action not in allowed either → warn but allow (migration grace period)
        if action not in self.ALLOWED_ACTIONS:
            # soft-warn: the action isn't explicitly allowed, but it's a
            # concrete agent method so we trust the orchestrator routed here.
            # During migration this keeps things working; the evaluator can
            # flag undeclared actions.
            import logging
            logging.getLogger(__name__).warning(
                "%s: action %r is neither allowed nor forbidden (undeclared). "
                "Consider adding it to ALLOWED_ACTIONS.", self.AGENT_ID, action
            )


# ── Registry: a single source of truth for "which agents exist" ─────────────

_AGENT_REGISTRY: dict[str, type[BaseAgent]] = {}


def register_agent(cls: type[BaseAgent]) -> type[BaseAgent]:
    """
    Class decorator: register a BaseAgent subclass in the global registry.
    Lets the orchestrator / /agents_status enumerate agents without imports.
    Usage:
        @register_agent
        class Researcher(BaseAgent): ...
    """
    _AGENT_REGISTRY[cls.AGENT_ID] = cls
    return cls


def all_agents() -> dict[str, type[BaseAgent]]:
    """Return {agent_id: class} for every registered BaseAgent."""
    return dict(_AGENT_REGISTRY)


def contracts() -> list[AgentContract]:
    """Materialise contracts for all registered agents (instantiates each)."""
    out = []
    for cls in _AGENT_REGISTRY.values():
        try:
            out.append(cls().declare())
        except Exception:
            # agent failed to instantiate (e.g. missing API key) — skip, don't crash
            import logging
            logging.getLogger(__name__).exception(
                "agent %s failed to declare contract", cls.AGENT_ID
            )
    return out
