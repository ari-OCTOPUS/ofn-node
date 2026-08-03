# NBB Control Plane — Specification v0.2

status: reconstructed baseline · scope: skeleton contract + phase gates
audience: any coding agent or human continuing this system to production

---

## 1. Goal

A **local-first, multi-agent control plane** that manages several revenue
ventures ("organs") in parallel under one scarce resource (API budget), with
minimal human involvement but **absolute human sovereignty**. The single
fitness metric is **NBB — Net Bank Balance**: real AUD confirmed in the bank.

Three problems it must solve:

1. **State never dies** — the ledger (genome) is append-only, hash-chained,
   and replicable off-box; every projection (soma) is disposable and
   rebuildable from it.
2. **Scarce-resource allocation** under a single hard cap, without starving
   vital organs (floors) and without enforcement scattering (one choke point).
3. **Honest Darwinian selection** — reward (spawn) and punishment (cull) keyed
   only to CONFIRMED revenue, never to self-reported signals.

## 2. Architecture contract

```
          proposals                verdicts
Governor ───────────► Gates ◄─────────────── Human (boss, kill switch)
 (decides nothing     (enforce: budget_gate,
  alone; LLM lives     spawn_gate, effector_gate
  behind LLMPort)      = single choke point)
                          │ allowed (shadow → simulate)
                          ▼
                       Ledger  ──── projections ───► API / dashboard
                    (append-only,
                     hash-chained)
```

- **Kernel** (`src/nbb_cp/kernel/`): pure decisions. stdlib-only **by
  invariant**, enforced by `tests/test_import_lint.py`. No I/O, no clock
  reads, no env reads, no third-party imports. Ever.
- **Adapters** (`src/nbb_cp/adapters/`): implement `kernel/ports.py`
  Protocols. May import kernel; never import app/api.
- **App** (`src/nbb_cp/app/`): wiring and orchestration. The only layer that
  builds adapters and calls the service.
- **Lock-in containment**: LangGraph (Phase 1) lives entirely inside
  `adapters/llm/`. If a graph type appears in a kernel or app signature, the
  contract is broken. Swapping LangGraph out must touch one directory.

### Test levels

| Level | Where | What | Speed |
|---|---|---|---|
| L0 | `tests/l0_kernel/` | pure kernel units, no I/O | ms |
| L1 | `tests/l1_adapters/` | sqlite/API/service integration, race tests | ms–s |
| L2 | `tests/l2_replay/` | cassette-replayed end-to-end epochs, deterministic | s |

Baseline (this skeleton): **150 tests green** — `python -m pytest`.

## 3. Domain model

- `Money` — integer cents, AUD default. Floats never touch the ledger.
- `Organ` — venture/project; `floor` (protected minimum), `vital` (exempt
  from cull). Baseline organs: accounting, painting-leads, ziman.
- `Proposal(kind ∈ {GRANT, EFFECT, SPAWN})` — the only way anything happens.
- `Verdict` — human decision; the only source of approval for gated actions.
- `BudgetState(cap, committed, version)` — version is the optimistic-lock
  token; stores must CAS on it.
- `LedgerEvent(seq, ts, kind, payload, prev_hash, hash)` — kinds: PROPOSAL,
  VERDICT, GRANT, SPEND, REVENUE, SPAWN, LIFECYCLE, INCIDENT, KILL.
- Revenue attribution five-state: REPORTED → APPROVED → SETTLED → CONFIRMED →
  ATTRIBUTED. Only the last two count toward fitness (INV-7).
- Cost accounting three-bucket: `input_cents + output_cents +
  orchestration_cents`. Dropping the orchestration bucket poisons selection.
- σ (sigma) — executed spawns per active agent in a trailing window. The
  spawn gate judges **prospective** σ (value after one more spawn) ≤ 1.

## 4. The 12 invariants (normative)

The registry with full text is code: `src/nbb_cp/kernel/invariants.py`.
IDs are stable and citable (INV-1 … INV-12); gate denials and incidents must
reference them. Summary:

| ID | Invariant | Enforced by |
|---|---|---|
| INV-1 | Σ committed ≤ single global cap | `budget.reserve`, `budget_gate`, CAS stores, audit |
| INV-2 | irreversible/spawn ⇒ approved human verdict | `effector_gate`, `lifecycle.transition`, audit |
| INV-3 | kill switch denies everything | `effector_gate` (first check), audit |
| INV-4 | propose/enforce/rule triad; one choke point | `service.execute` is the only execution path |
| INV-5 | append-only hash-chained ledger | `events.verify_chain`, stores, audit |
| INV-6 | spawn propose-only, depth ≤ 1, prospective σ ≤ 1 | `spawn_gate` (admission + re-check at execution) |
| INV-7 | fitness reads CONFIRMED/ATTRIBUTED only | `fitness.compute_fitness`, audit |
| INV-8 | self-reports untrusted; external gate re-verifies | `effector_gate` requires verdicts, not claims |
| INV-9 | boundary text is data, never instructions | `ExternalText.quarantined()` delimiters |
| INV-10 | one-rung lifecycle; dormancy reversible; extinction absorbing+human | `lifecycle.transition` |
| INV-11 | no self-editing of law | process rule: invariants/gates change only via human-reviewed commits |
| INV-12 | fail closed | error taxonomy + every gate's default deny |

## 5. Execution semantics

1. `submit_proposal` — admission gate (budget/spawn), ledgered with outcome.
   Denied proposals are ledgered but never indexed for execution.
2. `record_verdict` — human decision, ledgered.
3. `execute` — the **single** execution path: effector gate (kill → human →
   mode), then per-kind execution. GRANT re-checks the cap at execution time
   and lands via CAS retry loop (bounded, then fail). SPAWN re-checks
   prospective σ at execution time (approvals age). In SHADOW mode outcomes
   are ledgered with `shadow: true` and side effects are simulated.
4. `audit` — runs every state-checkable invariant over a `SystemView`; any
   violation is an incident. Clean audit is part of every phase gate.

## 6. Configuration (env)

See `.env.example`. `NBB_GLOBAL_CAP_CENTS` is the one cap (INV-1); every
other figure is derived. `NBB_MODE=shadow` is the default; `live` is
unreachable until the Phase 6 shadow-to-live gate passes. Unknown mode
strings fail closed to shadow.

## 7. Phase roadmap (summary — full orders in CODING_AGENT_PROMPT.md)

| Phase | Week | Theme | Gate (must be green to advance) |
|---|---|---|---|
| 0 | 1 | baseline verification | full suite + import-lint + demo epoch |
| 1 | 2 | real LLM via LangGraph adapter + cassettes | L2 replays of recorded real traffic |
| 2 | 3 | Postgres + Alembic beside sqlite | suite green on BOTH storage legs |
| 3 | 4 | OTel + KPI metrics + /metrics | metrics assertions + audit-on-scrape |
| 4 | 5 | API completion (contract, validation, codes) | contract tests incl. negative paths |
| 5 | 6 | React dashboard + React Flow | e2e smoke against replayed state |
| 6 | 7 | failure attribution + incident drill + shadow-to-live gate | drill passes; live checklist signed |
| 7 | 8 | CI/CD + Docker + DR | pipeline green from clean clone; restore drill |

## 8. Provenance

This spec reconstructs a v0.2 skeleton originally produced in a claude.ai
conversation (never transferred to this machine). Domain law is drawn from
the MycoCardium charter analysis and METABOLIC-GOVERNOR v0.1 corpus
(`docs/ARCHITECTURE_REVIEW.md` maps sources and deviations). Where the
original 33 review findings could not be recovered, their two confirmed bug
classes — optimistic-lock races and TOCTOU windows — are encoded as
regression tests in `tests/l1_adapters/test_stores_concurrency.py` and gate
re-checks in `app/service.py`.
