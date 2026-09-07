"""Pin a classified codec onto a caller-owned run_id.

The pin records (run_id → codec). Same pair is already_pinned.
A second different codec is codec_conflict. peek never writes.

A pinned encode is not send_authorized. Ready is not authorized.
Missing is UNKNOWN (None), not FALSE.

utf8 is text. hex is digest-form. ascii is seven-bit. Sealed
send/ready names never pin. Encoding does not grant a send.

The pin does not produce encoded bytes and does not write a
ledger. Distinct from typed_event, receipt_bind, envelope_class,
store_class, receipts, dedup, and codec_class admission.
Not wired into run_store.py. HALT stops STARTS, not this pin.

Kernel purity: typing only. No I/O, no clock, no now().
This file must not name a business or product.
"""

from __future__ import annotations

from typing import Dict, Optional

from .codec_class import (
    CODECS,
    admit_codec,
    grants_send as codec_grants_send,
    ready_is_authorized as codec_ready_is_authorized,
)
from .envelope import RUN_ID_RE, is_sealed_tool_name
from .errors import FailClosedError
from .events import is_forbidden_effect_name

FAMILIES = frozenset({"text", "digest", "seven_bit"})

_CODEC_FAMILY = {
    "utf8": "text",
    "hex": "digest",
    "ascii": "seven_bit",
}

_SEALED = frozenset({
    "send_authorized",
    "quote_sent",
    "campaign_envelope_ready",
    "send-authorized",
    "quote-sent",
    "campaign-envelope-ready",
})


def grants_send() -> bool:
    """An encode pin never authorizes a send. Structurally False."""
    return False


def halt_blocks_pin() -> bool:
    """Structurally False. HALT stops STARTS, not this pin."""
    return False


def pin_allows_send() -> bool:
    """Structurally False. A pinned codec is not a send."""
    return False


def ready_is_authorized() -> bool:
    """Structurally False. campaign_envelope_ready ≠ send_authorized."""
    return False


def unknown_is_false() -> bool:
    """Structurally False. UNKNOWN is not FALSE."""
    return False


def timeout_proves_concurrent_write() -> bool:
    """Structurally False. Timeout is UNKNOWN, not a writer."""
    return False


def claims_immutable() -> bool:
    """Structurally False. A pin is not filesystem immutability."""
    return False


def wires_into_run_store() -> bool:
    """Structurally False. Not wired into the run store."""
    return False


def later_disarm_supersedes() -> bool:
    """Structurally True. A later hold/disarm beats older authorization."""
    return True


def produces_encoded_bytes() -> bool:
    """Structurally False. A pin records a name. It does not encode."""
    return False


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


def _run_id(value: object) -> str:
    if type(value) is not str or not RUN_ID_RE.match(value):
        raise FailClosedError(f"run_id required: {value!r}")
    if _is_sealed(value):
        raise FailClosedError(
            "run_id cannot be a sealed send/ready name")
    return value


def _codec(value: object) -> str:
    if _is_sealed(value):
        raise FailClosedError(
            "codec cannot be a sealed send/ready name")
    if type(value) is not str or value not in CODECS:
        raise FailClosedError(
            f"unknown codec is not a refusal and not a grant: {value!r}")
    return value


def pin_family(codec: object) -> Optional[str]:
    """Map a known codec to its family. Unknown codec is None, not FALSE."""
    if codec is None:
        return None
    if _is_sealed(codec):
        raise FailClosedError(
            "sealed send/ready name is not a codec family")
    if type(codec) is not str:
        raise FailClosedError(f"codec must be a str or None: {codec!r}")
    return _CODEC_FAMILY.get(codec)


def pin_allows_encode(codec: object) -> bool:
    """True only for a known codec. Still does not grant a send."""
    if codec is None:
        return False
    if _is_sealed(codec):
        return False
    if type(codec) is not str:
        raise FailClosedError(f"codec must be a str or None: {codec!r}")
    if codec_grants_send() or grants_send():
        raise FailClosedError("codec/pin drifted into granting send")
    return codec in CODECS


class EncodePin:
    """Caller-owned (run_id → codec) map. Replay / peek do not write."""

    def __init__(self) -> None:
        self._pinned: Dict[str, str] = {}

    def peek(self, run_id: object) -> Optional[str]:
        """Read without writing. Missing run is None, not FALSE."""
        rid = _run_id(run_id)
        return self._pinned.get(rid)

    def pin(
        self,
        run_id: object,
        codec: object,
        *,
        timeout: object = False,
    ) -> str:
        """Record a codec. Second same pair is already_pinned."""
        if timeout is True:
            raise FailClosedError(
                "timeout is UNKNOWN — UNKNOWN is not a pin")
        if type(timeout) is not bool:
            raise FailClosedError(
                f"timeout must be an exact bool: {timeout!r}")
        rid = _run_id(run_id)
        labeled = _codec(codec)
        if codec_grants_send() or codec_ready_is_authorized():
            raise FailClosedError("codec/pin drifted into send or ready")
        prior = self._pinned.get(rid)
        if prior is None:
            self._pinned[rid] = labeled
            return "pinned"
        if prior == labeled:
            return "already_pinned"
        raise FailClosedError(
            f"codec_conflict run={rid!r} have={prior!r} got={labeled!r}")

    def try_pin(
        self,
        run_id: object,
        codec: object,
        *,
        timeout: object = False,
    ) -> Optional[str]:
        """Missing codec or timeout is UNKNOWN (None). Present-but-bad fails closed."""
        if codec is None or timeout is True:
            return None
        return self.pin(run_id, codec, timeout=timeout)


def pin_ready_stays_ready() -> bool:
    """Structurally True. Ready is never rewritten to authorized."""
    return not ready_is_authorized()


def admit_then_pin(
    *,
    run_id: object,
    intended: object,
    codec: object,
    payload: object,
    pin: EncodePin,
    halted: object = False,
    timed_out: object = False,
) -> Optional[str]:
    """Admit first. A refused encode does not pin. Inspect does not pin.

    Timeout / unknown admission is UNKNOWN (None), not a pin and not
    FALSE. A granted encode pins. Ready is still not authorized.
    """
    decision = admit_codec(
        intended=intended,
        codec=codec,
        payload=payload,
        halted=halted,
        timed_out=timed_out,
    )
    if decision.grants_send or decision.reason == "sealed_effect":
        if decision.grants_send:
            raise FailClosedError("admit drifted into granting send")
        raise FailClosedError(
            "sealed send/ready name is not an encode pin")
    if not decision.allowed or decision.intended != "encode":
        return None
    return pin.pin(run_id, decision.codec, timeout=timed_out)
