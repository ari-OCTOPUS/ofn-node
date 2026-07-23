# OCTOPUS Phase-0 — OWNER DEPLOYMENT PACKET (2026-07-23)

> This packet is a **proposal for owner review only**. Approving it does not authorize any
> agent to merge, migrate a live DB, change flags, restart a service, send a message, or make
> a paid/external call. Every live action below is done **by the owner**, in the order given,
> after you decide to proceed. Until then the live organism at `F:\backup` is untouched.

---

## 0. One-paragraph summary

The Phase-0 safety candidate is **complete and green**. On the isolated repository
`F:\octopus-phase0-isolated` (branch `blocker-fixes-2026-07-22`, HEAD **`1110b94`**), the exact
money-effect authorization gate (C1–C7), the global-halt boundary (D1–D5), and the constitutional
reachability invariants (PRE-0) are implemented and verified. The full manifest-driven sandbox
suite passes **263/263** with the barrier proving **0 attempted live writes and 0 external
network attempts**. A 14-agent adversarial red team produced 4 confirmed findings (1 P1, 3 P2),
**all fixed and re-verified**. The live tree at `F:\backup` was never modified (master still at
`05d2b5a`; `_ops/chrono.py` last written 2026-07-21, before this work). **Nothing is deployed;
the candidate stops here, at your boundary.**

---

## 1. Exact repository / branch / HEAD

| item | value |
|---|---|
| candidate repo | `F:\octopus-phase0-isolated` (standalone clone, shares history with live) |
| branch | `blocker-fixes-2026-07-22` |
| final HEAD | **`1110b94`** (`redteam-fixes-p1-p2`) |
| live baseline | `05d2b5a` on `F:\backup` master — confirmed common ancestor of HEAD |
| halt sub-branch | `phase0-A-halt` (a git worktree of the same repo) merged in at `8f417f3` |

The live master `05d2b5a` **is an ancestor** of the candidate HEAD, so the candidate is a clean
forward integration of the live baseline plus the Phase-0 commits.

---

## 2. Commit range and diff summary

Range **`05d2b5a..1110b94`** = 23 commits. The Phase-0 money/safety/halt slices:

| commit | slice |
|---|---|
| `32db70b`→`1f3ebae` | C1 schema-migration framework · C2 binding columns · C3 idempotency index |
| `82fd1f6` | C4 exact per-effect money authorization |
| `9f9a6dd` | C4.1 close the E4 id-only bypass |
| `7dfe991` | **C5 CAS execution** (migration v4, claim/commit/fail, TOCTOU closed) |
| `c28a810` | **C6 receipt/reconciliation** (stale sweeps, reconcile_effect, redrive) |
| `8f417f3` | merge `phase0-A-halt` (D1 `ce24058` outbound halt gate, D2 `8b880c8` halt coverage) |
| `bd908f3` | **C7 money caller-migration** (Telegram approve → exact C4 binding via card snapshot) |
| `07859f5` | **D3/D4/D5** global-halt completion (providers, launchers, virtual-time integration) |
| `fdfb58e` | **PRE-0** ten invariants via real entry points |
| `1110b94` | **red-team fixes** (1 P1 + 3 P2) |

Code diff (excluding phase-0 docs): **42 files, +3421 / −100**. The money/safety core:
`_ops/chrono.py` +695/−33, `_ops/budget/approval_channel.py` +47/−? (caller migration + owner-gate).

---

## 3. Full test results

**Manifest-driven sandbox suite** (`test-authority/run_sandbox_suite.py --full`, hermetic,
per-file subprocess, barrier-backstopped):

```
manifest_total: 263    PASS: 263    FAIL: 0
barrier: attempted_live_writes=0 · external_network_attempts=0 · barrier_install_failures=0
         child_processes_with_evidence=279
report: OCTOPUS-PRIME/phase-0/test-authority/FULL-SANDBOX-TEST-REPORT.json
```

Targeted money/safety proofs (all green):

| area | test | count |
|---|---|---|
| C5 CAS | `test_c5_cas_execution` | 33/33 |
| C6 reconcile | `test_c6_receipt_reconciliation` | 32/32 |
| C4 / C4.1 | `test_c4_exact_authorization` / `test_c41_e4_id_only` | 18 + 10 |
| C7 money routing | `test_telegram_channel`, `test_telegram_rfc_router`, `test_lead_effect_gate` | pass unmodified |
| D3 provider/effect halt | `test_d3_provider_effect_halt` | all |
| D4 launcher halt | `test_d4_launcher_halt` | all |
| D5 virtual-time halt | `test_d5_halt_integration` | all |
| PRE-0 real entry | `test_pre0_real_entry` | 27/27 |
| owner-gate panic | `test_panic_command` | 6/6 |

---

## 4. C / D / PRE-0 verdicts

**C (exact effect authorization) — PASS.** Money (`pay`) is releasable ONLY via `release_effect`
with the full binding (effect_id + content_hash + action_kind + target_ref + single-use
approval_id + expiry + human ledger ref). Batch release is an allowlist `{send,publish,sync}` that
structurally excludes money. Execution is a CAS state machine
(`pending→releasable→EXECUTING→settled`) — two executors yield one winner, a stale/wrong
execution_id can never finalize, and there is no direct `pending→settled`. Ambiguous outcomes
(halt mid-flight, lost worker) go to `RECONCILE_REQUIRED`, never a fabricated terminal state.
The production Telegram approval path now carries the exact binding (C7), so an owner approval
end-to-end releases money via C4 — proven by the telegram tests passing unmodified.

**D (global halt) — PASS.** `HALT-ALL` and architect `STOP` refuse every effector transition
(release/execute/settle/reconcile/redrive), every provider call (`model_router`), the money
writeback (`ps_writeback`), and every launcher boot (all 6 `.bat` guards abort before launch).
`complete_execution`/`fail_execution` under halt divert an in-flight effect to
`RECONCILE_REQUIRED` (honest — the external effect may have happened). The D5 virtual-time
scenario proves the settled-count is bit-identical across a halted window and nothing duplicates.

**PRE-0 (constitutional reachability) — PASS.** Ten invariants proven through real entry points:
AGI-identity claims stay ADVISORY through the real Memory Gate; hostile prompt/retrieved content
is powerless against the halt and the effect binding; code-autonomy cannot target the
constitution/verifier/guards; broad and id-only approvals release zero money; the watchdog yields
to every STOP; and `HALT-ALL` deletion exists only inside `opslib.clear_halt_all`, reachable only
from the two owner `/resume` surfaces — now additionally owner-gated by `from_id` (red-team P1).

---

## 5. Red-team result (14 agents, SEC / TEST / MIG / GOV)

10 raw findings → **4 confirmed, 3 refuted, 3 suspect.** All 4 confirmed are **fixed** at
`1110b94`; no P0.

| # | lens | sev | finding | resolution |
|---|---|---|---|---|
| 1 | GOV | **P1** | `/panic` `/resume` (clears HALT-ALL) `/stop` authorized by `chat_id∈allowlist` (incl. group chats) — any allowed-group member could clear the owner panic boundary | **FIXED**: `handle_command` owner-gates these on `from_id==owner`; `poll_once` threads the real `from_id`. Tests added. |
| 2 | MIG | P2 | `fail_execution` was the only effector transition without a halt gate — a stale worker under halt could terminalize an in-flight money effect to `FAILED_SAFE` (asserting "no money moved"), skipping reconciliation | **FIXED**: under halt it now diverts `EXECUTING→RECONCILE_REQUIRED` like `complete_execution`. Test added. |
| 3 | TEST | P2 | `test_d4_launcher_halt` verified only the guard's line *position*, not that it *aborts* — a log-and-fall-through guard would pass | **FIXED**: now asserts the action clause is `goto`/`exit`. |
| 4 | GOV | P2 | `AGI-HYPOTHESIS-PROTOCOL.md` claimed a `check_generated_files` control that does not exist in code (dead-policy / identity-leakage doc) | **FIXED**: reworded as `[SPEC, not built]`, pointed to the real ADVISORY-always Memory Gate proof. |

**Refuted (3):** `_do_approve` unconditional Approval (money moves only via the separate exact
lane — the Approval attestation has no live money consumer and `capability_gate` is closed in the
paper phase); `_E4_MONEY_KINDS` denylist (the only money kind that can be requested is `pay`, and
it is fully guarded); code-autonomy self-targetable (money/budget guards are outside the
allowlist and test-pinned; a weakening self-edit turns the shadow suite red).

**Suspect (3, recorded, not blockers):** capability_gate/money_gate have no halt check — a
defense-in-depth asymmetry, but those gates are closed in the paper phase (no `LIVE-ENABLED`
flag) and the money-moving lane (EffectorGate) refuses under halt independently. `test_d3`'s
"settle refuses under halt" is proven transitively via `begin_execution` rather than a direct
`settle` call. "Money never batches" is pinned by `test_c4` line 71 (the finding overstated the
gap). **Recommended follow-up (Phase-1A hardening, not Phase-0 blockers):** add a `master_halted()`
check to `capability_gate.require`/`money_gate.check` for defense-in-depth before those gates are
ever armed.

---

## 6. Live backup / restore evidence

- Restore drill (prior session, still valid): **459/459 files restored byte-identical, 0 hash
  mismatches** (`RESTORE-DRILL-REPORT.md`, manifest `SAFETY-BACKUP-MANIFEST.json`).
- Live tree untouched this session — **verified**: `F:\backup` master still `05d2b5a`;
  `F:\backup\_ops\chrono.py` last-written **2026-07-21** (before this work); its SHA-256 differs
  from the candidate (expected — the candidate carries C5/C6/D3), confirming no write occurred.
- No STOP/HALT flag set or cleared; no process restarted; no external effect issued this session.

---

## 7. DB migration preview (chrono.db v3 → v4)

The only schema change is **additive** and **owned by `ChronoDB._migrate` (transactional,
fail-closed)** — it runs automatically the first time the new `chrono.py` opens the live
`chrono.db`. It does **not** need a manual SQL step, but here is exactly what it does:

- `CHRONO_SCHEMA_TARGET` 3 → 4; step `_migrate_3_to_4` runs inside `BEGIN IMMEDIATE` (a failure
  rolls back and leaves `user_version=3` intact — proven by `test_c5` induced-failure case).
- Adds 6 nullable columns: `execution_id`, `execution_started_at`, `execution_finished_at`,
  `execution_worker_ref`, `external_receipt_ref`, `failure_reason`.
- Widens the `status` CHECK to add `EXECUTING`, `EXPIRED`, `FAILED_SAFE`, `RECONCILE_REQUIRED`.
- **Zero existing rows change status** (additive). The C3 UNIQUE idempotency index is recreated
  after the table rebuild (proven by `test_c5` — a silent idempotency loss would be a real bug;
  the test pins against it).
- Rollback: keep a copy of the live `chrono.db` before first boot of the new code; a v4 DB opened
  by the old (v3-target) code fails closed (`user_version=4 > target 3` → `ChronoSchemaError`), so
  a downgrade requires restoring the pre-migration DB copy (step in §9).

---

## 8. Temporary disarm requirement (before merge)

Per `PHASE-0-OWNER-APPROVAL-PACKET.md`, while merging keep the 6 live-effect flags disarmed so a
bug cannot touch money/apply during the transition (`OCTOPUS_WIRE_PS_WRITEBACK`,
`OCTOPUS_WIRE_POCKETSMITH`, `OCTOPUS_WIRE_APPLY_MERGE`, `OCTOPUS_WIRE_MERGE_APPLIES_KNOB`,
`OCTOPUS_WIRE_MISSION_RUNNER`, `OCTOPUS_WIRE_RUNNER_APPLY`). You edit `_ops/OCTOPUS-flags.cmd`
(`=1`→`=0`); the agent never touches it. Re-arm on your schedule after smoke tests pass.

---

## 9. Deployment sequence (owner-run, only if you approve)

```
T0  Final backup + state snapshot of F:\backup (esp. _ops/state/chrono.db, ledger.jsonl).
T1  Temporary disarm: set the 6 flags in _ops/OCTOPUS-flags.cmd to =0.
T2  Merge the exact candidate: git -C F:\backup merge --no-ff blocker-fixes-2026-07-22
    (a --no-ff merge gives you one explicit revert point).
T3  Copy the live chrono.db aside (chrono.db.pre-v4) — the migration rollback anchor.
T4  First boot: the new chrono.py auto-runs the v3→v4 migration (transactional, fail-closed).
T5  Smoke tests with external effects still OFF (flags disarmed): create a fake pay effect,
    verify it can ONLY settle via exact release_effect + begin/complete_execution with a receipt,
    and that /panic (as owner) refuses everything and a non-owner cannot clear it.
T6  A1 shadow: watch organ-gate-log + reconciliation_report for a quiet window; no real sends.
T7  Rollback on any red: restore chrono.db.pre-v4, git -C F:\backup reset --hard 05d2b5a
    (or revert the merge commit), re-arm nothing until diagnosed.
```

**Expected downtime:** one organism restart cycle (seconds); the migration is a fast additive
ALTER/rebuild on a small DB. **No first-window** PocketSmith writeback, autonomous apply, provider
activation, email, or real E4 effect.

---

## 10. Rollback commands (quick reference)

| to undo | command |
|---|---|
| the merge | `git -C "F:\backup" reset --hard 05d2b5a` (pre-merge) or `git -C "F:\backup" revert -m 1 <merge-sha>` |
| the migration | restore `chrono.db.pre-v4` over the live `chrono.db` |
| the candidate repo | it is standalone under `F:\octopus-phase0-isolated`; deleting it does not affect live |
| re-arm | restore `_ops/OCTOPUS-flags.cmd` from your backup |

---

## 11. Unresolved items carried forward (not Phase-0 blockers)

- **P1-adjacent hardening (recommended):** add `master_halted()` to `capability_gate.require` /
  `money_gate.check` before those gates are ever armed (defense-in-depth; the money-moving lane
  already refuses under halt).
- **LEAD-REV invoice:** `NEEDS_OWNER_REVIEW` — the invoice claims GST-registered while the owner
  GST verdict is unresolved (`VQ-ACC-005`). The system must not auto-send or tax-confirm it. This
  is your decision, made privately.
- **Provider routing (GLM):** deferred — a config-only DeepSeek→GLM switch cannot work for the
  direct `DeepSeekClient` callers; the safe path is MultiProviderClient → shadow → owner canary,
  after Phase-0.
- **propagation-lab vendoring:** deferred until after Phase-0 (copy-first, hash-compare vs
  `octopus-ramanujan`, pick one core).

---

## 12. Explicit owner decisions required

1. **Approve or decline the Phase-0 merge** into live `F:\backup` per §9.
2. If approving, confirm the **temporary disarm** of the 6 flags during the merge window.
3. Decide the **LEAD-REV GST / invoice** question (privately; do not have the agent infer it).
4. Confirm whether the **capability_gate/money_gate halt hardening** (§11) should be done as a
   small pre-merge slice or deferred to Phase-1A.

Until you decide, the agent does nothing further to the live system.
