"""Hardware registry loader and validator."""
from __future__ import annotations

from .io import read_yaml
from .models import HardwareNode, NodeStatus, PowerSource, GateResult, RiskLevel


def load_hardware_registry(path: str) -> list[HardwareNode]:
    data = read_yaml(path)
    raw_nodes = data.get("nodes", [])
    nodes: list[HardwareNode] = []
    for item in raw_nodes:
        nodes.append(
            HardwareNode(
                node_id=str(item.get("node_id", "")).strip(),
                device_type=str(item.get("device_type", "unknown")),
                status=NodeStatus(str(item.get("status", "unknown")).lower()),
                location_code=str(item.get("location_code", "unknown")),
                power_source=PowerSource(str(item.get("power_source", "unknown")).lower()),
                electricity_cost_usd_kwh=item.get("electricity_cost_usd_kwh"),
                role=str(item.get("role", "unknown")),
                access_method=str(item.get("access_method", "unknown")),
                notes_safe=str(item.get("notes_safe", "")),
            )
        )
    return nodes


def validate_hardware_registry(nodes: list[HardwareNode]) -> list[GateResult]:
    results: list[GateResult] = []
    if not nodes:
        return [
            GateResult(
                name="HARDWARE_REGISTRY_PRESENT",
                passed=False,
                risk=RiskLevel.RED,
                message="No nodes found. Fill hardware registry before any execution planning.",
            )
        ]

    missing_ids = [n for n in nodes if not n.node_id]
    results.append(
        GateResult(
            name="NODE_IDS",
            passed=not missing_ids,
            risk=RiskLevel.RED if missing_ids else RiskLevel.GREEN,
            message="All nodes have node_id." if not missing_ids else f"{len(missing_ids)} node(s) missing node_id.",
        )
    )

    unknown_status = [n.node_id for n in nodes if n.status == NodeStatus.UNKNOWN]
    results.append(
        GateResult(
            name="NODE_STATUS_KNOWN",
            passed=not unknown_status,
            risk=RiskLevel.ORANGE if unknown_status else RiskLevel.GREEN,
            message="All node statuses are known." if not unknown_status else "Some node statuses are unknown.",
            evidence=unknown_status,
        )
    )

    unknown_power = [n.node_id for n in nodes if n.power_source == PowerSource.UNKNOWN]
    results.append(
        GateResult(
            name="POWER_SOURCE_KNOWN",
            passed=not unknown_power,
            risk=RiskLevel.ORANGE if unknown_power else RiskLevel.GREEN,
            message="All power sources are known." if not unknown_power else "Some power sources are unknown.",
            evidence=unknown_power,
        )
    )

    return results
