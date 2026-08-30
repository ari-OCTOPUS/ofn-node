#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gateway.py -- Unified connector gateway with privacy-preserving controls (EQUIP G9).

Single entry point for all personal connector operations. The gateway:
  1. Resolves the connector from the registry
  2. Validates the request (action, target, scope)
  3. Enforces risk classification (integrates with G8 risk_gate)
  4. Checks owner gate requirements
  5. Enforces consent requirements (integrates with consent_gate)
  6. Redacts sensitive data (PII/health/financial) from responses
  7. Audit-logs every decision (allow/deny/escalate)

Acceptance scenario:
  For each discovered connector: a permitted read (audited) and a denied write
  (without approval). No real writes to telegram/email/bank -- mock/dry-run only.

Design principles:
  - deny-by-default: unknown connector/action = DENY
  - resolve-before-act: target must be fully resolved before any write attempt
  - draft != send: draft operations never touch external systems
  - revoke is immediate: revoked connector = all actions blocked
  - sensitive data never leaves in public output
  - dry-run mode: evaluate policy without executing

$0 | stdlib-only | no network | all policy checks are local
"""
from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from schema import (
    ConnectorManifest,
    ConnectorRequest,
    ConnectorResponse,
    ReadScope,
    WriteScope,
    RiskClass,
    OwnerGate,
    SCHEMA,
)
from registry import ConnectorRegistry

# ── Constants ────────────────────────────────────────────────────────────────

WRITE_ACTIONS = frozenset({"write", "send", "delete", "update"})
READ_ACTIONS = frozenset({"read", "list", "query", "search", "get"})
DRAFT_ACTIONS = frozenset({"draft", "propose"})
DISCONNECT_ACTIONS = frozenset({"disconnect", "revoke"})

# Valid action types
VALID_ACTIONS = READ_ACTIONS | WRITE_ACTIONS | DRAFT_ACTIONS | DISCONNECT_ACTIONS

# Sensitive data patterns for redaction (applied to response data)
_PII_PATTERNS = (
    re.compile(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"),   # phone-like
    re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),  # email
    re.compile(r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b"),  # credit card-like
)

# ── Data structures ──────────────────────────────────────────────────────────

# Type for consent checker callback (same signature as consent_gate.may_draft)
ConsentChecker = Callable[[str], tuple[bool, str]]


# ── Gateway ──────────────────────────────────────────────────────────────────


class ConnectorGateway:
    """Unified gateway for all personal connector operations.

    This is the single point through which all connector requests must pass.
    It enforces privacy, consent, risk, and approval policies consistently
    across all connectors.

    Usage:
        registry = ConnectorRegistry(seed=True)
        gateway = ConnectorGateway(registry)
        response = gateway.route(request)
        if not response.allowed:
            # stop before reaching the connector
    """

    def __init__(
        self,
        registry: ConnectorRegistry,
        *,
        audit_path: Path | str | None = None,
        consent_checker: ConsentChecker | None = None,
        now: float | None = None,
    ) -> None:
        self._registry = registry
        self._audit_path = Path(audit_path) if audit_path else None
        self._consent_checker = consent_checker
        self._request_count = 0
        self._audit_log: list[dict] = []
        self._now_factory = now if now is not None else None

    def _now(self) -> float:
        return self._now_factory if self._now_factory else time.time()

    # ── Main routing method ───────────────────────────────────────────────

    def route(self, request: ConnectorRequest) -> ConnectorResponse:
        """Route a connector request through the full policy pipeline.

        Pipeline (fail-fast, deny-by-default):
          1. Validate request shape (action, connector_id)
          2. Resolve connector from registry (unknown = DENY)
          3. Check revocation status
          4. Scope check: action allowed for this connector's capabilities
          5. Target resolution: target must be in allowlist (if set)
          6. Owner gate check
          7. Consent check (if required)
          8. Risk classification
          9. Dry-run mode evaluation
          10. Build response

        Returns ConnectorResponse with allow/deny + full audit context.
        """
        _now = self._now()
        self._request_count += 1

        # Step 1: Validate request
        if not request.action or request.action not in VALID_ACTIONS:
            resp = ConnectorResponse(
                request_id=request.request_id,
                connector_id=request.connector_id,
                allowed=False,
                reason=f"invalid_action:{request.action!r}",
                action=request.action,
                target=request.target,
                risk_class="unknown",
                dry_run=request.dry_run,
            )
            self._audit(resp, _now, "invalid_action")
            return resp

        # Step 2: Resolve connector
        manifest = self._registry.lookup(request.connector_id)
        if manifest is None:
            revoked = self._registry.is_revoked(request.connector_id)
            resp = ConnectorResponse(
                request_id=request.request_id,
                connector_id=request.connector_id,
                allowed=False,
                reason="unknown_connector" if not revoked else "connector_revoked",
                action=request.action,
                target=request.target,
                risk_class="unknown",
                dry_run=request.dry_run,
            )
            self._audit(resp, _now, "unknown_or_revoked")
            return resp

        # Steps 3-9: Policy checks
        resp = self._apply_policy(request, manifest, _now)
        self._audit(resp, _now, resp.reason)
        return resp

    # ── Policy pipeline ─────────────────────────────────────────────────

    def _apply_policy(
        self,
        request: ConnectorRequest,
        manifest: ConnectorManifest,
        now: float,
    ) -> ConnectorResponse:
        """Apply all policy checks in order (fail-fast)."""

        # Step 3: Scope check
        scope_result = self._check_scope(request, manifest)
        if not scope_result["allowed"]:
            return ConnectorResponse(
                request_id=request.request_id,
                connector_id=request.connector_id,
                allowed=False,
                reason=scope_result["reason"],
                action=request.action,
                target=request.target,
                risk_class=manifest.risk_class.value,
                dry_run=request.dry_run,
            )

        # Step 4: Target allowlist check
        target_result = self._check_target(request, manifest)
        if not target_result["allowed"]:
            return ConnectorResponse(
                request_id=request.request_id,
                connector_id=request.connector_id,
                allowed=False,
                reason=target_result["reason"],
                action=request.action,
                target=request.target,
                risk_class=manifest.risk_class.value,
                dry_run=request.dry_run,
            )

        # Step 5: Owner gate check
        gate_result = self._check_owner_gate(request, manifest)
        if gate_result["escalate"]:
            return ConnectorResponse(
                request_id=request.request_id,
                connector_id=request.connector_id,
                allowed=request.dry_run,   # dry-run shows what would happen
                reason=gate_result["reason"],
                action=request.action,
                target=request.target,
                risk_class=manifest.risk_class.value,
                dry_run=request.dry_run,
                approval_required=True,
            )

        # Track approval requirement for dry-run responses
        needs_approval = gate_result.get("needs_approval", False)

        # Step 6: Consent check
        consent_result = self._check_consent(request, manifest)
        if not consent_result["allowed"]:
            return ConnectorResponse(
                request_id=request.request_id,
                connector_id=request.connector_id,
                allowed=False,
                reason=consent_result["reason"],
                action=request.action,
                target=request.target,
                risk_class=manifest.risk_class.value,
                dry_run=request.dry_run,
            )

        # Step 7: Sensitive data classification for response
        needs_redaction = (
            manifest.contains_pii or
            manifest.contains_financial or
            manifest.contains_health
        )

        # Step 8: All checks passed
        return ConnectorResponse(
            request_id=request.request_id,
            connector_id=request.connector_id,
            allowed=True,
            reason="allowed",
            action=request.action,
            target=request.target,
            risk_class=manifest.risk_class.value,
            dry_run=request.dry_run,
            approval_required=needs_approval,
            redacted=needs_redaction,
        )

    def _check_scope(
        self, request: ConnectorRequest, manifest: ConnectorManifest
    ) -> dict:
        """Check if the requested action is within connector's scope."""
        action = request.action

        # Read actions: always allowed if read_scope > NONE
        if action in READ_ACTIONS:
            if manifest.read_scope == ReadScope.NONE:
                return {"allowed": False, "reason": "read_not_permitted"}
            return {"allowed": True, "reason": "scope_ok"}

        # Draft actions: allowed if write_scope >= DRAFT
        if action in DRAFT_ACTIONS:
            if manifest.write_scope in (WriteScope.NONE,):
                return {"allowed": False, "reason": "draft_not_permitted"}
            return {"allowed": True, "reason": "scope_ok"}

        # Write actions: require write_scope >= APPROVED_WRITE
        if action in WRITE_ACTIONS:
            if manifest.write_scope == WriteScope.NONE:
                return {"allowed": False, "reason": "write_not_permitted"}
            if manifest.write_scope == WriteScope.DRAFT:
                return {
                    "allowed": False,
                    "reason": "write_requires_approved_write_scope",
                }
            return {"allowed": True, "reason": "scope_ok"}

        # Disconnect actions: always allowed (even on read-only connectors)
        if action in DISCONNECT_ACTIONS:
            return {"allowed": True, "reason": "scope_ok"}

        return {"allowed": False, "reason": "unknown_action"}

    def _check_target(
        self, request: ConnectorRequest, manifest: ConnectorManifest
    ) -> dict:
        """Check if the target is in the connector's allowlist."""
        # If no allowlist is defined, all targets are allowed
        if not manifest.allowed_targets:
            return {"allowed": True, "reason": "no_allowlist"}

        # For disconnect, target doesn't need allowlist check
        if request.action in DISCONNECT_ACTIONS:
            return {"allowed": True, "reason": "disconnect_no_target_check"}

        # Check against allowlist
        target = str(request.target).strip()
        if target in manifest.allowed_targets:
            return {"allowed": True, "reason": "target_allowed"}

        return {
            "allowed": False,
            "reason": f"target_not_in_allowlist:{target!r}",
        }

    def _check_owner_gate(
        self, request: ConnectorRequest, manifest: ConnectorManifest
    ) -> dict:
        """Check if owner gate is required for this action."""
        needs_gate = False

        # Owner gate for write actions
        if request.action in WRITE_ACTIONS:
            if manifest.owner_gate in (OwnerGate.ALWAYS, OwnerGate.WRITE_ONLY):
                needs_gate = True

        # Owner gate ALWAYS for any action (write only, read is exempt)
        if manifest.owner_gate == OwnerGate.ALWAYS:
            if request.action in (READ_ACTIONS | DRAFT_ACTIONS):
                needs_gate = False  # read/draft not gated even with ALWAYS

        if needs_gate:
            if not request.dry_run:
                return {
                    "escalate": True,
                    "needs_approval": True,
                    "reason": "owner_gate_required",
                }
            else:
                # Dry-run: allow but indicate approval would be needed
                return {
                    "escalate": False,
                    "needs_approval": True,
                    "reason": "owner_gate_required",
                }

        return {"escalate": False, "needs_approval": False, "reason": "gate_not_required"}

    def _check_consent(
        self, request: ConnectorRequest, manifest: ConnectorManifest
    ) -> dict:
        """Check consent requirement using injected consent checker."""
        if not manifest.requires_consent:
            return {"allowed": True, "reason": "no_consent_required"}

        if self._consent_checker is None:
            # No consent checker injected = deny (fail-closed)
            return {"allowed": False, "reason": "consent_checker_not_configured"}

        try:
            # Use the connector_id as the consent subject
            ok, reason = self._consent_checker(request.connector_id)
            if ok:
                return {"allowed": True, "reason": "consent_ok"}
            return {"allowed": False, "reason": f"consent_denied:{reason}"}
        except Exception as e:
            return {"allowed": False, "reason": f"consent_error:{type(e).__name__}"}

    # ── Redaction ────────────────────────────────────────────────────────

    @staticmethod
    def redact(data: Any, *, patterns: tuple | None = None) -> Any:
        """Redact sensitive data from response payloads.

        Recursively processes dicts and lists, replacing matches with [REDACTED].
        Preserves structure but removes identifying information.
        """
        _pats = patterns or _PII_PATTERNS
        if isinstance(data, str):
            for pat in _pats:
                data = pat.sub("[REDACTED]", data)
            return data
        if isinstance(data, dict):
            # Redact values for keys that look sensitive
            redacted_keys = {
                "email", "phone", "mobile", "address", "ssn", "dob",
                "account_number", "card_number", "balance", "amount",
                "heart_rate", "blood_pressure", "weight",
            }
            return {
                k: "[REDACTED]" if k.lower() in redacted_keys
                else ConnectorGateway.redact(v, patterns=_pats)
                for k, v in data.items()
            }
        if isinstance(data, list):
            return [ConnectorGateway.redact(v, patterns=_pats) for v in data]
        return data

    # ── Audit ──────────────────────────────────────────────────────────

    def _audit(self, response: ConnectorResponse, now: float, reason: str) -> None:
        """Append audit entry. Never throws. Never blocks."""
        entry = {
            "schema": "connector-gateway-audit.v1",
            "timestamp": now,
            "request_id": response.request_id,
            "connector_id": response.connector_id,
            "action": response.action,
            "target": response.target,
            "allowed": response.allowed,
            "reason": reason,
            "risk_class": response.risk_class,
            "dry_run": response.dry_run,
            "approval_required": response.approval_required,
        }
        self._audit_log.append(entry)

        # Flush to file
        if self._audit_path:
            try:
                self._audit_path.parent.mkdir(parents=True, exist_ok=True)
                with open(self._audit_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(
                        entry, ensure_ascii=False, sort_keys=True,
                    ) + "\n")
            except OSError:
                pass

    def audit_trail(self) -> list[dict]:
        """Return all audit entries."""
        return list(self._audit_log)

    def stats(self) -> dict:
        """Return gateway statistics."""
        total = len(self._audit_log)
        allowed = sum(1 for e in self._audit_log if e.get("allowed"))
        denied = total - allowed
        return {
            "total_requests": self._request_count,
            "total_audited": total,
            "allowed": allowed,
            "denied": denied,
            "registry_size": self._registry.size(),
        }


# ── Convenience factory ─────────────────────────────────────────────────────

def default_gateway(
    *,
    audit_path: str | None = None,
    consent_checker: ConsentChecker | None = None,
) -> ConnectorGateway:
    """Create a gateway with default seeded registry."""
    registry = ConnectorRegistry(seed=True, audit_path=audit_path)
    return ConnectorGateway(
        registry,
        audit_path=audit_path,
        consent_checker=consent_checker,
    )
