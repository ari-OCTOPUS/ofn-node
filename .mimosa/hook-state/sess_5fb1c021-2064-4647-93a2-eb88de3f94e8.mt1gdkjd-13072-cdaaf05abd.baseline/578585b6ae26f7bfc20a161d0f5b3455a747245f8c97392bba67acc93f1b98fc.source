"""
Worker D — Asset / Image (KB-01, namespace: content_*)
draft-only. Before/after enhancement + brand overlay.

MVP: enhancement of real photos (not generative AI).
Cost: cheap per-asset (Phase 0: no implementation).
Phase 0: Stub.
"""
from __future__ import annotations

from dataclasses import dataclass

from .base_agent import (
    BaseAgent, AgentCapability, RiskLevel, QualificationStatus, register_agent,
)


@dataclass
class AssetDraft:
    draft_id: str
    asset_type: str        # "before_after", "brand_overlay", "suburb_hero"
    source_path: str       # path to operator-uploaded photo
    output_path: str = ""  # filled after processing
    agent_id: str = "D_asset"
    cost_usd: float = 0.0


@register_agent
class AssetAgent(BaseAgent):
    """Worker D: Image enhancement draft (not generative AI in MVP)."""
    AGENT_ID = "D_asset"
    ALLOWED_ACTIONS = frozenset({"read", "analyse", "draft", "propose"})
    FORBIDDEN_ACTIONS = frozenset({
        "publish", "send", "spend", "alter_policy", "expose_pii",
        "write_canonical_memory", "access_secrets",
    })

    @property
    def role_name(self) -> str:
        return "Worker D — Asset / Image"

    @property
    def qualification_status(self) -> QualificationStatus:
        return QualificationStatus.TRAINEE

    @property
    def risk_level(self) -> RiskLevel:
        return RiskLevel.GREEN

    @property
    def required_inputs(self) -> frozenset[str]:
        return frozenset({"photo"})

    @property
    def capabilities(self) -> tuple[AgentCapability, ...]:
        return (
            AgentCapability("draft_before_after", "AssetDraft"),
        )

    def health(self) -> dict:
        # Phase 0 stub — no external deps, always ready to return a stub
        return {"ready": True, "detail": "stub (Phase 2 not implemented)"}

    def draft_before_after(self, before_path: str, after_path: str) -> AssetDraft:
        """Create a branded before/after comparison card."""
        # TODO Phase 2: enhancement + brand overlay
        return AssetDraft(
            draft_id="", asset_type="before_after", source_path=before_path
        )
