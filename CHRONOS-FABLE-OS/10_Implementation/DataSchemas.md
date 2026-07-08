# Data Schemas — annotated (L0 substrate + L4 memory + L8/L9/L13)

_Companion to `DataSchemas.sql`. Provenance and evidence level per table. `[SOLID]` = verbatim from a present primary; `[EST]` = reconstruction to confirm against a missing primary._

## Status

| Group | Tables | Evidence | Source |
|---|---|---|---|
| **L0 chrono substrate** | `heartbeat`, `leg_clock`, `langar_ledger`, `experience_meter`, `duration_marker`, `anticipation_queue` | **[SOLID]** | DOC-B §8 (in repo) |
| **L4 memory** | `memory_vault_item`, `semantic_cache_item` | subset [SOLID] / rest **[EST]** | confirmed {tag,confidence,falsifier,valid_until}; full set → DOC-A (MER-2) |
| **L8/L9/L13** | `guard_decision`, `project`, `checkpoint` | **[EST]** | Master Handoff §6, reconciled to L0 |

> **F-1 / F-7 note (2026-07-08):** the L0 tables were previously `[BLOCKED]` in every prior deliverable. DOC-B is now in the repo, so the LANGAR DDL is exact, not reconstructed. The Master Handoff's `[EST]` `ledger_event` shape is reconciled here to the real `langar_ledger`: the handoff's `settled` flag is **not** a column — settlement is an *action* (`release_gated_effects()` on human append, DOC-B §9), and `event_type` lives on the business-event record (AKO-002), a different table from the ledger.

## Invariants each table enforces

- `langar_ledger.age_tick` + `is_human` ⇒ **INV-01 / TINV-3 / TINV-7** (mortal arrow; only human-append advances age; irreversible effects gate on append). **OQ-2 answer = `is_human=1`.**
- `langar_ledger.prev_hash/hash` ⇒ **INV-05** (append-only, tamper-evident, single total order TINV-2).
- `semantic_cache_item.authoritative = 0` (CHECK) ⇒ **INV-06** (cache is never truth; reconstructable from ledger).
- `memory_vault_item.falsifier / valid_until` ⇒ **PRIM-10 / AP-06** (no memory without invalidation).
- `memory_vault_item.superseded_by` (never DELETE) ⇒ **INV-12** (additive-only).
- `project.money_link` NULL ⇒ status `incubating` ⇒ **INV-14**.
- `leg_clock.state` ∈ {alive,suspected,failed} ⇒ **TINV-4** (phi-accrual liveness, SWIM suspected).
- `anticipation_queue.due_beat` (beats, not wall-clock) ⇒ **INV-04 / TINV-5**.

## Open (needs a missing primary)

- **MER-2 (DOC-A / Survival-Stack):** full `memory_vault_item` field set beyond the confirmed 4; LiteLLM routing table (L2).
- **MER-3 (lab-seed JSON):** quantitative experiment/telemetry tables (L10) — not modeled here; `[BLOCKED]`.
