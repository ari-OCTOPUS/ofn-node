"""Codec class — kernel-pure encode/inspect/replay admission.

``events.make_event`` owns the factory. ``typed_event`` owns record
shape. ``receipts`` owns the receipt body. This module is the third
witness: may a payload be encoded, inspected, or replayed under a
named codec?

``encode`` is a START. HALT refuses it. ``inspect`` and ``replay``
are not STARTS — HALT does not block them. This module does not
produce encoded bytes and does not write a ledger.

A sealed send/ready name is never a codec, never an intent, and
never a payload. ``campaign_envelope_ready`` is structurally
distinct from ``send_authorized``; both are refused as
``sealed_effect``. Encoding does not grant a send.

Timeout is UNKNOWN. It does not prove concurrent writing and it
does not encode.

Unknown codec is not FALSE and is not a grant — it fails closed.
Width, when supplied, must be an exact int matching payload
length. Bool/str/float widths fail closed.

Not wired into the run store. Admitting an inspect or replay is
not ``send_authorized``, ``quote_sent``, or
``campaign_envelope_ready``. Ready is not authorized.

Distinct from typed_event, receipt_bind, envelope_class,
store_class, receipts, and dedup.

Kernel purity: typing + dataclasses. No json, no clock, no I/O.
This file must not name a business or product.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .envelope import is_sealed_tool_name
from .errors import FailClosedError
from .events import is_forbidden_effect_name

# Closed vocabularies. Widen only with a test.
INTENTS = frozenset({"encode", "inspect", "replay"})
CODECS = frozenset({"utf8", "hex", "ascii"})
STATUSES = frozenset({"VERIFIED", "SUSPECTED", "UNKNOWN"})
ACTIVITIES = frozenset({"idle", "concurrent", "unknown"})
REFUSAL_REASONS = frozenset({
    "sealed_effect",
    "halt_active",
    "unknown_codec",
    "empty_payload",
    "width_mismatch",
    "unknown_activity",
    "suspected_concurrent",
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
    """A codec class never authorizes a send. Structurally False."""
    return False


def halt_blocks_inspect() -> bool:
    """Structurally False. HALT stops STARTS, not inspect/replay."""
    return False


def encodes_bytes() -> bool:
    """Structurally False. This classifies. It does not encode."""
    return False


def ready_is_authorized() -> bool:
    """Structurally False. Ready and authorized are different names."""
    return False


def claims_immutable() -> bool:
    """Structurally False. A codec verdict is not chattr +i."""
    return False


def unknown_is_false() -> bool:
    """Structurally False. UNKNOWN is not FALSE."""
    return False


def timeout_proves_concurrent() -> bool:
    """Structurally False. A timeout is UNKNOWN, not a race."""
    return False


def proposal_is_execution() -> bool:
    """Structurally False. Classifying a codec is not an external effect."""
    return False


def promotes_ready_to_send() -> bool:
    """Structurally False. Ready stays ready."""
    return False


def wires_into_run_store() -> bool:
    """Structurally False. Complementary; not imported by the store."""
    return False


def classify_timeout() -> str:
    """A timeout is UNKNOWN. It does not prove concurrent writing."""
    return "UNKNOWN"


def _fold(name: str) -> str:
    return name.strip().lower().replace("-", "_")


def _is_sealed(name: object) -> bool:
    if not isinstance(name, str):
        return False
    if is_forbidden_effect_name(name):
        return True
    if is_sealed_tool_name(name):
        return True
    return _fold(name) in {_fold(s) for s in _SEALED}


def _require_name(value: object, *, what: str) -> str:
    if isinstance(value, bool) or not isinstance(value, str) or not value.strip():
        raise FailClosedError(f"{what} must be a non-empty name: {value!r}")
    return value.strip()


def _require_member(value: object, *, what: str, allowed: frozenset[str]) -> str:
    name = _require_name(value, what=what)
    if name not in allowed:
        raise FailClosedError(
            f"unknown {what} is not a refusal and not a grant: {name!r}")
    return name


def _require_payload(value: object) -> str:
    if isinstance(value, bool) or not isinstance(value, str):
        raise FailClosedError(
            f"payload must be a str, not a grant: {value!r}")
    if _is_sealed(value):
        raise FailClosedError(
            "payload cannot be a sealed send/ready name")
    return value


def classify_status(*, activity: str, timed_out: bool) -> str:
    """Derive the codec-row status. Timeout outranks activity.

    A timeout is UNKNOWN even when activity says concurrent.
    That is the load-bearing rule: timeout does not prove a race.
    """
    if timed_out:
        return "UNKNOWN"
    if activity == "unknown":
        return "UNKNOWN"
    if activity == "concurrent":
        return "SUSPECTED"
    if activity == "idle":
        return "VERIFIED"
    raise FailClosedError(
        f"unknown activity is not a refusal and not a grant: {activity!r}")


@dataclass(frozen=True)
class CodecDecision:
    """The codec-admission verdict. ``grants_send`` is structurally False.

    Two independent claims live on the same object so a silent default
    cannot masquerade as an authorization: ``allowed`` and
    ``grants_send`` are both recorded, and the constructor refuses
    ``grants_send=True``.
    """

    allowed: bool
    reason: Optional[str]
    status: str
    intended: str
    codec: str
    timed_out: bool
    grants_send: bool = False

    def __post_init__(self) -> None:
        if self.grants_send:
            raise FailClosedError(
                "CodecDecision cannot grant send_authorized / quote_sent / "
                "campaign_envelope_ready — a codec class is not a send")
        if self.status not in STATUSES:
            raise FailClosedError(
                f"unknown codec status is not a refusal and not a grant: "
                f"{self.status!r}")
        if self.intended not in INTENTS:
            raise FailClosedError(
                f"unknown or missing intended: {self.intended!r}")
        if type(self.timed_out) is not bool:
            raise FailClosedError(
                f"timed_out must be an exact bool: {self.timed_out!r}")
        object.__setattr__(self, "codec", _require_name(self.codec, what="codec"))
        if self.allowed:
            if self.reason is not None:
                raise FailClosedError(
                    f"allowed codec must not carry a reason: {self.reason!r}")
            if self.intended == "encode" and self.status != "VERIFIED":
                raise FailClosedError(
                    "CodecDecision cannot allow an encode unless VERIFIED")
        else:
            if self.reason not in REFUSAL_REASONS:
                raise FailClosedError(
                    f"unknown or missing refusal reason: {self.reason!r}")
        if _is_sealed(self.codec) or _is_sealed(self.intended):
            if self.allowed or self.reason != "sealed_effect":
                raise FailClosedError(
                    "CodecDecision cannot grant or mis-label a sealed "
                    "send/ready name")


def admit_codec(
    *,
    intended: object,
    codec: object,
    payload: object,
    width: object = None,
    activity: object = "idle",
    halted: object = False,
    timed_out: object = False,
) -> CodecDecision:
    """May this payload be encoded, inspected, or replayed?

    ``intended``, ``codec``, and ``payload`` are required.
    Unknown names fail closed — UNKNOWN is not FALSE and is not
    admitted as idle.

    ``width``, when not None, must be exact int matching
    ``len(payload)``. Bool/str/float fail closed.

    ``halted`` and ``timed_out`` must be exact bools. HALT refuses
    ``encode`` only. Timeout forces status UNKNOWN and refuses
    encode; it does not classify the row as SUSPECTED.

    Signature is sealed: no ``resend``, no ``send_authorized``.
    Tests lock the parameter list; the kernel does not import inspect.
    """
    raw_intent = _require_name(intended, what="intended")
    raw_codec = _require_name(codec, what="codec")
    raw_payload = _require_payload(payload)
    activity_name = _require_member(
        activity, what="activity", allowed=ACTIVITIES)
    if type(halted) is not bool:
        raise FailClosedError(f"halted must be an exact bool: {halted!r}")
    if type(timed_out) is not bool:
        raise FailClosedError(
            f"timed_out must be an exact bool: {timed_out!r}")
    if width is not None and type(width) is not int:
        raise FailClosedError(f"width must be an exact int: {width!r}")

    if _is_sealed(raw_intent) or _is_sealed(raw_codec):
        return CodecDecision(
            allowed=False,
            reason="sealed_effect",
            status=classify_status(activity=activity_name, timed_out=timed_out),
            intended=raw_intent if raw_intent in INTENTS else "inspect",
            codec=raw_codec,
            timed_out=timed_out,
        )

    intent = _require_member(raw_intent, what="intended", allowed=INTENTS)
    status = classify_status(activity=activity_name, timed_out=timed_out)

    if raw_codec not in CODECS:
        return CodecDecision(
            allowed=False,
            reason="unknown_codec",
            status=status,
            intended=intent,
            codec=raw_codec,
            timed_out=timed_out,
        )

    if raw_payload == "":
        return CodecDecision(
            allowed=False,
            reason="empty_payload",
            status=status,
            intended=intent,
            codec=raw_codec,
            timed_out=timed_out,
        )

    if width is not None and width != len(raw_payload):
        return CodecDecision(
            allowed=False,
            reason="width_mismatch",
            status=status,
            intended=intent,
            codec=raw_codec,
            timed_out=timed_out,
        )

    if intent == "encode" and halted:
        return CodecDecision(
            allowed=False,
            reason="halt_active",
            status=status,
            intended=intent,
            codec=raw_codec,
            timed_out=timed_out,
        )

    if intent == "encode":
        if status == "UNKNOWN":
            return CodecDecision(
                allowed=False,
                reason="unknown_activity",
                status=status,
                intended=intent,
                codec=raw_codec,
                timed_out=timed_out,
            )
        if status == "SUSPECTED":
            return CodecDecision(
                allowed=False,
                reason="suspected_concurrent",
                status=status,
                intended=intent,
                codec=raw_codec,
                timed_out=timed_out,
            )

    return CodecDecision(
        allowed=True,
        reason=None,
        status=status,
        intended=intent,
        codec=raw_codec,
        timed_out=timed_out,
    )
