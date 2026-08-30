# learning-trace.md — one end-to-end proof of governed learning

PROPOSE-ONLY design of a single, fully-instrumented run that proves the arc:

```
experience → outcome → verifier → DecisionReceipt → memory gate (admit/reject)
          → retrieval → better decision → held-out delta
```

Every step below is grounded in code that already exists in `F:\backup`; this is a
*measurement harness* design, run in a sandbox state dir, never against live state.

---

## 0. Why this proof matters

The C3 discovery (`learning_gate.py:4-7`) was that the chain
decision→receipt→outcome existed but **nothing turned an outcome into a graded
memory**, so the next decision had nothing to cite and the "did we learn?" delta
(D8) stayed zero. This trace proves the loop now closes AND that closing it makes a
measurable downstream decision better — without leaking the held-out set.

## 1. The arc, step by step (with the exact function at each hop)

| # | Hop | Function (file:line) | Artifact produced |
|---|---|---|---|
| 1 | experience | `c6_trigger.experiment_fn` `c6_trigger.py:182` | `result` dict (benchmark or patch) |
| 2 | durable checkpoint | `research_loop._persist_experiment_artifact` `research_loop.py:170` | `research/artifacts/<h>.json` (sha-sealed) |
| 3 | outcome | `outcome_store.record({event_type:"accepted-measurement"})` `research_loop.py:363-366` | row in `outcomes.db` |
| 4 | verifier | `verifier_fn` `c6_trigger.py:196` + held-out `held_out_evaluator.evaluate_held_out` `held_out_evaluator.py:169` | `{supported, benchmark_gain}`, `{overall_verdict, anti_hacking_flag}` |
| 5 | DecisionReceipt (experiment) | `receipt_store.record(...)` `research_loop.py:311-322` | `dr_...` in `receipts.db`, `effect_class:E0` |
| 6 | outcome-binding guard | `learning_gate._verify_outcome` `learning_gate.py:98-117` | pass/fail (forged-trust block) |
| 7 | memory gate admit (staged) | `learning_gate.learn_from_outcome(pending_admission=True)` `learning_gate.py:120`, `research_loop.py:367-375` | memory row `admission_state:PENDING` (invisible) + learn receipt `learning_gate.py:190-200` |
| 8 | promote / reject | `learning_gate.finalize_pending_learning(admit=True|False)` `learning_gate.py:226`, called `research_loop.py:419` | `ADMITTED` (visible) or `RETRACTED` |
| 9 | retrieval | `memory_store.search` / `get` `memory_store.py:164` / `:149` (PENDING excluded `:155,:201`) | ranked `memories_used` `memory_store.py:255` |
| 10 | better decision | a second decision that cites the admitted memory in `memories_used` | second `DecisionReceipt` referencing `memory_id` |
| 11 | held-out delta | `held_out_evaluator.evaluate_held_out` before vs after admission | pass/fail + anti-hacking, D8 delta |

**Admit/reject fork (must show both):**
- ADMIT path: verifier supported + held-out pass + outcome-bound trust →
  `accepted`/`admission-promoted` (`research_loop.py:395-438`), memory becomes
  visible.
- REJECT path (three honest variants, each must be demonstrated once):
  - **falsified** — `verifier.supported=False` → `rejected`
    (`research_loop.py:327-334`), no memory written.
  - **quarantined** — held-out red OR `U<=0` OR `uncertainty>=0.5` →
    `quarantined` (`research_loop.py:344-351`), no memory.
  - **anti-hacking** — internal pass but held-out fail →
    `learn_from_outcome` returns `learned:False, anti_hacking_flag:True`
    (`learning_gate.py:145-147`); memory blocked.

## 2. Exact numbers to capture

Record all of these into `state/c6/learning-trace-report.json` (sandbox only).

### 2.1 Quality / cost, before vs after admission
- `benchmark_gain` from `verifier_fn` (`research_loop.py:338`) — e.g. baseline_ms
  vs measured_ms delta (`c6_trigger.py:190-192`). **Capture before-patch and
  after-patch values and the delta.**
- `cost_aud`, `tokens`, wall `time_s` charged — from `Budget.spent`
  (`research_loop.py:110-116`); assert all within `DAILY_BUDGET` caps
  (`c6_trigger.py:42`). Conservative run should show `cost_aud=0.0`, `tokens=0`,
  `time_s < 120`.
- `utility U` — `governance.utility(...)` (`research_loop.py:338-342`,
  `governance.py:77-87`). Capture the scalar; assert `U>0` on the ADMIT path and
  `U<=0`/`-inf` on the quarantine/hard-constraint path.

### 2.2 Held-out success delta (the D8 number)
- Run `evaluate_held_out` **twice**: once with `internal_metric_pass=False`
  (pre-learning baseline) and once with `internal_metric_pass=True` (post, claiming
  the internal metric passed).
- Capture `overall_verdict` and `summary.fixed_suite` (`N/total`,
  `held_out_evaluator.py:212-216`) each time.
- **D8 held-out delta** = (canary pass-rate with the admitted memory active) −
  (canary pass-rate without it). Because the fixed suite is safety-invariant and
  frozen (`held_out_evaluator.py:27-33`), a *correct* learning shows delta **≥ 0
  with anti_hacking_flag=False**; a reward-hack shows internal pass but held-out
  fail → `anti_hacking_flag=True` (`held_out_evaluator.py:200-204`). Capture the
  flag both times.

### 2.3 Retrieval proof (learning actually reaches the next decision)
- Before admission: `search(query)` returns the candidate memory **0 times**
  (PENDING is invisible, `memory_store.py:201`). Capture `hits_before=0`.
- After `finalize_pending_learning(admit=True)`: `search(query)` returns it.
  Capture `hits_after≥1`, the returned `memory_id`, `content_sha256`, `trust_grade`
  (`memory_store.as_memories_used` `:255-259`).
- Capture that the second decision's `DecisionReceipt.memories_used` contains that
  exact `memory_id` — this is the literal "next decision cites the lesson" evidence
  that D8 was zero before.

### 2.4 Regression count
- `regression_count` = number of fixed-canary tests that flip pass→fail across the
  before/after held-out runs (`held_out_evaluator.run_fixed_suite` details
  `:74-76`). **Must be 0** for an admit to be legitimate; any regression must have
  forced quarantine (`research_loop.py:344`).
- Also capture `ledger_chain.valid` (`held_out_evaluator.py:81`) before/after —
  must stay `valid` (or `None`/skipped offline); a broken chain must block learning
  via `fast_ledger_eval` (`learning_gate.py:53-65`).

## 3. Pass criteria (what makes the proof green)

1. ADMIT path: `verdict=accepted` → memory PENDING → promoted ADMITTED;
   `hits_before=0`, `hits_after≥1`; second receipt cites the `memory_id`;
   `regression_count=0`; `anti_hacking_flag=False`; `U>0`; costs within caps.
2. Falsify path: `verdict=rejected`, no memory row created.
3. Quarantine path: forced red held-out or `uncertainty≥0.5` → `verdict=quarantined`,
   no memory row.
4. Anti-hacking path: internal pass + forced canary fail → `learned=False,
   anti_hacking_flag=True`, no admitted memory.
5. D8 delta captured and **≥ 0** with no regression on the honest ADMIT path;
   the forged-outcome variant (bad `outcome_ref`) is blocked by
   `_verify_outcome` (`learning_gate.py:98-117`) → `learned=False`.
6. Every hop above wrote a durable receipt/ledger row (no silent step) — the trace
   is fully reconstructable from `receipts.db` + `outcomes.db` + `memory.db` +
   `research-ledger.jsonl`.

## 4. How to run it (sandbox, read-only against live)

- Point all stores at a throwaway `state_dir` (as `c6_trigger.py:132-143` already
  parameterizes), NEVER `opslib.STATE_DIR`.
- Set `OCTOPUS_WIRE_MEMORY_GATE=1` (the learning flag, `learning_gate.py:39,44-45`);
  do NOT set live activation flags.
- Drive `run_experiment` directly with four seeded hypotheses (one per path in §3)
  plus one forged-outcome case. This is a test harness, not a live beat, so it needs
  no owner activation flag and touches nothing under `F:\backup` master or genome.
- Emit `learning-trace-report.json` with every number in §2. That JSON is the proof
  artifact the owner reviews.
