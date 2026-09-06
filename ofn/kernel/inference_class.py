"""Inference fence — an inference never becomes an observation here.

Promotion of INFERENCE → OBSERVATION is structurally refused.
UNKNOWN → OBSERVATION is refused. Missing is UNKNOWN (None),
not FALSE. A timeout does not prove concurrent writing.

campaign_envelope_ready cannot be promoted to send_authorized.
This module does not mint reports and does not verify them
(another open change owns that pair).

Not wired into run_store.py. HALT stops STARTS, not a fence.

Kernel purity: typing only. No I/O, no clock, no now().
"""

from __future__ import annotations

from typing import Optional

from .envelope import is_sealed_tool_name
from .errors import FailClosedError
from .events import is_forbidden_effect_name
from .observation_class import INFERENCE, OBSERVATION, UNKNOWN


_CLASSES = frozenset({OBSERVATION, INFERENCE, UNKNOWN})
_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
})


def grants_send() -> bool:
    """An inference fence never authorizes a send. Structurally False."""
    return False


def halt_blocks_infer() -> bool:
    """Structurally False. HALT stops STARTS, not this fence."""
    return False


def timeout_proves_concurrent_write() -> bool:
    """Structurally False. Timeout is UNKNOWN, not a writer."""
    return False


def proposal_is_execution() -> bool:
    """Structurally False. An inference is not an external effect."""
    return False


def ready_is_authorized() -> bool:
    """Structurally False. campaign_envelope_ready ≠ send_authorized."""
    return False


def claims_immutable() -> bool:
    """Structurally False. A fence is not filesystem immutability."""
    return False


def ready_to_send() -> bool:
    """Structurally False. Ready is not a send authorization."""
    return False


def _class_name(value: object) -> Optional[str]:
    if value is None:
        return None
    if type(value) is not str:
        raise FailClosedError(f"class name must be a str or None: {value!r}")
    folded = value.strip().upper().replace("-", "_")
    raw_fold = value.strip().lower().replace("-", "_")
    if (
        is_forbidden_effect_name(value)
        or is_forbidden_effect_name(raw_fold)
        or is_sealed_tool_name(value)
        or raw_fold in _SEALED
    ):
        raise FailClosedError(
            f"class names a sealed send/ready state: {value!r}")
    if not folded:
        raise FailClosedError("class name is empty")
    if folded not in _CLASSES:
        raise FailClosedError(f"unknown class name: {value!r}")
    return folded


def promote(from_class: object, to_class: object) -> Optional[str]:
    """Refuse every promotion that would invent a stronger witness.

    Same-class re-state returns the class. Missing either side is
    UNKNOWN (None), not False. INFERENCE/UNKNOWN cannot become
    OBSERVATION. OBSERVATION cannot become INFERENCE (silent
    downgrade refused).
    """
    src = _class_name(from_class)
    dst = _class_name(to_class)
    if src is None or dst is None:
        return None
    if src == dst:
        return src
    raise FailClosedError(
        f"refusing promotion {src} → {dst} — inference is not observation")
