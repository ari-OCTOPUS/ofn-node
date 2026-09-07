"""Epoch class — kernel-pure classifier for a RunStore window.

The run store is append-only. This module is the second witness: is
this *named window* open (accepting appends), already cut, or a
rewrite/truncate dressed as a window?

``open`` is the only admitted state. ``cut``, ``rewrite``, and
``truncate`` are known refusals — they are not classified as FALSE
and they are not admitted. A missing or unknown state is UNKNOWN,
not open.

An epoch identity is not a run_id. The prefixes are different so a
silent default cannot mint a window that collides with a run. A
sealed send/ready name is never an epoch and never a state.
``campaign_envelope_ready`` is structurally distinct from
``send_authorized``; both are refused.

HALT stops STARTS. This classifier has no halt parameter: an
in-flight open window must still be classifiable so recovery does
not need the owner.

Not wired into the run store (that file is owned by another open
change).

Admitting an open epoch is not ``send_authorized``, ``quote_sent``,
or ``campaign_envelope_ready``. Ready is not authorized.

Kernel purity: typing + dataclasses + re. No json, no clock, no I/O.
This file must not name a business or product.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional, Pattern

from .envelope import RUN_ID_RE
from .errors import FailClosedError
from .events import is_forbidden_effect_name

# Closed state vocabulary. Widen only with a test.
STATES = frozenset({"open"})

# Known refused states. These are a refusal, not an unknown.
REFUSED_STATES = frozenset({"cut", "rewrite", "truncate"})

# Known refusals. Unknown names fail closed — they are not
# classified as FALSE.
REFUSAL_REASONS = frozenset({
    "cut",
    "rewrite",
    "truncate",
    "sealed_effect",
})

# Distinct from RUN_ID_RE (``run-``). Same digit/token widths so a
# caller cannot smuggle a run identity by changing only the prefix.
EPOCH_ID_RE: Pattern[str] = re.compile(r"^epoch-[0-9]{10,12}-[a-z0-9]{10,}$")

_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
    "send-authorized",
    "quote-sent",
    "campaign-envelope-ready",
})


def grants_send() -> bool:
    """An epoch classifier never authorizes a send. Structurally False."""
    return False


def halt_blocks_epoch() -> bool:
    """Structurally False. HALT stops STARTS, not window classification."""
    return False


def ready_is_authorized() -> bool:
    """Structurally False. Ready and authorized are different names."""
    return False


def claims_immutable() -> bool:
    """Structurally False. Classification is not chattr +i."""
    return False


def unknown_state_is_open() -> bool:
    """Structurally False. A missing state is UNKNOWN, not open."""
    return False


def unknown_is_false() -> bool:
    """Structurally False. UNKNOWN is not FALSE."""
    return False


def proposal_is_execution() -> bool:
    """Structurally False. Naming a window is not an external effect."""
    return False


def wires_into_run_store() -> bool:
    """Structurally False. This module is not wired into the store."""
    return False


def later_disarm_supersedes() -> bool:
    """Structurally True. A later disarm/hold outranks a ready name."""
    return True


def _is_sealed(name: object) -> bool:
    if not isinstance(name, str):
        return False
    if is_forbidden_effect_name(name):
        return True
    folded = name.strip().lower().replace("-", "_")
    return folded in {s.replace("-", "_") for s in _SEALED}


def _require_name(value: object, *, what: str) -> str:
    if isinstance(value, bool) or not isinstance(value, str) or not value.strip():
        raise FailClosedError(f"{what} must be a non-empty name: {value!r}")
    return value.strip()


def classify_state(state: object) -> str:
    """Return the window state, or fail closed.

    Unknown names are not classified as open and are not FALSE.
    ``cut`` / ``rewrite`` / ``truncate`` are known states (then
    refused on admit), not an unknown.
    """
    name = _require_name(state, what="state")
    folded = name.strip().lower()
    if folded == "open":
        return "open"
    if folded in REFUSED_STATES:
        return folded
    raise FailClosedError(
        f"unknown epoch state is not a refusal and not a grant: {state!r}")


def is_epoch_id(value: object) -> bool:
    """True only for the epoch shape. A run_id is not an epoch."""
    if isinstance(value, bool) or not isinstance(value, str):
        return False
    return bool(EPOCH_ID_RE.match(value.strip()))


@dataclass(frozen=True)
class EpochDecision:
    """The epoch-admission verdict. ``grants_send`` is structurally False.

    Two independent claims live on the same object so a silent default
    cannot masquerade as an authorization: ``allowed`` and
    ``grants_send`` are both recorded, and the constructor refuses
    ``grants_send=True``.
    """

    allowed: bool
    reason: Optional[str]
    state: str
    epoch_id: str
    grants_send: bool = False

    def __post_init__(self) -> None:
        if self.grants_send:
            raise FailClosedError(
                "EpochDecision cannot grant send_authorized / quote_sent / "
                "campaign_envelope_ready — an epoch class is not a send")
        object.__setattr__(self, "state", _require_name(self.state, what="state"))
        object.__setattr__(self, "epoch_id",
                           _require_name(self.epoch_id, what="epoch_id"))
        if self.allowed:
            if self.reason is not None:
                raise FailClosedError(
                    f"allowed epoch must not carry a reason: {self.reason!r}")
            if self.state != "open":
                raise FailClosedError(
                    "EpochDecision cannot allow a cut, rewrite, or truncate")
            if _is_sealed(self.state) or _is_sealed(self.epoch_id):
                raise FailClosedError(
                    "EpochDecision cannot grant a sealed send/ready name")
            if not EPOCH_ID_RE.match(self.epoch_id):
                raise FailClosedError(
                    f"allowed epoch must carry an epoch-shaped id: "
                    f"{self.epoch_id!r}")
            if RUN_ID_RE.match(self.epoch_id):
                raise FailClosedError(
                    "EpochDecision cannot admit a run_id as an epoch")
        else:
            if self.reason not in REFUSAL_REASONS:
                raise FailClosedError(
                    f"unknown or missing refusal reason: {self.reason!r}")
            if _is_sealed(self.state) or _is_sealed(self.epoch_id):
                if self.reason != "sealed_effect":
                    raise FailClosedError(
                        "EpochDecision cannot mis-label a sealed send/ready name")


def admit_epoch(
    *,
    state: object,
    epoch_id: object,
) -> EpochDecision:
    """May this named window accept appends?

    ``state`` and ``epoch_id`` are required names. Unknown states and
    malformed ids fail closed — UNKNOWN is not FALSE and is not
    admitted. A sealed send/ready name is a known refusal
    (``sealed_effect``). ``cut`` / ``rewrite`` / ``truncate`` are
    known refusals under their own reason. A run_id is not an epoch.

    Signature is sealed: no ``resend``, no ``send_authorized``, no
    ``halt``. Tests lock the parameter list; the kernel does not
    import inspect.
    """
    state_name = _require_name(state, what="state")
    epoch_name = _require_name(epoch_id, what="epoch_id")

    if _is_sealed(state_name) or _is_sealed(epoch_name):
        return EpochDecision(
            allowed=False,
            reason="sealed_effect",
            state=state_name,
            epoch_id=epoch_name,
        )

    classified = classify_state(state_name)
    if classified in REFUSED_STATES:
        return EpochDecision(
            allowed=False,
            reason=classified,
            state=classified,
            epoch_id=epoch_name,
        )

    if RUN_ID_RE.match(epoch_name):
        raise FailClosedError(
            f"run_id is not an epoch window: {epoch_name!r}")

    if not EPOCH_ID_RE.match(epoch_name):
        raise FailClosedError(
            f"epoch_id not shaped at the boundary: {epoch_name!r}")

    return EpochDecision(
        allowed=True,
        reason=None,
        state="open",
        epoch_id=epoch_name,
    )
