# EQUIP G9 — Personal Connectors — Evidence Report

**Date:** 2026-08-16
**Wave:** E1 (Group 9)
**Branch:** `equip/g9-connectors-20260816`
**Base:** `cf034f8` (Wave D CONDITIONAL PASS)
**Implementer:** 9 (Wave E1)
**Verdict:** PASS

---

## Executive Verdict: PASS

A unified connector gateway was implemented with registry, capability manifests,
privacy-preserving controls (PII/health/financial redaction), consent enforcement,
owner gate escalation, revocation, and full audit trail. All 6 builtin connectors
(Telegram, GitHub, HuggingFace, Email, Finance, HealthKit) are registered with
typed manifests enforcing read-only constraints for HealthKit/Finance as required.
176/176 tests pass with 0 failures, 0 regressions on dependent groups (G7 82/82,
G8 71/71, consent 10/10). Security scan: 0 actionable findings.

---

## Discovered Architecture

### Existing connectors in the vault (pre-G9)

| Connector | Location | Status | Key Findings |
|-----------|----------|--------|-------------|
| **Telegram** | `_ops/telegram_center/`, `_ops/telegram_contract/` | Live control plane | Full access contract with surface routing, capability manifest schema, ADR-042 send-site allowlist (Phase 0). WORKLOCK on `center.py`. |
| **Email** | `_ops/legs/email_inbound.py` | Flag-off, propose-only | Gmail OAuth readonly. `OCTOPUS_WIRE_EMAIL=1` flag. $0, stdlib-only. |
| **Finance** | `_ops/legs/pocketsmith_api.py` | Flag-off, propose-only | PocketSmith API v2 read-only GET only. `OCTOPUS_WIRE_POCKETSMITH` flag. $0, stdlib-only. |
| **Consent** | `_ops/legs/consent_store.py`, `consent_gate.py`, `consent_firewall.py` | Active | Full consent state machine with structural firewall (3-layer). |
| **Health sync** | `_ops/legs/sync_health.py` | Monitoring | Internal sync monitoring, not an external health API connector. |

### Existing policy modules reused

| Module | Location | Role in G9 |
|--------|----------|------------|
| Risk Gate | `_ops/containment/risk_gate.py` | Risk tier classification (G8, 71/71 tests) |
| Approval Binder | `_ops/containment/approval_binder.py` | HMAC approval tokens (G8) |
| Policy Enforcer | `_ops/identity/policy_enforcer.py` | PEP for zero-trust (G7, 82/82 tests) |
| Consent Gate | `_ops/legs/consent_gate.py` | Consent predicates (10/10 tests) |
| Write Gate | `_ops/memory/write_gate_enforcer.py` | Memory write validation (G2) |

### Gap identified

No unified connector registry or gateway existed. Each connector had independent
auth/flag/policy without cross-connector consistency. No mechanism for:
- Registering connectors with typed capability manifests
- Consistent scope enforcement across connectors
- Cross-connector leakage prevention
- Immediate revocation of connector access
- PII/health/financial redaction at the gateway level

---

## Implemented Capabilities

### New files

| File | Purpose |
|------|---------|
| `_ops/connectors/__init__.py` | Package exports and documentation |
| `_ops/connectors/schema.py` | Data types: `ConnectorManifest`, `ConnectorRequest`, `ConnectorResponse`, enums for scope/risk/gate, builtin connector definitions, JSON Schema generation, PII redaction patterns |
| `_ops/connectors/registry.py` | `ConnectorRegistry`: register/revoke/lookup connectors, audit trail, seeded with 6 builtin connectors |
| `_ops/connectors/gateway.py` | `ConnectorGateway`: unified routing with 7-step policy pipeline (validate, resolve, revoke-check, scope, target, owner-gate, consent), audit logging, stats |
| `_ops/tests/test_connector_gateway.py` | 176 tests in 9 sections |

### Connector manifests (6 builtin)

| Connector | read_scope | write_scope | risk_class | owner_gate | consent | PII | Financial | Health |
|-----------|-----------|-------------|------------|------------|---------|-----|-----------|--------|
| telegram | detailed | draft | irreversible | write_only | no | no | no | no |
| github | detailed | approved_write | reversible_write | always | no | no | no | no |
| huggingface | metadata | none | read_only | never | no | no | no | no |
| email | summarized | none | read_only | never | yes | yes | no | no |
| finance | summarized | none | read_only | never | yes | yes | yes | no |
| healthkit | summarized | none | read_only | always | yes | yes | no | yes |

### Key design decisions

1. **Deny-by-default**: Unknown connector or action = blocked immediately
2. **Structural firewall**: HealthKit/Finance write_scope=NONE enforced in `ConnectorManifest.__post_init__`
3. **HF_TOKEN never created**: `huggingface` builtin has `token_env=""`, write_scope=NONE
4. **Resolve-before-act**: Target must be in allowlist before any operation
5. **Draft != send**: `DRAFT` actions never require approval but never touch external systems
6. **Revocation is immediate**: `revoke()` sets tombstone, `lookup()` returns None
7. **Redaction is recursive**: PII/health/financial patterns + sensitive key names in dicts
8. **Consent is per-connector**: Each manifest declares `requires_consent`, enforced at gateway
9. **$0, stdlib-only**: No new pip dependencies

---

## Changed Files

```
_ops/connectors/__init__.py          (NEW)
_ops/connectors/schema.py            (NEW)
_ops/connectors/registry.py          (NEW)
_ops/connectors/gateway.py          (NEW)
_ops/tests/test_connector_gateway.py (NEW)
```

No existing files modified. No dependencies added.

---

## Tests + Exact Results

### G9 Connector Gateway Tests: 176/176 PASS

```
test_connector_gateway (G9 CONNECTORS)
--- Schema: builtin connectors ---
  30 PASS (6 connectors x 5 assertions)
--- Schema: health must be read-only ---
--- Schema: finance read-only or draft ---
--- Schema: forbidden risk_class rejected ---
--- Schema: invalid connector_id ---
  15 PASS
--- Schema: serialization round-trip ---
  6 PASS
--- Schema: JSON Schema ---
  4 PASS
--- Registry: seed / lookup / register / revoke / re-register / list / audit ---
  29 PASS
--- Telegram: read/write/draft/target/disconnect ---
  12 PASS
--- GitHub: read/write/dry-run ---
  8 PASS
--- HuggingFace: read/write ---
  4 PASS
--- Email: read(consented, no-checker, denied)/write ---
  8 PASS
--- Finance: read(consented, no-checker)/write/draft ---
  7 PASS
--- HealthKit: read(consented, no-checker)/write ---
  5 PASS
--- Gateway: unknown/invalid/empty/revoked/dry-run/audit/stats ---
  15 PASS
--- Redaction: PII/dict/nested/list ---
  10 PASS
--- Adversarial: connector_id/target/consent-error/empty ---
  10 PASS
--- Data classes: serialization ---
  7 PASS
--- Isolation: revoke-cascade / consent-per-connector / write-scope ---
  10 PASS
--- Convenience: default_gateway ---
  2 PASS
PASS 176/176 (0 failures)
```

### Regression Tests: All Green

| Test Suite | Result |
|-----------|--------|
| G8 containment (`test_containment.py`) | 71/71 PASS |
| G7 identity (`test_g7_identity_zero_trust.py`) | 82/82 PASS |
| Consent gate (`test_consent_gate.py`) | 10/10 PASS |

---

## Security Scan Findings by Severity

### Static analysis (connector module files)

| Category | Count | Details |
|----------|-------|---------|
| HIGH (secrets, injection, deserialization) | 0 | None |
| INFO/LOW (network, broad exception) | 0 | None |

### G9 connector-specific scan

| Check | Count | Details |
|-------|-------|---------|
| overbroad OAuth scope | 0 | No OAuth scopes in module |
| cross-connector leakage | 0 | Each request scoped to single connector_id |
| wrong recipient | 0 | Target allowlist enforced per-connector |
| stale consent | 0 | Consent checked per-request, not cached |
| hidden write permission | 0 | All write scopes in typed manifests |
| sensitive logs | 0 | Only section labels in test output (false positives) |
| token persistence | 0 | Only env var names stored, never values |
| revoked-token reuse | 0 | Revocation is immediate tombstone |
| untrusted model artifacts | 0 | HF write blocked, no model download in scope |
| accidental long-term storage | 0 | Retention class enforced per manifest |

**Result: CLEAN (0 actionable findings)**

---

## Unresolved Risks

1. **Telegram write path**: Current `write_scope=DRAFT` means no direct writes. If
   upgraded to `APPROVED_WRITE`, the gateway owner_gate will require approval, but
   the actual send implementation in `center.py` (WORKLOCK) is untouched.

2. **GitHub token**: The `github` connector assumes `GITHUB_TOKEN` env var. The gateway
   does not manage token lifecycle; it only routes requests. Token rotation is the
   owner's responsibility.

3. **Consent checker integration**: The gateway accepts a callback but does not
   integrate with the vault's `consent_store.py` directly. This is intentional
   (separation of concerns) but means the caller must wire the consent check.

4. **No MCP integration yet**: The gateway is a Python API. It could be exposed as
   MCP tools in a future EQUIP group, but that is explicitly not in this vertical slice.

---

## Rollback

```bash
git checkout equip/g5-infra-20260816
# Delete connector files:
rm -rf _ops/connectors/
rm _ops/tests/test_connector_gateway.py
# No migration, no deps, no state changes.
```

---

## Reproduce Commands

```bash
cd F:\backup
git checkout equip/g9-connectors-20260816

# Run G9 tests
PYTHONIOENCODING=utf-8 python -X utf8 _ops/tests/test_connector_gateway.py

# Run regression tests
PYTHONIOENCODING=utf-8 python -X utf8 _ops/tests/test_containment.py
PYTHONIOENCODING=utf-8 python -X utf8 _ops/tests/test_g7_identity_zero_trust.py
PYTHONIOENCODING=utf-8 python -X utf8 _ops/tests/test_consent_gate.py
```

---

## Evidence Paths

- Test file: `F:\backup\_ops\tests\test_connector_gateway.py`
- Connector package: `F:\backup\_ops\connectors/`
- This report: `F:\backup\06-EVIDENCE\EQUIP-G9-CONNECTORS-2026-08-16.md`

---

## Recommended Next Step

1. **G10 Cognition** (per sequential plan)
2. Optionally: Wire the connector gateway to MCP server for external tool discovery
3. Optionally: Integrate consent_store.py as the default consent checker callback
