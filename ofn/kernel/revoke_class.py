"""Classify revoke of a ready hold without granting a send.

void_class / cancel_pin (unpublished / other body) own voiding a
task identity. hold_class / disarm_pin and later_hold /
scoped_authz (unpublished / other body) own hold/disarm tickets.
send_fence owns the ready→authorized promotion refuse.
campaign_bind owns naming a ready state. close_gate owns
deadline close. rejection owns a refused start.

This module is the revoke witness: held / withdrawn. A later
withdraw supersedes an older ready classification. It does not
promote campaign_envelope_ready to send_authorized and it does
not invent quote_sent.

issue is a START. HALT refuses it. revoke / classify / observe
continue under HALT — withdrawing a ready hold is recovery, not
a new run. Missing withdrawn or subject is UNKNOWN (None), not
FALSE. Timeout is UNKNOWN and does not prove a writer.

send_authorized / quote_sent are sealed send names and fail
closed. campaign_envelope_ready is a READY subject that can be
held or withdrawn — it is not a send.

Not wired into run_store.py. Distinct from envelope_class,
store_class, send_fence, campaign_bind, close_gate, and
rejection.

Kernel purity: dataclasses + typing + re (via envelope).
No I/O, no clock, no now().
This file must not name a business or product.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .envelope import RUN_ID_RE, is_sealed_tool_name
from .errors import FailClosedError
from .events import is_forbidden_effect_name

HELD = "held"
WITHDRAWN = "withdrawn"
UNKNOWN = "UNKNOWN"

FAMILIES = frozenset({HELD, WITHDRAWN})

ISSUE = "issue"
REVOKE = "revoke"
CLASSIFY = "classify"
OBSERVE = "observe"

INTENTS = frozenset({ISSUE, REVOKE, CLASSIFY, OBSERVE})

READY = "ready"
RUN = "run"

SUBJECT_KINDS = frozenset({READY, RUN})

_SEND_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
    "send-authorized",
    "quote-sent",
})
_READY = frozenset({
    "campaign_envelope_ready",
    "campaign-envelope-ready",
    "ready",
})


def grants_send() -> bool:
    """A revoke classifier never authorizes a send. Structurally False."""
    return False


def halt_blocks_classify() -> bool:
    """Structurally False. HALT stops STARTS, not this classify."""
    return False


def halt_blocks_observe() -> bool:
    """Structurally False. observe continues under HALT."""
    return False


def halt_blocks_revoke() -> bool:
    """Structurally False. revoke is recovery, not a START."""
    return False


def halt_blocks_issue() -> bool:
    """Structurally True. issue is a START; HALT refuses it."""
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
    """Structurally False. A recorded revoke is not an external effect."""
    return False


def promotes_ready_to_send() -> bool:
    """Structurally False. Ready stays ready, or is withdrawn."""
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


def later_withdraw_supersedes() -> bool:
    """Structurally True. A later withdraw beats an older ready hold."""
    return True


def later_disarm_supersedes() -> bool:
    """Structurally True. A later hold/disarm beats older authorization."""
    return True


def withdrawn_is_authorized() -> bool:
    """Structurally False. Withdrawn ready is not send_authorized."""
    return False


def _fold(value: str) -> str:
    return value.strip().lower().replace("-", "_")


def _refuse_send_sealed(value: str, *, what: str) -> None:
    folded = _fold(value)
    send_names = {_fold(s) for s in _SEND_SEALED}
    if (
        folded in send_names
        or is_forbidden_effect_name(value) and folded in send_names
        or is_sealed_tool_name(value) and folded in send_names
    ):
        raise FailClosedError(
            f"{what} names a sealed send state: {value!r} — "
            "this classifier never granted a send")


def classify_intent(value: object) -> str:
    """issue / revoke / classify / observe or UNKNOWN.

    None → UNKNOWN (no witness). bool/int/float/bytes fail closed.
    Empty / unknown / send-sealed names fail closed. Ready as an
    intent is a shape error (ready is a subject, not an intent).
    UNKNOWN is not FALSE.
    """
    if value is None:
        return UNKNOWN
    if type(value) is not str:
        raise FailClosedError(f"intent must be a str or None: {value!r}")
    _refuse_send_sealed(value, what="intent")
    text = value.strip()
    if not text:
        raise FailClosedError("intent is empty")
    folded = _fold(text)
    if folded in {_fold(s) for s in _READY}:
        raise FailClosedError(
            f"intent names a ready subject, not an intent: {value!r}")
    if folded in INTENTS:
        return folded
    raise FailClosedError(
        f"unknown intent is not a refusal and not a grant: {value!r}")


def classify_subject(value: object) -> Optional[str]:
    """ready / run, or None when missing.

    None → UNKNOWN (None), not FALSE. send names fail closed.
    campaign_envelope_ready (and aliases, including ``ready``)
    classify as ready. A well-formed run_id classifies as run.
    Empty / unknown / bool fail closed.
    """
    if value is None:
        return None
    if type(value) is not str:
        raise FailClosedError(f"subject must be a str or None: {value!r}")
    _refuse_send_sealed(value, what="subject")
    text = value.strip()
    if not text:
        raise FailClosedError("subject is empty")
    folded = _fold(text)
    if folded in {_fold(s) for s in _READY}:
        return READY
    if RUN_ID_RE.match(text):
        return RUN
    raise FailClosedError(
        f"unknown subject is not a refusal and not a grant: {value!r}")


def classify_family(
    withdrawn: object,
    *,
    timeout: object = False,
) -> Optional[str]:
    """held / withdrawn, or None when missing or timed out.

    Missing withdrawn is UNKNOWN (None), not FALSE.
    Timeout is UNKNOWN (None) and does not prove a writer.
    Present-but-bad still fails closed. withdrawn must be an
    exact bool. bool is the only admitted type.
    """
    if timeout is not False:
        if type(timeout) is not bool:
            raise FailClosedError(
                f"timeout must be an exact bool: {timeout!r}")
        return None
    if withdrawn is None:
        return None
    if type(withdrawn) is not bool:
        raise FailClosedError(
            f"withdrawn must be an exact bool or None: {withdrawn!r}")
    return WITHDRAWN if withdrawn else HELD


def _require_slot(value: object) -> str:
    if type(value) is not str:
        raise FailClosedError(f"slot must be a str: {value!r}")
    _refuse_send_sealed(value, what="slot")
    text = value.strip()
    if not text:
        raise FailClosedError("slot is empty")
    return text


def _require_subject_text(value: object) -> str:
    kind = classify_subject(value)
    if kind is None:
        raise FailClosedError("subject missing — UNKNOWN is not a bind")
    if type(value) is not str:
        raise FailClosedError(f"subject must be a str: {value!r}")
    text = value.strip()
    if kind == READY:
        return READY
    return text


@dataclass(frozen=True)
class RevokeBind:
    """One intent + family + subject_kind + subject + slot.

    Frozen so a later write cannot silently retcon a withdrawn
    ready hold into send_authorized.
    """

    intent: str
    family: str
    subject_kind: str
    subject: str
    slot: str


def bind_revoke(
    intent: object,
    subject: object,
    *,
    withdrawn: object,
    slot: object,
) -> RevokeBind:
    """Require every side. Missing fails closed (use try_bind).

    Explicit bind is not try_bind: absence is not softened to
    UNKNOWN here.
    """
    klass = classify_intent(intent)
    if klass == UNKNOWN:
        raise FailClosedError("intent missing — UNKNOWN is not a bind")
    kind = classify_subject(subject)
    if kind is None:
        raise FailClosedError("subject missing — UNKNOWN is not a bind")
    family = classify_family(withdrawn, timeout=False)
    if family is None:
        raise FailClosedError(
            "withdrawn missing — UNKNOWN is not a bind")
    key = _require_slot(slot)
    text = _require_subject_text(subject)
    return RevokeBind(
        intent=klass,
        family=family,
        subject_kind=kind,
        subject=text,
        slot=key,
    )


def try_bind(
    intent: object,
    subject: object,
    *,
    withdrawn: object,
    slot: object,
) -> Optional[RevokeBind]:
    """Missing intent, subject, withdrawn, or slot is UNKNOWN (None).

    None is not FALSE. A present-but-bad value still fails closed —
    unknown shape is not a default family.
    """
    if (
        intent is None
        or subject is None
        or withdrawn is None
        or slot is None
    ):
        return None
    return bind_revoke(
        intent, subject, withdrawn=withdrawn, slot=slot)


def admit_revoke(
    intent: object,
    subject: object,
    *,
    withdrawn: object = False,
    halted: object = False,
    timeout: object = False,
) -> Optional[bool]:
    """True when the intent may proceed.

    Missing intent or subject is UNKNOWN (None), not False.
    classify / observe / revoke continue under HALT. issue is
    refused when halted. Timeout is UNKNOWN (None) and does not
    prove a writer. A send name never reaches True — it fails
    closed at classify. halted / timeout must be exact bools.
    withdrawn already True does not grant a send; revoke of an
    already-withdrawn hold is False (measured, not missing).
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
    kind = classify_subject(subject)
    if kind is None:
        return None
    family = classify_family(withdrawn, timeout=False)
    if family is None:
        return None
    if klass == ISSUE:
        return not halted
    if klass == REVOKE:
        return family == HELD
    return True
