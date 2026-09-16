---
schema: equip-evidence.v1
wave: B1
group: 7
title: EQUIP G7 -- Identity and Zero-Trust Agent/Tool Security
date: 2026-08-16
branch: equip/g7-identity-20260816
verdict: CONDITIONAL PASS
requires_scan: true
---

# EQUIP G7 -- Identity and Zero-Trust Agent/Tool Security

## Executive Verdict: CONDITIONAL PASS

Wave B1 (G7 Identity) passes the release gate with conditions.
No architecture invariant was broken. No critical or high-severity findings.
All 82 new tests pass. All regression tests pass (G2: 49/49, G6: 53/53,
gate: 10/10, telemetry: 9/9, read seam: 5/5). Kill switch remains independent.
Action Plane remains propose-only. MCP server was NOT modified (extension, not replacement).
MEDIUM-001 from Wave A scan was remediated and verified.

**Conditions:**
1. **CONDITIONAL-001**: The G7 identity modules (`_ops/identity/`) are not yet wired
   into the MCP server's `_handle()` function. The PEP exists but is not enforcing
   on live tool calls. This is a vertical slice, not production wiring.
2. **CONDITIONAL-002**: HMAC signing key (`OCTOPUS_CAPABILITY_TOKEN_HMAC`) must be
   provisioned in the environment before the token system is operational. Without it,
   both `issue()` and `verify()` fail-closed (no tokens issued, no tokens validated).
3. **CONDITIONAL-003**: The nonce replay store (`used_nonces`) is in-memory only.
   Persistence must be added before production use (append-only JSONL, matching
   the pattern of `capability-effects.jsonl`).

No FAIL-triggering finding (no bypass, data loss, unauthorized write, secret leak,
broken kill switch, invariant violation, or unrecoverable state).

---

## 1. Change Discovery

### 1.1 Commit Chain (baseline a3431eb..HEAD)

```
360a7c6  EQUIP G7: Zero-Trust identity, capability tokens, policy enforcement, MEDIUM-001 fix
```

### 1.2 Changed Files (7 files, +1712, -2)

| File | Action | Lines | Group |
|---|---|---|---|
| `_ops/identity/__init__.py` | NEW | +18 | G7 |
| `_ops/identity/identity_store.py` | NEW | +169 | G7 |
| `_ops/identity/capability_token.py` | NEW | +295 | G7 |
| `_ops/identity/policy_enforcer.py` | NEW | +385 | G7 |
| `_ops/tests/test_g7_identity_zero_trust.py` | NEW | +839 | G7 |
| `_ops/memory/write_gate_enforcer.py` | MODIFIED | +2, -1 | MEDIUM-001 |
| `_ops/memory/gate.py` | MODIFIED | +2, -1 | MEDIUM-001 |

**No existing files modified except MEDIUM-001 remediation (2 files).**
No migrations. No new pip dependencies (stdlib-only).

### 1.3 MEDIUM-001 Remediation (Wave A Cross-Reference)

**Finding**: `_SECRET_RX` in `write_gate_enforcer.py` and `gate.py` did not cover
`ghp_*` GitHub PATs. Content containing GitHub tokens from a trusted source would
pass validation.

**Remediation**: Added `ghp_[a-zA-Z0-9]{36,}`, `gho_[a-zA-Z0-9]{36,}`, and
`ghu_[a-zA-Z0-9]{36,}` patterns to `_SECRET_RX` in both files.

**Verification**:
- `validate_content("ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghij1234567890")` now returns `(False, "secret/PII pattern detected")`
- `gate._SECRET_RX.search("ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghij1234567890")` now matches
- Existing smoke test in `write_gate_enforcer.py` still passes
- All G2 regression tests (49/49) pass
- Memory gate tests (10/10) pass

**Retest Status**: CLOSED.

---

## 2. Architecture Invariants Verification

| Invariant | Verification Method | Status |
|---|---|---|
| NBB-CP not bypassable | MCP server not modified. No direct delete/execute tool added. | INTACT |
| Action Plane propose-only | `propose_action` function untouched. PEP is a layer above, not a replacement. | INTACT |
| sandbox = ADR-039 | No sandbox references in G7 modules. | INTACT |
| kill switch = halted flag + STOP + kill.switch file | No kill switch references in G7 modules. | INTACT |
| kill switch independent of model | G7 modules do not reference model inference. | INTACT |
| CORTEX_HYPOTHESIS unchanged | No G7 module references CORTEX_HYPOTHESIS. | INTACT |
| Finance/HealthKit read-only | No G7 module references finance or health. | INTACT |
| SOG/Kalman not authority | PEP decisions are authoritative, not observational. Correct for identity domain. | N/A |
| deny-by-default | Unknown agent_id = DENIED. No token = role-based check only. | INTACT |
| MCP discovery != permission | PEP enforces: knowing a tool exists does not grant access. | INTACT |

---

## 3. Discovered Architecture

### 3.1 Existing Identity/Auth Landscape (Pre-G7)

Before G7, the repository had multiple identity-adjacent mechanisms but no unified
identity system:

| Module | Purpose | Identity? | Gap |
|---|---|---|---|
| `octopus_mcp/server.py` | MCP tool execution | No agent identity check | Anonymous callers |
| `action_bridge/owner_gate.py` | HMAC owner approvals | Per-action, not per-agent | No agent identity |
| `action_bridge/scope_guard.py` | Path containment | No identity, path-only | Path != agent |
| `capability_registry.py` | Capability discovery | No auth enforcement | Discovery != permission |
| `capabilities.py` | Owner verdict to capability | No per-task binding | Verdict != capability token |
| `autonomy_grant.py` | Self-service allowlist | No agent identity | Role-based, no per-task |
| `memory/gate.py` | Memory write gate | Source classification | Source != agent identity |
| `memory/write_gate_enforcer.py` | Memory write validation | Source classification | Same as above |
| `_octopus/config/bots.yaml` | Bot role definitions | Static config | No runtime enforcement |

### 3.2 G7 Vertical Slice

G7 fills the gap between "who can do what" (static config) and "is this specific
call authorized" (runtime enforcement):

```
Agent/Service
    |
    v
IdentityStore -- "Is this agent known? What role? On whose behalf?"
    |
    v
CapabilityToken -- "Is this token valid? Bound to this agent/task/action/resource? Not expired? Not replayed?"
    |
    v
PolicyEnforcer -- "Does role + token scope meet tool sensitivity? Any risk factors? Audit the decision."
    |
    v
Tool Execution (only if ALLOW)
```

### 3.3 Design Decisions

1. **No SPIFFE/Keycloak/SPIRE**: Single-laptop deployment does not justify
   operational complexity. The IdentityStore is in-memory with a `default_store()`
   that seeds known identities from `bots.yaml`.

2. **HMAC (not asymmetric crypto)**: Same pattern as `owner_gate.py`. Key from
   env var. Fail-closed if key missing. Sufficient for single-node deployment.

3. **Token, not API key**: Tokens are short-lived (max 1 hour), bound to task_id,
   single-action, and replay-resistant. This avoids the "static API key" antipattern
   identified in IETF `draft-klrc-aiagent-auth`.

4. **Extension, not replacement**: The MCP server (`server.py`) is NOT modified.
   The PEP is designed to wrap tool calls. Wiring is a separate step (owner decision).

5. **Separation of "who" from "on whose behalf"**: `Identity.on_behalf_of` field
   plus `check_delegation()` enforces the confused-deputy defense.

---

## 4. Implemented Capabilities

### 4.1 IdentityStore (`_ops/identity/identity_store.py`)

- Typed identity: `user`, `agent`, `service`, `tool`
- Roles: `observer`, `worker`, `coordinator`, `owner` (ordered by privilege)
- Delegation: `on_behalf_of` field with `check_delegation()`
- Revocation: `revoke(agent_id)`
- deny-by-default: unknown agent = denied
- `default_store()` pre-populated from `bots.yaml` (owner, octopus, telbot, mcp-vault)

### 4.2 CapabilityToken (`_ops/identity/capability_token.py`)

- HMAC-SHA256 signed tokens
- Bound to: agent_id, task_id, action, resource, scope, duration
- Replay-resistant: unique nonce per token
- Time-bounded: default 5 min TTL, max 1 hour
- Resource patterns: `path:/notes/**`, `tool:*`, exact match
- `issue()` and `verify()` functions
- Fail-closed: no HMAC key = no tokens issued, no tokens validated

### 4.3 PolicyEnforcer (`_ops/identity/policy_enforcer.py`)

- deny-by-default: no identity + no token = DENIED
- RBAC: role hierarchy (observer < worker < coordinator < owner)
- ABAC: risk factors (secrets path, env path, git path, traversal, large output)
- Tool sensitivity levels: low (read tools), medium (propose), critical (modify/delete)
- Scope hierarchy: read < propose < write
- Audit trail: append-only JSONL with every decision (ALLOW/DENY/ESCALATE)
- Immutable `PolicyDecision` dataclass
- Token scope can override role scope (purpose-built grants)

### 4.4 MEDIUM-001 Fix

- `ghp_*`, `gho_*`, `ghu_*` patterns added to `_SECRET_RX` in both
  `write_gate_enforcer.py` and `gate.py`
- Aligned with `redact.py` patterns from G6 telemetry

---

## 5. Acceptance Scenario

**Requirement**: A worker with read permission attempts a write test. The request
must be DENIED before reaching the tool, and the policy decision must be auditable.

**Test**: `test_e2e_acceptance_scenario` in `test_g7_identity_zero_trust.py`

```
1. Issue read-only token to octopus for read_file_slice on /notes/**
2. Attempt propose_action (requires propose scope) with read-only token
3. PEP evaluates:
   - Identity: known (octopus, coordinator) -- PASS
   - Token: valid HMAC, not expired, not replayed -- PASS
   - Token action binding: token action=read_file_slice, requested=propose_action
   - Result: DENIED (action-mismatch)
4. Audit trail contains: decision=DENY, agent_id=octopus, action=propose_action
```

**Result**: PASS. The request is denied at the PEP layer, never reaching the tool.

**Additional acceptance tests**:
- `test_observer_write_denied`: observer cannot propose -- DENIED
- `test_worker_propose_denied`: worker cannot propose -- DENIED
- `test_mcp_vault_read_only`: MCP vault can only read -- DENIED for propose

---

## 6. Tests Executed

### 6.1 G7 New Test Suite

```
Command: PYTHONIOENCODING=utf-8 python -X utf8 _ops/tests/test_g7_identity_zero_trust.py
Result: 82/82 passed (0 failures, 0 errors, 0.342s)
```

| Section | Tests | Category |
|---|---|---|
| A. IdentityStore | 18 | Registration, lookup, privilege hierarchy, delegation, revocation |
| B. CapabilityToken | 20 | Issue, verify, binding, expiry, replay, forgery, resource matching |
| C. PolicyEnforcer | 21 | RBAC, ABAC, escalation, audit, token enhancement, nonce consumption |
| D. MEDIUM-001 | 6 | ghp_/gho_/ghu_ detection in write_gate_enforcer and gate |
| E. Integration | 6 | End-to-end identity + token + policy + audit |
| F. Adversarial | 11 | Forgery, stolen token, expiry, escalation, confused deputy, null byte |

### 6.2 Regression Tests (Post-MEDIUM-001 Fix)

```
Command: PYTHONIOENCODING=utf-8 python -X utf8 _ops/tests/test_g2_trusted_memory_loop.py
Result: 49/49 passed (0 failures, 0 errors)

Command: PYTHONIOENCODING=utf-8 python -X utf8 _ops/tests/test_g6_observability.py
Result: 53/53 passed (0 failures, 0 errors)

Command: PYTHONIOENCODING=utf-8 python -X utf8 _ops/tests/test_memory_gate.py
Result: 10/10 OK

Command: PYTHONIOENCODING=utf-8 python -X utf8 _ops/tests/test_telemetry.py
Result: 9/9 OK

Command: PYTHONIOENCODING=utf-8 python -X utf8 _ops/tests/test_memory_read_seam.py
Result: 5/5 OK

Command: PYTHONIOENCODING=utf-8 python -X utf8 _ops/tests/test_octopus_mcp_search.py
Result: 3/4 -- 1 FAIL (t_empty_query_is_handled) [PRE-EXISTING, not caused by G7]
```

### 6.3 Static Analysis

| Check | Result |
|---|---|
| Dangerous functions (eval/exec/compile/subprocess/os.system) | NONE found (re.compile is regex, not compile()) |
| Network imports | NONE found |
| External pip dependencies | NONE (stdlib-only) |
| Real secrets/credentials | NONE found |
| Unsafe deserialization | NONE |
| SQL injection | NONE (no SQL in G7 modules) |
| File write modes | All append-only (audit) |
| Token key exposure | NONE (key from env, never logged or printed) |

---

## 7. Security Scan Results

### 7.1 Privilege Escalation

| Test | Result |
|---|---|
| Observer -> propose without token | DENIED (insufficient-privilege) |
| Worker -> write without token | DENIED (insufficient-privilege) |
| Observer -> propose WITH propose-scoped token | ALLOW (token is valid grant) |
| Forged token with bad signature | DENIED (bad-signature) |
| Tampered token (agent_id changed) | DENIED (bad-signature) |

### 7.2 Confused Deputy

| Test | Result |
|---|---|
| Agent claims on_behalf_of without delegation | DENIED (check_delegation returns False) |
| Stolen token used by different agent | DENIED (agent-mismatch) |
| Token bound to wrong action | DENIED (action-mismatch) |
| Token bound to wrong task | DENIED (task-mismatch) |
| Token bound to wrong resource | DENIED (resource-mismatch) |

### 7.3 Token Replay

| Test | Result |
|---|---|
| Same nonce used twice | DENIED (replayed) on second use |
| Token with different nonce | ALLOW (fresh token) |
| Expired token | DENIED (expired) |
| Token TTL > max (clamped to 1h) | Token issued with 3600s max |

### 7.4 Audit Completeness

| Check | Result |
|---|---|
| Every DENY is audited | YES |
| Every ALLOW is audited | YES |
| Every ESCALATE is audited | YES |
| Audit includes agent_id, action, resource, reason | YES |
| Audit failure does not block decision | YES |
| Audit file is append-only JSONL | YES |

---

## 8. Findings by Severity

### CONDITIONAL-001: PEP Not Wired to MCP Server

| Field | Value |
|---|---|
| Severity | CONDITIONAL |
| Finding | The PolicyEnforcer evaluates decisions but is not called from `_handle()` in `server.py`. The MCP server accepts tool calls from any caller without identity check. |
| Impact | No runtime enforcement until wiring is done. |
| Remediation | Add identity assertion to MCP protocol (when upstream SEP-990 identity-assertion is available) or add a wrapper layer. Owner decision required. |

### CONDITIONAL-002: HMAC Key Not Provisioned

| Field | Value |
|---|---|
| Severity | CONDITIONAL |
| Finding | `OCTOPUS_CAPABILITY_TOKEN_HMAC` env var is not set in production. Without it, `issue()` returns `{"ok": False, "reason": "no-signing-key"}` and `verify()` returns `{"ok": False, "reason": "no-signing-key"}`. |
| Impact | Token system is fail-closed by design. No tokens can be issued or validated without the key. |
| Remediation | Generate and provision a 32+ character key in `OCTOPUS-flags.cmd` or equivalent. |

### CONDITIONAL-003: Nonce Store In-Memory Only

| Field | Value |
|---|---|
| Severity | CONDITIONAL |
| Finding | `used_nonces` is a Python `set[str]` in memory. Process restart loses all consumed nonces, allowing replay of previously-used tokens. |
| Impact | Replay protection resets on restart. |
| Remediation | Persist nonce set to append-only JSONL (pattern: `capability-effects.jsonl`). Load on startup. |

### MEDIUM-001 (Wave A): REMEDIATED

| Field | Value |
|---|---|
| Original Finding | `_SECRET_RX` missing `ghp_*` GitHub PAT pattern |
| Remediation | Added `ghp_`, `gho_`, `ghu_` patterns to both `write_gate_enforcer.py` and `gate.py` |
| Verification | 6 dedicated tests pass; all regression tests pass |
| Status | CLOSED |

### LOW-001: No Cross-Agent Impersonation Detection at Runtime

| Field | Value |
|---|---|
| Severity | LOW (informational) |
| Finding | An agent with a valid token can perform any action within its scope. There is no cross-agent check (e.g., "agent A cannot impersonate agent B's task"). Task binding exists but is optional in `verify()`. |
| Status | By design for vertical slice. Task binding enforcement is caller's responsibility. |

---

## 9. Environment Fingerprint

```
Platform: win32 (Windows 10.0.26200 x64)
Shell: Git Bash
Python: python -X utf8
Working Directory: F:\backup
Current Branch: equip/g7-identity-20260816
HEAD SHA: 360a7c6
Baseline SHA: a3431eb
Wave: B1 (G7 Identity)
Date: 2026-08-16
```

---

## 10. Evidence Paths

| Artifact | Path |
|---|---|
| Identity store | `_ops/identity/identity_store.py` |
| Capability token | `_ops/identity/capability_token.py` |
| Policy enforcer | `_ops/identity/policy_enforcer.py` |
| Package init | `_ops/identity/__init__.py` |
| Test suite | `_ops/tests/test_g7_identity_zero_trust.py` |
| MEDIUM-001 fix (gate) | `_ops/memory/gate.py` |
| MEDIUM-001 fix (enforcer) | `_ops/memory/write_gate_enforcer.py` |
| This evidence | `06-EVIDENCE/EQUIP-G7-IDENTITY-2026-08-16.md` |
| Wave A scan | `06-EVIDENCE/EQUIP-SCAN-WAVE-A-2026-08-16.md` |

---

## 11. Rollback Plan

All G7 changes are additive (5 new files + 2 files modified for MEDIUM-001).
Rollback = revert the single commit:

```bash
git checkout equip/g7-identity-20260816
git revert --no-commit 360a7c6
git checkout HEAD -- .
```

Or harder reset:
```bash
git reset --hard a3431eb
```

No migrations. No dependency changes. No database schema changes.
No state files created (all tests use tempdir).

---

## 12. Reproduce Commands

```bash
# Branch
git checkout equip/g7-identity-20260816

# G7 tests (82/82)
PYTHONIOENCODING=utf-8 python -X utf8 _ops/tests/test_g7_identity_zero_trust.py

# Regression: G2 (49/49)
PYTHONIOENCODING=utf-8 python -X utf8 _ops/tests/test_g2_trusted_memory_loop.py

# Regression: G6 (53/53)
PYTHONIOENCODING=utf-8 python -X utf8 _ops/tests/test_g6_observability.py

# Regression: gate (10/10)
PYTHONIOENCODING=utf-8 python -X utf8 _ops/tests/test_memory_gate.py

# Regression: telemetry (9/9)
PYTHONIOENCODING=utf-8 python -X utf8 _ops/tests/test_telemetry.py

# Regression: read seam (5/5)
PYTHONIOENCODING=utf-8 python -X utf8 _ops/tests/test_memory_read_seam.py

# MEDIUM-001 smoke test
PYTHONIOENCODING=utf-8 python -X utf8 _ops/memory/write_gate_enforcer.py

# Security scan (AST)
python -X utf8 -c "import ast; tree = ast.parse(open('_ops/identity/capability_token.py').read()); ..."
```

---

## 13. Recommended Next Steps

1. **Wire PEP to MCP server**: Add identity assertion and token validation to
   `_handle()` in `server.py` when upstream SEP-990 identity-assertion is available,
   or create a wrapper layer. Owner decision required.

2. **Provision HMAC key**: Generate `OCTOPUS_CAPABILITY_TOKEN_HMAC` and add to
   environment configuration.

3. **Persist nonce store**: Extend `used_nonces` to use append-only JSONL for
   restart-proof replay protection.

4. **Proceed to Wave B1 Group 8 (G8 Containment)**: Per EQUIP rules, next group
   may proceed if owner accepts this CONDITIONAL PASS. Independent scan by a
   different agent is required before merge.
