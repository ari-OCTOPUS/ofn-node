# C3 — DURABLE LEARNING LOOP — REPORT (2026-07-23)

> Goal: Perception→Memory→Reasoning→Decision→Outcome→**Learning→Memory Update**, anti-self-deception.
> Base: C2 (memory substrate) + C4. Commits `89b8ed6` (build) + `a7c9826` (red-team hardening).

## What already existed (verified, not rebuilt)
- **MemoryStore** (append-only, FTS5, supersede-not-delete), **MemoryGate** (dedup, provenance, salience bar, independent-grader `_verify_external_grade` that ignores claimant-set flags), **DecisionReceiptStore** (immutable, CoT-rejecting, `memories_used`=hash-refs, PENDING never faked), **lead_outcome_recorder** (decision→receipt→outcome→link, cites `memories_used`). Flags `MEMORY_GATE`+`LEAD_OUTCOME` were default-off.

## The genuine gap C3 closed
Nothing wrote a **learned memory from an outcome** — so the next decision had nothing to cite and D8 stayed 0. `learning_gate.py` adds that arc with two anti-self-deception guards.

## Build + live activation
- `learning_gate.learn_from_outcome`: high-trust outcome → candidate lesson → guards → `MemoryGate.submit` (GRADED, dedup, versioning) + durable learning receipt. `rollback_learning` supersedes (invalidate).
- Flags **activated** (`MEMORY_GATE`+`LEAD_OUTCOME`); live canary: `learned=True`, and the next `record_lead_decision` **cited the learned memory_id**. DBs created: memory.db, receipts.db.
- **Wired live** into the owner-verdict path: an owner **accept** → gated learning (cheap ledger eval, outcome-bound), dedup per-proposal → no flood.

## Adversarial review — no P0/P1-exploit; 3 real P1s found and FIXED (`a7c9826`)
1. **BUG — rollback was a no-op for TTL'd memories.** `memory_store` supersede only invalidated `valid_to IS NULL`, but semantic (90d)/episodic memories carry a future `valid_to` → the rolled-back memory stayed live+citable for its whole TTL. **Fixed**: supersede now shortens a future `valid_to` to now. The original test asserted an already-true condition (false green) — **rewritten** to assert `get`/`search` exclusion post-rollback.
2. **FORGERY — trust was an unauthenticated caller string.** `trust="OWNER_CONFIRMED"` bound to nothing. **Fixed**: `learn_from_outcome` now verifies `outcome_ref` against **outcomes.db** (OWNER_CONFIRMED requires a real `accepted-measurement` row); no store / forged ref → **fail-closed**. +test.
3. **DEAD PATH — `learn_from_outcome` had no production caller** (wiring wrote to the gate directly). **Fixed**: wired into `record_verdict_durably` (live owner-accept path), outcome-bound.

## Honest residual limitations (documented, not hidden)
- **Held-out gate = system-safety circuit-breaker, NOT a content oracle.** A memory write doesn't change the fixed canary tests, so the held-out eval can't judge whether a *specific lesson* is true — it blocks learning only while the system is in a safety-regression window. **The real content defense is guard #2 (outcome-binding):** you can't learn a lesson unless a real durable outcome backs it. A per-lesson predictive held-out eval (does citing it improve decision accuracy on a labeled held-out set?) needs a labeled dataset → **future work**, explicitly not claimed done.
- **P2 (accepted, mitigated/known):** salience is caller-set (dedup + outcome-binding bound abuse; a per-source quota is future work); the `semantic` namespace stamps `GRADED` on the salience bar alone — same label as receipt-verified GRADED (consumers should treat semantic-GRADED as "salience-passed", not "independently verified"; the independent-grader path (`_verify_external_grade`) remains the only receipt-verified GRADED and is correctly fail-closed); `_SECRET_RX` catches keys/tokens but not general PII/CoT — the store isn't bypassable and receipts carry only sha, but a length/PII cap on memory content is future work.

## Tests
- `test_learning_loop.py` **9/9**: durable artifact; loop closes (real decision cites learned id); harmful-learning blocked; anti-hacking blocked; zero duplicate learning; outcome≠preference; **forged-trust rejected**; **rollback excludes from get/search**; restart continuity. Full sandbox suite: 271/271 (re-verifying after hardening).

## D8 / success criteria
- Every "learned" claim → durable memory + receipt (artifact) — **enforced** (no artifact → not learned).
- Next decision uses durable memory — **proven** (citation, live + test).
- Memory rollback/versioning — **now real** (bug fixed).
- Outcome ≠ preference — **enforced** at two layers (trust tier + outcome-binding).
- Zero duplicate learning — **enforced** (dedup).
- **D8 2 → 4** (honest): the learning arc is closed, outcome-bound, restart-safe, and its rollback works — a real compounding substrate. Not higher because content-correctness eval (per-lesson held-out) is future work, so "learning that reliably improves capability" isn't yet measured on a held-out task set.

## VERDICT: C3 DONE (loop closed, anti-self-deception guards real, red-team-hardened) — with named future work
Rollback = revert `89b8ed6`+`a7c9826`, or flags → 0. External-effect lanes remain disarmed.
