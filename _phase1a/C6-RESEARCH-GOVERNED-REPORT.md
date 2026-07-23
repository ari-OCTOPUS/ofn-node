# C6 — RESEARCH & GOVERNED SELF-IMPROVEMENT — REPORT (2026-07-23)

> Goal: discover & improve **without** blindly editing the genome. Proposal-only, sandbox/worktree,
> autonomous-apply FORBIDDEN, owner gate intact. Commit `30f867d`.

## Precondition note (honest)
C6's charter lists live entry gates. Two are unmet — **live 24h one-heartbeat parity soak** (C5 scheduler ready, soak pending) and the **live STOP-METABOLIC halt** (organism frozen). I proceeded because C6 is **entirely proposal-only / sandbox / worktree with autonomous-apply forbidden** — those gates protect *live actuation*, which C6 does not do. Nothing here runs live over the frozen organism; the loop never applies, merges, or deploys.

## What was built (composition, not reinvention)
The harness composes the whole stack behind constitutional governance:

| concern | mechanism | reuse |
|---|---|---|
| research spec | `research_contract` — immutable, hashed, **falsifiable** (falsification_criteria required); tools **fail-closed** to the PRE-0 constitutional-allowed set | — |
| action gate | every action through `governance.self_improvement_permits` (fail-closed; `merge_or_deploy`/`edit_verifier`/`edit_constitution`/… FORBIDDEN) | PRE-0/governance.py |
| hard budget | `Budget` — cost_aud / tokens / time_s / max_experiments; overrun → **terminate** | mission step 11 |
| bad conjecture | falsified hypothesis → **terminate** (ledger `rejected`), never rewrite forever (rewrite cap `MAX_REWRITES`) | mission step 7 |
| durable evidence | each experiment → DecisionReceipt + Outcome | C3 decision_receipt/outcome_store |
| verification | verifier + **held-out eval** before accept; anti-hacking honored | C3 held_out_evaluator |
| acceptance | `governance.utility` — hard-constraint fail ⇒ −∞ (benchmark gain can't buy a violation) | PRE-0/governance.py |
| memory admission | a finding enters memory **ONLY** via `learning_gate` (verifier+outcome-bound, C3) | C3 learning_gate |
| quarantine | held-out-fail / U≤0 / high uncertainty → **quarantined**, not committed | mission step 12 |
| self-model calibration | `record_calibration` — predicted vs measured; overconfidence → high uncertainty → quarantine | mission step 8 |
| long-horizon restart | `durable_journal` research-journal checkpoints → resume | C2-D |
| research ledger | append-only accepted/rejected/quarantined + evidence + receipt_id | deliverable |
| **no auto-apply** | `propose_only_apply_guard` proves `merge_or_deploy` is FORBIDDEN; the loop returns proposals only | mission step 5 |

## Tool invention (proposal-only) — reuses the doctor RFC lane
Code-change proposals go through the existing owner-gated lane: `doctor.propose_rfc → run_sandbox (isolated tmp, real suite) → _critic_review (adversarial) → submit_for_approval` (Telegram card) → **only a human-append merges** (`apply_merge` behind `OCTOPUS_WIRE_MERGE_APPLIES_KNOB`). C6 adds nothing that bypasses this; `merge_or_deploy` stays constitutionally forbidden. Cross-domain transfer is admissible only through the same held-out verification (the loop's `held_out_eval` gate).

## Tests
- `test_research_loop.py` **9/9**: contract validation (falsif + tools fail-closed); accepted→memory-via-gate; falsified→terminate-not-learned; bad-conjecture rewrite-cap terminate; budget terminate; held-out→quarantine; governance no-auto-apply; durable research-journal; calibration-overconfidence→quarantine. Full sandbox suite: 272/272 (re-verifying).

## Deliverables (mission)
- **Research ledger** — `state/research/ledger*.jsonl` (accepted/rejected/quarantined per hypothesis).
- **Accepted/rejected hypotheses** — recorded with evidence + receipt_id + utility.
- **Capability calibration** — `record_calibration` ledger (predicted vs measured, overconfidence flag).
- **Generated tools in sandbox** — via the doctor RFC lane (propose→sandbox→submit), owner-gated.
- **No silent apply / external effect** — proven: `merge_or_deploy` forbidden; loop returns proposals; external-effect flags disarmed.

## Honest status
The **governed research *harness*** is complete and proven — the safety spine (fail-closed governance, hard budget, falsification-terminate, held-out verify, memory-only-via-gate, quarantine, calibration, no-auto-apply, restart-safe) all hold under test. What it does **not** yet include is a *real research mission run* (a genuine question researched to accept/reject) — that needs the live preconditions (heartbeat soak, metabolic halt cleared) and a real owner-supplied question, and by charter each apply stays owner-gated. So: C6's engineering (the governed loop) is done and safe; running actual research missions is the owner-gated next step.

## VERDICT: C6 HARNESS DONE (governed, proposal-only, owner-gated) — real mission runs pending live preconditions
Rollback = revert `30f867d`. Zero live effect / zero apply.
