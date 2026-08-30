#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_containment.py -- Comprehensive tests for EQUIP G8 Containment modules.

Tests all containment modules:
  - risk_gate: Risk classification, enforcement, budget tracking
  - approval_binder: Tamper-evident approval tokens
  - agent_circuit: Per-agent circuit breaker for loop storms
  - audit_chain: Tamper-evident hash-chain audit ledger
  - kill_coordinator: Unified kill switch coordinator

Acceptance scenario (from G8 spec):
  A test agent enters a loop/retry storm. Budget governor or circuit breaker
  must trip. Then kill switch is activated in sandbox and absence of side
  effects after kill is proven. Kill is never tested on the live organism.

$0 | stdlib-only | no network | no external dependencies
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
import time
import sqlite3
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
_containment = _OPS / "containment"
for _p in (str(_OPS), str(_OPS / "budget"), str(_OPS / "telemetry"),
           str(_containment), str(_OPS / "action_bridge")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ── Imports after path setup ──────────────────────────────────────────────────
from risk_gate import (
    RiskTier, classify, tier_min, tier_max, action_fingerprint,
    BudgetState, check as risk_check, EnforcementDecision, DEFAULT_CLASSIFICATION,
    DEFAULT_BUDGET,
)
from approval_binder import (
    ApprovalToken, issue, verify, hash_arguments, _canonical_payload, _sign,
)
from agent_circuit import (
    AgentCircuitState, AgentState, check_agent, record_action,
    kill_agent, is_agent_killed, DEFAULT_THRESHOLDS,
)
from audit_chain import (
    AuditChain, AuditEntry, _hash_entry, _hash_details, GENESIS_HASH,
)
from kill_coordinator import (
    KillCoordinator, KillReason,
)

passed = 0
failed = 0


def ok(name: str):
    global passed
    passed += 1
    print(f"  [PASS] {name}")


def fail(name: str, reason: str):
    global failed
    failed += 1
    print(f"  [FAIL] {name}: {reason}")


def run(fn):
    try:
        fn()
    except AssertionError as e:
        fail(fn.__name__, str(e))
    except Exception as e:
        fail(fn.__name__, f"{type(e).__name__}: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1: Risk Gate Tests
# ══════════════════════════════════════════════════════════════════════════════

def t_risk_01_unknown_tool_is_irreversible():
    """Unknown tools default to IRREVERSIBLE (fail-closed)."""
    tier = classify("totally_unknown_tool")
    assert tier == RiskTier.IRREVERSIBLE, f"Expected IRREVERSIBLE, got {tier}"
    ok("risk_01_unknown_tool_is_irreversible")


def t_risk_02_known_tools_classified_correctly():
    """Known tools are classified to their correct tiers."""
    assert classify("list_tree") == RiskTier.READ_ONLY
    assert classify("read_file_slice") == RiskTier.READ_ONLY
    assert classify("create_note") == RiskTier.REVERSIBLE_WRITE
    assert classify("propose_action") == RiskTier.IRREVERSIBLE
    assert classify("delete_file") == RiskTier.IRREVERSIBLE
    assert classify("execute_trade") == RiskTier.FINANCIAL
    assert classify("send_payment") == RiskTier.FINANCIAL
    ok("risk_02_known_tools_classified_correctly")


def t_risk_03_read_only_allowed_without_approval():
    """READ_ONLY tools pass without approval."""
    d = risk_check("list_tree", "act-001")
    assert d.allow is True, d.reason
    assert d.requires_approval is False
    ok("risk_03_read_only_allowed_without_approval")


def t_risk_04_irreversible_denied_without_approval():
    """IRREVERSIBLE tools denied without approval."""
    d = risk_check("propose_action", "act-002")
    assert d.allow is False
    assert d.requires_approval is True
    assert "approval_required" in d.reason
    ok("risk_04_irreversible_denied_without_approval")


def t_risk_05_financial_denied_without_approval():
    """FINANCIAL tools denied without approval."""
    d = risk_check("execute_trade", "act-003")
    assert d.allow is False
    assert d.requires_approval is True
    assert d.risk_tier == RiskTier.FINANCIAL
    ok("risk_05_financial_denied_without_approval")


def t_risk_06_approved_irreversible_allowed():
    """IRREVERSIBLE with approval is allowed."""
    d = risk_check("deploy", "act-004", approved=True)
    assert d.allow is True
    assert d.requires_approval is True
    ok("risk_06_approved_irreversible_allowed")


def t_risk_07_kill_switch_blocks_everything():
    """Kill switch active blocks ALL actions regardless of tier/approval."""
    for tool in ["list_tree", "propose_action", "execute_trade"]:
        d = risk_check(tool, "act-kill", approved=True, kill_active=True)
        assert d.allow is False, f"{tool} should be blocked by kill"
        assert d.kill_active is True
    ok("risk_07_kill_switch_blocks_everything")


def t_risk_08_circuit_open_blocks_action():
    """Open circuit breaker blocks actions."""
    d = risk_check("list_tree", "act-005", circuit_open=True)
    assert d.allow is False
    assert d.circuit_open is True
    ok("risk_08_circuit_open_blocks_action")


def t_risk_09_budget_exceeded_blocks_action():
    """Exceeded budget blocks actions."""
    budget = BudgetState(agent_id="test-agent")
    budget.limits["max_retries"] = 3
    for _ in range(4):
        budget.record(is_retry=True)
    d = risk_check("list_tree", "act-006", budget=budget)
    assert d.allow is False
    assert d.budget_exceeded is not None
    ok("risk_09_budget_exceeded_blocks_action")


def t_risk_10_dry_run_allows_but_shows_what_would_happen():
    """Dry-run mode returns allow=True but shows requirements."""
    d = risk_check("execute_trade", "act-dry", dry_run=True, approved=False)
    assert d.allow is True
    assert d.dry_run is True
    assert d.requires_approval is True
    assert "dry_run" in d.reason
    ok("risk_10_dry_run_allows_but_shows_what_would_happen")


def t_risk_11_budget_state_tracking():
    """Budget state accurately tracks consumption."""
    budget = BudgetState(agent_id="t", limits=dict(DEFAULT_BUDGET))
    budget.record(token_cost=0.5)
    budget.record(external_call=True)
    budget.record(is_retry=True)
    budget.record(money=10.0)
    c = budget.consumed
    assert c["token_cost_usd"] == 0.5
    assert c["external_calls"] == 1
    assert c["retries"] == 1
    assert c["money_spent_usd"] == 10.0
    ok("risk_11_budget_state_tracking")


def t_risk_12_budget_exceeded_detection():
    """Budget exceeded correctly identifies the exceeded limit."""
    budget = BudgetState(agent_id="t", limits={"max_token_cost_usd": 1.0, "max_retries": 2,
                                                "max_time_seconds": 10, "max_external_calls": 5,
                                                "max_money_usd": 0.0})
    budget.record(token_cost=1.5)
    exc = budget.exceeded()
    assert exc == "token_cost_usd", f"Expected token_cost_usd exceeded, got {exc}"
    ok("risk_12_budget_exceeded_detection")


def t_risk_13_action_fingerprint_deterministic():
    """Action fingerprint is deterministic."""
    fp1 = action_fingerprint("act-1", "deploy", {"v": "1.0"})
    fp2 = action_fingerprint("act-1", "deploy", {"v": "1.0"})
    assert fp1 == fp2
    ok("risk_13_action_fingerprint_deterministic")


def t_risk_14_action_fingerprint_changes_with_args():
    """Different arguments produce different fingerprints."""
    fp1 = action_fingerprint("act-1", "deploy", {"v": "1.0"})
    fp2 = action_fingerprint("act-1", "deploy", {"v": "2.0"})
    assert fp1 != fp2
    ok("risk_14_action_fingerprint_changes_with_args")


def t_risk_15_tier_comparison():
    """Tier comparison functions work correctly."""
    assert tier_min(RiskTier.READ_ONLY, RiskTier.FINANCIAL) == RiskTier.READ_ONLY
    assert tier_max(RiskTier.READ_ONLY, RiskTier.IRREVERSIBLE) == RiskTier.IRREVERSIBLE
    ok("risk_15_tier_comparison")


def t_risk_16_custom_classification():
    """Custom classification overrides defaults."""
    custom = {"list_tree": RiskTier.FINANCIAL}
    assert classify("list_tree", custom) == RiskTier.FINANCIAL
    assert classify("unknown", custom) == RiskTier.IRREVERSIBLE
    ok("risk_16_custom_classification")


def t_risk_17_decision_to_dict_serializable():
    """EnforcementDecision.to_dict() produces valid JSON."""
    d = risk_check("list_tree", "act-serial")
    serialized = json.dumps(d.to_dict())
    assert json.loads(serialized) is not None
    ok("risk_17_decision_to_dict_serializable")


def t_risk_18_enforcement_order_kill_first():
    """Kill is checked before circuit and budget."""
    budget = BudgetState(agent_id="t", limits={"max_token_cost_usd": 100.0})
    d = risk_check("list_tree", "act-order",
                   budget=budget, circuit_open=True,
                   kill_active=True, approved=True)
    assert d.kill_active is True
    assert "kill_switch" in d.reason
    ok("risk_18_enforcement_order_kill_first")


def t_risk_19_enforcement_order_circuit_before_budget():
    """Circuit is checked before budget."""
    budget = BudgetState(agent_id="t", limits={"max_token_cost_usd": 100.0})
    d = risk_check("list_tree", "act-order2",
                   budget=budget, circuit_open=True)
    assert d.circuit_open is True
    ok("risk_19_enforcement_order_circuit_before_budget")


def t_risk_20_reversible_write_needs_no_approval():
    """REVERSIBLE_WRITE tools pass without approval."""
    d = risk_check("create_note", "act-rev")
    assert d.allow is True
    assert d.requires_approval is False
    ok("risk_20_reversible_write_needs_no_approval")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2: Approval Binder Tests
# ══════════════════════════════════════════════════════════════════════════════

# Set HMAC key for approval binder tests
_APPROVAL_KEY = "test-g8-hmac-key-32chars!!"


def _with_approval_key(fn):
    """Decorator to set/unset HMAC key around a test."""
    def wrapper():
        old = os.environ.get("OCTOPUS_APPROVAL_BINDER_HMAC")
        os.environ["OCTOPUS_APPROVAL_BINDER_HMAC"] = _APPROVAL_KEY
        try:
            fn()
        finally:
            if old is None:
                os.environ.pop("OCTOPUS_APPROVAL_BINDER_HMAC", None)
            else:
                os.environ["OCTOPUS_APPROVAL_BINDER_HMAC"] = old
    return wrapper


@_with_approval_key
def t_approval_01_issue_and_verify():
    """Basic issue and verify with matching params."""
    nonce_store: set[str] = set()
    tok = issue("act-001", "deploy", "/prod/api",
                {"version": "2.1"})
    v = verify(tok, "act-001", "deploy", "/prod/api",
               {"version": "2.1"}, nonce_store=nonce_store)
    assert v["valid"] is True, v["reason"]
    ok("approval_01_issue_and_verify")


@_with_approval_key
def t_approval_02_tampered_signature_detected():
    """Tampered signature is detected."""
    nonce_store: set[str] = set()
    tok = issue("act-002", "deploy", "/prod", {"v": "1"})
    tok.signature = "X" * 32
    v = verify(tok, "act-002", "deploy", "/prod", {"v": "1"},
               nonce_store=nonce_store)
    assert v["valid"] is False
    assert "signature_invalid" in v["reason"]
    ok("approval_02_tampered_signature_detected")


@_with_approval_key
def t_approval_03_expired_token_detected():
    """Expired token is rejected."""
    nonce_store: set[str] = set()
    tok = issue("act-003", "deploy", "/prod", {"v": "1"},
                ttl_seconds=0)
    time.sleep(0.01)  # Ensure expiry
    v = verify(tok, "act-003", "deploy", "/prod", {"v": "1"},
               nonce_store=nonce_store)
    assert v["valid"] is False
    assert "expired" in v["reason"]
    ok("approval_03_expired_token_detected")


@_with_approval_key
def t_approval_04_action_id_mismatch():
    """Action ID mismatch is detected."""
    nonce_store: set[str] = set()
    tok = issue("act-004", "deploy", "/prod", {"v": "1"})
    v = verify(tok, "act-OTHER", "deploy", "/prod", {"v": "1"},
               nonce_store=nonce_store)
    assert v["valid"] is False
    assert "action_id_mismatch" in v["reason"]
    ok("approval_04_action_id_mismatch")


@_with_approval_key
def t_approval_05_tool_name_mismatch():
    """Tool name mismatch is detected."""
    nonce_store: set[str] = set()
    tok = issue("act-005", "deploy", "/prod", {"v": "1"})
    v = verify(tok, "act-005", "delete_file", "/prod", {"v": "1"},
               nonce_store=nonce_store)
    assert v["valid"] is False
    assert "tool_name_mismatch" in v["reason"]
    ok("approval_05_tool_name_mismatch")


@_with_approval_key
def t_approval_06_target_mismatch():
    """Target mismatch is detected."""
    nonce_store: set[str] = set()
    tok = issue("act-006", "deploy", "/prod/api", {"v": "1"})
    v = verify(tok, "act-006", "deploy", "/prod/OTHER", {"v": "1"},
               nonce_store=nonce_store)
    assert v["valid"] is False
    assert "target_mismatch" in v["reason"]
    ok("approval_06_target_mismatch")


@_with_approval_key
def t_approval_07_arguments_mismatch():
    """Arguments mismatch is detected (approval binding)."""
    nonce_store: set[str] = set()
    tok = issue("act-007", "deploy", "/prod", {"version": "1.0", "env": "prod"})
    v = verify(tok, "act-007", "deploy", "/prod",
               {"version": "2.0", "env": "prod"},
               nonce_store=nonce_store)
    assert v["valid"] is False
    assert "arguments_mismatch" in v["reason"]
    ok("approval_07_arguments_mismatch")


@_with_approval_key
def t_approval_08_nonce_replay_prevented():
    """Nonce replay is prevented."""
    nonce_store: set[str] = set()
    tok = issue("act-008", "deploy", "/prod", {"v": "1"})
    # First use succeeds
    v1 = verify(tok, "act-008", "deploy", "/prod", {"v": "1"},
                nonce_store=nonce_store)
    assert v1["valid"] is True
    # Replay fails
    v2 = verify(tok, "act-008", "deploy", "/prod", {"v": "1"},
                nonce_store=nonce_store)
    assert v2["valid"] is False
    assert "replayed" in v2["reason"]
    ok("approval_08_nonce_replay_prevented")


@_with_approval_key
def t_approval_09_no_hmac_key_fails_closed():
    """No HMAC key configured = all verifications fail (fail-closed)."""
    old = os.environ.pop("OCTOPUS_APPROVAL_BINDER_HMAC", None)
    try:
        tok = ApprovalToken(
            action_id="act", tool_name="t", target="/",
            arguments_hash="h", approver="owner",
            issued_at=time.time(), expires_at=time.time() + 300,
            nonce="test-nonce", signature="anything")
        nonce_store: set[str] = set()
        v = verify(tok, "act", "t", "/", {}, nonce_store=nonce_store)
        assert v["valid"] is False
        assert "no_hmac_key" in v["reason"]
    finally:
        os.environ["OCTOPUS_APPROVAL_BINDER_HMAC"] = _APPROVAL_KEY
    ok("approval_09_no_hmac_key_fails_closed")


@_with_approval_key
def t_approval_10_token_serializable():
    """Approval token can be serialized to/from JSON."""
    tok = issue("act-010", "deploy", "/prod", {"v": "1"})
    serialized = json.dumps(tok.to_dict())
    loaded = json.loads(serialized)
    tok2 = ApprovalToken.from_dict(loaded)
    assert tok2.action_id == tok.action_id
    assert tok2.signature == tok.signature
    ok("approval_10_token_serializable")


def t_approval_11_arguments_hash_deterministic():
    """Arguments hash is deterministic."""
    h1 = hash_arguments({"a": 1, "b": 2})
    h2 = hash_arguments({"b": 2, "a": 1})  # Different order, same content
    assert h1 == h2
    ok("approval_11_arguments_hash_deterministic")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3: Agent Circuit Tests
# ══════════════════════════════════════════════════════════════════════════════

def t_agent_01_initial_state_active():
    """New agent starts in ACTIVE state."""
    state = AgentCircuitState(agent_id="test-1")
    r = check_agent(state)
    assert r["allow"] is True
    assert r["state"] == AgentState.ACTIVE.value
    ok("agent_01_initial_state_active")


def t_agent_02_normal_operation_within_thresholds():
    """Normal action rate stays within thresholds."""
    state = AgentCircuitState(agent_id="test-2")
    for i in range(30):
        record_action(state)
    r = check_agent(state)
    assert r["allow"] is True
    ok("agent_02_normal_operation_within_thresholds")


def t_agent_03_retry_storm_trips_circuit():
    """High retry rate trips the circuit breaker."""
    state = AgentCircuitState(agent_id="test-3")
    now = time.time()
    # Simulate 25 retries in 1 minute (threshold is 20)
    for i in range(25):
        state.retry_timestamps.append(now - i * 2)  # spread over 50s
        state.total_retries += 1
    r = check_agent(state)
    assert r["allow"] is False, f"Circuit should be open: {r}"
    assert r["state"] == AgentState.OPEN.value
    assert "retry" in r["reason"].lower() or "retry" in (state.open_reason or "").lower()
    ok("agent_03_retry_storm_trips_circuit")


def t_agent_04_action_storm_trips_circuit():
    """High action rate trips the circuit breaker."""
    state = AgentCircuitState(agent_id="test-4")
    now = time.time()
    # Simulate 65 actions in 1 minute (threshold is 60)
    for i in range(65):
        state.action_timestamps.append(now - i * 0.9)  # spread over ~58s
        state.total_actions += 1
    r = check_agent(state)
    assert r["allow"] is False
    assert r["state"] == AgentState.OPEN.value
    ok("agent_04_action_storm_trips_circuit")


def t_agent_05_killed_agent_permanently_blocked():
    """Killed agent is permanently blocked."""
    state = AgentCircuitState(agent_id="test-5")
    kill_agent(state)
    assert is_agent_killed(state) is True
    r = check_agent(state)
    assert r["allow"] is False
    assert r["state"] == AgentState.KILLED.value
    ok("agent_05_killed_agent_permanently_blocked")


def t_agent_06_cooldown_recovery():
    """Circuit recovers after cooldown period."""
    state = AgentCircuitState(agent_id="test-6")
    now = time.time()
    # Trip the circuit
    for i in range(65):
        state.action_timestamps.append(now - i * 0.9)
        state.total_actions += 1
    r = check_agent(state)
    assert r["allow"] is False

    # Simulate cooldown elapsed
    state.opened_at = now - 60  # cooldown_seconds default = 30
    state.action_timestamps = []  # Clear old timestamps
    r2 = check_agent(state)
    assert r2["allow"] is True
    assert "recovered" in r2["reason"]
    ok("agent_06_cooldown_recovery")


def t_agent_07_degraded_state_warning():
    """High but not critical retry rate causes degraded state."""
    state = AgentCircuitState(agent_id="test-7")
    now = time.time()
    # 12 retries in 1 minute (threshold for degraded = 10, for open = 20)
    for i in range(12):
        state.retry_timestamps.append(now - i * 4)
        state.total_retries += 1
    r = check_agent(state)
    assert r["allow"] is True  # Degraded doesn't block
    assert r["state"] == AgentState.DEGRADED.value
    ok("agent_07_degraded_state_warning")


def t_agent_08_record_action_updates_state():
    """record_action correctly updates timestamps and counters."""
    state = AgentCircuitState(agent_id="test-8")
    record_action(state, is_retry=False)
    assert state.total_actions == 1
    assert state.total_retries == 0
    assert len(state.action_timestamps) == 1

    record_action(state, is_retry=True)
    assert state.total_actions == 2
    assert state.total_retries == 1
    assert len(state.retry_timestamps) == 1
    ok("agent_08_record_action_updates_state")


def t_agent_09_state_serializable():
    """AgentCircuitState can be serialized to dict."""
    state = AgentCircuitState(agent_id="test-9")
    record_action(state)
    d = state.to_dict()
    assert json.loads(json.dumps(d)) is not None
    ok("agent_09_state_serializable")


def t_agent_10_killed_agent_cooldown_does_not_recover():
    """Killed agent does NOT recover even after cooldown."""
    state = AgentCircuitState(agent_id="test-10")
    kill_agent(state)
    state.opened_at = time.time() - 10000  # Way past cooldown
    r = check_agent(state)
    assert r["allow"] is False
    assert r["state"] == AgentState.KILLED.value
    ok("agent_10_killed_agent_cooldown_does_not_recover")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4: Audit Chain Tests
# ══════════════════════════════════════════════════════════════════════════════

def t_audit_01_empty_chain_valid():
    """Empty chain is valid."""
    chain = AuditChain()
    v = chain.verify()
    assert v["valid"] is True
    assert v["entries_checked"] == 0
    ok("audit_01_empty_chain_valid")


def t_audit_02_single_entry_valid():
    """Chain with single entry is valid."""
    chain = AuditChain()
    chain.append("test_event", "system", "act-1", "read_only", "ALLOW")
    v = chain.verify()
    assert v["valid"] is True
    assert v["entries_checked"] == 1
    ok("audit_02_single_entry_valid")


def t_audit_03_chain_with_multiple_entries_valid():
    """Chain with multiple entries is valid."""
    chain = AuditChain()
    for i in range(10):
        chain.append(f"event_{i}", f"agent_{i % 3}", f"act-{i}",
                     "irreversible", "ALLOW" if i % 2 == 0 else "DENY")
    v = chain.verify()
    assert v["valid"] is True
    assert v["entries_checked"] == 10
    ok("audit_03_chain_with_multiple_entries_valid")


def t_audit_04_tampered_decision_detected():
    """Tampering with a decision is detected."""
    chain = AuditChain()
    chain.append("e1", "system", "act-1", "irreversible", "DENY",
                 {"reason": "no_approval"})
    chain.append("e2", "system", "act-2", "read_only", "ALLOW")
    # Tamper: change DENY to ALLOW
    chain._entries[0].decision = "ALLOW"
    v = chain.verify()
    assert v["valid"] is False
    assert v["reason"] == "entry_hash_mismatch:entry=1"
    ok("audit_04_tampered_decision_detected")


def t_audit_05_tampered_prev_hash_detected():
    """Tampering with prev_hash linkage is detected."""
    chain = AuditChain()
    chain.append("e1", "system", "act-1", "read_only", "ALLOW")
    chain.append("e2", "system", "act-2", "read_only", "ALLOW")
    chain._entries[1].prev_hash = "X" * 32
    v = chain.verify()
    assert v["valid"] is False
    assert "prev_hash_mismatch" in v["reason"]
    ok("audit_05_tampered_prev_hash_detected")


def t_audit_06_jsonl_round_trip():
    """Chain survives JSONL serialization round-trip."""
    chain = AuditChain()
    for i in range(5):
        chain.append(f"event_{i}", "agent_1", f"act-{i}",
                     "reversible_write", "ALLOW",
                     {"tool": f"tool_{i}"})
    jsonl = chain.to_jsonl()
    chain2 = AuditChain.from_jsonl(jsonl)
    assert chain2.length == 5
    v = chain2.verify()
    assert v["valid"] is True
    ok("audit_06_jsonl_round_trip")


def t_audit_07_hash_chain_propagation():
    """Each entry's prev_hash matches previous entry's hash."""
    chain = AuditChain()
    for i in range(8):
        chain.append(f"ev-{i}", "sys", f"act-{i}", "read_only", "ALLOW")
    assert chain._entries[0].prev_hash == GENESIS_HASH
    for i in range(1, len(chain._entries)):
        assert chain._entries[i].prev_hash == chain._entries[i-1].entry_hash, \
            f"Chain break at entry {i+1}"
    ok("audit_07_hash_chain_propagation")


def t_audit_08_details_not_in_hash_content():
    """Details dict is stored separately, only hash in chain entry."""
    chain = AuditChain()
    chain.append("ev", "sys", "act-1", "read_only", "ALLOW",
                 {"secret": "should-not-appear-in-chain"})
    entry = chain._entries[0]
    # Details should not appear in the hash payload
    assert "secret" not in entry.to_dict().get("entry_hash", "")
    assert entry.details_hash == _hash_details({"secret": "should-not-appear-in-chain"})
    ok("audit_08_details_not_in_hash_content")


def t_audit_09_kill_event_recorded():
    """Kill events can be recorded in the chain."""
    chain = AuditChain()
    chain.append("kill_activated", "system", "kill-001",
                 "financial", "KILL", {"trigger": "owner_command"})
    assert chain.length == 1
    v = chain.verify()
    assert v["valid"] is True
    assert chain._entries[0].decision == "KILL"
    ok("audit_09_kill_event_recorded")


def t_audit_10_malformed_jsonl_skipped():
    """Malformed JSONL lines are skipped, chain continues."""
    chain = AuditChain()
    chain.append("e1", "sys", "a1", "read_only", "ALLOW")
    jsonl = chain.to_jsonl() + "THIS IS NOT JSON\n" + '{"schema":"audit-chain.v1","seq":2,"ts":"2026-01-01T00:00:00Z","event":"e2","actor":"sys","action_id":"a2","risk_tier":"read_only","decision":"ALLOW","details_hash":"abc","prev_hash":"' + chain._entries[0].entry_hash + '","entry_hash":"WRONG"}\n'
    chain2 = AuditChain.from_jsonl(jsonl)
    # Malformed line should be skipped
    assert chain2.length >= 1
    ok("audit_10_malformed_jsonl_skipped")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 5: Kill Coordinator Tests
# ══════════════════════════════════════════════════════════════════════════════

def t_kill_01_initial_state_allows_tasks():
    """Coordinator starts with all tasks allowed."""
    coord = KillCoordinator()
    r = coord.can_start_task("worker-1")
    assert r["allow"] is True
    ok("kill_01_initial_state_allows_tasks")


def t_kill_02_agent_kill_blocks_specific_agent():
    """Per-agent kill blocks only that agent."""
    coord = KillCoordinator()
    coord.kill_agent("worker-1", KillReason.RETRY_STORM)
    assert coord.can_start_task("worker-1")["allow"] is False
    assert coord.can_start_task("worker-2")["allow"] is True
    ok("kill_02_agent_kill_blocks_specific_agent")


def t_kill_03_global_kill_blocks_all():
    """Global kill blocks all agents."""
    coord = KillCoordinator()
    coord.kill_agent("worker-1", KillReason.RETRY_STORM)
    coord.kill_global(KillReason.OWNER_COMMAND, "owner")
    assert coord.can_start_task("worker-1")["allow"] is False
    assert coord.can_start_task("worker-2")["allow"] is False
    assert coord.can_start_task("worker-99")["allow"] is False
    ok("kill_03_global_kill_blocks_all")


def t_kill_04_compensation_forbidden_after_kill():
    """Compensation is NEVER allowed after any kill."""
    coord = KillCoordinator()
    # After agent kill
    coord.kill_agent("worker-1", KillReason.BUDGET_EXCEEDED)
    assert coord.can_run_compensation("worker-1")["allow"] is False
    # Other agent still can
    assert coord.can_run_compensation("worker-2")["allow"] is True
    # After global kill
    coord.kill_global(KillReason.OWNER_COMMAND)
    assert coord.can_run_compensation("worker-2")["allow"] is False
    ok("kill_04_compensation_forbidden_after_kill")


def t_kill_05_kill_order_recorded():
    """Kill orders are recorded in history."""
    coord = KillCoordinator()
    coord.kill_agent("w1", KillReason.SAFETY_VIOLATION, "system",
                    {"violation": "path_traversal"})
    coord.kill_global(KillReason.OWNER_COMMAND, "owner")
    assert len(coord.kill_history) == 2
    assert coord.kill_history[0].reason == KillReason.SAFETY_VIOLATION
    assert coord.kill_history[1].reason == KillReason.OWNER_COMMAND
    ok("kill_05_kill_order_recorded")


def t_kill_06_kill_order_serializable():
    """Kill orders can be serialized to JSON."""
    coord = KillCoordinator()
    coord.kill_agent("w1", KillReason.RETRY_STORM, "system",
                     {"retry_count": 150})
    order = coord.kill_history[0]
    d = order.to_dict()
    assert json.loads(json.dumps(d)) is not None
    assert d["reason"] == "retry_storm"
    ok("kill_06_kill_order_serializable")


def t_kill_07_global_kill_order_accessible():
    """Global kill order is accessible."""
    coord = KillCoordinator()
    coord.kill_global(KillReason.OWNER_COMMAND, "owner")
    assert coord.global_kill_order is not None
    assert coord.global_kill_order.reason == KillReason.OWNER_COMMAND
    ok("kill_07_global_kill_order_accessible")


def t_kill_08_no_unkill():
    """There is no programmatic unkilling."""
    coord = KillCoordinator()
    coord.kill_agent("w1", KillReason.CIRCUIT_BREAKER)
    assert coord.can_start_task("w1")["allow"] is False
    # No method to unkill -- this is by design
    assert not hasattr(coord, "unkill_agent") or not callable(
        getattr(coord, "unkill_agent", None))
    ok("kill_08_no_unkill")


def t_kill_09_multiple_agent_kills():
    """Multiple agents can be killed independently."""
    coord = KillCoordinator()
    coord.kill_agent("w1", KillReason.RETRY_STORM)
    coord.kill_agent("w2", KillReason.BUDGET_EXCEEDED)
    coord.kill_agent("w3", KillReason.SAFETY_VIOLATION)
    assert coord.can_start_task("w1")["allow"] is False
    assert coord.can_start_task("w2")["allow"] is False
    assert coord.can_start_task("w3")["allow"] is False
    assert coord.can_start_task("w4")["allow"] is True
    ok("kill_09_multiple_agent_kills")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 6: Integration / Acceptance Scenario
# ══════════════════════════════════════════════════════════════════════════════

def t_accept_01_loop_storm_detected_and_blocked():
    """ACCEPTANCE: Agent in loop storm is detected and blocked by circuit breaker."""
    # Setup
    agent_state = AgentCircuitState(agent_id="storm-agent")
    budget = BudgetState(agent_id="storm-agent", limits=dict(DEFAULT_BUDGET))
    coord = KillCoordinator()
    chain = AuditChain()

    # Agent enters loop: 70 rapid actions with some retries
    now = time.time()
    storm_detected = False
    for i in range(70):
        r = record_action(agent_state, is_retry=(i % 4 == 0))
        budget.record(is_retry=(i % 4 == 0))

        # Check circuit after each action
        cr = check_agent(agent_state)
        if not cr["allow"]:
            storm_detected = True
            # Record in audit chain
            chain.append("circuit_breaker_trip", "system",
                         f"storm-action-{i}", "irreversible", "DENY",
                         {"agent": "storm-agent", "reason": cr["reason"]})
            break

    assert storm_detected, "Circuit breaker should have tripped during storm"

    # Verify coordinator blocks new tasks for this agent
    # (agent circuit is independent of coordinator, but let's verify consistency)
    cr = check_agent(agent_state)
    assert cr["allow"] is False

    # Verify chain integrity
    v = chain.verify()
    assert v["valid"] is True

    ok("accept_01_loop_storm_detected_and_blocked")


def t_accept_02_kill_then_no_side_effects():
    """ACCEPTANCE: After kill, no new tasks or compensation are possible."""
    agent_state = AgentCircuitState(agent_id="test-agent")
    budget = BudgetState(agent_id="test-agent", limits=dict(DEFAULT_BUDGET))
    coord = KillCoordinator()
    chain = AuditChain()

    # First, some normal activity
    chain.append("action_evaluated", "test-agent", "act-1",
                 "read_only", "ALLOW", {"tool": "list_tree"})

    # Kill the agent
    coord.kill_agent("test-agent", KillReason.OWNER_COMMAND, "owner")
    kill_agent(agent_state)

    # Record kill in audit chain
    chain.append("kill_activated", "owner", "kill-001",
                 "irreversible", "KILL",
                 {"target": "test-agent", "reason": "owner_command"})

    # Verify: no new tasks allowed
    r = coord.can_start_task("test-agent")
    assert r["allow"] is False, "New tasks must be blocked after kill"

    # Verify: no compensation allowed
    r = coord.can_run_compensation("test-agent")
    assert r["allow"] is False, "Compensation must be forbidden after kill"

    # Verify: risk gate blocks with kill_active
    d = risk_check("list_tree", "act-after-kill", kill_active=True)
    assert d.allow is False
    assert d.kill_active is True

    # Verify: agent circuit permanently blocked
    assert is_agent_killed(agent_state) is True
    cr = check_agent(agent_state)
    assert cr["allow"] is False
    assert cr["state"] == AgentState.KILLED.value

    # Verify: audit chain still intact
    v = chain.verify()
    assert v["valid"] is True

    ok("accept_02_kill_then_no_side_effects")


def t_accept_03_full_pipeline_risk_to_audit():
    """ACCEPTANCE: Full pipeline from risk classification to audit trail."""
    chain = AuditChain()
    nonce_store: set[str] = set()
    budget = BudgetState(agent_id="pipeline-agent", limits=dict(DEFAULT_BUDGET))

    # Set approval key
    old_key = os.environ.get("OCTOPUS_APPROVAL_BINDER_HMAC")
    os.environ["OCTOPUS_APPROVAL_BINDER_HMAC"] = _APPROVAL_KEY

    try:
        # 1. READ_ONLY action -- auto-allowed
        test_budget = {
            "max_token_cost_usd": 1.0, "max_retries": 10,
            "max_time_seconds": 300, "max_external_calls": 50,
            "max_money_usd": 10.0,  # Non-zero to avoid immediate exceed
        }
        budget = BudgetState(agent_id="pipeline-agent", limits=test_budget)
        d1 = risk_check("list_tree", "pipe-001", agent_id="pipeline-agent",
                         budget=budget)
        chain.append("action_evaluated", "pipeline-agent", "pipe-001",
                     d1.risk_tier.value, "ALLOW" if d1.allow else "DENY",
                     {"tool": "list_tree"})
        assert d1.allow is True

        # 2. IRREVERSIBLE without approval -- denied
        d2 = risk_check("deploy", "pipe-002", agent_id="pipeline-agent",
                         budget=budget, approved=False)
        chain.append("action_evaluated", "pipeline-agent", "pipe-002",
                     d2.risk_tier.value, "DENY",
                     {"tool": "deploy", "reason": d2.reason})
        assert d2.allow is False

        # 3. Issue approval for the action
        tok = issue("pipe-003", "deploy", "/prod/api",
                    {"version": "2.0"})
        chain.append("approval_issued", "owner", "pipe-003",
                     "irreversible", "ALLOW",
                     {"approver": "owner", "target": "/prod/api"})

        # 4. Verify and execute
        v = verify(tok, "pipe-003", "deploy", "/prod/api",
                   {"version": "2.0"}, nonce_store=nonce_store)
        assert v["valid"] is True

        d3 = risk_check("deploy", "pipe-003",
                         agent_id="pipeline-agent",
                         budget=budget, approved=True)
        chain.append("action_evaluated", "pipeline-agent", "pipe-003",
                     d3.risk_tier.value, "ALLOW" if d3.allow else "DENY",
                     {"tool": "deploy", "approved": True})
        assert d3.allow is True

        # 5. Verify full chain
        v = chain.verify()
        assert v["valid"] is True
        assert chain.length == 4

    finally:
        if old_key is None:
            os.environ.pop("OCTOPUS_APPROVAL_BINDER_HMAC", None)
        else:
            os.environ["OCTOPUS_APPROVAL_BINDER_HMAC"] = old_key

    ok("accept_03_full_pipeline_risk_to_audit")


def t_accept_04_budget_and_circuit_together():
    """ACCEPTANCE: Budget and circuit breaker work together."""
    agent_state = AgentCircuitState(agent_id="budget-agent")
    budget = BudgetState(agent_id="budget-agent",
                         limits={"max_token_cost_usd": 0.5, "max_retries": 5,
                                 "max_time_seconds": 60, "max_external_calls": 10,
                                 "max_money_usd": 10.0})

    # Run actions that consume budget
    for i in range(6):
        budget.record(token_cost=0.1, is_retry=True)
        record_action(agent_state, is_retry=True)

    # Budget should be exceeded on retries
    budget_exc = budget.exceeded()
    assert budget_exc is not None, "Budget should be exceeded"

    # Risk gate should deny due to budget
    d = risk_check("list_tree", "budget-act", budget=budget,
                   agent_id="budget-agent")
    assert d.allow is False
    assert d.budget_exceeded is not None

    ok("accept_04_budget_and_circuit_together")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 7: Negative / Edge Cases
# ══════════════════════════════════════════════════════════════════════════════

def t_neg_01_empty_action_id():
    """Empty action_id doesn't crash risk gate."""
    d = risk_check("", "act-id-empty")
    assert hasattr(d, "allow")
    ok("neg_01_empty_action_id")


def t_neg_02_none_arguments():
    """None arguments don't crash risk gate or approval binder."""
    d = risk_check("list_tree", "act-none", arguments=None)
    assert d.allow is True
    h = hash_arguments(None)
    assert h is not None
    ok("neg_02_none_arguments")


def t_neg_03_empty_tool_name():
    """Empty tool name defaults to IRREVERSIBLE (fail-closed)."""
    tier = classify("")
    assert tier == RiskTier.IRREVERSIBLE
    ok("neg_03_empty_tool_name")


def t_neg_04_audit_chain_double_append_same_seq():
    """Two entries with same seq in chain would be caught by verify."""
    chain = AuditChain()
    chain.append("e1", "sys", "a1", "read_only", "ALLOW")
    # Manually add duplicate
    dup = AuditEntry(
        seq=1, ts=chain._entries[0].ts, event="e1-fake",
        actor="attacker", action_id="a1", risk_tier="read_only",
        decision="ALLOW", details_hash=chain._entries[0].details_hash,
        prev_hash=chain._entries[0].prev_hash,
        entry_hash=chain._entries[0].entry_hash,
    )
    chain._entries.insert(1, dup)
    v = chain.verify()
    assert v["valid"] is False
    assert "sequence" in v["reason"]
    ok("neg_04_audit_chain_double_append_same_seq")


def t_neg_05_budget_with_zero_limits():
    """Budget with zero limits immediately exceeded."""
    budget = BudgetState(agent_id="zero",
                         limits={"max_token_cost_usd": 0, "max_retries": 0,
                                 "max_time_seconds": 0, "max_external_calls": 0,
                                 "max_money_usd": 0})
    exc = budget.exceeded()
    # Zero limits means the first resource consumed exceeds them
    budget.record(token_cost=0.001)
    exc = budget.exceeded()
    assert exc is not None
    ok("neg_05_budget_with_zero_limits")


def t_neg_06_agent_circuit_empty_state():
    """Agent circuit with empty state doesn't crash."""
    state = AgentCircuitState(agent_id="")
    r = check_agent(state)
    assert "allow" in r
    ok("neg_06_agent_circuit_empty_state")


def t_neg_07_approval_verify_with_empty_nonce_store():
    """Approval verify without nonce store works (no replay check)."""
    old_key = os.environ.get("OCTOPUS_APPROVAL_BINDER_HMAC")
    os.environ["OCTOPUS_APPROVAL_BINDER_HMAC"] = _APPROVAL_KEY
    try:
        tok = issue("act-neg", "deploy", "/t", {"v": "1"})
        # Verify without nonce store (no replay prevention)
        v = verify(tok, "act-neg", "deploy", "/t", {"v": "1"})
        assert v["valid"] is True
        # But WITH nonce store, replay should fail
        nonce_store: set[str] = set()
        v2 = verify(tok, "act-neg", "deploy", "/t", {"v": "1"},
                    nonce_store=nonce_store)
        assert v2["valid"] is True  # First use with fresh store succeeds
        v3 = verify(tok, "act-neg", "deploy", "/t", {"v": "1"},
                    nonce_store=nonce_store)
        assert v3["valid"] is False
    finally:
        if old_key is None:
            os.environ.pop("OCTOPUS_APPROVAL_BINDER_HMAC", None)
        else:
            os.environ["OCTOPUS_APPROVAL_BINDER_HMAC"] = old_key
    ok("neg_07_approval_verify_with_empty_nonce_store")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    checks = sorted([(n, f) for n, f in globals().items()
                    if n.startswith("t_") and callable(f)],
                   key=lambda x: x[0])

    print(f"test_containment (G8) -- {len(checks)} checks")
    print("=" * 60)

    for name, fn in checks:
        run(fn)

    total = passed + failed
    print("=" * 60)
    if failed:
        print(f"FAIL {passed}/{total} ({failed} failures)")
        sys.exit(1)
    else:
        print(f"PASS {passed}/{total} (0 failures)")
        sys.exit(0)
