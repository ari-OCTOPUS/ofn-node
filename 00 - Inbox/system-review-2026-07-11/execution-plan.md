---
type: proposal
status: active
tags: [plan, execution, parallel, backlog, governance, handoff]
created: 2026-07-11
updated: 2026-07-11
created_by: agent
sources:
  - "[[00 - Inbox/system-review-2026-07-11/implementation-backlog]]"
  - "[[00 - Inbox/system-review-2026-07-11/user-decision-packet]]"
---

# Execution Plan — pinned parallel roadmap (2026-07-11)

> Owner granted broad authority + "some independence" + "build in parallel for you and your agents". This pins the plan, the parallel lanes, and — critically — **the autonomy boundary**: what I execute autonomously vs. what still needs your explicit "go" even under full authority.

## Autonomy boundary (holds even with "اختیار تام")

These stay owner-gated because they protect the project itself, not me:

| Always owner-gated | Why |
|---|---|
| Flip any live flag / ACTIVATION (guard `STRICT`, `HEART_*`, `IGNITION_*_LIVE`, `HEARTSTATE_SHADOW`→live use) | changes live behavior; your shadow→approve→promote doctrine |
| Merge any branch to `master` (production) | production write; also blocked by stale `.git` lock until you clear it |
| Anything touching **money live** (drawdown enforce, budgets prices) | §10 "پول/خارجی fail-closed"; needs your numbers |
| Secrets, genome/ledger, schema keys, `.git`, `settings.json` | hard rails (§0.2/§6/§10); `.git` also blocked technically |
| Destructive delete / overwrite of human notes | §0.1 move-not-delete |

Everything else that is **additive · $0 · flag-off · reversible · tested** → I build autonomously, shadow-first, and hand you the flip.

## The DAG (waves × parallel lanes)

```
WAVE 0 (owner)            WAVE 1 (built/pending flip)      WAVE 2 (autonomous, parallel)        WAVE 3 (needs a gate)
─────────────             ──────────────────────           ────────────────────────            ───────────────────
B0 clear git locks  ──►   B1 fail-closed guard (BUILT ✓)   Lane A: B5 route-scorer   ┐          B2 drawdown (money → owner)
   [YOU]                     b41a27e — flip = D1 [YOU]      Lane B: B4 calib-probe    ├─ me      B7 promote telemetry [D4]
                                                            Lane C: B3 consolidate    ┘          B10 budgets prices [your #s]
                                                            (all NEW modules, flag-off,          merge-to-master [YOU]
                                                             zero edit to existing code)
                                                            then: B6 UI cards, B9 test-portable,
                                                                  B8 HANDOFF split, B12 depth-guard
```

## Lane table (Wave 2 — what I build now, in parallel)

Each is a **NEW standalone module + standalone test**, zero edits to existing files (wiring is a later flag-gated step). This makes them conflict-free (parallel-safe) and maximally additive.

| Lane | Item | New module | What it does | Wire-in later (owner-gated) |
|---|---|---|---|---|
| A | **B5** route-scorer | `_ops/cortex/route_scorer.py` | dynamic score (complexity/risk/privacy/impact/cost/urgency) → tier + decision-record; the doctrine your prompt-3 wants vs today's static `TASK_TIERS` | `model_router.ask()` consults it behind `CORTEX_ROUTE_SCORER` |
| B | **B4** calibration-probe | `_ops/cortex/calibration_probe.py` | externally-graded Brier/AURC over `outcomes/discoveries.jsonl`; abstain-below | `self_model` calls it behind `CORTEX_SELF_MONITOR` |
| C | **B3** consolidate | `_ops/cortex/consolidate.py` | episodic→semantic (recency×importance×relevance), bounded, **archive-not-delete** | `cortex.run_cycle` calls it behind `CORTEX_CONSOLIDATE` |

**Then (sequential, single-file, me):** B6 `/ops` cards (Execution Board + Audit Drawer + Human-Guidance Box), B9 test path portability (~20 files), B8 HANDOFF split (move old → archive), B12 depth-guard (shadow warn).

## Verification gate (every item, non-negotiable)

build → standalone test green → **full suite green (`REAL_VAULT=<worktree>`)** → validators baseline → commit on feature branch. No flag flipped. No merge. I report; you flip/merge.

## What I am doing THIS turn

1. ✅ Pinned this plan + wrote `prompt-pack.md` (reusable subagent prompts).
2. ▶ Launched a **parallel workflow** (Lanes A/B/C) — 3 agents, isolated, each builds its module + test, self-verifies, returns code. I integrate + run the full suite + commit when they land.
3. Left owner-gated items untouched (flip D1, D2 money, merge, B10 prices).

## Your open actions (small, high-leverage)

- **Now:** clear `.git` locks (one-liner in chat) → unblocks merges/backups.
- **When ready:** flip D1 (`HH_HUMAN_GUARD_SHADOW_ALERT=1` → observe → `HH_HUMAN_GUARD_STRICT=1`).
- **Say "go"** on: D2 (drawdown shadow), B7 promote telemetry, B10 budgets prices (need your numbers), merges.
