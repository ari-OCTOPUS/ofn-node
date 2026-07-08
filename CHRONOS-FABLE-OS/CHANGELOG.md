# CHANGELOG — CHRONOS-FABLE OS

_Additive log (INV-12). Newest first. No prior content is deleted; deprecated files move to `_legacy/`._

## 2026-07-08 — Organization pass + audit closure

**Reorganized** the loose synthesis bundle into the canonical 16-folder tree; placed every file at its canonical path; staged the two present primaries under `01_SourceMap/_primaries/`.

**Audit fixes applied** (see `00_Executive/Audit_2026-07-08.md`):
- **F-1** — DOC-B (`OCTOPUS_CHRONO_ARCHITECTURE.md`) recognized as **present**, not missing. MER-1 marked RESOLVED; `DocumentMap.yaml` moved DOC-B to `present_primary`; `Graphs.yaml` L0 and `UnifiedArchitecture.md` L0 un-blocked; `index.yaml` v2 updated.
- **F-2** — `age_tick` rule resolved to `is_human=1` from DOC-B (TINV-3 + schema + §11); downgraded in `ProjectState.md`, `FinalAnswer.md`, `CrossMapping_and_Conflicts.md` (CFL-09) from "needs file" to "operator ratification only".
- **F-3** — `Graphs.yaml` dependency-graph layer numbers made canonical (Doctor=L7, Guards=L8, Business=L9, Research=L10, Observability=L13); `critical_path` fixed to `L13-checkpoint → L7`.
- **F-4** — "14 layers" corrected to "15 (14 numbered + Lp)" in `UnifiedArchitecture.md`; `index.yaml` v2 notes it.
- **F-6** — CFL-03 isolation given a concrete `[EST]` design (`08_Safety/IsolationModel.md`); cross-referenced from `CrossMapping_and_Conflicts.md`.

**Materialized** the Part-B files that were claimed but absent:
`08_Safety/SafetyModel.md`, `08_Safety/IsolationModel.md`, `10_Implementation/DataSchemas.sql` (verbatim DOC-B §8), `10_Implementation/DataSchemas.md`, `10_Implementation/EventCatalog_and_APIs.md`, `09_Research/FalsifiableTests.md`, `02_AtomicKnowledge/DOC04_SelfImprovement.md`, `14_DeveloperDocs/CONTRIBUTING.md`, `13_MasterPrompts/MasterSystemPrompt.v2.md`.

**Proposed laws** (pending operator ratification, NOT yet in canonical counts): `INV-17*` structural-isolation, `AP-14*` trust-boundary-fallacy — appended to `04_Patterns/Patterns_AntiPatterns_Invariants.yaml`.

**Deprecated** (not deleted): `MasterSystemPrompt` v1 → `13_MasterPrompts/_legacy/MasterSystemPrompt.v1.md`.

**Still blocked (upgrade hooks live):** SRC-1 (MER-6), Survival-Stack/DOC-A (MER-2), lab-seed JSON (MER-3), EEG data.


## 2026-07-08 — Vault ingest (Phase A of "both")

Connected to the live vault (`F:\backup`). Found several CHRONOS "missing primaries" already in it; ingested additively (originals untouched; snapshots in `01_SourceMap/_primaries/from-vault/` with `PROVENANCE.md`).

- **MER-6 substantially closed:** `07 - Knowledge/Time-Architecture/` (Level A verbatim) supplies DOC-01 (holographic time-under-fear) + DOC-03 (P1..P14 puzzle), the C1..C8 claims, the unified equation, and the **E1..E5 + L/SOC/¼ falsifiers**. Upgraded `09_Research/FalsifiableTests.md` from placeholders to real predictions + refutation conditions. Still open: DOC-04/05/07 verbatim.
- **Bonus (Level A):** `Octopus_Heart_Design_v1.md` → new `08_Safety/HeartDesign_PulseCore.md` (Pulse Core cascade + Awareness Genome + 7 structural invariants + Ring 0–4 + EffectorGate). Strengthens L0 + L8; structural answer to CFL-03.
- **MER-2 assessed, still open:** vault Survival files are the same governance lineage but lack the memory field-set + LiteLLM routing internals.
- Updated `MissingEvidenceRegister.md`, `DocumentMap.yaml`, `index.yaml` additively.


## 2026-07-08 — Operator verdicts + MER-3 close

- **OQ-4 name = `Octopus`** (system/creature). Repo folder kept as CHRONOS-FABLE-OS (theory layer); recorded in ProjectState/index/MANIFEST.
- **Safety ratified:** INV-17 (structural isolation) + AP-14 (trust-boundary fallacy) promoted from proposed → canonical. Counts: invariants 16→17, anti-patterns 13→14.
- **MER-3 CLOSED:** `lab seed data.json` → `09_Research/ExperimentRegistry.md` (3 N=1 experiments; sealed predictions NOT decoded, per the seed's blinding law). `lab_seed_data.json` stored in 09_Research + _primaries.
- **Aging = two-clock model recorded** (ProjectState verdict 4): heart beat-rate drives `experience_rate`/metabolic aging (TINV-6, autonomous); mortality `age_tick` stays human-append (Telegram tap). One operator confirm still owed on whether the mortality root should also be heart-driven (recommendation: no).
- **OQ-1 stasis:** effect/cognition split set as default — enables full Telegram autonomy with tap-only approvals.
