# DESIGN — Reproduction = C6 self-improvement (M3.A, generation 2)

PROPOSE-ONLY. Read-only architect draft against the LIVE organism at `F:\backup`.
Nothing here is applied. Every transplant is an owner tap. `merge_or_deploy` and
`replicate` stay FORBIDDEN forever.

---

## 0. Verified reality — the premise has already moved

The mission brief says `run_experiment` has "ZERO runtime caller outside tests."
**That is stale.** A generation-1 of exactly this work is already live and wired:

- `F:\backup\_ops\c6_trigger.py` — a runtime trigger. `c6_research_beat()` at
  `c6_trigger.py:102` calls `research_loop.run_experiment` at `c6_trigger.py:144-149`.
- It is invoked once per day from the organism daily tick at
  `organism.py:570-578`, behind `_w.flag("OCTOPUS_WIRE_C6_RESEARCH")`.
- Design doc `F:\backup\_ops\DESIGN-reproduction-c6.md` already documents gen-1.
- `research_contract.py` exists (`make_contract` at `:90`); `research_loop.run_experiment`
  at `research_loop.py:198`.

So the runtime trigger, the flag+owner-gate, the conservative caps, the
`_permit()`/`propose_only_apply_guard` path, and RFC-card delivery **already ship**.
This document is therefore **generation 2**: it does NOT re-invent the trigger. It
closes the four gaps that gen-1 left open, all additive and propose-only.

### What gen-1 already satisfies (confirmed by reading code)

| Mission requirement | Where it already lives | Status |
|---|---|---|
| Runtime trigger feeding `run_experiment` from heartbeat-periodic source | `c6_trigger.c6_research_beat` @ `c6_trigger.py:102`, daily tick `organism.py:570-578` | DONE |
| Behind flag + owner-gate | `OCTOPUS_WIRE_C6_RESEARCH` env + `ACTIVATION-C6-RESEARCH.flag` file, both required at `c6_trigger.py:45-51` | DONE |
| Conservative mode = 1 experiment/day | `DAILY_BUDGET.max_experiments=1` `c6_trigger.py:42`; daily tick cadence | DONE |
| Hard budget + token caps | `DAILY_BUDGET={cost_aud:0.50, time_s:120, tokens:50000, max_experiments:1}` `c6_trigger.py:42`; enforced by `Budget.exceeded` `research_loop.py:118-127` | DONE |
| Every action through `_permit()` | `run_experiment` gate `_permit("test_in_sandbox")` `research_loop.py:211`; `_permit` `research_loop.py:43-47` (fail-closed) | DONE |
| `propose_only_apply_guard` present | `research_loop.py:471-473` | DEFINED but never CALLED — see Gap 4 |
| Held-out mandatory + anti-hacking | `held_out_eval=_lg.fast_ledger_eval` passed `c6_trigger.py:148`; anti-hacking flag `held_out_evaluator.py:200-204` | DONE |

### Historical scar (resolved, noted for the owner)

`governor-alerts.md:1503` records: `c6 run_experiment failed: TypeError:
run_experiment() got an unexpected keyword argument 'evaluator'`. The current
`c6_trigger.py:148` passes `held_out_eval=`, not `evaluator=`. **This scar is
already healed** in the live code; no action needed.

---

## 1. The four gaps this generation closes

### Gap 1 — No unified reproduction state machine (the core ask)

Reproduction state is currently scattered across **four independent vocabularies**
with no reconciliation:

1. **Research verdict** (`ResearchLedger` rows) — `_TERMINAL_VERDICTS =
   ("accepted","rejected","quarantined","verified-not-admitted")` at
   `research_loop.py:35`, plus `terminated`, `admission-promoted`.
2. **Memory admission_state** — `PENDING | ADMITTED | RETRACTED`,
   `_ADMISSION_STATES` at `memory_store.py:29`; PENDING is invisible to
   `get`/`search` (`memory_store.py:155`, `:201`).
3. **Hypothesis-queue status** — `PENDING | RUNNING | DONE` in
   `c6_trigger.py` (`_pop_next_hypothesis` `:54`, `_mark_hypothesis` `:230`).
4. **RFC card state** — `merge / deny / edit` buttons in `approval_channel.rfc_card`
   (referenced `DESIGN-reproduction-c6.md:17`).

Nothing maps these onto a single lifecycle, so "where is this reproduction event
right now?" has no single answer, and there is no receipt at each transition.

**Design — one canonical lifecycle** (new pure module `c6_state_machine.py`):

```
PROPOSED ──▶ RUNNING ──▶ VERIFIED ──▶ PENDING_ADMISSION ──▶ ADMITTED ──▶ TRANSPLANTED
    │            │           │                                   │            (owner tap
    │            │           │                                   │             = birth)
    │            ▼           ▼                                   ▼
    │        TERMINATED   REJECTED                             DENIED
    │        (budget/     (falsified /                      (owner declines)
    │         crash)       max-rewrites)
    │            │
    └────────────┴──────────────▶ QUARANTINED / RETRACTED (safety terminal)
```

Canonical states and the scattered fields they reconcile:

| Unified state | Research verdict (`ledger_entry`) | Memory `admission_state` | Queue status | RFC card |
|---|---|---|---|---|
| `PROPOSED` | (none yet) | (none) | `PENDING` | (none) |
| `RUNNING` | (journal `EXPERIMENT_RUNNING` `research_loop.py:271`) | (none) | `RUNNING` | (none) |
| `VERIFIED` | supported+held_ok, pre-admission `research_loop.py:342` | (none) | `RUNNING` | (none) |
| `PENDING_ADMISSION` | `accepted` + `admission_state:"PENDING"` `research_loop.py:399` | `PENDING` (invisible) | `RUNNING` | (none) |
| `ADMITTED` | `admission-promoted` + `ADMITTED` `research_loop.py:430-432` | `ADMITTED` | `DONE` | `OPEN` |
| `TRANSPLANTED` | (owner action, new receipt) | `ADMITTED` | `DONE` | `MERGED` |
| `REJECTED` | `rejected` `research_loop.py:331`/`:229` | (none/n-a) | `DONE` | (alert only) |
| `QUARANTINED` | `quarantined` `research_loop.py:347` | (none) | `DONE` | (alert only) |
| `RETRACTED` | (post-hoc rollback) | `RETRACTED` `memory_store.py:143` | `DONE` | n-a |
| `VERIFIED_NOT_ADMITTED` | `verified-not-admitted` `research_loop.py:386` | `PENDING`→retracted | `DONE` | (alert only) |
| `TERMINATED` | `terminated` `research_loop.py:212,260,440` | (none) | `RUNNING`→re-queue | (none) |

The mission's requested labels map exactly:
`PROPOSED→RUNNING→VERIFIED→PENDING_ADMISSION→ADMITTED|REJECTED|RETRACTED|QUARANTINED`
— with `TRANSPLANTED`/`DENIED` added as the owner-gate leaf beyond `ADMITTED`, and
`TERMINATED`/`VERIFIED_NOT_ADMITTED` retained as honest failure leaves that already
exist in code.

**Receipt at each transition.** `c6_state_machine.transition()` writes ONE append-only
row to `state/c6/state-machine.jsonl` AND records a `DecisionReceipt`
(`effect_class:"E0"`, the same store used at `research_loop.py:311` and
`learning_gate.py:190`) for every edge. The row carries:
`{repro_id, contract_id, from, to, verdict, memory_id, receipt_id, ts, evidence_sha}`.
`repro_id = sha256(contract_id)` is the stable lineage key. Illegal edges
(e.g. `REJECTED→ADMITTED`) are rejected by an allowed-transition table — the same
fail-closed posture as `memory_store.set_admission_state` (`memory_store.py:220-247`).

This is a **reconciler + recorder**, not a new controller: it derives the unified
state from the artifacts that `run_experiment` already produces (`result["verdict"]`,
`result["ledger_entry"]["admission_state"]`, `result["memory_id"]`), so it cannot
diverge from ground truth and adds zero new authority.

### Gap 2 — The experiment produces a benchmark number, not a transplantable patch

For "reproduction = governed **code** self-improvement" to be literally true, the
sandbox artifact must be a **candidate diff**, not just a latency delta. Today
`_derive_fns` (`c6_trigger.py:178-203`) runs a micro-benchmark and returns
`{measured_ms, benchmark_gain_ms}`. That proves the *loop* works but never yields
something to transplant.

**Design — `kind:"code_patch"` hypotheses (additive, still $0, still sandboxed):**
- A hypothesis may carry `patch_path` (a `.patch` under `state/c6/candidates/`, authored
  by the owner or by a future proposer) plus `bench_before`/`bench_after` commands.
- `experiment_fn` applies the patch **into a throwaway sandbox copy only** (never
  `F:\backup` master; never genome), runs the frozen baseline benchmark before/after,
  and returns `{benchmark_gain, patch_sha256, sandbox_green: bool}`.
- `verifier_fn` requires `sandbox_green and benchmark_gain>0` to set `supported=True`.
- The patch content is carried as an artifact reference (sha only) into the RFC card.
- **Absolute:** the trigger NEVER applies the patch to master. Applying = `merge_or_deploy`
  = FORBIDDEN (`governance.py:62`). The green patch is *attached to the RFC card* and
  waits for the owner. That owner tap is the only path from `ADMITTED` to `TRANSPLANTED`.

Conservative mode ships `kind:"micro_benchmark"` as today's default; `code_patch`
is opt-in per hypothesis so gen-1 behavior is unchanged when no patch is queued.

### Gap 3 — "Generational birth" doctrine is undocumented and unmeasured

There is no place in code that says: an owner-gated transplant of a green sandbox
patch to master **is** a reproduction generation, and human approval rate **is** the
selection pressure. See `align-replication-to-c6.md` (deliverable 2) for the exact
replication.py doctrine change and the read-only generation counter.

### Gap 4 — `propose_only_apply_guard` is defined but never called

`propose_only_apply_guard` (`research_loop.py:471-473`) asserts the loop never
auto-applies. `c6_trigger` relies only on the internal `_permit("test_in_sandbox")`
gate and never calls the guard at its own boundary. **Design:** `c6_research_beat`
calls `propose_only_apply_guard("merge_or_deploy")` before any card delivery and
**hard-refuses to proceed if `permitted` is ever True** (it must always be False,
since `merge_or_deploy ∈ SELF_IMPROVEMENT_FORBIDDEN`, `governance.py:62`). This turns
a passive comment into an active tripwire: if governance is ever mutated to permit
merge, the C6 beat halts instead of transplanting.

---

## 2. Trigger design (generation 2, reconciled)

`c6_research_beat` gains a thin state-machine wrapper; the executable pipeline is
otherwise unchanged from `c6_trigger.py:102-175`:

1. `flag_on()` — env flag AND owner activation flag (`c6_trigger.py:45-51`). Off → no-op.
2. **Guard tripwire** — `propose_only_apply_guard("merge_or_deploy")`; abort if permitted.
3. Pop hypothesis → emit `PROPOSED→RUNNING` transition (receipt).
4. `make_contract` (`research_contract.py:90`) — immutable, falsification-gated,
   tools ⊆ `SELF_IMPROVEMENT_ALLOWED` (`research_contract.py:18-20,58-61`).
5. `run_experiment(...)` with real stores (`c6_trigger.py:144-149`) — inside it:
   `_permit("test_in_sandbox")`, budget caps, verifier, held-out, two-phase memory
   admission via `learning_gate.learn_from_outcome(pending_admission=True)`
   (`research_loop.py:367-375`) then `finalize_pending_learning(admit=True)`
   (`research_loop.py:419`).
6. **Reconcile** `result` → unified state via `c6_state_machine.derive(result)` and
   emit the transition (`RUNNING→{VERIFIED→PENDING_ADMISSION→ADMITTED | REJECTED |
   QUARANTINED | VERIFIED_NOT_ADMITTED | TERMINATED}`), one receipt each.
7. RFC card delivered **only when unified state == ADMITTED and utility > 0**
   (today the card is delivered on every verdict; gen-2 restricts it, matching
   `DESIGN-reproduction-c6.md:38` intent "card only if utility>0"). Card carries
   the patch sha for `code_patch` hypotheses. Card state `OPEN`.
8. Owner tap on the card → out of band → `admit_transplant(repro_id)` emits
   `ADMITTED→TRANSPLANTED` (birth) or `ADMITTED→DENIED`. **No auto-apply**; the tap
   is the owner performing the merge themselves per the prohibited-action rule.

Cadence options (both supported, conservative default = daily):
- **Heartbeat-periodic (default, live):** daily tick `organism.py:570-578`, exactly
  1 experiment/day via `max_experiments:1`.
- **Cortex goal-module (future):** a goal-module may `append` a structured hypothesis
  to `state/c6/hypothesis-queue.jsonl`; it can only ENQUEUE, never execute — execution
  stays behind the same daily gate. This keeps the goal source decoupled from the
  governed executor.

---

## 3. Governance conformance (final boundary)

- `merge_or_deploy` FORBIDDEN — never called; guard tripwire actively asserts it
  (`governance.py:62,66-71`). Transplant = owner's own hands.
- `replicate` FORBIDDEN — this design adds NO spawn; generations are counted, never
  spawned (deliverable 2).
- `edit_verifier`/`edit_constitution` FORBIDDEN — held-out suite is frozen
  (`held_out_evaluator.py:27-33`); genome untouched; verifier/constitution defects
  route to the owner maintenance lane (`governance.py:111-113`).
- `expose_heldout_answers` FORBIDDEN — held-out only returns pass/fail + anti-hacking
  flag (`held_out_evaluator.py:200-217`); no answers leak into memory.
- `conceal_failures` FORBIDDEN — every transition (including REJECTED/QUARANTINED/
  TERMINATED) writes a durable receipt + ledger row; nothing is swallowed.
- Held-out mandatory + anti-hacking active — `held_out_eval` always passed
  (`c6_trigger.py:148`); `learn_from_outcome` blocks on `anti_hacking_flag`
  (`learning_gate.py:145-147`).
- `propose_only_apply_guard` never bypassed — now actively enforced at the trigger
  boundary (Gap 4).

## 4. Risk & rollback

- Flag off (default) → complete no-op; gen-1 and gen-2 both dormant.
- Rollback: `OCTOPUS_WIRE_C6_RESEARCH=0` + restart; or remove
  `ACTIVATION-C6-RESEARCH.flag`. Either kills the beat.
- New module `c6_state_machine.py` is pure/read-derive + append-only journal; it has
  no authority and cannot change any verdict. Removing it reverts to gen-1 exactly.
- `code_patch` hypotheses are opt-in; with none queued, behavior == gen-1.
- Every reproduction event is fully reconstructable from
  `state/c6/state-machine.jsonl` + receipts + research ledger.
