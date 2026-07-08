# MANIFEST — file map, provenance, and blocked items

_Every file in the tree, where it came from, and its evidence status. Generated 2026-07-08._

## File map

| Path | Origin | Phase | Status |
|---|---|---|---|
| `00_Executive/ProjectState.md` | synthesis | continuity | READY (+F-2 update) |
| `00_Executive/FinalAnswer.md` | synthesis | 14 | READY (+F-2 update) |
| `00_Executive/DesignDNA.md` | synthesis | 9 | READY |
| `00_Executive/Audit_2026-07-08.md` | this session | audit | READY |
| `01_SourceMap/DocumentMap.yaml` | synthesis | 0 | READY (+F-1 update) |
| `01_SourceMap/MissingEvidenceRegister.md` | synthesis | 0 | READY (MER-1 closed) |
| `01_SourceMap/_primaries/OCTOPUS_CHRONO_ARCHITECTURE.md` | **primary DOC-B** | source | **[SOLID] in repo** |
| `01_SourceMap/_primaries/OCTOPUS_HYBRID_SYNTHESIS.md` | **primary SRC-2** | source | **[SOLID] in repo** |
| `02_AtomicKnowledge/AtomicObjects.core.yaml` | synthesis | 1 | READY (28 atoms) |
| `02_AtomicKnowledge/DOC04_SelfImprovement.md` | this session | 1 | PARTIAL (BLOCKED-verbatim MER-6) |
| `03_Primitives/Primitives.yaml` | synthesis | 2 | READY (18) |
| `04_Patterns/Patterns_AntiPatterns_Invariants.yaml` | synthesis | 3-5 | READY (12/13/16 + INV-17*/AP-14* proposed) |
| `05_Graphs/Graphs.yaml` | synthesis | 6 | READY (numbering fixed F-3; dep-graph L2/L4 partial MER-2) |
| `06_Architecture/UnifiedArchitecture.md` | synthesis | 10 | READY (15 layers, F-4) |
| `07_Comparisons/CrossMapping_and_Conflicts.md` | synthesis | 7-8 | READY (+F-2/F-6 updates) |
| `08_Safety/SafetyModel.md` | this session | 8 | READY |
| `08_Safety/IsolationModel.md` | this session (Handoff §5) | 8 | READY(design)/PARTIAL(verify) |
| `09_Research/FalsifiableTests.md` | this session | 9 | qual READY / quant BLOCKED (MER-3) |
| `10_Implementation/DataSchemas.sql` | **DOC-B §8 verbatim** | 10 | READY (L0) / EST (L4+) |
| `10_Implementation/DataSchemas.md` | this session | 10 | READY (annotated) |
| `10_Implementation/EventCatalog_and_APIs.md` | this session | 10 | PARTIAL (APIs EST) |
| `11_Agents/AgentInstructions.md` | synthesis | 12 | READY (10 roles) |
| `12_Roadmap/Roadmap.md` | synthesis | 12 | READY |
| `13_MasterPrompts/MasterSystemPrompt.v2.md` | this session | 13 | READY |
| `13_MasterPrompts/UnifiedMasterPrompt_and_Data.md` | prior session | 13 | reference |
| `13_MasterPrompts/_legacy/MasterSystemPrompt.v1.md` | synthesis | 13 | deprecated (INV-12) |
| `14_DeveloperDocs/CONTRIBUTING.md` | this session | 14 | READY |
| `15_MachineReadable/index.yaml` | this session | 15 | READY (v2) |

## Canonical counts

atoms 28 · primitives 18 · patterns 12 · anti-patterns **14** · invariants **17** · conflicts 10 · agent-roles 10 · layers 15 (14 + Lp). System name = **Octopus** (OQ-4). INV-17/AP-14 ratified 2026-07-08.

## Blocked items (hard evidence walls — do NOT fabricate)

| # | Blocked | Why | Unblock by |
|---|---|---|---|
| 1 | Vault exact full field set | only 4 fields confirmed | upload **Survival-Stack** (DOC-A) → MER-2 |
| 2 | LiteLLM routing table | not in any present artifact | same (DOC-A) → MER-2 |
| 3 | ✅ CLOSED — experiment registry built (`09_Research/ExperimentRegistry.md`) from `lab_seed_data.json`. Only the `rate↔aging` coupling still needs its own telemetry. | — | MER-3 done 2026-07-08 |
| 4 | DOC-03/04/05/07 verbatim atom bodies + the 8 self-improvement domains | SRC-1 not in context | re-supply **SRC-1** → MER-6 |
| 5 | E1/E2 EEG tests | need EEG *data*, not a doc | provide EEG dataset |
| 6 | Ratify INV-17*, AP-14*, system name, OQ-1 stasis, OQ-2 age_tick | operator decisions, not evidence | **operator verdict** |

## Resolved this session (were blocked/stale before)

LANGAR SQL DDL · TINV-1..7 verbatim · pacemaker/phi/F19 pseudocode · `age_tick=is_human` — all closed by the now-present DOC-B (§7/§8/§9/§11).
