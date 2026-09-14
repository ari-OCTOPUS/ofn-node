"""Classify an idempotency key. Missing is UNKNOWN, not empty/FALSE.

A sealed send/ready name is never a key. Binding a key is not
burning it, not authorizing a send, and not promoting
campaign_envelope_ready to send_authorized.

Distinct from idempotency.py (envelope contract hash),
receipts.py, dedup.py, write_fence.py, and campaign_bind.
Not wired into run_store.py. HALT stops STARTS, not a bind.

Kernel purity: dataclasses + typing. No I/O, no clock, no now().
This file must not name a business or product.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .envelope import is_sealed_tool_name
from .errors import FailClosedError
from .events import is_forbidden_effect_name

KEY_BOUND = "KEY_BOUND"
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
    """A key class never authorizes a send. Structurally False."""
    return False


def halt_blocks_bind() -> bool:
    """Structurally False. HALT stops STARTS, not this bind."""
    return False


def unknown_is_false() -> bool:
    """Structurally False. UNKNOWN is not FALSE."""
    return False


def ready_is_authorized() -> bool:
    """Structurally False. campaign_envelope_ready ≠ send_authorized."""
    return False


def promotes_ready_to_send() -> bool:
    """Structurally False. A key bind is not a rename of authorized."""
    return False


def burns_key() -> bool:
    """Structurally False. Classification does not consume the key."""
    return False


def claims_immutable() -> bool:
    """Structurally False. A bind is not filesystem immutability."""
    return False


def timeout_proves_concurrent_write() -> bool:
    """Structurally False. Timeout is UNKNOWN, not a writer."""
    return False


def proposal_is_execution() -> bool:
    """Structurally False. Binding a key is not an external effect."""
    return False


def _fold(value: str) -> str:
    return value.strip().lower().replace("-", "_")


def is_sealed_key(name: object) -> bool:
    """True only for sealed send/ready names. UNKNOWN names stay unknown."""
    if not isinstance(name, str):
        return False
    if is_forbidden_effect_name(name):
        return True
    folded = _fold(name)
    if is_forbidden_effect_name(folded) or is_sealed_tool_name(name):
        return True
    return folded in {_fold(s) for s in _SEALED}


def classify_key(value: object) -> str:
    """KEY_BOUND or UNKNOWN. Missing is UNKNOWN, not FALSE.

    send_authorized / quote_sent / campaign_envelope_ready fail
    closed — they are not a missing classification and they are
    not a key. An unknown present non-string fails closed
    (shape error), not UNKNOWN.
    """
    if value is None:
        return UNKNOWN
    if type(value) is not str:
        raise FailClosedError(f"key must be a str or None: {value!r}")
    if not value.strip():
        raise FailClosedError("key is empty")
    if is_sealed_key(value):
        raise FailClosedError(
            f"key names a sealed send/ready state: {value!r} — "
            "a key is not a send")
    return KEY_BOUND


@dataclass(frozen=True)
class KeyBind:
    """One caller-chosen key. Frozen so a later write cannot
    silently retcon it into send_authorized.
    """

    key: str
    key_class: str

    def __post_init__(self) -> None:
        if self.key_class != KEY_BOUND:
            raise FailClosedError(
                f"KeyBind key_class must be KEY_BOUND: {self.key_class!r}")
        if type(self.key) is not str or not self.key.strip():
            raise FailClosedError(f"KeyBind key must be a non-empty str: {self.key!r}")
        if is_sealed_key(self.key):
            raise FailClosedError(
                "KeyBind cannot carry a sealed send/ready name")
        object.__setattr__(self, "key", self.key.strip())


def bind_key(value: object) -> KeyBind:
    """Require KEY_BOUND. Missing fails closed (use try_bind)."""
    klass = classify_key(value)
    if klass == UNKNOWN:
        raise FailClosedError(
            "key missing — UNKNOWN is not a key bind")
    if type(value) is not str:
        raise FailClosedError(f"key must be a str: {value!r}")
    return KeyBind(key=value.strip(), key_class=KEY_BOUND)


def try_bind(value: object) -> Optional[KeyBind]:
    """Missing is UNKNOWN (None). Present-but-bad still fails closed."""
    if value is None:
        return None
    return bind_key(value)
