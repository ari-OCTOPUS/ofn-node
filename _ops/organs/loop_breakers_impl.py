#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""loop_breakers_impl.py — C20 (مگا‌دستور #۱۷): کدنویسی واقعی loop breakers.

Sentinel adapter · Tool request generator · RFC deduper · Alert aggregator.
همه offline · بدون Telegram send · بدون مدل پولی."""
from __future__ import annotations

import hashlib
import json
import re
import time
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# ── ۱) Sentinel adapter (F6) ─────────────────────────────────────────────

class UnknownMetric:
    """جایگزین sentinel عددی — render می‌شود به «نامعلوم» نه -1."""
    __slots__ = ("reason",)

    def __init__(self, reason: str = "sentinel"):
        self.reason = reason

    def __repr__(self) -> str:
        return f"UnknownMetric({self.reason})"

    def render(self) -> str:
        return "نامعلوم"


class NonNegativeMetric:
    """متریک غیرمنفی — اگر مقدار منفی ببینید → UnknownMetric."""
    __slots__ = ("value",)

    def __init__(self, value: float | int):
        if value < 0:
            raise ValueError(f"NonNegativeMetric got negative: {value}")
        self.value = value


def safe_metric(value: float | int | None, *, sentinel_value: float = -1) -> "NonNegativeMetric | UnknownMetric":
    """تبدیل typed: مقدار sentinel یا None → UnknownMetric، نه عدد منفی."""
    if value is None or value == sentinel_value:
        return UnknownMetric(reason="sentinel_or_none")
    try:
        return NonNegativeMetric(value)
    except ValueError:
        return UnknownMetric(reason=f"negative_value:{value}")


# ── ۲) Tool request generator (F5) ───────────────────────────────────────

@dataclass
class ToolRequest:
    need: str
    target_path: str
    capability: str
    attempts: int = 0
    last_rejection: str = ""
    quarantined_until: float = 0.0  # unix timestamp


class ToolRequestGate:
    """حداکثر ۲ تلاش → TOOL_REQUEST_QUARANTINED → cooldown 24h."""

    MAX_ATTEMPTS = 2
    COOLDOWN_S = 24 * 3600

    def __init__(self, state_path: Path | None = None):
        self.state_path = state_path
        self._requests: dict[str, ToolRequest] = {}
        if state_path and state_path.exists():
            try:
                data = json.loads(state_path.read_text(encoding="utf-8"))
                for k, v in data.items():
                    self._requests[k] = ToolRequest(**v)
            except (OSError, ValueError, TypeError):
                pass

    def _key(self, need: str, path: str, cap: str) -> str:
        return hashlib.sha256(f"{need}|{path}|{cap}".encode()).hexdigest()[:16]

    def check(self, need: str, path: str, cap: str) -> dict:
        """بررسی قبل از تولید card — اگر quarantine است reject."""
        key = self._key(need, path, cap)
        req = self._requests.get(key)
        if req is None:
            return {"allowed": True, "reason": "new"}
        if time.time() < req.quarantined_until:
            return {"allowed": False, "reason": "TOOL_REQUEST_QUARANTINED",
                    "remaining_cooldown_s": int(req.quarantined_until - time.time())}
        if req.attempts >= self.MAX_ATTEMPTS:
            return {"allowed": False, "reason": "TOOL_REQUEST_QUARANTINED",
                    "attempts": req.attempts}
        return {"allowed": True, "reason": "retry", "attempts": req.attempts}

    def record_rejection(self, need: str, path: str, cap: str, reason: str) -> None:
        key = self._key(need, path, cap)
        req = self._requests.setdefault(key, ToolRequest(need, path, cap))
        req.attempts += 1
        req.last_rejection = reason
        if req.attempts >= self.MAX_ATTEMPTS:
            req.quarantined_until = time.time() + self.COOLDOWN_S

    def _save(self) -> None:
        if self.state_path:
            self.state_path.parent.mkdir(parents=True, exist_ok=True)
            self.state_path.write_text(json.dumps(
                {k: vars(v) for k, v in self._requests.items()},
                ensure_ascii=False, indent=1), encoding="utf-8")


# ── ۳) RFC deduper (F7) ──────────────────────────────────────────────────

def rfc_semantic_key(organ: str, bottleneck_type: str, proposed_capability: str) -> str:
    """کلید semántic بدون مدل پولی."""
    return hashlib.sha256(
        f"{organ}|{bottleneck_type}|{proposed_capability}".encode()).hexdigest()[:16]


class RFCDeduper:
    """RFCهای مشابه merge؛ سقف RFC باز."""

    MAX_OPEN = 10

    def __init__(self):
        self._open: dict[str, dict] = {}

    def submit(self, organ: str, bottleneck: str, capability: str) -> dict:
        key = rfc_semantic_key(organ, bottleneck, capability)
        if key in self._open:
            return {"action": "MERGED", "existing_id": self._open[key]["id"]}
        if len(self._open) >= self.MAX_OPEN:
            return {"action": "REJECTED", "reason": "MAX_OPEN_RFC_REACHED"}
        rfc_id = f"rfc-{key[:8]}"
        self._open[key] = {"id": rfc_id, "organ": organ,
                          "bottleneck": bottleneck, "capability": capability,
                          "submitted_at": time.time()}
        return {"action": "CREATED", "id": rfc_id}


# ── ۴) Alert aggregator (F7) ─────────────────────────────────────────────

@dataclass
class Incident:
    incident_key: str
    subsystem: str
    issue_type: str
    root_cause: str
    state_epoch: str
    count: int = 1
    first_seen: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)
    severity: str = "info"


class AlertAggregator:
    """incident key = subsystem + issue_type + root_cause + state_epoch.
    count update، نه پیام جدید؛ escalation فقط با severity change."""

    def __init__(self):
        self._incidents: dict[str, Incident] = {}

    def _key(self, subsystem: str, issue: str, root: str, epoch: str) -> str:
        return hashlib.sha256(f"{subsystem}|{issue}|{root}|{epoch}".encode()).hexdigest()[:16]

    def ingest(self, subsystem: str, issue: str, root: str, epoch: str,
               severity: str = "info") -> dict:
        """یک alert جدید → اگر همان incident است، count++; نه notification جدید."""
        key = self._key(subsystem, issue, root, epoch)
        if key in self._incidents:
            inc = self._incidents[key]
            inc.count += 1
            inc.last_seen = time.time()
            escalated = severity != inc.severity
            if escalated:
                inc.severity = severity
            return {"action": "AGGREGATED", "incident_key": key,
                    "count": inc.count, "escalated": escalated,
                    "notification": False}
        inc = Incident(key, subsystem, issue, root, epoch, severity=severity)
        self._incidents[key] = inc
        return {"action": "NEW_INCIDENT", "incident_key": key,
                "notification": True, "count": 1}

    def stats(self) -> dict:
        return {"total_incidents": len(self._incidents),
                "total_alerts_ingested": sum(i.count for i in self._incidents.values()),
                "duplicate_suppression_rate": round(
                    1 - len(self._incidents) / max(1, sum(i.count for i in self._incidents.values())), 4)}
