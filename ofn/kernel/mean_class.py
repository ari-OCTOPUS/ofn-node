"""Classify an arithmetic mean of exact ints without granting a send.

median_class / mode_pin (other body) own order-statistic / frequency.
remainder_class / leftover_pin own leftover after integer divide.
quotient_class / divide_pin (other body) own integer quotient.
congruent_class / residue_pin (other body) own a ≡ b (mod m).
square_class / root_pin (other body) own one perfect square.
lcm_class / least_pin (other body) own two-integer least common multiple.
peak_class / trough_pin own a three-sample extremum.

This module is the bag-mean witness: EXACT / MIXED. Missing bag is
UNKNOWN (None), not FALSE and not 0. A present-but-wrong type or an
empty bag fails closed. Timeout is UNKNOWN and does not prove a writer.

EXACT means total is divisible by count (the mean is an exact int).
MIXED means the mean exists but is not an exact int. MIXED is a
family, never FALSE and never a silent EXACT. A measured single 0
is EXACT with mean 0, never UNKNOWN.

sample is a START. HALT refuses it. classify / observe / inspect
continue under HALT. Classification never grants a send and never
promotes campaign_envelope_ready to authorized.

Sealed send/ready names are never an intent and never a slot.
Not wired into run_store.py.

Kernel purity: dataclasses + typing. No I/O, no clock, no now().
This file must not name a business or product.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .envelope import is_sealed_tool_name
from .errors import FailClosedError
from .events import is_forbidden_effect_name

EXACT = "EXACT"
MIXED = "MIXED"
UNKNOWN = "UNKNOWN"

FAMILIES = frozenset({EXACT, MIXED})

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
    """A mean classifier never authorizes a send. Structurally False."""
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
    """Structurally False. A recorded mean is not an external effect."""
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


def missing_is_zero() -> bool:
    """Structurally False. Missing bag is UNKNOWN, not 0."""
    return False


def mixed_is_false() -> bool:
    """Structurally False. MIXED is a family, not FALSE."""
    return False


def exact_mean_is_authorized() -> bool:
    """Structurally False. An exact integer mean is not a send."""
    return False


def empty_is_zero() -> bool:
    """Structurally False. Empty bag fails closed, not 0."""
    return False


def measured_zero_is_unknown() -> bool:
    """Structurally False. A measured 0 bag is EXACT, never UNKNOWN."""
    return False


def order_statistic_is_mean() -> bool:
    """Structurally False. Median/mode is a different witness."""
    return False


def leftover_is_mean() -> bool:
    """Structurally False. Remainder after divide is a different witness."""
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


def _require_int(value: object, *, what: str) -> int:
    if type(value) is not int:
        raise FailClosedError(f"{what} must be an exact int: {value!r}")
    return value


def _require_bag(value: object) -> tuple[int, ...]:
    if type(value) is not tuple and type(value) is not list:
        raise FailClosedError(f"samples must be a list or tuple: {value!r}")
    if not value:
        raise FailClosedError("samples is empty — not UNKNOWN and not 0")
    out: list[int] = []
    for index, item in enumerate(value):
        out.append(_require_int(item, what=f"samples[{index}]"))
    return tuple(out)


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
    samples: object,
    *,
    timeout: object = False,
) -> Optional[str]:
    """EXACT / MIXED, or None when missing or timed out.

    Missing bag is UNKNOWN (None), not FALSE and not 0.
    Timeout is UNKNOWN (None) and does not prove a writer.
    Present-but-bad still fails closed. Empty bag fails closed.
    Each sample must be an exact int. bool is not an int here.

    EXACT when total % count == 0. MIXED otherwise. A measured
    single 0 is EXACT. MIXED is a family, not FALSE.
    """
    if timeout is not False:
        if type(timeout) is not bool:
            raise FailClosedError(
                f"timeout must be an exact bool: {timeout!r}")
        return None
    if samples is None:
        return None
    bag = _require_bag(samples)
    total = sum(bag)
    if total % len(bag) == 0:
        return EXACT
    return MIXED


def exact_mean(
    samples: object,
    *,
    timeout: object = False,
) -> Optional[int]:
    """Integer mean when EXACT; None when missing, timed out, or MIXED.

    None is not FALSE and not 0. A measured 0 mean is 0, never None.
    MIXED has no exact integer mean — that None is not a missing bag.
    """
    family = classify_family(samples, timeout=timeout)
    if family is None:
        return None
    if family != EXACT:
        return None
    bag = _require_bag(samples)
    return sum(bag) // len(bag)


def bag_total(samples: object) -> int:
    """Sum of a present bag. Missing is not softened here."""
    bag = _require_bag(samples)
    return sum(bag)


def bag_count(samples: object) -> int:
    """Count of a present bag. Missing is not softened here."""
    bag = _require_bag(samples)
    return len(bag)


def _require_slot(value: object) -> str:
    if type(value) is not str:
        raise FailClosedError(f"slot must be a str: {value!r}")
    _refuse_sealed(value, what="slot")
    text = value.strip()
    if not text:
        raise FailClosedError("slot is empty")
    return text


@dataclass(frozen=True)
class MeanBind:
    """One intent + family + count + total + slot.

    Frozen so a later write cannot silently retcon the recorded
    mean into send_authorized. The bag itself is not stored —
    equal count+total is the same mean identity.
    """

    intent: str
    family: str
    count: int
    total: int
    slot: str


def bind_mean(
    intent: object,
    samples: object,
    *,
    slot: object,
) -> MeanBind:
    """Require every side. Missing fails closed (use try_bind).

    Explicit bind is not try_bind: absence is not softened to
    UNKNOWN here.
    """
    klass = classify_intent(intent)
    if klass == UNKNOWN:
        raise FailClosedError("intent missing — UNKNOWN is not a bind")
    family = classify_family(samples, timeout=False)
    if family is None:
        raise FailClosedError("samples missing — UNKNOWN is not a bind")
    bag = _require_bag(samples)
    key = _require_slot(slot)
    return MeanBind(
        intent=klass,
        family=family,
        count=len(bag),
        total=sum(bag),
        slot=key,
    )


def try_bind(
    intent: object,
    samples: object,
    *,
    slot: object,
) -> Optional[MeanBind]:
    """Missing intent or bag or slot is UNKNOWN (None).

    None is not FALSE. A present-but-bad value still fails closed —
    unknown shape is not a default family.
    """
    if intent is None or samples is None or slot is None:
        return None
    return bind_mean(intent, samples, slot=slot)


def admit_mean(
    intent: object,
    samples: object,
    *,
    halted: object = False,
    timeout: object = False,
) -> Optional[bool]:
    """True when the intent may proceed.

    Missing intent or bag is UNKNOWN (None), not False.
    classify / observe / inspect continue under HALT. sample is
    refused when halted. Timeout is UNKNOWN (None) and does not
    prove a writer. A send name never reaches True — it fails
    closed at classify. halted / timeout must be exact bools.
    MIXED is a family, not a send, and does not invent False
    for classify / observe / inspect.
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
    family = classify_family(samples, timeout=False)
    if family is None:
        return None
    if klass == SAMPLE:
        return not halted
    return True
