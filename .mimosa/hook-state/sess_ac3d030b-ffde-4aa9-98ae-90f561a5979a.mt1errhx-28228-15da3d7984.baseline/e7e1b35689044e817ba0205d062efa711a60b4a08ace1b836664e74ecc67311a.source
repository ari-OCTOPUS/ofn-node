"""
Worker D — Asset / Image (KB-01, namespace: content_*)
draft-only. Before/after enhancement + brand overlay.

MVP: enhancement of real photos (not generative AI).
Cost: cheap per-asset (Phase 0: no implementation).
Phase 0: Stub.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AssetDraft:
    draft_id: str
    asset_type: str        # "before_after", "brand_overlay", "suburb_hero"
    source_path: str       # path to operator-uploaded photo
    output_path: str = ""  # filled after processing
    agent_id: str = "D_asset"
    cost_usd: float = 0.0


class AssetAgent:
    """Worker D: Image enhancement draft (not generative AI in MVP)."""
    AGENT_ID = "D_asset"

    def draft_before_after(self, before_path: str, after_path: str) -> AssetDraft:
        """Create a branded before/after comparison card."""
        # TODO Phase 2: enhancement + brand overlay
        return AssetDraft(
            draft_id="", asset_type="before_after", source_path=before_path
        )
