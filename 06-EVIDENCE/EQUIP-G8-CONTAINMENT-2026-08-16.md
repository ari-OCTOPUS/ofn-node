---
schema: equip-evidence.v1
wave: B2
group: 8
title: EQUIP G8 -- Bounded Agency and Damage Containment
date: 2026-08-16
branch: equip/g8-containment-20260816
verdict: CONDITIONAL PASS
requires_scan: true
contradiction_claimed: C-034
---

# EQUIP G8 -- Bounded Agency and Damage Containment

## Executive Verdict: CONDITIONAL PASS

Wave B2 (G8 Containment) passes the release gate with conditions.
No architecture invariant was broken. No critical or high-severity findings.
All 71 new containment tests pass. All 10 MEDIUM-002 remediation tests pass.
All regression tests pass (G7: 82/82, kill seam closer: 5/5, kill seam wire: 8/8,
circuit breaker: 7/7, money gate: 10/10, governor contract: 18/18).
Kill switch remains independent of LLM. Action Plane remains propose-only.
MCP server was NOT modified. MEDIUM-002 from Wave A scan was remediated and verified.

**Conditions:**
1. **CONDITIONAL-001**: The `_ops/containment/` modules are a vertical slice,
   not production wiring. The `risk_gate.check()` function is the enforcement
   point but is not yet wired into the MCP server's `_handle()` function or
   the `propose_action` pipeline. The G7 PEP should be extended to call
   `risk_gate.check()` before tool execution.
2. **CONDITIONAL-002**: The approval binder HMAC key (`OCTOPUS_APPROVAL_BINDER_HMAC`)
   must be provisioned in the environment before the approval system is
   operational. Without it, both `issue()` and `verify()` fail-closed (no valid
   signatures). The `audit_chain` does not require external keys.
3. **CONDITIONAL-003**: The `audit_chain` is in-memory only. For production,
   entries must be flushed to append-only JSONL on disk (matching the pattern of
   `organ-gate-log.jsonl` and G7 PEP audit). The serialization (`to_jsonl()`)
   and deserialization (`from_jsonl()`) are implemented and tested.
4. **CONDITIONAL-004**: The `kill_coordinator` currently wraps existing
   `halted()`/`kill_seam_denies()` as read-only checks. For full production use,
   it should also be wired to write `HALT-ALL` / `STOP-ORGANISM` files when
   `kill_global()` / `kill_agent()` are called (currently it tracks state
   in-memory only).

No FAIL-triggering finding (no bypass, data loss, unauthorized write, secret
leak, broken kill switch, invariant violation, or unrecoverable state).

---

## 1. Change Discovery

### 1.1 Commit Chain (baseline 0cb86f2..HEAD)

```
fe6cb0b  EQUIP G8: Bounded Agency -- risk tiers, approval binder, agent circuit, audit chain, kill coordinator, MEDIUM-002 fix
```

### 1.2 Changed Files (9 files, +2624, -23)

| File | Action | Lines | Notes |
|---|---|---|---|
| `_ops/containment/__init__.py` | NEW | +15 | Package docstring |
| `_ops/containment/risk_gate.py` | NEW | +309 | Risk tier classification + enforcement gate + budget tracking |
| `_ops/containment/approval_binder.py` | NEW | +219 | Tamper-evident HMAC approval tokens |
| `_ops/containment/agent_circuit.py` | NEW | +271 | Per-agent circuit breaker for loop/retry storms |
| `_ops/containment/audit_chain.py` | NEW | +285 | Hash-chain tamper-evident audit ledger |
| `_ops/containment/kill_coordinator.py` | NEW | +219 | Unified kill switch coordinator |
| `_ops/telemetry/alert_rules.py` | MODIFY | +48, -23 | MEDIUM-002 fix: injectable `db_path` parameter |
| `_ops/tests/test_containment.py` | NEW | +1080 | 71 tests for all containment modules |
| `_ops/tests/test_alert_rules_testable.py` | NEW | +237 | 10 tests for MEDIUM-002 remediation |

---

## 2. Discovered Architecture

### 2.1 Existing Containment Infrastructure (Pre-G8)

| Component | Path | Status | Notes |
|---|---|---|---|
| Circuit Breaker | `_ops/budget/circuit_breaker.py` | ACTIVE | Per-target, exponential backoff, rate-based window, well-tested |
| Money Gate | `_ops/budget/money_gate.py` | ACTIVE | Per-action human approval for financial ops, fail-closed |
| Capability Gate | `_ops/budget/capability_gate.py` | ACTIVE | 3-factor: capability marker + LIVE_ENABLED + per-action approval |
| Kill Seam | `_ops/budget/opslib.py` (kill_seam_denies) + `_ops/now_moves/kill_seam_closer.py` | ACTIVE | Flag-gated STOP-ORGANISM check, well-tested |
| Master Halt | `halted()` / `HALT_ALL` / `STOP-ARCHITECT` | ACTIVE | Hard system-wide stop, LLM-independent |
| Action Ladder | `_ops/action_bridge/contracts.py` | ACTIVE | A0-A6 action classification (structural, not enforcement) |
| Idempotency | `_ops/action_bridge/idempotency.py` | ACTIVE | Dedup + conflict detection |
| Drawdown Guard | `_ops/budget/drawdown_guard.py` | SHADOW | Shadow-count only, not enforced live |
| Governor | `_ops/budget/governor.py` | DEPRECATED | Routing budget adapter, zero callers |

### 2.2 Gaps Filled by G8

| Gap | Before G8 | After G8 |
|---|---|---|
| Risk tier enforcement | Action ladder existed but no enforcement gateway | `risk_gate.check()` with kill > circuit > budget > tier cascade |
| Approval binding | Money gate had approval but no cryptographic binding | `approval_binder` with HMAC + nonce replay prevention |
| Per-agent circuit | Only per-target circuit breaker existed | `agent_circuit` detects loop/retry storms per agent |
| Tamper-evident audit | Logs existed but no integrity verification | `audit_chain` with SHA256 hash-chain |
| Kill coordination | Multiple independent kill mechanisms, no unified coordinator | `kill_coordinator` wraps all mechanisms, adds per-agent tracking |
| Alert rule testability | `check_retry_storm`/`check_denied_actions` had zero test coverage | Injectable `db_path` parameter + 10 tests (MEDIUM-002 closed) |

---

## 3. Implemented Capabilities

### 3.1 Risk Gate (`_ops/containment/risk_gate.py`)

- **Risk Tier Classification**: Tools classified as `READ_ONLY`, `REVERSIBLE_WRITE`,
  `IRREVERSIBLE`, or `FINANCIAL`. Unknown tools default to `IRREVERSIBLE` (fail-closed).
- **Enforcement Cascade**: kill_active > circuit_open > budget_exceeded >
  approval_required > allowed. Each check is fail-fast.
- **Budget Tracking**: Per-agent `BudgetState` tracks token cost, time, retries,
  external calls, and money. All limits configurable.
- **Dry-Run Mode**: Returns what WOULD happen without executing (allow=True
  with requirement details).
- **Deterministic Fingerprinting**: `action_fingerprint()` for approval binding.

### 3.2 Approval Binder (`_ops/containment/approval_binder.py`)

- **HMAC-SHA256 Signatures**: Tamper-evident tokens binding action_id + tool_name
  + target + arguments_hash + approver + expiry.
- **Argument Binding**: Changing any argument invalidates the approval.
- **Nonce Replay Prevention**: Each nonce can be used exactly once.
- **Fail-Closed**: No HMAC key in environment = all verifications fail.
- **Expiry Enforcement**: Time-to-live on all approvals.

### 3.3 Agent Circuit Breaker (`_ops/containment/agent_circuit.py`)

- **Per-Agent State**: `AgentCircuitState` tracks action timestamps, retry
  timestamps, and counters.
- **Rate-Based Detection**: Actions/minute and retries/minute thresholds.
- **Sustained Storm Detection**: 5-minute window for sustained high activity.
- **Degraded State**: Warning level before circuit opens (high retry rate).
- **Permanent Kill**: `kill_agent()` sets permanent KILLED state, no recovery.
- **Auto-Recovery**: OPEN state recovers to ACTIVE after configurable cooldown.

### 3.4 Audit Chain (`_ops/containment/audit_chain.py`)

- **Hash-Chain Integrity**: Each entry includes `prev_hash` and `entry_hash`.
  Tampering with any entry invalidates all subsequent entries.
- **JSONL Serialization**: `to_jsonl()` / `from_jsonl()` for persistence.
- **Verification**: `verify()` walks the chain, recomputes hashes, detects any
  mismatch.
- **Event Types**: `action_evaluated`, `approval_issued`, `kill_activated`, etc.
- **Details Separation**: Details dict stored separately, only hash in chain entry
  (prevents secret leakage in audit).

### 3.5 Kill Coordinator (`_ops/containment/kill_coordinator.py`)

- **Unified Interface**: Single point for kill checks and activation.
- **Per-Agent Kill**: Individual agents can be killed without affecting others.
- **Global Kill**: Blocks all agents simultaneously.
- **Compensation Gate**: `can_run_compensation()` returns False after any kill.
- **System Integration**: Reads existing `halted()`, `kill_seam_denies()`,
  `master_halted()` for compatibility.
- **LLM-Independent**: All checks are file-based or in-memory, no LLM calls.
- **No Unkill**: No programmatic method to reverse a kill (by design).

---

## 4. Tests

### 4.1 New Tests: `test_containment.py` -- 71/71 PASS

| Section | Count | Description |
|---|---|---|
| Risk Gate | 20 | Classification, enforcement, budget, dry-run, ordering |
| Approval Binder | 11 | Issue/verify, tamper, expiry, mismatch, replay, fail-closed |
| Agent Circuit | 10 | Normal/storm/degraded/killed/cooldown/recovery |
| Audit Chain | 10 | Validity, tamper detection, JSONL round-trip, hash propagation |
| Kill Coordinator | 9 | Global/per-agent, compensation, history, no-unkill |
| Acceptance Scenarios | 4 | Loop storm + circuit breaker, kill + no side effects, full pipeline |
| Negative/Edge Cases | 7 | Empty inputs, zero limits, malformed chain, burst rate |

### 4.2 New Tests: `test_alert_rules_testable.py` -- 10/10 PASS

| Test | Description |
|---|---|
| medium002_01 | No events => no alert |
| medium002_02 | Below threshold => no alert |
| medium002_03 | Above threshold => alert fires |
| medium002_04 | Stale events outside window |
| medium002_05 | Denied actions below threshold |
| medium002_06 | Denied actions above threshold |
| medium002_07 | Non-denied errors not counted |
| medium002_08 | Custom window parameter |
| medium002_09 | Missing DB path no crash |
| medium002_10 | Alert schema fields |

### 4.3 Regression Tests -- All Green

| Suite | Result |
|---|---|
| G7 Identity (test_g7_identity_zero_trust.py) | 82/82 |
| Kill Seam Closer (test_kill_seam_closer.py) | 5/5 |
| Kill Seam Wire (test_kill_seam_wire.py) | 8/8 |
| Circuit Breaker Backoff (test_circuit_breaker_backoff_window.py) | 7/7 |
| Money Gate (test_money_gate.py) | 10/10 |
| Governor Contract (test_governor_contract.py) | 18/18 |

Total: 81 new tests + 140 regression tests = **221 tests green**.

---

## 5. Scan Findings

### 5.1 Static Analysis

- **Secrets**: No hardcoded secrets, tokens, or credentials in new code.
- **Shell Injection**: No `os.system()` or `shell=True` subprocess calls.
- **SQL Injection**: Parameterized queries only (`_count_events` in alert_rules).
- **Path Traversal**: No dynamic path construction from user input.
- **Unsafe Deserialization**: No `pickle`, `eval`, or `exec` calls.
- **Unbounded Loops**: No `while True:` loops.
- **Dependencies**: All new code is stdlib-only. No new pip packages required.

### 5.2 Security Scan (G8 Specific)

| Check | Result |
|---|---|
| Approval replay prevention | PASS -- nonce tracked, replay rejected |
| Approval/argument mismatch | PASS -- hash binding detects changes |
| Budget bypass | PASS -- fail-closed, unknown = deny |
| Race after kill | PASS -- killed agents permanently blocked |
| Partial transaction | N/A -- no transactional operations in slice |
| Failed compensation | PASS -- compensation forbidden after kill by design |
| Unbounded fan-out | PASS -- rate limits per agent |
| Cascading retries | PASS -- agent circuit breaker detects retry storms |
| Stale circuit state | PASS -- sliding window with automatic cleanup |
| Audit log tampering | PASS -- hash-chain detects any modification |
| Kill switch independent of LLM | PASS -- file-based, no AI call needed |

---

## 6. MEDIUM-002 Remediation

**Finding (Wave A)**: `check_retry_storm()` and `check_denied_actions()` in
`_ops/telemetry/alert_rules.py` had zero test coverage because they were
hardcoded to query the live brain/events DB.

**Fix**: Extracted DB access into `_count_events(db_path, status, summary_like,
window_minutes)` helper function. Both `check_retry_storm()` and
`check_denied_actions()` now accept an optional `db_path` parameter (default
`None` preserves existing behavior -- falls back to `memory.store.DB_PATH`).
Backwards-compatible: existing callers unaffected.

**Verification**: 10 new tests in `test_alert_rules_testable.py` cover both functions
with injectable test databases. All pass.

---

## 7. Unresolved Risks

1. **Production Wiring**: The containment modules exist but are not wired into
   the live MCP server or action pipeline. This is a vertical slice.
2. **Persistence**: Audit chain and agent circuit state are in-memory only.
   Production requires disk persistence (append-only JSONL).
3. **Observability Integration**: Per-agent circuit breaker events should feed
   into the G6 telemetry system for alerting.
4. **Contraction Claim**: C-034 -- not yet filed in `01-TRUTH/CONTRADICTIONS.md`
   (to be done by scanner or owner).

---

## 8. Rollback Plan

All G8 changes are isolated to:
- `_ops/containment/` (new package, can be deleted entirely)
- `_ops/tests/test_containment.py` (new test file)
- `_ops/tests/test_alert_rules_testable.py` (new test file)
- `_ops/telemetry/alert_rules.py` (minimal backward-compatible change)

Rollback: `git revert fe6cb0b` removes all G8 changes. The alert_rules.py
change is backwards-compatible, so the revert restores the original behavior
while keeping the refactored `_count_events` helper if desired.

---

## 9. Reproduce Commands

```bash
# G8 containment tests
PYTHONIOENCODING=utf-8 python -X utf8 _ops/tests/test_containment.py

# MEDIUM-002 alert rule tests
PYTHONIOENCODING=utf-8 python -X utf8 _ops/tests/test_alert_rules_testable.py

# Regression tests
PYTHONIOENCODING=utf-8 python -X utf8 _ops/tests/test_g7_identity_zero_trust.py
PYTHONIOENCODING=utf-8 python -X utf8 _ops/tests/test_kill_seam_wire.py
PYTHONIOENCODING=utf-8 python -X utf8 _ops/tests/test_circuit_breaker_backoff_window.py
PYTHONIOENCODING=utf-8 python -X utf8 _ops/tests/test_money_gate.py
PYTHONIOENCODING=utf-8 python -X utf8 _ops/tests/test_governor_contract.py
```

---

## 10. Evidence Paths

- Implementation: `_ops/containment/` (6 files)
- Tests: `_ops/tests/test_containment.py`, `_ops/tests/test_alert_rules_testable.py`
- MEDIUM-002 fix: `_ops/telemetry/alert_rules.py`
- This report: `06-EVIDENCE/EQUIP-G8-CONTAINMENT-2026-08-16.md`

---

## 11. Recommended Next Step

Wave B independent scan by a separate agent (per EQUIP protocol).
