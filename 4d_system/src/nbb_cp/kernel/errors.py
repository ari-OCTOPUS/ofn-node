"""Kernel error taxonomy. Every error names the invariant it protects, when one applies."""

from __future__ import annotations


class KernelError(Exception):
    """Base class for all kernel-raised errors."""

    invariant: str | None = None


class CapExceededError(KernelError):
    """Reserving this amount would push committed spend past the global cap."""

    invariant = "INV-1"


class HumanVerdictRequiredError(KernelError):
    """An irreversible or spawn action was attempted without an approved human verdict."""

    invariant = "INV-2"


class KilledError(KernelError):
    """The kill switch is engaged; all gates deny."""

    invariant = "INV-3"


class LedgerIntegrityError(KernelError):
    """The hash chain is broken or an append would rewrite history."""

    invariant = "INV-5"


class SpawnViolationError(KernelError):
    """Spawn request violates depth<=1 / propose-only / sigma<=1 discipline."""

    invariant = "INV-6"


class IllegalTransitionError(KernelError):
    """Lifecycle transition skipped a ladder rung or left an absorbing state."""

    invariant = "INV-10"


class FailClosedError(KernelError):
    """Input failed validation; the kernel denies rather than guesses."""

    invariant = "INV-12"


class ConcurrencyConflictError(KernelError):
    """Optimistic version token was stale; caller must re-read and retry."""

    invariant = None
