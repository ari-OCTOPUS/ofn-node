# EQUIP G4 — Safe Autonomous Coding Capability — Evidence Report

**Date:** 2026-08-16
**Implementer:** EQUIP D1 Agent (G4 Coding)
**Branch:** `equip/g4-coding-20260816`
**Base:** `equip/g3-perception-20260816` @ `0fff585`
**Verdict:** **PASS**

---

## Executive Verdict: PASS

G4 delivers a complete vertical slice for safe autonomous coding capability:
a 6-submodule `coding_sandbox` package with deny-by-default filesystem jail,
shell allowlist, patch validation, test runner, and sandbox lifecycle management.
Additionally, a real security vulnerability (MEDIUM-002) in `_resource_match` was
discovered, fixed, and regression-tested. All 111 new tests pass with zero new
dependencies and zero secrets.

---

## Discovered Architecture

### Existing Coding-Related Infrastructure
- `_ops/collab_coding.py`: Propose-only coding collaboration via Telegram (flag-gated)
- `_ops/code_autonomy_card.py`: Read-only card showing recent autonomous code actions
- `_ops/shell_capability.py`: Raw shell execution with deny-list (flag-gated, activation-gated)
- `_ops/self_patch.py`: Self-patching mechanism
- `_ops/octopus_mcp/server.py`: MCP server (JSON-RPC stdio, propose-only action plane)

### Reusable Modules from Prior EQUIP Groups
- **G1** `task_orchestrator.py`: Task state machine, checkpointing, idempotency, retry
- **G7** `identity/policy_enforcer.py`: PEP (deny-by-default, RBAC, ABAC, audit)
- **G7** `identity/capability_token.py`: Short-lived, scoped, HMAC-signed tokens
- **G8** `containment/risk_gate.py`: Risk classification, budget tracking, kill switch
- **G8** `containment/approval_binder.py`: Approval flow for sensitive operations
- **G3** `observatory/fetch_guard.py`: Network fetch with SSRF protection

### Security Bug Found: MEDIUM-002 (lstrip in _resource_match)

**Location:** `_ops/identity/capability_token.py`, line 279 (old)
**Severity:** MEDIUM (capability token path matching bypass)

**Bug:** The `_resource_match()` function used `str.lstrip("path:")` to strip the
`"path:"` prefix from capability token patterns. However, `str.lstrip()` strips
individual **characters** from the character set `{'p','a','t','h',':'}`, not the
literal string `"path:"`.

**Impact:** A capability token granting access to `path:app/**` would match
`/etc/passwd`, `/notes/daily.md`, and any path starting with `/` because:
```python
"path:app/".lstrip("path:")  # Returns "/" — not "app/"
```
This effectively granted unrestricted filesystem access via a scoped token.

**Fix:** Introduced `_strip_path_prefix()` using string slicing (`slicing`)
instead of `lstrip()`:
```python
def _strip_path_prefix(prefix: str) -> str:
    if prefix.startswith("path:"):
        return prefix[len("path:"):]
    return prefix
```

---

## Implemented Capabilities

### 1. Protected Path Definitions (`protected_paths.py`)
- Deny-by-default path classification system
- 4 permission levels: PROTECTED, OWNER_APPROVAL, READ_ONLY, WRITABLE
- 12 protected pattern categories (safety, credentials, git internals, policy, runtime state, CI/deploy)
- Worktree-aware writable detection
- Quick-check convenience functions

### 2. Filesystem Jail (`filesystem_jail.py`)
- Path normalization without disk access (PurePosixPath)
- Symlink escape detection (blocks symlinks pointing outside jail)
- Path traversal detection (`..` sequences)
- System path blocking (`/etc/passwd`, `C:\Windows\`)
- Batch validation for multiple paths

### 3. Command Runner (`command_runner.py`)
- Shell allowlist: 12 command categories (python, git, file ops, search, code quality)
- Deny-list: network (curl, wget, ssh), privilege escalation (sudo), destructive (rm -rf), dangerous git (push, merge, reset --hard, clean -f)
- Timeout enforcement with subprocess
- Output size limit (100 KB per stream)
- Proxy environment variable stripping (network default-deny)
- Append-only audit trail

### 4. Patch Validator (`patch_validator.py`)
- Diff size limits (50 KB max, 500 lines max, 10 files max)
- Unified diff format validation (file headers + hunk headers required)
- Secret pattern detection (8 patterns: ghp_, sk-, AKIA, password=, api_key=, xox*, gho_, ghu_)
- Protected path violation detection in patch filenames
- Reversibility tracking

### 5. Test Runner (`test_runner.py`)
- Multi-format output parsing (pytest, unittest, script-style N/N)
- Timeout enforcement
- Output size limit (200 KB)
- Kill-switch awareness
- No-skip enforcement (agent cannot hide failing tests)

### 6. Sandbox Lifecycle Manager (`sandbox.py`)
- Git worktree + branch creation per task
- State machine (CREATED -> WORKTREE_READY -> CODING -> TESTING -> COMMITTED -> CLEANED)
- Kill-switch propagation (file-based + callable)
- Integrated command/test/patch/commit operations
- Task ID + evidence reference in commit messages
- Automatic cleanup (worktree removal + branch deletion)

---

## Changed Files

| File | Action | Lines |
|------|--------|-------|
| `_ops/coding_sandbox/__init__.py` | NEW | 22 |
| `_ops/coding_sandbox/sandbox.py` | NEW | 473 |
| `_ops/coding_sandbox/protected_paths.py` | NEW | 199 |
| `_ops/coding_sandbox/filesystem_jail.py` | NEW | 167 |
| `_ops/coding_sandbox/command_runner.py` | NEW | 288 |
| `_ops/coding_sandbox/patch_validator.py` | NEW | 218 |
| `_ops/coding_sandbox/test_runner.py` | NEW | 275 |
| `_ops/tests/test_g4_coding_sandbox.py` | NEW | 998 |
| `_ops/identity/capability_token.py` | MODIFIED | +30/-8 |
| `_ops/orchestration/task_orchestrator.py` | MODIFIED | +0/-2 |

**Total:** 2866 insertions, 10 deletions across 10 files.

---

## Migrations / New Dependencies

None. All code is stdlib-only (Python 3.10+). No pip installs. No network.

---

## Tests + Exact Results

### G4 Test Suite (111 tests)
```
Ran 111 tests in 20.662s

OK (111/111, 0 failures, 0 errors)

Sections:
  A. Protected Paths:         20/20
  B. Filesystem Jail:         12/12
  C. Command Runner:          20/20
  D. Patch Validator:         11/11
  E. Test Runner:              8/8
  F. Sandbox Lifecycle:        7/7
  G. Bug Regression (lstrip): 11/11
  H. Integration:               6/6
  I. Adversarial/Negative:    16/16
```

### Regression Tests (prior EQUIP groups)
```
G7 Identity Zero Trust:  82/82 passed (0 failures, 0 errors)
G1 Orchestration:         50/50 passed ALL GREEN
G3 Perception Envelope:   77/77 passed
```

---

## Security Scan Findings

| Category | Severity | Finding |
|----------|----------|---------|
| Secrets | NONE | No real credentials in code. Test fixtures use fake tokens intentionally. |
| Command injection | NONE | No os.system(), eval(), exec(). shell=True bounded by allowlist. |
| Path traversal | MITIGATED | Filesystem jail detects traversal; PurePosixPath normalization. |
| Unsafe deserialization | NONE | No pickle, yaml.load, marshal. |
| Network access | NONE | No urllib, requests, socket. Proxy vars stripped at execution. |
| Dependency confusion | N/A | Zero new dependencies. |
| Test deletion | MITIGATED | No-skip enforcement in test_runner. Agent cannot xfail/skip/delete. |
| Symlink escape | MITIGATED | Detected by filesystem_jail check_jail(). |
| Secret access | MITIGATED | Protected paths deny .env, credentials, tokens, policy files. |
| Unauthorized push/merge | MITIGATED | git push/merge blocked in command_runner deny-list. |

### MEDIUM-002: lstrip Path Traversal in Capability Tokens
- **Severity:** MEDIUM
- **Status:** FIXED
- **Regression tests:** 11 tests in Section G
- **Backward compatibility:** All 82 G7 tests pass (no regression)

---

## Unresolved Risks

1. **Sandbox escape via code execution:** The command_runner uses `shell=True` which
   is inherently harder to sandbox than list-based subprocess calls. The allowlist
   mitigates but doesn't eliminate this risk. A future enhancement could use list-based
   argument passing for all commands.

2. **Windows symlink handling:** Symlink creation requires admin privileges on
   Windows. The jail detection code handles this gracefully but cannot test the
   symlink-escape path on restricted environments.

3. **Test file execution:** The test_runner executes arbitrary Python files. A
   malicious test file could attempt os operations. This is mitigated by running
   within the worktree jail, but the Python process itself has full system access.

4. **Git worktree isolation:** Git worktrees share the same object store. An agent
   could theoretically create extremely large objects. The patch size limit (50 KB)
   partially mitigates this.

---

## Rollback Plan

```bash
git checkout equip/g3-perception-20260816
# All G4 changes are on equip/g4-coding-20260816 and can be safely discarded.
# The branch can be deleted without affecting master or any other branch.
```

Files to remove if rollback needed:
- `_ops/coding_sandbox/` (entire directory)
- `_ops/tests/test_g4_coding_sandbox.py`
- Revert `_ops/identity/capability_token.py` and `_ops/orchestration/task_orchestrator.py`

---

## Reproduce Commands

```bash
# Run G4 tests
cd F:/backup
PYTHONIOENCODING=utf-8 python -X utf8 _ops/tests/test_g4_coding_sandbox.py

# Verify G7 regression
PYTHONIOENCODING=utf-8 python -X utf8 _ops/tests/test_g7_identity_zero_trust.py

# Verify G1 regression
PYTHONIOENCODING=utf-8 python -X utf8 _ops/tests/test_orchestration_g1.py

# Verify G3 regression
PYTHONIOENCODING=utf-8 python -X utf8 _ops/tests/test_perception_envelope.py

# Demonstrate the lstrip bug fix
python -X utf8 -c "
import sys; sys.path.insert(0, '_ops/identity')
from capability_token import _resource_match
# Before fix: _resource_match('/etc/passwd', 'path:app/**') was True
# After fix: must be False
assert not _resource_match('/etc/passwd', 'path:app/**'), 'BUG STILL EXISTS'
assert _resource_match('path:app/main.py', 'path:app/**'), 'VALID PATH BLOCKED'
print('MEDIUM-002 regression: PASS')
"
```

---

## Evidence Paths

- Test file: `_ops/tests/test_g4_coding_sandbox.py`
- Module: `_ops/coding_sandbox/`
- Bug fix: `_ops/identity/capability_token.py` (lines 258-313)
- Prior scan: `06-EVIDENCE/EQUIP-SCAN-WAVE-C-2026-08-16.md`

---

## Recommended Next Step

G5 (Infrastructure) should integrate the coding_sandbox with the TaskOrchestrator
for end-to-end task-based coding workflows. The sandbox currently creates worktrees
independently — G5 could wire this into the task lifecycle so that coding tasks
are automatically isolated. The `protected_paths.py` definitions should also be
reviewed against `_PROJECT_INSTRUCTIONS.md` for completeness.
