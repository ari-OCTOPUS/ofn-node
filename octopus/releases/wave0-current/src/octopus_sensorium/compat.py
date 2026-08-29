"""Fill missing envelope fields. Never invent signature_verified=true."""

from __future__ import annotations

from typing import Any

from octopus_sensorium.models.observation import Observation


def upgrade_observation(obs: dict[str, Any]) -> dict[str, Any]:
    upgraded = dict(obs)
    result = dict(upgraded.get("result") or {})
    result.setdefault("encoding", "json")
    upgraded["result"] = result
    time_block = dict(upgraded.get("time") or {})
    time_block.setdefault("time_unverified", bool((upgraded.get("quality") or {}).get("time_unverified")))
    upgraded["time"] = time_block
    provenance = dict(upgraded.get("provenance") or {})
    provenance["signature_verified"] = False
    upgraded["provenance"] = provenance
    upgraded.setdefault(
        "evidence",
        {"evidence_chain_id": None, "supporting_event_ids": [], "opposing_event_ids": []},
    )
    upgraded.setdefault(
        "policy",
        {
            "actionable": False,
            "may_change_readiness": False,
            "may_quarantine": False,
            "human_approval_required": True,
        },
    )
    security = dict(upgraded.get("security") or {})
    security.setdefault("redaction_applied", False)
    upgraded["security"] = security
    return Observation.model_validate(upgraded).model_dump()
