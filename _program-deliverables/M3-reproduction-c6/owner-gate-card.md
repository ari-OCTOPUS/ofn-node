# Owner-gate card — M3.A reproduction = C6 (generation 2)

## What you are approving
Merging the DRAFT `reproduction-c6.patch` into a working branch (NOT master, NOT
genome). The patch is **additive and propose-only**. It:
1. Adds a new pure module `_ops/c6_state_machine.py` — a reconciler/recorder that
   collapses the four scattered reproduction vocabularies (research verdict, memory
   admission_state, hypothesis-queue status, RFC card state) into ONE canonical
   lifecycle `PROPOSED→RUNNING→VERIFIED→PENDING_ADMISSION→ADMITTED→TRANSPLANTED`
   (+ REJECTED/QUARANTINED/RETRACTED/VERIFIED_NOT_ADMITTED/TERMINATED/DENIED), writing
   an append-only transition row + a DecisionReceipt at every edge.
2. Hardens the existing live trigger `_ops/c6_trigger.py`: activates the dormant
   `propose_only_apply_guard` as a HALT tripwire, emits unified-state transitions,
   and restricts RFC-card delivery to `ADMITTED` results with utility>0.
3. Reframes `_ops/budget/replication.py` doctrine (reproduction = owner-gated code
   transplant, not spawn) and adds a READ-ONLY `c6_generations()` counter.

## What this does NOT do
- Does NOT auto-apply, merge, or deploy anything. `merge_or_deploy` and `replicate`
  stay FORBIDDEN (`governance.py:59-63`). A "generational birth" (TRANSPLANTED) is
  recorded ONLY when you tap merge on an RFC card and perform the merge yourself.
- Does NOT run unless BOTH `OCTOPUS_WIRE_C6_RESEARCH=1` AND
  `ACTIVATION-C6-RESEARCH.flag` (your file) are present. Default = dormant no-op.
- Does NOT touch the genome, `.env`, budgets state, kill-switches, or the held-out
  suite. No new spawn logic anywhere.
- Adds no new authority: the state machine only derives state from artifacts
  `run_experiment` already produces; it cannot change any verdict.

## Rollback
- `OCTOPUS_WIRE_C6_RESEARCH=0` + restart, or delete `ACTIVATION-C6-RESEARCH.flag`
  → beat becomes a complete no-op.
- Revert the patch → returns to generation-1 exactly; `_ops/c6_state_machine.py` is
  standalone (delete it, no other file depends on it at import time except the
  fail-soft `try/except import` in `c6_trigger.py`).
- All reproduction history remains reconstructable from
  `state/c6/state-machine.jsonl` + receipts.db + research-ledger.jsonl.

## Your decision
- TAP MERGE → approve the branch merge (you perform it); reproduction telemetry and
  guard tripwire go live behind the still-required activation flags.
- TAP DENY → nothing changes; generation-1 continues as-is.
