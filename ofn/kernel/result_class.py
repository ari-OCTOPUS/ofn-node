"""Classify a four-state effect result without granting a send.

passed / rejected / failed / unknown are labels of an already-bounded
attempt. They are not send_authorized and not quote_sent.

Missing is UNKNOWN (None), not FALSE. Classification never grants a
send and never promotes campaign_envelope_ready to authorized.

ok=True with sent=False is a shape error (D7), not a pass.
sent=True is only admissible beside result=passed, and even then
this classifier does not authorize a send.

Distinct from release_pipeline (adapter), send_fence / campaign_bind,
settlement, and receipts. Not wired into run_store.py.
HALT stops STARTS, not this classifier.

Kernel purity: typing only. No I/O, no clock, no now().
"""

from __future__ import annotations

from typing import Optional

from .envelope import is_sealed_tool_name
from .errors import FailClosedError
from .events import is_forbidden_effect_name

PASSED = "passed"
REJECTED = "rejected"
FAILED = "failed"
UNKNOWN = "unknown"

_RESULTS = frozenset({PASSED, REJECTED, FAILED, UNKNOWN})
_SEND = frozenset({
    "send_authorized",
    "quote_sent",
    "send-authorized",
    "quote-sent",
})
_READY = frozenset({
    "campaign_envelope_ready",
    "campaign-envelope-ready",
})


def grants_send() -> bool:
    """A result classifier never authorizes a send. Structurally False."""
    return False


def halt_blocks_classify() -> bool:
    """Structurally False. HALT stops STARTS, not this classifier."""
    return False


def unknown_is_false() -> bool:
    """Structurally False. UNKNOWN is not FALSE."""
    return False


def ready_is_authorized() -> bool:
    """Structurally False. campaign_envelope_ready ≠ send_authorized."""
    return False


def promotes_ready_to_send() -> bool:
    """Structurally False. A classifier is not a rename of authorized."""
    return False


def timeout_proves_concurrent_write() -> bool:
    """Structurally False. Timeout is UNKNOWN, not a writer."""
    return False


def proposal_is_execution() -> bool:
    """Structurally False. A classified result is not an external effect."""
    return False


def claims_immutable() -> bool:
    """Structurally False. A classifier is not filesystem immutability."""
    return False


def wires_into_run_store() -> bool:
    """Structurally False. Not wired into the run store."""
    return False


def _fold(value: str) -> str:
    return value.strip().lower().replace("-", "_")


def _refuse_send_name(value: str, *, what: str) -> None:
    folded = _fold(value)
    if (
        is_forbidden_effect_name(value)
        or is_forbidden_effect_name(folded)
        or is_sealed_tool_name(value)
        or folded in {s.replace("-", "_") for s in _SEND}
        or folded in {s.replace("-", "_") for s in _READY}
    ):
        raise FailClosedError(
            f"{what} names a sealed send/ready state: {value!r} — "
            "a result label is not authorized")


def classify_result(
    result: object,
    *,
    sent: object = None,
    ok: object = None,
) -> Optional[str]:
    """Four-state label, or None when result is missing.

    Missing result is UNKNOWN (None), not FALSE.
    Present-but-bad still fails closed.
    """
    if result is None:
        if sent is True or ok is True:
            raise FailClosedError(
                "result missing while sent/ok is True — "
                "UNKNOWN is not a pass")
        return None
    if type(result) is not str:
        raise FailClosedError(f"result must be a str or None: {result!r}")
    if not result.strip():
        raise FailClosedError("result is empty")
    _refuse_send_name(result, what="result")
    folded = _fold(result)
    if folded not in _RESULTS:
        raise FailClosedError(f"unknown result label: {result!r}")
    if sent is not None and type(sent) is not bool:
        raise FailClosedError(f"sent must be a bool or None: {sent!r}")
    if ok is not None and type(ok) is not bool:
        raise FailClosedError(f"ok must be a bool or None: {ok!r}")
    if ok is True and sent is False:
        raise FailClosedError(
            "ok=True with sent=False is a shape error — not a pass")
    if sent is True and folded != PASSED:
        raise FailClosedError(
            f"sent=True is inadmissible beside result={folded!r}")
    return folded
