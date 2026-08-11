#!/usr/bin/env python3
"""Offline deterministic fault injection for already-mocked provider seams.

This module opens no socket and implements no provider. It wraps a callable
supplied by a test, injects one scripted fault per invocation, and records only
bounded counters. Retry policy remains the responsibility of the real SUT.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable


class RateLimitFault(RuntimeError):
    status_code = 429


class CorruptProviderResponse(RuntimeError):
    pass


@dataclass(frozen=True)
class Fault:
    kind: str

    def apply(self) -> None:
        if self.kind == "pass":
            return
        if self.kind == "timeout":
            raise TimeoutError("injected provider timeout")
        if self.kind == "rate_limit":
            raise RateLimitFault("injected provider rate limit")
        if self.kind == "corrupt_json":
            raise CorruptProviderResponse("injected corrupt provider response")
        raise ValueError("unknown fault kind")


class ChaosProxy:
    """A finite script; exhaustion defaults to ``pass`` rather than looping."""

    def __init__(self, faults: Iterable[str | Fault] = ()):
        self._faults = [v if isinstance(v, Fault) else Fault(str(v)) for v in faults]
        self.attempt_count = 0
        self.delegate_count = 0

    def invoke(self, delegate: Callable[..., Any], *args, **kwargs) -> Any:
        self.attempt_count += 1
        idx = self.attempt_count - 1
        fault = self._faults[idx] if idx < len(self._faults) else Fault("pass")
        fault.apply()
        self.delegate_count += 1
        return delegate(*args, **kwargs)

    def snapshot(self) -> dict[str, int]:
        return {"attempt_count": self.attempt_count,
                "delegate_count": self.delegate_count,
                "script_length": len(self._faults)}
