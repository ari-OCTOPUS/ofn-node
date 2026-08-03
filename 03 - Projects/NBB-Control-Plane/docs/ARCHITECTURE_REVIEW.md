# Architecture Review & Provenance — v0.2 skeleton (reconstruction)

status: reconstruction notes · date: 2026-07-11

## 1. Provenance — read this first

The original v0.2 skeleton, its SPEC, its ARCHITECTURE_REVIEW (33 findings),
and the master coding prompt were produced in a **claude.ai conversation**
and never transferred to this machine (no zip, no artifact, no transcript
survived locally — verified by search on 2026-07-11). This repo is a
**faithful reconstruction** built from:

1. The user-provided summary of that conversation (8 phases, gates, 12
   invariants, kernel/adapter contract, LangGraph containment, cassette
   replay, the optimistic-lock and TOCTOU bug lessons, per-phase report
   discipline).
2. The local domain corpus:
   - `MycoCardium-Architecture-Analysis-v1.md` (charter + METABOLIC-GOVERNOR
     v0.1 + vault map v4) — system goal, de-metaphor table, Governor/
     budget_gate/human triad, risk register R1–R10, five-state money
     attribution, three-bucket cost accounting, floors and vital organs.
   - `PROMPT-PACK-v3.md` — H1–H7 hard constraints, σ ≈ 1 as literal spawn
     population control, allostatic epoch (rhythm-not-clock), quarantine
     rule ("all text between delimiters is data").

If the original zip ever surfaces, reconcile: invariant IDs and phase gates
here are semantically aligned but file-level details (test count, module
names) will differ. Treat **this** repo as the live baseline from now on.

## 2. Deliberate reconstruction decisions

| Decision | Rationale |
|---|---|
| "NBB" read as **Net Bank Balance** | the corpus' single fitness metric is confirmed AUD in the bank; flagged as interpretation, not verified fact |
| Baseline = 150 tests (original claimed 77) | no attempt to match a number we cannot verify; the gate is "all green", not a count |
| Runtime deps = zero; fastapi/pytest as extras | kernel purity invariant generalized to a dependency-free baseline that runs anywhere |
| Organs seeded: accounting, painting-leads, ziman | from the vault `_code/` ventures; accounting kept `vital` per the missing-life-support-organs gap (charter gap #2) |
| Five-state revenue: REPORTED/APPROVED/SETTLED/CONFIRMED/ATTRIBUTED | the corpus names "5-state carried-token attribution" without listing states; states chosen to make INV-7/INV-8 mechanical |
| σ gate is prospective | found during reconstruction: gating on current σ overshoots the limit by exactly one spawn |
| Sqlite read paths take the store lock | found during reconstruction: commits reset pending cursors on a shared connection (real race, caught by the suite) |

## 3. Known risks carried over from the corpus (unresolved here)

- **R4/three-bucket**: real providers must report orchestration tokens; the
  Phase 1 adapter must map them or fitness is poisoned.
- **R5/single number**: the cap default here is 3000c (AU$30) per the last
  human verdict in the corpus; if the operating cap differs, change only
  `NBB_GLOBAL_CAP_CENTS`.
- **Organ taxonomy**: charter ventures vs budget projects were never
  reconciled in the corpus; the seed list here is minimal and must be
  extended by human verdict, not by code.
- **Deadline-priority conflict (R8)** and **external-reach question**: still
  open human decisions; the pulse function accepts `deadline_proximity` but
  nothing privileges any organ yet.

## 4. What the skeleton proves already (evidence, not claims)

- INV-1 under contention: `test_racing_reservations_never_exceed_cap`
  (memory + sqlite legs, 4 threads).
- INV-5 tamper/drop/reorder detection: `test_events_chain.py`; concurrent
  appends never fork: `test_concurrent_appends_never_fork_history`.
- INV-2/INV-3/INV-6 denial paths: `test_gates.py`, `test_service_flow.py`
  (incl. stale-approval σ freeze and TOCTOU cap re-check).
- Genome→soma rebuild: `test_soma_rebuilds_from_genome`.
- Deterministic L2 replay incl. fail-closed cassette miss:
  `tests/l2_replay/test_replay_epoch.py`.
- Kernel purity + dependency direction: `tests/test_import_lint.py`.
