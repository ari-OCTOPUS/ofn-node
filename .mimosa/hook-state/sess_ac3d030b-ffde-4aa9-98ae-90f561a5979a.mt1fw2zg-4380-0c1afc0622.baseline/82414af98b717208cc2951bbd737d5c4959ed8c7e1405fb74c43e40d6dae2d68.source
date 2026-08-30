"""Model-tier router (intelligence). Maps a task kind to a tier + model from
gates.yaml. It does NOT call any API -- it returns the CHOICE so the caller's
LLM client uses the right model. This is the "expensive intelligence at rare
decision points, cheap everywhere else" rule made concrete (RouteLLM/FrugalGPT
pattern; verified 40-85% savings vs routing everything through the top model).
"""
from __future__ import annotations

from typing import Any

# task kind -> tier name (tiers themselves are defined in genome/gates.yaml)
TASK_TIER = {
    "heartbeat": "cheap",
    "digest": "cheap",
    "classify": "cheap",
    "index": "cheap",
    "generate": "default",
    "creativity": "default",
    "doctor": "premium",
    "architecture": "premium",
}


def choose(genome, task_kind: str) -> dict[str, Any]:
    tiers = genome.gates.get("intelligence", {}).get("tiers", {})
    tier = TASK_TIER.get(task_kind, "default")
    spec = tiers.get(tier, {}) or {}
    return {
        "task": task_kind,
        "tier": tier,
        "model": spec.get("model"),
        "in_price": spec.get("in"),
        "out_price": spec.get("out"),
    }
