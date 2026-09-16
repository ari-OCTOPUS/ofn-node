# OCTOPUS AUDIT -- PHASE 8: IMPLEMENTATION RULES

**Date:** 2026-07-08
**Phase:** 8 of 9 -- Implementation Rules & Invariants
**Status:** Final
**Classification:** INTERNAL -- Engineering Reference

---

## Purpose

This phase codifies every hard rule the Octopus organism must obey. These are
non-negotiable invariants derived from ORGANISM-SPEC.md (I1-I10), plus
additional rules discovered during the nine-phase audit.  Any violation is
a system-level defect.

---

## Section A -- Safety Invariants (ORGANISM-SPEC I1-I10)

### I1. Append-Only Ledger

- No `DELETE`, no in-place edit of any epoch file, state file, or log entry.
- Corrections use a new append with `correction_of: <uuid>`.
- Violation: any code path that truncates or overwrites a ledger file.

### I2. Single Enforcer Per Domain

- **Money gate:** one function, one code path -- `governor.py`.
- **Capability gate:** one function, one code path -- `governor.py`.
- **Approval channel:** one function, one code path -- `telegram.py`.
- No second code path may approve spend, grant capability, or accept a proposal.

### I3. Fail-Closed

- Denial is the default state.
- Approval requires an explicit positive action (human button press, explicit
  `accept()` call).
- Never auto-approve, auto-merge, or auto-settle.
- On ambiguity or error, the safe answer is NO.

### I4. Numbers from File

- All monetary thresholds, limits, and budgets come from `budgets.yaml` or
  from the live state file -- never hardcoded in source.
- The only exception is zero (0) used as "unset / no budget" sentinel.
- Every function that needs a number MUST read it at call time from the
  canonical source.

### I5. Dual-Lock Live

- Any action that moves real money requires TWO independent confirmations:
  1. **Attribution lock** -- `attribution.propose()` with full trace.
  2. **Human approval** -- Telegram message with explicit accept/reject buttons.
- Neither lock alone is sufficient.

### I6. budgets.yaml Read-Only

- Production code (`organism.py`, any organ) MUST treat `budgets.yaml` as
  read-only.
- Only a human (or a human-initiated script) may edit this file.
- No code path may write, rename, or delete `budgets.yaml`.

### I7. Human-Only Acceptance

- No auto-merge of proposals.
- No auto-settle of financial transactions.
- No bot or background process may issue the final "accept" action.
- The human (owner/PS1) is the sole authority for acceptance.

### I8. Anti-Cancer

- Unbounded growth in any dimension triggers an alarm:
  - Epoch files exceeding 90 in count.
  - Telemetry payload exceeding size budget.
  - Log files exceeding rotation threshold.
  - Any subsystem spawning indefinite sub-processes.
- Growth alarms route to Telegram as high-priority alerts.

### I9. Secret Hygiene

- `.env` files are NEVER committed to git.
- `.gitignore` and `.agentignore` MUST include `.env`, `*.env`, `secrets/`.
- Tokens and secrets are masked in all logs (first 4 chars visible, rest
  replaced with `****`).
- Secrets loaded via `os.environ` only -- never stored in JSON state files.

### I10. Anti-Injection

- No `eval()`, `exec()`, `compile()`, `__import__` from user input.
- No dynamic code loading from external sources.
- No user-supplied strings in file paths without sanitization.
- All external input is treated as untrusted and validated before use.

---

## Section B -- New Rules Discovered During Audit

### R11. Beat Function Pattern

Every organ's beat function MUST follow this exact structure:

```
def beat(ctx: Context) -> None:
    flag = check_flag()           # 1. Check kill-flag first
    if flag:
        return                     # 2. STOP check -- exit immediately
    cadence = divisor()           # 3. Cadence divisor (skip if not time)
    if not cadence_due():
        return
    try:
        do_work(ctx)               # 4. Actual work in try/except
    except Exception as e:
        log_error(e)               # 5. Catch everything, log, continue
    return None                    # 6. Always return None (fail-soft)
```

**Invariant:** A beat function MUST NEVER kill the tick.  A failing organ
does not crash the organism.

### R12. New Organ Checklist

Every new organ added to the organism MUST include all three:

| Item | Requirement | Verification |
|------|-------------|--------------|
| (a) Wiring factory function | Registered in `wiring.py` | `wiring.py` contains factory entry |
| (b) Dashboard page | HTML page in `dashboard/` | Page renders in dashboard index |
| (c) Test file | `tests/test_<organ>.py` | All tests green in CI |

An organ missing any of these is incomplete and must not be merged.

### R13. Epoch Rotation Mandatory

- Maximum 90 epoch files retained in the epoch directory.
- On each tick, if file count > 90, the oldest file is deleted.
- Deletion is the ONLY exception to I1 (append-only), explicitly
  sanctioned for rotation.
- Rotation event is logged with the UUID of the deleted epoch.

### R14. Structured Logging

- ALL events MUST go through `octopus_logger.py`.
- Output format: JSON Lines (JSONL), one object per line.
- Schema version: `v1` (field `_schema: "v1"` in every log entry).
- Required fields: `timestamp`, `organ`, `event`, `level`, `trace_id`.
- Trace propagation: every downstream call receives and forwards the
  parent `trace_id`.
- No `print()` statements in production code.  No ad-hoc logging.

### R15. No Module Import Without Wiring

- Every subsystem MUST be instantiated through its factory function in
  `wiring.py`.
- `organism.py` MUST NOT contain direct `import` of any organ module.
- The wiring layer is the single point of dependency management.
- Violation: any `from <organ_module> import ...` inside `organism.py`.

### R16. Telegram T-8 Contract

The Telegram organ must obey this strict ordering:

1. **Quarantine first** -- receive message, validate structure, quarantine
   suspicious input (rate-limiting, unknown command, malformed payload).
2. **Dispatch second** -- only after quarantine passes, route to the
   appropriate handler.
3. **Fail-soft on send** -- if `sendMessage` or any Telegram API call fails,
   log the error and return None.  Never retry more than once, never block
   the tick.

### R17. Dashboard Writes Only Control-Files

The dashboard web interface may write ONLY these files:

| File | Purpose |
|------|---------|
| `OCTOPUS.env` | Environment variable updates |
| `STOP-ORGANISM` | Graceful shutdown signal |
| `RESTART-REQUESTED` | Restart signal |

The dashboard MUST NOT directly modify state files, epoch files, or budgets.

### R18. Panel Writes Only Propose-Only

- Dashboard panels (human-facing UI) MUST call `attribution.propose()` only.
- They MUST NEVER call `attribution.settle()`.
- Settlement is reserved for the dual-lock path (attribution + human approval).

### R19. State File Atomicity

- All state file writes MUST use `LockedJSON` from `opslib`.
- File locking: `O_EXCL` (exclusive create) for new files, stale-lock
  detection for existing files.
- No raw `open()` + `write()` for state files.
- Concurrent writes to the same state file MUST be serialized through the
  lock mechanism.

### R20. Watchdog Propose-Only

- The watchdog organ detects organism death.
- On detection, it proposes revival (writes a proposal, not a command).
- Execution of revival is the responsibility of the owner (PS1) or the
  approved restart mechanism.
- The watchdog MUST NOT directly kill or restart the process.

---

## Section C -- Coding Standards

### C1. stdlib-Only Production Code

- All production code (organism, organs, dashboard, wiring) MUST use only
  Python standard library modules.
- No `pip` dependencies in production.
- The only exception: test files may use `pytest` or `requests-mock` for
  testing purposes.

### C2. Language Convention

- **Persian (Farsi)** for natural-language comments where the author's
  natural expression is Persian.
- **English** for all code symbols: function names, variable names, class
  names, file names.
- Docstrings: English (for tooling compatibility), inline comments: either.

### C3. Vault-Native Epistemic Tags

All design documents and architectural notes use these tags:

| Tag | Meaning |
|-----|---------|
| `[EST]` | Established fact -- verified in code or documentation |
| `[THM]` | Theorem -- derived from established facts |
| `[HYP]` | Hypothesis -- plausible but unverified |
| `[CHOICE]` | Design decision -- could have been different |
| `[OPEN]` | Open question -- needs owner input |

### C4. Function Contract

Every function MUST have:

1. **Type hints** on all parameters and return value.
2. **Docstring** with at minimum: one-line summary, Parameters section,
   Returns section (if not None), Raises section (if applicable).

```python
def example(ctx: Context, amount: float) -> bool:
    """Check if amount is within budget.

    Args:
        ctx: The organism context containing budget state.
        amount: The proposed spending amount.

    Returns:
        True if amount is within budget, False otherwise.
    """
    ...
```

### C5. Testing Rules

- Tests MUST cost $0 to run (no API calls, no paid services).
- HTTP dependencies: injectable mocks (pass base_url as parameter, default
  to test stub).
- No network calls in test suites.
- Test isolation: each test creates and cleans up its own state files.
- Coverage target: every beat function, every wiring factory, every
  propose/settle path.

---

## Section D -- Enforcement Mechanism

### D1. Pre-Merge Checklist

Before any code is merged into the organism:

- [ ] All 20 rules (I1-I10, R11-R20) checked manually or via lint.
- [ ] New organ checklist (R12) verified for any new modules.
- [ ] `pytest tests/` -- all green.
- [ ] No hardcoded numbers (I4) -- grep for numeric literals > 0.
- [ ] No `eval`/`exec` (I10) -- grep for dangerous builtins.
- [ ] No direct imports in `organism.py` (R15) -- verify wiring-only.

### D2. CI Gate

- `pytest` must pass with 0 failures.
- Any test that requires network access is a test bug.
- Any production code that imports a non-stdlib module is a merge block.

### D3. Runtime Guard

- The organism's boot sequence checks for:
  - Existence of `budgets.yaml` (fail-closed if missing).
  - Absence of `.env` in tracked files (I9).
  - All organs registered in wiring.py (R15).
- Boot failures are logged and the organism does not start.

---

## Section E -- Rule Index

| ID | Rule | Source | Severity if Violated |
|----|------|--------|---------------------|
| I1 | Append-only ledger | ORGANISM-SPEC | CRIT |
| I2 | Single enforcer per domain | ORGANISM-SPEC | CRIT |
| I3 | Fail-closed | ORGANISM-SPEC | CRIT |
| I4 | Numbers from file | ORGANISM-SPEC | HIGH |
| I5 | Dual-lock live | ORGANISM-SPEC | CRIT |
| I6 | budgets.yaml read-only | ORGANISM-SPEC | HIGH |
| I7 | Human-only acceptance | ORGANISM-SPEC | CRIT |
| I8 | Anti-cancer | ORGANISM-SPEC | HIGH |
| I9 | Secret hygiene | ORGANISM-SPEC | CRIT |
| I10 | Anti-injection | ORGANISM-SPEC | CRIT |
| R11 | Beat function pattern | Audit discovery | HIGH |
| R12 | New organ checklist | Audit discovery | MED |
| R13 | Epoch rotation | Audit discovery | HIGH |
| R14 | Structured logging | Audit discovery | MED |
| R15 | No import without wiring | Audit discovery | HIGH |
| R16 | Telegram T-8 contract | Audit discovery | HIGH |
| R17 | Dashboard writes only control-files | Audit discovery | MED |
| R18 | Panel writes only propose-only | Audit discovery | HIGH |
| R19 | State file atomicity | Audit discovery | HIGH |
| R20 | Watchdog propose-only | Audit discovery | MED |

---

*End of Phase 8 -- Implementation Rules*
