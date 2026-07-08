# CHRONOS-FABLE OS — PHASE 10 DELIVERABLE: Unified Cognitive Operating System
_The hidden complete system. Architectural evolution, not a merge._
_evidence: A=primary · B=conversation · I=inference (fusion structure = I,88%)_

## Thesis
`CHRONOS-FABLE OS = CHRONOS-VAULT (L0–L8: time/trust substrate + cognition, from
docs A/B/C/D) ⊕ Ari OS (personal + business + research + worker + interface, from
DOC-02/01/07)`, under the six-pillar Design DNA. CHRONOS-VAULT is the **engine
room**; Ari OS is the **operator-facing wrapper**. They share the same DNA, so the
fusion is along natural seams, not a merge of rivals.

Metaphor (from DOC-06): **B = physics (time/trust), A = body (survival/ops),
C = muscles (orchestration), D = nervous-system rulebook (epistemics)** — and Ari
OS adds the **skin & organs** (operator interface, business, personal state).

## Layer stack (15 layers: 14 numbered L0–L13 + the `Lp` modulation layer)
> Each layer: purpose · primitives · key modules · guards · failure mode · maturity.
> Maturity: 🟢 code/spec-ready · 🟡 partial (see MER) · 🔴 speculative.

**L0 · Substrate — Time & Trust** 🟢
- purpose: single total order + arrow of time; all comms via immutable events.
- primitives: Event, Time(HLC), Human Anchor · modules: unified **Event-Bus/LANGAR** (append-only, hash-chain), pacemaker heartbeat, phi-accrual liveness, **TINV-7 effect-gate**.
- guards: Truth Guard · failure: OTP restart from known-good ledger · maturity: 🟢 (SQL schema now available — DOC-B §8; MER-1 closed 2026-07-08).
- fuses: DOC-02 Event Bus ⊕ B/C LANGAR — **decision: one substrate, two views** (business events + causal ledger).

**L1 · Epistemic Kernel** 🟢
- purpose: govern every write/claim. primitives: Evidence Tag, Falsifier.
- modules: tag engine (E/S/P/M/I/R/C/G), eliminability test, evidence≠derivation, **mandatory gap-report**, added-value gate.
- guards: (is itself a guard on knowledge) · failure: untagged write rejected · maturity: 🟢. from DOC-05/D.

**Lp · Personal-State Layer** 🟢
- purpose: model the operator as a "hormonal system" that modulates guards (does NOT decide).
- primitives: State/Mode · inputs: energy/sleep/HRV/mood/consumption (+ DOC-04 8-domain signals).
- outputs → Modes: Normal/Low-Energy/Offline/High-Energy-Guard/Recovery · maturity: 🟢 (signal wiring 🟡). from DOC-02/DOC-04.

**L2 · Model Pool** 🟢
- purpose: hot-swappable engines. modules: frontier / local(Ollama) / paradigm-hedge slot; LiteLLM gateway; learned+rule routing (by verifiability × wrong-step risk).
- guards: cost cap · failure: fall back to local · maturity: 🟢 (routing rules 🟡 MER-2). from A.

**L3 · Agent Orchestration** 🟢
- purpose: coordinate cognition. primitives: Agent/Leg. modules: **light orchestrator on the bus** (never direct-calls), **mortal sub-legs** (isolated context, forked HLC, no ledger write, killed after N beats, tokens billed to parent, hard concurrency cap ~2–3).
- guards: Worker Guard, Autonomy Guard · failure: sub-leg kill; parent continues · maturity: 🟢. fuses C(sub-legs)+A(routing)+DOC-02(orchestrator-on-bus, resolves CFL-06).

**L4 · Memory** 🟡
- purpose: layered truth. modules: **authoritative Vault** {tag, confidence, falsifier, valid_until} (A) ⊕ **two-tier evictable ladder** raw-log→semantic cache, reconstructable (C) ⊕ **reconsolidation** on mismatch (D). Knowledge Fabric is its knowledge face (see L6).
- guards: Non-Destruct · failure: cache rebuild from ledger · maturity: 🟡 (vault fields MER-2). PAT-04/11.

**L5 · Reasoning / World-Model** 🔴
- purpose: anticipation. modules: active-inference/precision(Π) module; anticipation_queue scheduled by beat (not wall-clock); optional world-model hedge.
- maturity: 🔴 speculative — must earn mechanism status via a novel falsifiable prediction (DOC-05 added-value; CFL-10). from D + B#11.

**L6 · Knowledge Fabric** 🟢
- purpose: knowledge as system DNA. modules: /knowledge/fable (builder's own knowledge) + /knowledge/external (world research) + /knowledge/internal (run lessons).
- consumed by L7 · maturity: 🟢. from DOC-02.

**L7 · Evolution Doctor / Reflection** 🟢
- purpose: self-improvement, anchored. pattern PAT-07: mine Fabric+metrics → bottleneck → RFC → sandbox → Critic → **human-append settle** → flagged merge → log lesson.
- primitives: Reflection/Critic, Proposal · guards: **Evolution Guard** (sandbox-only, no auto-merge) · maturity: 🟢. fuses DOC-02 P5 + C H-4 + D gap-report. Closes AP-03 (self-referential loop).

**L8 · Guard / Safety (control plane)** 🟢
- purpose: interpose policy before any effect. modules: the **7 Guards** (Truth/Money/State/Autonomy/Evolution/Worker/Non-Destruct) + **effect/cognition split** (PAT-09) + 5 independent safety layers (kill-switch, cost-cap, TINV-7, human-anchor, epistemic gap-report).
- failure: default-deny → cooldown queue · maturity: 🟢. fuses DOC-02 + all. **Open: isolation/injection (CFL-03) partial.**

**L9 · Business / Money** 🟢
- purpose: fitness = money + speed. modules: project_registry (status/money_status/**money_link**), **priority_score** formula, Money Ledger; DOC-07 revenue blueprints as concrete money_links.
- guards: Money Guard (irreversible-class + cooldown + offline-freeze) · maturity: 🟢. from DOC-01/02/07. Closes AP-11.

**L10 · Research Engine** 🟢
- purpose: bets, not rabbit holes. modules: **Research-Ingest-Template** (INGEST/DERIVE/REGISTER/PROPOSE/GUARD — PAT-08), claims/experiments split, falsifiers, experiment registry.
- guards: RABBIT_HOLE_RISK + max_daily_research_time · maturity: 🟢 (quantitative experiment registry 🟡 MER-3). from DOC-01/03. Closes AP-02.

**L11 · Interface** 🟢
- purpose: operator control. modules: Telegram Control Core (cmd→event); **Re-entry Packet** built from log after Offline.
- maturity: 🟢 (real Telegram wiring is NEXT-2, after guards green). from DOC-02 GOAL-5/8.

**L12 · Worker Layer** 🟢
- purpose: overseas workers. modules: isolated task_packet portal (no canonical/credential/PII).
- guards: Worker Guard · maturity: 🟢. from DOC-02 GOAL-6.

**L13 · Observability / Replay** 🟢
- purpose: debug & audit. modules: per-beat checkpoint + time-travel replay over hash-chain; cost/latency/error metrics; Weekly Evolution Report.
- maturity: 🟢. fuses C(checkpoint)+B(hash-chain)+A(metrics).

## Dependency spine (build order)
`L0 → (L1 ∥ L13-checkpoint) → L4-ladder → L3-sublegs → L7-anchored-doctor → interop`
— exactly the DOC-C / DOC-06 phased roadmap (ship substrate first; no hybrid before Phase 0).

## Feedback loops (5)
heartbeat/liveness · metabolic aging (faster=older) · monthly model-swap eval ·
anchored self-improvement (human-append) · reconsolidation memory update.

## What was DISCARDED (deliberately, per DOC-C/06)
microVM isolation (no hardware) · visual agent builder (industry retreating to code-first) ·
migration to any external framework (would delete the only moat) · A2A interop (deferred until a real external leg exists).

## Residual risks (carried forward)
- **CFL-03 isolation/injection** — only process-level partial fix on constrained HW.
- **L5 reasoning** — speculative until a falsifiable added-value prediction exists.
- **OQ-1 stasis canon** — effect/cognition split recommended, verdict owed.
