"""Example: Ziman copy via BrainPort — no model names in business code."""
from __future__ import annotations

import sys
from pathlib import Path

# Lab pack path bootstrap (until installed as a real package)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from brainport import GenerateRequest, get_provider


def draft_product_blurb(product: str, audience: str = "AU gift shoppers") -> str:
    provider = get_provider("copy")  # Lab chooses fugu; business does not name it
    req = GenerateRequest(
        prompt=f"Write a 2-sentence Shopify blurb for: {product}. Audience: {audience}.",
        system="Ziman handmade gifts. Warm, specific, no hype spam.",
        capability="copy",
        max_tokens=200,
    )
    health = provider.health()
    assert health.ok, health.detail
    _ = provider.estimate_cost(req)
    _ = provider.model_capabilities()
    return provider.generate(req).text


if __name__ == "__main__":
    print(draft_product_blurb("personalized wooden name plaque"))
