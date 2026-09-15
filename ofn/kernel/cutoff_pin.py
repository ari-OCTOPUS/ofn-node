"""Cutoff pin — pin a named cutoff epoch without reading a clock.

A pin names a closed cutoff id and an exact-int epoch. Optional
``now_epoch_s`` classifies position. The kernel does not read a
clock; both instants are caller-supplied.

Positions (distinct from deadline_window and from horizon_class):

  before   — now < cutoff
  at_pin   — now == cutoff  (UNKNOWN grant — not before, not a send)
  after    — now > cutoff
  unknown  — now is None

``deadline_window.window_open`` treats equal as closed (False).
This pin treats equal as ``at_pin``: UNKNOWN, not a grant, not
False. ``horizon_class`` uses inside/at_edge/past on a horizon
kind; this pin cites a cutoff name + epoch. Complementary, not
a copy.

UNKNOWN now is None, never 0. 0 is a measured epoch.

A sealed send/ready name is never a cutoff name.
``campaign_envelope_ready`` is structurally distinct from
``send_authorized``; both fail closed as sealed names.

Not wired into the run store. Distinct from deadline_window
(bool open/closed), clock_bind (epoch+stamp pair), and
horizon_class (horizon admission).

HALT stops STARTS. This module has no halt parameter: pinning
a cutoff is not a run start.

Kernel purity: dataclasses + typing. No json, no clock, no I/O.
This file must not name a business or product.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .errors import FailClosedError
from .events import is_forbidden_effect_name

# Closed cutoff-name vocabulary. Widen only with a test.
CUTOFF_NAMES = frozenset({
    "mint_cutoff",
    "validate_cutoff",
    "replay_cutoff",
    "store_cutoff",
    "receipt_cutoff",
})
POSITIONS = frozenset({"before", "at_pin", "after", "unknown"})

_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
    "send-authorized",
    "quote-sent",
    "campaign-envelope-ready",
})


def grants_send() -> bool:
    """A pin never authorizes a send. Structurally False."""
    return False


def ready_is_authorized() -> bool:
    """Structurally False. Ready and authorized are different names."""
    return False


def claims_immutable() -> bool:
    """Structurally False. A pin is not chattr +i."""
    return False


def copies_deadline_window() -> bool:
    """Structurally False. Complementary; does not import deadline_window."""
    return False


def copies_horizon_class() -> bool:
    """Structurally False. Complementary; does not import horizon_class."""
    return False


def copies_clock_bind() -> bool:
    """Structurally False. Distinct from clock_bind / utc_class."""
    return False


def equal_is_closed() -> bool:
    """Structurally False. Equal is at_pin / UNKNOWN, not closed-as-False."""
    return False


def halt_blocks_pin() -> bool:
    """Structurally False. HALT stops STARTS, not a cutoff pin."""
    return False


def unknown_is_false() -> bool:
    """Structurally False. UNKNOWN is not FALSE."""
    return False


def unknown_epoch_is_zero() -> bool:
    """Structurally False. Missing now is UNKNOWN, not 0."""
    return False


def timeout_proves_concurrent() -> bool:
    """Structurally False. A timeout is UNKNOWN, not a race."""
    return False


def proposal_is_execution() -> bool:
    """Structurally False. Pinning a cutoff is not an external effect."""
    return False


def promotes_ready_to_send() -> bool:
    """Structurally False. Ready stays ready."""
    return False


def wires_into_run_store() -> bool:
    """Structurally False. Complementary; not imported by the store."""
    return False


def _fold(name: str) -> str:
    return name.strip().lower().replace("-", "_")


def _is_sealed(name: object) -> bool:
    if not isinstance(name, str):
        return False
    if is_forbidden_effect_name(name):
        return True
    return _fold(name) in {_fold(s) for s in _SEALED}


def _require_name(value: object, *, what: str) -> str:
    if isinstance(value, bool) or not isinstance(value, str) or not value.strip():
        raise FailClosedError(f"{what} must be a non-empty name: {value!r}")
    return value.strip()


def require_cutoff(value: object) -> str:
    """Closed cutoff id. Sealed names and unknowns fail closed."""
    name = _require_name(value, what="cutoff")
    if _is_sealed(name):
        raise FailClosedError(
            f"cutoff names a sealed send/ready state: {name!r}")
    if name not in CUTOFF_NAMES:
        raise FailClosedError(
            f"unknown cutoff is not a refusal and not a grant: {name!r}")
    return name


def require_epoch(value: object, *, what: str) -> int:
    """Exact int. Bool/str/float/None fail closed.

    A pin requires a measured cutoff epoch. Missing is not softened
    to 0. Call pin_cutoff with now_epoch_s=None when the *now* side
    must stay UNKNOWN.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        raise FailClosedError(f"{what} must be an exact int: {value!r}")
    return value


def require_now(value: object) -> Optional[int]:
    """Exact int, or None for UNKNOWN.

    ``None`` is UNKNOWN, not 0. ``True`` / ``1.0`` / ``\"0\"`` fail closed.
    """
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise FailClosedError(f"now_epoch_s must be exact int or None: {value!r}")
    return value


def classify_position(*, now_epoch_s: Optional[int], cutoff_epoch_s: int) -> str:
    """Derive the pin position. Missing now is UNKNOWN, not 0."""
    if now_epoch_s is None:
        return "unknown"
    if now_epoch_s < cutoff_epoch_s:
        return "before"
    if now_epoch_s == cutoff_epoch_s:
        return "at_pin"
    return "after"


@dataclass(frozen=True)
class CutoffPin:
    """A citation of a named cutoff epoch. ``grants_send`` is False.

    Two independent claims live on the same object so a silent default
    cannot masquerade as an authorization: ``position`` and
    ``grants_send`` are both recorded, and the constructor refuses
    ``grants_send=True``.
    """

    cutoff: str
    epoch_s: int
    now_epoch_s: Optional[int]
    position: str
    grants_send: bool = False

    def __post_init__(self) -> None:
        if self.grants_send:
            raise FailClosedError(
                "CutoffPin cannot grant send_authorized / quote_sent / "
                "campaign_envelope_ready — a pin is not a send")
        object.__setattr__(self, "cutoff", require_cutoff(self.cutoff))
        object.__setattr__(self, "epoch_s", require_epoch(self.epoch_s, what="epoch_s"))
        object.__setattr__(self, "now_epoch_s", require_now(self.now_epoch_s))
        expected = classify_position(
            now_epoch_s=self.now_epoch_s, cutoff_epoch_s=self.epoch_s)
        if self.position != expected:
            raise FailClosedError(
                f"position {self.position!r} does not match epochs "
                f"(expected {expected!r})")
        if self.position not in POSITIONS:
            raise FailClosedError(
                f"unknown position is not a refusal and not a grant: "
                f"{self.position!r}")

    def now_is_unknown(self) -> bool:
        """True only when the caller supplied None. 0 is a measurement."""
        return self.now_epoch_s is None

    def independently_verified(self) -> bool:
        """A pin is one record. It is not a pair of witnesses."""
        return False


def pin_cutoff(
    *,
    cutoff: object,
    epoch_s: object,
    now_epoch_s: object = None,
) -> CutoffPin:
    """The boundary's only sanctioned constructor.

    Signature is sealed: no ``resend``, no ``send_authorized``, no
    ``halt``, no ``immutable``. Tests lock the parameter list; the
    kernel does not import inspect.
    """
    name = require_cutoff(cutoff)
    epoch = require_epoch(epoch_s, what="epoch_s")
    now = require_now(now_epoch_s)
    return CutoffPin(
        cutoff=name,
        epoch_s=epoch,
        now_epoch_s=now,
        position=classify_position(now_epoch_s=now, cutoff_epoch_s=epoch),
        grants_send=False,
    )
