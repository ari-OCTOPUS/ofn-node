# CHRONOS-FABLE OS — PHASES 7+8 DELIVERABLE
# Cross-Domain Mapping · Conflict Detection
# evidence: A=primary | B=conversation | I=inference

## PHASE 7 — CROSS-DOMAIN MAPPING
_How one concept manifests differently across the corpus. Common core → one primitive._

| Concept | Ari OS (DOC-02) | Survival Stack A | Chrono/Hybrid B/C | Π/Seam D | Common core → primitive |
|---|---|---|---|---|---|
| **Memory** | Knowledge Fabric (fable/ext/int); theory/claims split | Vault + falsifier + validity | ledger + evictable ladder | reconsolidation (mismatch) | authoritative-but-decaying + cache → PRIM-02 |
| **Time** | ts on events; Modes | (monthly eval cadence) | HLC + beat + TINV-5 | retro/predictive seam; personal time | logical beats, not wall-clock → PRIM-06 |
| **Guard** | 7 Guards (middleware) | kill-switch/cost-cap/quarantine | TINV-7 effect-gate | 4 walls + eliminability | policy check before effect → PRIM-03 |
| **Human** | verdict/approval | git-merge quarantine | human-append = arrow | clinician gate (Layer 2) | root-of-trust → PRIM-04 |
| **Agent** | specialist agents + Orchestrator | orchestrator-worker | 6 legs + mortal sub-legs | (single subject) | isolated-context worker → PRIM-11 |
| **Reflection** | Critic/Reflection loop | golden-set eval | trace-grader | gap-report | second-pass critique → PRIM-14 |
| **Learning** | Evolution Doctor loop | monthly model swap | anchored trace-grader | reconsolidation | anchored propose→approve → PAT-02/07 |
| **Cost** | energy_cost in priority; Money Guard | $budget/cap | metabolic aging/spawn | added-value (epistemic) | accounted cost on all capability → PRIM-05 |
| **Attention** | (Personal State focus) | routing by verifiability | scheduler by beat | Π precision-weighting | precision on a channel → PRIM-17 |
| **State** | Modes + Personal State Layer | (quarantine states) | stasis | hot vs cool baseline | mode modulates guards → PRIM-13 |
| **Evidence** | Truth Guard | claim confidence + falsifier | 【E】【P】【S】 in SRC-2 | tags + evidence≠derivation | tagged, sourced claims → PRIM-07 |
| **Planning** | Orchestrator routing | routing rules only | scheduler + dynamic spawn | attractor re-sculpt (change≠push) | route + spawn under cost → PAT-05 |
| **Evolution** | propose→test→approve→merge | external eval swap | H-4 anchored | mismatch/reconsolidation | non-destructive anchored change → PAT-02 |
| **Failure** | self-heal (module.failed→RFC) | quarantine | OTP restart + replay | (structural humility) | known-good restore + replay → S-recovery |
| **Registry** | Project/Money/Decision/Risk | (vault index) | (ledger) | reference-data map | canonical indexed objects → PRIM-12 |
| **Tool** | (via workers) | MCP explicit scope | MCP (A2A deferred) | n/a | scoped tool + audit → INV-10 |
| **Boundary** | Non-Destruct Guard, /_legacy | vault | no core fragmentation | source law (theory sacred) | additive-only vault → PRIM-15 |
| **Money** | GOAL-7 fitness; Money Ledger | (cost cap) | (metabolic $) | (n/a) | money_link fitness → PRIM-16 |
| **Identity/Self** | GOAL-3 simulate human; Personal State | (n/a) | (operator worldview) | self-model, minimal/narrative self | operator-model modulates system → Lp |
| **Experiment** | RFC propose-only | golden set | (roadmap exit criteria) | falsifiable tests + eliminability | falsifier-driven test → PRIM-10 |

**Universal edges (DOC-06-confirmed):**
- *Cost is the universal edge* — $ / aging / spawn / added-value all reduce to "no capability without accounted cost."
- *Human-append = git-merge = clinician* — three names, one anti-drift root-of-trust.
- *Falsifier + gap-report + hash-chain* = three layers of truth maintenance (semantic/epistemic/cryptographic).

---

## PHASE 8 — CONFLICT DETECTION
_Registered, not silently resolved. Recommended resolution stated where one exists._

- **CFL-01 — Stasis vs 24/7 Autonomy** `[A, sev: HIGH]`
  - side_a: B/C "human-append = arrow of time" ⇒ operator absence = system coma.
  - side_b: mission requires 24/7 lead-gen / cognition.
  - type: architectural/safety. **Resolution: Effect/Cognition Split (PAT-09)** — irreversible effects block, internal cognition/aging continues bounded. *Unresolved sub-question: OQ-1 canon verdict owed.*

- **CFL-02 — Determinism vs Parallelism (single process)** `[A, sev: MEDIUM]`
  - side_a: B's TINV-5 deterministic replay/audit.
  - side_b: C's dynamic-spawn parallelism.
  - **Resolution: checkpoint FIRST (H-3), then sub-legs (H-1); hard concurrency cap.** (DOC-06 critical insight #3.)

- **CFL-03 — Isolation / injection defense** `[A/I, sev: HIGH]`
  - All four assume single-process/trust-boundary weakness; none solves prompt-injection isolation.
  - type: safety. **Partial resolution: process-level isolation for sub-legs** (best on Orange Pi). *Biggest residual risk; genuinely open.*
  - **UPDATE 2026-07-08 (F-6):** concrete `[EST]` mitigation now in `08_Safety/IsolationModel.md` (seccomp-bpf, cgroups v2, userns, brokered egress, D1–D5). Residual R1 (model-layer injection) + R2 (shared-silicon side-channels) remain — reduced, not solved.

- **CFL-04 — Quantum/metaphor stance** `[A/I, sev: MEDIUM]`
  - side_a: D forbids quantum-as-mechanism (wall 1) & metaphor-as-mechanism.
  - side_b: B casually invokes a "3-regime time" substrate; DOC-01 uses holographic (Ryu-Takayanagi) *as structural metaphor* (C2/C8 flagged ⚠️【S】).
  - type: epistemic. **Resolution: run the eliminability test.** Keep only if the substrate/metaphor is purely descriptive (removing it changes no prediction). Otherwise ⚠️ reject or demote to 【P】.

- **CFL-05 — Memory permanence vs forgetting** `[A, sev: LOW-MED]`
  - side_a: A's authoritative durable vault.
  - side_b: C's mandatory eviction + non-authoritative cache.
  - **Resolution: split roles** — vault authoritative (with validity window), cache evictable & reconstructable from ledger (PAT-04/11). Not truly in conflict once layered.

- **CFL-06 — Central orchestrator vs distributed/event-driven** `[A, sev: LOW]`
  - side_a: DOC-02 event-driven choreography (self-healing, offline-safe).
  - side_b: orchestrator-worker (A/C) topology decision centralized in lead.
  - **Resolution: light orchestrator ON an event bus** — orchestrator reads/writes only via events (DOC-02 P4 explicitly). Hybrid, not exclusive.

- **CFL-07 — Fable as knowledge-source vs Fable as executor** `[B/I, sev: LOW]`
  - side_a: DOC-02 says Fable's own knowledge is "part of system DNA" (Knowledge Fabric source).
  - side_b: Fable is the builder/coder that executes prompts P1–P5.
  - **Resolution: both, cleanly separated** — /knowledge/fable = source; Fable-the-agent = executor bound by Non-Destruct + Evolution Guards. No contradiction if the executor cannot write to source-of-truth (AP-08).

- **CFL-08 — MASTER-BUILD ↔ Playbook / naming / price-ladder** `[B, sev: LOW]`
  - Cross-document inconsistencies flagged in the broader project state (naming, ladders).
  - type: business/organizational. **Resolution: precedence rule** — locked-rules > canonical spec > drafts; register, don't auto-resolve. (Outside AGI-core; tracked for completeness.)

- **CFL-09 — age_tick advancement** `[A, sev: MEDIUM, BLOCKED-detail]`
  - open: advance on every append, or only `is_human=1`?
  - **RESOLVED (2026-07-08): `is_human=1`.** DOC-B (now in repo) locks it: TINV-3 + `langar_ledger.is_human` + §11. No longer file-blocked; awaiting operator ratification (OQ-2).

- **CFL-10 — D's added-value unproven** `[A, sev: MEDIUM]`
  - Π/Seam may be a "translation machine" (AP-12) unless it yields ≥1 novel falsifiable prediction.
  - **Resolution: gate its 【E】 status on a demonstrated added-value prediction; until then adopt D only as the Epistemic Kernel (rulebook), not as a mechanism.**
