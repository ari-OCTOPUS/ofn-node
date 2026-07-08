# Missing Evidence Register — CHRONOS-FABLE OS

> Maintained per phase. When a primary file becomes available, the linked
> deliverables are upgraded from PARTIAL/BLOCKED → READY and re-extracted.
> Status as of Phase 0→1, 2026-07-08.

## Legend
- **BLOCKED** — impossible to complete correctly without the missing primary.
- **PARTIAL** — can be drafted from a *review/reflection* of the missing doc that
  IS in context, but exact internals must be verified against the original.

---

## MER-1 — DOC B primary: `OCTOPUS_CHRONO_ARCHITECTURE.md`
- **Status:** ✅ RESOLVED (2026-07-08) — file now in repo at `01_SourceMap/_primaries/OCTOPUS_CHRONO_ARCHITECTURE.md`; §7/§8/§9/§11 close every item below. Deliverables upgraded: 02_AtomicKnowledge B-internals, 05_Graphs L0, 10_Implementation/DataSchemas. Prior status was PARTIAL
- **Why needed:** SRC-2 (`OCTOPUS_HYBRID_SYNTHESIS.md`) declares `depends_on: OCTOPUS_CHRONO_ARCHITECTURE.md (design locked)`. That file is the substrate spec.
- **What is currently derivable (Level A/B):** From SRC-2 + DOC-06 review we have the *names and roles* of TINV-2/3/5/6/7, LANGAR hash-chain ledger, HLC-per-agent, pacemaker/heartbeat, phi-accrual liveness, F19 scheduler, `age_tick` / `experience_rate`, OTP doctor restart.
- **What is BLOCKED without it:** complete/verbatim **TINV-1..7 definitions**, the **LANGAR SQL schema**, pacemaker + phi-accrual **pseudocode**, exact `age_tick` advancement rule (open Q: every append vs `is_human=1`).
- **Blocks deliverables:** `02_AtomicKnowledge` (B-internals), `05_Graphs/DependencyGraph`, `10_Implementation/DataSchemas`, `10_Implementation/APIs`.
- **Upgrade trigger:** upload `OCTOPUS_CHRONO_ARCHITECTURE.md`.

## MER-2 — DOC A primary: "Survival Stack"
- **Status:** PARTIAL
- **Why needed:** DOC-06 reviews it (SRC-1:1917-1983) but only in condensed form.
- **Currently derivable:** philosophy (paradigm-agnostic barbell), LiteLLM+Docker+Ollama execution, invalidation-aware vault concept, kill-switch/cost-cap/quarantine governance, golden-set eval.
- **BLOCKED without it:** exact **vault record schema** (`{tag, confidence, falsifier, valid_until}` fields confirmed via DOC-06 but not their full spec), routing-rule table, governance-plane details.
- **Blocks deliverables:** `03_Primitives/Memory` (exact vault fields), `08_Safety` (governance detail), `10_Implementation/DataSchemas`.
- **Upgrade trigger:** upload the Survival Stack source.

## MER-3 — `file 3`: Lab-seed JSON (sealed predictions + falsifiers)
- **Status:** BLOCKED
- **Why needed:** DOC-06 (SRC-1:2327, 2351) names it as the empirical/measurement arm — the N=1 template for validating B's rate↔aging coupling and DOC-01's E1/E2 EEG tests.
- **BLOCKED without it:** the quantitative Π-telemetry experiment registry and the concrete falsification protocol schema.
- **Blocks deliverables:** `09_Research/ExperimentRegistry`, `09_Research/FalsifiableTests` (quantitative layer only — qualitative falsifiers from DOC-01 E1-E3 are READY).
- **Upgrade trigger:** upload the lab-seed JSON.

## MER-4 — DOC D full original
- **Status:** MOSTLY-READY (low impact)
- **Why:** DOC D's essence == the Π/Seam mother-prompt, which IS present at SRC-1:1321-1527 (Level A). Only supplementary framing may be missing.
- **Impact:** minimal; extraction of the Epistemic Kernel can proceed.

## MER-5 — `pasted_text` method files (4.53 KB + 6.13 KB)
- **Status:** READY (not blocking)
- **Why:** their content == the 14-phase method, reconstructed **verbatim** in the conversation (Level B, confidence 98). No upgrade needed.

---

### Rollup
| Missing item | Status | Severity | Deliverables affected |
|---|---|---|---|
| DOC B primary | ✅ RESOLVED (in repo) | — | (was: atoms(B), dependency graph, data schemas, APIs) |
| DOC A primary | PARTIAL | Low-Med | memory primitive, governance, data schemas |
| file 3 (lab-seed) | BLOCKED | Low | experiment registry, quantitative falsifiers |
| DOC D original | MOSTLY-READY | Negligible | — |
| method pasted_text | READY | None | — |

**Net:** No phase is fully blocked. Phases 1–13 can proceed to READY/PARTIAL
outputs; only two narrow arms (B substrate internals, quantitative experiment
registry) carry hard BLOCKED subsets.


---

## STATUS UPDATE 2026-07-08 (vault ingest — found in the live vault, not the upload set)

### MER-6 — DOC-01 + DOC-03 (holographic time / P1..P14 puzzle): ✅ SUBSTANTIALLY CLOSED
Located at `07 - Knowledge/Time-Architecture/` (Level A, sacred verbatim `theory.md` + `experiments.md` + `claims.md` + `MAP.md`; snapshots in `_primaries/from-vault/`). Closes the E1..E5 + L/SOC/¼ falsifiers (see `09_Research/FalsifiableTests.md`) and the C1..C8 claims + unified equation. **Still open:** DOC-04 (8 self-improvement domains), DOC-05 (Π/Seam), DOC-07 (revenue) verbatim bodies — NOT in this area.

### MER-2 — DOC-A (vault field set + LiteLLM routing): STILL OPEN
The vault Survival lineage (`04 - Architect System/L-Survival-v3.md`, `SURVIVAL-ARCHITECTURE.md`) matches DOC-A's **governance** themes (kill-switch/cost-cap/tamper-evident audit/EffectorGate) but does **not** contain the memory-record field set or the LiteLLM routing table. Upgrade trigger unchanged: the original Survival-Stack doc with those internals.

### BONUS — Octopus Heart Design (Level A, in vault root)
`Octopus_Heart_Design_v1.md` → `08_Safety/HeartDesign_PulseCore.md`. Strengthens L0 (pacemaker cascade) + L8 (Ring 0–4, EffectorGate, fail-closed FSM). Not a MER item; net-new safety substance.
