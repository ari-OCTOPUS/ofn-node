from __future__ import annotations

KNOWN_PLUGIN_TYPES = {
    "system_resources",
    "thermal",
    "filesystem",
    "process",
    "anomaly",
    "contradiction",
}


def discover_enabled(sensors: list[dict], known_types: set[str] | None = None) -> tuple[list[dict], list[dict]]:
    known = known_types or KNOWN_PLUGIN_TYPES
    enabled: list[dict] = []
    unknown: list[dict] = []
    for spec in sensors:
        if spec.get("status") in {"discovered_unregistered", "not_enabled"}:
            continue
        if spec.get("enabled") is False:
            continue
        plugin = spec.get("plugin") or {}
        if not plugin:
            continue
        if plugin.get("type") not in known:
            unknown.append(spec)
            continue
        enabled.append(spec)
    return enabled, unknown
