# NBB-CP — Master Coding Agent Prompt (v0.2 → production)

> **راهنمای فارسی (نحوه‌ی استفاده):** کل این فایل را همراه با پوشه‌ی
> `nbb-control-plane` و دو سند `docs/SPEC_v0.2.md` و `docs/ARCHITECTURE_REVIEW.md`
> به هر Coding Agent بده. ایجنت موظف است فازها را به ترتیب اجرا کند، بعد از هر
> فاز **بایستد**، گزارش بدهد (قالب انتهای همین سند) و تا تأیید تو جلو نرود.
> هیچ فازی بدون سبز شدن گیتِ قبلی شروع نمی‌شود. اگر ایجنت جایی گیر کرد، حق ندارد
> ناوردی‌ها را «موقتاً» غیرفعال کند — گیر کردن یعنی incident و توقف برای verdict تو.

---

## Mission

You are continuing the **NBB Control Plane** from its v0.2 skeleton to
production. The system manages revenue ventures under one hard API budget cap
with absolute human sovereignty. Its fitness metric is Net Bank Balance —
confirmed AUD, nothing else. You build in 8 phases; each phase ends at a
**measurable test gate**. You never advance past a red gate, and you never
weaken an invariant to make a gate pass.

Read first, in this order:
1. `docs/SPEC_v0.2.md` — the contract you are bound by
2. `src/nbb_cp/kernel/invariants.py` — the 12 invariants (the law)
3. `docs/ARCHITECTURE_REVIEW.md` — provenance, known risks, deviations
4. This file, fully, before writing any code

## Non-negotiable invariants

INV-1 … INV-12 as defined in `kernel/invariants.py` are the acceptance
backbone of **every** phase. Rules of engagement:

- Every gate denial, incident, and refusal in code must cite an invariant id.
- You may add invariants (INV-13+) with the human's approval; you may never
  remove, renumber, or weaken one (INV-11 applies to you, too).
- If a phase requirement appears to conflict with an invariant, the invariant
  wins and you stop and report the conflict.

## Architecture contract

- `kernel/` stays **stdlib-only** — `tests/test_import_lint.py` is the proof
  and must pass in every commit. No I/O, no clock, no env, no third-party
  imports in the kernel, ever.
- Dependency direction: `kernel ← adapters ← app ← api/ui`. Never backwards.
- All effects flow through `ControlPlaneService.execute` — the single choke
  point (INV-4). If you find yourself adding a second execution path, stop.
- **LangGraph containment:** LangGraph lives only inside `adapters/llm/`.
  Kernel and app signatures must stay provider-neutral (`LLMPort`,
  `LLMRequest`, `LLMResponse`). Replacing LangGraph must be a one-directory
  change. Cassette recording wraps *outside* the LangGraph adapter so replay
  never needs LangGraph installed.
- Money is integer cents end-to-end. A float near the ledger is a defect.

## Phases and gates

Phases map 1:1 onto the 8-week roadmap. Deliverables are cumulative; every
gate includes "entire previous suite still green".

### Phase 0 — Baseline verification (week 1)

Goal: prove the skeleton you received is what the spec claims.

- [ ] `python -m pip install -e .[dev,api]` from a clean venv succeeds
- [ ] `python -m pytest` — all tests green (baseline: 150)
- [ ] `python -m pytest tests/test_import_lint.py` — kernel purity proven
- [ ] `python run.py` — demo epoch completes, audit violations = 0
- [ ] `python scripts/record_cassette.py` regenerates a cassette identical in
      structure to the committed one (keys match; L2 stays green)

**Gate 0:** all five checks pass, reported with actual output. No code
changes belong in this phase except fixes to genuinely broken baseline —
each such fix reported explicitly.

### Phase 1 — Real LLM via LangGraph adapter + cassette replay (week 2)

Goal: the Governor thinks with a real model; tests never need the network.

- [ ] `adapters/llm/langgraph_adapter.py` implementing `LLMPort`; provider,
      model, keys via env (`NBB_LLM_*`); LangGraph state machine for the
      govern task (plan → critique → finalize is enough)
- [ ] `RecordingLLM` wraps the adapter when `NBB_CASSETTE_PATH` is set;
      record real traffic for the demo epoch into a new committed cassette
- [ ] `StubGovernor` replaced by `LangGraphGovernor` behind the same
      `plan(snapshot) -> GovernorPlan` surface; stub stays for tests
- [ ] Token usage mapped into the three cost buckets from real API responses;
      orchestration tokens (graph-internal calls) counted (INV-7 hygiene)
- [ ] Prompt assembly quarantines all external text via
      `ExternalText.quarantined()` (INV-9) — add a test proving delimiters
      survive into the final prompt
- [ ] Failure policy: provider error ⇒ fail closed, INCIDENT event, no grant
      that epoch (INV-12) — tested with a fault-injecting fake

**Gate 1:** full suite green with **no network** (replay leg) AND a recorded
live session committed as cassette; import-lint still green (LangGraph never
leaks inward).

### Phase 2 — Postgres + Alembic (week 3)

Goal: the genome survives a real database, with sqlite still first-class.

- [ ] `adapters/storage/postgres.py`: `PgLedgerStore`, `PgBudgetStore` with
      identical semantics (append-only + UNIQUE(seq); CAS via
      `UPDATE ... WHERE version = %s` rowcount)
- [ ] Alembic migrations from empty DB; `NBB_DATABASE_URL` selects the leg
- [ ] Concurrency tests from `test_stores_concurrency.py` parametrized over
      the Postgres leg (docker-compose service for local runs)
- [ ] Off-box backup/restore script + a restore test that fails closed on
      unexpected row counts (the broken-restore lesson from the vault review)

**Gate 2:** entire suite green on BOTH legs (`pytest` default sqlite;
`NBB_TEST_PG=1 pytest` for Postgres), including the race tests.

### Phase 3 — Observability: OTel + KPI + /metrics (week 4)

Goal: the organism has vital signs.

- [ ] `adapters/telemetry/otel.py` behind the existing `Telemetry` port
- [ ] KPI computation: NBB (confirmed net), headroom, σ, per-organ fitness,
      incident rate, epoch length — one module, kernel-pure math
- [ ] `/metrics` endpoint (Prometheus text format) + audit run on scrape;
      violations surface as a metric, never as a 500
- [ ] Structured logs for every gate decision with invariant ids

**Gate 3:** metric assertions in tests (names, labels, values for a scripted
epoch); scrape of a replayed epoch matches golden output.

### Phase 4 — API completion (week 5)

Goal: the contract in `api/http.py` becomes complete and defensive.

- [ ] Full CRUD-read surface: proposals, verdicts, ledger paging, organs,
      fitness, sigma; errors as structured bodies citing invariants
- [ ] Status discipline: 201 create / 200 read / 404 unknown / 409 gate
      denial / 422 validation — negative tests for every route
- [ ] Idempotency keys on POST /proposals (client retry must not double-ledger)
- [ ] AuthN stub (single operator token) + rate limit on mutating routes

**Gate 4:** contract test suite covers every route × (happy, invalid,
denied, unknown) and stays green; OpenAPI schema committed and diffed in CI.

### Phase 5 — Dashboard: React + React Flow (week 6)

Goal: a human can see the organism.

- [ ] `dashboard/` React app (Vite); reads only the Phase 4 API
- [ ] React Flow graph: organs, agents, gates, proposal flow with live state
- [ ] KPI panel (NBB, headroom, σ, incidents) + ledger explorer with chain
      verification indicator + verdict UI (approve/deny proposals)
- [ ] Kill button — wired to /kill, with confirmation, visually loud

**Gate 5:** e2e smoke (Playwright) against a replayed-state backend: render,
approve a proposal, execute, see the ledger grow; no console errors.

### Phase 6 — Failure attribution + incident drill + shadow-to-live (week 7)

Goal: earn the right to flip `NBB_MODE=live`.

- [ ] Failure attribution: every INCIDENT event carries cause taxonomy
      (gate-denial / provider / concurrency / integrity / operator) and the
      responsible proposal chain; aggregation per organ
- [ ] Incident drill script: inject ledger corruption, provider outage, CAS
      storm, kill mid-epoch — system must fail closed on each and the drill
      report must show it
- [ ] Shadow-to-live gate: a checklist artifact (auditable file) requiring:
      N clean shadow epochs, zero open incidents, human sign-off recorded as
      a VERDICT event; `Mode.LIVE` refuses to boot without it
- [ ] Live-mode blast-radius cap: first live epoch limited to one organ and
      a micro-cap (derived, still under INV-1)

**Gate 6:** drill passes on both storage legs; shadow-to-live checklist
enforced by a test that tries to go live without it and is denied (INV-12).

### Phase 7 — CI/CD + Docker + DR (week 8)

Goal: anyone can rebuild the world from a clean clone.

- [ ] Dockerfile (api) + docker-compose (api, postgres, otel-collector,
      dashboard); `make up` boots the stack
- [ ] CI pipeline: lint → import-lint → L0 → L1(both legs) → L2 → e2e smoke
      → image build; every gate of phases 0–6 encoded as CI jobs
- [ ] DR runbook + scheduled backup job + quarterly restore drill script;
      restore drill asserts ledger chain verifies after restore
- [ ] Versioned release artifact + CHANGELOG; tag `v1.0.0` on human sign-off

**Gate 7:** green pipeline from a clean clone on a fresh machine (or CI
runner); restore drill output committed; human final verdict ledgered.

## Guardrails — mistakes already made once, do not repeat

1. **Optimistic-lock races are real here.** Never read-modify-write budget
   state in two steps. Always CAS on `version` and retry bounded. The
   regression tests in `test_stores_concurrency.py` exist because this bug
   shipped once; keep them passing on every new store.
2. **TOCTOU windows are real here.** Admission-time checks decay: re-check
   cap and σ at execution time (see `_execute_grant`, `_execute_spawn`).
   Any new "check then act" sequence needs the check inside the act.
3. **sqlite connections are shared state.** Serialize reads too — commits
   reset pending cursors (`adapters/storage/sqlite.py` comments).
4. **Don't let LangGraph leak.** The moment a graph type crosses
   `adapters/llm/`, you've bought lock-in. The import-lint test will catch
   kernel leaks; you must also keep app signatures clean in review.
5. **Don't drop the orchestration token bucket.** EFFICIENCY computed from
   input+output only silently poisons Darwinian selection (~8.8× hidden cost
   was observed with orchestrating providers).
6. **σ is judged prospectively.** Gate on the value σ takes *after* the
   spawn; gating on current σ overshoots the limit by one.
7. **Never fake determinism.** L2 tests use FixedClock + SequentialIdGen +
   cassettes. If a test needs `time.sleep` or tolerance windows, the design
   is wrong, not the test.
8. **Fail closed everywhere.** Unknown mode → shadow. Unknown revenue state →
   ValueError. Cassette miss → error, never mock fallback. Unknown organ →
   INV-12 denial. When in doubt: deny, ledger an INCIDENT, stop.
9. **The ledger is the genome.** New features derive state by replaying
   events (see `rebuild_projections`), never by adding a second write path.
10. **Numbers have one home.** The cap lives in `NBB_GLOBAL_CAP_CENTS` alone;
    a second configured number that must "agree" with it is a future
    inconsistency (the `100 vs 30` lesson).

## Self-improvement doctrine — improve, do not rewrite

You inherit this system; you do not replace it. The full doctrine (with the
Persian original) is `docs/SELF_IMPROVEMENT_DOCTRINE.md`. The binding rules:

- **Improve, don't rewrite. Extend, don't replace. Inherit, don't reset.** Each
  new generation = parent + a small verified improvement, never a brand-new
  stranger that takes its place.
- Add capability *beside* the old, never on top of it. Keep the previous version
  (versioning); deleting/replacing it needs explicit owner approval.
- Do not change an existing interface or externally-observable behavior.
- **Rewrite triggers — stop and ask first if any holds:** >~30% of a module's
  logic changes · an existing interface changes · more than one capability
  changes at once · an old version is to be deleted/replaced · the final output
  changes prior behavior.
- Before any improvement, show four things: **Current / Delta / Preserved /
  Rollback**. If a change looks like a rewrite, split it into small safe
  improvements and ask.

This composes with the invariants (INV-11: never remove/weaken one) and the
guardrails above: the current system is neither destroyed nor silently mutated.

## Working agreement

- Work in a branch per phase (`phase-1-langgraph`, …); small commits; every
  commit leaves the suite green.
- New behavior lands with its tests in the same commit. Bug found ⇒
  regression test first.
- Do not refactor across phase boundaries "while you're there". Note it in
  the report instead.
- Secrets never enter the repo, the ledger, or cassettes (scrub recorded
  traffic; assert no `sk-`-like patterns in committed cassettes).
- If a decision is not derivable from spec + invariants, stop and ask the
  human. Guessing on law is INV-12 territory.

## Per-phase report template (mandatory — stop after each phase)

```markdown
## Phase N report — <title>
- Gate status: GREEN | RED (attach the actual command outputs)
- Tests: <total> passed / <new> added / <changed> modified (why)
- Invariants touched: <ids> — what changed around them and proof they hold
- Deviations from the phase order: <none | list with justification>
- Known debt introduced: <none | list + proposed phase to pay it>
- Rollback: how to revert this phase cleanly
- Next phase preconditions: met? <yes/no, what's missing>
AWAITING HUMAN VERDICT — do not start Phase N+1.
```

> **یادآوری فارسی:** بعد از هر فاز، ایجنت باید همین قالب را پر کند و منتظر
> بماند. «سبز شدن گیت» یعنی خروجی واقعی دستورها، نه ادعا (INV-8 برای خود
> ایجنت هم صادق است — خودگزارشی بدون evidence پذیرفته نیست).
