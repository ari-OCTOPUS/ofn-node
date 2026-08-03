# Skeleton hardening — post-review pass

The v0.2 skeleton baseline was put through a 108-agent adversarial review
(finders → independent verifiers). The review confirmed that the "150 tests
green" baseline was **partly dishonest**: one safety-critical test could not
fail, and the Phase-0 architecture gate had holes. This pass fixes the confirmed
defects and makes the green honest. Everything below is verified against the
source, and the two previously-fake gates were mutation-tested (a broken
implementation now fails them).

## Fixed

| ID | Defect | Invariant | Fix | Regression test |
|----|--------|-----------|-----|-----------------|
| H2 | `record_spend`/`record_revenue` wrote raw `int(...)`, so **negative amounts** (an adversarial LLM self-reporting −tokens, INV-8) poisoned fitness | INV-7, INV-12 | Route every bucket through `Money(...)` → negatives and floats fail closed | `test_negative_{spend,revenue}_rejected_fail_closed`, `test_negative_spend_does_not_poison_fitness` |
| H3 | `record_kill` only ledgered a KILL event; the effector gate read the *external* switch → **POST /kill halted nothing** | INV-3 | `KillSwitch` gains `engage()`/`release()`; `record_kill` engages the real switch (safety before bookkeeping); added `resume()`/`RESUME` + `/resume` endpoint; audit is now interval-based so a released kill stops condemning later work | `test_record_kill_actually_halts_execution`, `test_resume_restores_and_leaves_audit_clean` |
| H4 | `test_racing_reservations_never_exceed_cap` was **tautological** — `committed <= cap` can never fail for any store, so a broken CAS passed | INV-1 | Reworked to a **conservation** assertion: `committed == (landed reservations) × 10`. Mutation-tested: a non-atomic CAS lands 161 reservations but records 1000c → old assert passes, new assert fails | `test_racing_reservations_conserve_every_landed_reservation` |
| H5 | The Phase-0 **import-lint gate had 3 bypasses**: absolute intra-package imports (`import nbb_cp.app`), bare relative imports (`from .. import adapters`), and `glob` vs `rglob` (kernel subpackages unscanned) | architecture gate | Parser now records all three spellings; `kernel_files()` uses `rglob`. Mutation-tested against the review's exact evasion files — the gate now catches all of them | `TestParserCatchesEvasions::*` |
| M4 | `advance_epoch` mutated memory only; `rebuild_projections` reset the epoch from payloads → **epoch silently regressed on restart** (and skewed the sigma window). The soma-rebuild test never advanced the epoch, so it masked this | (soma-is-disposable guarantee, INV-6 window) | `advance_epoch` ledgers an `EPOCH` event; rebuild restores it. The rebuild test now advances epochs and asserts the epoch survives | `test_soma_rebuilds_from_genome` (strengthened) |
| M1, M3 | Concurrency TOCTOU: the SPAWN sigma re-check and the kill sample in `execute()` had check-then-append windows the store-level CAS cannot span | INV-6, INV-3 | A service `RLock` serializes `execute()` / `record_kill()` / `resume()` — the TOCTOU lesson applied at the orchestration layer, not just the budget store | covered by the kill/spawn flow tests under the lock |
| — | `run_audit` had no positive test (only ever asserted `== []`), and the budget store could silently diverge from the ledger (M2 class) with no audit check to catch it | INV-1, INV-3 | Added `_check_budget_reconciliation` (committed must equal Σ GRANT events) and positive service-level audit tests that construct a violating genome | `TestRuntimeAudit::*`, `test_budget_ledger_divergence_flagged_inv1` |

## Deliberately deferred (flagged, not fixed)

These are real but are owned by a later phase or are design decisions, not
oversights. Left as-is so the baseline still reflects the roadmap.

- **H1 — `execute()` idempotency** (one verdict → N executions / N budget commits).
  The prompt schedules idempotency for **Phase 4**. The service `RLock` closes the
  *concurrent* double-execute race, but a sequential replay of `POST
  /proposals/{id}/execute` still re-runs. Fix in Phase 4 by marking
  `ProposalStatus.EXECUTED` and de-indexing on execute.
- **M2 — cross-store atomicity.** The budget CAS and the GRANT append are two
  writes on two SQLite connections; a crash between them diverges committed from
  the ledger. This pass makes the divergence **detectable** (reconciliation
  audit check) but not impossible. True atomicity (single connection / WAL /
  compensation) is a storage-layer decision — natural alongside the Phase 2
  Postgres/Alembic work.
- **M5 — `NBB_MODE=live` boots today.** SPEC §6 says live is unreachable until the
  Phase-6 shadow-to-live gate. Making `from_env` refuse `live` is a **Phase 6**
  deliverable ("Mode.LIVE refuses to boot without the gate"); left reachable so
  that phase has something to build.
- **H6 — CI workflow location.** `.github/workflows/ci.yml` sits under
  `nbb-control-plane/`, not the repo root, so GitHub Actions won't discover it.
  Repo-layout / **Phase 7** CI-CD concern; fix by hoisting `.github/` to the root
  with `defaults.run.working-directory: nbb-control-plane`.
- **LOW:** unbounded `fastapi`/`starlette` extras (TestClient deprecation warning
  is live today — pin an upper bound); `.env.example` says "copy to .env" but
  nothing loads a dotenv; `Organ.vital` defaults `True` so every seeded organ is
  cull-exempt (revisit when the cull loop lands); INV-3 registry/`.env` wording
  ("every gate denies") is stricter than the code (only the effector gate denies).

## Dropped by the review (correctly)

- CAS give-up raising without an INCIDENT — spec §5 sanctions "bounded, then fail".
- `lifecycle.transition` "dead code" / INV-10 — the extinction audit check fires
  fail-closed; an unwired-but-L0-tested kernel primitive is scope, not a bug.
