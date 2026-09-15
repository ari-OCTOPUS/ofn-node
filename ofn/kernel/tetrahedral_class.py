"""Classify one exact integer as a tetrahedral number without granting a send.

pentagonal_class / figure_pin (other body) own P_n = n(3n-1)/2.
hexagonal_class / lattice_pin (other body) own H_n = n(2n-1).
heptagonal_class / gonal_pin (other body) own He_n = n(5n-3)/2.
octagonal_class / vertex_pin (other body) own O_n = n(3n-2).
triangular_class / series_pin (other body) own T_n = n(n+1)/2.
cube_class / cubic_pin (other body) own n^3, not Te_n.
square_class / root_pin (other body) own n^2.
payload_bound (unpublished / other body) is a different
module and is not recreated here.

This module is the tetrahedral witness: zero / tetrahedral /
other for one non-negative exact int as Te_n = n(n+1)(n+2)/6.
Walk identity 6 Te = n(n+1)(n+2) fail-closes. Missing value
is UNKNOWN (None), not FALSE and not 0. A present-but-wrong
type fails closed. Timeout is UNKNOWN and does not prove
a writer. Measured 0 is ZERO, never TETRAHEDRAL. Measured 1
is TETRAHEDRAL index 1, never UNKNOWN.

sample is a START. HALT refuses it. classify / observe /
inspect continue under HALT. Classification never grants
a send and never promotes campaign_envelope_ready to
authorized. other is recorded, not granted.

Sealed send/ready names are never an intent and never a slot.
Not wired into run_store.py. Distinct from envelope_class,
store_class, seq, token_ceiling, remainder_class, and
attest_class.

Kernel purity: dataclasses + typing. No I/O, no clock, no now().
This file must not name a business or product.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .envelope import is_sealed_tool_name
from .errors import FailClosedError
from .events import is_forbidden_effect_name

ZERO = "zero"
TETRAHEDRAL = "tetrahedral"
OTHER = "other"
UNKNOWN = "UNKNOWN"

FAMILIES = frozenset({ZERO, TETRAHEDRAL, OTHER})

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
    """A tetrahedral classifier never authorizes a send. Structurally False."""
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
    """Structurally False. A recorded tetrahedral is not an external effect."""
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


def measured_zero_is_tetrahedral() -> bool:
    """Structurally False. Measured 0 is ZERO, never TETRAHEDRAL."""
    return False


def measured_one_is_unknown() -> bool:
    """Structurally False. Measured 1 is TETRAHEDRAL index 1, never UNKNOWN."""
    return False


def other_is_granted() -> bool:
    """Structurally False. other is recorded, not a sample grant."""
    return False


def missing_index_is_zero() -> bool:
    """Structurally False. Missing index is UNKNOWN, not 0."""
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


def _require_nonneg(value: object, *, name: str) -> int:
    if type(value) is not int:
        raise FailClosedError(f"{name} must be an exact int: {value!r}")
    if value < 0:
        raise FailClosedError(f"{name} must be >= 0: {value!r}")
    return value


def _te_of(index: int) -> int:
    return index * (index + 1) * (index + 2) // 6


def _walk_holds(value: int, index: int) -> bool:
    return 6 * value == index * (index + 1) * (index + 2)


def _index_of(value: int) -> Optional[int]:
    """Return n>=1 such that Te_n = value, or None.

    0 is not an index grant (ZERO is a different family).
    Walk identity is checked before returning n.
    """
    if value == 0:
        return None
    target = 6 * value
    lo, hi = 1, value
    found: Optional[int] = None
    while lo <= hi:
        mid = (lo + hi) // 2
        prod = mid * (mid + 1) * (mid + 2)
        if prod == target:
            found = mid
            break
        if prod < target:
            lo = mid + 1
        else:
            hi = mid - 1
    if found is None:
        return None
    if not _walk_holds(value, found):
        raise FailClosedError(
            f"walk identity failed: 6*{value} != {found}*({found}+1)*({found}+2)")
    return found


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
    value: object,
    *,
    timeout: object = False,
) -> Optional[str]:
    """zero / tetrahedral / other, or None when missing or timed out.

    Missing value is UNKNOWN (None), not FALSE.
    Timeout is UNKNOWN (None) and does not prove a writer.
    Present-but-bad still fails closed. Value must be exact int >= 0.
    bool is not an int here. Measured 0 is ZERO, never TETRAHEDRAL.
    Measured 1 is TETRAHEDRAL, never UNKNOWN.
    """
    if timeout is not False:
        if type(timeout) is not bool:
            raise FailClosedError(
                f"timeout must be an exact bool: {timeout!r}")
        return None
    if value is None:
        return None
    number = _require_nonneg(value, name="value")
    if number == 0:
        return ZERO
    if _index_of(number) is not None:
        return TETRAHEDRAL
    return OTHER


def index_of(
    value: object,
    *,
    timeout: object = False,
) -> Optional[int]:
    """Return n for Te_n, or None when missing, timed out, zero, or other.

    None is UNKNOWN, not 0 and not FALSE. ZERO and OTHER have no
    granted index. Present-but-bad fails closed.
    """
    family = classify_family(value, timeout=timeout)
    if family is None or family != TETRAHEDRAL:
        return None
    return _index_of(_require_nonneg(value, name="value"))


def tetrahedral_of(
    index: object,
    *,
    timeout: object = False,
) -> Optional[int]:
    """Return Te_n = n(n+1)(n+2)/6, or None when missing or timed out.

    index 0 → 0 (the formula value, not a family grant).
    None is UNKNOWN, not FALSE. Present-but-bad fails closed.
    """
    if timeout is not False:
        if type(timeout) is not bool:
            raise FailClosedError(
                f"timeout must be an exact bool: {timeout!r}")
        return None
    if index is None:
        return None
    n = _require_nonneg(index, name="index")
    produced = _te_of(n)
    if n > 0 and not _walk_holds(produced, n):
        raise FailClosedError(
            f"walk identity failed producing Te_{n}={produced}")
    return produced


def _require_slot(value: object) -> str:
    if type(value) is not str:
        raise FailClosedError(f"slot must be a str: {value!r}")
    _refuse_sealed(value, what="slot")
    text = value.strip()
    if not text:
        raise FailClosedError("slot is empty")
    return text


@dataclass(frozen=True)
class TetrahedralBind:
    """One intent + family + value + index + slot.

    Frozen so a later write cannot silently retcon the recorded
    tetrahedral into send_authorized. index is None for zero/other.
    """

    intent: str
    family: str
    value: int
    index: Optional[int]
    slot: str


def bind_tetrahedral(
    intent: object,
    value: object,
    *,
    slot: object,
) -> TetrahedralBind:
    """Require every side. Missing fails closed (use try_bind).

    Explicit bind is not try_bind: absence is not softened to
    UNKNOWN here.
    """
    klass = classify_intent(intent)
    if klass == UNKNOWN:
        raise FailClosedError("intent missing — UNKNOWN is not a bind")
    family = classify_family(value, timeout=False)
    if family is None:
        raise FailClosedError("value missing — UNKNOWN is not a bind")
    number = _require_nonneg(value, name="value")
    key = _require_slot(slot)
    idx = _index_of(number) if family == TETRAHEDRAL else None
    return TetrahedralBind(
        intent=klass,
        family=family,
        value=number,
        index=idx,
        slot=key,
    )


def try_bind(
    intent: object,
    value: object,
    *,
    slot: object,
) -> Optional[TetrahedralBind]:
    """Missing intent, value, or slot is UNKNOWN (None).

    None is not FALSE. A present-but-bad value still fails closed —
    unknown shape is not a default family.
    """
    if intent is None or value is None or slot is None:
        return None
    return bind_tetrahedral(intent, value, slot=slot)


def admit_tetrahedral(
    intent: object,
    value: object,
    *,
    halted: object = False,
    timeout: object = False,
) -> Optional[bool]:
    """True when the intent may proceed.

    Missing intent or value is UNKNOWN (None), not False.
    classify / observe / inspect continue under HALT. sample is
    refused when halted. Timeout is UNKNOWN (None) and does not
    prove a writer. A send name never reaches True — it fails
    closed at classify. halted / timeout must be exact bools.
    other / zero are families, not a send, and do not invent
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
    family = classify_family(value, timeout=False)
    if family is None:
        return None
    if klass == SAMPLE:
        return not halted
    return True
