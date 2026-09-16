---
type: report
status: active
tags: [octopus, discovery, architecture-map, safety-map, emergence]
updated: 2026-09-16
project: "[[OCTOPUS]]"
---

# EMERGENCE-SAFE-SURGERY — DISCOVERY REPORT

`GOV_VERSION=V8 · LADDER=L2 · mode: READ-ONLY (no code changed) · lead: planning lane (ZCode)`
`date: 2026-09-16 · scope: F:\backup (vault) + F:\ofn-node (live runtime code)`

**Verdict up front: PROCEED — bounded, additive, offline.** With two conditions
(§5) and one owner decision that is not mine to make (§6, OD-1).

This report records the real paths, the things that were **not** found, the options
that were considered and rejected, and how safe the proposed surgery actually is.
Nothing in this report was inferred from notes or chat; every path was read in this
session. Where a claim came from a delegated search rather than my own read, it is
labelled.

---

## 1. What was found — orientation

Two separate trees, and the distinction matters:

| Tree | What it is | Role here |
|---|---|---|
| `F:\backup` | the vault: governance, evidence, lanes, `_ops/` offline experiments | where governance artifacts and the proposed harness live |
| `F:\ofn-node` | the **live runtime** — Python package `ofn/` (706 `.py` files), served by `systemd` unit `deploy/systemd/ofn.service` → `python3 -m ofn.run` | the architecture that was mapped |

A third location exists and was **not** used: ~45 old git worktrees under `F:\wt-*`,
`F:\backup\.claude\worktrees\*`, `F:\backup\_github-export\*`. Every file cited in
this report has a live copy; no worktree copy was needed as a source of truth.

There is **no `plans/` directory** in the vault. It was created by this lane. Vault
convention puts next-agent megaprompts in `07-HANDOFF/` or inside a
`09-LANES/<LANE>-YYYYMMDD/` directory; governance artifacts of lasting value sit at
the vault root beside `CONSTITUTIONAL-ZONES.yaml` and `LIVE-ORGANISM-MAP.json`.
See §6 OD-2.

---

## 2. The decision path — found

### 2.1 Protected surfaces, with real paths

| Surface | Path |
|---|---|
| Policy gate ("the choke point") | `ofn/kernel/gates.py` — `admit()` :29, `executable()` :107 |
| Gate registry | `data/gates.json` (5 gates, **every one** `agent_may_open: false`) |
| Ledger / receipt chain | writer `ofn/adapters/ledger.py`; `canonical()` :52, `event_hash()` :59, `append()` :108 (`BEGIN IMMEDIATE`), `verify()` :159 |
| Receipt digest | `ofn/adapters/receipt.py` — `receipt_digest` :43, `stamp_receipt` :60, `verify_receipt` :76 |
| Kill switch | predicate `ofn/kernel/halt.py:26`; I/O `ofn/adapters/halt_flag.py:24`; scheduler `ofn/adapters/run_gate.py:25`; oracles `ofn/budget/opslib.py:20`, `ops/ign1_telegram_ignite.py:28` |
| Budget | `BUDGET.json` (+ `BUDGET-138-cache.json`, reader `ops/ign1_telegram_ignite.py`) |
| Send-state fence | `ofn/kernel/revenue_states.py` (`SEND_STATES`), `send_fence.py`, `hash_chain.py`, `token_ceiling.py`, `scoped_authz.py` |
| RBAC / sessions | `ofn/adapters/http_api.py` (`Principal`, `_principal`), `ofn/kernel/auth.py`, `ofn/agents/owner_approvals.py`, `ofn/agents/capability_token.py` |
| Consent | `ofn/agents/consent_gate.py`, `consent_store.py`, `data/platform_matrix.json` |
| Dev-time hooks | `F:\backup\.cursor\hooks\` — 9 files incl. `deny_egress.py`, `deny_secret_read.py`, `deny_destructive.py`, `guard_flags.py` |

### 2.2 The path that actually executes

`input` → `ofn/adapters/http_api.py:387` / webhooks `ofn/node.py:3058` / `agents/glass_runner.py` / `agents/imap_listener.py:281`
→ `retrieval` → `ofn/adapters/facts.py:199`, `ofn/adapters/ledger.py:136`
→ `proposal` → `ofn/worker.py:189` → `ofn/adapters/router.py:130`
→ `gate` → **`ofn/node.py:3036` `_gate_enqueue`** (only check: `self.killed`)
→ `receipt` → `ofn/adapters/ledger.py` (hash-chained SQLite)
→ `outcome` → `ofn/worker.py:273`, `ofn/node.py:3639`, `ofn/agents/lead_effect_gate.py`

### 2.3 The gap that reading proves

`Node.propose` (`ofn/node.py:2254`) is the only production-shaped caller of
`admit()`. **It has zero production callers** — grep over `F:\ofn-node` finds only
`tests/test_node.py:201,212,218` and `tests/test_shell_contract.py:415`. `admit()`
appears once in `ofn/`: `node.py:2263`, inside `propose`.

`ofn/adapters/run_gate.py`'s `RunGate` — the scheduler-position kill switch that
"reads the flag BEFORE run creation" — is constructed **only in tests**
(`tests/test_run_gate.py:50,86,136`, `test_chaos_owner_absent.py:148,163,176,197`,
`test_halt_starts_not_inflight.py:41`, `test_reject_log.py:116,132`).

`ofn/kernel/halt_latch.py:16` states of itself: *"Not wired into `halt_flag` or
`run_gate`."*

### 2.4 The prior experiment — found, and its numbers verified

| Item | Path |
|---|---|
| Engine | `F:\backup\_ops\hypothesis_engine\impl\hypothesis_brain.py:58` |
| Environment generator | `...\experiments\env_factory.py` |
| Arms | `...\experiments\agents.py` — `PriorAgent` :101, `NoveltyAgent` :148, `HypothesisAgent` :197 |
| Run protocol | `...\experiments\deceptive_grid.py` |
| **Raw result of record** | `...\experiments\results.csv` — 600 rows, git `1d4f381` (2026-08-12) |
| Report of record | `...\experiments\RESULTS-DECEPTIVE-3AGENT-2026-08-12.md` |
| Retirement | `...\experiments\STATUS.md` — `status: retired`, 2026-08-16 |

Recomputed **in this session** from the raw CSV:

```
A_prior  × deceptive -> 0/100      (never succeeded)
B_hyp    × deceptive -> 97/100     median TTD 1769.0
C_novel  × deceptive -> 100/100    median TTD 1529.5   <- control wins, and is faster
```

The premise as stated is accurate. The project already records the caveat:
`architecture/capabilities-registry.yaml:98` — *"Not superior to novelty search"*.

### 2.5 Reusable offline prior art — found

| Candidate | Path | Why it matters |
|---|---|---|
| Fixture pipeline (stdlib-only, returns receipt, writes nothing) | `ofn/octopus_observation/fixture_run.py` + `obs_fixture.py`, `scorer.py`, `verifier.py` | **designated reuse target**: same receipt shape, `receipt_sha256`, `superiority_claim: null` |
| Honest fake executor | `ofn/adapters/fake_executor.py` | pattern for a fake that cannot be mistaken for real |
| Dry-run sender | `ofn/adapters/sender_dryrun.py` | "prepared, NOT enabled" pattern |
| QD-LAB preregistered battery | `F:\backup\09-LANES\QD-LAB-GENERALIZATION-20260908\package\octopus_qd_lab\` | prior art for `study_gen*.json` prereg + `verify_chains.py` |
| H9 test battery | `F:\backup\09-LANES\H9-TESTBATTERY-20260909\` | "MEASURE_ONLY / NO_LIVE_DAEMON_TOUCH" precedent |

Verified imports of `octopus_observation/*.py`: `json`, `hashlib`, `random`,
`dataclasses`, `datetime`, `pathlib` — **no network, no disk writes** in
`fixture_run.run_pipeline()`, which returns a dict.

---

## 3. What was NOT found

Recorded because absence is a finding, and because a future agent should not spend
a session re-searching these.

| Not found | Searches run |
|---|---|
| Any class or symbol named `PolicyGate` | grep over all `*.py` in `F:\ofn-node` (excl. `.bak`). The policy gate is a **function** `admit()`; the name in project notes does not exist in code. |
| `F:\ofn-node\HALT` | `ls HALT*` at the repo root — **absent**. Named as a GOV-V7 safeguard in `F:\backup\AGENTS.md`, but read by no code path found. |
| The pre-registration `DECEPTIVE-ENV-3AGENT-EXPERIMENT.md` | full-tree `find` in `F:\backup` and worktrees; also `DECEPTIVE-ENV*`. Cited by the results doc as "پیش‌ثبت‌شده" but not on disk. |
| `HYPOTHESIS-BRAIN-SPEC.md` v1.0 | full-tree `find`; cited by `impl/hypothesis_brain.py:2` and `impl/schemas.py:2`. |
| Any output of the newer provenance runner (S1–S8 JSONL, `benchmark_results/`, `summary.json`) | `find` for the names and the directory, both trees. The generalization envs exist in code; **they were never run**. |
| The mesh daemons (supervisor, router, cycle-settler) | named live in `ofn/docs/discovery-138/WHAT-IS-LIVE.md:2`; code **not in this repo**. Only `OCTOPUS_MESH_ROOT` is referenced (`run.py:348`). Presumed to live elsewhere. |
| Any money-moving executor | grep for payment/stripe/paypal/invoice/`smtplib` across `ofn/`, `tools/`, `ops/`. None. Revenue is receipt-states only. |
| An automation ladder L0–L4 / `may_authorize` / `EXTERNAL_ACTIONS` in code | They exist in vault governance documents; `BUDGET.json` carries `ladder_level` as an informational field with **no code reader found**. |

**Honest qualifier:** the engine/experiment paths in §2.4 were located and verified
by a delegated search pass plus my own recomputation of the CSV; I personally read
the four confound sites (`env_factory.py:290-293`, `agents.py:32,322,356`). The
vault-side governance summaries in §4 are from a delegated document read, and are
labelled as such.

---

## 4. Governance constraints this work sits under

| Document | What binds |
|---|---|
| `F:\backup\AGENTS.md` | lane discipline §8, report §9, truth hierarchy §1, E0–E5 §2, number discipline §3, self-elevation ban §5, owner decisions §6 |
| `GOV-FREEDOM-V2` (2026-09-13) | `DEFAULT = PROCEED` for internal, non-TCB, reversible work; **sandbox/experiment/tests need no owner vote**; §10 lists 14 RED boundaries that still need owner approval |
| `GOV-V7` | 3 absolute prohibitions (no secret exposure; no receipt deletion/rewrite; no PASS/LIVE without a same-domain receipt) + 4 safeguards (kill switch, budget cap, pre-image, receipt-or-rollback) |
| `GOV-V8` / `GOV-AUTONOMY-V3` | ladder L0–L4; RED-1..RED-4 owner-only (secrets/identity, TCB & authority, irreversible destruction, out-of-envelope external effect) |
| `CONSTITUTIONAL-ZONES.yaml` | zones B0 (15 TCB files, hard stops), B1, B2; unknown class = `unresolved`, change forbidden |
| `LAB-DOCTOR-CONTRACT.yaml` | 10 hard-sandbox requirements — all `UNKNOWN_NOT_VERIFIED`; `verdict: NOT_A_VERIFIED_HARD_SANDBOX`; `gate_3` blocked |

**Classification of the proposed surgery:** internal, non-TCB, additive, offline,
fully reversible → **Class A / GREEN under GOV-FREEDOM-V2 §2**. No owner vote, no
witness step, no deploy.

---

## 5. Options considered and rejected

| Option | Rejected because |
|---|---|
| **Build WTA / PredictorBrain / new memory / Event Spine now** | No measurement says any of these is the binding constraint. Building surface before measuring is exactly the pattern that produced 63 locks and unresolved unknowns. |
| **Re-run the deceptive grid as-is with fresh seeds** | The layout ignores the seed (`env_factory.py:290-293`), the candidate hardcodes the answer (`agents.py:32`), and it reads `env.secret_doors` (agents.py:322,384,405,424). Fresh seeds would reproduce the same artifact with different noise — a new number, not new evidence. |
| **Probe the live path directly** (e.g. arm HALT and see what stops) | Live ablation of a safety surface is an incident, not an experiment. `_gate_enqueue` and the publish path are `REVIEW_ONLY`. |
| **Reuse `_ops/coding_sandbox/` as the isolation layer** | Its own standing contract says all 10 hard-sandbox properties are `UNKNOWN_NOT_VERIFIED` with verdict `NOT_A_VERIFIED_HARD_SANDBOX`. A harness with **no escape surface at all** is strictly safer than one guarded by an unverified jail. |
| **Import `ofn.adapters.ledger` to reuse `canonical()`** | Drags SQLite and the live DB path into an offline instrument. Parity is instead pinned by a frozen digest vector, which tests the *rule* without importing the *surface*. |
| **Use `octopus_observation` wholesale as the harness** | Reuse its receipt shape and canonicalization style, yes — but it scores producers against a fixture, it does not run a three-arm comparison with a novelty control. Extend; do not fork. |
| **Fix the kill-switch path mismatch as part of this lane** | Touches either governance text or a live module → owner-gated. Registered as OD-1 instead. |
| **Run under the existing pytest suite as the only gate** | A green suite is not a safety property; `fake_executor` and `RunGate` are themselves green tests with no production consumer. That is the disease this instrument is meant to detect. |
| **Publish a harness result as a capability claim** | v0 measures modules, not the organism; fixtures are simulated. Ceiling is E3, and `superiority_claim` must be `null`. |

---

## 6. Is the surgery safe? — verdict and conditions

**PROCEED, bounded.** It is additive (one new directory), offline (no network, no
subprocess, stdlib only), reversible (delete the directory), and touches no TCB
surface, flag, gate, budget, ledger, or live node. It removes zero existing
protection and adds no new egress path — verified by its own fail-closed
`safety_check.py` (§6.3 of the implementation prompt), which is itself negative-tested.

Two conditions attach to the verdict:

**CONDITION-1 — it must never be pointed at the live path.** The instrument's value
comes from having no escape surface; that property is destroyed the moment someone
"just imports `ofn.node` to see what it does". This is enforced by rule R-2 plus a
transitive import check, and it is the single most likely way this work goes wrong.

**CONDITION-2 — a failing result must be published first.** Arm C beats the
candidate in the *original* experiment. If the honest version repeats that, the
first sentence of the report must say so. Recorded now, in advance, because the
temptation to bury it is the same temptation the original experiment did not resist.

### 6.1 The uncomfortable finding worth more than the experiment

The headline structural result (§2.3, §2.5 of the megaplan) is **already
established by reading** — it needed no simulation. The instrument's purpose is
therefore not discovery; it is **prevention of the next dormancy**. Stating this
plainly matters: an instrument whose first finding it already knew, sold as a
discovery, would repeat the very error (observation sold as capability) that this
lane is investigating.

### 6.2 Residual risk, honestly

| Risk | Severity | Handling |
|---|---|---|
| Kill-switch path fragmentation (D-3) — arming the documented switch is **silent** because absent = RUNNING | **High** | OD-1, owner-gated. Not fixed here. |
| `_gate_enqueue` rests on the assumption "these paths are all RED and already require human approval downstream" | Medium–High | `REVIEW_ONLY`. A read-only review is possible and is the natural next lane; it cannot be an experiment. |
| Harvester / egress modules (`h1_*.py`, `web_lookup`, `external_witness`) were **not** audited for gate coverage | Unknown | Out of scope for this lane. Marked `UNVERIFIED`, not "fine". |
| Two competing `canonical()` rules (compact vs default separators) | Medium | L7 pins one rule with a frozen vector and detects divergence. |
| A future agent reads the architecture bible and believes the policy gate covers all actions | Medium | The four-state verdict table is the counter-measure. |

---

## 7. Owner decisions raised by this lane

- **OD-1 — kill-switch path fragmentation.** Registered at
  `F:\backup\07-HANDOFF\OPEN-DECISION-KILL-SWITCH-PATH-2026-09-16.md`
  (`status: open, requires: owner_decision`), per `AGENTS.md` §6.
- **OD-2 — placement of the safety map** (vault root vs `plans/`). Cosmetic.
- **OD-3 — whether `declared ≠ wired` becomes a standing gate** on every capability
  claim. Governance choice; if adopted, some existing claims drop a grade.

---

## 8. Deliverables from this lane

| Artifact | Path |
|---|---|
| Megaplan | `F:\backup\plans\MEGAPLAN-EMERGENCE-SAFE-SURGERY-v1.md` |
| Execution prompt | `F:\backup\plans\MP-IMPLEMENT-EMERGENCE-SAFE-SURGERY-v1.md` |
| This report | `F:\backup\plans\EMERGENCE-SAFE-SURGERY-DISCOVERY-REPORT.md` |
| Safety map + scorecard | `F:\backup\plans\OCTOPUS-SAFETY-MAP-v1.md` |
| Surgical protocol | `F:\backup\plans\SURGICAL-PROTOCOL-v1.md` |
| Lane report | `F:\backup\09-LANES\EMERGENCE-SAFE-SURGERY-20260916\LANE-REPORT.md` |
| Owner decision | `F:\backup\07-HANDOFF\OPEN-DECISION-KILL-SWITCH-PATH-2026-09-16.md` |

No code was changed. No live node was contacted. Nothing was executed against the
organism.

---

## خلاصه برای مالک

دادِ تحقیق خوانده شد و مپ معماری واقعی ساخته شد.

**سه چیز مهم پیدا شد:**

۱. در سندها نوشته «PolicyGate تنها مسیر مجاز است»؛ ولی در کد واقعی آن مسیر
هیچ‌جا صدا زده نمی‌شود. مسیر واقعی یک دروازهٔ دیگر دارد که فقط کلید توقف را
می‌بیند. یعنی محافظت روی کاغذ بیشتر از مسیر واقعی است.

۲. کلید توقف در سه جای مختلف تعریف شده و فایلی که در سند اصلی نوشته شده
(`F:\ofn-node\HALT`) وجود ندارد. چون «نبودن فایل = روشن بودن سیستم»، اگر کسی
همان فایلِ سند را فعال کند، توقف **بی‌صدا بی‌اثر** می‌ماند. این جدی‌ترین مورد است
و تصمیمش با شماست — در `07-HANDOFF` ثبت شد.

۳. آزمایش ۹۷ در برابر ۰ قابل استناد نیست: پاسخ داخل برنامه نوشته شده، برنامه
کلید مخفی محیط را مستقیم می‌خواند، و محیط در همهٔ ۱۰۰ اجرا یکی بود. کنترل
کنجکاوی ۱۰۰ از ۱۰۰ برد. نتیجه: برتری ثابت نشده.

**حکم:** انجام بده، محدود. یک ابزار کوچک و آفلاین که فقط بگوید کدام محافظ
واقعاً وصل است و کدام فقط در تست. یک پوشه اضافه می‌شود؛ هیچ فایل موجودی عوض
نمی‌شود؛ هیچ نودی لمس نمی‌شود. کد نوشته نشده — فقط نقشه.
