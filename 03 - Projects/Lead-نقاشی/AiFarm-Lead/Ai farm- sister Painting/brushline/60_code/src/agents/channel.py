"""
Worker E -- Channel Publisher (KB-01/03).
DRAFT ONLY. Never auto-posts. Prepares channel-ready drafts and, only after a
human APPROVE, produces a publish PREVIEW.

INV-1 (non-negotiable): the ONLY method that could ever "publish" is publish(),
and it refuses unless the draft has an APPROVED ApprovalAction. In this MVP
publish() produces a PREVIEW payload (live_posted=False) -- there is NO live
Google Business Profile / social API call yet (that lands with real OAuth creds).
So there is no code path from draft -> live post that bypasses the Queue.

Channels: gbp (Google Business Profile), social (facebook/instagram).
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from ..config import config
from ..database import get_connection
from ..models import Draft, DraftType
from .. import audit
from ..governance import check_and_enforce
from .base_agent import (
    BaseAgent, AgentCapability, RiskLevel, QualificationStatus, register_agent,
)

# Channel drafting/preview does no LLM/API work in MVP -> ~0 AUD (still gated).
_EST_CHANNEL_DRAFT_AUD = 0.0
_EST_PUBLISH_AUD = 0.0

_DRAFT_TYPE_BY_CHANNEL = {
    "gbp": DraftType.GBP_POST,
    "social": DraftType.CAPTION,
    "facebook": DraftType.CAPTION,
    "instagram": DraftType.CAPTION,
}
_CHANNEL_BY_DRAFT_TYPE = {
    "gbp_post": "gbp",
    "caption": "social",
}


class ChannelError(Exception):
    pass


@register_agent
class ChannelAgent(BaseAgent):
    """Worker E: format content into channel DRAFTS; publish only after APPROVE."""

    AGENT_ID = "E_channel"
    # Worker E is the ONLY agent with publish in scope, but it is HARD-GATED
    # by INV-1 (publish() refuses without an APPROVED ApprovalAction). So we
    # keep "publish" out of ALLOWED and rely on assert_may() + the approval
    # check at the call site. This makes the boundary grep-able: a human can
    # see "publish is forbidden for all agents" and then find the ONE place
    # (publish()) that lifts it via the approval gate.
    ALLOWED_ACTIONS = frozenset({"read", "analyse", "draft", "propose"})
    FORBIDDEN_ACTIONS = frozenset({
        "publish",  # INV-1: only via explicit APPROVED ApprovalAction, not autonomously
        "send", "spend", "pay", "alter_policy", "alter_permissions",
        "expose_pii", "write_canonical_memory", "access_secrets",
    })

    @property
    def role_name(self) -> str:
        return "Worker E — Channel Publisher"

    @property
    def qualification_status(self) -> QualificationStatus:
        return QualificationStatus.TRAINEE

    @property
    def risk_level(self) -> RiskLevel:
        return RiskLevel.YELLOW  # drafts are green, but publish() touches ORANGE

    @property
    def required_inputs(self) -> frozenset[str]:
        return frozenset({"content", "approval"})

    @property
    def capabilities(self) -> tuple[AgentCapability, ...]:
        return (
            AgentCapability("draft_gbp_post", "Draft"),
            AgentCapability("draft_social_post", "Draft"),
            # publish is external_action=True but gated by INV-1 approval
            AgentCapability("publish", "preview", external_action=True),
        )

    def health(self) -> dict:
        return {"ready": True, "detail": "no external deps (MVP preview only)"}

    # -- drafting (DRAFT only -- goes to Gate -> Queue, never posted here) --------

    def draft_gbp_post(self, content: str,
                       cta: str = "Get in touch for a free, no-obligation quote.") -> Draft:
        """Build a Google Business Profile post DRAFT from provided content."""
        return self._draft("gbp", content, cta)

    def draft_social_post(self, content: str, platform: str = "instagram",
                          cta: str = "DM us for a free quote.") -> Draft:
        """Build a social (facebook/instagram) post DRAFT."""
        return self._draft(platform, content, cta)

    def _draft(self, channel: str, content: str, cta: str) -> Draft:
        check_and_enforce(_EST_CHANNEL_DRAFT_AUD, self.AGENT_ID)
        draft_type = _DRAFT_TYPE_BY_CHANNEL.get(channel, DraftType.CAPTION)
        body = self._format(content, cta)
        draft = Draft(
            id=str(uuid.uuid4()),
            draft_type=draft_type,
            content=body,
            agent_id=self.AGENT_ID,
            model_used="E_channel_format",
            created_at=datetime.utcnow(),
        )
        self._save(draft)
        audit.append("DRAFT_CREATED", draft.id, {
            "draft_type": draft_type.value,
            "channel": _CHANNEL_BY_DRAFT_TYPE.get(draft_type.value, channel),
        })
        return draft

    def _format(self, content: str, cta: str) -> str:
        body = (content or "").strip()
        if cta and cta.strip() and cta.strip().lower() not in body.lower():
            body = f"{body}\n\n{cta.strip()}"
        return body

    # -- publish (INV-1 gated; MVP = preview only, no live post) ------------------

    def publish(self, draft_id: str, operator_chat_id: Optional[int] = None) -> dict:
        """
        Produce a publish PREVIEW for an APPROVED draft.

        INV-1: raises ChannelError unless an APPROVED ApprovalAction exists for
        this draft. MVP does NOT post live (live_posted=False) -- it returns the
        channel-ready preview a human/real-API step would use.
        """
        check_and_enforce(_EST_PUBLISH_AUD, self.AGENT_ID)

        approved = self._approved_action(draft_id)
        if not approved:
            raise ChannelError(
                f"INV-1 violation blocked: draft {draft_id} has no APPROVED "
                f"approval action; refusing to publish."
            )
        draft = self._get_draft(draft_id)
        if draft is None:
            raise ChannelError(f"draft {draft_id} not found")

        channel = _CHANNEL_BY_DRAFT_TYPE.get(draft["draft_type"], "unknown")
        preview = {
            "draft_id": draft_id,
            "channel": channel,
            "draft_type": draft["draft_type"],
            "formatted_content": draft["content"],
            "live_posted": False,   # MVP: preview only -- no live channel API yet
            "approval_action_id": approved["id"],
        }
        audit.append("PUBLISH", draft_id, {
            "channel": channel,
            "mode": "preview_only",
            "live_posted": False,
            "approval_action_id": approved["id"],
        })
        return preview

    # -- internals ---------------------------------------------------------------

    def _approved_action(self, draft_id: str) -> Optional[dict]:
        conn = get_connection()
        try:
            row = conn.execute(
                "SELECT * FROM approval_actions WHERE draft_id = ? AND status = 'approved' "
                "ORDER BY rowid DESC LIMIT 1",
                (draft_id,),
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def _get_draft(self, draft_id: str) -> Optional[dict]:
        conn = get_connection()
        try:
            row = conn.execute(
                "SELECT * FROM drafts WHERE id = ?", (draft_id,)
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def _save(self, draft: Draft) -> None:
        conn = get_connection()
        try:
            conn.execute(
                """INSERT INTO drafts
                   (id, lead_id, draft_type, content, agent_id, model_used,
                    tokens_in, tokens_out, cost_usd, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (draft.id, draft.lead_id, draft.draft_type.value, draft.content,
                 draft.agent_id, draft.model_used, draft.tokens_in,
                 draft.tokens_out, draft.cost_usd, draft.created_at.isoformat())
            )
            conn.commit()
        finally:
            conn.close()
