from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PolicyDecision:
    recommendation: str
    executable: bool
    reason: str
    profile: str
    authority: str
    advisory: dict[str, Any] | None


class Wave0ObserveOnlyPolicy:
    PROFILE = "WAVE0_OBSERVE_ONLY"
    AUTHORITY = "NONE"

    def decide(
        self,
        state: dict[str, float],
        metacontrol_advisory: dict[str, Any] | None = None,
    ) -> PolicyDecision:
        del state
        if metacontrol_advisory is None:
            return PolicyDecision(
                recommendation="NO_ACTION",
                executable=False,
                reason="observe_only",
                profile=self.PROFILE,
                authority=self.AUTHORITY,
                advisory=None,
            )
        recommendation = metacontrol_advisory.get("recommendation", "NO_ACTION")
        return PolicyDecision(
            recommendation="NO_ACTION",
            executable=False,
            reason=f"denied_observe_only:{recommendation}",
            profile=self.PROFILE,
            authority=self.AUTHORITY,
            advisory=metacontrol_advisory,
        )
