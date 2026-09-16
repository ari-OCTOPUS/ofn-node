"""Router: businesses ask for a capability, Lab picks the provider (prefer fugu)."""
from __future__ import annotations

import os
from typing import Optional

from .contract import ModelProvider
from .providers.deepseek import DeepSeekProvider
from .providers.fugu import FuguProvider

# Map capability -> preferred provider name. Businesses never pass model ids.
_CAPABILITY_DEFAULTS = {
    "copy": "fugu",
    "chat": "fugu",
    "tool": "fugu",
    "embed": "fugu",
}


def get_provider(capability: str = "copy", *, override: Optional[str] = None) -> ModelProvider:
    """Return a ModelProvider for the capability.

    - Prefer fugu (owner Lab policy).
    - `override` is for Lab/ops only (env BRAINPORT_PROVIDER), not for Ziman/Studio imports.
    """
    name = (override or os.environ.get("BRAINPORT_PROVIDER") or _CAPABILITY_DEFAULTS.get(capability, "fugu")).lower()
    if name in ("fugu", "prefer-fugu", "default"):
        return FuguProvider()
    if name in ("deepseek", "ds"):
        return DeepSeekProvider()
    raise ValueError(f"unknown BrainPort provider key: {name!r} (Lab keys only; not vendor model ids)")
