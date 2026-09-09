"""Classify a time-bounded lease token against one run.

A lease_id is ``lse-`` + 16 lowercase hex. It binds one run_id.
Actions: admit / inspect / renew / steal / expire.

admit and renew are STARTS (HALT refuses via may_proceed).
inspect and expire continue under HALT.
steal is never admitted.

Missing lease_id, run_id, or action is UNKNOWN, not FALSE and
not expired. Malformed tokens fail closed. Sealed send/ready
names refuse. campaign_envelope_ready stays distinct from
send_authorized.

A live or expired window is a separate classify in renew_pin.
This module does not read a clock.

Distinct from later_hold (epoch supersede), scoped_authz
(newer scoped pin), deadline_window (run create/append close),
start_permit (pre-mint HALT), event_id (evt- mint), slot/occupy
and ttl/expire (other open changes). Not wired into
run_store.py. HALT stops STARTS, not inspect/expire classify.

Kernel purity: dataclasses + typing + re. No I/O, no clock, no now().
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from .envelope import RUN_ID_RE, is_sealed_tool_name
from .errors import FailClosedError
from .events import is_forbidden_effect_name

LEASE_ADMIT = "LEASE_ADMIT"
LEASE_INSPECT = "LEASE_INSPECT"
LEASE_RENEW = "LEASE_RENEW"
LEASE_EXPIRE = "LEASE_EXPIRE"
UNKNOWN = "UNKNOWN"

LEASE_ID_RE = re.compile(r"^lse-[a-f0-9]{16}$")

_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
    "send-authorized",
    "quote-sent",
    "campaign-envelope-ready",
})
_ACTIONS = {
    "admit": LEASE_ADMIT,
    "inspect": LEASE_INSPECT,
    "renew": LEASE_RENEW,
    "expire": LEASE_EXPIRE,
}
_STARTS = frozenset({LEASE_ADMIT, LEASE_RENEW})
_CONTINUES = frozenset({LEASE_INSPECT, LEASE_EXPIRE})


def grants_send() -> bool:
    """A lease classify never authorizes a send. Structurally False."""
    return False


def rearms_send() -> bool:
    """Structurally False. A lease class does not re-arm outbound."""
    return False


def halt_blocks_classify() -> bool:
    """Structurally False. HALT stops STARTS, not this classify."""
    return False


def halt_blocks_inspect() -> bool:
    """Structurally False. inspect continues under HALT."""
    return False


def halt_blocks_expire() -> bool:
    """Structurally False. expire is an observation, not a START."""
    return False


def steals_lease() -> bool:
    """Structurally False. steal is never admitted."""
    return False


def unknown_is_false() -> bool:
    """Structurally False. UNKNOWN is not FALSE."""
    return False


def unknown_is_expired() -> bool:
    """Structurally False. Missing is not an expiry proof."""
    return False


def ready_is_authorized() -> bool:
    """Structurally False. campaign_envelope_ready ≠ send_authorized."""
    return False


def promotes_ready_to_send() -> bool:
    """Structurally False. A lease class is not a rename of authorized."""
    return False


def claims_immutable() -> bool:
    """Structurally False. A classify is not filesystem immutability."""
    return False


def timeout_proves_concurrent_write() -> bool:
    """Structurally False. Timeout is UNKNOWN, not a writer."""
    return False


def proposal_is_execution() -> bool:
    """Structurally False. A lease class is not an external effect."""
    return False


def wires_into_run_store() -> bool:
    """Structurally False. This module is not imported by the store."""
    return False


def later_disarm_supersedes() -> bool:
    """Structurally True. A later hold/disarm still beats this class."""
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
            "a lease is not a send")


def require_lease_id(value: object) -> str:
    """Exact ``lse-`` + 16 lowercase hex. Fail closed otherwise."""
    if type(value) is not str:
        raise FailClosedError(f"lease_id must be a str: {value!r}")
    _refuse_sealed_name(value, what="lease_id")
    if not LEASE_ID_RE.match(value):
        raise FailClosedError(f"lease_id not boundary-minted: {value!r}")
    return value


def require_run_id(value: object) -> str:
    """Boundary-minted run_id. Fail closed on sealed or malformed."""
    if type(value) is not str:
        raise FailClosedError(f"run_id must be a str: {value!r}")
    _refuse_sealed_name(value, what="run_id")
    if not RUN_ID_RE.match(value):
        raise FailClosedError(f"run_id not boundary-minted: {value!r}")
    return value


def _action_or_unknown(value: object) -> Optional[str]:
    if value is None:
        return None
    if type(value) is not str:
        raise FailClosedError(f"action must be a str or None: {value!r}")
    if not value.strip():
        raise FailClosedError("action is empty")
    _refuse_sealed_name(value, what="action")
    folded = _fold(value)
    if folded == "steal":
        raise FailClosedError("steal is never admitted")
    if folded not in _ACTIONS:
        raise FailClosedError(f"unknown lease action: {value!r}")
    return _ACTIONS[folded]


def classify_lease(lease_id: object, run_id: object, action: object) -> str:
    """LEASE_ADMIT / INSPECT / RENEW / EXPIRE, or UNKNOWN.

    Missing any side is UNKNOWN, not FALSE. Present-but-bad
    (malformed, sealed, steal, empty, bool) fails closed.
    """
    if lease_id is None or run_id is None or action is None:
        if lease_id is not None:
            require_lease_id(lease_id)
        if run_id is not None:
            require_run_id(run_id)
        if action is not None:
            _action_or_unknown(action)
        return UNKNOWN
    require_lease_id(lease_id)
    require_run_id(run_id)
    klass = _action_or_unknown(action)
    if klass is None:
        return UNKNOWN
    return klass


def is_start(klass: object) -> bool:
    """True only for ADMIT / RENEW. UNKNOWN / inspect / expire are not."""
    if klass is None:
        return False
    if type(klass) is not str:
        raise FailClosedError(f"klass must be a str or None: {klass!r}")
    folded = _fold(klass)
    if folded == UNKNOWN.lower():
        return False
    named = folded.upper()
    if named in _STARTS:
        return True
    if named in _CONTINUES:
        return False
    _refuse_sealed_name(klass, what="klass")
    raise FailClosedError(f"unknown lease class: {klass!r}")


def may_proceed(klass: object, halted: object) -> Optional[bool]:
    """START + halted → False. inspect/expire continue. Missing → None.

    True is not a send grant. halted must be an exact bool.
    """
    if type(halted) is not bool:
        raise FailClosedError(f"halted must be bool: {halted!r}")
    if klass is None:
        return None
    if type(klass) is not str:
        raise FailClosedError(f"klass must be a str or None: {klass!r}")
    folded = _fold(klass)
    if folded == UNKNOWN.lower():
        return None
    named = folded.upper()
    if named in _STARTS:
        return not halted
    if named in _CONTINUES:
        return True
    _refuse_sealed_name(klass, what="klass")
    raise FailClosedError(f"unknown lease class: {klass!r}")


def admit_send(klass: object) -> Optional[bool]:
    """True is unreachable. Known class → False. Missing → None."""
    if klass is None:
        return None
    if type(klass) is not str:
        raise FailClosedError(f"klass must be a str or None: {klass!r}")
    folded = _fold(klass)
    if folded == UNKNOWN.lower():
        return None
    named = folded.upper()
    if named in _STARTS or named in _CONTINUES:
        return False
    _refuse_sealed_name(klass, what="klass")
    raise FailClosedError(f"unknown lease class: {klass!r}")


@dataclass(frozen=True)
class LeaseClass:
    """One classified lease. Frozen so a later write cannot retcon
    a bind into send_authorized.
    """

    lease_id: str
    run_id: str
    action: str
    lease_class: str


def pin_lease(lease_id: object, run_id: object, action: object) -> LeaseClass:
    """Require a known class. Missing fails closed (use try_pin)."""
    klass = classify_lease(lease_id, run_id, action)
    if klass == UNKNOWN:
        raise FailClosedError("lease missing — UNKNOWN is not a lease pin")
    return LeaseClass(
        lease_id=require_lease_id(lease_id),
        run_id=require_run_id(run_id),
        action=_fold(action) if type(action) is str else "",
        lease_class=klass,
    )


def try_pin(lease_id: object, run_id: object, action: object) -> Optional[LeaseClass]:
    """Missing is UNKNOWN (None). Present-but-bad still fails closed."""
    if lease_id is None or run_id is None or action is None:
        return None
    return pin_lease(lease_id, run_id, action)
