"""Pin a HarmonicBind so the recorded bag cannot be retconned.

The caller owns the table. This module does no I/O and does
not mint. First pin records (slot → sorted:family:mean) after
sorting the presented bag. The same encoding again is
already_pinned. A different bag or family on the same slot
fails closed as reciprocal_collision.

peek never writes. Missing peek is UNKNOWN (None), not FALSE.
Timeout does not prove concurrent writing.

campaign_envelope_ready is structurally distinct from
send_authorized. A pin never grants a send and never
promotes ready to authorized. A later disarm supersedes
an older authorization claim.

Not wired into run_store.py. HALT stops STARTS, not a pin.
Distinct from mean/average, geometric/product, ratio/share,
floor/ceil, remainder/leftover, square/root, lcm/least,
and coprime/common.

Kernel purity: typing only. No I/O, no clock, no now().
This file must not name a business or product.
"""

from __future__ import annotations

from typing import Mapping, MutableMapping, Optional, Tuple

from .errors import FailClosedError
from .harmonic_class import (
    EXACT,
    MIXED,
    SAMPLE,
    HarmonicBind,
    bind_harmonic,
    classify_family,
    classify_intent,
)

PINNED = "pinned"
ALREADY_PINNED = "already_pinned"

_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
})


def grants_send() -> bool:
    """A reciprocal pin never authorizes a send. Structurally False."""
    return False


def halt_blocks_pin() -> bool:
    """Structurally False. HALT stops STARTS, not this pin."""
    return False


def ready_is_authorized() -> bool:
    """Structurally False. campaign_envelope_ready ≠ send_authorized."""
    return False


def claims_immutable() -> bool:
    """Structurally False. A pin is not filesystem immutability."""
    return False


def timeout_proves_concurrent_write() -> bool:
    """Structurally False. Timeout is UNKNOWN, not a writer."""
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


def consumes_nonce() -> bool:
    """Structurally False. This pin is not nonce once-consume."""
    return False


def unknown_is_false() -> bool:
    """Structurally False. UNKNOWN is not FALSE."""
    return False


def later_disarm_supersedes() -> bool:
    """Structurally True. A later hold/disarm beats older authorization."""
    return True


def missing_harmonic_is_one() -> bool:
    """Structurally False. Missing harmonic is UNKNOWN, not 1."""
    return False


def mixed_mean_is_zero() -> bool:
    """Structurally False. MIXED mean is UNKNOWN, not 0."""
    return False


def pin_allows_send(bind: HarmonicBind) -> bool:
    """Structurally False. Even a sample bind is not send_authorized."""
    if not isinstance(bind, HarmonicBind):
        raise FailClosedError(f"bind must be a HarmonicBind: {bind!r}")
    return False


def pin_allows_sample(bind: HarmonicBind) -> bool:
    """True only when the pinned intent is sample and family is exact.

    This is not a grant of sampling and not send_authorized.
    HALT still stops the factory START. Mixed mean is
    recorded, not authorized as a clean bag.
    """
    if not isinstance(bind, HarmonicBind):
        raise FailClosedError(f"bind must be a HarmonicBind: {bind!r}")
    return bind.intent == SAMPLE and bind.family == EXACT


def _ordered(bind: HarmonicBind) -> Tuple[int, ...]:
    return tuple(sorted(bind.values))


def _encode(bind: HarmonicBind) -> str:
    bag = ",".join(str(v) for v in _ordered(bind))
    mean = "-" if bind.harmonic is None else str(bind.harmonic)
    return f"{bag}:{bind.family}:{mean}"


def _refuse_sealed_slot(value: str) -> None:
    folded = value.strip().lower().replace("-", "_")
    if folded in {s.replace("-", "_") for s in _SEALED}:
        raise FailClosedError(
            f"slot names a sealed send/ready state: {value!r}")


def peek_reciprocal(table: Mapping[str, str], slot: object) -> Optional[str]:
    """Return the pinned encoding or None.

    None is UNKNOWN, not FALSE. Never writes. Missing table key
    is UNKNOWN. A sealed slot fails closed.
    """
    if table is None:
        raise FailClosedError("table missing — UNKNOWN is not a pin table")
    if type(slot) is not str:
        if slot is None:
            return None
        raise FailClosedError(f"slot must be a str or None: {slot!r}")
    if not slot.strip():
        raise FailClosedError("slot is empty")
    _refuse_sealed_slot(slot)
    text = slot.strip()
    if text not in table:
        return None
    pinned = table[text]
    if type(pinned) is not str or pinned.count(":") != 2:
        raise FailClosedError(f"pinned encoding drifted: {pinned!r}")
    bag_text, family, mean_text = pinned.split(":")
    if family not in {EXACT, MIXED}:
        raise FailClosedError(f"pinned family drifted: {family!r}")
    if not bag_text:
        raise FailClosedError(f"pinned bag drifted: {pinned!r}")
    for part in bag_text.split(","):
        if not part.isdigit() or int(part) < 1:
            raise FailClosedError(f"pinned bag drifted: {pinned!r}")
    if family == EXACT:
        if not mean_text.isdigit() or int(mean_text) < 1:
            raise FailClosedError(f"pinned mean drifted: {pinned!r}")
    elif mean_text != "-":
        raise FailClosedError(f"pinned mixed mean drifted: {pinned!r}")
    return pinned


def pin_reciprocal(
    table: MutableMapping[str, str],
    bind: HarmonicBind,
) -> str:
    """Record (slot → sorted:family:mean) at most once per encoding.

    First pin → pinned. Same encoding again → already_pinned.
    Different bag, family, or mean on the same slot fails closed.
    Permuted sides of the same bag are the same encoding (replay).
    """
    if table is None:
        raise FailClosedError("table missing — UNKNOWN is not a pin table")
    if not isinstance(bind, HarmonicBind):
        raise FailClosedError(f"bind must be a HarmonicBind: {bind!r}")
    checked = bind_harmonic(
        bind.intent,
        bind.values,
        slot=bind.slot,
    )
    if (
        checked.family != bind.family
        or checked.harmonic != bind.harmonic
        or checked.values != bind.values
    ):
        raise FailClosedError(
            "HarmonicBind drifted from re-bind: "
            f"have family={bind.family!r} harmonic={bind.harmonic!r} "
            f"values={bind.values!r}")
    existing = peek_reciprocal(table, checked.slot)
    encoded = _encode(checked)
    if existing is None:
        table[checked.slot] = encoded
        return PINNED
    if existing == encoded:
        return ALREADY_PINNED
    raise FailClosedError(
        f"reciprocal_collision: slot {checked.slot!r} pinned "
        f"{existing!r}, refused {encoded!r}")


def retcon_refused(
    table: Mapping[str, str],
    bind: HarmonicBind,
) -> Optional[bool]:
    """True when bind disagrees with a pinned encoding.

    Missing pin is UNKNOWN (None), not False. A measured
    disagreement is True. A matching pin is False.
    """
    if not isinstance(bind, HarmonicBind):
        raise FailClosedError(f"bind must be a HarmonicBind: {bind!r}")
    existing = peek_reciprocal(table, bind.slot)
    if existing is None:
        return None
    return existing != _encode(bind)


def try_pin(
    table: MutableMapping[str, str],
    intent: object,
    values: object,
    *,
    slot: object,
    timeout: object = False,
) -> Optional[str]:
    """Missing values/intent/slot or timeout is UNKNOWN (None).

    Present-but-bad still fails closed. Timeout does not write
    and does not prove a concurrent writer.
    """
    if timeout is not False:
        if type(timeout) is not bool:
            raise FailClosedError(
                f"timeout must be an exact bool: {timeout!r}")
        return None
    if intent is None or values is None or slot is None:
        return None
    if classify_intent(intent) == "UNKNOWN":
        return None
    if classify_family(values, timeout=False) is None:
        return None
    return pin_reciprocal(
        table, bind_harmonic(intent, values, slot=slot))
