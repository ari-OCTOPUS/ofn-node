# Octopus Operations Runbook — Troubleshooting Playbook

**Scope:** `_ops/` metabolism layer, budget gate, leg workers, organism state.  
**Rules:** additive-only, read-only scripts, stdlib-only, no external dependencies, $0 offline-first.  
**Invariant anchors:** I1 (append-only ledger), I2 (budget_gate single enforcer), I3 (fail-closed → FREEZE on divergence), I6 (no hardcoded numbers, read from `budgets.yaml`).

---

## Quick Reference: Exit Codes

| Tool | Exit 0 | Exit 1 | Exit 2 |
|------|--------|--------|--------|
| `health_check.py` | All green | Warning | Error |
| `budget_monitor.py` | Within limits | Divergence/spike | Over-cap |
| `flag_monitor.py` | Consistent | Unexpected combo | HALT-ALL / FREEZE |
| `leg_monitor.py` | All clean | Missing organs | Structural violation |

Run all: `RUN-HEALTH-CHECK.bat` (Windows) or `python3 health_check.py && python3 budget_monitor.py && ...`.

---

## Symptom Tree

### 1. ORGANISM-STATE shows `halted`, `frozen`, or `stop_organism`

**Diagnosis:**
```bash
python _ops/observability/health_check.py
```
Check `checks.flags` and `checks.organism_state`.

**Actions:**

| Condition | Action | Verify |
|-----------|--------|--------|
| `HALT-ALL` exists | Do NOT restart. Read `HALT-ALL` content. Resolve root cause. Delete `HALT-ALL` only after owner review. | `health_check.py` → flags level = ok |
| `FREEZE.flag` exists | Read `FREEZE.flag` for reason. Resolve divergence/corruption. Delete after manual review. | `budget_monitor.py` shows no divergence |
| `STOP-ORGANISM` exists | Review `organ-gate-log.jsonl` tail. If intentional, leave it. If accidental, delete after owner review. | organism_state → stop_organism = false |
| `STOP-METABOLIC` exists | Metabolism halted; loops may still run. Review telemetry. Delete after owner review. | flags check → ok |
| `STOP-ARCHITECT` exists | Architect-level stop. All downstream stops. Review `04 - Architect System/STOP`. | master_halted = None |

**Invariant:** Only the owner deletes STOP/FREEZE/HALT files. Scripts are read-only.

---

### 2. `budget_monitor.py` reports `organ_spending = err`

**Symptom:** `PROJECT_F: monthly 35.2 AUD > cap 20.0` or `GLOBAL: total 45 AUD > cap 30`.

**Diagnosis:**
1. Read `_ops/budget/organ-state.json`.
2. Compare with `budgets.yaml` `global.cap_monthly` and per-project caps/floors.
3. Check `organ-gate-log.jsonl` for recent `reserve` entries with `allow: true` that pushed the cap.

**Actions:**
- If telemetry is lower than billed → possible bug in `settle` (double-counting).  
  **Do not FREEZE manually.** The `budget_monitor.py` proposes; owner decides.  
  File a diff in `_ops/budget/budgets-proposed-diff.md` if cap adjustment is needed.
- If the organ is genuinely over-cap → `organ_gate` should have already denied.  
  If it didn't, this is a **gate bypass** → file a CONFLICT note to `AGENT_QUESTIONS.md`.

**Verification:**
```bash
python _ops/budget/organ_gate.py  # prints JSON status
```
Expected: `rows[organ].spent_month_aud <= cap_monthly_aud`.

---

### 3. `budget_monitor.py` reports `telemetry_divergence = warn`

**Symptom:** `telemetry divergence 24% (genome 12.3 vs organ 9.8 USD)`.

**Root causes:**
1. **Unit mismatch:** One source records USD, the other AUD, and FX rate drifted.  
   Check `fx_aud_per_usd` in `organ_gate.status()`.
2. **Missing ledger entries:** Genome ledger METRIC events lost (write failure).  
   Check `ledger-fallback.jsonl` size in `health_check.py`.
3. **Unmapped business:** `telemetry.py` maps business to organ. If a new business appears, it goes to `UNMAPPED`.  
   Check `telemetry.py` `ORGAN_MAP`.

**Actions:**
- Verify FX rate in `budgets.yaml` matches pinned rate in `opslib.fx_aud_per_usd()`.
- If `ledger-fallback.jsonl` is growing, ledger append is failing. Check `genome-system/ledger/ledger.jsonl` permissions.
- If unmapped, add mapping to `telemetry.py` ORGAN_MAP (requires owner approval).

**Verification:**
```bash
python _ops/observability/budget_monitor.py
# genome_total_usd and organ_total_usd should converge within 10% after fix.
```

---

### 4. `health_check.py` reports `germline = err`

**Symptom:** `lag 48h >= 26h` or `no germline artifacts reachable`.

**Diagnosis:**
1. Check `E:\germline\` exists and contains `hourly-latest.bundle` or `vault-*.bundle`.
2. Check `GITWRITE-FAILED.flag` in `_ops/backup/`.

**Actions:**
- If off-box disk is offline → mount/check disk. No script will fix this.
- If `GITWRITE-FAILED.flag` exists → read it. It contains the explicit failure reason.  
  Resolve git-write issue (network, credentials, disk space). Then delete the flag.
- If no bundles exist but backups should run → verify the backup task is scheduled.

**Verification:**
```bash
python _ops/observability/health_check.py
# germline.lag_h should be < 2.0
```

---

### 5. `health_check.py` reports `budgets_yaml = err`

**Symptom:** `budgets.yaml unreadable or missing global/projects`.

**Impact:** `organ_gate` will FREEZE on next reserve (fail-closed). This is a **critical path**.

**Diagnosis:**
1. Check file exists: `_ops/budget/budgets.yaml`.
2. Check content contains `global:` and `projects:`.
3. Check file permissions (readable by runner).

**Actions:**
- If file is missing → restore from germline backup (`E:\germline\vault-*.bundle`).
- If file is corrupted → fix syntax, or restore from last known good.
- If file is locked by another process → wait or terminate the lock holder.

**Verification:**
```bash
python _ops/observability/health_check.py
# budgets_yaml.readable = true
```

---

### 6. `health_check.py` reports `organ_state = err`

**Symptom:** `organ-state.json unreadable` or `top-level is not dict`.

**Diagnosis:**
1. Check if `.lock` file is stale (>60s). If yes, the previous process crashed holding the lock.
2. Check JSON validity.

**Actions:**
- If stale lock exists → delete `organ-state.json.lock` (safe; lock is O_EXCL style).
- If JSON is corrupted → reconstruct from `organ-gate-log.jsonl` by replaying `reserve`/`settle`/`release` entries, or restore from backup.

**Verification:**
```bash
python _ops/observability/health_check.py
# organ_state.level = ok
```

---

### 7. `flag_monitor.py` reports `SELF-IMPROVE-AUTO without GOVERNOR-LLM`

**Symptom:** Autonomous self-improvement loop lacks governance oversight.

**Impact:** The loop may generate proposals without LLM-governor review. This is a **governance gap**, not a hard failure.

**Actions:**
- Either add `ACTIVATION-GOVERNOR-LLM.flag` (owner decision), or remove `ACTIVATION-SELF-IMPROVE-AUTO.flag`.
- Do not leave the system in this state overnight.

**Verification:**
```bash
python _ops/observability/flag_monitor.py
# activation_flags.issues = empty
```

---

### 8. `leg_monitor.py` reports `wildcard read_allowlist detected`

**Symptom:** A leg file contains `read_allowlist="*"` or similar.

**Impact:** Violates INV-17 (isolation model). A leg with wildcard can read any note, including PII.

**Actions:**
- **Do not run the leg.** Edit the file to specify exact note IDs.
- Re-verify with `leg_monitor.py` before restarting.

**Verification:**
```bash
python _ops/observability/leg_monitor.py
# leg_files.level = ok
```

---

### 9. `leg_monitor.py` reports `non-zero spawn`

**Symptom:** A leg file contains `spawn=1` or similar.

**Impact:** A leg could spawn subprocesses, violating worker isolation.

**Actions:**
- Set `spawn=0` in the leg's TaskPacket construction.
- Re-verify.

---

### 10. `budget_monitor.py` reports `recent_denials = warn`

**Symptom:** >5 denials in last 30 organ_gate log entries.

**Root causes:**
1. Organ over-cap (legitimate).
2. `budget_gate` deny (global cap reached).
3. Unknown organ (leg not mapped in `budgets.yaml`).
4. `organ-state-lock-busy` (concurrent access).

**Actions:**
- Check `denial_reasons` in `budget_monitor.py` output.
- If `organ-monthly` → wait or raise cap via `budgets-proposed-diff.md`.
- If `budget_gate` → check global spend in `budget-state.json`.
- If `unknown-organ` → add organ to `budgets.yaml` or fix leg's `packet.organ`.
- If `organ-state-lock-busy` → check for stuck processes, delete stale `.lock`.

---

### 11. Ledger append failures (`ledger_fallback` growing)

**Symptom:** `health_check.py` shows `ledger_fallback.size_bytes > 1024`.

**Diagnosis:** `opslib.ledger_note()` writes to `_ops/state/ledger-fallback.jsonl` when `genome_ledger().append()` fails.

**Actions:**
1. Check `07 - Knowledge/genome-system/ledger/ledger.jsonl` exists and is writable.
2. Check disk space.
3. If temporary, replay `ledger-fallback.jsonl` into the main ledger after fixing the issue.

**Verification:**
```bash
python _ops/observability/health_check.py
# ledger_fallback.level = ok
```

---

### 12. Dashboard (port 8770) unreachable but organism is running

**Diagnosis:**
1. `dashboard/server.py` is a separate process from `organism.py`.
2. Check if port 8770 is in use: `netstat -ano | findstr 8770`.
3. Check `_ops/state/ORGANISM-STATE.json` for `exited` field.

**Actions:**
- If dashboard crashed → restart `RUN-DASHBOARD.bat`.
- If organism is stopped (`STOP-ORGANISM` exists) → dashboard should also stop. Do not force-start.

---

## Decision Tree (ASCII)

```
START
  |
  +-- System stopped? (STOP-ORGANISM / HALT-ALL / FREEZE)
  |     |
  |     +-- YES → Read flag content → Resolve → Delete flag (owner only) → Verify
  |     |
  |     +-- NO  → Continue
  |
  +-- Run health_check.py
        |
        +-- budgets_yaml = err? → Restore from backup → Verify
        |
        +-- organ_state = err? → Check lock → Fix JSON → Verify
        |
        +-- germline = err? → Check off-box disk / GITWRITE-FAILED → Verify
        |
        +-- ledger_fallback = warn? → Check ledger path / disk → Verify
        |
        +-- All green? → Run budget_monitor.py
              |
              +-- organ_spending = err? → Check caps → Propose diff or wait → Verify
              |
              +-- telemetry_divergence = warn? → Check FX / unmapped / ledger → Verify
              |
              +-- All green? → Run flag_monitor.py
                    |
                    +-- issues? → Fix activation flags → Verify
                    |
                    +-- All green? → Run leg_monitor.py
                          |
                          +-- issues? → Fix isolation / secrets / spawn → Verify
                          |
                          +-- All green? → SYSTEM HEALTHY
```

---

## File Reference

| File | Purpose | Safe to Read | Safe to Write |
|------|---------|--------------|---------------|
| `_ops/budget/budgets.yaml` | Single Source of Truth | ✅ Yes | ❌ No (propose diff only) |
| `_ops/budget/organ-state.json` | Per-organ spending | ✅ Yes | ⚠️ Only via `LockedJson` in gate |
| `_ops/budget/budget-state.json` | Global budget gate state | ✅ Yes | ⚠️ Only via `budget_gate` |
| `_ops/budget/organ-gate-log.jsonl` | Append-only audit log | ✅ Yes | ❌ No (append only via gate) |
| `_ops/state/ORGANISM-STATE.json` | Organism lifecycle | ✅ Yes | ⚠️ Only via organism lifecycle |
| `_ops/state/ledger-fallback.jsonl` | Failed ledger writes | ✅ Yes | ❌ No (internal only) |
| `_ops/budget/FREEZE.flag` | Divergence lock | ✅ Yes | ❌ No (owner only) |
| `_ops/HALT-ALL` | Panic stop | ✅ Yes | ❌ No (owner only) |
| `_ops/STOP-ORGANISM` | Organism stop | ✅ Yes | ❌ No (owner only) |
| `_ops/backup/GITWRITE-FAILED.flag` | Backup failure | ✅ Yes | ❌ No (backup process only) |
| `07 - Knowledge/genome-system/ledger/ledger.jsonl` | Genome ledger | ✅ Yes | ❌ No (ledger class only) |
| `_ops/legs/*.py` | Worker definitions | ✅ Yes | ⚠️ Review before any change |
| `_ops/budget/opslib.py` | Common library | ✅ Yes | ❌ **DO NOT TOUCH** (audit in progress) |
| `_ops/budget/organ_gate.py` | Per-organ gate | ✅ Yes | ❌ **DO NOT TOUCH** (audit in progress) |
| `_ops/budget/telemetry.py` | Telemetry reader | ✅ Yes | ❌ **DO NOT TOUCH** (audit in progress) |
| `_ops/budget/reconcile.py` | Reconciliation | ✅ Yes | ❌ **DO NOT TOUCH** (audit in progress) |
| `_ops/legs/leg.py` | Leg framework | ✅ Yes | ❌ **DO NOT TOUCH** (audit in progress) |
| `_ops/germline.py` | Germline backup | ✅ Yes | ❌ **DO NOT TOUCH** (audit in progress) |
| `_ops/budget/opslib.py` | Common library | ✅ Yes | ❌ **DO NOT TOUCH** (audit in progress) |

---

## Emergency Contacts / Escalation

1. **System frozen / HALT-ALL** → Owner review. No automated restart.
2. **Budget over-cap with no deny** → File CONFLICT to `AGENT_QUESTIONS.md`.
3. **PII leak suspicion** → HALT-ALL immediately. Review leg `read_allowlist`.
4. **Ledger corruption** → Do not write. Preserve `ledger.jsonl` and `ledger-fallback.jsonl`. Owner replay.

---

*Runbook version: 2026-07-21 (additive, stdlib-only, read-only scripts).*
