#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""schema.py -- Connector capability manifest schema (EQUIP G9).

Defines the data structures for a privacy-preserving personal connector registry.
Each connector is registered with typed metadata describing its owner, scopes,
read/write capabilities, retention policy, and risk classification.

Design principles:
  - deny-by-default: unregistered connector = UNKNOWN = blocked
  - manifest is immutable once registered (re-register overwrites)
  - read/write/retention are enum-validated, not free text
  - risk_class integrates with G8 risk_gate.py RiskTier
  - owner_gate signals whether owner approval is required before any action
  - consent_required signals whether consent_gate.py must pass before read

$0 | stdlib-only | no network | pure data classes + validation
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

SCHEMA = "connector-manifest.v1"

# ── Valid enum types ──────────────────────────────────────────────────────────


class ConnectorStatus(str, Enum):
    """Lifecycle state of a connector."""
    ACTIVE = "active"
    SUSPENDED = "suspended"      # temporarily disabled
    REVOKED = "revoked"          # access permanently revoked
    PROPOSED = "proposed"        # not yet activated


class ReadScope(str, Enum):
    """What read access a connector provides."""
    NONE = "none"
    METADATA = "metadata"            # list/query only (e.g., repo names)
    SUMMARIZED = "summarized"        # aggregated data (e.g., balance)
    DETAILED = "detailed"            # full records (e.g., transactions)
    RAW = "raw"                      # unprocessed (highest sensitivity)


class WriteScope(str, Enum):
    """What write access a connector provides."""
    NONE = "none"
    DRAFT = "draft"                  # only draft proposals (no external effect)
    APPROVED_WRITE = "approved_write" # write only after owner approval
    DIRECT_WRITE = "direct_write"    # immediate external write (dangerous)


class RetentionClass(str, Enum):
    """Data retention policy for data from this connector."""
    NONE = "none"                    # no storage at all
    EPHEMERAL = "ephemeral"          # in-memory only, not persisted
    SESSION = "session"              # lasts current session
    SHORT = "short"                  # 30 days
    MEDIUM = "medium"                # 12 months
    LONG = "long"                    # indefinite (requires explicit approval)


class RiskClass(str, Enum):
    """Risk classification aligned with G8 risk_gate.py tiers."""
    READ_ONLY = "read_only"
    REVERSIBLE_WRITE = "reversible_write"
    IRREVERSIBLE = "irreversible"
    FINANCIAL = "financial"
    FORBIDDEN = "forbidden"


class OwnerGate(str, Enum):
    """Whether owner gate is required for operations."""
    NEVER = "never"
    WRITE_ONLY = "write_only"
    ALWAYS = "always"


# ── Validation patterns ──────────────────────────────────────────────────────

_CONNECTOR_ID_RE = re.compile(r"^[a-z][a-z0-9_-]{1,63}$")
_OWNER_ID_RE = re.compile(r"^[a-z][a-z0-9_-]{1,63}$")
_TOKEN_ENV_RE = re.compile(r"^[A-Z][A-Z0-9_]{1,63}$")


# ── Data structures ───────────────────────────────────────────────────────────


def _coerce_enum(value: Any, enum_cls: type) -> Any:
    """Coerce string to enum if needed."""
    if isinstance(value, enum_cls):
        return value
    if isinstance(value, str):
        try:
            return enum_cls(value)
        except ValueError:
            raise ValueError(f"invalid {enum_cls.__name__}: {value!r}")
    return value


@dataclass(frozen=True)
class ConnectorManifest:
    """Immutable capability manifest for a single connector.

    This is the single source of truth for what a connector can and cannot do.
    The gateway reads this manifest before routing any request.
    """
    # Identity
    connector_id: str
    title: str
    version: str
    owner: str                    # who owns/manages this connector

    # Capabilities (accept str or Enum; coerced to Enum in __post_init__)
    read_scope: ReadScope
    write_scope: WriteScope
    retention: RetentionClass
    risk_class: RiskClass
    owner_gate: OwnerGate

    # Sensitivity flags
    contains_pii: bool = False
    contains_financial: bool = False
    contains_health: bool = False

    # Access control
    token_env: str = ""           # environment variable name for token (never the value)
    allowed_targets: tuple[str, ...] = ()   # allowlist of target identifiers
    max_results_per_query: int = 100        # output ceiling
    requires_consent: bool = False          # consent_gate must pass for read

    # Provenance
    registered_at: float = 0.0
    registered_by: str = ""
    schema_version: str = SCHEMA

    # Compliance
    data_never_leaves_vault: bool = True     # connector data must not appear in public output
    dry_run_available: bool = True           # supports dry-run mode

    def __post_init__(self) -> None:
        """Validate and coerce the manifest on construction."""
        # Coerce string fields to enums
        object.__setattr__(self, "read_scope",
                           _coerce_enum(self.read_scope, ReadScope))
        object.__setattr__(self, "write_scope",
                           _coerce_enum(self.write_scope, WriteScope))
        object.__setattr__(self, "retention",
                           _coerce_enum(self.retention, RetentionClass))
        object.__setattr__(self, "risk_class",
                           _coerce_enum(self.risk_class, RiskClass))
        object.__setattr__(self, "owner_gate",
                           _coerce_enum(self.owner_gate, OwnerGate))

        # Validate
        if not _CONNECTOR_ID_RE.match(self.connector_id):
            raise ValueError(f"invalid connector_id: {self.connector_id!r}")
        if not _OWNER_ID_RE.match(self.owner):
            raise ValueError(f"invalid owner: {self.owner!r}")
        if self.token_env and not _TOKEN_ENV_RE.match(self.token_env):
            raise ValueError(f"invalid token_env: {self.token_env!r}")
        if self.max_results_per_query < 1:
            raise ValueError("max_results_per_query must be >= 1")
        # Health + Financial connectors must be read-only
        if self.contains_health and self.write_scope != WriteScope.NONE:
            raise ValueError("health connectors must be write_scope=NONE")
        if self.contains_financial and self.write_scope not in (
            WriteScope.NONE, WriteScope.DRAFT):
            raise ValueError(
                "financial connectors must be write_scope=NONE or DRAFT")
        # Forbidden risk class
        if self.risk_class == RiskClass.FORBIDDEN:
            raise ValueError(
                "forbidden connectors cannot be registered as active")

    def to_dict(self) -> dict:
        """Serialize to JSON-safe dict."""
        return {
            "schema": self.schema_version,
            "connector_id": self.connector_id,
            "title": self.title,
            "version": self.version,
            "owner": self.owner,
            "read_scope": self.read_scope.value,
            "write_scope": self.write_scope.value,
            "retention": self.retention.value,
            "risk_class": self.risk_class.value,
            "owner_gate": self.owner_gate.value,
            "contains_pii": self.contains_pii,
            "contains_financial": self.contains_financial,
            "contains_health": self.contains_health,
            "token_env": self.token_env,
            "allowed_targets": list(self.allowed_targets),
            "max_results_per_query": self.max_results_per_query,
            "requires_consent": self.requires_consent,
            "registered_at": self.registered_at,
            "registered_by": self.registered_by,
            "data_never_leaves_vault": self.data_never_leaves_vault,
            "dry_run_available": self.dry_run_available,
        }

    @classmethod
    def from_dict(cls, d: dict) -> ConnectorManifest:
        """Deserialize from dict. Raises on invalid fields."""
        return cls(
            connector_id=str(d["connector_id"]),
            title=str(d["title"]),
            version=str(d["version"]),
            owner=str(d["owner"]),
            read_scope=ReadScope(str(d["read_scope"])),
            write_scope=WriteScope(str(d["write_scope"])),
            retention=RetentionClass(str(d["retention"])),
            risk_class=RiskClass(str(d["risk_class"])),
            owner_gate=OwnerGate(str(d["owner_gate"])),
            contains_pii=bool(d.get("contains_pii", False)),
            contains_financial=bool(d.get("contains_financial", False)),
            contains_health=bool(d.get("contains_health", False)),
            token_env=str(d.get("token_env", "")),
            allowed_targets=tuple(d.get("allowed_targets", [])),
            max_results_per_query=int(d.get("max_results_per_query", 100)),
            requires_consent=bool(d.get("requires_consent", False)),
            registered_at=float(d.get("registered_at", 0)),
            registered_by=str(d.get("registered_by", "")),
            data_never_leaves_vault=bool(
                d.get("data_never_leaves_vault", True)),
            dry_run_available=bool(d.get("dry_run_available", True)),
        )

    @classmethod
    def json_schema(cls) -> dict:
        """Return JSON Schema for validation (for downstream consumers)."""
        return {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": f"octopus.{SCHEMA}",
            "title": "Connector Capability Manifest",
            "type": "object",
            "required": [
                "connector_id", "title", "version", "owner",
                "read_scope", "write_scope", "retention",
                "risk_class", "owner_gate",
            ],
            "properties": {
                "connector_id": {
                    "type": "string",
                    "pattern": "^[a-z][a-z0-9_-]{1,63}$",
                },
                "title": {"type": "string", "minLength": 2, "maxLength": 100},
                "version": {"type": "string", "minLength": 1},
                "owner": {
                    "type": "string",
                    "pattern": "^[a-z][a-z0-9_-]{1,63}$",
                },
                "read_scope": {
                    "type": "string",
                    "enum": [s.value for s in ReadScope],
                },
                "write_scope": {
                    "type": "string",
                    "enum": [s.value for s in WriteScope],
                },
                "retention": {
                    "type": "string",
                    "enum": [s.value for s in RetentionClass],
                },
                "risk_class": {
                    "type": "string",
                    "enum": [s.value for s in RiskClass],
                },
                "owner_gate": {
                    "type": "string",
                    "enum": [s.value for s in OwnerGate],
                },
                "contains_pii": {"type": "boolean"},
                "contains_financial": {"type": "boolean"},
                "contains_health": {"type": "boolean"},
                "token_env": {"type": "string"},
                "allowed_targets": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "max_results_per_query": {
                    "type": "integer", "minimum": 1,
                },
                "requires_consent": {"type": "boolean"},
                "data_never_leaves_vault": {"type": "boolean"},
                "dry_run_available": {"type": "boolean"},
            },
            "additionalProperties": False,
        }


# ── Request / Response types ────────────────────────────────────────────────


@dataclass(frozen=True)
class ConnectorRequest:
    """A request to be routed through the connector gateway."""
    request_id: str
    connector_id: str
    action: str               # "read" | "write" | "draft" | "disconnect"
    target: str               # channel/repo/model/account identifier
    arguments: dict = field(default_factory=dict)
    agent_id: str = "unknown"
    dry_run: bool = False
    idempotency_key: str = ""
    timestamp: float = 0.0

    def to_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "connector_id": self.connector_id,
            "action": self.action,
            "target": self.target,
            "arguments": self.arguments,
            "agent_id": self.agent_id,
            "dry_run": self.dry_run,
            "idempotency_key": self.idempotency_key,
            "timestamp": self.timestamp,
        }


@dataclass(frozen=True)
class ConnectorResponse:
    """Response from the connector gateway."""
    request_id: str
    connector_id: str
    allowed: bool
    reason: str
    action: str
    target: str
    risk_class: str
    dry_run: bool
    approval_required: bool = False
    redacted: bool = False     # whether PII/health/financial data was redacted
    data: Any = None           # actual payload (only for read/allowed)
    error: str = ""            # error message if any

    def to_dict(self) -> dict:
        return {
            "schema": SCHEMA,
            "request_id": self.request_id,
            "connector_id": self.connector_id,
            "allowed": self.allowed,
            "reason": self.reason,
            "action": self.action,
            "target": self.target,
            "risk_class": self.risk_class,
            "dry_run": self.dry_run,
            "approval_required": self.approval_required,
            "redacted": self.redacted,
            "data": self.data,
            "error": self.error,
        }


# ── Built-in connector definitions (seed registry) ──────────────────────────

BUILTIN_CONNECTORS: dict[str, dict] = {
    "telegram": {
        "connector_id": "telegram",
        "title": "Telegram Control Plane",
        "version": "1.0.0",
        "owner": "system",
        "read_scope": "detailed",
        "write_scope": "draft",
        "retention": "session",
        "risk_class": "irreversible",
        "owner_gate": "write_only",
        "contains_pii": False,
        "contains_financial": False,
        "contains_health": False,
        "token_env": "TG_CENTER_BOT_TOKEN",
        "allowed_targets": ("owner_outer_dm", "owner_inner_dm", "legs_forum_group"),
        "max_results_per_query": 50,
        "requires_consent": False,
        "data_never_leaves_vault": True,
        "dry_run_available": True,
    },
    "github": {
        "connector_id": "github",
        "title": "GitHub Research Connector",
        "version": "1.0.0",
        "owner": "system",
        "read_scope": "detailed",
        "write_scope": "approved_write",
        "retention": "short",
        "risk_class": "reversible_write",
        "owner_gate": "always",
        "contains_pii": False,
        "contains_financial": False,
        "contains_health": False,
        "token_env": "GITHUB_TOKEN",
        "allowed_targets": (),
        "max_results_per_query": 100,
        "requires_consent": False,
        "data_never_leaves_vault": True,
        "dry_run_available": True,
    },
    "huggingface": {
        "connector_id": "huggingface",
        "title": "Hugging Face Model Research",
        "version": "1.0.0",
        "owner": "system",
        "read_scope": "metadata",
        "write_scope": "none",
        "retention": "none",
        "risk_class": "read_only",
        "owner_gate": "never",
        "contains_pii": False,
        "contains_financial": False,
        "contains_health": False,
        "token_env": "",            # HF_TOKEN must NOT be created (OWNER-CLOSE)
        "allowed_targets": (),
        "max_results_per_query": 50,
        "requires_consent": False,
        "data_never_leaves_vault": True,
        "dry_run_available": True,
    },
    "email": {
        "connector_id": "email",
        "title": "Email Inbound (Gmail Read-Only)",
        "version": "1.0.0",
        "owner": "system",
        "read_scope": "summarized",
        "write_scope": "none",
        "retention": "ephemeral",
        "risk_class": "read_only",
        "owner_gate": "never",
        "contains_pii": True,
        "contains_financial": False,
        "contains_health": False,
        "token_env": "GMAIL_CLIENT_ID",
        "allowed_targets": (),
        "max_results_per_query": 25,
        "requires_consent": True,
        "data_never_leaves_vault": True,
        "dry_run_available": True,
    },
    "finance": {
        "connector_id": "finance",
        "title": "PocketSmith Finance (Read-Only)",
        "version": "1.0.0",
        "owner": "system",
        "read_scope": "summarized",
        "write_scope": "none",
        "retention": "ephemeral",
        "risk_class": "read_only",
        "owner_gate": "never",
        "contains_pii": True,
        "contains_financial": True,
        "contains_health": False,
        "token_env": "POCKETSMITH_API_KEY",
        "allowed_targets": (),
        "max_results_per_query": 100,
        "requires_consent": True,
        "data_never_leaves_vault": True,
        "dry_run_available": True,
    },
    "healthkit": {
        "connector_id": "healthkit",
        "title": "Apple HealthKit (Read-Only)",
        "version": "1.0.0",
        "owner": "system",
        "read_scope": "summarized",
        "write_scope": "none",
        "retention": "none",
        "risk_class": "read_only",
        "owner_gate": "always",
        "contains_pii": True,
        "contains_financial": False,
        "contains_health": True,
        "token_env": "",            # no token for HealthKit (local device)
        "allowed_targets": (),
        "max_results_per_query": 25,
        "requires_consent": True,
        "data_never_leaves_vault": True,
        "dry_run_available": True,
    },
}
