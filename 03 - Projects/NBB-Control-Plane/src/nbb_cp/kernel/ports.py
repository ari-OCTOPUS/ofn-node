"""Ports: the only doorway between kernel decisions and the outside world.

Adapters implement these Protocols. The kernel never imports an adapter; the
app layer wires them together. Keep every port minimal — a fat port is lock-in
wearing a trench coat (the LangGraph adapter must fit behind LLMPort without
leaking graph types into the kernel).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping, Protocol, Sequence

from .domain import BudgetState
from .events import EventKind, LedgerEvent


@dataclass(frozen=True)
class LLMRequest:
    """Provider-neutral completion request. Untrusted context arrives pre-quarantined."""

    task: str                      # routing hint: "govern", "summarize", ...
    prompt: str
    params: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class LLMResponse:
    text: str
    input_tokens: int = 0
    output_tokens: int = 0
    orchestration_tokens: int = 0  # third bucket; never drop it


class LLMPort(Protocol):
    def complete(self, request: LLMRequest) -> LLMResponse: ...


class LedgerStore(Protocol):
    """Append-only event storage. Implementations must reject history rewrites."""

    def append(self, ts: str, kind: EventKind, payload: Mapping[str, object]) -> LedgerEvent: ...
    def read_all(self) -> Sequence[LedgerEvent]: ...
    def head(self) -> LedgerEvent | None: ...


class BudgetStore(Protocol):
    """Budget state with compare-and-swap semantics on BudgetState.version."""

    def get(self) -> BudgetState: ...
    def compare_and_swap(self, expected_version: int, new_state: BudgetState) -> None:
        """Atomically replace state iff stored version == expected_version.

        Raises ConcurrencyConflictError otherwise. This is the anti-double-spend
        primitive; implementations must make the check-and-write atomic (no
        read-then-write windows — the TOCTOU lesson).
        """
        ...


class Telemetry(Protocol):
    def emit(self, name: str, value: float, tags: Mapping[str, str] | None = None) -> None: ...


class Clock(Protocol):
    def now_iso(self) -> str: ...


class IdGen(Protocol):
    def new_id(self, prefix: str) -> str: ...


class KillSwitch(Protocol):
    def engaged(self) -> bool: ...
    def engage(self) -> None:
        """Halt the organism. In-band kill (record_kill) must flip the real switch,
        not just ledger an event — otherwise the API's only stop control halts nothing."""
        ...

    def release(self) -> None:
        """Reverse a kill. Extinction is absorbing; a kill switch is not."""
        ...


def events_of(store: LedgerStore, *kinds: EventKind) -> Iterable[LedgerEvent]:
    """Convenience filter used by app code; kept here so it stays kernel-pure."""
    wanted = set(kinds)
    return (e for e in store.read_all() if not wanted or e.kind in wanted)
