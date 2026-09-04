"""Compatibility pin — cite two schema versions without widening them.

A pin names the class of a left version and a right version and
records whether they are compatible. It does not rewrite
``SUPPORTED_VERSION``, does not mint a run_id, and does not
admit a START.

Missing either side is UNKNOWN. Compatible is then ``None``,
never False — UNKNOWN is not FALSE. Two supported sides are
compatible. Any UNKNOWN_VERSION side is not compatible and
does not invent a second supported version.

Timeout forces UNKNOWN and sets compatible to ``None``. It
does not prove concurrent writing.

A sealed send/ready name is never a version.
``campaign_envelope_ready`` is structurally distinct from
``send_authorized``; both fail closed as sealed names.

Not wired into the run store. Pinning compatibility is not
``send_authorized``, ``quote_sent``, or
``campaign_envelope_ready``. Ready is not authorized.

HALT stops STARTS. This module has no halt parameter: a pin
is not a run start.

Kernel purity: dataclasses + typing. No json, no clock, no I/O.
This file must not name a business or product.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .errors import FailClosedError
from .version_class import (
    VERSION_CLASSES,
    classify_timeout,
    classify_version,
    _is_sealed,
)


def grants_send() -> bool:
    """A pin never authorizes a send. Structurally False."""
    return False


def ready_is_authorized() -> bool:
    """Structurally False. Ready and authorized are different names."""
    return False


def claims_immutable() -> bool:
    """Structurally False. A pin is not chattr +i."""
    return False


def halt_blocks_pin() -> bool:
    """Structurally False. HALT stops STARTS, not a compatibility pin."""
    return False


def unknown_is_false() -> bool:
    """Structurally False. UNKNOWN is not FALSE."""
    return False


def unknown_version_is_false() -> bool:
    """Structurally False. UNKNOWN_VERSION is a class, not FALSE."""
    return False


def timeout_proves_concurrent() -> bool:
    """Structurally False. A timeout is UNKNOWN, not a race."""
    return False


def proposal_is_execution() -> bool:
    """Structurally False. A pin is not an external effect."""
    return False


def promotes_ready_to_send() -> bool:
    """Structurally False. Ready stays ready."""
    return False


def wires_into_run_store() -> bool:
    """Structurally False. Complementary; not imported by the store."""
    return False


def rewrites_supported_version() -> bool:
    """Structurally False. The pin cites; it does not widen version 1."""
    return False


def copies_envelope_class() -> bool:
    """Structurally False. This pin does not import envelope_class."""
    return False


@dataclass(frozen=True)
class CompatPin:
    """A citation of two version classes. ``grants_send`` is False.

    Two independent claims live on the same object so a silent default
    cannot masquerade as an authorization: ``compatible`` and
    ``grants_send`` are both recorded, and the constructor refuses
    ``grants_send=True``. ``compatible is None`` means UNKNOWN.
    """

    left_class: str
    right_class: str
    compatible: Optional[bool]
    timed_out: bool
    grants_send: bool = False

    def __post_init__(self) -> None:
        if self.grants_send:
            raise FailClosedError(
                "CompatPin cannot grant send_authorized / quote_sent / "
                "campaign_envelope_ready — a pin is not a send")
        if self.left_class not in VERSION_CLASSES:
            raise FailClosedError(
                f"unknown left_class is not a refusal and not a grant: "
                f"{self.left_class!r}")
        if self.right_class not in VERSION_CLASSES:
            raise FailClosedError(
                f"unknown right_class is not a refusal and not a grant: "
                f"{self.right_class!r}")
        if type(self.timed_out) is not bool:
            raise FailClosedError(
                f"timed_out must be an exact bool: {self.timed_out!r}")
        if self.compatible is not None and type(self.compatible) is not bool:
            raise FailClosedError(
                f"compatible must be exact bool or None: {self.compatible!r}")
        if self.timed_out and self.compatible is not None:
            raise FailClosedError(
                "CompatPin timeout must leave compatible UNKNOWN (None)")
        if (
            self.left_class == "UNKNOWN" or self.right_class == "UNKNOWN"
        ) and self.compatible is not None and not self.timed_out:
            raise FailClosedError(
                "CompatPin cannot treat UNKNOWN as False or True")
        if (
            self.left_class == "SUPPORTED"
            and self.right_class == "SUPPORTED"
            and not self.timed_out
            and self.compatible is not True
        ):
            raise FailClosedError(
                "CompatPin of two SUPPORTED sides must be compatible")
        if (
            (
                self.left_class == "UNKNOWN_VERSION"
                or self.right_class == "UNKNOWN_VERSION"
            )
            and not self.timed_out
            and self.left_class != "UNKNOWN"
            and self.right_class != "UNKNOWN"
            and self.compatible is not False
        ):
            raise FailClosedError(
                "CompatPin cannot invent compatibility for UNKNOWN_VERSION")

    def compatible_is_unknown(self) -> bool:
        """True only when the caller could not measure both sides."""
        return self.compatible is None


def pin_compat(
    *,
    left: object,
    right: object,
    timed_out: object = False,
) -> CompatPin:
    """The boundary's only sanctioned constructor.

    ``left`` and ``right`` are schema versions (exact int or None).
    Sealed send/ready names fail closed. Timeout forces UNKNOWN
    and does not prove a writer.

    Signature is sealed: no ``resend``, no ``send_authorized``, no
    ``immutable``. Tests lock the parameter list; the kernel does not
    import inspect.
    """
    if type(timed_out) is not bool:
        raise FailClosedError(
            f"timed_out must be an exact bool: {timed_out!r}")
    if _is_sealed(left) or _is_sealed(right):
        raise FailClosedError(
            "CompatPin refuses a sealed send/ready name as a version")
    left_class = classify_version(left)
    right_class = classify_version(right)
    if timed_out:
        return CompatPin(
            left_class="UNKNOWN",
            right_class="UNKNOWN",
            compatible=None,
            timed_out=True,
            grants_send=False,
        )
    if left_class == "UNKNOWN" or right_class == "UNKNOWN":
        return CompatPin(
            left_class=left_class,
            right_class=right_class,
            compatible=None,
            timed_out=False,
            grants_send=False,
        )
    if left_class == "SUPPORTED" and right_class == "SUPPORTED":
        return CompatPin(
            left_class=left_class,
            right_class=right_class,
            compatible=True,
            timed_out=False,
            grants_send=False,
        )
    return CompatPin(
        left_class=left_class,
        right_class=right_class,
        compatible=False,
        timed_out=False,
        grants_send=False,
    )


# Re-export so a pin caller can name timeout without importing the class.
timeout_is_unknown = classify_timeout
