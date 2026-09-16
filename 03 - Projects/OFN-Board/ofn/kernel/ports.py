"""Ports: the only doorway between kernel decisions and the world.

Adapters implement these Protocols; the kernel never imports an adapter. Keep
each port narrow — a wide port is vendor lock-in with extra steps.

Deliberately mirrors the shape of the existing control-plane's ports so an
adapter written for one can be reused for the other, in particular
`ModelResponse.orchestration_tokens`, which exists for the same reason there:
the third bucket is real spend and dropping it corrupts every budget decision
downstream.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Protocol, Sequence

from .domain import RiskTier, TenantId


@dataclass(frozen=True)
class ModelRequest:
    """Provider-neutral request. Untrusted context arrives already quarantined."""

    task: str                       # routing hint: "classify", "draft", "plan"
    prompt: str
    tenant: TenantId | None = None
    max_tier: RiskTier = RiskTier.GREEN
    params: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ModelResponse:
    text: str
    visible_tokens: int = 0
    orchestration_tokens: int = 0   # third bucket; never drop it
    model: str = ""


class ModelPort(Protocol):
    """One call, one answer. Routing between rules/local/remote lives above."""

    def complete(self, request: ModelRequest) -> ModelResponse: ...


class LedgerPort(Protocol):
    """Append-only, hash-chained. Implementations must refuse history rewrites."""

    def append(self, tenant: TenantId, kind: str,
               payload: Mapping[str, object]) -> str: ...
    def read(self, tenant: TenantId, limit: int = 100) -> Sequence[Mapping[str, object]]: ...
    def verify_chain(self, tenant: TenantId) -> bool: ...


class StatePort(Protocol):
    """Key-value state. Every key must have been minted by a TenantScope —
    implementations call `scope.assert_owns(key)` before returning a value."""

    def get(self, key: str) -> bytes | None: ...
    def put(self, key: str, value: bytes) -> None: ...
    def keys(self, prefix: str) -> Sequence[str]: ...


class OutboxPort(Protocol):
    """Durable, idempotent queue for anything leaving the node.

    Nothing reaches the world except through here, and nothing leaves here
    without an approved decision. That is the structural reason a leg cannot
    exfiltrate on its own: it has no other exit.
    """

    def enqueue(self, tenant: TenantId, idempotency_key: str,
                payload: Mapping[str, object]) -> None: ...
    def pending(self, tenant: TenantId) -> Sequence[Mapping[str, object]]: ...
    def mark_sent(self, idempotency_key: str) -> None: ...


class KillSwitchPort(Protocol):
    def engaged(self) -> bool: ...
    def engage(self, reason: str) -> None: ...
    def release(self) -> None: ...


class ClockPort(Protocol):
    """The kernel takes time as a parameter; only adapters read a clock."""

    def epoch_seconds(self) -> int: ...
    def iso(self) -> str: ...
