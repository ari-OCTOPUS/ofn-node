#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_connector_gateway.py -- Comprehensive tests for G9 connector gateway.

Tests cover all 6 builtin connectors + custom connectors:
  - Schema validation (ConnectorManifest)
  - Registry operations (register, revoke, lookup, list)
  - Gateway routing (read/write/draft/disconnect per connector)
  - Scope enforcement (read-only connectors deny writes)
  - Target allowlist enforcement
  - Owner gate escalation
  - Consent enforcement
  - Revocation (immediate block)
  - Unknown connector denial
  - Dry-run mode
  - PII/health/financial redaction
  - Audit trail completeness
  - Negative/malformed inputs
  - Idempotency
  - Cross-connector isolation

Acceptance scenario per connector:
  - One permitted read (audited) -> allowed
  - One denied write (without approval) -> denied

No real writes. No external network. Pure Python assertions.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
for _p in (str(_OPS), str(_OPS / "connectors")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from connectors.schema import (
    SCHEMA,
    BUILTIN_CONNECTORS,
    ConnectorManifest,
    ConnectorRequest,
    ConnectorResponse,
    ConnectorStatus,
    OwnerGate,
    ReadScope,
    RetentionClass,
    RiskClass,
    WriteScope,
)
from connectors.registry import ConnectorRegistry
from connectors.gateway import ConnectorGateway, default_gateway


_pass = 0
_fail = 0


def _ok(label: str) -> None:
    global _pass
    _pass += 1
    print(f"  [PASS] {label}")


def _no(label: str, detail: str = "") -> None:
    global _fail
    _fail += 1
    print(f"  [FAIL] {label} {detail}")


def _eq(a, b, label: str) -> bool:
    if a == b:
        _ok(label)
        return True
    _no(label, f"expected {b!r}, got {a!r}")
    return False


def _true(v, label: str) -> bool:
    if v is True:
        _ok(label)
        return True
    _no(label, f"expected True, got {v!r}")
    return False


def _false(v, label: str) -> bool:
    if v is False:
        _ok(label)
        return True
    _no(label, f"expected False, got {v!r}")
    return False


def _isinstance(v, t, label: str) -> bool:
    if isinstance(v, t):
        _ok(label)
        return True
    _no(label, f"expected {t.__name__}, got {type(v).__name__}")
    return False


# ═══════════════════════════════════════════════════════════════════════════
# SECTION A: Schema validation
# ═══════════════════════════════════════════════════════════════════════════

def test_schema_builtins_valid():
    """All builtin connectors must produce valid manifests."""
    print("\n--- Schema: builtin connectors ---")
    for cid, spec in BUILTIN_CONNECTORS.items():
        try:
            m = ConnectorManifest(**{
                **spec, "registered_at": 0.0, "registered_by": "test"
            })
            _isinstance(m, ConnectorManifest, f"builtin_{cid}_valid")
            _eq(m.connector_id, cid, f"builtin_{cid}_id_matches")
            _isinstance(m.risk_class, RiskClass, f"builtin_{cid}_risk_is_enum")
            _isinstance(m.read_scope, ReadScope, f"builtin_{cid}_read_is_enum")
            _isinstance(m.write_scope, WriteScope, f"builtin_{cid}_write_is_enum")
        except Exception as e:
            _no(f"builtin_{cid}_construction", str(e))


def test_schema_health_readonly():
    """Health connectors must reject write_scope != NONE."""
    print("\n--- Schema: health must be read-only ---")
    try:
        m = ConnectorManifest(
            connector_id="test-health-bad",
            title="Bad Health",
            version="1.0",
            owner="test",
            read_scope=ReadScope.DETAILED,
            write_scope=WriteScope.DRAFT,  # should fail
            retention=RetentionClass.NONE,
            risk_class=RiskClass.READ_ONLY,
            owner_gate=OwnerGate.ALWAYS,
            contains_health=True,
        )
        _no("health_write_rejected", "should have raised ValueError")
    except ValueError:
        _ok("health_write_rejected")


def test_schema_finance_readonly_or_draft():
    """Financial connectors must be NONE or DRAFT only."""
    print("\n--- Schema: finance read-only or draft ---")
    try:
        m = ConnectorManifest(
            connector_id="test-fin-bad",
            title="Bad Finance",
            version="1.0",
            owner="test",
            read_scope=ReadScope.DETAILED,
            write_scope=WriteScope.DIRECT_WRITE,  # should fail
            retention=RetentionClass.NONE,
            risk_class=RiskClass.FINANCIAL,
            owner_gate=OwnerGate.ALWAYS,
            contains_financial=True,
        )
        _no("finance_direct_write_rejected", "should have raised ValueError")
    except ValueError:
        _ok("finance_direct_write_rejected")


def test_schema_forbidden_rejected():
    """Forbidden risk_class cannot be registered."""
    print("\n--- Schema: forbidden risk_class rejected ---")
    try:
        m = ConnectorManifest(
            connector_id="test-forbidden",
            title="Forbidden",
            version="1.0",
            owner="test",
            read_scope=ReadScope.NONE,
            write_scope=WriteScope.NONE,
            retention=RetentionClass.NONE,
            risk_class=RiskClass.FORBIDDEN,
            owner_gate=OwnerGate.NEVER,
        )
        _no("forbidden_rejected", "should have raised ValueError")
    except ValueError:
        _ok("forbidden_rejected")


def test_schema_invalid_connector_id():
    """Invalid connector_id formats are rejected."""
    print("\n--- Schema: invalid connector_id ---")
    bad_ids = ["", "A" * 100, "123", "-bad", "has space", "UPPER"]
    for bid in bad_ids:
        try:
            ConnectorManifest(
                connector_id=bid,
                title="T", version="1.0", owner="test",
                read_scope=ReadScope.NONE, write_scope=WriteScope.NONE,
                retention=RetentionClass.NONE,
                risk_class=RiskClass.READ_ONLY,
                owner_gate=OwnerGate.NEVER,
            )
            _no(f"bad_id_{bid[:10]}", "should have raised")
        except ValueError:
            _ok(f"bad_id_{bid[:10]}")


def test_schema_serialization():
    """Manifest to_dict/from_dict round-trips correctly."""
    print("\n--- Schema: serialization round-trip ---")
    spec = dict(BUILTIN_CONNECTORS["telegram"])
    spec["registered_at"] = 1234567890.0
    spec["registered_by"] = "test-actor"
    m1 = ConnectorManifest(**spec)
    d = m1.to_dict()
    _isinstance(d, dict, "to_dict_returns_dict")
    _eq(d["connector_id"], "telegram", "to_dict_id")
    _eq(d["risk_class"], "irreversible", "to_dict_risk_class")

    m2 = ConnectorManifest.from_dict(d)
    _eq(m2.connector_id, m1.connector_id, "from_dict_id_match")
    _eq(m2.risk_class, m1.risk_class, "from_dict_risk_match")
    _eq(m2.write_scope, m1.write_scope, "from_dict_write_match")


def test_schema_json_schema():
    """JSON Schema generation works."""
    print("\n--- Schema: JSON Schema ---")
    js = ConnectorManifest.json_schema()
    _isinstance(js, dict, "json_schema_is_dict")
    _eq(js["$id"], f"octopus.{SCHEMA}", "json_schema_id")
    _true("connector_id" in js.get("required", []), "connector_id_required")
    _true("risk_class" in js.get("required", []), "risk_class_required")


# ═══════════════════════════════════════════════════════════════════════════
# SECTION B: Registry
# ═══════════════════════════════════════════════════════════════════════════

def test_registry_seed():
    """Seeded registry has all 6 builtin connectors."""
    print("\n--- Registry: seed ---")
    reg = ConnectorRegistry(seed=True)
    _eq(reg.size(), 6, "seed_size_6")
    for cid in ("telegram", "github", "huggingface", "email", "finance", "healthkit"):
        m = reg.lookup(cid)
        if m is None:
            _no(f"seed_has_{cid}", "not found")
        else:
            _ok(f"seed_has_{cid}")


def test_registry_lookup_unknown():
    """Unknown connector returns None."""
    print("\n--- Registry: unknown lookup ---")
    reg = ConnectorRegistry(seed=True)
    _true(reg.lookup("nonexistent") is None, "unknown_is_none")
    _true(reg.lookup("") is None, "empty_is_none")
    _true(reg.lookup("GITHUB") is None, "case_sensitive_none")


def test_registry_register_custom():
    """Custom connector registration works."""
    print("\n--- Registry: register custom ---")
    reg = ConnectorRegistry(seed=True)
    m = ConnectorManifest(
        connector_id="custom_test",
        title="Custom Test Connector",
        version="1.0",
        owner="test-owner",
        read_scope=ReadScope.METADATA,
        write_scope=WriteScope.NONE,
        retention=RetentionClass.EPHEMERAL,
        risk_class=RiskClass.READ_ONLY,
        owner_gate=OwnerGate.NEVER,
    )
    _true(reg.register(m, actor="test"), "register_custom")
    _eq(reg.size(), 7, "size_after_register")
    looked = reg.lookup("custom_test")
    if looked and looked.connector_id == "custom_test":
        _ok("lookup_custom")
    else:
        _no("lookup_custom", "not found or wrong id")


def test_registry_revoke():
    """Revoked connector is immediately blocked."""
    print("\n--- Registry: revoke ---")
    reg = ConnectorRegistry(seed=True)
    _true(reg.revoke("telegram", actor="owner"), "revoke_telegram")
    _true(reg.is_revoked("telegram"), "is_revoked")
    _true(reg.lookup("telegram") is None, "lookup_revoked_none")
    _eq(reg.size(), 5, "size_after_revoke")


def test_registry_re_register_revoked():
    """Re-registering a revoked connector lifts the revocation."""
    print("\n--- Registry: re-register revoked ---")
    reg = ConnectorRegistry(seed=True)
    reg.revoke("telegram", actor="owner")
    spec = dict(BUILTIN_CONNECTORS["telegram"])
    spec["registered_at"] = 100.0
    spec["registered_by"] = "re-actor"
    m = ConnectorManifest(**spec)
    _true(reg.register(m, actor="re-actor"), "re_register")
    _false(reg.is_revoked("telegram"), "not_revoked_after_re_register")
    _true(reg.lookup("telegram") is not None, "lookup_after_re_register")


def test_registry_list_all():
    """list_all returns all connectors with status."""
    print("\n--- Registry: list_all ---")
    reg = ConnectorRegistry(seed=True)
    reg.revoke("email", actor="owner")
    all_list = reg.list_all(include_revoked=True)
    _eq(len(all_list), 6, "list_all_with_revoked")
    active_list = reg.list_all(include_revoked=False)
    _eq(len(active_list), 5, "list_active_only")
    revoked_entry = [e for e in all_list if e.get("connector_id") == "email"][0]
    _eq(revoked_entry["status"], "revoked", "email_status_revoked")


def test_registry_audit_trail():
    """Registry operations produce audit entries."""
    print("\n--- Registry: audit trail ---")
    reg = ConnectorRegistry(seed=True)
    trail = reg.audit_trail()
    # 6 seed entries
    _true(len(trail) >= 6, "audit_has_seed_entries")
    seed_events = [e for e in trail if e["event"] == "register" and e["actor"] == "system-seed"]
    _eq(len(seed_events), 6, "seed_register_events")

    reg.revoke("telegram", actor="owner")
    trail2 = reg.audit_trail()
    revoke_events = [e for e in trail2 if e["event"] == "revoke"]
    _eq(len(revoke_events), 1, "revoke_event")


def test_registry_audit_persist():
    """Audit trail can be written to file."""
    print("\n--- Registry: audit persist ---")
    with tempfile.NamedTemporaryFile(
        suffix=".jsonl", mode="w", delete=False, encoding="utf-8"
    ) as f:
        tmppath = f.name
    try:
        reg = ConnectorRegistry(seed=True, audit_path=tmppath)
        reg.revoke("telegram", actor="owner")
        content = Path(tmppath).read_text(encoding="utf-8")
        lines = [l for l in content.strip().splitlines() if l.strip()]
        _true(len(lines) >= 7, f"audit_file_lines={len(lines)}")
        # Parse first line
        first = json.loads(lines[0])
        _eq(first["schema"], "connector-registry-audit.v1", "audit_schema")
    finally:
        os.unlink(tmppath)


# ═══════════════════════════════════════════════════════════════════════════
# SECTION C: Gateway routing — per-connector acceptance scenarios
# ═══════════════════════════════════════════════════════════════════════════

def _make_gateway(consent_checker=None, now=0.0, audit_path=None):
    """Create a gateway with seeded registry and optional consent checker."""
    reg = ConnectorRegistry(seed=True, now=now, audit_path=audit_path)
    return ConnectorGateway(reg, consent_checker=consent_checker,
                             audit_path=audit_path, now=now)


def _req(connector_id, action, target="x", dry_run=False, ts=0.0, agent="unknown"):
    return ConnectorRequest(
        request_id=f"req-{connector_id}-{action}",
        connector_id=connector_id,
        action=action,
        target=target,
        dry_run=dry_run,
        timestamp=ts,
        agent_id=agent,
    )


# --- Telegram ---

def test_telegram_read_allowed():
    """Telegram: read to allowed target is permitted."""
    print("\n--- Telegram: read allowed ---")
    gw = _make_gateway()
    resp = gw.route(_req("telegram", "read", "owner_outer_dm"))
    _true(resp.allowed, "tg_read_allowed")
    _eq(resp.reason, "allowed", "tg_read_reason")
    _eq(resp.risk_class, "irreversible", "tg_risk_class")


def test_telegram_write_denied_draft_scope():
    """Telegram: write denied because scope is DRAFT (not APPROVED_WRITE)."""
    print("\n--- Telegram: write denied (draft scope) ---")
    gw = _make_gateway()
    resp = gw.route(_req("telegram", "write", "owner_outer_dm"))
    _false(resp.allowed, "tg_write_denied")
    _eq(resp.reason, "write_requires_approved_write_scope", "tg_write_reason")


def test_telegram_draft_allowed():
    """Telegram: draft is allowed (write_scope >= DRAFT)."""
    print("\n--- Telegram: draft allowed ---")
    gw = _make_gateway()
    resp = gw.route(_req("telegram", "draft", "owner_outer_dm"))
    _true(resp.allowed, "tg_draft_allowed")


def test_telegram_target_allowlisted():
    """Telegram: target must be in allowlist."""
    print("\n--- Telegram: target allowlist ---")
    gw = _make_gateway()
    # Allowed target
    resp1 = gw.route(_req("telegram", "read", "owner_outer_dm"))
    _true(resp1.allowed, "tg_target_allowed_dm")
    # Disallowed target
    resp2 = gw.route(_req("telegram", "read", "some_random_chat"))
    _false(resp2.allowed, "tg_target_blocked")
    _true("target_not_in_allowlist" in resp2.reason, "tg_target_blocked_reason")


def test_telegram_disconnect_allowed():
    """Telegram: disconnect always allowed."""
    print("\n--- Telegram: disconnect ---")
    gw = _make_gateway()
    resp = gw.route(_req("telegram", "disconnect", "owner_outer_dm"))
    _true(resp.allowed, "tg_disconnect_allowed")


# --- GitHub ---

def test_github_read_allowed():
    """GitHub: read is permitted."""
    print("\n--- GitHub: read allowed ---")
    gw = _make_gateway()
    resp = gw.route(_req("github", "read", "octopus-repo"))
    _true(resp.allowed, "gh_read_allowed")
    _eq(resp.risk_class, "reversible_write", "gh_risk_class")


def test_github_write_without_approval():
    """GitHub: write denied without owner approval."""
    print("\n--- GitHub: write denied (owner_gate=always) ---")
    gw = _make_gateway()
    resp = gw.route(_req("github", "write", "octopus-repo"))
    _false(resp.allowed, "gh_write_denied")
    _true(resp.approval_required, "gh_write_approval_required")


def test_github_write_dry_run():
    """GitHub: write allowed in dry-run mode (shows what would happen)."""
    print("\n--- GitHub: write dry-run ---")
    gw = _make_gateway()
    resp = gw.route(_req("github", "write", "octopus-repo", dry_run=True))
    _true(resp.allowed, "gh_write_dryrun_allowed")
    _true(resp.dry_run, "gh_write_dryrun_flag")
    _true(resp.approval_required, "gh_write_dryrun_approval")


# --- Hugging Face ---

def test_huggingface_read_allowed():
    """HuggingFace: metadata read is allowed."""
    print("\n--- HuggingFace: read allowed ---")
    gw = _make_gateway()
    resp = gw.route(_req("huggingface", "read", "some-model"))
    _true(resp.allowed, "hf_read_allowed")
    _eq(resp.risk_class, "read_only", "hf_risk_class")


def test_huggingface_write_denied():
    """HuggingFace: write denied (write_scope=NONE, HF_TOKEN absent)."""
    print("\n--- HuggingFace: write denied ---")
    gw = _make_gateway()
    resp = gw.route(_req("huggingface", "write", "some-model"))
    _false(resp.allowed, "hf_write_denied")
    _eq(resp.reason, "write_not_permitted", "hf_write_reason")


# --- Email ---

def test_email_read_with_consent():
    """Email: read allowed when consent checker passes."""
    print("\n--- Email: read with consent ---")
    gw = _make_gateway(consent_checker=lambda cid: (True, "ok"))
    resp = gw.route(_req("email", "read", "inbox"))
    _true(resp.allowed, "email_read_with_consent")
    _true(resp.redacted, "email_redacted_flag")


def test_email_read_without_consent():
    """Email: read denied when no consent checker configured (fail-closed)."""
    print("\n--- Email: read without consent ---")
    gw = _make_gateway(consent_checker=None)
    resp = gw.route(_req("email", "read", "inbox"))
    _false(resp.allowed, "email_read_no_consent")
    _true("consent_checker_not_configured" in resp.reason, "email_no_consent_reason")


def test_email_read_consent_denied():
    """Email: read denied when consent checker rejects."""
    print("\n--- Email: read consent denied ---")
    gw = _make_gateway(consent_checker=lambda cid: (False, "withheld"))
    resp = gw.route(_req("email", "read", "inbox"))
    _false(resp.allowed, "email_read_consent_denied")
    _true("consent_denied" in resp.reason, "email_consent_denied_reason")


def test_email_write_denied():
    """Email: write denied (write_scope=NONE)."""
    print("\n--- Email: write denied ---")
    gw = _make_gateway(consent_checker=lambda cid: (True, "ok"))
    resp = gw.route(_req("email", "write", "inbox"))
    _false(resp.allowed, "email_write_denied")


# --- Finance (PocketSmith) ---

def test_finance_read_with_consent():
    """Finance: read allowed with consent."""
    print("\n--- Finance: read with consent ---")
    gw = _make_gateway(consent_checker=lambda cid: (True, "ok"))
    resp = gw.route(_req("finance", "read", "accounts"))
    _true(resp.allowed, "fin_read_allowed")
    _true(resp.redacted, "fin_redacted")
    _eq(resp.risk_class, "read_only", "fin_risk_class")


def test_finance_read_without_consent():
    """Finance: read denied without consent (fail-closed)."""
    print("\n--- Finance: read without consent ---")
    gw = _make_gateway(consent_checker=None)
    resp = gw.route(_req("finance", "read", "accounts"))
    _false(resp.allowed, "fin_read_no_consent")


def test_finance_write_denied():
    """Finance: write denied (write_scope=NONE)."""
    print("\n--- Finance: write denied ---")
    gw = _make_gateway(consent_checker=lambda cid: (True, "ok"))
    resp = gw.route(_req("finance", "write", "accounts"))
    _false(resp.allowed, "fin_write_denied")


def test_finance_draft_denied():
    """Finance: draft denied (write_scope=NONE means no draft either)."""
    print("\n--- Finance: draft denied ---")
    gw = _make_gateway(consent_checker=lambda cid: (True, "ok"))
    resp = gw.route(_req("finance", "draft", "accounts"))
    _false(resp.allowed, "fin_draft_denied")


# --- HealthKit ---

def test_healthkit_read_with_consent():
    """HealthKit: read allowed with consent + owner gate."""
    print("\n--- HealthKit: read with consent ---")
    gw = _make_gateway(consent_checker=lambda cid: (True, "ok"))
    resp = gw.route(_req("healthkit", "read", "heart_rate"))
    _true(resp.allowed, "hk_read_allowed")
    _true(resp.redacted, "hk_redacted")


def test_healthkit_read_without_consent():
    """HealthKit: read denied without consent."""
    print("\n--- HealthKit: read without consent ---")
    gw = _make_gateway(consent_checker=None)
    resp = gw.route(_req("healthkit", "read", "heart_rate"))
    _false(resp.allowed, "hk_read_no_consent")


def test_healthkit_write_denied():
    """HealthKit: write denied (write_scope=NONE, structural firewall)."""
    print("\n--- HealthKit: write denied ---")
    gw = _make_gateway(consent_checker=lambda cid: (True, "ok"))
    resp = gw.route(_req("healthkit", "write", "heart_rate"))
    _false(resp.allowed, "hk_write_denied")


# ═══════════════════════════════════════════════════════════════════════════
# SECTION D: Cross-connector gateway behaviors
# ═══════════════════════════════════════════════════════════════════════════

def test_unknown_connector_denied():
    """Unknown connector always denied."""
    print("\n--- Gateway: unknown connector ---")
    gw = _make_gateway()
    resp = gw.route(_req("nonexistent_connector", "read", "x"))
    _false(resp.allowed, "unknown_denied")
    _eq(resp.reason, "unknown_connector", "unknown_reason")


def test_invalid_action_denied():
    """Invalid action is denied."""
    print("\n--- Gateway: invalid action ---")
    gw = _make_gateway()
    resp = gw.route(_req("telegram", "explode", "x"))
    _false(resp.allowed, "invalid_action_denied")
    _true("invalid_action" in resp.reason, "invalid_action_reason")


def test_empty_action_denied():
    """Empty action is denied."""
    print("\n--- Gateway: empty action ---")
    gw = _make_gateway()
    resp = ConnectorRequest(
        request_id="r-empty", connector_id="telegram", action="", target="x"
    )
    routed = gw.route(resp)
    _false(routed.allowed, "empty_action_denied")


def test_revoked_connector_denied():
    """Revoked connector is denied at gateway level."""
    print("\n--- Gateway: revoked connector ---")
    reg = ConnectorRegistry(seed=True)
    reg.revoke("telegram", actor="owner")
    gw = ConnectorGateway(reg)
    resp = gw.route(_req("telegram", "read", "owner_outer_dm"))
    _false(resp.allowed, "revoked_denied")
    _eq(resp.reason, "connector_revoked", "revoked_reason")


def test_dry_run_never_executes():
    """Dry-run mode shows what would happen without blocking reads."""
    print("\n--- Gateway: dry-run mode ---")
    gw = _make_gateway(consent_checker=lambda cid: (True, "ok"))
    resp = gw.route(_req("telegram", "read", "owner_outer_dm", dry_run=True))
    _true(resp.allowed, "dryrun_read_allowed")
    _true(resp.dry_run, "dryrun_flag")


def test_gateway_audit_trail():
    """All gateway decisions are audit-logged."""
    print("\n--- Gateway: audit trail ---")
    gw = _make_gateway()
    gw.route(_req("telegram", "read", "owner_outer_dm"))
    gw.route(_req("telegram", "write", "owner_outer_dm"))
    gw.route(_req("nonexistent", "read", "x"))

    trail = gw.audit_trail()
    _eq(len(trail), 3, "audit_3_entries")

    # Check first entry
    e0 = trail[0]
    _eq(e0["connector_id"], "telegram", "audit_0_connector")
    _true(e0["allowed"], "audit_0_allowed")
    _eq(e0["action"], "read", "audit_0_action")

    # Check second entry
    e1 = trail[1]
    _false(e1["allowed"], "audit_1_denied")

    # Check third entry
    e2 = trail[2]
    _false(e2["allowed"], "audit_2_denied")


def test_gateway_audit_persist():
    """Gateway audit trail can be written to file."""
    print("\n--- Gateway: audit persist ---")
    with tempfile.NamedTemporaryFile(
        suffix=".jsonl", mode="w", delete=False, encoding="utf-8"
    ) as f:
        tmppath = f.name
    try:
        gw = _make_gateway(audit_path=tmppath)
        gw.route(_req("telegram", "read", "owner_outer_dm"))
        content = Path(tmppath).read_text(encoding="utf-8")
        lines = [l for l in content.strip().splitlines() if l.strip()]
        _true(len(lines) >= 1, f"gw_audit_file_lines={len(lines)}")
        entry = json.loads(lines[-1])
        _eq(entry["schema"], "connector-gateway-audit.v1", "gw_audit_schema")
        _true("request_id" in entry, "gw_audit_has_request_id")
    finally:
        os.unlink(tmppath)


def test_gateway_stats():
    """Gateway stats are accurate."""
    print("\n--- Gateway: stats ---")
    gw = _make_gateway()
    gw.route(_req("telegram", "read", "owner_outer_dm"))
    gw.route(_req("telegram", "write", "owner_outer_dm"))
    gw.route(_req("nonexistent", "read", "x"))
    stats = gw.stats()
    _eq(stats["total_requests"], 3, "stats_total")
    _eq(stats["registry_size"], 6, "stats_registry_size")


# ═══════════════════════════════════════════════════════════════════════════
# SECTION E: Redaction
# ═══════════════════════════════════════════════════════════════════════════

def test_redact_pii():
    """PII patterns are redacted from strings."""
    print("\n--- Redaction: PII ---")
    data = "Call me at 555-123-4567 or email test@example.com"
    result = ConnectorGateway.redact(data)
    _true("[REDACTED]" in result, "phone_redacted")
    _true("test@example.com" not in result, "email_removed")
    _true("[REDACTED]" in result.split(" or ")[1], "email_redacted")


def test_redact_dict():
    """Sensitive keys in dicts are redacted."""
    print("\n--- Redaction: dict keys ---")
    data = {
        "name": "Test",
        "email": "secret@example.com",
        "balance": 1234.56,
        "heart_rate": 72,
        "normal_field": "visible",
    }
    result = ConnectorGateway.redact(data)
    _eq(result["name"], "Test", "name_not_redacted")
    _eq(result["email"], "[REDACTED]", "email_redacted")
    _eq(result["balance"], "[REDACTED]", "balance_redacted")
    _eq(result["heart_rate"], "[REDACTED]", "heart_rate_redacted")
    _eq(result["normal_field"], "visible", "normal_visible")


def test_redact_nested():
    """Nested structures are redacted recursively."""
    print("\n--- Redaction: nested ---")
    data = {"user": {"email": "a@b.com", "phone": "555-000-0000"}}
    result = ConnectorGateway.redact(data)
    _eq(result["user"]["email"], "[REDACTED]", "nested_email")
    _eq(result["user"]["phone"], "[REDACTED]", "nested_phone")


def test_redact_list():
    """Lists are redacted element-wise."""
    print("\n--- Redaction: list ---")
    data = ["test@example.com", "normal text", "555-111-2222"]
    result = ConnectorGateway.redact(data)
    _eq(result[0], "[REDACTED]", "list_email_redacted")
    _eq(result[1], "normal text", "list_normal_preserved")
    _eq(result[2], "[REDACTED]", "list_phone_redacted")


# ═══════════════════════════════════════════════════════════════════════════
# SECTION F: Negative / adversarial inputs
# ═══════════════════════════════════════════════════════════════════════════

def test_adversarial_connector_id():
    """Adversarial connector_id patterns are denied."""
    print("\n--- Adversarial: connector_id injection ---")
    gw = _make_gateway()
    for bad_id in ["../etc/passwd", "; rm -rf /", "../../.env",
                   "CONNECTION; DROP TABLE", "telegram\x00evil"]:
        resp = gw.route(ConnectorRequest(
            request_id="r-adv", connector_id=bad_id,
            action="read", target="x",
        ))
        _false(resp.allowed, f"adv_id_{bad_id[:12]}")


def test_adversarial_target():
    """Adversarial target patterns in allowlisted connectors."""
    print("\n--- Adversarial: target injection ---")
    gw = _make_gateway()
    for bad_target in ["owner_outer_dm; DROP", "../../../etc/shadow",
                       "owner_outer_dm\x00evil_target"]:
        resp = gw.route(_req("telegram", "read", bad_target))
        _false(resp.allowed, f"adv_target_{bad_target[:12]}")


def test_adversarial_consent_checker_error():
    """Consent checker raising exception = deny (fail-closed)."""
    print("\n--- Adversarial: consent checker error ---")
    def bad_checker(cid):
        raise RuntimeError("consent service unavailable")
    gw = _make_gateway(consent_checker=bad_checker)
    resp = gw.route(_req("email", "read", "inbox"))
    _false(resp.allowed, "consent_error_denied")
    _true("consent_error" in resp.reason, "consent_error_reason")


def test_empty_request():
    """Empty/minimal request handling."""
    print("\n--- Adversarial: minimal request ---")
    gw = _make_gateway()
    resp = ConnectorRequest(
        request_id="", connector_id="", action="", target=""
    )
    routed = gw.route(resp)
    _false(routed.allowed, "empty_request_denied")


# ═══════════════════════════════════════════════════════════════════════════
# SECTION G: Request/Response data classes
# ═══════════════════════════════════════════════════════════════════════════

def test_request_response_serialization():
    """ConnectorRequest and ConnectorResponse serialize correctly."""
    print("\n--- Data classes: serialization ---")
    req = _req("telegram", "read", "owner_outer_dm")
    d = req.to_dict()
    _isinstance(d, dict, "req_to_dict")
    _eq(d["connector_id"], "telegram", "req_dict_id")

    resp = ConnectorResponse(
        request_id="r1", connector_id="telegram",
        allowed=True, reason="ok", action="read",
        target="owner_outer_dm", risk_class="irreversible",
        dry_run=False,
    )
    rd = resp.to_dict()
    _eq(rd["schema"], SCHEMA, "resp_schema")
    _true(rd["allowed"], "resp_allowed")


def test_response_serializable():
    """Response with data payload is JSON-serializable."""
    print("\n--- Data classes: response JSON safe ---")
    resp = ConnectorResponse(
        request_id="r1", connector_id="telegram",
        allowed=True, reason="ok", action="read",
        target="owner_outer_dm", risk_class="irreversible",
        dry_run=False, data={"key": "value", "num": 42},
    )
    try:
        json.dumps(resp.to_dict())
        _ok("resp_json_safe")
    except (TypeError, ValueError) as e:
        _no("resp_json_safe", str(e))


# ═══════════════════════════════════════════════════════════════════════════
# SECTION H: Cross-connector isolation
# ═══════════════════════════════════════════════════════════════════════════

def test_connector_isolation():
    """Revoking one connector doesn't affect others."""
    print("\n--- Isolation: revoke doesn't cascade ---")
    reg = ConnectorRegistry(seed=True)
    reg.revoke("telegram", actor="owner")
    # Other connectors still work
    gw = ConnectorGateway(reg)
    resp = gw.route(_req("github", "read", "repo"))
    _true(resp.allowed, "github_still_allowed_after_tg_revoke")
    resp2 = gw.route(_req("huggingface", "read", "model"))
    _true(resp2.allowed, "hf_still_allowed_after_tg_revoke")


def test_consent_per_connector():
    """Consent denial for one connector doesn't block others."""
    print("\n--- Isolation: consent per-connector ---")
    def selective_consent(cid):
        # Only allow email, deny finance
        return (cid == "email", "ok" if cid == "email" else "denied")
    gw = _make_gateway(consent_checker=selective_consent)
    r1 = gw.route(_req("email", "read", "inbox"))
    _true(r1.allowed, "email_consent_ok")
    r2 = gw.route(_req("finance", "read", "accounts"))
    _false(r2.allowed, "finance_consent_denied")
    # huggingface doesn't require consent at all
    r3 = gw.route(_req("huggingface", "read", "model"))
    _true(r3.allowed, "hf_no_consent_needed")


def test_write_scope_isolation():
    """Each connector's write scope is enforced independently."""
    print("\n--- Isolation: write scope per-connector ---")
    gw = _make_gateway()
    # telegram: DRAFT scope -> write denied (needs APPROVED_WRITE)
    tgw = gw.route(_req("telegram", "write", "owner_outer_dm"))
    _false(tgw.allowed, "tg_write_denied_scope")
    # huggingface: NONE scope -> write denied
    hfgw = gw.route(_req("huggingface", "write", "model"))
    _false(hfgw.allowed, "hf_write_denied_scope")
    _eq(hfgw.reason, "write_not_permitted", "hf_write_none_reason")
    # telegram: draft is allowed (DRAFT >= DRAFT)
    tdr = gw.route(_req("telegram", "draft", "owner_outer_dm"))
    _true(tdr.allowed, "tg_draft_allowed_scope")
    # huggingface: draft denied (NONE < DRAFT)
    hfd = gw.route(_req("huggingface", "draft", "model"))
    _false(hfd.allowed, "hf_draft_denied_scope")


# ═══════════════════════════════════════════════════════════════════════════
# SECTION I: Default gateway convenience
# ═══════════════════════════════════════════════════════════════════════════

def test_default_gateway():
    """default_gateway creates a working gateway with seeded registry."""
    print("\n--- Convenience: default_gateway ---")
    gw = default_gateway()
    resp = gw.route(_req("huggingface", "read", "model"))
    _true(resp.allowed, "default_gw_hf_read")
    stats = gw.stats()
    _eq(stats["registry_size"], 6, "default_gw_registry_size")


# ═══════════════════════════════════════════════════════════════════════════
# Main runner
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    sections = [
        test_schema_builtins_valid,
        test_schema_health_readonly,
        test_schema_finance_readonly_or_draft,
        test_schema_forbidden_rejected,
        test_schema_invalid_connector_id,
        test_schema_serialization,
        test_schema_json_schema,
        test_registry_seed,
        test_registry_lookup_unknown,
        test_registry_register_custom,
        test_registry_revoke,
        test_registry_re_register_revoked,
        test_registry_list_all,
        test_registry_audit_trail,
        test_registry_audit_persist,
        test_telegram_read_allowed,
        test_telegram_write_denied_draft_scope,
        test_telegram_draft_allowed,
        test_telegram_target_allowlisted,
        test_telegram_disconnect_allowed,
        test_github_read_allowed,
        test_github_write_without_approval,
        test_github_write_dry_run,
        test_huggingface_read_allowed,
        test_huggingface_write_denied,
        test_email_read_with_consent,
        test_email_read_without_consent,
        test_email_read_consent_denied,
        test_email_write_denied,
        test_finance_read_with_consent,
        test_finance_read_without_consent,
        test_finance_write_denied,
        test_finance_draft_denied,
        test_healthkit_read_with_consent,
        test_healthkit_read_without_consent,
        test_healthkit_write_denied,
        test_unknown_connector_denied,
        test_invalid_action_denied,
        test_empty_action_denied,
        test_revoked_connector_denied,
        test_dry_run_never_executes,
        test_gateway_audit_trail,
        test_gateway_audit_persist,
        test_gateway_stats,
        test_redact_pii,
        test_redact_dict,
        test_redact_nested,
        test_redact_list,
        test_adversarial_connector_id,
        test_adversarial_target,
        test_adversarial_consent_checker_error,
        test_empty_request,
        test_request_response_serialization,
        test_response_serializable,
        test_connector_isolation,
        test_consent_per_connector,
        test_write_scope_isolation,
        test_default_gateway,
    ]

    print("=" * 60)
    print("test_connector_gateway (G9 CONNECTORS)")
    print("=" * 60)

    for fn in sections:
        try:
            fn()
        except Exception as e:
            _no(f"UNCAUGHT in {fn.__name__}", str(e))
            import traceback
            traceback.print_exc()

    total = _pass + _fail
    print(f"\n{'=' * 60}")
    print(f"test_connector_gateway: {_pass}/{total} passed "
          f"({_fail} failures)")
    print(f"{'=' * 60}")
    sys.exit(0 if _fail == 0 else 1)
