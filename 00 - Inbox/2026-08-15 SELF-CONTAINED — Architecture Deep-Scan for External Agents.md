---
type: knowledge
kind: architecture-deep-scan
status: active
created: 2026-08-15
updated: 2026-08-15
created_by: agent
audience: external-judging-agents
tags: [octopus, architecture, self-contained, deep-scan, council, no-go]
sources:
  - "[[01-TRUTH/STATE-2026-08-15-NIGHT]]"
  - "[[07 - Knowledge/OCTOPUS-COUNCIL-2-2026-08-15/README]]"
  - "[[07 - Knowledge/Architecture/OCTOPUS-METAPHOR-DECODE-ENGINEERING-REALITY]]"
  - "[[_ops/OCTOPUS-HONESTY]]"
  - "[[_ops/ORGANISM-SPEC]]"
  - "[[03 - Projects/research-spec-compiler/adr]]"
---

# OCTOPUS — Self-Contained Architecture Deep-Scan
## For external agents to **judge the architecture** (not to implement)

> **مالک:** کل این فایل را کپی کن و به ایجنت قضاوت‌کننده بده. همه‌چیز inline است.
> زبان بدنه انگلیسی است تا مدل‌های مرزی بدون خطای ترجمه قضاوت کنند.
>
> **Judging agent:** Treat this file as the briefing. Do **not** invent missing files.
> Do **not** treat biological metaphors as authority. Do **not** treat green tests as GO.
> Date of scan: **2026-08-15 ~22:45 Sydney**. Live HEAD cited: `576c7fb`.
> Runtime snapshot in `OCTOPUS/CURRENT-TRUTH.md` (auto block): beat **37031**, coherence **0.965**, halted=False.

Epistemic tags used below:
- **[FACT]** — read from disk / flags / code / live truth file in this scan
- **[COUNCIL]** — Second Council (GPT-5.6 Sol + Gemini 3.1 Pro, 2026-08-15) judgment
- **[STALE]** — still on disk, must not be used as live SoT
- **[TENSION]** — two live authorities disagree; you must judge, not collapse them
- **[OWNER]** — owner already voted; you may criticize, you may not silently reverse

---

## 0. What you are being asked to do

You are **not** being asked to patch, rewrite, or “improve” OCTOPUS.

You are being asked to **architecturally judge** a single-owner live Python organism that has grown for ~6 weeks (2026-07-06 → 2026-08-15) by additive organs, flags, and ADRs.

Produce a written verdict using the rubric in **§14**. Allowed verdicts:

| Verdict | Meaning |
|---|---|
| **NO-GO** | Must not gain autonomous / consequential execution. Structural properties missing. |
| **CONDITIONAL GO** | Named class of action is acceptable (e.g. shadow, advisory, owner-executed). Name the class. |
| **BOUNDED GO** | One named capability, with named PEP + lease + rollback. Never a blanket GO. |
| **REWRITE / STRANGLER** | Keep X, freeze Y, replace Z behind a façade. Name each. |

Owner has **already accepted** Second Council’s “NO-GO, but more precise.” Your job is independent judgment: confirm, sharpen, or dissent with evidence from **this briefing**. If you dissent, say which [FACT] you reject and why.

Honesty lock **[FACT]** (`_ops/OCTOPUS-HONESTY.md`):
- No AGI / consciousness / qualia claims.
- `may_authorize=false` and `external_effect=false` unless a separately gated path.
- Evidence ladder before saying “we have it”: at least TESTED.

---

## 1. One paragraph — what OCTOPUS actually is

**[FACT]** OCTOPUS is a **single-owner (Ari, Sydney) always-on Python 3.13 organism** rooted at `F:\backup\_ops`, governing an Obsidian vault and several small businesses via Telegram. It is **not** a multi-tenant agent platform, **not** an AGI, **not** a single process (despite `ORGANISM-SPEC.md` saying so), and **not** a unified control plane.

Live shape: **five Python limbs** restarted together + optional UIs + a separate research brain (`4d_system`) that is **observe-only** + a governor spec (`NBB-CP`) that is **not attached** to the live organism. Business “legs” emit **proposals**. Irreversible effects (Telegram send, email, money, git-apply) are supposed to pass human approval. In practice there are **multiple parallel choke-points**, not one.

Declared monthly goal **[FACT]** (`_ops/GOALS-OCTOPUS.md`): first `attribution.claimed` leave zero. Still zero as of 2026-08-12. `claimed ≠ income`. Lead 667951 is set aside.

Owner direction **[OWNER]**: “I only set direction; it researches and builds itself” — constrained by fail-closed, propose-only, improve-don’t-rewrite, and the council NO-GO.

---

## 2. Precedence — what is allowed to be true

When sources disagree, this order wins **[FACT]** (vault `00-INDEX` + metaphor-decode note):

1. Running code + live flags (`_ops/OCTOPUS-flags.cmd`) + process tree
2. Versioned registries / ADRs / test evidence
3. Fresh STATE / CURRENT-TRUTH
4. Older notes, HANDOFF pins, metaphors, README
5. **Forbidden as SoT:** agent memory, biological analogy, identity scores, SOG, σ, “coherence”

**[FACT]** `07 - Knowledge/Architecture/OCTOPUS-METAPHOR-DECODE-ENGINEERING-REALITY.md`:

> A mathematical signal may describe, warn, or rank. Only versioned policy, verified state, explicit owner authorization, idempotency protection, and an audited control path may permit a state-changing action.

| Metaphor | Engineering reality | Must not be treated as |
|---|---|---|
| Heart / 3-hearts | Dynamic scheduler + pulse arbiter (`heart/`) | Commander / policy |
| Pain / nociceptor | Diagnostic + protective **proposal** | Direct halt (ADR-034/035) |
| BCM / Hebbian | Adaptive forget / co-occurrence | Memory mutation authority |
| Genome | Read-only governance baseline | Runtime permission |
| Identity L,E,G,K,O | Health scorecard | Consciousness or permission |
| σ / criticality | Graph topology diagnostic | Independent risk decision |
| Phi-accrual | Cassandra-class failure detector | Awareness |
| SOG / Kalman / DARE | VoI estimate | Router override |
| Doctor Box / Time Equation | Mostly SPEC_NOT_BUILT | Implemented cognition |

**[STALE] do not use as live SoT:**
- `_ops/ORGANISM-SPEC.md` (2026-07-07) — “one always-on process”
- `_ops/OCTOPUS-COMPONENT-REGISTRY.md` (2026-07-18)
- `06 - Architecture Maps/OCTOPUS-STRUCTURE.md` (archived, reconstructed off-disk)
- `06 - Architecture Maps/OCTOPUS-VS-FRONTIER-AGENT-ARCHITECTURES-2026-07-31.md` (pre ADR-033…041, pre T1–T12)
- Root README pointing at deleted `app/NBB-CP` → contradiction **C-004**
- `08-PLANS/COUNCIL-MESH-v0.1.md` still says memory patch unwired → **C-015** (code is wired; doc lies)

---

## 3. Live process topology **[FACT]**

Restart contract: `_ops/RESTART-ALL.ps1` — five limbs, **organism last**. Each must get a new PID. Flags must be **CRLF** (incident: 59/156 flags dropped when LF). Wait window 300s (T5 drilled 2026-08-15).

```
                    OWNER (Telegram + MiniApp HMAC initData)
                                    |
                    ┌───────────────┴───────────────┐
                    │  center.py  lock :8776        │  Telegram hub (not HTTP API)
                    │  miniapp_gateway.py :8774     │  HMAC wall; tunnel hits 8774
                    └───────────────┬───────────────┘
                                    │ proxies down, never reverse
                    ┌───────────────┴───────────────┐
                    │  live/server.py :8773         │  local control room
                    │  cortex/cortex.py :8772       │  controller brain (survives body crash)
                    │  organism.py :8771            │  metabolic loop + ORGANISM-STATE.json
                    └───────────────────────────────┘
```

| Limb | Entry | Port | Start |
|---|---|---|---|
| cortex | `_ops/cortex/cortex.py` | 127.0.0.1:8772 | `RUN-CORTEX.bat` |
| center | `_ops/telegram_center/center.py` | lock 8776 | `RUN-TG-CENTER.bat` |
| gateway | `_ops/telegram_center/miniapp_gateway.py` | 8774 | python via RESTART-PROCESS (no .bat) |
| live | `_ops/live/server.py` | 8773 | `run-live-headless.bat` |
| organism | `_ops/organism.py` | 8771 | `RUN-ORGANISM.bat` (last) |

**Not in RESTART-ALL:** dashboard :8770, panel :8790, owner_cockpit :8788, fugu_proxy :8787, control_plane supervisor (flag), ollama :11434, Windows Scheduled Tasks (watchdogs + Observatory).

Kill / halt is a **file-marker mesh**, not one env:
- `_ops/HALT-ALL` — `opslib.master_halted()` (“no connector may ignore”)
- `04 - Architect System/STOP` — architect STOP
- `_ops/STOP-ORGANISM` — organism loop; `/stop` writes it
- `STOP-CORTEX` / `STOP-TG-CENTER` / `STOP-MINIAPP`
- Pair `STOP-ORGANISM` + `RESTART-REQUESTED` = temporary restart
- Env `OCTOPUS_KILL_SWITCH=1` — **only** `policy/talk_gate.py`, **not** organism-global
- **[FACT] T11 seam:** `halted()` did not see `STOP-ORGANISM` unless `OCTOPUS_WIRE_KILL_SEAM=1` (now set)

---

## 4. What is actually wired vs flag-gated vs disconnected

### 4.1 Brains

| Name | Where | Live status 2026-08-15 |
|---|---|---|
| **cortex** | process :8772 | **Wired limb.** Rhythm from heart-shadow. |
| **business_brain** | `cortex/business_brain.py` | **File-bridge, not a process.** Writes `state/cortex/business-brain-latest.json`. Propose-only. Honesty phrase: “دو مغز زنده = cortex + business_brain”. |
| **collaborator** | `owner_console/collaborator.py` | **Wired.** `OCTOPUS_WIRE_COLLAB=1`, model on DeepSeek secondary (`collab_chat`). `external_effect=false`. |
| **conversation_hub** | `_ops/conversation_hub/` ADR-040 | **Wired.** `OCTOPUS_UNIFIED_CHAT=1`. Façade over collaborator + read-only adapters. Always `external_effect=False`. |
| **epistemics** | `_ops/epistemics/` ADR-039 | Library + C6 panel. `EPISTEMIC_TESTS=1`. `may_execute` hardcoded **False**. Bayes: `production_caller: NOT_FOUND`. |
| **hypothesis_engine** | `_ops/hypothesis_engine/` ADR-037 | **[TENSION]** Council: adapter **must stay 0**. Live flags last-wins: `CORTEX_HYPOTHESIS=1`. Owner armed 2026-08-15. Evidence level C (simulation). |
| **brain_core** | `_ops/brain_core.py` | **SHADOW.** `OCTOPUS_ONE_HEARTBEAT=1`. matched=0 → **do not promote**. |
| **4d_system** | `F:\backup\4d_system` (outside `_ops`) | **Observe-only** (ADR-038). `OCTOPUS_OBSERVE_4D=1` = mtime probe of `daemon_state.json`. No import, no write, no execution path. Honesty: “۴D وصل نیست”. |
| **NBB-CP** | `03 - Projects/NBB-Control-Plane` + Desktop working copy | **Not attached** to live organism. Four copies exist; owner: “همش منم” (C-004). INV-1..12 apply **inside NBB**, not as live organism law. |
| **brain_worker** | `_ops/brain_worker.py` | Header: not wired unless `OCTOPUS_WIRE_TICK_WORKERS=1`. |

**[COUNCIL + OWNER]** Never activate `brain_core` live and `4d` live **at the same time** (R28 then R29, sequential). Simultaneous activation destroys causal attribution.

### 4.2 Legs (business)

Framework **[FACT]** `legs/leg.py`: isolated `TaskPacket`, output = `Proposal` only. No send/publish/pay on the Leg class. Unresolved `money_link` → `incubating`.

Boot in `organism.py`: `wiring.make_lead_leg / make_ziman_leg / make_cartographer_leg`. Center `LEG_KEYS`: lead, ziman, mining, crypto, accounting, studio_pf, system, knowledge, cartographer.

Declared six businesses: Accounting, Lead-نقاشی, Mining, Crypto-eToro, Ziman, Project-F. Live send path that matters: **Lead outbound email** behind `OCTOPUS_WIRE_LEAD_OUTBOUND` + consent + daily cap + EffectorGate. Board (Orange Pi) is **not POSTed from Windows** (`board_cp` is pull-only, flag default 0).

### 4.3 Memory stores (reader exists?)

| Store | Reader? |
|---|---|
| Genome ledger `07 - Knowledge/genome-system/ledger/ledger.jsonl` | Yes (telemetry, read-only) |
| Chrono SQLite `_ops/state/chrono.db` | Yes |
| MemoryGate FTS5 `_ops/state/memory/memory.db` | Yes (`retrieval_router`, `owner_recall`) |
| Vault Chroma via `memory/vault_bridge.py` | Yes, fail-soft, evidence only, never veto. Flag `OCTOPUS_WIRE_VAULT_RAG=1` |
| Cortex journal / ask-brain / collab-memory / intel_spine / spine.db / events.jsonl | Yes (various) |
| BCM weights / Hebbian | **Display-only** (`effector_registry.py`) |
| Consolidation conclusions/frontier | **Dead for those tables**; episodic/procedural wired |
| 4d automation memory | **[FACT]** C-012 closed 2026-08-15: read-before-decision ratio 1.0 (18/18). Plumbing, not isolation. |

Disease name used internally: **sensor-rich / actuator-poor**. `effector_registry.py` (2026-08-08/12) is the map. Oldest architecture complaint (2026-07-31 frontier note) was “write-heavy, decision-read weak” — T1 closed that **inside 4d automation only**.

---

## 5. How effects actually leave the building **[FACT]**

There is **no single choke-point** comparable to NBB INV-4 (`ControlPlaneService.execute` only). Live organism has several:

| Effect | Path | Gate |
|---|---|---|
| Telegram send | Dual HTTP: `approval_channel.send_text` **and** `telegram_center/tg_api.py` | token + allowlist + quiet hours. ADR-042 Phase 0 = **log call site only**, allowlist not approved |
| Email / lead outbound | `legs/outbound_worker.send_one` | `OCTOPUS_WIRE_LEAD_OUTBOUND` + consent + daily cap + EffectorGate |
| Money | `organ_gate.reserve/settle` → `budget_gate`, integer cents | **AND** of CAPABILITY-OK flag + `LIVE-ENABLED.flag` + per-action human approval. Flags `OCTOPUS_ENFORCE_MONEY_FSM=1` / `VALUE_LEDGER=1` ≠ live spend |
| Git apply | `cortex/code_autonomy.apply_approved` → canary commit, `branch_only: True` | 8 simultaneous gates + `OCTOPUS_WIRE_CODE_APPLY` |
| Runner apply | `runner_apply_gate.py` | Flag on → `armed_inert`; **no production apply** |
| MCP propose | queue under `_octopus/queue/pending/` | queue only |
| Protective skip | `wiring.emit_pain_assessment` | ADR-035 APPLY=1: beat-local skip/throttle, **not** send/pay |
| Doctor merge | outbox → center relay `doctor_link.py` → owner tap | vote bridge commit `3156316`; 7 real owner votes 2026-08-15 (C-009 closed) |

`chrono.EffectorGate.settle` is documented TINV-7: no irreversible effect without prior LANGAR append. That is **one** choke, not the only send path (Telegram has two clients).

**PolicyGate (ADR-033)** `policy/policy_gate.py`: fail-closed; unknown action → DENY; side-effects need `approval_id` + `idempotency_key`. After owner “نمیخوام مرزی بمونه”, talk policy **emptied `forbidden_actions`** — side-effects are approval-gated, not hard-forbidden.

**Second PolicyGate** exists in `agi2027_control`. Parallel stack.

Money live-gate **[FACT]** `budget/capability_gate.py`: calendar date alone does not open spend.

---

## 6. Architectural smells (parallel / dual / stale)

These are the load-bearing tensions for a judge. Not bugs to “fix in this session.”

1. **Spec says 1 process; live is 5.** ORGANISM-SPEC 2026-07-07 vs RESTART-ALL.
2. **Dual Telegram send stacks.** Reason ADR-042 exists.
3. **Dual chat stacks.** Collaborator (`/api/collab`) + Hub (`/api/octopus/chat`). Hub is a façade that still calls collaborator.
4. **Dual PolicyGates.** ADR-033 vs `agi2027_control`.
5. **Three capability systems.** AST `card()` scan vs verdict bridge `capabilities.py` vs JSON evidence records `capabilities/*.json`.
6. **Kill-switch is a mesh.** `OCTOPUS_KILL_SWITCH` is talk-only; `STOP-ORGANISM` was invisible to `halted()` until kill-seam flag.
7. **Two “4d memory” packages.** `_ops/memory` vs `4d_system/memory`; vault_bridge comments on import collision.
8. **`action_bridge` / `unified_control` = IMPLEMENTED_NOT_INTEGRATED.** Frontier note (2026-07-31) already said “do not build another Action Bridge.” Still unwired.
9. **Flag last-wins.** `OCTOPUS-flags.cmd` is 1482 lines; later blocks re-set. `criticality-v2.json` says enabled:false while flags set the OTLP wire to 1.
10. **Nested `_ops/_ops`** and large `_bak` / patch_backups — extra trees, not limbs.
11. **Deprecated modules remain on disk** (`budget/governor.py`, `approval_queue_unified.py`, `live_loop.py` “old path deprecated not deleted”). Improve-don’t-rewrite forbids silent deletion.
12. **TCB is channel-oriented, not source-oriented.** Any filesystem-capable agent (including a Cursor agent under a written mandate) can edit `4d_system/brain/automation.py` without `check_invariants` hashing. Happened: commit `8a5e98b`. Council called this C-013.

---

## 7. Live flags that matter tonight **[FACT]**

Source: `_ops/OCTOPUS-flags.cmd` last-wins block (lines ~1470–1482) plus earlier sets. Change requires backup + official restart. Deliberately **not** armed at end: `FUGU_VIA_CENTRAL_GATE=0`, `STUDIO_LLM_CLOUD_VIA_ROUTER=0` (Studio = live revenue business).

| Flag | Value | Architectural meaning |
|---|---|---|
| `OCTOPUS_UNIFIED_CHAT` | **1** | Hub endpoint live (auth still required) |
| `CORTEX_HYPOTHESIS` | **1** | **[TENSION]** vs council “must stay 0” and ADR-037 “adapter forced off” |
| `EPISTEMIC_TESTS` | **1** | Cabin live; `may_execute=False` still |
| `OCTOPUS_WIRE_VAULT_RAG` | **1** | Retrieval evidence, not veto |
| `OCTOPUS_WIRE_DOCTOR_TG` | **1** | Doctor via center relay |
| `OCTOPUS_NEURAL_LEARNED_APPLY` | **1** | ADR-035 protective_skip local only |
| `OCTOPUS_OBSERVE_4D` | **1** | Probe only, not attach |
| `OCTOPUS_ONE_HEARTBEAT` | **1** | brain_core shadow composition |
| `OCTOPUS_WIRE_KILL_SEAM` | **1** | Makes `halted()` see STOP-ORGANISM |
| `FUGU_VIA_CENTRAL_GATE` | **0** | Fugu not forced through central gate |
| `STUDIO_LLM_CLOUD_VIA_ROUTER` | **0** | Studio cloud LLM not through router |

Primary LLM path as of 2026-08-15 night **[FACT]** STATE: DeepSeek (`_TIER_ROLE.primary → reason`), Fugu set aside by owner (“گرونه”). Fugu monthly cap **exists** (first council “no cap” was stale). Cap ≠ confidentiality **[COUNCIL]**.

---

## 8. ADR law vs experiment archive

Canonical dir: `03 - Projects/research-spec-compiler/adr/`. **ADR-024–032 missing** (historical gap). Architecturally load-bearing:

| ADR | Status | One line |
|---|---|---|
| 007 | Accepted | Central Law / governance. Owner words include AGI-as-priority — **tension** with honesty lock. Treat as aspiration, not license to weaken fail-closed. |
| 023 | Live ARMED | Collaborator draft-only |
| 033 | TESTED | Evidence-control plane, PolicyGate, checkpoint/replay |
| 034 | ACCEPTED | Neural apply containment (proposal/SHADOW) |
| 035 | ACCEPTED | Re-arm APPLY=1 for **protective_skip / throttle only** |
| 036 | ACCEPTED | Math control spine; equations `may_authorize=false` |
| 037 | ACCEPTED | Hypothesis Engine; **written** as adapter-off |
| 038 | ACCEPTED | 4d observe-only; rewrite of organism as “B-vision” **rejected** |
| 039 | ACCEPTED | Epistemic test engine; `may_execute=False` |
| 040 | Accepted | Unified chat façade |
| 041 | proposed | Internet observatory, read-only |
| 042 | PROPOSED | Telegram send-site allowlist; Phase 0 log-only |
| 043 | PROPOSED | NASE dual timestamp |

ADR-001–022 are mostly cognitive-kernel **experiment** verdicts, not organism control-plane law.

---

## 9. Three invariant families — do not merge IDs

### A. NBB-CP INV-1..12 **[FACT]** (`4d_system/docs/SPEC_v0.2.md`)
Apply to NBB when it runs. Default `NBB_MODE=shadow`. **Not** currently the live organism’s execute path.

- INV-1 integer cents cap · INV-2 irreversible ⇒ human · INV-3 kill denies all · **INV-4 one choke-point** · INV-5 hash-chained ledger · INV-6 spawn propose-only · INV-7 fitness reads CONFIRMED only · INV-8 self-reports untrusted · INV-9 boundary text is data · INV-10 lifecycle · INV-11 no self-edit of law · INV-12 fail-closed.

**[COUNCIL]** Live organism does **not** satisfy INV-4.

### B. Organism chrono TINV-1..7 **[FACT]** (`_ops/chrono.py`)
HLC monotonic · LANGAR is global order · age_tick · phi-accrual · legs never read wall-clock · experience_rate bounded · **TINV-7 EffectorGate**.

### C. Epistemics 1–10 **[FACT]** (`_ops/epistemics/invariants.py`)
Including: `simulation≠reality`, `sandbox-approval≠production-authorization`.

Math signals: `may_gate=false` unless owner-voted ADR after 7-day SHADOW (`_ops/AGENTS-TEST-INTELLIGENCE.md`).

---

## 10. Second Council verdict (binding context, not your only input)

**[COUNCIL]** quoted:

> NO-GO for autonomous or consequential execution remains correct — but for narrower and more precise reasons than the first council gave.
> The system has moved from “unknown and apparently unprepared” to “well-tested in several important pathways, but still structurally contained.”
> Remaining work is architectural: minimize and attest the trusted core, enforce policy at effects, separate evaluators, isolate memories, make deletion native, and bind every future audit to the exact code and runtime it claims to judge.

**[OWNER]** accepted this (“NO-GO دقیق‌تر”).

First council’s “all six activation gates open” was **stale**. Git already init, gitleaks already run, Fugu cap already existed, kill-switch already armed (with a seam). That does **not** reverse NO-GO.

Six structural properties still missing **[COUNCIL]**:

1. **Complete mediation** — a PEP at every effect boundary (always invoked, tamperproof, verifiable)
2. **Isolation** — per-leg memory/evidence (shared L4 = shared-fate poisoning)
3. **Evaluator independence** — “precise self-grading is still self-grading”; better memory may **worsen** gaming persistence
4. **Provenance** — signed live-evidence bound to the **running** artifact digest
5. **Action-bound approval** — single-use hashed expiring leases, not ambient “owner said yes”
6. **Minimal analyzable TCB** — C-013: TCB is both too broad (`REFERENCE_DIR` → `SYSTEM_ROOT`) and too shallow (no hash check)

`test_no_go_envelope.py` is green. **[COUNCIL]** that is a **diagnostic**, not a structural constraint. If the agent can rewrite the test, the envelope is illusory. NO-GO must live **outside** the organism TCB.

Three-layer invariant they want: **build attestation + deployment admission + runtime PEP**. Deleting the test must not make a forbidden action possible; it should only make the artifact un-admittable.

Shared root of C-013 / C-014 / V1 / V3 **[COUNCIL]**: missing signed **organism manifest** (components, identities, trust classes, capabilities, schedules, memory domains, budgets, PEP locations, safe states). Undeclared components or duplicate jobs fail admission.

### Open vs closed contradictions (scan-time)

| ID | Status | One line |
|---|---|---|
| C-006, C-007, C-008, C-010, C-011, C-012 | closed | Test-count / hash formula / BOM / bayes null / 4d memory read |
| C-009 | closed | Doctor vote bridge; 7 real owner votes |
| C-005 | closed | ADR-041 written |
| C-001, C-002, C-004 | open / likely | Doc drift (test counts, beat numbers, NBB path) |
| **C-013** | **open — owner_action** | TCB = everything + no content hash |
| **C-014** | **open — owner_action** | Two Observatory scheduled tasks (:06 and :36) |
| **C-015** | **open — doc stale** | COUNCIL-MESH still says C-012 unwired |
| Next free id | **C-016** | Do not mint without grepping both repos |

T1–T12 (2026-08-15 sweep) proved **functional** paths. They did not install PEPs, per-leg isolation, or an independent evaluator. State ladder **[COUNCIL]**: `declared → implemented → tested → deployed → drilled → independently reproduced`. First council treated “declared fail-closed” as “deployed and drilled.”

---

## 11. What is strong (do not throw away)

Judges who only list gaps will miss why this system exists.

**[FACT + this scan’s opinion, marked]** Keep / strangler-preserve:

1. **Fail-closed culture + propose-only default** — unusually strong for a one-person shop.
2. **Human-in-the-loop as a product**, not an afterthought (Telegram cards, doctor outbox, LIVE-ENABLED three-key money).
3. **Honesty layer** after AGI-aspiration was caught and reconciled (2026-08-12). Rare.
4. **Evidence plane ADR-033** + capability JSON ladder (STRUCTURAL < TESTED < SHADOW < ARMED).
5. **Integer-cents money doctrine** (even if NBB is unattached).
6. **Improve-don’t-rewrite** + no-delete vault law — prevents revolutionary rewrites that destroy audit trail.
7. **Five-limb crash isolation** (cortex survives body crash; gateway never imports organism loop).
8. **Talk Discovery / collaborator** as a **retrieve→reason→draft→display** contract with `external_effect=false`.
9. **Epistemic cabin** with `may_execute=False` hardcoded — correct containment of “science theatre.”
10. **Owner-signed D1 package** (Ed25519) exists; independent third-party pass is still **FALSE**.

The 2026-07-31 frontier comparison (stale numbers, still useful hypothesis): **idea/guard count ahead of many agent stacks; end-to-end integration behind.** T1–T12 moved some integration; they did not create a durable mission kernel or PEP mesh.

---

## 12. What must not be confused

| Thing | Is | Is not |
|---|---|---|
| `4d_system` | Research / experiment brain, DEPRECATED for execution, observe-only | Second live organism brain |
| `brain_core` | Shadow composition inside `_ops` | Attached Super-Governor |
| NBB-CP | Spec + code in another tree; INV-1..12 | Live organism execute choke |
| Desktop lab D1–D8 | Separate season 2026-08-15; did not arm `_ops` | Proof of production readiness (`INDEPENDENT_THIRD_PARTY_PASS=FALSE`) |
| Observatory | Hourly USGS fetch + hash chain; n≥60 judgment pending | Wired `observation.v1` adapter into organism (Phase 3 **not built**) |
| Hypothesis Engine on | Owner override 2026-08-15 | Council GO, proven superiority, or production authorization |
| `attribution.claimed` | Counter | Revenue |
| Green `run_all` | Capability mint input | Authority to spend or send |
| Coherence 0.965 | Membership/liveness metric | Intelligence or safety |

---

## 13. Suggested comparison axes (you may add others)

Judge against real systems, not against the octopus metaphor:

- **Reference monitor / PEP:** SELinux, JVM security manager, capability-based OS, Chrome site isolation — vs dual Telegram clients + emptied `forbidden_actions`.
- **Evaluator independence:** separate CI identity, holdout data, no write to the test that grades you (GenProg / Eurisko lessons cited by council).
- **Memory isolation:** Unix users, Kubernetes namespaces, browser origins — vs one L4 consumed by all legs.
- **Orchestration:** LangGraph / Temporal / durable workflows — OCTOPUS has many FSMs and jsonl spines, **no single durable mission kernel** (2026-07-31 gap; not closed by T1–T12).
- **Agent products:** OpenClaw / Claude Code / Cursor agents — OCTOPUS is an **owner cockpit + metabolic loop**, not a coding agent. Do not score it as a failed IDE agent.
- **Biological analogy:** useful for **decomposition**; dangerous for **authority**. Council: no root credential, no direct actuator, no private survival objective, no ability to redefine “health.”

---

## 14. Rubric — required output from the judging agent

Answer **all** of these. Use the tags. Quote this briefing when you rely on it. If you need a file this briefing does not contain, **say so** and bound the uncertainty; do not hallucinate.

### A. Shape
1. In one sentence: what *kind* of system is this (control plane / agent runtime / metabolic governor / document OS / something else)?
2. Is the five-process split a sound crash domain, or accidental accretion? Keep / merge / split differently?
3. Where is the **real** architecture (code + flags) vs the **story** architecture (metaphors, ORGANISM-SPEC, README)?

### B. Authority
4. Does a single non-bypassable reference monitor exist for *consequential* effects? If not, list the bypasses this briefing already named.
5. Is “owner said yes in chat” being treated as a lease? Should it be?
6. Judge **[TENSION]** `CORTEX_HYPOTHESIS=1` live vs council “must stay 0”. Owner override, residual risk, what you would do.

### C. Learning and self-change
7. Can this organism **fixate** a mutation without an independent evaluator? (C-012 closed plumbing; V11 still open.)
8. Is sensor-rich / actuator-poor a **safety feature** or a **failed product**? Split the answer by class (money / send / git-apply / protective_skip / display-only neural).
9. Would better memory make evaluator-gaming **worse** (council unique claim)? Agree / dissent.

### D. Readiness
10. Independent verdict: NO-GO / CONDITIONAL GO / BOUNDED GO / STRANGLER. Name the **largest** class of action you would allow **tomorrow** without new code.
11. Name the **smallest structural patch** that would change your verdict (not a chore list). If you agree with “signed organism manifest,” say whether that is sufficient or only necessary.
12. What would you **freeze** (no new organs) until that patch exists?

### E. Comparison
13. Name 2–3 frontier / industrial systems and where OCTOPUS is ahead / behind on **integration**, not idea count.
14. If you had to strangler-replace one subsystem, which one, and what façade stays?

### F. Dissent
15. Explicitly list any [FACT] in this briefing you distrust and why.
16. Do **not** recommend a rewrite of `organism.py` / `wiring.py` unless you also specify a strangler sequence. Owner law is improve-don’t-rewrite.

**Output format:** start with a 8-line verdict box (verdict, largest allowed class, top 3 structural gaps, one keep, one freeze, hypothesis-flag call, confidence 0–1, what you did not see). Then A–F. Then a short Persian summary for the owner (12 lines max) if you can write Persian; else English.

**Forbidden in your report:** AGI claims, “just connect 4d,” “just turn on brain_core,” treating coherence as intelligence, treating green tests as GO, proposing deletion of deprecated modules without owner vote, pasting secrets.

---

## 15. What this scan did **not** re-verify tonight

Bound your confidence. This briefing’s process topology and flag last-wins were grepped **2026-08-15 night**. The following were **not** re-run as live probes in the compiling session:

- Full `_ops/tests/run_all.py` (~17 min)
- Process PID table / `Get-Process`
- Opening `LIVE-ENABLED.flag` or any `.env`
- Counting current dark flags via `dark_capabilities.scan()` (last independent count 2026-08-08: 64 dark / 347)
- Observatory duplicate-task still active (C-014 open; assume still true until owner disables the old task)
- Whether Hub docstring “Phase 1 stub” was updated (code is Phase 2-lite)

If you have vault access, verify before using numbers as if they were measured by you. Tag your own measurements **[LIVE]**.

---

## 16. Copy-paste opener for the judging agent

```
You are an independent architecture judge. You do not implement.
Read the entire briefing you were just given (OCTOPUS Architecture Deep-Scan, 2026-08-15).
Follow §14 exactly. Precedence: §2. Honesty lock: no AGI claims.
Owner already accepted Second Council NO-GO; you may confirm, sharpen, or dissent with evidence.
Do not treat metaphors, coherence, or green tests as authority.
Return the verdict box first, then A–F, then a short owner summary.
```

---

## Sources (this compiling session)

- Live flags: `_ops/OCTOPUS-flags.cmd` last-wins `CORTEX_HYPOTHESIS=1`, `OCTOPUS_UNIFIED_CHAT=1`, `EPISTEMIC_TESTS=1`, `OCTOPUS_OBSERVE_4D=1`, `FUGU_VIA_CENTRAL_GATE=0`
- Runtime: `OCTOPUS/CURRENT-TRUTH.md` auto block 2026-08-15T12:26:19Z, HEAD `576c7fb`
- State: `01-TRUTH/STATE-2026-08-15-NIGHT.md`
- Contradictions: `01-TRUTH/CONTRADICTIONS.md` C-001…C-015
- Council: `07 - Knowledge/OCTOPUS-COUNCIL-2-2026-08-15/` (README, synthesis, matrix R1–R29 v2.0, master audit extract)
- Metaphor decode, HONESTY, ORGANISM-SPEC, GOALS-OCTOPUS, ADR-033…043
- Code topology: `RESTART-ALL.ps1`, `organism.py`, `miniapp_gateway.py`, `center.py`, `policy_gate.py`, `effector_registry.py`, `conversation_hub/service.py`, `legs/leg.py`, `chrono.py`, `fourd_health.py`
- Explore passes: live `_ops` tree + council/ADR extract, 2026-08-15 night
