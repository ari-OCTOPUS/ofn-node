"""Independent pin — kernel-pure overall verdict for a set of approvals.

Per-event names come from ``approval_class``. This module is the
second witness for the *set*: which verdicts may satisfy, and
which must not.

Closed overall vocabulary (three names):

  satisfied     → independent count >= required (required >= 1)
  unsatisfied   → complete set of named non-independent verdicts
                  and count still below required
  unknown       → else any unknown, or we cannot tell. Never FALSE.

Unknown events do not count as independent and do not count as
unsatisfied. Missing the list is UNKNOWN, not empty. ``required``
of ``None`` is UNKNOWN, not 1. ``required < 1`` fails closed —
lowering required-approvals does not satisfy this pin.

A sealed send/ready name is never a verdict. ``campaign_envelope_ready``
is structurally distinct from ``send_authorized``; both are refused.

HALT stops STARTS. This pin has no halt parameter: an in-flight
pin must still be classifiable so recovery does not need the owner.

Not wired into the run store, the review-gate workflow, or any
adapter. Pinning is not ``send_authorized``, ``quote_sent``, or
``campaign_envelope_ready``. Ready is not authorized.

Kernel purity: dataclasses + typing. No json, no clock, no I/O.
This file must not name a business or product.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

from .approval_class import APPROVAL_VERDICTS
from .errors import FailClosedError
from .events import is_forbidden_effect_name

# Closed overall vocabulary. Widen only with a test.
PIN_VERDICTS = frozenset({
    "satisfied",
    "unsatisfied",
    "unknown",
})

_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
    "send-authorized",
    "quote-sent",
    "campaign-envelope-ready",
})


def grants_send() -> bool:
    """An independence pin never authorizes a send. Structurally False."""
    return False


def halt_blocks_pin() -> bool:
    """Structurally False. HALT stops STARTS, not this pin."""
    return False


def ready_is_authorized() -> bool:
    """Structurally False. Ready and authorized are different names."""
    return False


def claims_immutable() -> bool:
    """Structurally False. A pin is not chattr +i."""
    return False


def unknown_is_false() -> bool:
    """Structurally False. Unknown is not unsatisfied."""
    return False


def unknown_is_satisfied() -> bool:
    """Structurally False. Unknown is not a valid independent approval."""
    return False


def author_self_satisfies() -> bool:
    """Structurally False. The author cannot satisfy independence."""
    return False


def bot_satisfies() -> bool:
    """Structurally False. Bot/App approvals do not satisfy."""
    return False


def unlisted_satisfies() -> bool:
    """Structurally False. A human outside the valid set does not satisfy."""
    return False


def zero_required_satisfies() -> bool:
    """Structurally False. Lowering required-approvals does not satisfy."""
    return False


def proposal_is_execution() -> bool:
    """Structurally False. Naming a pin is not an external effect."""
    return False


def _is_sealed(name: object) -> bool:
    if not isinstance(name, str):
        return False
    if is_forbidden_effect_name(name):
        return True
    folded = name.strip().lower().replace("-", "_")
    return folded in {s.replace("-", "_") for s in _SEALED}


def _require_verdict(value: object) -> str:
    if isinstance(value, bool) or not isinstance(value, str) or not value.strip():
        raise FailClosedError(f"approval verdict must be a name: {value!r}")
    name = value.strip()
    if _is_sealed(name):
        raise FailClosedError(
            f"approval verdict names a sealed send/ready state: {name!r}")
    if name not in APPROVAL_VERDICTS:
        raise FailClosedError(
            f"unknown approval verdict is not a pin: {name!r}")
    return name


def _require_verdicts(verdicts: object) -> tuple[str, ...]:
    """A missing list is UNKNOWN, not an empty set of reviews.

    ``None`` fails closed. A string is not a list (iteration would
    walk characters). A bool is not a list.
    """
    if verdicts is None:
        raise FailClosedError(
            "verdicts is UNKNOWN, not empty — refusing pin")
    if isinstance(verdicts, (bool, str, bytes, bytearray)):
        raise FailClosedError(
            f"verdicts must be a sequence of names: {verdicts!r}")
    if not isinstance(verdicts, (Sequence, Iterable)):
        raise FailClosedError(
            f"verdicts must be a sequence of names: {verdicts!r}")
    out: list[str] = []
    for item in verdicts:
        out.append(_require_verdict(item))
    return tuple(out)


def _require_count(value: object) -> int:
    if value is None:
        raise FailClosedError(
            "required is UNKNOWN, not 1 — refusing pin")
    if isinstance(value, bool) or not isinstance(value, int):
        raise FailClosedError(f"required must be a positive int: {value!r}")
    if value < 1:
        raise FailClosedError(
            "required must be >= 1 — lowering required-approvals "
            "does not satisfy")
    return value


@dataclass(frozen=True)
class PinDecision:
    """One independence pin. ``grants_send`` is structurally False.

    Two independent claims live on the same object so a silent default
    cannot masquerade as an authorization: ``verdict`` and
    ``grants_send`` are both recorded, and the constructor refuses
    ``grants_send=True``.
    """

    verdict: str
    required: int
    independent_count: int
    unknown_count: int
    grants_send: bool = False

    def __post_init__(self) -> None:
        if self.grants_send:
            raise FailClosedError(
                "PinDecision cannot grant send_authorized / quote_sent / "
                "campaign_envelope_ready — a pin is not a send")
        if self.verdict not in PIN_VERDICTS:
            raise FailClosedError(f"unknown pin verdict: {self.verdict!r}")
        if _is_sealed(self.verdict):
            raise FailClosedError(
                "PinDecision cannot carry a sealed send/ready name")
        if (not isinstance(self.required, int)
                or isinstance(self.required, bool)
                or self.required < 1):
            raise FailClosedError(
                f"required must be a positive int: {self.required!r}")
        if (not isinstance(self.independent_count, int)
                or isinstance(self.independent_count, bool)
                or self.independent_count < 0):
            raise FailClosedError(
                f"independent_count must be a non-negative int: "
                f"{self.independent_count!r}")
        if (not isinstance(self.unknown_count, int)
                or isinstance(self.unknown_count, bool)
                or self.unknown_count < 0):
            raise FailClosedError(
                f"unknown_count must be a non-negative int: "
                f"{self.unknown_count!r}")
        if self.verdict == "satisfied" and self.independent_count < self.required:
            raise FailClosedError(
                "satisfied pin cannot have independent_count < required")
        if self.verdict == "unsatisfied" and self.unknown_count != 0:
            raise FailClosedError(
                "unsatisfied pin cannot include unknown events")
        if self.verdict == "unsatisfied" and self.independent_count >= self.required:
            raise FailClosedError(
                "unsatisfied pin cannot have independent_count >= required")


def pin_independent(
    *,
    verdicts: object,
    required: object,
) -> PinDecision:
    """Roll a sequence of approval verdicts into one overall name.

    ``verdicts`` and ``required`` are required. A missing list
    (``None``) is UNKNOWN, not empty. A missing ``required``
    (``None``) is UNKNOWN, not 1. A Python int >= 1 is the only
    admitted type for ``required``. ``0`` fails closed.

    Order of precedence is mechanical:

    1. independent_count >= required → ``satisfied``
    2. else any ``unknown`` → overall ``unknown``
    3. else ``unsatisfied``

    A sealed send/ready name fails closed. Signature is sealed: no
    ``resend``, no ``send_authorized``, no ``halt``. Tests lock the
    parameter list; the kernel does not import inspect.
    """
    names = _require_verdicts(verdicts)
    need = _require_count(required)

    independent_count = sum(1 for n in names if n == "independent")
    unknown_count = sum(1 for n in names if n == "unknown")

    if independent_count >= need:
        overall = "satisfied"
    elif unknown_count:
        overall = "unknown"
    else:
        overall = "unsatisfied"

    return PinDecision(
        verdict=overall,
        required=need,
        independent_count=independent_count,
        unknown_count=unknown_count,
    )
