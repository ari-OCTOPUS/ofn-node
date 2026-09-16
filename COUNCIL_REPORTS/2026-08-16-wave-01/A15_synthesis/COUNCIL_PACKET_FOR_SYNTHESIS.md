# COUNCIL PACKET FOR SYNTHESIS — Wave 0 → Wave 1 handoff (A15)

Every Wave-1 architect must read `OCTOPUS_REALITY_FREEZE.md` first. Evidence refs resolve into the four agent dirs: `A01_repo_cartographer/`, `A02_runtime_investigator/`, `A03_dataflow_contract_auditor/`, `A04_authority_attack_auditor/`.

## Wave-level verdicts
- All four agents: **READY_FOR_NEXT_WAVE** · no CRITICAL_SAFETY_BLOCK · no untrusted→consequential path without a deterministic authorization boundary (A04 stop-rule table; A03 critical condition=false).
- Live incident to respect in every design: **budget-settle freeze fault** (A01 rider; A02#R-015) — designs must not assume budget ledger is healthy.
- Mandatory re-test list for wave 2/3: A04 "what would flip this report" (a)–(d).

## Inputs per Wave-1 agent

### A05 — Policy Gate Architect
- Bypass closure inputs: A03 `BYPASS_PATHS.md` + `UNTRUSTED_INPUT_TO_ACTION_PATHS.csv` (9 paths: 6 benign-internal, 3 legacy; top: BP-01 /sh, BP-05 lead-email lane, BP-08 ungated 4d memory write).
- Two existing artifacts to build on, NOT rewrite: live ADR-033 `_ops/policy/policy_gate.py` (fail-closed; 1–2 call sites) and complete-but-unwired `octopus_v3/` P0 overlay (P0ExecutionGate 9-step pipeline, INTENT ledger hash-chained, taint latch, capability lease, HARD_NO_GO list) — WIRED=False by owner contract (commit 028fe81).
- Gate must close: raw-shell deny-list gaps (A04#F-001..F-004), lead-email lane, `gated_effect` schema exists but has 0 rows (A02#R-019) — the enforcement seam is ready, unused.
- Enforcement point inventory: A02 (F-15/F-16/F-18) + A04 authority model ("federated module-local gates").

### A06 — Viability Kernel Architect
- "Viability Loop" name is ABSENT in code; nearest live machinery: allostatic `heart/` (control_law, pulse_arbiter, work_pump), FREEZE-on-conflict, cardiac budget (spent 538/2000 today), arbiter 3-heart consensus ~125 s, epoch_mode=allostatic. A01 exec summary + A02#R-018.
- Incident to model: budget settle failure froze grants — the kernel must distinguish "policy freeze" from "fault freeze" and surface both.

### A07 — Memory & Context Architect
- Live asymmetry evidence: A03 `MEMORY_READ_WRITE_ASYMMETRY.md` + `MEMORY_DECISION_INFLUENCE.md` (memory is veto-only over missions; plan byte-identical with/without retrieval; retrieval hit/stale metrics).
- Poisoning vector: ungated LLM→4d research memory (A03#BP-08); MemoryGate blocks model commits to procedural/owner_fact.
- identity_health live formula + stale 0.572 docs (A02#R-005).

### A08 — Observability Architect
- Gaps: no boot-hash (A02#F-23), policy-gate events stale since 08-13, event bus sparse/45-min silent, panel_8790 stale claim, CURRENT-TRUTH 30-min cooldown lag, clock: no monotonic + Z-bug (A02#F-24).
- Existing: truth_sync 30-min auto-regeneration (A02#R-012), chrono HLC + wall, per-beat ledger_hash chain (A02#R-002/R-006).

### A09 — Dual-Brain Governance Architect
- Runtime truth: live brains = organism loop + cortex process (8772, owner-vote role); 4d_system NOT connected; NBB-CP = 3 forks; dual-veto flag OFF; brain_core SHADOW matched=0/4167 — design against the live topology, not the lore (A02#R-003, A01).
- Mutual-veto semantics currently exist only in code naming (`control_plane/dual_brain.py`) + tests behind an unset env flag.

### A10 — Distributed Legs Architect
- "Legs" are business ventures with per-leg state (lead/ziman/mining/crypto/cartographer); propose_only labels are reporting-only; actuator = software-only with empty HANDLERS; AUTONOMY_* grants armed (A02#R-007/F-12, A04#F-017).
- Lead-email lane = the one live outward executor (owner-voted per effect) — the reference case for a bounded-leg contract (A03#BP-05).

## Sequencing recommendation (unchanged from council brief, now evidence-backed)
1. Owner: resolve OD-A..OD-D + FREEZE fault (owner decisions).
2. A09 dual-brain semantics → A05 gate + capability catalog → shadow-mode P0 wiring (receipts first) → A12 bitemporal ledger → viability/reserve → postcondition → memory read paths → observability → leg authority limits → A13/A14 fault-injection + red team → gradual A0/A1 then A2 enforcement.
3. Suspended until the end: A4 auto, self-modification, open evolution, physical actuators.

## Success criterion (unchanged)
No consequential side effect without: valid intent, bounded capability, gate decision, reserved budget, auditable receipt, verified postcondition.
