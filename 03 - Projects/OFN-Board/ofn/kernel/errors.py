"""Kernel errors. Every one of them means "deny", never "guess".

Fail-closed is the house rule (INV-12): unknown input, missing data, or a
violated precondition produces a denial and an incident — never a default.
"""

from __future__ import annotations


class KernelError(Exception):
    """Base for every kernel-raised failure."""


class FailClosedError(KernelError):
    """Input the kernel refuses to interpret. Deny and raise an incident."""


class TenantIsolationError(KernelError):
    """An attempt to read or write across a tenant boundary.

    This is never a recoverable condition — it means a caller tried to reach
    state that does not belong to it. Surfacing loudly is the point.
    """


class QuotaExceededError(KernelError):
    """Spending this would cross a ceiling. The node stops, not just the caller."""


class PackError(KernelError):
    """A business pack is malformed, incomplete, or claims capabilities the
    kernel does not implement."""


class UnknownTenantError(KernelError):
    """Routing could not resolve a tenant. Fail closed rather than pick one."""
