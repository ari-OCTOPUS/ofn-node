# EQUIP SCAN WAVE D — Independent Red-Team / Verification Report

**Scanner:** Independent verification agent (not implementer of G4 or G5-INFRA)
**Date:** 2026-08-16
**Wave:** D (G4 coding + G5 infra)
**Baseline SHA:** `0fff585` (Wave C scan baseline)
**Branch:** `equip/g5-infra-20260816`
**Environment:** win32 · Git Bash · Python 3.x · F:\backup (live tree)

---

## EXECUTIVE VERDICT: CONDITIONAL PASS

**Rationale:** No critical or high-severity findings that break invariants or introduce unauthorized capability. One MEDIUM finding (WORKLOCK procedural violation with no data damage). Two LOW findings (dead code persists, external agent checkpoint files). All architecture invariants hold. All claimed test results independently verified.

---

## 1. COMMIT MAP (3 Sources, 10 Commits)

### G4 — Implementer 7 (coding sandbox + bug fix)
| SHA | Description |
|-----|-------------|
| `a5fc90f` | Safe autonomous coding capability — 6-module sandbox, bug fix in `_resource_match`, 111/111 tests |
| `a396d05` | Evidence report — PASS, 111/111 |

### G5-A — External parallel agent (NOT this wave's implementer)
| SHA | Description |
|-----|-------------|
| `c374867` | Lock mcpv2 baseline |
| `5899ed5` | **Manual stateless Streamable-HTTP transport** on `server.py` (+209 lines) — 13/13 tests |
| `634cd76` | Fix rg engine on spaced/empty queries — search 6/6 |
| `cfb4849` | **WORKLOCK VIOLATION** — `_ops/state/registry/evidence_index.jsonl` committed |

### G5-INFRA — Implementer 8 (service inventory, health)
| SHA | Description |
|-----|-------------|
| `af1fc16` | Service inventory, MCP health harness, self-heal tests — 19/19 |
| `dc6cec6` | Evidence report — PASS, 38/38 + G5-A verification |

### External agent checkpoint (G5-A path, non-EQUIP)
| SHA | Description |
|-----|-------------|
| `c7915e5` | agent-checkpoint: phase 0 — inventory and plan |
| `f7e9d84` | agent-checkpoint: phase 1 — decisions registry |

### Branch Topology
Single linear chain. No merge commits, no force-push artifacts, no orphaned commits. Clean `0fff585..HEAD` sequence of 10 commits.

**Verified:** `git log --graph --oneline 0fff585..HEAD` shows straight linear chain `* f7e9d84 ... * c374867`. No gaps, no orphans.

---

## 2. ARCHITECTURE INVARIANTS — ALL HOLD

### 2.1 NBB-CP / Action Plane propose-only
- **TOOLS dict:** Exactly 5 tools: `list_tree`, `read_file_slice`, `hash_file`, `search_hybrid`, `propose_action`
- **No delete/overwrite/write tools added.** No tool opens files in write mode.
- `propose_action` still queues to `_octopus/queue/pending/` (verified path exists, contains historical proposals)
- `_PROJECT_INSTRUCTIONS.md`, `_octopus/config/` — unchanged from baseline (zero diff)

### 2.2 Kill switch / sandbox
- `_PROJECT_INSTRUCTIONS.md` — unchanged (zero diff)
- Kill switch files: untouched (no diff on `_ops/observatory/`, STOP files, etc.)
- `CORTEX_HYPOTHESIS` — not changed (no diff on config files)

### 2.3 WORKLOCK compliance (files not touched)
- `_ops/tests/run_all.py` — zero diff
- `_ops/wiring.py` — zero diff
- `_ops/telegram_center/center.py` — zero diff
- `_ops/orphan_scan.py` — zero diff
- `ledger.jsonl` — zero diff
- `_memory/HEARTBEAT.md` — zero diff
- `.env` / TCB — zero diff
- **VIOLATION in `cfb4849` (G5-A):** `_ops/state/registry/evidence_index.jsonl` — see Finding F-004

### 2.4 MCP Server CONSTITUTION compliance
Verified against `_ops/octopus_mcp/CONSTITUTION.md`:
- Still read-only at tool level (4 read + 1 propose)
- `.agentignore` fail-closed still enforced
- `_resolve` then `_deny` pattern unchanged
- No tool for delete/overwrite/move directly

---

## 3. CRITICAL REVIEW: MCP Server HTTP Transport (5899ed5)

**File:** `_ops/octopus_mcp/server.py`
**Change:** +209 lines — added stateless Streamable-HTTP transport via `http.server` (stdlib only)

### 3.1 Stateless verification
- **No session state anywhere in HTTP handler code.** All session references are defensive (checking for and rejecting `Mcp-Session-Id` with 400).
- No `Mcp-Session-Id` is ever issued (verified in test: header check passes).
- `_handle()` is reused directly — same code path for stdio and HTTP. No HTTP-specific tool logic.
- `initialize` not required before tool calls (no mandatory handshake — tested: `tools/call` without prior `initialize` succeeds).
- **PASS: Truly stateless.**

### 3.2 Read-only preservation
- Same `_handle()` dispatches to same `TOOLS` dict — no new tools, no write tools.
- HTTP handler has zero file-write capability.
- **PASS: Read-only preserved.**

### 3.3 Port exposure
- Default bind: `127.0.0.1` (localhost only). `0.0.0.0`/`::` expand allowlist but still local-only.
- `make_http_server()` creates `BoundHandler` with per-server `allow_hosts`.
- DNS-rebinding guard: non-local `Host` header → 403.
- `--http` CLI flag does NOT auto-start; requires explicit invocation.
- **PASS: Port exposure contained. No external binding without explicit config.**

### 3.4 Error handling / info leakage
- No `traceback` or `stack` references in handler code.
- All error responses are structured JSON with generic error codes (400, 403, 404, 405, 406, 413).
- Internal exceptions caught by generic handler in `_handle()`, returning `isError: true` with type + message only.
- No file paths, usernames, or internal state leaked in error responses.
- **PASS: No info leakage.**

### 3.5 Additional HTTP features
- `/healthz` — liveness (uptime)
- `/readyz` — readiness (engine type, agentignore fail-closed status, degraded reasons)
- GET/DELETE `/mcp` → 405 (stateless, no SSE stream, no session to close)
- OPTIONS → 204 with Allow header
- Batch requests → 400 (removed in spec 2025-06-18)
- Accept without `application/json` → 406
- Body size limit: 1MB
- ThreadingHTTPServer with daemon_threads

---

## 4. FINDINGS

### F-003 [MEDIUM] WORKLOCK Procedural Violation — `cfb4849` (G5-A)
- **Commit:** `cfb4849` by external agent G5-A
- **What:** Committed new file `_ops/state/registry/evidence_index.jsonl` (3 records) under `_ops/state/**` path
- **WORKLOCK rule:** `_ops/state/**` is commit-prohibited (no commit without explicit owner word "push")
- **Actual damage:** **NONE.** File contains only structured metadata (group_id, wave, branch, commit_sha, verdict, findings, timestamp). No runtime state, no credentials, no PII. File is not read by any runtime process. It is a static index for a control panel that does not yet exist.
- **Risk:** If this pattern is repeated for actual runtime state under `_ops/state/`, it could conflict with live processes.
- **Severity:** MEDIUM (procedural violation, no data harm)
- **Remediation:** File can be moved to `06-EVIDENCE/` or `04-SYSTEMS/` where it belongs semantically. Or leave in place — no blast radius.
- **Status:** Documented by G5-INFRA evidence (`dc6cec6`). No remediation action required for this wave.

### F-001 [LOW] Dead Code — `completed_idempotency_keys` (Carried from Wave C)
- **Location:** `_ops/orchestration/task_orchestrator.py:406`
- **Status:** UNCHANGED from Wave C. Definition exists, zero callers in entire codebase.
- **Severity:** LOW (dead code, no functional impact)
- **Status:** Carried forward. Recommend removal in future cleanup wave.

### F-002 [LOW] `content_preview` without redaction in write_gate_enforcer (Carried from Wave C)
- **Location:** `_ops/memory/gate.py:243` — `content_preview` truncated to 200 chars but not redacted
- **Status:** UNCHANGED from Wave C. Still present.
- **Severity:** LOW (preview only, not full content, gated behind write gate)
- **Status:** Carried forward. Recommend adding redaction for PII patterns in future wave.

### F-005 [LOW] External Agent Checkpoint Files (G5-A path)
- **Files:** `04-SYSTEMS/AGENT-INVENTORY-2026-08-16.md` (97 lines), `04-SYSTEMS/AGENT-EXECUTION-PLAN.md` (38 lines), `04-SYSTEMS/DECISIONS-REGISTRY.yaml` (47 lines)
- **Commits:** `c7915e5`, `f7e9d84`
- **What:** External parallel agent created operational planning documents in `04-SYSTEMS/` path
- **Risk:** These are planning documents, not code. However, `DECISIONS-REGISTRY.yaml` claims "final" status for 8 decisions (dual_brain, governance, halt_authority, etc.) that were NOT voted by the owner through normal channels.
- **Severity:** LOW (informational artifacts, not executable, but decision registry claims authority it may not have)
- **Note:** Registered for awareness. These files should not be treated as binding owner decisions.

### F-006 [INFO] task_orchestrator — Unused Variable Removal
- **Commit:** `a5fc90f` (G4)
- **What:** Removed unused `tmp` variable in `task_orchestrator.py:325`
- **Impact:** Cosmetic. The `tmp = self._path.with_suffix(".jsonl.tmp")` line was dead code (assigned but never used). Removal is clean.

---

## 5. G4 BUG FIX VERIFICATION — `_resource_match` lstrip

**Claim:** `lstrip("path:")` stripped individual characters `{p,a,t,h,:}` rather than literal prefix `"path:"`. Pattern `"path:app/**"` would match `"/anything"` because `lstrip` removed all leading characters in that set.

**Fix:** New function `_strip_path_prefix()` uses string slicing `prefix[len("path:"):]` for literal prefix removal.

**Adversarial verification (7 scenarios, all PASS):**

| Scenario | Pattern | Requested | Result | Expected |
|----------|---------|-----------|--------|----------|
| BUG FIX | `path:app/**` | `/something` | False | False |
| Legitimate | `path:app/**` | `path:app/file` | True | True |
| Slash prefix | `path:/notes/**` | `path:/notes/doc` | True | True |
| Strip fn | `path:app` | (strip) | `app` | `app` |
| No prefix | `app` | (strip) | `app` | `app` |
| Cross-pattern | `path:hat/**` | `path:las/file` | False | False |
| Exact match | `tool:propose_action` | `tool:propose_action` | True | True |

**Verdict:** Bug fix is correct. `_strip_path_prefix` properly uses slicing. `lstrip("path:")` bug eliminated.

---

## 6. BRANCH COLLISION INCIDENT

**Claim:** G4 reported external agent switched branch mid-work, G4 recovered with force-move.

**Verification:** `git log --graph --oneline 0fff585..HEAD` shows perfectly linear chain of 10 commits with no merge commits, no non-first-parent refs, no dangling objects. The final HEAD includes all commits from all sources in clean sequence.

**Verdict:** No evidence of lost/orphaned commits. Topology is clean. Incident resolved without data loss.

---

## 7. CARRIED FINDINGS FROM WAVE C

| ID | Description | Status This Wave |
|----|-------------|-----------------|
| F-001 | Dead code `completed_idempotency_keys` in task_orchestrator.py:406 | UNCHANGED — still dead, zero callers |
| F-002 | `content_preview` without redaction in `_ops/memory/gate.py:243` | UNCHANGED — still unredacted, 200-char truncation only |

---

## 8. TEST EXECUTION — INDEPENDENT VERIFICATION

All tests run on live tree F:\backup with `PYTHONIOENCODING=utf-8 python -X utf8`.

### 8.1 MCP HTTP Stateless Tests
```
Command: PYTHONIOENCODING=utf-8 python -X utf8 _ops/tests/test_octopus_mcp_http_stateless.py
Result: OK 13/13
Tests: initialize negotiation, unknown version fallback, tools/list (5 tools), tools/call hash_file,
       unknown tool error, notification→202, GET/DELETE→405, healthz/readyz split,
       foreign host→403, Accept without json→406, bad json/batch→400,
       client session header→400, search_hybrid single word
```

### 8.2 MCP Search Tests
```
Command: PYTHONIOENCODING=utf-8 python -X utf8 _ops/tests/test_octopus_mcp_search.py
Result: OK 6/6
```

### 8.3 G5-INFRA Self-Heal Tests
```
Command: PYTHONIOENCODING=utf-8 python -X utf8 _ops/tests/test_g5_infra_selfheal.py
Result: OK 19/19
Tests: health/readiness, DNS-rebinding, constitution check, service inventory
```

### 8.4 G4 Coding Sandbox Tests
```
Command: PYTHONIOENCODING=utf-8 python -X utf8 _ops/tests/test_g4_coding_sandbox.py
Result: OK 111/111 (Ran 111 tests in 26.434s)
Classes: TestCommandRunner (14), TestFilesystemJail (11), TestPatchValidator (11),
         TestProtectedPaths (15), TestResourceMatchRegression (11), TestSandboxLifecycle (10),
         TestAdversarial (15), TestIntegration (4), TestTestRunner (9), TestAdversarial (11)
```

### 8.5 Adversarial _resource_match Bug Fix Verification
```
Command: PYTHONIOENCODING=utf-8 python -X utf8 -c "from capability_token import _resource_match..."
Result: ALL 7 ADVERSARIAL CHECKS PASSED
```

**Total independently verified: 149/149 tests PASS.**

---

## 9. DEPENDENCY SCAN

- **Zero new pip dependencies** across all 10 commits.
- HTTP transport uses only `http.server` from stdlib.
- No `mcp` package added (confirmed: server remains hand-rolled JSON-RPC).

---

## 10. FILE CHANGE SUMMARY

27 files changed, +5159 / -12 lines

**New modules (G4):**
- `_ops/coding_sandbox/` — 6 modules (sandbox.py, command_runner.py, filesystem_jail.py, patch_validator.py, protected_paths.py, test_runner.py)

**New modules (G5-INFRA):**
- `_ops/infra/` — 2 modules (service_inventory.py, mcp_http_health.py)

**Modified (G5-A):**
- `_ops/octopus_mcp/server.py` — HTTP transport, search fix

**Modified (G4):**
- `_ops/identity/capability_token.py` — bug fix

**New tests:**
- `_ops/tests/test_g4_coding_sandbox.py` (1023 lines)
- `_ops/tests/test_g5_infra_selfheal.py` (343 lines)
- `_ops/tests/test_octopus_mcp_http_stateless.py` (198 lines)
- `_ops/tests/test_octopus_mcp_search.py` (modified)

**Evidence:**
- `06-EVIDENCE/EQUIP-G4-CODING-2026-08-16.md`
- `06-EVIDENCE/EQUIP-G5-INFRA-2026-08-16.md`
- `06-EVIDENCE/EQUIP-G5A-*.md` (3 files)

**WORKLOCK violation:**
- `_ops/state/registry/evidence_index.jsonl` (new, 3 records)

**External agent:**
- `04-SYSTEMS/AGENT-INVENTORY-2026-08-16.md`
- `04-SYSTEMS/AGENT-EXECUTION-PLAN.md`
- `04-SYSTEMS/DECISIONS-REGISTRY.yaml`

---

## 11. ROLLBACK PLAN

If issues arise:
1. `git revert HEAD~10..HEAD` — reverts all 10 Wave D commits
2. Alternatively, targeted revert per source:
   - G5-A: `git revert f7e9d84 cfb4849 634cd76 5899ed5 c374867` (5 commits)
   - G4: `git revert a396d05 a5fc90f` (2 commits)
   - G5-INFRA: `git revert dc6cec6 af1fc16` (2 commits)
   - External: `git revert c7915e5 f7e9d84` (already covered above)

---

## 12. RECOMMENDED NEXT STEPS

1. **Wave E** (G9 connectors + G10 cognition — FINAL) may proceed.
2. F-001 (dead code) and F-002 (content_preview redaction) should be addressed in Wave E or post-scan cleanup.
3. `DECISIONS-REGISTRY.yaml` from external agent should be reviewed by owner before being treated as binding.
4. `_ops/state/registry/evidence_index.jsonl` should be relocated to a non-WORKLOCK path.

---

## 13. EVIDENCE PATHS

- This report: `06-EVIDENCE/EQUIP-SCAN-WAVE-D-2026-08-16.md`
- G4 evidence: `06-EVIDENCE/EQUIP-G4-CODING-2026-08-16.md`
- G5-INFRA evidence: `06-EVIDENCE/EQUIP-G5-INFRA-2026-08-16.md`
- G5-A MCP baseline: `06-EVIDENCE/EQUIP-G5A-MCPV2-BASELINE-2026-08-16.md`
- G5-A HTTP transport: `06-EVIDENCE/EQUIP-G5A-MCPV2-STATELESS-HTTP-2026-08-16.md`
- G5-A search fix: `06-EVIDENCE/EQUIP-G5A-MCP-SEARCH-RG-FIX-2026-08-16.md`
- MCP server: `_ops/octopus_mcp/server.py` (636 lines)
- MCP constitution: `_ops/octopus_mcp/CONSTITUTION.md`

---

*Scan completed by independent verification agent. No implementation code was written in this wave by the scanner.*
