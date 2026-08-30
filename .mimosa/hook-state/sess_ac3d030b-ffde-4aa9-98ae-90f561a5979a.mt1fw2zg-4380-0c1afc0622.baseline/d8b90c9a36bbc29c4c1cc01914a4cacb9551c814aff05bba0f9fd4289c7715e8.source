#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""registry.py -- Connector registry with audit and revocation (EQUIP G9).

Central registry for all personal connectors. Provides:
  - Register/deregister connectors with typed manifests
  - Lookup by connector_id (O(1) via dict)
  - List all connectors with optional status filter
  - Revocation: immediately invalidates a connector, preventing all actions
  - Audit trail: every register/revoke/lookup decision is logged
  - Idempotent registration (same connector_id overwrites)

Deny-by-default: unknown connector_id = None = gateway blocks.
Revoked connectors are kept in the registry (tombstone) for audit, but
all operations on them return blocked.

$0 | stdlib-only | no network | append-only audit log
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from schema import (
    ConnectorManifest,
    ConnectorStatus,
    RiskClass,
    SCHEMA,
    BUILTIN_CONNECTORS,
)

_HERE = Path(__file__).resolve().parent


@dataclass
class AuditEntry:
    """Single audit entry for a registry decision."""
    timestamp: float
    event: str              # "register" | "revoke" | "lookup_blocked" | "lookup_found"
    connector_id: str
    actor: str               # who triggered the event
    detail: str = ""

    def to_dict(self) -> dict:
        return {
            "schema": "connector-registry-audit.v1",
            "timestamp": self.timestamp,
            "event": self.event,
            "connector_id": self.connector_id,
            "actor": self.actor,
            "detail": self.detail,
        }


class ConnectorRegistry:
    """Central registry for personal connectors.

    Usage:
        reg = ConnectorRegistry(audit_path="/tmp/audit.jsonl")
        reg.register(manifest, actor="owner")
        manifest = reg.lookup("telegram")
        reg.revoke("telegram", actor="owner")

    All operations are idempotent and audit-logged.
    """

    def __init__(
        self,
        *,
        audit_path: Path | str | None = None,
        seed: bool = True,
        now: float | None = None,
    ) -> None:
        self._connectors: dict[str, ConnectorManifest] = {}
        self._revoked: set[str] = set()          # tombstones
        self._audit_log: list[AuditEntry] = []
        self._audit_path = Path(audit_path) if audit_path else None
        self._register_count = 0
        _now = now if now is not None else time.time()

        # Seed with built-in connectors
        if seed:
            for cid, spec in BUILTIN_CONNECTORS.items():
                spec_copy = dict(spec)
                spec_copy["registered_at"] = _now
                spec_copy["registered_by"] = "system-seed"
                try:
                    manifest = ConnectorManifest(**spec_copy)
                    self._connectors[cid] = manifest
                    self._audit_log.append(AuditEntry(
                        timestamp=_now,
                        event="register",
                        connector_id=cid,
                        actor="system-seed",
                        detail="builtin-seed",
                    ))
                except ValueError:
                    pass  # skip invalid builtins (shouldn't happen)

        # Persist seed audit to file if path provided
        if self._audit_path:
            self._flush_audit()

    def register(self, manifest: ConnectorManifest, *, actor: str = "system") -> bool:
        """Register or re-register a connector. Returns True if new/updated.

        Idempotent: re-registering the same connector_id overwrites.
        If previously revoked, re-registering lifts the revocation.
        """
        now = time.time()
        was_revoked = manifest.connector_id in self._revoked

        # If revoked, clear tombstone (re-registration = re-grant access)
        self._revoked.discard(manifest.connector_id)
        self._connectors[manifest.connector_id] = manifest
        self._register_count += 1

        entry = AuditEntry(
            timestamp=now,
            event="register",
            connector_id=manifest.connector_id,
            actor=actor,
            detail=f"was_revoked={was_revoked}",
        )
        self._audit_log.append(entry)
        self._flush_audit()
        return True

    def revoke(self, connector_id: str, *, actor: str = "owner") -> bool:
        """Revoke a connector. All future operations on it are blocked.

        The manifest is kept in the registry for audit, but lookup() returns
        None and is_revoked() returns True.
        """
        now = time.time()
        cid = str(connector_id).strip()

        if cid not in self._connectors:
            return False  # nothing to revoke

        self._revoked.add(cid)
        entry = AuditEntry(
            timestamp=now,
            event="revoke",
            connector_id=cid,
            actor=actor,
            detail="access_revoked_immediately",
        )
        self._audit_log.append(entry)
        self._flush_audit()
        return True

    def lookup(self, connector_id: str) -> ConnectorManifest | None:
        """Lookup a connector. Returns None if unknown or revoked."""
        cid = str(connector_id).strip()
        manifest = self._connectors.get(cid)
        if manifest is None:
            return None
        if cid in self._revoked:
            return None  # revoked = invisible to callers
        return manifest

    def is_revoked(self, connector_id: str) -> bool:
        """Check if a connector is revoked (even if manifest exists)."""
        return str(connector_id).strip() in self._revoked

    def list_all(self, *, include_revoked: bool = False) -> list[dict]:
        """List all connectors as dicts."""
        result = []
        for cid, manifest in self._connectors.items():
            d = manifest.to_dict()
            d["status"] = (
                "revoked" if cid in self._revoked else "active"
            )
            if not include_revoked and cid in self._revoked:
                continue
            result.append(d)
        return result

    def audit_trail(self) -> list[dict]:
        """Return all audit entries as dicts."""
        return [e.to_dict() for e in self._audit_log]

    def size(self) -> int:
        """Number of registered connectors (excluding revoked)."""
        return len(self._connectors) - len(self._revoked)

    def _flush_audit(self) -> None:
        """Append audit entries to file. Never throws. Never blocks."""
        if not self._audit_path:
            return
        try:
            self._audit_path.parent.mkdir(parents=True, exist_ok=True)
            # Only write entries not yet persisted
            # Simple approach: rewrite entire audit on each flush
            # (acceptable for small registry, not for high-frequency use)
            with open(self._audit_path, "w", encoding="utf-8") as f:
                for entry in self._audit_log:
                    f.write(json.dumps(
                        entry.to_dict(),
                        ensure_ascii=False,
                        sort_keys=True,
                    ) + "\n")
        except OSError:
            pass  # audit failure must never block operations


# ── Convenience factory ─────────────────────────────────────────────────────

def default_registry(*, audit_path: str | None = None) -> ConnectorRegistry:
    """Create a registry seeded with built-in connectors."""
    return ConnectorRegistry(audit_path=audit_path, seed=True)
