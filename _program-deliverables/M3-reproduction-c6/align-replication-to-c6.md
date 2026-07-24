# align-replication-to-c6.md — doctrine change for `replication.py`

PROPOSE-ONLY. The doctrine change below is additive: it reframes what a
"generation" is and adds a **read-only** counter. It adds NO spawn logic. The
`replicate` action stays FORBIDDEN forever (`governance.py:62`).

---

## The doctrine shift

Owner's recorded decision: **reproduction = governed code self-improvement, NOT
process spawn.** But `replication.py` still measures reproduction the old way — as
sub-agent spawn events feeding a branching ratio σ:

- `sigma_state` computes `σ = approved_spawns / active_cells` from ledger
  `SPAWN_PROPOSAL` / `APPROVAL` events (`replication.py:40-75`).
- `evaluate` emits `spawn-subagent` proposals, human-gated, capped at
  `MAX_CELLS=6` (`replication.py:30,97-105`).
- The module docstring frames reproduction as "spawn = mutation; human-gate =
  selection pressure" (`replication.py:6-8`).

Under the C6 doctrine, **a reproduction generation is an owner-gated transplant of a
green sandbox patch to master** (an `ADMITTED` C6 patch that the owner taps to merge),
not a spawned process. The σ machinery stays (it is still the correct guard for the
*population-of-cells* geometry, and its `σ>1 → cancer-axis → stop` alarm at
`replication.py:69-72` remains a valuable brake), but the docstring must state plainly
that **the canonical reproduction generation counter is the count of ADMITTED /
TRANSPLANTED C6 patches, and this module must never gain spawn-execution logic.**

## Fitness = selection pressure (already true, now made explicit)

`fitness.py` already computes VALUE = human acceptance rate
(`sent/(sent+rejected)`, `fitness.py:16,171`) and is deliberately non-authoritative
until ~28 days of data (`fitness.py:19-21,37,215`). The alignment: **the same
human-approval-rate selection pressure that gates spawn eligibility
(`acceptance_rate ≥ accept_threshold`, `replication.py:89`) is the pressure that
should gate which C6 hypothesis lineages advance into `PENDING_ADMISSION`.** A lineage
(hypothesis `kind`) whose RFC cards the owner keeps merging has high fitness and earns
more experiment budget; a lineage the owner keeps denying is selected out. No new
authority — this is the existing approval-rate signal pointed at the C6 queue.

## Concrete changes (all additive, propose-only)

1. **Docstring doctrine block** (`replication.py:2-19`): add a paragraph stating
   reproduction = owner-gated C6 patch transplant; σ/spawn geometry is retained only
   as a population guard; generations are COUNTED from ADMITTED C6 patches; this
   module must NEVER gain spawn-execution logic (`replicate` FORBIDDEN forever,
   `governance.py:62`).

2. **New read-only helper `c6_generations()`**: counts `admission-promoted` /
   `ADMITTED` rows in the C6 research ledger
   (`_ops/state/c6/research-ledger.jsonl`, written by `run_experiment` via
   `ResearchLedger.append_strict`, rows shaped at `research_loop.py:430-432`).
   Returns `{"generations": N, "source": "...", "note": "owner-gated transplants;
   never process spawns"}`. It reads only; it proposes/executes nothing.

3. **Surface it in `evaluate`'s report**: add `report["c6_generations"] =
   c6_generations()` alongside the existing `sigma` block (`replication.py:115-126`)
   so the organism's reproduction telemetry shows the *doctrinally correct* generation
   count next to the legacy σ population metric.

## What does NOT change (hard invariants)

- No spawn is ever executed here — `evaluate` still only writes PROPOSALs
  (`replication.py:97-105,125`). `c6_generations()` is pure read.
- `replicate ∈ SELF_IMPROVEMENT_FORBIDDEN` (`governance.py:62`) — untouched.
- σ alarms, `MAX_CELLS`, double-gate live activation (`replication.py:17-18,92-94`)
  — untouched.
- No genome writes; the C6 ledger read is under `state/`, not
  `07 - Knowledge/genome-system`.

The unified diff for items 1–3 is in `reproduction-c6.patch`.
