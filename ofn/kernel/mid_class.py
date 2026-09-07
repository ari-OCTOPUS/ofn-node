"""Classify the middle of a counted sequence without granting a send.

head_class / tail_pin (other body, #226) own end families of a
counted sequence (empty / single / head / tail / interior / past)
from length + index. This module does not recreate that.
carve_class / extract_pin (other body, #225) own cut_at + guest
vs host length. remainder_class / leftover_pin own leftover after
divide. segment_class / slice_pin (other body) own interval cuts.
offset_class / range_pin (other body) own interval bounds.
prefix_class / stem_pin (other body) own string prefixes.
seq.py is stateful (gap == replay) and is not recreated here.
payload_bound (unpublished / other body) is a different
module and is not recreated here.

This module is the middle witness: empty / single / odd_center /
even_split. Missing length is UNKNOWN (None), not FALSE and
not 0. A present-but-wrong type fails closed. Timeout is
UNKNOWN and does not prove a writer.

A unique center exists only for single and odd_center.
even_split records two middles; it does not invent one index.
empty has no center. Missing unique center is UNKNOWN, not 0.

center is a START. HALT refuses it. classify / observe / inspect
continue under HALT. Classification never grants a send
and never promotes campaign_envelope_ready to authorized.

Sealed send/ready names are never an intent and never a slot.
Not wired into run_store.py. Distinct from envelope_class,
store_class, seq, token_ceiling, and head_class.

Kernel purity: dataclasses + typing. No I/O, no clock, no now().
This file must not name a business or product.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .envelope import is_sealed_tool_name
from .errors import FailClosedError
from .events import is_forbidden_effect_name

EMPTY = "empty"
SINGLE = "single"
ODD_CENTER = "odd_center"
EVEN_SPLIT = "even_split"
UNKNOWN = "UNKNOWN"

FAMILIES = frozenset({EMPTY, SINGLE, ODD_CENTER, EVEN_SPLIT})

CENTER = "center"
CLASSIFY = "classify"
OBSERVE = "observe"
INSPECT = "inspect"

INTENTS = frozenset({CENTER, CLASSIFY, OBSERVE, INSPECT})

_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
    "send-authorized",
    "quote-sent",
    "campaign-envelope-ready",
})


def grants_send() -> bool:
    """A mid classifier never authorizes a send. Structurally False."""
    return False


def halt_blocks_classify() -> bool:
    """Structurally False. HALT stops STARTS, not this classify."""
    return False


def halt_blocks_observe() -> bool:
    """Structurally False. observe continues under HALT."""
    return False


def halt_blocks_inspect() -> bool:
    """Structurally False. inspect continues under HALT."""
    return False


def halt_blocks_center() -> bool:
    """Structurally True. center is a START; HALT refuses it."""
    return True


def ready_is_authorized() -> bool:
    """Structurally False. campaign_envelope_ready ≠ send_authorized."""
    return False


def claims_immutable() -> bool:
    """Structurally False. A classify is not filesystem immutability."""
    return False


def unknown_is_false() -> bool:
    """Structurally False. UNKNOWN is not FALSE."""
    return False


def timeout_proves_concurrent_write() -> bool:
    """Structurally False. Timeout is UNKNOWN, not a writer."""
    return False


def proposal_is_execution() -> bool:
    """Structurally False. A recorded middle is not an external effect."""
    return False


def promotes_ready_to_send() -> bool:
    """Structurally False. Ready stays ready."""
    return False


def wires_into_run_store() -> bool:
    """Structurally False. Complementary; not imported by the store."""
    return False


def mints_run_id() -> bool:
    """Structurally False. The factory in envelope.py mints. This classifies."""
    return False


def classify_timeout() -> str:
    """A timeout is UNKNOWN. It does not prove concurrent writing."""
    return UNKNOWN


def later_disarm_supersedes() -> bool:
    """Structurally True. A later hold/disarm beats older authorization."""
    return True


def empty_is_zero() -> bool:
    """Structurally False. Missing length is UNKNOWN, not 0."""
    return False


def even_split_is_zero() -> bool:
    """Structurally False. Missing unique center is UNKNOWN, not 0."""
    return False


def unique_center_is_send() -> bool:
    """Structurally False. A unique center is not a send."""
    return False


def even_split_is_authorized() -> bool:
    """Structurally False. even_split is a family, not send_authorized."""
    return False


def _fold(value: str) -> str:
    return value.strip().lower().replace("-", "_")


def _refuse_sealed(value: str, *, what: str) -> None:
    folded = _fold(value)
    if (
        is_forbidden_effect_name(value)
        or is_forbidden_effect_name(folded)
        or is_sealed_tool_name(value)
        or folded in {_fold(s) for s in _SEALED}
    ):
        raise FailClosedError(
            f"{what} names a sealed send/ready state: {value!r} — "
            "ready is not authorized")


def _require_length(length: object) -> int:
    if type(length) is not int:
        raise FailClosedError(f"length must be an exact int: {length!r}")
    if length < 0:
        raise FailClosedError(f"length must be >= 0: {length!r}")
    return length


def classify_intent(value: object) -> str:
    """center / classify / observe / inspect or UNKNOWN.

    None → UNKNOWN (no witness). bool/int/float/bytes fail closed.
    Empty / unknown / sealed names fail closed. UNKNOWN is not FALSE.
    """
    if value is None:
        return UNKNOWN
    if type(value) is not str:
        raise FailClosedError(f"intent must be a str or None: {value!r}")
    _refuse_sealed(value, what="intent")
    text = value.strip()
    if not text:
        raise FailClosedError("intent is empty")
    folded = _fold(text)
    if folded in INTENTS:
        return folded
    raise FailClosedError(
        f"unknown intent is not a refusal and not a grant: {value!r}")


def classify_family(
    length: object,
    *,
    timeout: object = False,
) -> Optional[str]:
    """empty / single / odd_center / even_split, or None.

    Missing length is UNKNOWN (None), not FALSE.
    Timeout is UNKNOWN (None) and does not prove a writer.
    Present-but-bad still fails closed. length must be an
    exact int >= 0. bool is not an int here.

    length == 0 is empty (no item, no center).
    length == 1 is single (the one item is the center).
    length odd and >= 3 is odd_center (unique mid at length // 2).
    length even and >= 2 is even_split (two middles; no unique).
    """
    if timeout is not False:
        if type(timeout) is not bool:
            raise FailClosedError(
                f"timeout must be an exact bool: {timeout!r}")
        return None
    if length is None:
        return None
    size = _require_length(length)
    if size == 0:
        return EMPTY
    if size == 1:
        return SINGLE
    if size % 2 == 1:
        return ODD_CENTER
    return EVEN_SPLIT


def center_of(
    length: object,
    *,
    timeout: object = False,
) -> Optional[int]:
    """Return the unique center index, or None.

    None is UNKNOWN, not 0 and not FALSE. empty and even_split
    have no unique center. Missing or timeout is UNKNOWN.
    Present-but-bad fails closed.
    """
    family = classify_family(length, timeout=timeout)
    if family is None:
        return None
    if family in {EMPTY, EVEN_SPLIT}:
        return None
    size = _require_length(length)
    return size // 2


def lo_mid_of(
    length: object,
    *,
    timeout: object = False,
) -> Optional[int]:
    """Lower middle index, or None when missing / empty / timeout.

    single and odd_center share one mid (same as center_of).
    even_split uses length // 2 - 1. None is UNKNOWN, not 0.
    """
    family = classify_family(length, timeout=timeout)
    if family is None or family == EMPTY:
        return None
    size = _require_length(length)
    if family == EVEN_SPLIT:
        return size // 2 - 1
    return size // 2


def hi_mid_of(
    length: object,
    *,
    timeout: object = False,
) -> Optional[int]:
    """Upper middle index, or None when missing / empty / timeout.

    single and odd_center share one mid (same as center_of).
    even_split uses length // 2. None is UNKNOWN, not 0.
    """
    family = classify_family(length, timeout=timeout)
    if family is None or family == EMPTY:
        return None
    size = _require_length(length)
    return size // 2


def _require_slot(value: object) -> str:
    if type(value) is not str:
        raise FailClosedError(f"slot must be a str: {value!r}")
    _refuse_sealed(value, what="slot")
    text = value.strip()
    if not text:
        raise FailClosedError("slot is empty")
    return text


@dataclass(frozen=True)
class MidBind:
    """One intent + family + length + slot.

    Frozen so a later write cannot silently retcon the recorded
    middle into send_authorized.
    """

    intent: str
    family: str
    length: int
    slot: str


def bind_mid(
    intent: object,
    length: object,
    *,
    slot: object,
) -> MidBind:
    """Require every side. Missing fails closed (use try_bind).

    Explicit bind is not try_bind: absence is not softened to
    UNKNOWN here.
    """
    klass = classify_intent(intent)
    if klass == UNKNOWN:
        raise FailClosedError("intent missing — UNKNOWN is not a bind")
    family = classify_family(length, timeout=False)
    if family is None:
        raise FailClosedError("length missing — UNKNOWN is not a bind")
    size = _require_length(length)
    key = _require_slot(slot)
    return MidBind(
        intent=klass,
        family=family,
        length=size,
        slot=key,
    )


def try_bind(
    intent: object,
    length: object,
    *,
    slot: object,
) -> Optional[MidBind]:
    """Missing intent, length, or slot is UNKNOWN (None).

    None is not FALSE. A present-but-bad value still fails closed —
    unknown shape is not a default family.
    """
    if intent is None or length is None or slot is None:
        return None
    return bind_mid(intent, length, slot=slot)


def admit_mid(
    intent: object,
    length: object,
    *,
    halted: object = False,
    timeout: object = False,
) -> Optional[bool]:
    """True when the intent may proceed.

    Missing intent or length is UNKNOWN (None), not False.
    classify / observe / inspect continue under HALT. center is
    refused when halted. Timeout is UNKNOWN (None) and does not
    prove a writer. A send name never reaches True — it fails
    closed at classify. halted / timeout must be exact bools.
    empty / even_split are families, not a send, and do not
    invent False for classify / observe / inspect.
    """
    if type(halted) is not bool:
        raise FailClosedError(f"halted must be an exact bool: {halted!r}")
    if type(timeout) is not bool:
        raise FailClosedError(f"timeout must be an exact bool: {timeout!r}")
    if timeout:
        return None
    klass = classify_intent(intent)
    if klass == UNKNOWN:
        return None
    family = classify_family(length, timeout=False)
    if family is None:
        return None
    if klass == CENTER:
        return not halted
    return True
