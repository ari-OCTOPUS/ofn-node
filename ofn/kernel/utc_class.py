"""UTC stamp class — a supplied timestamp is UTC_Z, OFFSET, or UNKNOWN.

The kernel has no clock. This module only classifies a value the
boundary already holds. Missing is UNKNOWN, not FALSE and not 0.
A naive local stamp fails closed. An offset is not UTC_Z.

campaign_envelope_ready, send_authorized, and quote_sent are sealed
names, not timestamps. Classification never grants a send.

Not wired into run_store.py. HALT stops STARTS, not classification.

Kernel purity: re + typing. No datetime, no I/O, no now().
"""

from __future__ import annotations

import re

from .envelope import deadline_epoch_s, is_sealed_tool_name
from .errors import FailClosedError
from .events import is_forbidden_effect_name

UTC_Z = "UTC_Z"
OFFSET = "OFFSET"
UNKNOWN = "UNKNOWN"

# Shape only. Civil validity is deadline_epoch_s (same calendar gate
# as TaskEnvelope). Naive stamps have neither Z nor an offset.
_STAMP_Z = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z$"
)
_STAMP_OFFSET = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?[+-]\d{2}:\d{2}$"
)

_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
})


def grants_send() -> bool:
    """A stamp class never authorizes a send. Structurally False."""
    return False


def halt_blocks_utc() -> bool:
    """Structurally False. HALT stops STARTS, not stamp classification."""
    return False


def unknown_is_false() -> bool:
    """Structurally False. UNKNOWN is not FALSE."""
    return False


def claims_immutable() -> bool:
    """Structurally False. Classification is not filesystem immutability."""
    return False


def ready_is_authorized() -> bool:
    """Structurally False. campaign_envelope_ready ≠ send_authorized."""
    return False


def _refuse_sealed(value: str) -> None:
    folded = value.strip().lower().replace("-", "_")
    if (
        is_forbidden_effect_name(value)
        or is_forbidden_effect_name(folded)
        or is_sealed_tool_name(value)
        or folded in _SEALED
    ):
        raise FailClosedError(
            f"stamp names a sealed send/ready state: {value!r}")


def classify_stamp(value: object) -> str:
    """Classify one supplied stamp.

    None → UNKNOWN (no witness). bool/int/float/bytes fail closed
    (an epoch is not a stamp class; that bind lives in clock_bind).
    Empty / naive / garbage fail closed. OFFSET is returned as
    OFFSET, never as UTC_Z. Impossible civil dates fail closed.
    """
    if value is None:
        return UNKNOWN
    if type(value) is not str:
        raise FailClosedError(f"stamp must be a str or None: {value!r}")
    _refuse_sealed(value)
    text = value.strip()
    if not text:
        raise FailClosedError("stamp is empty")
    if _STAMP_Z.match(text):
        deadline_epoch_s(text)
        return UTC_Z
    if _STAMP_OFFSET.match(text):
        deadline_epoch_s(text)
        return OFFSET
    raise FailClosedError(
        f"stamp is naive or malformed (not UTC_Z / OFFSET): {value!r}")


def is_utc_z(value: object) -> bool:
    """True only for a civil-valid UTC_Z stamp.

    None is not UTC_Z. This is not a FALSE verdict on the missing
    witness — callers that need the three-way answer use classify_stamp.
    """
    return classify_stamp(value) == UTC_Z
