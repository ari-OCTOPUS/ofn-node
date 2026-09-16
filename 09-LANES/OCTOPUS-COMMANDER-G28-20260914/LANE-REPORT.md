# LANE REPORT — OCTOPUS-COMMANDER-G28-20260914 (session 4: ROUND30 directive)

GOV_VERSION=V8 · LADDER=L2 · customer_send=false · GO-B4=false · hold_external=true
2026-09-14 11:03Z→11:25Z (all `date -u`)

## Delivered this round (everything staged on the TRIO artifact; live executor 109e68c0 UNTOUCHED — all pins intact)

1. **B5 same-scope measurement (§1)** — three real counterexamples found and fixed on the way to the contract: (a) v1 compared `findings[:20]` before vs ALL caches after (successful cleanup FAILED — proven); (b) the scan listed a cache dir AND its child .pyc as separate targets → child mv rc=1 → whole action FAILED (`exit_codes [0,0,1,1]` measured); (c) same-basename targets collided in the quarantine dir. Final design (TRIO v2d `a85db3b0`): frozen target set + ONE counting rule both sides, findings dedupe, quarantine-**mv to unique names** (rm -rf removed per AGENTS.md), **measurement-first verdict** (partial mv failures keep explicit freed/access-error numbers; freed==0 fails honestly), zero-before = `B5_NOTHING_MEASURABLE` (no proposal, no slot burn). Physical-space-freeing explicitly NOT claimed (quarantine frees nothing; purge = owner-scoped). Real-path acceptance (handler → action record → real mv execution → verifier) in `trio-v2-battery.py`.
2. **CATSCOPE dedicated controls (§2)** — live-executor counterexample proven: an `OPS_B_OUTCOME_REJECTED` for `ALPHA_XY` blocks `BETA_XY` (suffix conflation); v2 isolates by class in all three paths (breaker, outcome-reject, admission). Bonus defect found+fixed: **one torn ledger line KILLED `budget_allows` on live** (tick death); v2 skips malformed lines fail-closed.
3. **G3 robustness (§2)** — tie-break deterministic; missing/null/invalid priority crashed v1's tick (proven) → v2 parses to 100; corrupt file ignored; **budget-blocked priority-1 no longer starves a ready priority-2** (v1 starved — proven; v2 proposes the ready one in the same tick, one-action-per-tick preserved).
4. **Queue DAG from identities (§3)** — extracted and classified: G8→(capability-pin), W24→(deploy-ordering on G8), TRIO independent (base = live executor), G30→(deploy-ordering on TRIO — edge REPLACED this round: its old byte-pin would stale-block forever after TRIO deploys). Chain receipts `OPS_B_REQUEST_ARTIFACT_UPDATED` + `OPS_B_REQUEST_EDGE_UPDATED`; chain verifies 1520. Pin-fate after TRIO documented (G8/W24 pins die only if TRIO jumps the queue — fail-closed, repin step recorded).
5. **§4a source-gap CLOSED** — the executor now performs the B8 copy itself from the bytes read at check time; barrier test swaps the source inside the write window → target still receives the VERIFIED bytes (not a second hash-check — the gap is not recreated).
6. **§4b rollback-precondition timing CLOSED** — preconditions freeze into the action record at admission and re-check at pre-effect; invalidating containment after admission → `PRECONDITION_DRIFT` block, target untouched (real B4 rollback-requests path, both polarities tested).
7. **owner_notify → consumption (§5) traced end-to-end with code refs** — chain is live/proven up to the decision row (cards→ingress→binder→owner_decision.v1.jsonl); **final edge OPEN: no production consumer resumes a task from an emitted decision** (only writers + liveness probe + test read the file; the first-bind STRATA-CHOICE row sits unconsumed). Recorded as NOT-full-wiring per the owner's own rule; the consumer component is the exact next build. Two-hash card untouched (open, silence ≠ answer).
8. **Battery 24/24 + regression matrix 32/32 on a85db3b0**; live-tick behavior unchanged (queue waits on budget as designed).

## Incident (honest report)

First battery run leaked isolation: `Path.home` was pinned only at fixture build, so the B5 scan globbed the REAL `~/wt-*` on 138 — 12 real cache items were mv-quarantined into fixture dirs (**recovered 100%** via the proposal path records, `recover-b5-leak.py` kept in the lane); the v1 rm -rf run hit fixture-internal targets only (verified GONE=0). No unique data touched (whitelist caches only); wt-c7-harness git-clean. Lesson: pin the environment for the WHOLE run — fixed in the battery (global battery-home).

## Evidence

Scripts: `apply-trio-v2/v2b/v2c/v2d.py`, `trio-v2-battery.py`, `dag-and-requeue.py`, `recover-b5-leak.py`, `dbg-b5.py` (lane dir + /tmp on 138). Checkpoint: `ROUND30-CHECKPOINT.json`. Chain rows ~1470–1520.

## Rollback

TRIO staged-only (live untouched): preimages `ops_agent.py.trio-v1-d0b86a35 / .trio-v2-9126c388 / .trio-v2b-aa867bfb / .trio-v2c-ae293073`; queue edges reversible via the recorded `dependencies_original` fields.

## NEXT-ACTION

1) Build the decision consumer (reads owner_decision rows → resumes the bound task → own receipt + read-back) and fixture-drive it with a financially-inert request. 2) Observe the 09-15 quota slots (G8 then W24) with byte/journal read-backs. 3) Post-TRIO repin step per the DAG note.
