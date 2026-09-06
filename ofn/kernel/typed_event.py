"""Typed event *record* class — TYPED or UNKNOWN.

kind_graph owns succession. events.make_event owns the factory.
This module is the second witness for *record shape*: a mapping
must carry kind + run_id + ts before it is TYPED. Missing is
UNKNOWN, not FALSE. A present-but-wrong type fails closed.

campaign_envelope_ready, send_authorized, and quote_sent are
sealed names, not spine kinds. Classification never grants a send.
PROPOSAL_CREATED is TYPED and is not EXECUTION_RECEIPT.

BUDGET_DEBIT without a ref fails closed (one verdict → one
budget effect). The store is not written here.

Not wired into run_store.py. HALT stops STARTS, not classification.

Kernel purity: dataclasses + typing. No json, no clock, no now().
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Optional

from .envelope import is_sealed_tool_name, require_epoch_s
from .errors import FailClosedError
from .events import (
    BUDGET_DEBIT,
    EVENT_KINDS,
    EXECUTION_RECEIPT,
    PROPOSAL_CREATED,
    is_forbidden_effect_name,
)

TYPED = "TYPED"
UNKNOWN = "UNKNOWN"

_REQUIRED = ("kind", "run_id", "ts")
_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
})


def grants_send() -> bool:
    """A record class never authorizes a send. Structurally False."""
    return False


def halt_blocks_typed() -> bool:
    """Structurally False. HALT stops STARTS, not record classification."""
    return False


def unknown_is_false() -> bool:
    """Structurally False. UNKNOWN is not FALSE."""
    return False


def proposal_is_execution() -> bool:
    """Structurally False. A proposal record is not an execution."""
    return False


def ready_is_authorized() -> bool:
    """Structurally False. campaign_envelope_ready ≠ send_authorized."""
    return False


def claims_immutable() -> bool:
    """Structurally False. Classification is not filesystem immutability."""
    return False


def timeout_proves_concurrent_write() -> bool:
    """Structurally False. Timeout is UNKNOWN, not a writer."""
    return False


def _refuse_sealed(value: object, *, what: str) -> None:
    if not isinstance(value, str):
        return
    folded = value.strip().lower().replace("-", "_")
    if (
        is_forbidden_effect_name(value)
        or is_forbidden_effect_name(folded)
        or is_sealed_tool_name(value)
        or folded in _SEALED
    ):
        raise FailClosedError(
            f"{what} names a sealed send/ready state: {value!r}")


def _require_kind(value: object) -> str:
    if type(value) is not str:
        raise FailClosedError(f"kind must be a str: {value!r}")
    if not value.strip():
        raise FailClosedError("kind is empty")
    _refuse_sealed(value, what="kind")
    if value not in EVENT_KINDS:
        raise FailClosedError(f"unknown event kind: {value!r}")
    return value


def _require_run_id(value: object) -> str:
    if type(value) is not str:
        raise FailClosedError(f"run_id must be a str: {value!r}")
    if not value.strip():
        raise FailClosedError("run_id is empty")
    _refuse_sealed(value, what="run_id")
    return value


def _require_ref(value: object) -> Optional[str]:
    if value is None:
        return None
    if type(value) is not str:
        raise FailClosedError(f"ref must be a str or None: {value!r}")
    if not value.strip():
        raise FailClosedError("ref is empty")
    _refuse_sealed(value, what="ref")
    return value


@dataclass(frozen=True)
class TypedEvent:
    """One typed spine record. Frozen so a later write cannot retcon
    the classified shape. Does not carry a payload body.
    """

    kind: str
    run_id: str
    ts: int
    ref: Optional[str]


def is_execution(kind: object) -> bool:
    """True only for EXECUTION_RECEIPT. PROPOSAL_CREATED is False.

    Sealed names fail closed — they are not a negative witness.
    """
    if kind is None:
        raise FailClosedError("kind missing — UNKNOWN is not a bool")
    named = _require_kind(kind)
    return named == EXECUTION_RECEIPT


def classify_record(record: object) -> str:
    """TYPED when kind, run_id, and ts are all present and valid.

    None record → UNKNOWN. A required field that is None → UNKNOWN
    (missing witness), not FALSE. A required field with the wrong
    type fails closed. Sealed kinds fail closed. BUDGET_DEBIT
    without ref fails closed.
    """
    if record is None:
        return UNKNOWN
    if type(record) is bool or isinstance(record, (str, bytes, list, tuple)):
        raise FailClosedError(f"record must be a mapping: {record!r}")
    if not isinstance(record, Mapping):
        raise FailClosedError(f"record must be a mapping: {record!r}")
    for key in _REQUIRED:
        if key not in record or record[key] is None:
            return UNKNOWN
    kind = _require_kind(record["kind"])
    _require_run_id(record["run_id"])
    require_epoch_s(record["ts"], "ts")
    ref = _require_ref(record["ref"] if "ref" in record else None)
    if kind == BUDGET_DEBIT and ref is None:
        raise FailClosedError(
            "BUDGET_DEBIT requires ref to the EXECUTION_RECEIPT it settles")
    return TYPED


def require_typed(record: object) -> TypedEvent:
    """Fail closed when the record is missing or not TYPED."""
    klass = classify_record(record)
    if klass == UNKNOWN:
        raise FailClosedError("record missing — UNKNOWN is not a typed event")
    assert isinstance(record, Mapping)
    return TypedEvent(
        kind=_require_kind(record["kind"]),
        run_id=_require_run_id(record["run_id"]),
        ts=require_epoch_s(record["ts"], "ts"),
        ref=_require_ref(record["ref"] if "ref" in record else None),
    )


def try_typed(record: object) -> Optional[TypedEvent]:
    """Missing record or missing required field is UNKNOWN (None).

    Present-but-bad values still fail closed.
    """
    if record is None:
        return None
    if isinstance(record, Mapping):
        for key in _REQUIRED:
            if key not in record or record[key] is None:
                return None
    return require_typed(record)


def proposal_kind() -> str:
    """Named constant — not an execution."""
    return PROPOSAL_CREATED


def execution_kind() -> str:
    """Named constant — the only receipt kind this module binds."""
    return EXECUTION_RECEIPT
