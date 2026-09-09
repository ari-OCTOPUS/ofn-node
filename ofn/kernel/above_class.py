"""Classify signed height of a plane without granting a send.

left_class / right_pin (other body, #229) own signed lateral
families (at / left / right) from one origin. This module
does not recreate that. front_class / back_pin (other body,
#230) own signed-depth families (at / back / front) from
one plane. near_class / far_pin (other body, #228) own
unsigned distance families (at / near / far) from origin +
radius. head_class / tail_pin (other body, #226) own end
families of a counted sequence. mid_class / center_pin
(other body, #227) own unique-center families from length
alone. carve_class / extract_pin (other body, #225) own
cut_at + guest vs host length. remainder_class /
leftover_pin own leftover after divide. hysteresis_class /
band_pin (#217) own a two-threshold latch with prior
(HIGH / LOW / INSIDE). Those uppercase ABOVE / BELOW names
are band sides against low/high + prior — not this height
axis, which has one plane and no prior. offset_class /
range_pin (other body) own interval bounds. watermark_class
/ high_pin (other body) own a single threshold.
payload_bound (unpublished / other body) is a different
module and is not recreated here.

This module is the signed-height witness: at / below / above
from one plane. Missing height or plane is UNKNOWN (None),
not FALSE and not 0. A present-but-wrong type fails closed.
Timeout is UNKNOWN and does not prove a writer.

AT is height == plane (signed 0 is measured, not missing).
BELOW is height < plane.
ABOVE is height > plane.
There is no radius here — unsigned reach is #228.
There is no lateral index — signed side is #229.
There is no depth here — signed depth is #230.
There is no prior / low / high pair — two-threshold latch
is #217.

mark is a START. HALT refuses it. classify / observe / inspect
continue under HALT. Classification never grants a send
and never promotes campaign_envelope_ready to authorized.

Sealed send/ready names are never an intent and never a slot.
Not wired into run_store.py. Distinct from envelope_class,
store_class, seq, token_ceiling, front_class, left_class,
and hysteresis_class.

Kernel purity: dataclasses + typing. No I/O, no clock, no now().
This file must not name a business or product.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .envelope import is_sealed_tool_name
from .errors import FailClosedError
from .events import is_forbidden_effect_name

AT = "at"
BELOW = "below"
ABOVE = "above"
UNKNOWN = "UNKNOWN"

FAMILIES = frozenset({AT, BELOW, ABOVE})

MARK = "mark"
CLASSIFY = "classify"
OBSERVE = "observe"
INSPECT = "inspect"

INTENTS = frozenset({MARK, CLASSIFY, OBSERVE, INSPECT})

_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
    "send-authorized",
    "quote-sent",
    "campaign-envelope-ready",
})


def grants_send() -> bool:
    """An above classifier never authorizes a send. Structurally False."""
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


def halt_blocks_mark() -> bool:
    """Structurally True. mark is a START; HALT refuses it."""
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
    """Structurally False. A recorded height is not an external effect."""
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


def missing_signed_is_zero() -> bool:
    """Structurally False. Missing signed height is UNKNOWN, not 0."""
    return False


def at_is_send() -> bool:
    """Structurally False. AT is a family, not a send."""
    return False


def below_is_authorized() -> bool:
    """Structurally False. BELOW is a family, not send_authorized."""
    return False


def above_is_send() -> bool:
    """Structurally False. ABOVE is a family, not a send."""
    return False


def at_is_below() -> bool:
    """Structurally False. Plane coincidence is AT, never BELOW."""
    return False


def at_is_above() -> bool:
    """Structurally False. Plane coincidence is AT, never ABOVE."""
    return False


def hysteresis_band_is_this_axis() -> bool:
    """Structurally False. #217 uppercase band sides are not this axis."""
    return False


def front_is_this_axis() -> bool:
    """Structurally False. #230 signed depth is not this height axis."""
    return False


def left_is_this_axis() -> bool:
    """Structurally False. #229 signed lateral is not this height axis."""
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


def _require_height(height: object) -> int:
    if type(height) is not int:
        raise FailClosedError(f"height must be an exact int: {height!r}")
    return height


def _require_plane(plane: object) -> int:
    if type(plane) is not int:
        raise FailClosedError(f"plane must be an exact int: {plane!r}")
    return plane


def classify_intent(value: object) -> str:
    """mark / classify / observe / inspect or UNKNOWN.

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
    height: object,
    *,
    plane: object,
    timeout: object = False,
) -> Optional[str]:
    """at / below / above, or None when missing or timed out.

    Missing height or plane is UNKNOWN (None), not FALSE.
    Timeout is UNKNOWN (None) and does not prove a writer.
    Present-but-bad still fails closed. height and plane must be
    exact ints (signed allowed). bool is not an int here.
    """
    if timeout is not False:
        if type(timeout) is not bool:
            raise FailClosedError(
                f"timeout must be an exact bool: {timeout!r}")
        return None
    if height is None or plane is None:
        return None
    pos = _require_height(height)
    wall = _require_plane(plane)
    if pos == wall:
        return AT
    if pos < wall:
        return BELOW
    return ABOVE


def signed_of(
    height: object,
    *,
    plane: object,
    timeout: object = False,
) -> Optional[int]:
    """Return height - plane, or None when missing or timed out.

    None is UNKNOWN, not 0 and not FALSE. Present-but-bad fails
    closed. AT records 0 because the sides were present.
    """
    if classify_family(height, plane=plane, timeout=timeout) is None:
        return None
    return _require_height(height) - _require_plane(plane)


def _require_slot(value: object) -> str:
    if type(value) is not str:
        raise FailClosedError(f"slot must be a str: {value!r}")
    _refuse_sealed(value, what="slot")
    text = value.strip()
    if not text:
        raise FailClosedError("slot is empty")
    return text


@dataclass(frozen=True)
class AboveBind:
    """One intent + family + height + plane + signed + slot.

    Frozen so a later write cannot silently retcon the recorded
    height into send_authorized.
    """

    intent: str
    family: str
    height: int
    plane: int
    signed: int
    slot: str


def bind_above(
    intent: object,
    height: object,
    *,
    plane: object,
    slot: object,
) -> AboveBind:
    """Require every side. Missing fails closed (use try_bind).

    Explicit bind is not try_bind: absence is not softened to
    UNKNOWN here.
    """
    klass = classify_intent(intent)
    if klass == UNKNOWN:
        raise FailClosedError("intent missing — UNKNOWN is not a bind")
    family = classify_family(height, plane=plane, timeout=False)
    if family is None:
        raise FailClosedError(
            "height or plane missing — UNKNOWN is not a bind")
    pos = _require_height(height)
    wall = _require_plane(plane)
    key = _require_slot(slot)
    return AboveBind(
        intent=klass,
        family=family,
        height=pos,
        plane=wall,
        signed=pos - wall,
        slot=key,
    )


def try_bind(
    intent: object,
    height: object,
    *,
    plane: object,
    slot: object,
) -> Optional[AboveBind]:
    """Missing intent, height, plane, or slot is UNKNOWN (None).

    None is not FALSE. A present-but-bad value still fails closed —
    unknown shape is not a default family.
    """
    if intent is None or height is None or plane is None or slot is None:
        return None
    return bind_above(intent, height, plane=plane, slot=slot)


def admit_above(
    intent: object,
    height: object,
    *,
    plane: object,
    halted: object = False,
    timeout: object = False,
) -> Optional[bool]:
    """True when the intent may proceed.

    Missing intent, height, or plane is UNKNOWN (None), not False.
    classify / observe / inspect continue under HALT. mark is
    refused when halted. Timeout is UNKNOWN (None) and does not
    prove a writer. A send name never reaches True — it fails
    closed at classify. halted / timeout must be exact bools.
    BELOW / ABOVE / AT are families, not a send, and do not invent
    False for classify / observe / inspect.
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
    family = classify_family(height, plane=plane, timeout=False)
    if family is None:
        return None
    if klass == MARK:
        return not halted
    return True
