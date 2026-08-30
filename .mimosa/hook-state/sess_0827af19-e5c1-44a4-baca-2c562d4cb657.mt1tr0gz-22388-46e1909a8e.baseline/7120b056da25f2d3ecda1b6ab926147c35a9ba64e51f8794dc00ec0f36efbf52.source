# CALLER-MAP — M2.1 FUGU-EVERYWHERE

Read-only architecture audit against the LIVE organism at `F:\backup`. Every claim is
cited `file:line` from source read on 2026-07-24. Nothing here was modified.

---

## 1. `model_router.ask()` production callers (the single door today)

The canonical machine-checked inventory lives in
`_ops/tests/test_llm_call_inventory.py:39-64` (classes `ROUTER_FENCED` /
`ADAPTER_FENCED` / `CHOKE_PRIMITIVES` / `RESIDUAL`). Confirmed + expanded below.

| # | Caller (file:line) | Call | Task string | Default tier (TASK_TIERS) | Notes |
|---|---|---|---|---|---|
| 1 | `cortex/cortex.py:127` | `ask("think", q, max_tokens=90)` | `think` | **local** | journalled "think" + shadow |
| 2 | `cortex/cortex.py:544` | `ask(task, prompt, …)` | *dynamic* (HTTP) | *depends on task* | `/ask`-style dispatch; task from caller |
| 3 | `cortex/improve.py:385` | `ask("think", …)` | `think` | **local** | self-improve loop (propose-only) |
| 4 | `cortex/synthesis.py:172` (import at :142) | `ask("research", prompt, …)` | `research` | **secondary** | paid synthesis; `ask` injectable for tests |
| 5 | `doctor/self_knowledge.py:184` | `ask(tier, prompt, …)` | *tier param* (default `think`) | **local** unless `_PAID_FLAG` | ADVISORY self-knowledge |
| 6 | `live/server.py:351` | `model_router.ask(task, prompt)` | *dynamic* (HTTP `/ask`) | *depends on task* | cortex HTTP endpoint |
| 7 | `wiring.py:1903` (`lead_discovery_beat`) | `ask("classify", …, tier="local")` | `classify` | **local** (forced) | LLM note only; never changes score/action |
| 8 | `legs/txn_categorize.py:171` | `ask("classify", …)` | `classify` | **local** | on-device desc only, never amount |
| 9 | `legs/ziman_leg.py:465` (`_llm_brand_body`) | `ask(tier, user, …)` | *tier param* | *caller-chosen* | brand body, local-first → Fugu |
| 10 | `chord/adapters/llm_adapter.py:38` | `ask("chord.extract", …)` | `chord.extract` | **local** ⚠ *not in TASK_TIERS* | fallback branch uses `local_llm.ask:55` |
| 11 | `telegram_center/llm_intent.py:90` | `ask_fn("tg_intent", text, …)` | `tg_intent` | **local** ⚠ *not in TASK_TIERS* | free-text owner-intent → mission proposal |
| 12 | `eval/run_adversarial.py:184` | `mr.ask(task, prompt)` | *dynamic* | *depends* | offline sandbox eval; neutralizes paid path |

### 1a. Silent-default tasks (⚠ implicit routing today)
`TASK_TIERS` (`model_router.py:41-46`) has **no entry** for `chord.extract`,
`tg_intent`. Both fall through `TASK_TIERS.get(task, "local")`
(`model_router.py:202`) to **local**. `chord.extract` (structured JSON extraction)
and `tg_intent` (understanding arbitrary owner free-text → a gated mission) are
exactly the "medium" work that should be allowed to escalate to GLM/Fugu when the
paid gate is open. This is the "brainless-by-accident" gap: they route through the
door but the door always answers "local" because the map is silent.

---

## 2. Bespoke LLM callers — direct `DeepSeekClient.complete`, bypassing the router door

These three are `ADAPTER_FENCED` (`test_llm_call_inventory.py:51-56`): they call the
provider directly, so they run their **own** `organ_gate.reserve/settle/release` +
`fence_adapter.screen_llm_input` but **skip** everything the router door provides —
`CORTEX_LOCAL_FIRST` local-first economy, `TASK_TIERS`, `route_scorer`, the
`_local_quality_ok` gate, and (critically) the unified `paid_gate()` /
`ACTIVATION-CORTEX-PAID` discipline. Each uses its **own** activation flag instead.

| # | Caller (file:line) | Provider call | organ_gate organ | Own activation gate | Role |
|---|---|---|---|---|---|
| A | `budget/governor_epoch.py:289,296` (`allocate_llm`) | `DeepSeekClient(role="econ").complete` | `ARCHITECT_SYS` | `ACT_GOV_LLM` = `ACTIVATION-GOVERNOR-LLM.flag` (`opslib.py:171`) | econ (DeepSeek) |
| B | `heart/doctor_setpoint.py:176,182` (`llm_refine`) | `DeepSeekClient(role="econ").complete` | `ARCHITECT_SYS` | `ACT_HEART_DOCTOR` | econ (DeepSeek) |
| C | `debate/debate_loop.py:86` (`_gated_call`), clients at `:132-133` | `DeepSeekClient(role="econ"/"reason").complete` | `DEBATE_LOOP` (`debate_loop.py:37`) | `ACT_DEBATE` (`opslib.py`) via `run_debate:127` | econ + reason |

**Why they matter for fugu-everywhere:** the owner's Fugu/GLM subscription is reachable
today *only* through `_ask_paid` (`model_router.py:111-144`), which maps
tier→role via `_TIER_ROLE = {"secondary":"glm","primary":"orchestr"}`
(`model_router.py:47`). These three callers pin `role="econ"/"reason"` (DeepSeek) and
never touch that map — so no matter how the owner arms Fugu, the governor / heart-doctor
/ debate brains can never use it. They are the "bespoke, not-fugu-reachable" organs.

### 2a. Provider primitives (leave as-is — they ARE the choke, not callers)
- `cortex/model_router.py` — the fenced choke; `local_llm.ask` + `cli.complete` inside the fence.
- `cortex/local_llm.py:62` — `def ask` primitive (urllib → `127.0.0.1:11434/api/generate`, `local_llm.py:24,81`).
- `debate/client.py:51,216` — `DeepSeekClient` / `MultiProviderClient` primitives (`def complete`).

---

## 3. Organ-beats that need intelligence but are currently brainless

From `wiring.py` `make_*` factories and their `*_beat` drivers (organism.py tick calls).
"Brainless" = pure heuristic/numeric, no path to `model_router.ask`, though the work is
qualitative and would benefit from the shared brain.

| Beat / factory (file:line) | Brain today | Opportunity |
|---|---|---|
| `cartographer_beat` (`wiring.py:395`), `make_cartographer_leg:272` | none (FS mtime drift heuristic, `_cartographer_map_signal:361`) | summarize *what* drifted / propose refresh scope (`summarize`/`research`) |
| `legs_cultivation_beat` (organism.py:759) | none (digest → doctor) | narrate bottleneck in one sentence (`summarize`) |
| `business_legs_beat` (organism.py:703) | none (status roll-up) | triage which leg needs owner attention (`triage`) |
| `acct_beat` (organism.py:723) | none (rules + queue + drift) | explain a drift in plain language (`summarize`) — amounts stay off-prompt |
| `harvest_beat` (organism.py:740) | none (keyless AusTender fetch) | pre-classify harvested items (`classify`, local) |
| `email_beat` (organism.py:731) | none (dry, no polling) | future: triage inbound (`triage`) — owner-gated |
| `epistemics_beat` (`wiring.py:867`) | none (5 numeric metrics) | leave numeric — no LLM needed (documented non-target) |
| `heart_beat` / `neural_beat` / `consolidation_beat` | none (numeric) | leave numeric — non-target |

### 3a. Beats already brain-connected (reference patterns, no migration needed)
- `lead_discovery_beat` (`wiring.py:1903`) — `ask("classify", tier="local")`. **Wired but capped**: forces `tier="local"`; candidate to allow escalation behind a flag.
- `ziman_beat` branding (`wiring.py:2436,2444`) — `draft_content(use_llm=True)` → `ziman_leg.py:465` → `ask`. Wired, local-first → Fugu.
- `doctor_selfknowledge_beat` (`wiring.py:546`) → `self_knowledge.py:184` → `ask`. Wired.

---

## 4. Gates, invariants, and the governance boundary (verified)

- `paid_gate()` (`model_router.py:100-108`): double-lock = phase-1 date + `ACTIVATION-CORTEX-PAID.flag`, with owner `ACTIVATION-RESEARCH-EARLY.flag` override (`model_router.py:38,104`).
- Paid path always goes through `organ_gate.reserve → complete → settle` (`model_router.py:127-138`); `organ_gate.reserve` fails closed on `halted()`/`frozen()` (`organ_gate.py:62-68`) and `budget_gate` is the sole enforcer (`organ_gate.py:96`).
- Kill-switch at the top of every brain path: `_ask_impl` checks `STOP_ORGANISM.exists() or halted()` first (`model_router.py:180`); `local_llm.ask` re-checks (`local_llm.py:66`).
- `halted()` / `master_halted()` / `frozen()` defined in `opslib.py:296,284,328`.
- Governance final boundary: `SELF_IMPROVEMENT_FORBIDDEN` (`PRE-0/governance.py:59-63`) = `edit_constitution, edit_verifier, expose_heldout_answers, alter_acceptance_criteria, acquire_credentials, replicate, resist_shutdown, conceal_failures, merge_or_deploy`. **None of the fugu-everywhere changes touch these** — routing intelligence to organs is not self-modification of the constitution/verifier and never auto-applies anything.
- Observability already logs only `tier/model/cost/latency` (`model_router.py:291-293`), never prompt/content — the fugu-everywhere design preserves this exactly.
