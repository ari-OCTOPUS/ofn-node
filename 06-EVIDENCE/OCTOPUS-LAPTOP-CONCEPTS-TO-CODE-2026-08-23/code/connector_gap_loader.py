"""CONNECTOR-GAP runtime hook.

Loads CONNECTOR-GAP-REGISTRY.json from the owner-brief / concepts-to-code
evidence package and marks GA4 / GSC / Ads as GAP until OAuth + owner signature.

No secrets. No OAuth automation. Read-only registry load.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULT_REGISTRY_CANDIDATES = (
    Path(r"F:\backup\06-EVIDENCE\OCTOPUS-LAPTOP-CONCEPTS-TO-CODE-2026-08-23\CONNECTOR-GAP-REGISTRY.json"),
    Path(r"F:\backup\06-EVIDENCE\OCTOPUS-LAPTOP-AGENT-OWNER-BRIEF-2026-08-22\CONNECTOR-GAP-REGISTRY.json"),
)


def resolve_registry_path(explicit: str | Path | None = None) -> Path:
    if explicit:
        p = Path(explicit)
        if not p.exists():
            raise FileNotFoundError(str(p))
        return p
    for c in DEFAULT_REGISTRY_CANDIDATES:
        if c.exists():
            return c
    raise FileNotFoundError("CONNECTOR-GAP-REGISTRY.json not found in known evidence paths")


def load_registry(path: str | Path | None = None) -> dict[str, Any]:
    p = resolve_registry_path(path)
    data = json.loads(p.read_text(encoding="utf-8"))
    data["_loaded_from"] = str(p)
    return data


def connector_status(registry: dict[str, Any], connector: str) -> dict[str, Any]:
    name = connector.strip()
    for gap in registry.get("gaps") or []:
        if str(gap.get("connector", "")).strip().lower() == name.lower():
            return {
                "connector": gap.get("connector"),
                "gap_id": gap.get("gap_id"),
                "status": gap.get("status"),
                "is_gap": True,
                "metrics_allowed": False,
                "reason": gap.get("reason"),
                "required_owner_action": gap.get("required_owner_action"),
                "gate": gap.get("gate"),
            }
    for item in registry.get("connector_probe_queue") or []:
        if str(item.get("connector", "")).strip().lower() == name.lower():
            return {
                "connector": item.get("connector"),
                "status": item.get("status"),
                "is_gap": False,
                "metrics_allowed": False,
                "output_policy": item.get("output_policy"),
                "reason": "pending_runtime_probe_no_invent",
            }
    return {
        "connector": name,
        "status": "UNKNOWN_NOT_IN_REGISTRY",
        "is_gap": True,
        "metrics_allowed": False,
        "reason": "unlisted_connector_treated_as_gap",
    }


def mark_oauth_gaps(registry: dict[str, Any] | None = None) -> dict[str, Any]:
    reg = registry or load_registry()
    out = []
    for name in ("GA4", "GSC", "Google Ads"):
        st = connector_status(reg, name)
        st["gap_until_oauth"] = True
        st["metrics_allowed"] = False
        if st.get("status") in (None, "UNKNOWN_NOT_IN_REGISTRY"):
            st["status"] = "WAITING_OWNER_OAUTH"
            st["is_gap"] = True
        out.append(st)
    return {
        "as_of_registry": reg.get("as_of"),
        "loaded_from": reg.get("_loaded_from"),
        "oauth_gaps": out,
        "hard_rules": reg.get("hard_rules") or [],
    }


if __name__ == "__main__":
    print(json.dumps(mark_oauth_gaps(), indent=2))
