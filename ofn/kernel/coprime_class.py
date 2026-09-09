"""Classify two exact integers as coprime or common without granting a send.

prime_class / composite_pin (other body) own one-integer
zero / unit / prime / composite. even_class / odd_pin (other
body) own one-integer parity. remainder_class / leftover_pin
own leftover after division. min_class / max_pin (other body)
own lesser / tie / greater. sign_class / magnitude_pin (other
body) own sign of one integer. parity_class / check_pin own
even/odd admission of a different kind.

This module is the two-integer gcd witness: coprime / common.
Missing either side is UNKNOWN (None), not FALSE and not 0.
A present-but-wrong type fails closed. Timeout is UNKNOWN
and does not prove a writer. (0, 0) fails closed — gcd 0 is
not a family.

sample is a START. HALT refuses it. classify / observe /
inspect continue under HALT. Classification never grants a
send and never promotes campaign_envelope_ready to authorized.

Sealed send/ready names are never an intent and never a slot.
Not wired into run_store.py. Distinct from envelope_class,
store_class, seq, token_ceiling, and remainder_class.

Kernel purity: dataclasses + typing. No I/O, no clock, no now().
This file must not name a business or product.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .envelope import is_sealed_tool_name
from .errors import FailClosedError
from .events import is_forbidden_effect_name

COPRIME = "coprime"
COMMON = "common"
UNKNOWN = "UNKNOWN"

FAMILIES = frozenset({COPRIME, COMMON})

SAMPLE = "sample"
CLASSIFY = "classify"
OBSERVE = "observe"
INSPECT = "inspect"

INTENTS = frozenset({SAMPLE, CLASSIFY, OBSERVE, INSPECT})

_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
    "send-authorized",
    "quote-sent",
    "campaign-envelope-ready",
})


def grants_send() -> bool:
    """A coprime classifier never authorizes a send. Structurally False."""
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


def halt_blocks_sample() -> bool:
    """Structurally True. sample is a START; HALT refuses it."""
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
    """Structurally False. A recorded pair is not an external effect."""
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


def missing_gcd_is_zero() -> bool:
    """Structurally False. Missing gcd is UNKNOWN, not 0."""
    return False


def measured_one_is_unknown() -> bool:
    """Structurally False. gcd 1 is COPRIME, never UNKNOWN."""
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


def _require_side(value: object, *, name: str) -> int:
    if type(value) is not int:
        raise FailClosedError(f"{name} must be an exact int: {value!r}")
    return value


def _gcd(left: int, right: int) -> int:
    x, y = abs(left), abs(right)
    while y:
        x, y = y, x % y
    return x


def classify_intent(value: object) -> str:
    """sample / classify / observe / inspect or UNKNOWN.

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
    left: object,
    *,
    right: object,
    timeout: object = False,
) -> Optional[str]:
    """coprime / common, or None when missing or timed out.

    Missing left or right is UNKNOWN (None), not FALSE.
    Timeout is UNKNOWN (None) and does not prove a writer.
    Present-but-bad still fails closed. Sides must be exact ints.
    bool is not an int here. (0, 0) fails closed — gcd 0 is
    not a family. gcd 1 is COPRIME, never UNKNOWN.
    """
    if timeout is not False:
        if type(timeout) is not bool:
            raise FailClosedError(
                f"timeout must be an exact bool: {timeout!r}")
        return None
    if left is None or right is None:
        return None
    a = _require_side(left, name="left")
    b = _require_side(right, name="right")
    shared = _gcd(a, b)
    if shared == 0:
        raise FailClosedError(
            "gcd of (0, 0) is not a family — UNKNOWN is not 0")
    if shared == 1:
        return COPRIME
    return COMMON


def gcd_of(
    left: object,
    *,
    right: object,
    timeout: object = False,
) -> Optional[int]:
    """Return gcd(|left|, |right|), or None when missing or timed out.

    None is UNKNOWN, not 0 and not FALSE. Present-but-bad fails closed.
    (0, 0) still fails closed.
    """
    family = classify_family(left, right=right, timeout=timeout)
    if family is None:
        return None
    return _gcd(_require_side(left, name="left"), _require_side(right, name="right"))


def _require_slot(value: object) -> str:
    if type(value) is not str:
        raise FailClosedError(f"slot must be a str: {value!r}")
    _refuse_sealed(value, what="slot")
    text = value.strip()
    if not text:
        raise FailClosedError("slot is empty")
    return text


@dataclass(frozen=True)
class CoprimeBind:
    """One intent + family + gcd + left + right + slot.

    Frozen so a later write cannot silently retcon the recorded
    pair into send_authorized. left/right are the presented
    sides, not reordered.
    """

    intent: str
    family: str
    gcd: int
    left: int
    right: int
    slot: str


def bind_coprime(
    intent: object,
    left: object,
    *,
    right: object,
    slot: object,
) -> CoprimeBind:
    """Require every side. Missing fails closed (use try_bind).

    Explicit bind is not try_bind: absence is not softened to
    UNKNOWN here.
    """
    klass = classify_intent(intent)
    if klass == UNKNOWN:
        raise FailClosedError("intent missing — UNKNOWN is not a bind")
    family = classify_family(left, right=right, timeout=False)
    if family is None:
        raise FailClosedError("left or right missing — UNKNOWN is not a bind")
    a = _require_side(left, name="left")
    b = _require_side(right, name="right")
    key = _require_slot(slot)
    shared = _gcd(a, b)
    return CoprimeBind(
        intent=klass,
        family=family,
        gcd=shared,
        left=a,
        right=b,
        slot=key,
    )


def try_bind(
    intent: object,
    left: object,
    *,
    right: object,
    slot: object,
) -> Optional[CoprimeBind]:
    """Missing intent, left, right, or slot is UNKNOWN (None).

    None is not FALSE. A present-but-bad value still fails closed —
    unknown shape is not a default family.
    """
    if intent is None or left is None or right is None or slot is None:
        return None
    return bind_coprime(intent, left, right=right, slot=slot)


def admit_coprime(
    intent: object,
    left: object,
    *,
    right: object,
    halted: object = False,
    timeout: object = False,
) -> Optional[bool]:
    """True when the intent may proceed.

    Missing intent, left, or right is UNKNOWN (None), not False.
    classify / observe / inspect continue under HALT. sample is
    refused when halted. Timeout is UNKNOWN (None) and does not
    prove a writer. A send name never reaches True — it fails
    closed at classify. halted / timeout must be exact bools.
    Common gcd is a family, not a send, and does not invent
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
    family = classify_family(left, right=right, timeout=False)
    if family is None:
        return None
    if klass == SAMPLE:
        return not halted
    return True
