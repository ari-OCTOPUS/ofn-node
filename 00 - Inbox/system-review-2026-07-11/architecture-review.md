---
type: report
status: draft
tags: [architecture, review, control-plane, governance, observability, 2027, handoff]
created: 2026-07-11
updated: 2026-07-11
created_by: agent
sources:
  - "[[06 - Architecture Maps/2027 Standards Base & Backlog]]"
  - "[[06 - Architecture Maps/URCP Reconciliation - control-plane on OCTOPUS]]"
  - "[[01 - Dashboard/HANDOFF]]"
  - "code-verified this session: _ops/registry_scan.py, _ops/live/server.py, _ops/cortex/model_router.py, _ops/budget/human_append_guard.py"
---

# Architecture Review — READ-ONLY (2026-07-11)

> **Mode:** READ-ONLY ANALYSIS. Nothing in the codebase was changed. This is a proposal artifact.
> **Evidence discipline:** `FACT` = verified in the live `master` tree (293f511) this session · `INFER` = reasoned from architecture / my training knowledge (cutoff Jan 2026), not fresh web data · `PROPOSAL` = recommended, needs your approval.
> **Scope note:** the production system is `master` @ `293f511` (the live `F:\backup` tree), which already has URCP Phase-0 + Phase-1 merged **plus** the RISK-LADDER + Vault-Operator-v2 work. This worktree (`seven-relationships-wired-949630`, branch `claude/urcp-registry-phase-0-73e6e7` @ eae8699) is *behind* master; the review targets master.

## 0. One-paragraph verdict

`FACT/INFER` — OCTOPUS is a genuinely advanced, self-built biomimetic control plane whose **governance discipline is its strongest asset**: additive-only, shadow-first, flag-gated, propose-only, tamper-evident audit chain, and a hard access-consciousness red line. It is *ahead* of most hobby/solo agent stacks on safety posture and *comparable to* small-team enterprise control planes on registry + risk-tiering + HITL. Its real weaknesses are not design — they are **three unclosed live gaps the owner already identified** (fail-open human-guard, test-only money kill-switch, unbounded memory) plus **operational hygiene drift** (stale git locks, 113 dirty live entries, a 1015-line HANDOFF). None require a rewrite; all are additive/stageable.

## 1. Dimension scorecard (26 dimensions)

🟢 aligned · 🟡 partial · 🔴 gap. "Owner#n" = already in your `2027 Standards Base & Backlog`.

| # | Dimension | Status | Evidence (this session) | Gap / note |
|---|---|---|---|---|
| 1 | Runtime registry / entity inventory | 🟢 | `FACT` registry_scan → 13 entities, unknown_owner 0, unknown_risk 0, conf 0.831 | strongest new layer (URCP Ph-0) |
| 2 | Risk tiering & classification | 🟢 | `FACT` L0–L3 + RISK-LADDER 4-color + `R4-pending` recognition | critical→R4 never auto (correct) |
| 3 | Human-in-the-loop / approval gates | 🟢 | `FACT` auto_approve + approval_channel + ACTIVATION flags | propose-only default |
| 4 | Fail-closed security defaults | 🔴 | `FACT` `human_append_guard.py:78-80` returns `(True,'guard-disabled-passthrough')` | **Owner#1** — is_human forgeable when guard unconfigured |
| 5 | Tamper-evident audit log | 🟢 | `FACT` epistemics/emit.py hash-chain (prev_hash+sha256) | RFC 9162-aligned |
| 6 | Money kill-switch / circuit breaker | 🔴 | `INFER` `spike_pct=25` test-asserted only, no live enforcer | **Owner#4** |
| 7 | Observability / event backbone | 🟢 | `FACT` events.py structured schema + EventEnvelope (Ph-1) + /ops | see UI gaps (#8) |
| 8 | Single-page control center (UI) | 🟡 | `FACT` `/ops` + `/` hologram exist; registry/heart/incident cards | missing Execution Board, Memory Graph, full Audit Drawer (prompt-2 doctrine) |
| 9 | Local-first hybrid routing | 🟡 | `FACT` model_router 3-tier local-first, fail-soft, cost-gated | **static task→tier map**, no dynamic complexity/risk/privacy scoring, no decision-record, no composed hybrid/redact-prepass |
| 10 | Cost tracking / budget governance | 🟡 | `FACT` budgets.yaml + organ_gate reserve/settle + capability_gate (fail-closed) | `INFER` 47 governor errors from unlocked price_in/out |
| 11 | Long-term memory consolidation | 🔴 | `INFER` no episodic→semantic; append-only logs unbounded | **Owner#7** |
| 12 | Memory hygiene / dedup | 🟡 | `FACT` dedup rules in constitution/vault_updater | 113 dirty live entries; HANDOFF 1015 lines |
| 13 | Online self-monitoring / calibration | 🔴 | `INFER` self_model offline/AST only | **Owner#5** (externally-graded probe) |
| 14 | Self-improvement loop (goal-directed) | 🟢 | `FACT`(HANDOFF) goal_directed + part_loops + business_brain, outcome-linked | closed loop, anti-circular |
| 15 | Anti-black-box (delegation depth ≤2) | 🟡 | `INFER` workflows exist; depth≤2 is convention | enforcement not verified |
| 16 | Structured handoff (schema) | 🟡 | `FACT` HANDOFF.md exists but 1015 lines, prose | `handoff-state.json` (this packet) is a schema seed |
| 17 | Explainability / provenance | 🟢 | `FACT` epistemics functional-only + trace_id/agent_id per emit | fact/emerging/hype triage |
| 18 | Reward-hack / self-signal gating | 🟢 | `FACT`(doc) `HEART_W_SHADOW=0` provenance-gated | Skalse-2022 aligned |
| 19 | Access-consciousness red line | 🟢 | `FACT` assert_access_only raises on phenomenal/qualia | principled + enforced |
| 20 | Test safety net | 🟢 | `FACT` suite 108/108 on master; adversarial reviews | 🟡 ~20 win-path tests fail off-Windows (**Owner#9**) |
| 21 | Shadow-first / flag-gated discipline | 🟢 | `FACT` every risky feature shadow→review→approve→promote | exemplary; matches your meta-ask |
| 22 | Incident response | 🟡 | `FACT` Ph-1 Incident record built | not yet wired into event paths (additive/shadow) |
| 23 | Telegram / messaging HITL channel | 🟡 | `INFER` approval_channel + needs_nudge exist | end-to-end Telegram loop not verified live |
| 24 | Git / backup integrity | 🔴 | `INFER`(HANDOFF+memory) stale AV `.git` locks block backups/pushes; 113 dirty | agent denied `.git` writes → owner-only recovery |
| 25 | Architecture-map currency | 🟢 | `FACT` MASTER-ARCHITECTURE, ECOSYSTEM, 2027-Standards, ADR-001, per-subsystem maps | rich; but HANDOFF bloat (#12/#16) |
| 26 | Schema / frontmatter governance | 🟡 | `FACT` validators enforced on curated layer | ~103 pre-existing errors (اونلی‌فنز doc-pkg + scout-digests), out of §11 scope |

**Tally:** 🟢 12 · 🟡 9 · 🔴 5. The 5 reds are the spine of the backlog; 4 of them are already in your own 2027 doc.

## 2. Where you compare well vs the field (`INFER`, knowledge cutoff Jan 2026)

- **Safety posture > typical solo/OSS agent stacks.** Shadow-first + flag-gated + propose-only + tamper-evident log + hard red line is stricter than most single-operator setups and matches patterns enterprise control planes advertise (policy-as-gate, immutable audit, human approval for high-risk).
- **Registry-as-source-of-truth (URCP Ph-0)** is the right primitive and you built it content-free / fail-closed-on-unknown — the correct instinct ("you cannot govern what you cannot see").
- **Cost governance (local-first routing + organ-gated metering)** is more disciplined than most personal agent projects, which route everything to a frontier model.

## 3. Where the field is ahead (`INFER`) → feeds backlog

- **Routing is static, not scored.** 2026 orchestration patterns route on *live* complexity/risk/privacy/cost signals and emit a decision record. You have the tiers + fail-soft; you lack the scorer + the record.
- **Memory lifecycle.** The field standardized episodic→semantic consolidation + salience retrieval + bounded logs; your logs are unbounded and consolidation is unbuilt (Owner#7).
- **Online calibration.** Externally-graded self-monitoring (Brier/ECE/AURC) is the accepted anti-overconfidence primitive; yours is offline (Owner#5).
- **Single-pane operator UX.** The control-plane doctrine you pasted (Execution Board + Memory Graph + Audit Drawer + Human-Guidance Box) is only ~50% present in `/ops`.

## 4. Honest limits of THIS review

- I did **not** re-run the suite or validators this turn (READ-ONLY; the isolated pieces I did verify are cited as `FACT`). Suite 108/108 is `FACT`-from-HANDOFF/memory, not re-verified now.
- The competitive/2027 comparison is `INFER` from training knowledge (cutoff Jan 2026), **not** fresh web research. Your own `2027 Standards Base & Backlog` already did a real 6-pillar web audit; a follow-up web-grounded benchmark is offered as decision **D5** in the decision packet.
- I read 4 modules end-to-end (registry_scan, live/server, model_router, human_append_guard) + your architecture docs; I did **not** read all 235 `_ops/*.py`. Dimension rows marked `INFER` lean on your own docs, not fresh code reads.

→ See `risk-register.md`, `implementation-backlog.md`, `user-decision-packet.md`, `handoff-state.json` in this folder.
