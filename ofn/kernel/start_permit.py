"""Start permit — the pre-mint HALT decision (kernel-pure).

HALT stops STARTS. ``adapters.run_gate`` reads a file and then asks the
store to create; this module is the vocabulary for that decision
*before* a run_id is minted and *before* any ledger write.

Complementary to, and not a replacement for:

  * ``kernel.halt``            — parse the flag text
  * ``adapters.halt_flag``     — read the file
  * ``adapters.run_gate``      — I/O wrapper (owned by an open change)
  * ``kernel.rejection``       — RUN_REJECTED side log after a mint
                                 (owned by PR #93)

A refused start is named ``RUN_REJECTED``. This module does not write
that name into a ledger — writing is adapter work. It also does not
take a run_id: deciding whether a start may happen must not require
an identity that only a successful start should mint.

Not wired into the run store (that file is owned by an open change).

A permit never grants ``send_authorized``, ``quote_sent``, or
``campaign_envelope_ready``. Clearing HALT is a resume of starts, not
a send grant.

Kernel purity: typing + dataclasses. No json, no clock, no I/O.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .errors import FailClosedError
from .events import (
    EVENT_KINDS,
    RUN_CREATED,
    RUN_REJECTED,
    is_forbidden_effect_name,
)
from .halt import is_halted

# Closed refusal vocabulary for a pre-mint decision. Widen only with a test.
REFUSAL_REASONS = frozenset({"halt_active", "sealed_effect"})

# "sent" / "authorized" / "ready" are not start kinds or tools.
_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
})


def grants_send() -> bool:
    """A start permit never authorizes a send. Structurally False."""
    return False


def halt_blocks_in_flight() -> bool:
    """Structurally False. HALT stops STARTS, not in-flight work."""
    return False


def burns_idempotency_key() -> bool:
    """Structurally False. A refused start does not burn the key."""
    return False


def _is_sealed(name: object) -> bool:
    if not isinstance(name, str):
        return False
    if is_forbidden_effect_name(name):
        return True
    folded = name.strip().lower().replace("-", "_")
    return folded in _SEALED


@dataclass(frozen=True)
class StartDecision:
    """The pre-mint verdict. ``grants_send`` is structurally False.

    Two independent claims live on the same object so a silent default
    cannot masquerade as an authorization: ``allowed`` and
    ``grants_send`` are both recorded, and the constructor refuses
    ``grants_send=True``.
    """

    allowed: bool
    reason: Optional[str]
    grants_send: bool = False

    def __post_init__(self) -> None:
        if self.grants_send:
            raise FailClosedError(
                "StartDecision cannot grant send_authorized / quote_sent / "
                "campaign_envelope_ready — a start permit is not a send")
        if self.allowed:
            if self.reason is not None:
                raise FailClosedError(
                    f"allowed start must not carry a reason: {self.reason!r}")
        else:
            if self.reason not in REFUSAL_REASONS:
                raise FailClosedError(
                    f"unknown or missing refusal reason: {self.reason!r}")

    @property
    def refusal_kind(self) -> Optional[str]:
        """RUN_REJECTED when refused; None when allowed.

        Naming the kind is not writing it. The adapter that records a
        refusal is a later, separate claim.
        """
        return None if self.allowed else RUN_REJECTED


def decide_start(
    *,
    halt_raw: Optional[str],
    proposed_kind: Optional[str] = None,
    proposed_tool: Optional[str] = None,
) -> StartDecision:
    """May a run start under this halt text and these proposed names?

    ``halt_raw`` is the flag file contents (or None if absent). The
    kernel does not read the file. Absence is RUNNING; corrupt/empty
    is HALTED — delegated to ``halt.is_halted``.

    ``proposed_kind`` / ``proposed_tool`` are optional. When supplied,
    a sealed send/ready name refuses the start (reason ``sealed_effect``)
    even if the halt switch is off. An unknown kind fails closed — it
    is not treated as FALSE and it is not treated as a start.

    Signature is sealed: no ``resend``, no ``send_authorized``.
    Tests lock the parameter list; the kernel does not import inspect.
    """
    if is_halted(halt_raw):
        return StartDecision(allowed=False, reason="halt_active")

    if proposed_kind is not None:
        if not isinstance(proposed_kind, str) or not proposed_kind.strip():
            raise FailClosedError(
                f"proposed_kind must be a non-empty name: {proposed_kind!r}")
        if _is_sealed(proposed_kind):
            return StartDecision(allowed=False, reason="sealed_effect")
        if proposed_kind == RUN_REJECTED:
            raise FailClosedError(
                "RUN_REJECTED is a refusal witness, not a start kind")
        if proposed_kind not in EVENT_KINDS:
            raise FailClosedError(
                f"unknown event kind is not a start: {proposed_kind!r}")
        if proposed_kind != RUN_CREATED:
            raise FailClosedError(
                f"a start proposes RUN_CREATED, not {proposed_kind!r}")

    if proposed_tool is not None:
        if not isinstance(proposed_tool, str) or not proposed_tool.strip():
            raise FailClosedError(
                f"proposed_tool must be a non-empty name: {proposed_tool!r}")
        if _is_sealed(proposed_tool):
            return StartDecision(allowed=False, reason="sealed_effect")

    return StartDecision(allowed=True, reason=None)
