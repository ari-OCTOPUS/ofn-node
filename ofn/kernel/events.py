"""Typed events — the spine's fixed vocabulary.

Two rules are load-bearing and encoded downstream in the run store:

  proposal ≠ execution   — PROPOSAL_CREATED and EXECUTION_RECEIPT are
                           different kinds and are never conflated;
  one verdict → one budget effect
                         — a BUDGET_DEBIT must reference (ref) exactly one
                           prior EXECUTION_RECEIPT, and the store rejects a
                           second debit against the same receipt.

RUN_REJECTED is not part of the eight-event happy spine; it exists so the
halt layer can record a refused start without creating a run (the kill
switch stops STARTS — it must not leave half-born runs behind).

Kernel purity: constants and validation only. No json, no clock, no I/O —
serialization belongs to the adapters.
"""

from __future__ import annotations

from typing import Any, Mapping, Optional

from .errors import FailClosedError

RUN_CREATED = "RUN_CREATED"
CLAIM_CREATED = "CLAIM_CREATED"
PROPOSAL_CREATED = "PROPOSAL_CREATED"
POLICY_DECISION = "POLICY_DECISION"
TOOL_INVOKED = "TOOL_INVOKED"
EXECUTION_RECEIPT = "EXECUTION_RECEIPT"
BUDGET_DEBIT = "BUDGET_DEBIT"
RUN_CLOSED = "RUN_CLOSED"
RUN_REJECTED = "RUN_REJECTED"

EVENT_KINDS = frozenset({
    RUN_CREATED, CLAIM_CREATED, PROPOSAL_CREATED, POLICY_DECISION,
    TOOL_INVOKED, EXECUTION_RECEIPT, BUDGET_DEBIT, RUN_CLOSED, RUN_REJECTED,
})

# Revenue / send names are states, not spine events. Recording them as a
# `kind` would collapse proposal into execution. The store checks this
# set independently of EVENT_KINDS so widening the vocabulary cannot
# accidentally admit a send.
FORBIDDEN_EFFECT_KINDS = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
})


def is_forbidden_effect_name(name: object) -> bool:
    """True only for the sealed send/ready names. UNKNOWN names are not
    treated as forbidden here — the kind gate handles those separately."""
    return isinstance(name, str) and name in FORBIDDEN_EFFECT_KINDS


# Payload root is depth 0. One nested mapping or list/tuple is depth 1.
# Deeper containers are out of scope (not claimed clean). Strings are
# never walked as sequences.
_SMUGGLE_SCAN_DEPTH = 1


def _scan_forbidden(obj: object, *, depth: int) -> Optional[str]:
    """Find a sealed send/ready name in a container, bounded by depth."""
    if is_forbidden_effect_name(obj):
        return str(obj)
    if depth > _SMUGGLE_SCAN_DEPTH:
        return None
    if isinstance(obj, Mapping):
        for key, value in obj.items():
            if is_forbidden_effect_name(key):
                return str(key)
            found = _scan_forbidden(value, depth=depth + 1)
            if found is not None:
                return found
        return None
    if isinstance(obj, (list, tuple)):
        for item in obj:
            found = _scan_forbidden(item, depth=depth + 1)
            if found is not None:
                return found
        return None
    return None


def payload_forbidden_effect(payload: Optional[Mapping[str, Any]]) -> Optional[str]:
    """Return a smuggled ready/authorized/sent name from a payload, if any.

    Scans the payload root and one nested mapping or list/tuple. Deeper
    nesting is out of scope (not recorded as 'clean'). Strings are never
    walked as sequences.
    """
    if payload is None:
        return None
    if not isinstance(payload, Mapping):
        raise FailClosedError(f"payload must be a mapping: {payload!r}")
    return _scan_forbidden(payload, depth=0)


def make_event(
    kind: str,
    run_id: str,
    *,
    now_epoch_s: int,
    payload: Optional[Mapping[str, Any]] = None,
    ref: Optional[str] = None,
) -> dict:
    """Build one event record. The store stamps event_id and seq on append;
    everything here is caller-supplied and validated.

    `ref` is the causal pointer — a BUDGET_DEBIT points at the
    EXECUTION_RECEIPT it settles. A verdict without its receipt is not a
    fact we can spend.
    """
    if kind in FORBIDDEN_EFFECT_KINDS:
        raise FailClosedError(
            f"forbidden effect kind: {kind!r} — ready/authorized/sent "
            "are not ledger events")
    if kind not in EVENT_KINDS:
        raise FailClosedError(f"unknown event kind: {kind!r}")
    if not isinstance(run_id, str) or not run_id.strip():
        raise FailClosedError(f"event run_id required: {run_id!r}")
    if not isinstance(now_epoch_s, int) or isinstance(now_epoch_s, bool):
        raise FailClosedError(f"now_epoch_s must be int: {now_epoch_s!r}")
    if payload is not None and not isinstance(payload, Mapping):
        raise FailClosedError(f"payload must be a mapping: {payload!r}")
    if ref is not None and (not isinstance(ref, str) or not ref.strip()):
        raise FailClosedError(f"ref must be a non-empty id: {ref!r}")
    if kind == BUDGET_DEBIT and ref is None:
        raise FailClosedError(
            "BUDGET_DEBIT requires ref to the EXECUTION_RECEIPT it settles "
            "(one verdict → one budget effect)")
    smuggled = payload_forbidden_effect(payload)
    if smuggled is not None:
        raise FailClosedError(
            f"payload smuggles forbidden effect name {smuggled!r} — "
            "ready/authorized/sent are not ledger facts")
    return {
        "kind": kind,
        "run_id": run_id,
        "ts": now_epoch_s,
        "payload": dict(payload or {}),
        "ref": ref,
    }
