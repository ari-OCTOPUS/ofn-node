"""Cycle state machine — fail-closed for publish/external."""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional


class CycleState(str, Enum):
    DISCOVERED = "DISCOVERED"
    BASELINED = "BASELINED"
    VALIDATING = "VALIDATING"
    OWNER_INPUT_REQUIRED = "OWNER_INPUT_REQUIRED"
    READY_INTERNAL = "READY_INTERNAL"
    VERIFYING = "VERIFYING"
    PASS_INTERNAL = "PASS_INTERNAL"
    PASS_WITH_CAVEAT = "PASS_WITH_CAVEAT"
    HOLD_EXTERNAL = "HOLD_EXTERNAL"
    READY_FOR_OWNER_REVIEW = "READY_FOR_OWNER_REVIEW"
    FAILED_RECOVERABLE = "FAILED_RECOVERABLE"
    FAILED_BLOCKING = "FAILED_BLOCKING"


ALLOWED: dict[CycleState, set[CycleState]] = {
    CycleState.DISCOVERED: {CycleState.BASELINED, CycleState.FAILED_BLOCKING},
    CycleState.BASELINED: {CycleState.VALIDATING, CycleState.FAILED_RECOVERABLE},
    CycleState.VALIDATING: {
        CycleState.OWNER_INPUT_REQUIRED,
        CycleState.READY_INTERNAL,
        CycleState.FAILED_RECOVERABLE,
        CycleState.FAILED_BLOCKING,
    },
    CycleState.OWNER_INPUT_REQUIRED: {
        CycleState.VALIDATING,
        CycleState.READY_FOR_OWNER_REVIEW,
        CycleState.HOLD_EXTERNAL,
        CycleState.FAILED_RECOVERABLE,
    },
    CycleState.READY_INTERNAL: {
        CycleState.VERIFYING,
        CycleState.HOLD_EXTERNAL,
        CycleState.FAILED_RECOVERABLE,
    },
    CycleState.VERIFYING: {
        CycleState.PASS_INTERNAL,
        CycleState.PASS_WITH_CAVEAT,
        CycleState.OWNER_INPUT_REQUIRED,
        CycleState.HOLD_EXTERNAL,
        CycleState.FAILED_RECOVERABLE,
        CycleState.FAILED_BLOCKING,
    },
    CycleState.PASS_INTERNAL: {CycleState.HOLD_EXTERNAL, CycleState.READY_FOR_OWNER_REVIEW},
    CycleState.PASS_WITH_CAVEAT: {CycleState.HOLD_EXTERNAL, CycleState.OWNER_INPUT_REQUIRED},
    CycleState.HOLD_EXTERNAL: {CycleState.READY_FOR_OWNER_REVIEW, CycleState.FAILED_BLOCKING},
    CycleState.READY_FOR_OWNER_REVIEW: {CycleState.VALIDATING, CycleState.HOLD_EXTERNAL},
    CycleState.FAILED_RECOVERABLE: {CycleState.DISCOVERED, CycleState.VALIDATING},
    CycleState.FAILED_BLOCKING: set(),
}


class TransitionError(ValueError):
    pass


class StateMachine:
    def __init__(self, state: CycleState = CycleState.DISCOVERED):
        self.state = state

    def can_transition(self, new_state: CycleState) -> bool:
        return new_state in ALLOWED.get(self.state, set())

    def transition(self, new_state: CycleState) -> CycleState:
        if not self.can_transition(new_state):
            raise TransitionError(f"illegal_transition:{self.state.value}->{new_state.value}")
        self.state = new_state
        return self.state

    def assert_fail_closed_publish(self, publish: bool) -> None:
        if publish:
            raise TransitionError("publish_fail_closed")

    def assert_fail_closed_external(self, external_send: Any = None) -> None:
        if external_send not in (None, False, "none", "", 0):
            raise TransitionError("external_send_fail_closed")
