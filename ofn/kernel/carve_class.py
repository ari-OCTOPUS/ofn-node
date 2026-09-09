"""Classify an extract window without granting a send.

splice_class / stitch_pin (other body) own insert_at vs host_len.
remainder_class / leftover_pin own leftover after divide.
offset_class / range_pin (other body) own interval bounds.
segment_class / slice_pin (other body) own slice families.
stride_class / step_pin (other body) own step size.
window_class / bound_pin (other body) own deadline-style windows.
payload_bound (unpublished / other body) is a different
module and is not recreated here.

This module is the extract witness: fits / overhang / past
for cut_at + guest_len against host_len. Missing any side
is UNKNOWN (None), not FALSE and not 0. A present-but-wrong
type fails closed. Timeout is UNKNOWN and does not prove
a writer.

carve is a START. HALT refuses it. classify / observe /
inspect continue under HALT. Classification never grants
a send and never promotes campaign_envelope_ready to
authorized. past is recorded, not granted.

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

FITS = "fits"
OVERHANG = "overhang"
PAST = "past"
UNKNOWN = "UNKNOWN"

FAMILIES = frozenset({FITS, OVERHANG, PAST})

CARVE = "carve"
CLASSIFY = "classify"
OBSERVE = "observe"
INSPECT = "inspect"

INTENTS = frozenset({CARVE, CLASSIFY, OBSERVE, INSPECT})

_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
    "send-authorized",
    "quote-sent",
    "campaign-envelope-ready",
})


def grants_send() -> bool:
    """A carve classifier never authorizes a send. Structurally False."""
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


def halt_blocks_carve() -> bool:
    """Structurally True. carve is a START; HALT refuses it."""
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
    """Structurally False. A recorded carve is not an external effect."""
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


def extracted_is_zero() -> bool:
    """Structurally False. Missing extracted length is UNKNOWN, not 0."""
    return False


def past_is_granted() -> bool:
    """Structurally False. past is recorded, not a carve grant."""
    return False


def overhang_is_granted() -> bool:
    """Structurally False. overhang is recorded, not a carve grant."""
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


def classify_intent(value: object) -> str:
    """carve / classify / observe / inspect or UNKNOWN.

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
    host_len: object,
    *,
    cut_at: object,
    guest_len: object,
    timeout: object = False,
) -> Optional[str]:
    """fits / overhang / past, or None when missing or timed out.

    Missing host_len, cut_at, or guest_len is UNKNOWN (None), not FALSE.
    Timeout is UNKNOWN (None) and does not prove a writer.
    Present-but-bad still fails closed. All three must be exact int >= 0.
    bool is not an int here.

    fits: cut_at + guest_len <= host_len
    overhang: cut_at < host_len and cut_at + guest_len > host_len
    past: cut_at >= host_len and a non-empty guest was requested,
          or cut_at > host_len. Empty extract at host_len is fits.
    """
    if timeout is not False:
        if type(timeout) is not bool:
            raise FailClosedError(
                f"timeout must be an exact bool: {timeout!r}")
        return None
    if host_len is None or cut_at is None or guest_len is None:
        return None
    host = _require_nonneg(host_len, name="host_len")
    cut = _require_nonneg(cut_at, name="cut_at")
    guest = _require_nonneg(guest_len, name="guest_len")
    if cut > host:
        return PAST
    if cut == host:
        return FITS if guest == 0 else PAST
    if cut + guest <= host:
        return FITS
    return OVERHANG


def extracted_of(
    host_len: object,
    *,
    cut_at: object,
    guest_len: object,
    timeout: object = False,
) -> Optional[int]:
    """Return extractable length, or None when missing, timed out, or past.

    fits → guest_len. overhang → host_len - cut_at (available, not requested).
    past → None (UNKNOWN, not 0). None is not FALSE.
    """
    family = classify_family(
        host_len, cut_at=cut_at, guest_len=guest_len, timeout=timeout)
    if family is None or family == PAST:
        return None
    host = _require_nonneg(host_len, name="host_len")
    cut = _require_nonneg(cut_at, name="cut_at")
    guest = _require_nonneg(guest_len, name="guest_len")
    if family == FITS:
        return guest
    return host - cut


def _require_slot(value: object) -> str:
    if type(value) is not str:
        raise FailClosedError(f"slot must be a str: {value!r}")
    _refuse_sealed(value, what="slot")
    text = value.strip()
    if not text:
        raise FailClosedError("slot is empty")
    return text


@dataclass(frozen=True)
class CarveBind:
    """One intent + family + cut + guest + host + extracted + slot.

    Frozen so a later write cannot silently retcon the recorded
    extract into send_authorized. extracted is None only for past.
    """

    intent: str
    family: str
    cut_at: int
    guest_len: int
    host_len: int
    extracted: Optional[int]
    slot: str


def bind_carve(
    intent: object,
    host_len: object,
    *,
    cut_at: object,
    guest_len: object,
    slot: object,
) -> CarveBind:
    """Require every side. Missing fails closed (use try_bind).

    Explicit bind is not try_bind: absence is not softened to
    UNKNOWN here.
    """
    klass = classify_intent(intent)
    if klass == UNKNOWN:
        raise FailClosedError("intent missing — UNKNOWN is not a bind")
    family = classify_family(
        host_len, cut_at=cut_at, guest_len=guest_len, timeout=False)
    if family is None:
        raise FailClosedError(
            "host_len, cut_at, or guest_len missing — UNKNOWN is not a bind")
    host = _require_nonneg(host_len, name="host_len")
    cut = _require_nonneg(cut_at, name="cut_at")
    guest = _require_nonneg(guest_len, name="guest_len")
    key = _require_slot(slot)
    extracted = extracted_of(host, cut_at=cut, guest_len=guest)
    return CarveBind(
        intent=klass,
        family=family,
        cut_at=cut,
        guest_len=guest,
        host_len=host,
        extracted=extracted,
        slot=key,
    )


def try_bind(
    intent: object,
    host_len: object,
    *,
    cut_at: object,
    guest_len: object,
    slot: object,
) -> Optional[CarveBind]:
    """Missing intent, host, cut, guest, or slot is UNKNOWN (None).

    None is not FALSE. A present-but-bad value still fails closed —
    unknown shape is not a default family.
    """
    if (
        intent is None
        or host_len is None
        or cut_at is None
        or guest_len is None
        or slot is None
    ):
        return None
    return bind_carve(
        intent, host_len, cut_at=cut_at, guest_len=guest_len, slot=slot)


def admit_carve(
    intent: object,
    host_len: object,
    *,
    cut_at: object,
    guest_len: object,
    halted: object = False,
    timeout: object = False,
) -> Optional[bool]:
    """True when the intent may proceed.

    Missing intent, host_len, cut_at, or guest_len is UNKNOWN (None),
    not False. classify / observe / inspect continue under HALT.
    carve is refused when halted. Timeout is UNKNOWN (None) and
    does not prove a writer. A send name never reaches True — it
    fails closed at classify. halted / timeout must be exact bools.
    overhang / past are families, not a send, and do not invent
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
    family = classify_family(
        host_len, cut_at=cut_at, guest_len=guest_len, timeout=False)
    if family is None:
        return None
    if klass == CARVE:
        return not halted
    return True
