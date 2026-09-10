"""Fail-closed gates for publish, external send, and LLM use."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


class GateError(PermissionError):
    pass


@dataclass(frozen=True)
class GatePolicy:
    publish: bool = False
    external_send: Any = "none"
    hold_external: bool = True
    use_llm: bool = False
    safe_to_claim: bool = False

    def check(self) -> None:
        if self.publish:
            raise GateError("publish_blocked_fail_closed")
        if self.use_llm:
            raise GateError("use_llm_blocked_fail_closed")
        if self.external_send not in (None, False, "none", "", 0):
            raise GateError("external_send_blocked_fail_closed")
        if self.hold_external and self.external_send not in (None, False, "none", "", 0):
            raise GateError("hold_external_blocks_send")
        if self.safe_to_claim:
            raise GateError("safe_to_claim_must_remain_false_until_owner_complete")

    def assert_no_external_send(self) -> None:
        if self.hold_external:
            if self.external_send not in (None, False, "none", "", 0):
                raise GateError("hold_external_blocks_send")
        else:
            # even without hold, default fail-closed in this package
            if self.external_send not in (None, False, "none", "", 0):
                raise GateError("external_send_blocked_fail_closed")


DEFAULT_LOCKS = GatePolicy(
    publish=False,
    external_send="none",
    hold_external=True,
    use_llm=False,
    safe_to_claim=False,
)


def enforce_locks(locks: Optional[dict] = None) -> GatePolicy:
    locks = locks or {}
    policy = GatePolicy(
        publish=bool(locks.get("publish", False)),
        external_send=locks.get("external_send", "none"),
        hold_external=bool(locks.get("hold_external", True)),
        use_llm=bool(locks.get("use_llm", False)),
        safe_to_claim=bool(
            locks.get("safe_to_claim", locks.get("safe_to_claim_live_executable_contract", False))
        ),
    )
    policy.check()
    return policy
