# CHRONOS-FABLE OS — Engineering Knowledge Repository

**One-line thesis:** `CHRONOS-FABLE OS = CHRONOS-VAULT (time/trust substrate + cognition) ⊕ Ari OS (governance + personal-state + business + research + worker)`, under a shared DNA of *event-driven · human-anchored · non-destructive · evidence-aware · cost-gated · operator-shaped*.

A single-operator, local-first, safety-governed cognitive/workflow OS: it ingests documents and tasks, runs small sandboxed worker processes that produce **proposals**, and routes anything irreversible or sensitive through **explicit human approval** — with a tamper-evident **event log as the single source of truth**. Built to run on constrained hardware (Orange-Pi class).

## Status — 2026-07-08 (organized + audit-closed)

This tree is the **agent-ready** consolidation of a 14-phase meta-synthesis. It has been reorganized into the canonical 16-folder structure and had the 2026-07-08 audit findings applied. **Read `HANDOFF.md` first**, then `13_MasterPrompts/MasterSystemPrompt.v2.md`.

Key closures this pass: the DOC-B substrate primary is now in-repo (LANGAR DDL, TINV-1..7, pacemaker/phi pseudocode → `10_Implementation/DataSchemas.sql`); `age_tick=is_human` resolved; layer numbering made canonical (L0–L13 + Lp); isolation/injection given a concrete `[EST]` design.

## Layout

```
CHRONOS-FABLE-OS/
  README.md · HANDOFF.md · MANIFEST.md · CHANGELOG.md
  00_Executive/        ProjectState · FinalAnswer · DesignDNA · Audit_2026-07-08
  01_SourceMap/        DocumentMap · MissingEvidenceRegister · _primaries/ (DOC-B, SRC-2)
  02_AtomicKnowledge/  AtomicObjects.core (28) · DOC04_SelfImprovement (PARTIAL)
  03_Primitives/       Primitives (18)
  04_Patterns/         Patterns(12) · AntiPatterns(13) · Invariants(16) · +INV-17*/AP-14* proposed
  05_Graphs/           Concept · Dependency · Execution (numbering canonical)
  06_Architecture/     UnifiedArchitecture (15 layers)
  07_Comparisons/      CrossMapping · Conflicts (10)
  08_Safety/           SafetyModel · IsolationModel (CFL-03)
  09_Research/         FalsifiableTests (qual READY / quant BLOCKED)
  10_Implementation/   DataSchemas.sql · DataSchemas.md · EventCatalog_and_APIs
  11_Agents/           AgentInstructions (10 roles)
  12_Roadmap/          Roadmap (phased, substrate-first)
  13_MasterPrompts/    MasterSystemPrompt.v2 · UnifiedMasterPrompt_and_Data · _legacy/v1
  14_DeveloperDocs/    CONTRIBUTING
  15_MachineReadable/  index.yaml (v2)
  _legacy/             deprecated versions (never deleted — INV-12)
```

## Evidence discipline

Every claim carries an **Evidence Level** (A=primary doc · B=conversation-derived · I=inference; or [SOLID]/[EST]/[INFERRED]/[UNVERIFIED]/[BLOCKED]) and a **Confidence 0–100%**. Nothing is fabricated: blocked items are named in `01_SourceMap/MissingEvidenceRegister.md`, not invented.

## Present primaries vs still-missing

- **In repo:** DOC-B (`OCTOPUS_CHRONO_ARCHITECTURE.md`), SRC-2 (`OCTOPUS_HYBRID_SYNTHESIS.md`).
- **Still missing (upgrade hooks live):** SRC-1 (holds DOC-01..07 verbatim), DOC-A (Survival-Stack), lab-seed JSON, EEG data. See `MANIFEST.md` §Blocked.
