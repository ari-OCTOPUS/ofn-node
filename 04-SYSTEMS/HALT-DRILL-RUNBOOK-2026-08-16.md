---
type: runbook
status: active
created: 2026-08-16
updated: 2026-08-23
created_by: agent
tags: [octopus, tcb, halt]
sources:
  - "[[06-EVIDENCE/UPDATE-DEBUG-SWEEP-2026-08-16]]"
  - "[[_ops/owner-runbook/README-2026-08-16-FA]]"
---

# Live halt drill — runbook only (owner picks the window)

> **READINESS 2026-08-23:** master-halt, outbound-halt, halt-coverage,
> provider-effect-halt, launcher-halt, and halt-integration checks all passed.
> This validates the rehearsal floor, not the live outcome. No TCB file was
> mutated and no live process was halted. Current evidence:
> [[../06-EVIDENCE/UPDATE-DEBUG-SWEEP-2026-08-23]].

Do **not** execute without an owner-selected window. The old pid `27164` was a
2026-08-16 snapshot and is not a current precondition. Re-measure the daemon pid,
manifest enforcement, and signature immediately before the drill.

## Preconditions [A]

- `check_invariants` with enforce loaded: ok=True, tampered=False, digests_ok=True.
- No `HALT-ALL`, `STOP-ORGANISM`, `4d_system/outputs/daemon.stop`.
- Owner at keyboard. Telegram quiet hours respected if possible (`OCTOPUS_QUIET_FROM=23`).

## Drill A — benign TCB touch

1. Record `git rev-parse HEAD` and `python -c "from brain.guardrails import check_invariants; ..."` (enforce on).
2. Benign edit: append a single blank line to **one** file in `CODE_TCB_FILES` (prefer a leaf such as `4d_system/llm/langchain_models.py` — still TCB). Do not edit `trust-boundary.json` itself.
3. Expect within one `_job_guard` cycle (`guard` is in `_MODE_CYCLE`, tick 30s → worst ~7 min): `tcb.tampered=True`, `mismatches` contains the relative path, `inv.ok=False`, `_job_guard` returns `halt=True`, daemon loop breaks, `daemon_state.halted_at` set, digest queued. Hash mismatch is the log.
4. `_ops` five limbs should **keep beating** (TCB halt is 4d daemon, not STOP-ORGANISM).

## Recovery (allowed path)

1. `git checkout -- <touched-tcb-file>` from HEAD (restore digest; **no re-sign** if the file matches the signed manifest again).
2. Confirm `check_invariants` ok=True / tampered=False.
3. Restart daemon **only** via a flags-complete wrapper (`setlocal` + `call OCTOPUS-flags.cmd`). Do not inherit a shell that has `SELF_CODE_ENABLED=1`.
4. Probe pid, `enforcement=True`, `last_tick` advancing, `proposals_this_run` still 0 unless owner wants propose-on.

Rollback proof: if checkout does not restore digest, **stop** — do not re-sign in the drill window; restore from the last signed tree and page the owner.

## Drill B — paired kill-partition (independent)

These switches do **not** substitute for each other [A exists() this sweep]:

| partition | file | what it stops |
|---|---|---|
| organism | `_ops/STOP-ORGANISM` | metabolic loop / RUN-ORGANISM |
| cortex | `_ops/STOP-CORTEX` | cortex watchdog revive |
| center | `_ops/STOP-TG-CENTER` | telegram center |
| 4d daemon | `4d_system/outputs/daemon.stop` | `brain.daemon` loop |
| code autonomy `_ops` | `_ops/STOP-CODE-AUTONOMY` | already present; not read by 4d daemon |
| observatory | `_ops/observatory/data/kill.switch` | observatory |
| global | `_ops/HALT-ALL` or `04 - Architect System/STOP` | watchdogs refuse revive |

Exercise: create `daemon.stop` only → daemon exits, beat on :8771 continues. Then clear it and recover via flags wrapper. Separately, `STOP-ORGANISM` must not be required to halt 4d, and vice versa.

## Out of scope

- Do not flip `CORTEX_HYPOTHESIS` or `OCTOPUS_TCB_MANIFEST_ENFORCE`.
- Do not disable the five-limb watchdogs for this drill.
- Kernel `integrity_ok=false` in `daemon_state` is a separate review item; do not “fix forward” during the drill.
