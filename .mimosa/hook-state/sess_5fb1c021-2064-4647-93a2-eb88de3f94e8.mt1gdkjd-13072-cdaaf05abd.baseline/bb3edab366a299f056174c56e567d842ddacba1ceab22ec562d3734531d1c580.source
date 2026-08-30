"""In-memory stores — reference implementations of the storage ports.

Semantics here are the contract sqlite/Postgres must match: append-only
ledger, atomic compare-and-swap on budget version. A lock guards the CAS so
threaded tests exercise real races.
"""

from __future__ import annotations

import threading
from typing import Mapping, Sequence

from ...kernel.domain import BudgetState
from ...kernel.errors import ConcurrencyConflictError
from ...kernel.events import EventKind, LedgerEvent, next_event


class MemoryLedgerStore:
    def __init__(self) -> None:
        self._events: list[LedgerEvent] = []
        self._lock = threading.Lock()

    def append(self, ts: str, kind: EventKind, payload: Mapping[str, object]) -> LedgerEvent:
        with self._lock:
            prev = self._events[-1] if self._events else None
            event = next_event(prev, ts, kind, dict(payload))
            self._events.append(event)
            return event

    def read_all(self) -> Sequence[LedgerEvent]:
        with self._lock:
            return tuple(self._events)

    def head(self) -> LedgerEvent | None:
        with self._lock:
            return self._events[-1] if self._events else None


class MemoryBudgetStore:
    def __init__(self, initial: BudgetState) -> None:
        self._state = initial
        self._lock = threading.Lock()

    def get(self) -> BudgetState:
        with self._lock:
            return self._state

    def compare_and_swap(self, expected_version: int, new_state: BudgetState) -> None:
        with self._lock:
            if self._state.version != expected_version:
                raise ConcurrencyConflictError(
                    f"stale version {expected_version}, store at {self._state.version}"
                )
            self._state = new_state
