"""Pin a first renew of a classified live lease.

pin_renew records one FIRST renew of a ``lse-`` token bound to one
run. prior_renew=True refuses as already_renewed. A bound_run_id
that disagrees with run_id refuses as lease_collision.

expire_epoch vs now_epoch: now >= expire is LEASE_EXPIRED (equal
means closed, same rule as deadline_window). Missing either epoch
is UNKNOWN, not FALSE and not expired. Caller supplies both
instants — the kernel has no clock.

A LIVE pin still does not grant a send. Expired is not a renew.
inspect/expire classes are not a renew pin. steal never pins.

campaign_envelope_ready stays distinct from send_authorized.
peek never writes. Not wired into run_store.py.

Distinct from lease_class (action classify), later_hold,
scoped_authz, deadline_window (run close, not a lease token),
and slot/occupy / ttl/expire (other open changes).
HALT stops STARTS, not this window classify.

Kernel purity: dataclasses + typing. No I/O, no clock, no now().
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .envelope import is_sealed_tool_name, require_epoch_s
from .errors import FailClosedError
from .events import is_forbidden_effect_name
from .lease_class import (
    LEASE_RENEW,
    UNKNOWN as LEASE_UNKNOWN,
    classify_lease,
    require_lease_id,
    require_run_id,
)

LEASE_LIVE = "LEASE_LIVE"
LEASE_EXPIRED = "LEASE_EXPIRED"
UNKNOWN = "UNKNOWN"

_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
    "send-authorized",
    "quote-sent",
    "campaign-envelope-ready",
})


def grants_send() -> bool:
    """A renew pin never authorizes a send. Structurally False."""
    return False


def rearms_send() -> bool:
    """Structurally False. A pin does not re-arm outbound."""
    return False


def halt_blocks_pin() -> bool:
    """Structurally False. HALT stops STARTS, not this window pin."""
    return False


def unknown_is_false() -> bool:
    """Structurally False. UNKNOWN is not FALSE."""
    return False


def unknown_is_expired() -> bool:
    """Structurally False. Missing now is not an expiry proof."""
    return False


def expired_is_false() -> bool:
    """Structurally False. EXPIRED is a class, not FALSE."""
    return False


def ready_is_authorized() -> bool:
    """Structurally False. campaign_envelope_ready ≠ send_authorized."""
    return False


def promotes_ready_to_send() -> bool:
    """Structurally False. A pin is not a rename of authorized."""
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


def wires_into_run_store() -> bool:
    """Structurally False. This module is not imported by the store."""
    return False


def live_is_send() -> bool:
    """Structurally False. LEASE_LIVE is a class, not a send grant."""
    return False


def peek_writes() -> bool:
    """Structurally False. peek classifies and does not pin."""
    return False


def later_disarm_supersedes() -> bool:
    """Structurally True. A later hold/disarm still beats this pin."""
    return True


def _fold(value: str) -> str:
    return value.strip().lower().replace("-", "_")


def _refuse_sealed_name(value: object, *, what: str) -> None:
    if type(value) is not str:
        return
    folded = _fold(value)
    if (
        is_forbidden_effect_name(value)
        or is_forbidden_effect_name(folded)
        or is_sealed_tool_name(value)
        or folded in {s.replace("-", "_") for s in _SEALED}
    ):
        raise FailClosedError(
            f"{what} names a sealed send/ready state: {value!r} — "
            "a renew is not a send")


def _epoch_or_unknown(value: object, *, what: str) -> Optional[int]:
    if value is None:
        return None
    _refuse_sealed_name(value, what=what)
    return require_epoch_s(value, what)


def classify_window(expire_epoch: object, now_epoch: object) -> str:
    """LEASE_LIVE, LEASE_EXPIRED, or UNKNOWN.

    Missing either side is UNKNOWN, not FALSE. Equal means
    expired (closed). Present-but-bad fails closed.
    """
    expire = _epoch_or_unknown(expire_epoch, what="expire_epoch")
    now = _epoch_or_unknown(now_epoch, what="now_epoch")
    if expire is None or now is None:
        return UNKNOWN
    if now >= expire:
        return LEASE_EXPIRED
    return LEASE_LIVE


def peek_window(expire_epoch: object, now_epoch: object) -> str:
    """Same as classify_window. Does not pin and does not write."""
    return classify_window(expire_epoch, now_epoch)


@dataclass(frozen=True)
class RenewPin:
    """One first live renew. Frozen so a later write cannot retcon
    LIVE into send_authorized.
    """

    lease_id: str
    run_id: str
    expire_epoch: int
    now_epoch: int
    window_class: str


def pin_renew(
    lease_id: object,
    run_id: object,
    expire_epoch: object,
    now_epoch: object,
    *,
    prior_renew: object = False,
    bound_run_id: object = None,
) -> RenewPin:
    """Require LEASE_RENEW + LIVE. Missing fails closed (use try_pin).

    prior_renew=True → already_renewed. bound_run_id mismatch →
    lease_collision. Expired is not a renew.
    """
    if type(prior_renew) is not bool:
        raise FailClosedError(f"prior_renew must be bool: {prior_renew!r}")
    if prior_renew:
        raise FailClosedError("already_renewed — second renew is not first")
    if bound_run_id is not None:
        bound = require_run_id(bound_run_id)
        current = require_run_id(run_id)
        if bound != current:
            raise FailClosedError(
                "lease_collision — same lease on a different run")
    klass = classify_lease(lease_id, run_id, "renew")
    if klass == LEASE_UNKNOWN:
        raise FailClosedError("lease missing — UNKNOWN is not a renew pin")
    if klass != LEASE_RENEW:
        raise FailClosedError(
            f"lease is {klass}, not LEASE_RENEW — inspect/expire do not pin")
    window = classify_window(expire_epoch, now_epoch)
    if window == UNKNOWN:
        raise FailClosedError("window missing — UNKNOWN is not a renew pin")
    if window != LEASE_LIVE:
        raise FailClosedError(
            f"window is {window}, not LEASE_LIVE — expired is not a renew")
    return RenewPin(
        lease_id=require_lease_id(lease_id),
        run_id=require_run_id(run_id),
        expire_epoch=require_epoch_s(expire_epoch, "expire_epoch"),
        now_epoch=require_epoch_s(now_epoch, "now_epoch"),
        window_class=LEASE_LIVE,
    )


def try_pin(
    lease_id: object,
    run_id: object,
    expire_epoch: object,
    now_epoch: object,
    *,
    prior_renew: object = False,
    bound_run_id: object = None,
) -> Optional[RenewPin]:
    """Missing lease or window is UNKNOWN (None). Present-but-bad
    still fails closed, including already_renewed and collision.
    """
    if lease_id is None or run_id is None:
        return None
    if expire_epoch is None or now_epoch is None:
        return None
    return pin_renew(
        lease_id,
        run_id,
        expire_epoch,
        now_epoch,
        prior_renew=prior_renew,
        bound_run_id=bound_run_id,
    )
