"""File-backed capability registry for the one-use local growth gate.

The registry is configuration and evidence, not a new live database schema.
It grants no executable, network, service-control, or external-action authority.
"""
from __future__ import annotations

import copy
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


GATE_ID = "GATE-CONTROLLED-CAPABILITY-AWAKENING-15MIN"
REGISTRY_SCHEMA_VERSION = 1
REGISTRY_PATH = Path(
    "/opt/octopus/lab/artifacts/capability-awakening/02_capability_registry.json"
)

CAPABILITY_STATES = (
    "LOCKED",
    "SHADOW",
    "TESTED",
    "CANARY",
    "ACTIVE_LOCAL",
)
STATE_NEXT = {
    "LOCKED": "SHADOW",
    "SHADOW": "TESTED",
    "TESTED": "CANARY",
    "CANARY": "ACTIVE_LOCAL",
}

INTERNAL_CAPABILITIES = (
    "MEMORY_RETRIEVAL",
    "MEMORY_CONSOLIDATION",
    "LOCAL_CURIOSITY",
    "LOCAL_LEARNING",
    "SELF_MODEL_UPDATE",
    "INNER_SPEECH",
    "LOCAL_HYPOTHESIS_ENGINE",
    "SANDBOX_EXPERIMENTS",
    "ENGINEERING_THETA",
    "ACTIVE_INFERENCE_SHADOW",
)
ACTIVE_INFERENCE_CAPABILITY = "ACTIVE_INFERENCE_SHADOW"

FORBIDDEN_REQUIRED: dict[str, Any] = {
    "OCTOPUS_LEARN_EXTERNAL": "0",
    "WAN_ACCESS": False,
    "ARBITRARY_WEB_ACCESS": False,
    "DEEPSEEK_CALL": False,
    "TELEGRAM_SEND": False,
    "EMAIL_SEND": False,
    "EXTERNAL_MESSAGE": False,
    "SHELL_EXECUTION": False,
    "SERVICE_CONTROL_AUTONOMOUS": False,
    "SYSTEMD_CONTROL_AUTONOMOUS": False,
    "FILE_DELETE": False,
    "WRITE_OUTSIDE_PROJECT": False,
    "NETWORK_CONFIGURATION": False,
    "SSH_TO_OTHER_HOST": False,
    "ESP32_ACTUATION": False,
    "CAMERA_RECORDING": False,
    "MICROPHONE_RECORDING": False,
    "FINANCIAL_ACTION": False,
    "PURCHASE": False,
    "OWNER_KEY_ACCESS": False,
    "IDENTITY_REWRITE": False,
    "SAFETY_GATE_MODIFICATION": False,
    "AUTONOMY_ESCALATION": False,
    "EXECUTABLE_ACTION": False,
    "WAVE1_UNLOCKED": False,
    "WAVE0_OBSERVE_ONLY": True,
    "PROPOSE_ONLY": True,
    "executable": False,
}


class CapabilityRegistryError(ValueError):
    """Registry is absent, malformed, unsafe, or illegally transitioned."""


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _validate_history(capability_id: str, entry: dict[str, Any]) -> None:
    history = entry.get("history")
    if not isinstance(history, list) or not history:
        raise CapabilityRegistryError(f"{capability_id}:history_required")
    first = history[0]
    if not isinstance(first, dict) or first.get("from") is not None:
        raise CapabilityRegistryError(f"{capability_id}:invalid_initial_history")
    current = first.get("to")
    expected_initial = (
        "SHADOW" if capability_id == ACTIVE_INFERENCE_CAPABILITY else "LOCKED"
    )
    if current != expected_initial:
        raise CapabilityRegistryError(
            f"{capability_id}:initial_state_must_be_{expected_initial}"
        )
    for item in history[1:]:
        if not isinstance(item, dict) or item.get("from") != current:
            raise CapabilityRegistryError(f"{capability_id}:history_not_contiguous")
        target = item.get("to")
        rollback = item.get("rollback") is True
        legal_rollback = rollback and current in {"CANARY", "ACTIVE_LOCAL"} and target == "TESTED"
        if STATE_NEXT.get(current) != target and not legal_rollback:
            raise CapabilityRegistryError(
                f"{capability_id}:illegal_transition:{current}->{target}"
            )
        current = target
    if entry.get("state") != current:
        raise CapabilityRegistryError(f"{capability_id}:state_history_mismatch")
    if capability_id == ACTIVE_INFERENCE_CAPABILITY and current != "SHADOW":
        raise CapabilityRegistryError("active_inference_must_remain_shadow")


def validate_registry(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise CapabilityRegistryError("registry_not_object")
    if payload.get("schema_version") != REGISTRY_SCHEMA_VERSION:
        raise CapabilityRegistryError("registry_schema_version")
    if payload.get("gate_id") != GATE_ID:
        raise CapabilityRegistryError("registry_gate_id")
    if payload.get("live_schema") != "phase3-skin-1":
        raise CapabilityRegistryError("live_schema_must_remain_phase3-skin-1")

    approval = payload.get("approval")
    if not isinstance(approval, dict):
        raise CapabilityRegistryError("approval_required")
    if approval.get("decision") != "APPROVED_WITH_CONDITIONS":
        raise CapabilityRegistryError("approval_decision")
    if approval.get("scope") != "ONE_USE":
        raise CapabilityRegistryError("approval_scope")
    if approval.get("expires_after_execution") is not True:
        raise CapabilityRegistryError("approval_expiry")

    capabilities = payload.get("capabilities")
    if not isinstance(capabilities, dict):
        raise CapabilityRegistryError("capabilities_required")
    if set(capabilities) != set(INTERNAL_CAPABILITIES):
        raise CapabilityRegistryError("capability_set_mismatch")
    for capability_id in INTERNAL_CAPABILITIES:
        entry = capabilities[capability_id]
        if not isinstance(entry, dict):
            raise CapabilityRegistryError(f"{capability_id}:entry_not_object")
        if entry.get("executable") is not False:
            raise CapabilityRegistryError(f"{capability_id}:executable_forbidden")
        if entry.get("scope") not in {"LOCAL_ONLY", "SHADOW_ONLY"}:
            raise CapabilityRegistryError(f"{capability_id}:scope")
        _validate_history(capability_id, entry)

    forbidden = payload.get("forbidden")
    if not isinstance(forbidden, dict):
        raise CapabilityRegistryError("forbidden_map_required")
    for name, required in FORBIDDEN_REQUIRED.items():
        if forbidden.get(name) != required:
            raise CapabilityRegistryError(f"forbidden_invariant:{name}")
    external = payload.get("external_capabilities")
    if external != {
        "EXTERNAL_LEARNING_CAPABILITY": "LOCKED",
        "EXTERNAL_ACTION_CAPABILITY": "LOCKED",
    }:
        raise CapabilityRegistryError("external_capabilities_must_remain_locked")
    return payload


def load_registry(path: Path | None = None) -> dict[str, Any]:
    selected = Path(path or REGISTRY_PATH)
    try:
        payload = json.loads(selected.read_text(encoding="utf-8"))
    except OSError as exc:
        raise CapabilityRegistryError("registry_unreadable") from exc
    except json.JSONDecodeError as exc:
        raise CapabilityRegistryError("registry_invalid_json") from exc
    return validate_registry(payload)


def atomic_write_registry(
    payload: dict[str, Any],
    path: Path | None = None,
) -> None:
    validate_registry(payload)
    selected = Path(path or REGISTRY_PATH)
    selected.parent.mkdir(parents=True, exist_ok=True)
    temporary = selected.with_suffix(selected.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.chmod(temporary, 0o644)
    temporary.replace(selected)


def transition_capabilities(
    payload: dict[str, Any],
    target: str,
    *,
    capability_ids: tuple[str, ...] | list[str] | None = None,
    evidence: list[str] | None = None,
    at: str | None = None,
) -> dict[str, Any]:
    validate_registry(payload)
    if target not in CAPABILITY_STATES:
        raise CapabilityRegistryError("unknown_target_state")
    selected = (
        tuple(capability_ids)
        if capability_ids is not None
        else tuple(
            item
            for item in INTERNAL_CAPABILITIES
            if item != ACTIVE_INFERENCE_CAPABILITY
        )
    )
    updated = copy.deepcopy(payload)
    stamp = at or utc_now()
    for capability_id in selected:
        if capability_id not in INTERNAL_CAPABILITIES:
            raise CapabilityRegistryError(f"unknown_capability:{capability_id}")
        if capability_id == ACTIVE_INFERENCE_CAPABILITY:
            if target != "SHADOW":
                raise CapabilityRegistryError("active_inference_must_remain_shadow")
            continue
        entry = updated["capabilities"][capability_id]
        current = entry["state"]
        if current == target:
            continue
        if STATE_NEXT.get(current) != target:
            raise CapabilityRegistryError(
                f"{capability_id}:illegal_transition:{current}->{target}"
            )
        entry["state"] = target
        entry["history"].append(
            {
                "from": current,
                "to": target,
                "at": stamp,
                "evidence": list(evidence or []),
            }
        )
    updated["updated_at"] = stamp
    validate_registry(updated)
    return updated


def capability_states(payload: dict[str, Any]) -> dict[str, str]:
    validate_registry(payload)
    return {
        capability_id: str(payload["capabilities"][capability_id]["state"])
        for capability_id in INTERNAL_CAPABILITIES
    }


def rollback_capabilities_to_tested(
    payload: dict[str, Any],
    *,
    reason: str,
    capability_ids: tuple[str, ...] | list[str] | None = None,
    at: str | None = None,
) -> dict[str, Any]:
    """Safety rollback. This is not a forward activation transition."""

    validate_registry(payload)
    selected = tuple(
        capability_ids
        or (
            item
            for item in INTERNAL_CAPABILITIES
            if item != ACTIVE_INFERENCE_CAPABILITY
        )
    )
    updated = copy.deepcopy(payload)
    stamp = at or utc_now()
    for capability_id in selected:
        if capability_id == ACTIVE_INFERENCE_CAPABILITY:
            continue
        entry = updated["capabilities"].get(capability_id)
        if not isinstance(entry, dict):
            raise CapabilityRegistryError(f"unknown_capability:{capability_id}")
        current = entry["state"]
        if current == "TESTED":
            continue
        if current not in {"CANARY", "ACTIVE_LOCAL"}:
            raise CapabilityRegistryError(
                f"{capability_id}:rollback_not_allowed_from_{current}"
            )
        entry["state"] = "TESTED"
        entry["history"].append(
            {
                "from": current,
                "to": "TESTED",
                "at": stamp,
                "evidence": [reason],
                "rollback": True,
            }
        )
        entry["quarantined"] = True
        entry["quarantine_reason"] = reason
    updated["phase"] = "TESTED"
    updated["updated_at"] = stamp
    updated["quarantined"] = sorted(selected)
    validate_registry(updated)
    return updated
