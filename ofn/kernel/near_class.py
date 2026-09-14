"""Classify distance from an origin without granting a send.

head_class / tail_pin (other body, #226) own end families of a
counted sequence (empty / single / head / tail / interior / past)
from length + index. This module does not recreate that.
mid_class / center_pin (other body, #227) own unique-center
families from length alone. carve_class / extract_pin (other
body, #225) own cut_at + guest vs host length.
remainder_class / leftover_pin own leftover after divide.
hysteresis_class / band_pin own a two-threshold latch with prior.
offset_class / range_pin (other body) own interval bounds.
watermark_class / high_pin (other body) own a single threshold.
payload_bound (unpublished / other body) is a different
module and is not recreated here.

This module is the distance witness: at / near / far from one
origin + one radius. Missing index, origin, or radius is
UNKNOWN (None), not FALSE and not 0. A present-but-wrong type
fails closed. Timeout is UNKNOWN and does not prove a writer.

AT is index == origin (distance 0 is measured, not missing).
NEAR is 0 < abs(index - origin) <= radius.
FAR is abs(index - origin) > radius.
radius == 0 admits AT or FAR only — nothing is near.

mark is a START. HALT refuses it. classify / observe / inspect
continue under HALT. Classification never grants a send
and never promotes campaign_envelope_ready to authorized.

Sealed send/ready names are never an intent and never a slot.
Not wired into run_store.py. Distinct from envelope_class,
store_class, seq, token_ceiling, and mid_class.

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
NEAR = "near"
FAR = "far"
UNKNOWN = "UNKNOWN"

FAMILIES = frozenset({AT, NEAR, FAR})

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
    """A near classifier never authorizes a send. Structurally False."""
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
    """Structurally False. A recorded distance is not an external effect."""
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


def missing_distance_is_zero() -> bool:
    """Structurally False. Missing distance is UNKNOWN, not 0."""
    return False


def at_is_send() -> bool:
    """Structurally False. AT is a family, not a send."""
    return False


def near_is_authorized() -> bool:
    """Structurally False. NEAR is a family, not send_authorized."""
    return False


def far_is_send() -> bool:
    """Structurally False. FAR is a family, not a send."""
    return False


def zero_radius_is_near() -> bool:
    """Structurally False. radius 0 admits AT or FAR, never NEAR."""
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


def _require_index(index: object) -> int:
    if type(index) is not int:
        raise FailClosedError(f"index must be an exact int: {index!r}")
    return index


def _require_origin(origin: object) -> int:
    if type(origin) is not int:
        raise FailClosedError(f"origin must be an exact int: {origin!r}")
    return origin


def _require_radius(radius: object) -> int:
    if type(radius) is not int:
        raise FailClosedError(f"radius must be an exact int: {radius!r}")
    if radius < 0:
        raise FailClosedError(f"radius must be >= 0: {radius!r}")
    return radius


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
    index: object,
    *,
    origin: object,
    radius: object,
    timeout: object = False,
) -> Optional[str]:
    """at / near / far, or None when missing or timed out.

    Missing index, origin, or radius is UNKNOWN (None), not FALSE.
    Timeout is UNKNOWN (None) and does not prove a writer.
    Present-but-bad still fails closed. index and origin must be
    exact ints (signed allowed). radius must be exact int >= 0.
    bool is not an int here.
    """
    if timeout is not False:
        if type(timeout) is not bool:
            raise FailClosedError(
                f"timeout must be an exact bool: {timeout!r}")
        return None
    if index is None or origin is None or radius is None:
        return None
    pos = _require_index(index)
    centre = _require_origin(origin)
    reach = _require_radius(radius)
    delta = abs(pos - centre)
    if delta == 0:
        return AT
    if delta <= reach:
        return NEAR
    return FAR


def distance_of(
    index: object,
    *,
    origin: object,
    radius: object,
    timeout: object = False,
) -> Optional[int]:
    """Return abs(index - origin), or None when missing or timed out.

    None is UNKNOWN, not 0 and not FALSE. Present-but-bad fails
    closed. AT records 0 because the sides were present.
    """
    if classify_family(
            index, origin=origin, radius=radius, timeout=timeout) is None:
        return None
    return abs(_require_index(index) - _require_origin(origin))


def _require_slot(value: object) -> str:
    if type(value) is not str:
        raise FailClosedError(f"slot must be a str: {value!r}")
    _refuse_sealed(value, what="slot")
    text = value.strip()
    if not text:
        raise FailClosedError("slot is empty")
    return text


@dataclass(frozen=True)
class NearBind:
    """One intent + family + index + origin + radius + distance + slot.

    Frozen so a later write cannot silently retcon the recorded
    distance into send_authorized.
    """

    intent: str
    family: str
    index: int
    origin: int
    radius: int
    distance: int
    slot: str


def bind_near(
    intent: object,
    index: object,
    *,
    origin: object,
    radius: object,
    slot: object,
) -> NearBind:
    """Require every side. Missing fails closed (use try_bind).

    Explicit bind is not try_bind: absence is not softened to
    UNKNOWN here.
    """
    klass = classify_intent(intent)
    if klass == UNKNOWN:
        raise FailClosedError("intent missing — UNKNOWN is not a bind")
    family = classify_family(index, origin=origin, radius=radius, timeout=False)
    if family is None:
        raise FailClosedError(
            "index, origin, or radius missing — UNKNOWN is not a bind")
    pos = _require_index(index)
    centre = _require_origin(origin)
    reach = _require_radius(radius)
    key = _require_slot(slot)
    return NearBind(
        intent=klass,
        family=family,
        index=pos,
        origin=centre,
        radius=reach,
        distance=abs(pos - centre),
        slot=key,
    )


def try_bind(
    intent: object,
    index: object,
    *,
    origin: object,
    radius: object,
    slot: object,
) -> Optional[NearBind]:
    """Missing intent, index, origin, radius, or slot is UNKNOWN (None).

    None is not FALSE. A present-but-bad value still fails closed —
    unknown shape is not a default family.
    """
    if (
        intent is None
        or index is None
        or origin is None
        or radius is None
        or slot is None
    ):
        return None
    return bind_near(
        intent, index, origin=origin, radius=radius, slot=slot)


def admit_near(
    intent: object,
    index: object,
    *,
    origin: object,
    radius: object,
    halted: object = False,
    timeout: object = False,
) -> Optional[bool]:
    """True when the intent may proceed.

    Missing intent, index, origin, or radius is UNKNOWN (None),
    not False. classify / observe / inspect continue under HALT.
    mark is refused when halted. Timeout is UNKNOWN (None) and
    does not prove a writer. A send name never reaches True —
    it fails closed at classify. halted / timeout must be exact
    bools. FAR / AT are families, not a send, and do not invent
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
    family = classify_family(index, origin=origin, radius=radius, timeout=False)
    if family is None:
        return None
    if klass == MARK:
        return not halted
    return True
