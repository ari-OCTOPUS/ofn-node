#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""registry.py — CapabilityRegistry (single source of Capability Truth).

Services may cache; they must not locally rewrite truth_status.
SPEC_NOT_BUILT ≠ STRUCTURAL.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_OPS = Path(__file__).resolve().parents[1]
_REG_DIR = _OPS / "capabilities"
_TRUTH_STATUSES = frozenset({
    "SPEC_NOT_BUILT",
    "STRUCTURAL",
    "TESTED",
    "SHADOW",
    "ARMED",
    "LOCKED",
    "RETIRED",
})
_EVIDENCE_LEVELS = frozenset({
    "SPEC_NOT_BUILT",
    "STRUCTURAL",
    "TESTED",
    "SHADOW",
    "ARMED",
    "LOCKED",
    "RETIRED",
})


@dataclass(frozen=True)
class CapabilityRecord:
    capability_id: str
    truth_status: str
    evidence_level: str
    runtime_path: str | None
    feature_flag: str | None
    enabled: bool
    allowed_effects: tuple[str, ...]
    may_affect_routing: bool
    may_affect_policy: bool
    may_trigger_external_action: bool
    adr: str | None
    raw: dict[str, Any]

    def as_public(self) -> dict[str, Any]:
        return {
            "capability_id": self.capability_id,
            "truth_status": self.truth_status,
            "evidence_level": self.evidence_level,
            "runtime": {
                "path": self.runtime_path,
                "feature_flag": self.feature_flag,
                "enabled": self.enabled,
            },
            "authority": {
                "allowed_effects": list(self.allowed_effects),
                "may_affect_routing": self.may_affect_routing,
                "may_affect_policy": self.may_affect_policy,
                "may_trigger_external_action": self.may_trigger_external_action,
            },
            "adr": self.adr,
        }


def _parse_simple_yaml(text: str) -> dict[str, Any]:
    """Minimal YAML subset parser (no PyYAML dependency). Indent-based maps/lists."""
    try:
        import yaml  # type: ignore
        return yaml.safe_load(text) or {}
    except Exception:
        pass
    # Fallback: JSON-compatible files only
    return json.loads(text) if text.strip().startswith("{") else _hand_yaml(text)


def _hand_yaml(text: str) -> dict[str, Any]:
    """Very small indent YAML reader for our registry files."""
    root: dict[str, Any] = {}
    stack: list[tuple[int, Any]] = [(-1, root)]
    pending_key: str | None = None

    for raw in text.splitlines():
        if not raw.strip() or raw.strip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        line = raw.strip()
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]

        if line.startswith("- "):
            item = line[2:].strip().strip('"').strip("'")
            if not isinstance(parent, list):
                # convert last pending
                continue
            parent.append(_scalar(item))
            continue

        if ":" in line:
            key, _, rest = line.partition(":")
            key = key.strip()
            rest = rest.strip()
            if rest == "" or rest == "|" or rest == ">":
                # nested map or list TBD
                nxt: dict[str, Any] | list[Any] = {}
                # peek next non-empty? default map; list if next is "- "
                parent[key] = nxt
                stack.append((indent, nxt))
                pending_key = key
            elif rest.startswith("[") and rest.endswith("]"):
                inner = rest[1:-1].strip()
                parent[key] = [
                    _scalar(x.strip()) for x in inner.split(",") if x.strip()
                ] if inner else []
            else:
                parent[key] = _scalar(rest)
    # Fix empty dicts that should be lists when only "- " children expected:
    # Our files use `allowed_effects: []` and nested maps — OK.
    return root


def _scalar(v: str) -> Any:
    if v in ("true", "True"):
        return True
    if v in ("false", "False"):
        return False
    if v in ("null", "None", "~"):
        return None
    if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
        return v[1:-1]
    try:
        if "." in v:
            return float(v)
        return int(v)
    except ValueError:
        return v


def load_record(path: Path) -> CapabilityRecord:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        data = json.loads(text)
    else:
        data = _parse_simple_yaml(text)
    runtime = data.get("runtime") or {}
    authority = data.get("authority") or {}
    evidence = data.get("evidence") or {}
    truth = str(data.get("truth_status") or "SPEC_NOT_BUILT")
    evid = str(data.get("evidence_level") or "SPEC_NOT_BUILT")
    if truth not in _TRUTH_STATUSES:
        truth = "SPEC_NOT_BUILT"
    if evid not in _EVIDENCE_LEVELS:
        evid = "STRUCTURAL" if truth != "SPEC_NOT_BUILT" else "SPEC_NOT_BUILT"
    # Enforce: SPEC_NOT_BUILT cannot claim runtime path as live
    path_val = runtime.get("code_path") or runtime.get("path")
    enabled = bool(runtime.get("enabled", False))
    if truth == "SPEC_NOT_BUILT":
        enabled = False
        path_val = path_val  # may be null
    return CapabilityRecord(
        capability_id=str(data.get("capability_id") or path.stem),
        truth_status=truth,
        evidence_level=evid,
        runtime_path=path_val,
        feature_flag=runtime.get("feature_flag"),
        enabled=enabled,
        allowed_effects=tuple(authority.get("allowed_effects") or ()),
        may_affect_routing=bool(authority.get("may_affect_routing", False)),
        may_affect_policy=bool(authority.get("may_affect_policy", False)),
        may_trigger_external_action=bool(
            authority.get("may_trigger_external_action", False)
        ),
        adr=(evidence.get("adr") if isinstance(evidence, dict) else None)
        or data.get("adr"),
        raw=data,
    )


class CapabilityRegistry:
    def __init__(self, directory: Path | None = None) -> None:
        self.directory = directory or _REG_DIR
        self._cache: dict[str, CapabilityRecord] = {}

    def reload(self) -> None:
        self._cache.clear()
        if not self.directory.exists():
            return
        for pattern in ("*.json", "*.yaml", "*.yml"):
            for path in sorted(self.directory.glob(pattern)):
                rec = load_record(path)
                self._cache[rec.capability_id] = rec

    def get(self, capability_id: str) -> CapabilityRecord | None:
        if not self._cache:
            self.reload()
        return self._cache.get(capability_id)

    def all(self) -> list[CapabilityRecord]:
        if not self._cache:
            self.reload()
        return list(self._cache.values())

    def assert_not_false_claim(self, capability_id: str) -> tuple[bool, str]:
        """UI/API must not present SPEC_NOT_BUILT as live/armed."""
        rec = self.get(capability_id)
        if rec is None:
            return False, "capability_unknown"
        if rec.truth_status == "SPEC_NOT_BUILT" and rec.enabled:
            return False, "spec_not_built_cannot_be_enabled"
        if rec.truth_status in ("SPEC_NOT_BUILT", "STRUCTURAL") and (
            rec.may_affect_routing or rec.may_trigger_external_action
        ):
            return False, "authority_exceeds_truth"
        return True, "ok"


_DEFAULT: CapabilityRegistry | None = None


def get_registry() -> CapabilityRegistry:
    global _DEFAULT
    if _DEFAULT is None:
        _DEFAULT = CapabilityRegistry()
        _DEFAULT.reload()
    return _DEFAULT
