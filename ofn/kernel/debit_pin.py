"""Debit pin — pair a classified ref with a one-verdict budget effect.

A debit pin records that a VERIFIED ``evt-`` ref may be the subject
of a FIRST budget effect. It does not write the store and does not
hash a body. A second debit against the same prior receipt is
refused (``second_debit``). Missing ref is UNKNOWN (None), not FALSE.

A debit never grants a send. ``campaign_envelope_ready`` cannot be
pinned into ``send_authorized``. A pin is not an
``EXECUTION_RECEIPT`` and is not a chain tip.

Timeout is UNKNOWN. It does not prove concurrent writing and it
does not invent a debit.

Not wired into the run store. Pinning a debit is not
``send_authorized``, ``quote_sent``, or
``campaign_envelope_ready``. Ready is not authorized.

HALT stops STARTS. This module has no halt parameter: pinning a
debit against an in-flight receipt is not a run start.

Kernel purity: dataclasses + typing. No hashlib of bodies, no I/O,
no clock, no now().
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .errors import FailClosedError
from .event_id import EVENT_ID_RE
from .events import PROPOSAL_CREATED, is_forbidden_effect_name
from .ref_class import (
    CLASSES as REF_CLASSES,
    admit_ref,
    classify_ref,
)

# Closed vocabularies. Widen only with a test.
DEBIT_CLASSES = frozenset({"FIRST", "UNKNOWN"})
REFUSAL_REASONS = frozenset({
    "sealed_effect",
    "proposal_not_receipt",
    "second_debit",
})

_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
    "send-authorized",
    "quote-sent",
    "campaign-envelope-ready",
})


def grants_send() -> bool:
    """A debit pin never authorizes a send. Structurally False."""
    return False


def halt_blocks_pin() -> bool:
    """Structurally False. HALT stops STARTS, not a pin."""
    return False


def unknown_is_false() -> bool:
    """Structurally False. UNKNOWN is not FALSE."""
    return False


def claims_immutable() -> bool:
    """Structurally False. A pin is not chattr +i."""
    return False


def ready_is_authorized() -> bool:
    """Structurally False. campaign_envelope_ready ≠ send_authorized."""
    return False


def proposal_is_execution() -> bool:
    """Structurally False. A proposal cannot be a debit subject."""
    return False


def timeout_proves_concurrent() -> bool:
    """Structurally False. A timeout is UNKNOWN, not a race."""
    return False


def wires_into_run_store() -> bool:
    """Structurally False. This pin is not wired into the store."""
    return False


def invents_debit() -> bool:
    """Structurally False. A pin records a classified ref; it does not mint."""
    return False


def promotes_ready_to_send() -> bool:
    """Structurally False. Ready stays ready."""
    return False


def burns_idempotency_key() -> bool:
    """Structurally False. A pin does not consume a key."""
    return False


def second_debit_is_first() -> bool:
    """Structurally False. One verdict → one budget effect."""
    return False


def later_disarm_supersedes() -> bool:
    """Structurally True. A later hold/disarm beats older authorization."""
    return True


def classify_timeout() -> str:
    """A timeout is UNKNOWN. It does not prove concurrent writing."""
    return "UNKNOWN"


def _fold_name(name: str) -> str:
    return name.strip().lower().replace("-", "_")


def _is_sealed(name: object) -> bool:
    if type(name) is not str:
        return False
    if is_forbidden_effect_name(name):
        return True
    return _fold_name(name) in {s.replace("-", "_") for s in _SEALED}


def _is_proposal_name(name: object) -> bool:
    if type(name) is not str:
        return False
    return _fold_name(name) == _fold_name(PROPOSAL_CREATED)


def classify_debit(
    ref: object,
    *,
    prior_debit: bool = False,
) -> Optional[str]:
    """FIRST or UNKNOWN (None). Missing is UNKNOWN.

    ``prior_debit=True`` is a known second-debit, not a class.
    Sealed send/ready names fail closed. Proposal names fail closed.
    Present-but-bad event_id still fails closed (shape error).
    """
    if type(prior_debit) is not bool:
        raise FailClosedError(
            f"prior_debit must be exact bool: {prior_debit!r}")
    if prior_debit:
        raise FailClosedError(
            "second BUDGET_DEBIT against the same prior receipt — "
            "one verdict maps to one budget effect")
    if ref is None:
        return None
    klass = classify_ref(ref)
    if klass is None:
        return None
    if klass not in REF_CLASSES:
        raise FailClosedError("ref class drifted")
    if type(ref) is not str:
        raise FailClosedError("debit ref must be str when classified")
    return "FIRST"


@dataclass(frozen=True)
class DebitPin:
    """One ref + one-verdict pin. Frozen so a later write cannot
    silently retcon the pin into send_authorized or a second debit.
    """

    ref: Optional[str]
    debit_class: str
    allowed: bool
    reason: Optional[str]
    timed_out: bool
    prior_debit: bool
    grants_send: bool = False

    def __post_init__(self) -> None:
        if self.grants_send:
            raise FailClosedError(
                "DebitPin cannot grant send_authorized / quote_sent / "
                "campaign_envelope_ready — a debit is not a send")
        if type(self.timed_out) is not bool:
            raise FailClosedError(
                f"timed_out must be exact bool: {self.timed_out!r}")
        if type(self.prior_debit) is not bool:
            raise FailClosedError(
                f"prior_debit must be exact bool: {self.prior_debit!r}")
        if self.debit_class not in DEBIT_CLASSES:
            raise FailClosedError(
                f"unknown debit class: {self.debit_class!r}")
        if self.allowed:
            if self.reason is not None:
                raise FailClosedError(
                    f"allowed debit must not carry a reason: {self.reason!r}")
            if self.prior_debit:
                raise FailClosedError(
                    "allowed debit cannot record prior_debit — "
                    "one verdict maps to one budget effect")
        else:
            if self.reason not in REFUSAL_REASONS:
                raise FailClosedError(
                    f"unknown or missing refusal reason: {self.reason!r}")
            if self.reason == "second_debit" and not self.prior_debit:
                raise FailClosedError(
                    "second_debit refusal requires prior_debit=True")
        if self.ref is not None:
            if type(self.ref) is not str:
                raise FailClosedError("ref must be a str or None")
            if _is_sealed(self.ref):
                if self.allowed or self.reason != "sealed_effect":
                    raise FailClosedError(
                        "sealed name may appear only as a sealed_effect "
                        "subject")
            elif _is_proposal_name(self.ref):
                if self.allowed or self.reason != "proposal_not_receipt":
                    raise FailClosedError(
                        "proposal name may appear only as a "
                        "proposal_not_receipt subject")
            elif not EVENT_ID_RE.match(self.ref):
                raise FailClosedError(
                    f"ref must be evt- + 16 lowercase hex: {self.ref!r}")
        if self.debit_class == "FIRST":
            if self.ref is None:
                raise FailClosedError("FIRST requires a recorded ref")
            if self.timed_out:
                raise FailClosedError("timed-out debit cannot be FIRST")
            if not self.allowed:
                raise FailClosedError("FIRST must be allowed")
        if self.debit_class == "UNKNOWN" and not self.timed_out:
            if (
                self.allowed
                and self.ref is not None
                and not _is_sealed(self.ref)
                and not _is_proposal_name(self.ref)
            ):
                raise FailClosedError(
                    "a present event_id cannot be UNKNOWN without timeout")


def pin_debit(
    ref: object,
    *,
    timed_out: bool = False,
    prior_debit: bool = False,
) -> DebitPin:
    """Pin a classified ref as a one-verdict budget-effect subject.

    Missing ref is UNKNOWN and admitted. A sealed send/ready name
    is a known refusal (``sealed_effect``). A proposal kind name is
    a known refusal (``proposal_not_receipt``). ``prior_debit=True``
    is a known refusal (``second_debit``). Timeout forces UNKNOWN
    and does not invent a debit.

    Signature is sealed: no ``halt``, no ``send_authorized``, no
    ``resend``. Tests lock the parameter list.
    """
    if type(timed_out) is not bool:
        raise FailClosedError(f"timed_out must be exact bool: {timed_out!r}")
    if type(prior_debit) is not bool:
        raise FailClosedError(
            f"prior_debit must be exact bool: {prior_debit!r}")

    if _is_sealed(ref):
        if type(ref) is not str:
            raise FailClosedError(f"sealed debit ref must be a str: {ref!r}")
        return DebitPin(
            ref=ref,
            debit_class="UNKNOWN",
            allowed=False,
            reason="sealed_effect",
            timed_out=timed_out,
            prior_debit=prior_debit,
        )

    if _is_proposal_name(ref):
        if type(ref) is not str:
            raise FailClosedError(
                f"proposal debit ref must be a str: {ref!r}")
        return DebitPin(
            ref=ref,
            debit_class="UNKNOWN",
            allowed=False,
            reason="proposal_not_receipt",
            timed_out=timed_out,
            prior_debit=prior_debit,
        )

    if prior_debit:
        rec = ref if type(ref) is str else None
        if rec is not None and not EVENT_ID_RE.match(rec):
            # Shape still fails closed — a bad id is not a second debit.
            classify_ref(ref)
        return DebitPin(
            ref=rec if rec is None or EVENT_ID_RE.match(rec) else None,
            debit_class="UNKNOWN",
            allowed=False,
            reason="second_debit",
            timed_out=timed_out,
            prior_debit=True,
        )

    dec = admit_ref(ref, timed_out=False)
    if not dec.allowed:
        raise FailClosedError("ref side refused — debit is not a send")

    if ref is None:
        return DebitPin(
            ref=dec.ref,
            debit_class="UNKNOWN",
            allowed=True,
            reason=None,
            timed_out=timed_out,
            prior_debit=False,
        )

    if timed_out:
        return DebitPin(
            ref=dec.ref,
            debit_class="UNKNOWN",
            allowed=True,
            reason=None,
            timed_out=True,
            prior_debit=False,
        )

    klass = classify_debit(ref, prior_debit=False)
    if klass is None:
        return DebitPin(
            ref=dec.ref,
            debit_class="UNKNOWN",
            allowed=True,
            reason=None,
            timed_out=False,
            prior_debit=False,
        )
    return DebitPin(
        ref=dec.ref,
        debit_class=klass,
        allowed=True,
        reason=None,
        timed_out=False,
        prior_debit=False,
    )


def try_pin(ref: object) -> Optional[DebitPin]:
    """Missing ref is UNKNOWN (None). Present-but-bad fails closed."""
    if ref is None:
        return None
    return pin_debit(ref)
