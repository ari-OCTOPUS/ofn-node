"""PAINT-L5-001 first follow-up — two-step confirm, dry_run default.

D-28 authorizes a real painting follow-up under the daily cap. This
module will not send from a host that is not the lead body. A missing
second confirmation is a refusal, not a send. Partner voices do not
gate this path.
"""

from __future__ import annotations

from typing import Any, Mapping

from ofn.config import D27_DAILY_SEND_CAP
from ofn.kernel.release_switch import RULE_OWNER_TWO_STEP

MISSION = "PAINT-L5-001"
RULE_NOT_ON_BODY = "paint:body_not_on_this_host"
RULE_DRY_RUN = "paint:dry-run"
RULE_CAP = "paint:send-cap"


class PaintFollowUpError(ValueError):
    """Follow-up refused. Nothing left the machine."""


def propose_follow_up(
    *,
    lead_id: str,
    body: str,
    owner_step1: bool,
    owner_step2: bool,
    dry_run: bool = True,
    sends_today: int = 0,
    on_lead_body: bool = False,
    daily_send_cap: int = D27_DAILY_SEND_CAP,
) -> dict[str, Any]:
    """Draft or refuse a painting follow-up. Never invents a send receipt."""
    if not lead_id or not str(lead_id).strip():
        raise PaintFollowUpError("paint:lead-id-required")
    if not (body or "").strip():
        raise PaintFollowUpError("paint:empty-body")
    if not (owner_step1 and owner_step2):
        raise PaintFollowUpError(RULE_OWNER_TWO_STEP)
    if sends_today >= daily_send_cap:
        raise PaintFollowUpError(RULE_CAP)
    if dry_run:
        return {
            "ok": True,
            "mission": MISSION,
            "lead_id": lead_id,
            "rule": RULE_DRY_RUN,
            "dry_run": True,
            "sent": False,
            "body": body,
        }
    if not on_lead_body:
        raise PaintFollowUpError(RULE_NOT_ON_BODY)
    raise PaintFollowUpError(RULE_NOT_ON_BODY)


def as_episode_fields(draft: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "decision": "follow_up",
        "proposed_action": {
            "kind": "paint_follow_up",
            "lead_id": draft.get("lead_id"),
            "dry_run": True,
            "sent": False,
        },
    }
