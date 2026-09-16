#!/usr/bin/env python3
"""Typed outcome contract for one Telegram long-poll attempt."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

PollKind = Literal[
    "OK",
    "LEASE_DENIED",
    "CONFLICT",
    "RATE_LIMITED",
    "TIMEOUT",
    "DNS_ERROR",
    "HTTP_5XX",
    "HTTP_4XX",
    "MALFORMED",
    "STOPPED",
    "WEBHOOK_PRESENT",
]

_KINDS = {
    "OK", "LEASE_DENIED", "CONFLICT", "RATE_LIMITED", "TIMEOUT",
    "DNS_ERROR", "HTTP_5XX", "HTTP_4XX", "MALFORMED", "STOPPED",
    "WEBHOOK_PRESENT",
}
_RETRYABLE = {
    "LEASE_DENIED", "CONFLICT", "RATE_LIMITED", "TIMEOUT", "DNS_ERROR",
    "HTTP_5XX",
}


@dataclass(frozen=True)
class PollOutcome:
    kind: PollKind
    updates: tuple[dict, ...] = field(default_factory=tuple)
    retry_after_s: float | None = None
    error_code: int | None = None
    reason: str = ""
    lease_generation: int | None = None
    started_at: float | None = None
    completed_at: float | None = None

    def __post_init__(self) -> None:
        if self.kind not in _KINDS:
            raise ValueError(f"invalid poll outcome kind: {self.kind!r}")
        object.__setattr__(self, "updates", tuple(
            item for item in self.updates if isinstance(item, dict)))
        if self.kind != "OK" and self.updates:
            raise ValueError("non-OK poll outcomes cannot carry updates")
        if self.retry_after_s is not None:
            value = float(self.retry_after_s)
            if value <= 0:
                raise ValueError("retry_after_s must be positive")
            object.__setattr__(self, "retry_after_s", value)
        object.__setattr__(self, "reason", str(self.reason or "")[:120])

    @property
    def ok(self) -> bool:
        return self.kind == "OK"

    @property
    def retryable(self) -> bool:
        return self.kind in _RETRYABLE

    def legacy_updates(self) -> list[dict]:
        return list(self.updates) if self.ok else []
