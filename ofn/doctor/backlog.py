#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""backlog — the doctor's self-backlog of its own missing organs.

Owner-mandated fields (Lane B directive, 2026-09-02), exactly nine:
id, missing_capability, evidence, severity, proposed_action, test_required,
owner_ruling_required, status, created_at.

Ids are stable hashes of (area, missing_capability), so re-running the round
upserts instead of duplicating — the doctor may not flood its own backlog.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import re
from pathlib import Path

__all__ = ["SelfBacklog", "BACKLOG_FIELDS"]

BACKLOG_FIELDS = (
    "id", "missing_capability", "evidence", "severity", "proposed_action",
    "test_required", "owner_ruling_required", "status", "created_at",
)

# Capabilities whose scheduling is policy, not engineering — owner rules them.
_OWNER_RULED_AREAS = {"lab", "gate", "flow", "doctor"}


def _stable_id(area: str, capability: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", f"{area} {capability}".lower()).strip("-")[:70]
    digest = hashlib.sha256(f"{area}::{capability}".encode("utf-8")).hexdigest()[:8]
    return f"SB-{slug}-{digest}"


def _utcnow() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class SelfBacklog:
    def __init__(self, state_path: Path | str):
        self.path = Path(state_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._items: dict[str, dict] = {}
        if self.path.exists():
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            self._items = {it["id"]: it for it in raw.get("items", [])}

    # ------------------------------------------------------------------ write
    def upsert(self, area: str, capability: str, *, evidence: str, severity: str,
               proposed_action: str, test_required: bool = True,
               owner_ruling_required: bool | None = None) -> str:
        if severity not in ("LOW", "MEDIUM", "HIGH", "CRITICAL"):
            raise ValueError(f"bad severity: {severity}")
        if owner_ruling_required is None:
            owner_ruling_required = area in _OWNER_RULED_AREAS
        item_id = _stable_id(area, capability)
        if item_id in self._items:
            old = self._items[item_id]
            old.update({
                "evidence": evidence, "severity": severity,
                "proposed_action": proposed_action,
                "test_required": test_required,
                "owner_ruling_required": owner_ruling_required,
            })
            changed = "updated"
        else:
            self._items[item_id] = {
                "id": item_id,
                "missing_capability": f"{area}: {capability}",
                "evidence": evidence,
                "severity": severity,
                "proposed_action": proposed_action,
                "test_required": test_required,
                "owner_ruling_required": owner_ruling_required,
                "status": "open",
                "created_at": _utcnow(),
            }
            changed = "added"
        self._save()
        return changed

    def upsert_from_gaps(self, gaps: list[dict]) -> dict:
        counts = {"added": 0, "updated": 0, "unchanged": 0}
        for g in gaps:
            sev = ("HIGH" if "BLOCKED" in g["status"] or "NOT_VERIFIED" in g["status"]
                   else "MEDIUM" if "NOT_STARTED" in g["status"] or "PARTIAL" in g["status"]
                   else "LOW")
            before = dict(self._items)
            changed = self.upsert(
                g["area"], g["item"],
                evidence=f"LAB-DOCTOR-CONTRACT.yaml status={g['status']}",
                severity=sev,
                proposed_action=(
                    "design + test the missing organ; scheduling and gate-opening "
                    "require an owner ruling"
                ),
            )
            if changed == "added" or before.get(_stable_id(g["area"], g["item"])) is None:
                counts[changed] += 1
            else:
                counts["updated"] += 1
        return counts

    # ------------------------------------------------------------------- read
    def items(self) -> list[dict]:
        return [self._items[k] for k in sorted(self._items)]

    def open_items(self) -> list[dict]:
        return [it for it in self.items() if it["status"] == "open"]

    def _save(self) -> None:
        payload = {"items": self.items(), "count": len(self._items),
                   "updated_at": _utcnow()}
        self.path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
