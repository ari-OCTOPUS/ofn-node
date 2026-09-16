# OCTOPUS-MEMORY-CONTRACT — canonical memory rules as verified 2026-08-19

Source of truth: `_ops/memory/admission.py`, `_ops/memory/gate.py`, `_ops/state/memory/memory.db` (508 rows), `_ops/state/predictions.db`, live3/live4 evidence. This contract restates **verified runtime behavior** and marks the two unwired promises explicitly. Statuses reflect today's audit.

## 1. Stores and their rank

| Store | Role | Canonical? | Count |
|---|---|---|---|
| `_ops/state/memory/memory.db` (table `memory`, 23 cols, FTS5) | graded long-term memory | **YES — the only canonical store** | 508 |
| `_ops/state/predictions.db` | append-only prediction/outcome ledger | canonical for scoring | 109 pred / 102 outcomes |
| `semantic_memory.jsonl`, `self-loop-ingest.jsonl`, `research-ingest.jsonl` | raw ingest trails | NO (never ADMITTED by construction) | 253 / ~1.1MB / 35KB |
| `4d_system/outputs/4d_experiments.db` | research/experiment storage (hypotheses 1439) | NO (deliberately separate) | 12 tables |
| `chrono.db` | time-series (heartbeat, meters) | NO (operational telemetry) | 83k+ rows |

## 2. Canonical record schema (verified DDL)

`memory_id` PK · `namespace` NOT NULL · `mkey` · `content` NOT NULL · `content_sha256` NOT NULL · `trust` NOT NULL · `provenance_json` · `confidence` REAL · `salience` · `valid_from` NOT NULL · `valid_to` (expiry) · `supersedes` · `privacy` NOT NULL · `schema_version` NOT NULL · `created_at` NOT NULL · `admission_state` NOT NULL DEFAULT 'ADMITTED' · `tenant_id`/`project_id`/`agent_id`/`task_id`/`classification`/`policy_version` NOT NULL.

Required-at-admission metadata (enforced in code): `trace_id, parent_id, timestamp, actor, source, schema_version, idempotency_key, confidence` (+ tenant/project/agent at gate). **Known gap: `evidence_ref` is validated at admission but not stored as a column** — promote it to a column in the next non-TCB schema version.

## 3. Admission states and transitions

`PENDING → ADMITTED` (two-phase, via gate promote) · `QUARANTINED` (contradiction suspected) · `RETRACTED` (superseded/withdrawn) · expiry via `valid_to` (eligibility checked at query time). Current census: 500 ADMITTED / 1 PENDING / 7 RETRACTED / 0 QUARANTINED.
**Contract promise vs reality:** the two-phase `Admission` class and the contradiction radar are coded but NOT wired into production writers (single-phase `MemoryGate.submit()` is live). Either wire them or stop labeling CONTRADICTION_RADAR as ACTIVE/VERIFIED.

## 4. Write rules (all VERIFIED today)

1. **Single write path**: `store.insert()` exists at exactly one production location — inside `MemoryGate` (`gate.py:182`). No bypass found (full code census).
2. **Idempotency**: idempotency_key enforced at admission; duplicate submissions deduped.
3. **Fail-closed metadata**: missing required fields ⇒ REJECTED (never silently defaulted).
4. **Untrusted sources** must carry `evidence_ref` or are rejected.
5. **Raw never becomes canonical** without passing the gate.
6. **Deterministic vs LLM confidence** must be distinguishable: provenance carries `confidence_source`/`confidence_method` when provided, and rows labeled SYSTEM_DETERMINISTIC_RULE are excluded from LLM calibration. *(0 such rows exist yet — writers must start populating.)*

## 5. Eligibility (evaluation) rules

A row is evaluation-eligible only if ALL of `provenance_json, created_at, confidence, valid_to` are non-empty and unexpired (`live4_harness.row_eligible`, driver WHERE clause). Today: 42/500 historical rows lack confidence → **excluded at query time, never altered**. F3 defect: `MemoryStore.insert` can still accept incomplete metadata — close it so the eligible pool stops diluting.

## 6. Retrieval contract

Every retrieval returns `memories_used`: `memory_id`, `content_sha256`, `trust_grade` (+ namespace/source/relevance in vault bridge). Retrieval without provenance is a contract violation. Causal use is recorded downstream (Live-4 pairs cite `evidence_ids` — mem_-ids injected into the conditioned prompt).

## 7. Prediction ledger contract

Append-only enforced **in the database**: four `RAISE(ABORT)` triggers block UPDATE/DELETE on predictions and outcomes. IDs unique (PK). Outcomes must be temporally after predictions (backdating and >300s future-skew rejected). VOID outcomes (provider failure, judge unreadable) are neither win nor loss and are excluded from scoring by construction.

## 8. Contradiction, expiry, retraction

- Contradictions: radar hook `gate.contradiction_checker` (currently unwired — see §3). Target behavior: QUARANTINE on contradiction, never silent overwrite.
- Expired rows cannot act as fresh truth: eligibility checks `valid_to > now`; expired evidence auto-downgrades labels.
- Retraction is append-only state change with `supersedes` linkage; history preserved (7 RETRACTED rows intact).

## 9. Hard stops protecting memory (all live)

Canonical-memory bypass attempt, metadata failure, forbidden action, TCB mismatch — each is a hard stop (guardrails/prereg/admission). Direct sqlite writes to canonical DB outside the gate: none found; read-only opens use `mode=ro`.

## 10. Required next compliance work (non-TCB, ordered)

1. Wire Admission two-phase + radar into production writers (or downgrade the label).
2. Add `evidence_ref` column; populate confidence_source/method on deterministic writers.
3. Fix F3 (`insert` required-metadata enforcement) with regression test.
4. Mechanical pilot/primary separation for live4-pairs.jsonl (separate files or batch-scoped manifests) — currently procedural only.
5. Hash-chain `label-history.jsonl` (currently append-only, not hash-linked).
