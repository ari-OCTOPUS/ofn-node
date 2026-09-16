---
type: proposal
status: draft
tags: [backlog, implementation, additive, staged, governance, handoff]
created: 2026-07-11
updated: 2026-07-11
created_by: agent
sources:
  - "[[00 - Inbox/system-review-2026-07-11/risk-register]]"
  - "[[06 - Architecture Maps/2027 Standards Base & Backlog]]"
---

# Implementation Backlog — READ-ONLY proposal (2026-07-11)

> **Nothing here is applied.** Every item is additive, flag-gated where behavior-affecting, shadow-first where risky, and rollback-able. "Owner#n" = already in your `2027 Standards Base & Backlog` (I re-rank + add, I don't duplicate). Waves = suggested order, not a schedule. Each item states: *standard/peer anchor · additive change · blast radius · test · risk tier · gate*.

## Wave 0 — Operational (owner-only, do-first, NO code)

- **B0 · Clear git locks + run live hygiene** (closes **R3**). *Standard:* a control plane whose own backup is wedged has no durability guarantee. *Action (yours):* `Remove-Item F:\backup\.git\*.lock`; run `_ops/maintenance/RUN-CLEANUP-2026-07-11.bat`; confirm `git status` sane + a clean push. *Blast radius:* live tree hygiene only. *Risk tier:* **Tier-3 (owner)** — agent is correctly denied `.git` + live-business-state writes. *Gate:* your hands.

## Wave 1 — Security & money (highest value, shadow-first)

| ID | Item | Standard/peer anchor | Additive change | Test | Tier | Gate |
|---|---|---|---|---|---|---|
| **B1** | Fail-closed `HumanAppendGuard` (**R1 / Owner#1**) | `INFER` default-deny (Saltzer-Schroeder / CISA SBD / NIST SA-8(23)) | `strict=False` param + `HH_HUMAN_GUARD_STRICT` env; strict+no-secret → `(False,'fail-closed-no-secret')` at `human_append_guard.py:78-80`. HMAC path untouched, default = today's behavior | unit: strict on/off × secret present/absent; regression: existing guard test 100% | **Tier-3** | your "go" |
| **B2** | Live drawdown kill-switch, shadow-count (**R2 / Owner#4**) | `INFER` circuit-breaker outside trade logic (SEC 15c3-5 / EU AI Act Art.14) | new fn reads same `spike_pct` drawdown; `HH_DRAWDOWN_ENFORCE` off → **log would-halt only** (shadow) before any real HALT | unit: would-halt fires at threshold; live-HALT only when flag on | **Tier-3** | your "go" |

## Wave 2 — Memory & calibration (additive, $0, flag-off)

| ID | Item | Anchor | Additive change | Test | Tier | Gate |
|---|---|---|---|---|---|---|
| **B3** | Episodic→semantic consolidation (**R4 / Owner#7**) | `INFER` Generative Agents (salience) + sleep-time compute | `cortex/consolidate.py`: tail events → recency×importance×relevance → bounded `semantic_memory.jsonl`; **archive-not-delete** raw; flag `CORTEX_CONSOLIDATE` | unit: bounded output, archive preserves, no-op without flag | Tier-2 | notify |
| **B4** | Online calibration probe (**R5 / Owner#5**) | `INFER` externally-graded (Kamoi TACL 2024; Brier/ECE/AURC) | `online_calibration_probe()` in self_model; grade recent claims vs external `outcomes/discoveries.jsonl`; flag `CORTEX_SELF_MONITOR` | unit: Brier computed, abstain-below threshold, no self-grading | Tier-2 | notify |

## Wave 3 — Routing, UI, control-plane completion (new findings)

| ID | Item | Anchor | Additive change | Test | Tier | Gate |
|---|---|---|---|---|---|---|
| **B5** | Dynamic route scorer + decision-record (**#9 dim**) | `INFER` your pasted routing doctrine (complexity/risk/privacy/impact/cost/urgency → route) | additive `score_route(task,ctx)->{tier,reasons}` *alongside* `TASK_TIERS` (static stays as fallback); emit `route.decided` record (task_id/scores/tier/why/est_cost); flag `CORTEX_ROUTE_SCORER` | unit: shallow→local, sensitive→local-redact-first, deep→primary; record shape | Tier-2 | notify |
| **B6** | Complete the single-pane operator UI (**#8 dim**) | `INFER` your pasted control-plane doctrine | additive `/ops` cards: **Execution Board** (queued/running/blocked/awaiting/done/quarantined), **Audit Drawer** (trace/decisions/policy triggers/memory writes), **Human-Guidance Box**. Read-only from existing state; hologram `/` untouched | `t_*` render tests like `test_live_cockpit t_e` | Tier-2 | notify |
| **B7** | Promote Phase-1 telemetry (wire incident/#13 + `HEARTSTATE_SHADOW`) (**R11**) | your own Ph-1 design | flip `HEARTSTATE_SHADOW=1` (telemetry only); wire `enrich=True`/incident into 2-3 event paths | existing `test_phase1_envelope` 9/9 + live /ops render | Tier-2/3 | D4 |

## Wave 4 — Hygiene & quality (low risk)

| ID | Item | Anchor | Additive change | Test | Tier |
|---|---|---|---|---|---|
| **B8** | Split HANDOFF (**R7**) | your own 200-line index cap (§8) | keep last ~5 sessions + wikilinks; **move** older → `_Archive/Logs/HANDOFF-archive-2026.md` | validator green | Tier-2 |
| **B9** | Portable test paths (**R8 / Owner#9**) | cross-platform CI hygiene | `REAL_VAULT / "a" / "b"` in ~20 files; py3.12 f-string fix | suite green on Linux+Windows | Tier-2 |
| **B10** | Lock `price_in/price_out` in budgets.yaml (**R6**) | cost-attribution correctness | add locked prices per role (**your rates**) | governor error-count → 0 | Tier-3 (your numbers) |
| **B11** | Fix `debate` `KeyError:'text'` (**R9**) | correctness | scoped fix once reproduced | regression test | Tier-2 |
| **B12** | Enforce anti-black-box invariants (**R10**) | your pasted doctrine (depth≤2, no write w/o event) | depth counter in workflow harness + event-emit assert; **shadow warn** first | unit: depth>2 warns; unlogged write flagged | Tier-2 |

## Sequencing logic (why this order)

1. **B0 first** — durability before features (a wedged backup makes everything else risky).
2. **B1/B2 next** — they close the only two HIGH *code* risks and reuse each other's fail-closed template (your own doc noted B1 is the reusable pattern for B2).
3. **B3/B4** — cheap, $0, flag-off; pay down the two 🔴 memory/calibration gaps.
4. **B5/B6/B7** — turn the control plane from "governed" to "fully inspectable + steerable" (the intent of your 3 pasted prompts).
5. **B8–B12** — hygiene; low risk, do opportunistically.

Every item ships as: PROPOSE (this doc) → build behind flag → shadow/canary → your approval → promote. No wave auto-promotes.
