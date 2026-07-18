# OCTOPUS Deep Connectivity Audit

**Date:** 2026-07-18  
**Root:** `F:\backup`  
**Mode:** READ-ONLY · DEEP-SCAN · PROPOSE-ONLY  
**Auditor:** GLM Octopus Connectivity Auditor  
**No files modified. No tests run. No git mutations. No external sends.**

---

## 1. Executive Verdict

### **UI AND MODULES AHEAD OF EXECUTION**

در ۱۲ خط:

- **بزرگ‌ترین قطع ارتباط:** مغز و سیستم‌عصبی اختاپوس (cortex، model_router، doctor، telemetry، heartbeat) کاملاً زنده و در حال تپیدن است (beat در زمانِ ممیزی در حال پیشرفت بود)، اما **هیچ مسیر اجرایی واقعی از مأموریت تا خروجی بیرونی وجود ندارد**. Mission Registry، Approval Queue و Action Graph به‌خوبی طراحی و تست شده‌اند، ولی `mission_runner` وجود ندارد و `ms:test` / `ms:review` در center.py فقط `add_note` می‌زنند — کدی (در `center.py:959-962`) به‌صراحت اعتراف می‌کند: «این handler فقط state را عوض/ثبت می‌کند و هیچ patch واقعی انجام نمی‌دهد».

- **خطرناک‌ترین disconnect:** **`_ops/state/telegram/missions/` اصلاً وجود ندارد** — هیچ Missionی هرگز در production به disk نرسیده. صفِ تأیید `_octopus/state/approvals.json` کاملاً خالی است (`pending: [], approved: [], rejected: [], done: []`). یعنی حلقهٔ intent → mission → approval در واقعیت تولیدی هرگز طی نشده؛ فقط در تست طی شده. در عین حال `CAPABILITY-OK.flag` تازه است و `LIVE-ENABLED.flag` غایب است — گیت عمداً بسته است.

- **مهم‌ترین مسیر درآمدی شکسته:** `business-brain-latest.json` خود می‌گوید: «هنوز درآمدِ تأییدشده‌ای ثبت نشده». هیچ lead واقعی (`_ops/state/legs/lead-inbox/` وجود ندارد)، هیچ کاتالوگ محصول (`ziman-catalog.json` وجود ندارد)، هیچ پاسخ مشتری، هیچ invoice ارسال‌شده، هیچ payment ثبت‌شده‌ای وجود ندارد. همهٔ legها DORMANT یا DATA-ONLY هستند (pocketsmith، email، austender همگی flag-off).

- **کوچک‌ترین repair با بیشترین اثر:** ساختن `mission_runner.py` (پرامپتِ CODEX-1 آماده است در `00 - Inbox/`) که فقط ۵ اکشن allowlist شده را در worktree ایزوله اجرا کند و خروجی را به `record_test` / `record_review` وصل کند. این یک گره، Mission Genome، Action Graph، Approval Queue، code_autonomy و doctor را همزمان زنده می‌کند و اختاپوس را از «داشتن قطعات» به «داشتن یک حلقهٔ کنترل» ارتقا می‌دهد.

---

## 2. Reality Snapshot

| Field | Value |
|---|---|
| Repository root | `F:\backup` |
| Branch | `master` |
| HEAD SHA | `9b3702ee2a5778cd9adaca65459dcc8b0cbff957` |
| Dirty state | 66 modified, 63 untracked (اکثراً runtime state در `_ops/state/`) |
| Last commit | `9b3702e fix(llm): GLM base_url default -> z.ai coding-plan endpoint` |
| Worktrees | 23 شاخهٔ `claude/*` parallel-agent در git (اکثر ادغام شده‌اند) |
| Nested git repos | `07 - Knowledge/genome-system/` (با `.git` مستقل، ledger грязный) |

### Key file inventory — ALL PRESENT

| File | Lines | Status |
|---|---|---|
| `_ops/telegram_center/center.py` | 1,224 | CONNECTED (structurally), polling not currently active |
| `_ops/telegram_center/render.py` | 752 | CONNECTED |
| `_ops/telegram_center/intent.py` | 141 | CONNECTED (rule-based, not LLM) |
| `_ops/telegram_center/actions.py` | 171 | **PARTIAL — skeleton, unused by render/center** |
| `_ops/telegram_center/approval_store.py` | 263 | CONNECTED |
| `_ops/telegram_center/metadata_scan.py` | 375 | CONNECTED (executed once: `audit.log` shows `files=2000`) |
| `_ops/telegram_center/mission.py` | 469 | PARTIAL (data model only, no execution) |
| `_ops/telegram_center/action_graph.py` | 191 | CONNECTED |
| `_ops/cortex/code_autonomy.py` | 436 | CONNECTED but **NOT WIRED to mission.py** |
| `_ops/tests/run_all.py` | 216 | CONNECTED |

### Live runtime evidence (organism IS alive)

- `_octopus/state/octopus_state.json` — `2026-07-18T12:04:31+10:00` bootstrap
- `_octopus/logs/audit.log` — آخرین رویداد `metadata_scan` در `2026-07-18T12:40:09+1000`
- `_ops/state/pulse/work-state.json` — `last_window_ts: 1784346591` (~`2026-07-18T13:49:51`)
- `_ops/state/CAPABILITY-OK.flag` — تازه (`Jul 18 13:57`)
- `_ops/state/cortex/journal.jsonl` — 53 KB، در حال رشد
- `_ops/state/cortex/outcomes.jsonl` — 206 ورودی
- `_ops/state/selfheal-events.jsonl` — 81 رویداد
- `_ops/state/doctor/self-knowledge-latest.json` — `2026-07-18T11:34:05`

### What was NOT executed (limits of this audit)

- **Telegram center is NOT currently polling** — `_octopus/logs/telegram.log` is 0 bytes
- **No live process inspection possible** (read-only, no `tasklist`/`ps`)
- **No test suite execution** (would write state, against rules)
- **No mission has ever been created in production** — `_ops/state/telegram/missions/` does not exist
- **`LIVE-ENABLED.flag` is absent** — capability gate intentionally closed (paper mode)

---

## 3. Organ Connectivity Matrix

| # | Organ | Purpose claimed | Entry points | Inputs | Outputs | Consumers | State owner | Runtime proof | Status |
|---|---|---|---|---|---|---|---|---|---|
| A | Telegram ingress | Live owner chat | `center.run_forever` | TG getUpdates | cards/callbacks | owner via TG | `_ops/state/telegram/center-config.json` | offset=223882891 but `telegram.log` empty | **PARTIAL** |
| B | Owner auth | Single-owner RBAC | `center._is_owner` | `from.id` | bool | all handlers | `.env` (`TELEGRAM_OWNER_CHAT_ID`) | fail-closed confirmed `center.py:487` | **CONNECTED** |
| C | Intent classifier | Free-text → intent | `center._handle_ask:557` | text | `{intent,leg,conf,danger}` | `_handle_ask` kind_map | none (pure fn) | rule-based, 12 test cases | **CONNECTED** |
| D | Mission Genome | Trackable missions | `mission.create_mission` | owner_intent | mission dict | `mission_card`, callbacks | `_ops/state/telegram/missions/` **(missing!)** | **dir does not exist** | **PARTIAL** |
| E | Action Graph | Risk/approval/rollback registry | `action_graph.get` | action_id | ActionSpec | `mission.build_plan` | static (`_ACTIONS`) | 17 specs, fully tested | **CONNECTED** |
| E' | Actions skeleton | Callback pattern catalog | (none) | — | — | **nobody** | static | docstring says "skeleton" | **ORPHAN** |
| F | Approval Queue | Unified approval state | `aps.add_pending` | job dict | approve/reject | `center._handle_approval_callback` | `_octopus/state/approvals.json` | **all buckets empty** | **CONNECTED** (zero traffic) |
| G | Mission Runner | Workflow execution | **does not exist** | — | — | — | — | CODEX-1 prompt in Inbox | **DORMANT** |
| G' | code_autonomy | Code patch executor | `tick`, `apply_approved` | patch | shadow test, apply | `cortex.py` tick | SHADOW_LOG, worktree | real git worktree, fully tested | **CONNECTED** (unwired to missions) |
| H | Worktree isolation | Sandbox for tests | `code_autonomy._git_shadow_test` | target_rel | green/red | code_autonomy | tmpdir + `git worktree` | deny-list, allow-list, REAL_VAULT env | **CONNECTED** |
| I | Testing / capability | Gate on test green | `run_all.main` | 163 test files | exit code, marker | `capability_gate.require` | `_ops/state/CAPABILITY-OK.flag` | marker fresh, fingerprint-checked | **CONNECTED** |
| J | Doctor | Diagnose + RFC | `doctor.mine_metrics` | telemetry | RFCs | `_ops/state/doctor/rfcs.json` | 1 RFC `submitted`, `sandbox_result: null` | RFCs never reach sandbox/critic | **PARTIAL** |
| J' | Telemetry | Per-organ micro-USD | `telemetry.snapshot` | budget, genome ledger | JSON | 5 consumers (doctor, governor, cockpit, organism) | `_ops/state/telemetry-latest.json` | AU$0.03/mo vs AU$30 cap | **CONNECTED** |
| J'' | Observability CLIs | health/budget/flag/leg monitors | CLI | state | stdout | **nobody in runtime** | — | CLI-only | **UI-ONLY** |
| K | Memory / vault | Knowledge base | none in `_ops/` | — | — | **not consumed by ops** | `_memory/`, `07 - Knowledge/` | written by external agent | **DATA-ONLY** |
| K' | genome-system | Research loop | `genome-system/run.py` | ledger | metrics | `telemetry.read_genome` (ledger only) | separate `.git` | code not imported by `_ops/` | **ORPHAN** (ledger only is read) |
| L | LLM routing | local→secondary→primary | `model_router.ask` | prompt | response | cortex, synthesis, doctor, improve | `_ops/cortex/model_router.py` | paid gate date-gated, `9b3702e` recent fix | **CONNECTED** |
| M | Business legs | Revenue generation | various | (mostly local) | leg digest | render | per-leg state | all flag-off or DATA-ONLY | **DORMANT** |
| M' | Lead leg | Customer acquisition | `lead_leg.py` | telegram intake | lead score | render | `_ops/state/legs/lead-inbox/` **(missing!)** | dir does not exist | **DORMANT** |
| N | Accounting | txn → ledger → report | `accountant.py` | txn-store.json | reports | (display only) | gitignored local files | 576 txns (from prior audit) | **DATA-ONLY** |
| N' | Budget / runway | Spend cap enforcement | `organ_gate.reserve` | organ, musd | reserve/settle | governor | `_ops/budget/budget-state.json` | AU$0.03/mo spent | **CONNECTED** |
| O | External adapters | PocketSmith/Gmail/AusTender | flag-gated | — | — | **all flag-off** | — | dormant by design | **DORMANT** |
| P | Security / redaction | secret containment | `_scrub`, `_redact`, `_mask_token` | any text | redacted text | tg_api, render, mission, approval_channel | code-level | INV-12 redaction confirmed | **CONNECTED** |
| Q | Governance | handoff/constitution | `CLAUDE.md`, `_PROJECT_INSTRUCTIONS.md` | — | — | agents | `01 - Dashboard/HANDOFF.md` (35 KB, current) | last updated today | **CONNECTED** |
| R | Archive / legacy | (none active) | — | — | — | — | `octopus_core/` | zero imports from `_ops/` | **ORPHAN** |

**Status legend:** CONNECTED / PARTIAL / DORMANT / ORPHAN / UI-ONLY / DATA-ONLY

---

## 4. End-to-End Flow Traces

### Flow A — Telegram free text → execution boundary

| Hop | file:line | Status | Evidence |
|---|---|---|---|
| 1. update arrives | `center.run_once:1160-1190` → `poll_updates` | **PARTIAL** | code present, `telegram.log` empty (not polling now) |
| 2. owner check | `center.handle_update:487` | **WORKING** | `if not self._is_owner(u): return None` — fail-closed, zero response |
| 3. router | `center.handle_update:489-494` | **WORKING** | cbq → `_handle_callback`, msg → `_handle_message` |
| 4. intent classify (mission first) | `mission_mod.infer_mission_type(text)` @ `center.py:540` | **WORKING** | code/test/evolution keywords → mission_type |
| 5. mission create | `mission_mod.create_mission(...)` @ `center.py:542` | **PARTIAL** | function exists, but **missions/ dir never created** |
| 6. approval bridge | `aps_mod.add_pending(...)` @ `center.py:546` | **WORKING** (code) | approval queue code path correct |
| 7. render card | `mission_mod.mission_card(...)` @ `center.py:553` | **WORKING** | HTML card + inline keyboard |
| 8. send to owner | `self._client.send(_scrub(txt), ...)` @ `center.py:554` | **WORKING** | redaction applied |
| 9. callback dispatch | `center._handle_callback:1099` | **WORKING** | mn/lg/pw/pwc/map/ap/ms/ok/no/later routed |
| 10. mission callback | `center._handle_mission_callback:956-1029` | **PARTIAL** | open/test/review/approve/reject handled |
| 11. **execution boundary** | **(none)** | **MISSING** | `ms:test` only `add_note + set_state(planned)` (line 984-985). docstring: «runner not executed by center» |
| 12. audit/evidence | `mission-audit.jsonl` | **PARTIAL** | audit log code exists; **file does not exist** (no mission ever created) |

**Specific answers:**
- **Non-owner silenced?** YES — `center.py:487-488`, zero response, zero side-effect.
- **Free-text → sensitive handler direct?** NO — free-text only navigates to cards, never executes.
- **Intent classifier production vs test?** Production path is real (`center.py:557`).
- **Mission really persisted?** NO — `_ops/state/telegram/missions/` directory absent.
- **Approval bound to mission ID + scope?** YES — `add_pending({id: m.id, type:"mission", risk, ...})`.
- **All mn/ms/map/ap callbacks handled?** YES.
- **UI shows "executed" when only registered?** **NO** — UI is honest: toast says «درخواست تست ثبت شد؛ اجرا جداست».
- **Duplicate updates safe?** YES — `center-config.json:seen[]` dedupe + `last_offset` persisted.

### Flow B — Mission Genome lifecycle

| Transition | Code? | Evidence |
|---|---|---|
| created → planned | **YES (manual)** | `set_state(mid, "planned")` @ `mission.py:285`, called from `ms:test` callback |
| planned → tested | **YES (auto)** | `record_test` @ `mission.py:303` auto-transitions |
| tested → reviewed | **YES (auto)** | `record_review` @ `mission.py:322` |
| reviewed → approved/rejected | **YES** | `set_owner_verdict` @ `mission.py:344` |
| approved → applied | **ENUM ONLY** | state defined in `_ALLOWED_STATES`, **no transition code** |
| applied → monitored | **ENUM ONLY** | no code |
| monitored → done | **ENUM ONLY** | no code |
| * → reverted | **ENUM ONLY** | no code |

**Specific answers:**
- **Which transitions are enum-only?** applied, monitored, done, reverted (4 of 12 states).
- **Status binds to evidence?** PARTIAL — `record_test` requires name/passed/detail, but **caller is `ms:test` which only adds a note, never invokes a real test runner**.
- **Can `test_passed` be set without exit code/report?** YES — `record_test(name, passed, detail)` accepts any `passed: bool`; no enforcement of real exit code.
- **Does scope mutation invalidate approval?** NO — approval binds to mission_id only, not to content hash/SHA/scope.
- **Mission Runner exists?** NO — only a prompt (`00 - Inbox/2026-07-18 Prompt-CODEX-1 - Mission Runner v0`).
- **Fitness from real outcome or heuristic?** **HEURISTIC** — `compute_fitness` @ `mission.py:369` weights (tests 0.35, doctor 0.20, epistemic 0.15, owner 0.25, rollback 0.05); but since tests/doctor are never really run, the weights measure **recorded claims, not measured outcomes**.
- **Survival/revenue contract used?** NO — no survival/revenue field exists in mission schema.

### Flow C — Code change loop

| Hop | file:line | Status | Evidence |
|---|---|---|---|
| 1. owner request | `center._handle_ask` (mt=code_apply_request) | **WORKING** | creates mission |
| 2. plan | `mission.build_plan(mt)` | **WORKING** | returns action spec list |
| 3. patch proposal | `code_autonomy.propose_to_owner` | **WORKING** | posts decision card to TG |
| 4. isolated worktree | `code_autonomy._git_shadow_test:110-152` | **WORKING** | `git worktree add --detach HEAD`, tmpdir, finally cleanup |
| 5. tests in worktree | `run_all.py` via subprocess @ line 132-134 | **WORKING** | `REAL_VAULT=<wt>`, `PYTHONUTF8=1`, timeout=600 |
| 6. diff/report | `git diff --stat` @ line 126 | **WORKING** | truncated 400 chars |
| 7. owner approval | `approval_channel` + `ap:ok` callback | **WORKING** | binds approval_id |
| 8. apply/commit | `code_autonomy._git_apply_canary` | **WORKING** | 7-gate, canary, auto-rollback on red |
| 9. capability revalidation | `capability_gate.mark_capability` after `run_all` green | **WORKING** | fingerprint-checked |
| 10. monitoring/rollback | auto-rollback in `_git_apply_canary` | **WORKING** | red → revert + freeze |

**Specific answers:**
- **Worktree isolation enforced or convention?** **ENFORCED** — `_DENY` tuple (`code_autonomy.py:36-39`) hard-blocks `.git/genome/ledger/.env/secret/budget/money/schema/kill/...`; `_ALLOW_ROOTS` restricts to `_ops/telegram_center/` and `_ops/cortex/`; `allowed_target` fail-closed.
- **Tests leak to live F:\backup?** NO — worktree at tmpdir, `REAL_VAULT` env redirected, cleanup in `finally`.
- **REAL_VAULT/sys.path hack?** REAL_VAULT exists by design (legitimate isolation); no sys.path hack in production code.
- **Approval bound to exact SHA/diff/scope?** **PARTIAL** — approval_id bound, but content hash NOT in approval record (scope drift possible).
- **Real apply path?** YES — `_git_apply_canary` writes, commits, runs canary suite, auto-rollbacks on red.
- **Rollback testable?** YES — auto-rollback on canary red is in code and tested.
- **Capability marker real gate or written-and-forgotten?** **REAL GATE** — read by `approval_channel.py:2270`, `auto_approve.py:94`; `is_open()` is triple-AND (capability + LIVE_ENABLED + per-action approval). **But `LIVE-ENABLED.flag` is absent**, so gate is currently **always closed** (paper mode by design).
- **code_autonomy WIRED to mission.py?** **NO** — code_autonomy has its own independent propose → approve → apply pipeline via `state/cortex/pending-patches/`. mission.py never invokes code_autonomy. **This is the central wiring gap.**

### Flow D — Business-to-revenue loop

| Hop | file:line | Status | Evidence |
|---|---|---|---|
| 1. market/customer signal | `harvest_austender`, `email_inbound` | **DORMANT** | both flag-off |
| 2. lead/demand record | `lead_leg.py` | **DORMANT** | `_ops/state/legs/lead-inbox/` does not exist |
| 3. product/inventory | `ziman_leg.py` reads `ziman-catalog.json` | **DORMANT** | catalog file does not exist |
| 4. pricing/owner verdict | (manual, in TG) | **MANUAL** | no pricing state file |
| 5. approved outreach | (none) | **MISSING** | no outreach code |
| 6. customer response | (none) | **MISSING** | no inbound channel wired |
| 7. invoice/payment | `_ops/state/legs/invoices/` (exists) | **PARTIAL** | dir exists Jul 17, content unknown |
| 8. accounting | `accountant.py`, `ledger_core.py` | **DATA-ONLY** | reads local gitignored txn-store |
| 9. survival dashboard | `business-brain-latest.json` | **WORKING (display)** | `"هنوز درآمدِ تأییدشده‌ای ثبت نشده"` |
| 10. priority update | (cortex journal) | **WORKING (internal)** | 53 KB journal, growing |

**Specific answers:**
- **Where does a real lead get registered?** **Nowhere yet** — `lead-inbox/` does not exist; `/lead` command referenced in business-brain but not wired in `center.py` handlers (only `/now`, `/budget`, `/revenue`, `/missions`, `/menu`, `/start`).
- **Product/inventory → lead/offer?** NO — ziman catalog file absent.
- **Pricing/owner verdict the blocking hop?** YES, but earlier — **lead capture itself is the first dead-end**.
- **Customer response/payment evidence can return?** NO — no inbound channel wired.
- **Accounting → mission/organ attribution?** YES via `organ_gate.reserve/settle` and `telemetry.ORGAN_MAP`, but data is local-only.
- **Dashboard E3/E4 evidence?** **NONE** — grep for `evidence_level: "E[345]"` returns zero hits in `_ops/state/`.
- **Which hop means system hasn't made money?** **Hop 2 (lead capture)** — without a registered lead, no downstream hop can fire.

### Flow E — Learning loop

| Hop | file:line | Status | Evidence |
|---|---|---|---|
| 1. trace/outcome/failure | `cortex/outcomes.jsonl` (206 entries) | **WORKING** | outcomes recorded |
| 2. evidence store | `selfheal-events.jsonl` (81), `journal.jsonl` (53 KB) | **WORKING** | append-only |
| 3. reflection/review | `doctor.self_knowledge.py` | **WORKING** | reads telemetry, writes self-knowledge-latest |
| 4. RFC proposal | `doctor.mine_metrics` → `rfcs.json` | **PARTIAL** | 1 RFC `submitted`, `sandbox_result: null` |
| 5. **sandbox test of RFC** | `doctor.sandbox_test` | **BROKEN** | RFC stuck at `submitted`, never reaches sandbox |
| 6. critic review | `doctor.critic_review` | **BROKEN** | `critic_review: null` |
| 7. owner-approved change | (manual) | **MISSING** | no auto-apply path from RFC |
| 8. memory update | `_memory/`, genome ledger | **DATA-ONLY** | not consumed by `_ops/` decisions |
| 9. new evaluation | (regression loop) | **PARTIAL** | run_all.py runs 163 tests, but no eval dataset |

**Specific answers:**
- **Memory → evidence/freshness?** NO — `_memory/` is written by external agent, not consumed by any `_ops/` decision code.
- **Failure feedback → future plans?** PARTIAL — outcomes recorded, but RFC pipeline stuck at submission.
- **LLM/Fugu/Ollama in decision path?** YES — `model_router.ask` called by cortex, synthesis, doctor.self_knowledge, improve. **Real decision path.**
- **Model routing based on quality/cost/risk/task?** YES — three-tier (local→secondary→primary), paid gate, `route_scorer.py` (flag-off currently).
- **Real eval dataset or regression loop?** PARTIAL — 163 tests = regression loop; no adversarial eval dataset (chamber.py is DORMANT stub).
- **Reports only or provable learning?** **Reports + telemetry only** — RFC pipeline doesn't close the loop.

---

## 5. Disconnect Register

Sorted by severity. Full machine-readable version in `OCTOPUS-DISCONNECT-REGISTER-2026-07-18.json`.

### D-001 — Mission Runner does not exist [CRITICAL]
- **Type:** D1 (Missing Trigger) + D4 (Missing State)
- **Organs:** G (Mission Runner), D (Mission Genome), G' (code_autonomy), J (Doctor)
- **Claim:** Mission lifecycle from create → apply → monitor → done
- **Reality:** `mission_runner.py` does not exist anywhere. Only `00 - Inbox/2026-07-18 Prompt-CODEX-1` prompt exists. `applied/monitored/done/reverted` states are enum-only.
- **Evidence:** `find _ops -name "mission_runner*"` → 0 hits; `mission.py:_ALLOWED_STATES` defines 12 states, only 8 have transition code.
- **Impact:** safety=none, reliability=HIGH (system can't execute), revenue=HIGH (no work can complete), owner_attention=HIGH
- **Root cause hypothesis:** Mission Genome shipped as data model first; execution deferred to a separate CODEX prompt that hasn't been actioned.
- **Smallest safe repair:** Build `mission_runner.py` per CODEX-1 prompt: only 5 allowlisted actions (`code.plan/code.test/code.diff/doctor.review/epistemics.review`), in worktree, artifacts to `_agent_reports/missions/<mid>/run-<ts>/`.
- **Owner decision required?:** YES — approve CODEX-1 prompt scope.
- **Verification test:** end-to-end mission create → runner → artifact → state transition test.
- **Do NOT touch:** `mission.py` data model, `approval_store.py`, `code_autonomy.py` internals.

### D-002 — Mission production persistence never happened [CRITICAL]
- **Type:** D4 (Missing State) + D11 (Test Illusion)
- **Organs:** D (Mission Genome), A (Telegram)
- **Claim:** Missions persist to `_ops/state/telegram/missions/missions.json`
- **Reality:** **Directory does not exist.** No mission has ever been created via production path. Only tests have exercised `create_mission` (in temp dirs).
- **Evidence:** `ls _ops/state/telegram/missions/` → No such file or directory. `_octopus/state/approvals.json` all buckets empty.
- **Impact:** safety=none, reliability=HIGH (state path unproven), revenue=HIGH, owner_attention=HIGH
- **Root cause hypothesis:** Telegram center has not actually processed a free-text mission-eligible owner message in production; or center not running.
- **Smallest safe repair:** Confirm Telegram center is launched, send one test mission-eligible free-text from owner, verify `missions.json` appears.
- **Owner decision required?:** YES — owner must send a real probe message.
- **Verification test:** owner sends "یه تست بنویس" → verify file created.

### D-003 — Telegram center not currently polling [HIGH]
- **Type:** D1 (Missing Trigger) + D12 (Environment Drift)
- **Organs:** A (Telegram ingress)
- **Claim:** `run_forever` polls Telegram getUpdates
- **Reality:** `_octopus/logs/telegram.log` is 0 bytes; `_octopus/logs/commands.log` 0 bytes; `_octopus/logs/errors.log` 0 bytes. `RUN-TG-CENTER.bat` exists but no evidence of active process.
- **Evidence:** `wc -c _octopus/logs/telegram.log` → 0. `center-config.json:last_offset: 223882891` shows past activity, but no recent.
- **Impact:** safety=none, reliability=HIGH (no live input channel), revenue=HIGH (no owner commands reach system), owner_attention=HIGH
- **Root cause hypothesis:** Center started for past sessions (offset advanced, topics created) but is not currently running. Either never launched as a service or crashed/stopped.
- **Smallest safe repair:** Owner launches `RUN-TG-CENTER.bat` (or schedules as service); verify `telegram.log` grows.
- **Owner decision required?:** YES — launching a long-running process is owner's call.
- **Verification test:** after launch, send `/now` from owner Telegram → `telegram.log` non-empty.
- **Do NOT touch:** do not auto-launch (rule against starting servers).

### D-004 — Mission callbacks register requests, never execute [HIGH]
- **Type:** D5 (False State) + D8 (Missing Feedback)
- **Organs:** D (Mission), G (Runner), A (Telegram UI)
- **Claim:** `ms:test` runs tests; `ms:review` invokes doctor
- **Reality:** Both callbacks only call `mission_mod.add_note(...)` and `set_state(mid, "planned")`. Docstring at `center.py:959-962` is explicit: «runner not executed by center ... دکمه‌های test/review فقط request/note ثبت می‌کنند تا UI دروغ نگوید».
- **Evidence:** `center.py:984-985` (`ms:test`), `center.py:996-997` (`ms:review`).
- **Impact:** safety=LOW (UI is honest, doesn't lie), reliability=HIGH (no execution), revenue=HIGH, owner_attention=MEDIUM
- **Root cause hypothesis:** Honest stub — UI intentionally doesn't claim execution, but the execution wiring was deferred.
- **Smallest safe repair:** D-001 solves this — `ms:test` invokes `mission_runner.run(mid, action="test")`.
- **Owner decision required?:** NO (subsumed by D-001).
- **Verification test:** click `ms:test:<id>` → `record_test(mid, "runner", True, <tail>)` is called.

### D-005 — code_autonomy not wired to Mission Genome [HIGH]
- **Type:** D1 (Missing Trigger) + D7 (Unsafe Coupling risk)
- **Organs:** G' (code_autonomy), D (Mission)
- **Claim:** Mission → code change execution
- **Reality:** `code_autonomy.py` has its own independent propose → approve → apply pipeline via `state/cortex/pending-patches/` and `state/telegram/approvals/`. `mission.py` never imports or calls `code_autonomy`. Two parallel approval worlds.
- **Evidence:** `grep -n "code_autonomy" _ops/telegram_center/mission.py` → 0 hits. `grep -n "import mission" _ops/cortex/code_autonomy.py` → 0 hits.
- **Impact:** safety=MEDIUM (two approval stores can diverge), reliability=HIGH, revenue=MEDIUM, owner_attention=MEDIUM
- **Root cause hypothesis:** code_autonomy pre-dates Mission Genome; they were built by different sessions and never unified.
- **Smallest safe repair:** `mission_runner.py` (D-001) becomes the single bridge: mission → runner → code_autonomy.shadow_test/apply_approved.
- **Owner decision required?:** NO (subsumed by D-001).
- **Verification test:** mission with mission_type=code_apply_request → runner → shadow_test result recorded in mission fitness.

### D-006 — RFC learning loop stuck at submission [HIGH]
- **Type:** D8 (Missing Feedback) + D1 (Missing Trigger)
- **Organs:** J (Doctor)
- **Claim:** Doctor proposes RFC → sandbox tests → critic reviews → owner approves → applied
- **Reality:** `rfcs.json` shows 1 RFC with `status: "submitted"`, `sandbox_result: null`, `critic_review: null`. Loop never advances past submission.
- **Evidence:** `_ops/state/doctor/rfcs.json` content.
- **Impact:** safety=none, reliability=MEDIUM, revenue=MEDIUM (no self-improvement closes), owner_attention=MEDIUM
- **Root cause hypothesis:** Sandbox/critic functions exist (`doctor.sandbox_test`, `doctor.critic_review` referenced in action_graph) but no scheduler/tick invokes them.
- **Smallest safe repair:** Add `doctor.advance_rfcs()` to the cortex tick loop — for each `submitted` RFC, run sandbox_test, then critic_review, then propose to owner via approval_channel.
- **Owner decision required?:** YES — auto-running sandbox on RFCs is a scope decision.
- **Verification test:** after tick, RFC `sandbox_result` non-null.

### D-007 — LIVE-ENABLED.flag absent → capability gate always closed [HIGH]
- **Type:** D6 (Missing Authority) + D14 (Duplicate Truth)
- **Organs:** I (Capability gate)
- **Claim:** Capability gate blocks risky actions unless all 3 conditions met
- **Reality:** `capability_gate.is_open()` = `capability_ok AND LIVE_ENABLED AND per_action_approval`. `CAPABILITY-OK.flag` present (fresh), but `LIVE-ENABLED.flag` absent → **gate always returns False**.
- **Evidence:** `ls _ops/state/LIVE-ENABLED.flag` → No such file. `octopus_state.json:human_approval_required: true`, `dry_run_required: true`.
- **Impact:** safety=GOOD (fail-safe), reliability=HIGH (no autonomous action possible), revenue=HIGH, owner_attention=HIGH
- **Root cause hypothesis:** Intentional paper-mode by design — owner has not yet blessed go-live.
- **Smallest safe repair:** Owner creates `LIVE-ENABLED.flag` when ready. NOT a code change.
- **Owner decision required?:** YES — this IS the go-live decision.
- **Verification test:** after flag created, `capability_gate.is_open()` returns True for read actions.
- **Do NOT touch:** do not create the flag without explicit owner instruction.

### D-008 — No lead capture path exists [HIGH]
- **Type:** D9 (Business Dead End) + D1 (Missing Trigger)
- **Organs:** M' (Lead leg), D (Business-to-revenue)
- **Claim:** Owner `/lead` command registers painting leads
- **Reality:** `_ops/state/legs/lead-inbox/` does not exist. `center.py:_handle_message` handlers only include `/now /budget /revenue /missions /menu /start`. **No `/lead` handler.** `business-brain-latest.json` references `/lead` but it's not wired.
- **Evidence:** `center.py:503-510` handler dict. `ls _ops/state/legs/` shows only `invoices/` and `lead-drafts/` (empty drafts).
- **Impact:** safety=none, reliability=none, revenue=CRITICAL (no revenue path can start), owner_attention=CRITICAL
- **Root cause hypothesis:** Lead intake was designed but never wired into center command router.
- **Smallest safe repair:** Add `/lead <text>` handler in `center.py:_handle_message` → `lead_leg.register_lead(text)` → writes to `lead-inbox/<id>.json` → renders lead card.
- **Owner decision required?:** YES — first real customer data enters system.
- **Verification test:** owner sends `/lead painting customer X` → file appears in lead-inbox.

### D-009 — actions.py is an orphan skeleton [MEDIUM]
- **Type:** D1 (Missing Trigger) + D10 (Governance Drift)
- **Organs:** E' (Actions skeleton)
- **Claim:** Centralized callback pattern registry
- **Reality:** `actions.py` exists (171 lines) but `render.py` and `center.py` hardcode their `callback_data` strings directly. Nobody imports `actions.py` for generation.
- **Evidence:** `grep -n "import actions" _ops/telegram_center/*.py` → 0 production hits.
- **Impact:** safety=LOW, reliability=MEDIUM (drift between skeleton and reality), revenue=none, owner_attention=LOW
- **Root cause hypothesis:** Built ahead of integration; never became the single source of truth.
- **Smallest safe repair:** Either delete `actions.py` or refactor `render.py` to source patterns from it.
- **Owner decision required?:** NO.
- **Verification test:** after refactor, single source of truth for callback strings.

### D-010 — Genome-system code orphaned; only ledger consumed [MEDIUM]
- **Type:** D14 (Duplicate/Competing Truth) + D1 (Missing Trigger)
- **Organs:** K' (genome-system)
- **Claim:** Research loop with agents (creativity, doctor, guardian)
- **Reality:** `07 - Knowledge/genome-system/` has its own `.git`, `run.py`, `research_loop.py`, `agents/`. **Zero imports from `_ops/`.** Only `ledger/ledger.jsonl` is read by `telemetry.read_genome()` as a cost source.
- **Evidence:** `grep -rn "from genome\|import genome" _ops/` → 0 hits.
- **Impact:** safety=none, reliability=MEDIUM (two competing "doctor"/"knowledge" concepts), revenue=none, owner_attention=LOW
- **Root cause hypothesis:** Parallel research track that hasn't been integrated.
- **Smallest safe repair:** Owner decides: archive, or wire `research_loop.py` into cortex tick.
- **Owner decision required?:** YES.
- **Verification test:** n/a (decision).

### D-011 — Observability CLIs are UI-only, not wired to runtime [MEDIUM]
- **Type:** D2 (Missing Consumer) + D8 (Missing Feedback)
- **Organs:** J'' (Observability)
- **Claim:** health_check, budget_monitor, flag_monitor, leg_monitor, tracer
- **Reality:** All are CLI tools. None are called from `cortex.py`, `governor_epoch.py`, or any tick loop. `tracer.py` decorator has zero callers in production.
- **Evidence:** `grep -rn "from observability\|import observability" _ops/ --include="*.py" | grep -v test` → 0 production hits.
- **Impact:** safety=none, reliability=MEDIUM (issues only surface when owner runs CLI manually), revenue=none, owner_attention=MEDIUM
- **Root cause hypothesis:** Built as one-off diagnostic tools.
- **Smallest safe repair:** Wire `health_check.run()` into the daily governor epoch; surface red findings to Telegram `mn:st` page.
- **Owner decision required?:** NO.
- **Verification test:** governor epoch output includes health_check summary.

### D-012 — Memory store is DATA-ONLY [MEDIUM]
- **Type:** D2 (Missing Consumer)
- **Organs:** K (Memory)
- **Claim:** Agent memory feeds decisions
- **Reality:** `_memory/HEARTBEAT.md` (46 KB), `EXPERIENCE-LEDGER.md`, etc. — all written by external agents (Claude Code sessions). **No `_ops/` decision code reads `_memory/`.**
- **Evidence:** `grep -rn "_memory\|HEARTBEAT" _ops/ --include="*.py"` → 0 hits.
- **Impact:** safety=none, reliability=LOW, revenue=none, owner_attention=LOW
- **Root cause hypothesis:** Memory is a human/agent-readable log, not a machine-consumed store.
- **Smallest safe repair:** Decide intent. If machine-memory: build a `memory.query()` API and call from doctor/cortex. If human-log: mark as documentation.
- **Owner decision required?:** YES — architecture decision.
- **Verification test:** n/a.

### D-013 — Approval record doesn't bind content hash/SHA [MEDIUM]
- **Type:** D6 (Missing Authority) + D7 (Unsafe Coupling risk)
- **Organs:** F (Approval), G' (code_autonomy)
- **Claim:** Approval binds to exact scope
- **Reality:** `approval_store.add_pending({id, type, title, risk, ...})` — no `content_hash` or `sha` field. Mission scope can drift between approval and execution.
- **Evidence:** `approval_store.py:113-167` `add_pending` signature.
- **Impact:** safety=MEDIUM (TOCTOU risk on high-risk actions), reliability=LOW, revenue=none, owner_attention=MEDIUM
- **Root cause hypothesis:** Approval store is content-free by design (redaction); hash binding was not added.
- **Smallest safe repair:** Add `content_sha256` field to approval record; `apply_approved` verifies hash matches before apply.
- **Owner decision required?:** NO.
- **Verification test:** apply_approved rejects on hash mismatch.

### D-014 — octopus_core/ legacy framework orphaned [LOW]
- **Type:** D14 (Duplicate/Competing Truth) + R (Archive)
- **Organs:** R (Archive)
- **Claim:** (legacy) Project-F runtime framework
- **Reality:** `octopus_core/` has competing implementations of `telemetry.py`, `event_bus.py`, `capability_registry.py`, `health.py`. **Zero imports from `_ops/`.**
- **Evidence:** `grep -rn "from octopus_core\|import octopus_core" _ops/` → 0 hits.
- **Impact:** safety=none, reliability=LOW (confusion), revenue=none, owner_attention=LOW
- **Root cause hypothesis:** Superseded by `_ops/` rebuild.
- **Smallest safe repair:** Move to `_Archive/` or delete.
- **Owner decision required?:** NO (but confirm no external consumer).

### D-015 — Chamber.py adversarial debate is dormant stub [LOW]
- **Type:** D1 (Missing Trigger)
- **Organs:** J (Doctor)
- **Claim:** Inner adversarial debate chamber
- **Reality:** `_ops/doctor/chamber.py` (10 KB) — no LLM calls, all deterministic stubs. Never invoked from tick.
- **Evidence:** reading chamber.py shows `pass`-style stubs.
- **Impact:** safety=none, reliability=LOW, revenue=none, owner_attention=LOW
- **Root cause hypothesis:** Designed but not implemented.
- **Smallest safe repair:** Implement or archive.
- **Owner decision required?:** YES.

---

## 6. Source-of-Truth Map

| Domain | Canonical source | Notes |
|---|---|---|
| Mission state | `_ops/state/telegram/missions/missions.json` | **does not exist yet** — will be created on first production mission |
| Approval (unified) | `_octopus/state/approvals.json` | currently empty |
| Approval (legacy) | `_ops/state/telegram/approvals/*.json` + `approvals.jsonl` | dual-write bridge |
| Code patches pending | `_ops/state/cortex/pending-patches/` | code_autonomy's own store |
| Evidence (cortex) | `_ops/state/cortex/outcomes.jsonl`, `journal.jsonl` | 206 + 53 KB |
| Evidence (selfheal) | `_ops/state/selfheal-events.jsonl` | 81 events |
| Capability | `_ops/state/CAPABILITY-OK.flag` (JSON with fingerprint) | fresh, real gate |
| Telemetry | `_ops/state/telemetry-latest.json` + daily archive | connected to 5 consumers |
| Budget | `_ops/budget/budget-state.json` + `organ-state.json` | per-organ attribution |
| LLM spend | genome ledger `ledger.jsonl` → telemetry `read_genome` | cross-system |
| RFCs | `_ops/state/doctor/rfcs.json` | loop doesn't close |
| Revenue | **NO canonical source** — business-brain is display-only | E0 evidence only |
| Product (ziman) | `ziman-catalog.json` | **does not exist** |
| Leads | `_ops/state/legs/lead-inbox/` | **does not exist** |
| Accounting txns | gitignored local `txn-store.json` | DATA-ONLY |
| Owner identity | `.env: TELEGRAM_OWNER_CHAT_ID` | loaded by env_loader |
| Owner verdicts | dual: octopus approvals.json + legacy approvals/*.json | D14 risk |
| Governance | `CLAUDE.md`, `_PROJECT_INSTRUCTIONS.md`, `01 - Dashboard/HANDOFF.md` | current |

**UNKNOWN ownership:** revenue evidence, real customer data, real product catalog — none exist yet.

---

## 7. Dead / Dormant / UI-only Inventory

| Path | Purpose | Last real caller | Status | Recommended |
|---|---|---|---|---|
| `_ops/telegram_center/actions.py` | Callback pattern skeleton | (none) | ORPHAN | **WIRE** (refactor render to use it) or delete |
| `_ops/doctor/chamber.py` | Adversarial debate | (none) | DORMANT | **OWNER DECISION** |
| `_ops/doctor/evolution.py` | Evolution propose/select | action_graph handler ref (convention only) | PARTIAL | **WIRE** via mission_runner |
| `_ops/doctor/calibration.py` | Feedback loop | (none in tick) | PARTIAL | **WIRE** to chrono.db |
| `_ops/doctor/spectral.py` | Graph spectral analysis | (none) | PARTIAL | PAUSE |
| `_ops/doctor/temperature.py` | Chamber temperature | (none) | PARTIAL | PAUSE |
| `_ops/observability/health_check.py` | Health CLI | manual only | UI-ONLY | **WIRE** to governor epoch |
| `_ops/observability/budget_monitor.py` | Budget drift CLI | manual only | UI-ONLY | **WIRE** |
| `_ops/observability/flag_monitor.py` | Flag consistency CLI | manual only | UI-ONLY | **WIRE** |
| `_ops/observability/leg_monitor.py` | Leg pattern scanner | manual only | UI-ONLY | **WIRE** |
| `_ops/observability/tracer.py` | Function-call tracing | (none) | DORMANT | ARCHIVE or WIRE |
| `_ops/legs/harvest_austender.py` | AusTender OCDS | flag-off | DORMANT | PAUSE (weak source) |
| `_ops/legs/email_inbound.py` | Gmail API | flag-off | DORMANT | **OWNER DECISION** (OAuth) |
| `_ops/legs/pocketsmith_api.py` | PocketSmith API | flag-off | DORMANT | **OWNER DECISION** (key) |
| `_ops/legs/mining_leg.py` | Mining | (none live) | DORMANT | PAUSE |
| `_ops/legs/knowledge_leg.py` | Knowledge | (none live) | DORMANT | PAUSE |
| `_memory/HEARTBEAT.md` | Agent heartbeat log | external agents | DATA-ONLY | **OWNER DECISION** (intent) |
| `07 - Knowledge/genome-system/` code | Research loop | (none in `_ops/`) | ORPHAN | **OWNER DECISION** |
| `octopus_core/` | Legacy framework | (none) | ORPHAN | ARCHIVE |

---

## 8. Business Reality Map

| Leg | واقعاً چه می‌کند؟ | مشتری | value/revenue connection | evidence level | blocking hop | verdict |
|---|---|---|---|---|---|---|
| **Lead-نقاشی (painting)** | Lead scoring math (local), no live source | none registered | designed but unwired | **E0** | `/lead` not in center router + lead-inbox missing | **FIRST TO WIRE** |
| **Ziman (gallery)** | Reads catalog (missing), branding biology | none | catalog file absent | **E0** | ziman-catalog.json missing | PAUSE |
| **Accounting** | Reads local txn-store (gitignored), 576 txns | owner (personal) | ledger_core exists, no bank feed | **E2** (real personal txns, no business revenue) | no business txn source | DATA-ONLY |
| **Mining** | Reads vault decision files | none | `live=False` always | **E0** | no pipeline | DORMANT |
| **Crypto** | Reads local market data files | none | freshness reporter only | **E1** (stale data) | no live feed | DATA-ONLY |
| **Knowledge** | (no spec) | none | none | **E0** | no business spec | DORMANT |
| **Project-F (langar)** | Local instantiation | (internal) | content_free, money-locked | **E1** | money_locked | PAUSE |
| **Cartographer** | Internal mapping | none | none | **E0** | (internal tool) | KEEP (internal) |

**Evidence levels:** E0=none, E1=stale/local data, E2=real personal data, E3=real customer signal, E4=customer response, E5=payment/revenue.

**No leg has reached E3+.** The whole organism is at E0-E2.

---

## 9. Ten Highest-Leverage Repairs

Ranked by leverage (effect ÷ scope ÷ risk).

| # | Repair | Effect on بقا/درآمد/ایمنی | Scope | Risk | Dependency | Owner approval? | ترتیب |
|---|---|---|---|---|---|---|---|
| 1 | **Build `mission_runner.py` (CODEX-1 prompt ready)** | HIGH on all 3 | medium (~300 LoC) | LOW (allowlist, worktree, artifacts) | none | YES (approve prompt) | 1st |
| 2 | **Wire `ms:test`/`ms:review` callbacks to runner** | unblocks Flow A, B, C | small | LOW | #1 | no | 2nd |
| 3 | **Add `/lead` handler + `lead-inbox/` persistence** | CRITICAL revenue path | small | LOW | none | YES (first real customer data) | 3rd (parallel with #1) |
| 4 | **Confirm/launch Telegram center** | unblocks all TG flows | trivial (owner action) | MEDIUM (long-running process) | none | YES | anytime |
| 5 | **Wire `doctor.advance_rfcs()` to cortex tick** | closes learning loop | small | LOW-MEDIUM (sandbox scope) | none | YES (auto-sandbox decision) | 4th |
| 6 | **Wire observability `health_check` to governor epoch + `mn:st`** | surfaces issues live | small | LOW | none | no | 5th |
| 7 | **Add `content_sha256` to approval record + verify on apply** | closes TOCTOU gap | small | LOW | none | no | 6th |
| 8 | **Unify code_autonomy approvals with mission approvals** | removes D14 dual-truth | medium | MEDIUM (refactor) | #1 | no | 7th |
| 9 | **Refactor `render.py` to source callbacks from `actions.py`** | single source of truth | small | LOW | none | no | 8th |
| 10 | **Owner creates `LIVE-ENABLED.flag` when ready for go-live** | opens capability gate | trivial (owner action) | HIGH (autonomy) | #1, #2 verified | YES | last |

---

## 10. Things Not To Touch

- **Active session files** in `_ops/state/cortex/journal.jsonl`, `outcomes.jsonl` — organism is live, appending.
- **All uncommitted work** — 66 modified + 63 untracked files. Inventory only.
- **All `claude/*` branches** — 23 parallel-agent branches, may be mid-work.
- **`07 - Knowledge/genome-system/.git/`** — nested repo with uncommitted ledger changes.
- **`.env`** — contains tokens (TELEGRAM_BOT_TOKEN, FUGU_API_KEY, GLM_API_KEY, etc.); path-only, never content.
- **`_octopus/config/`, `quarantine/`** — runtime secrets/configs.
- **`backup/pre-*` branches** — pre-go-live safety branches.
- **`ACTIVATION-*.flag` files** — 8 of 9 ON, intentional configuration by owner; do not flip.
- **`LIVE-ENABLED.flag`** — owner's go-live decision; do not create without explicit instruction.
- **`RUN-TG-CENTER.bat` infinite loop** — do not launch (rule against starting servers).
- **`_ops/state/legs/invoices/`** — may contain real customer PII; do not inspect content.
- **`txn-store.json`, `categorize-config.json`** — gitignored personal financial data.

---

## 11. Owner Decisions Required

7 real decisions, short, with options.

### D1. Build Mission Runner? (CODEX-1 prompt ready)
- **Option A (RECOMMENDED):** Approve CODEX-1 scope — 5 allowlisted actions, worktree-isolated, artifacts to `_agent_reports/missions/`. Effect: 5 organs light up at once.
- **Option B:** Defer — keep Mission Genome as registry only. Effect: system stays at "modules ahead of execution".
- **Option C:** Smaller scope — runner only supports `code.test` + `code.diff` (read-only), no `code.apply`. Effect: safer, slower.

### D2. Wire `/lead` command + first real lead?
- **Option A (RECOMMENDED):** Add `/lead <text>` handler + persist to `lead-inbox/`. Effect: revenue path can start.
- **Option B:** Defer until Ziman catalog exists. Effect: cleaner but slower.
- **Option C:** Use existing `/now` channel only (no new command). Effect: no structured lead data.

### D3. Launch Telegram center now?
- **Option A:** Owner runs `RUN-TG-CENTER.bat`. Effect: live input channel.
- **Option B:** Schedule as Windows service / cron. Effect: persistent.
- **Option C:** Keep static; use center via test harness only. Effect: no live owner input.

### D4. Auto-sandbox RFCs in doctor tick?
- **Option A (RECOMMENDED):** Yes — `doctor.advance_rfcs()` runs sandbox_test on `submitted` RFCs. Effect: learning loop closes.
- **Option B:** Manual — owner triggers sandbox per RFC. Effect: slower, safer.

### D5. Live-enable (create `LIVE-ENABLED.flag`)?
- **Option A:** Yes now. Effect: capability gate opens, autonomous actions possible.
- **Option B (RECOMMENDED):** Wait until #1, #2, #3 verified. Effect: safer go-live.
- **Option C:** Partial — enable for read actions only. Effect: progressive rollout.

### D6. Genome-system: integrate or archive?
- **Option A:** Wire `research_loop.py` into cortex tick. Effect: research loop live.
- **Option B (RECOMMENDED):** Keep ledger-only integration (status quo). Effect: cost tracking without code coupling.
- **Option C:** Archive genome-system code, keep ledger. Effect: cleaner.

### D7. Memory architecture: machine-consumed or human-log?
- **Option A:** Build `memory.query()` API, consume from doctor/cortex. Effect: closed-loop memory.
- **Option B (RECOMMENDED):** Mark `_memory/` as human/agent documentation. Effect: honest scoping.
- **Option C:** Hybrid — index `_memory/` for search only. Effect: middle ground.

---

## 12. Final Verdict

### 1. اختاپوس امروز واقعاً به چه چیزهایی وصل است؟

وصل و واقعی: **مغز و سیستم‌عصبی** — cortex (با model_router سه‌لایه، LLM در مسیر تصمیم)، heartbeat (در حال تپیدن، beat پیشرفت)، telemetry (به ۵ مصرف‌کننده وصل)، budget/organ_gate (AU$0.03 در برابر AU$30)، doctor self-knowledge، capability_gate با اثر انگشت واقعی، و code_autonomy با git worktree ایزوله واقعی. **Auth/RBAC fail-closed** درست در `center.py:487` قرار دارد. **Redaction (INV-12)** در همهٔ مسیرهای خروجی telegram اعمال می‌شود. **شبکهٔ تست** (۱۶۳ فایل) و **حاکمیت** (HANDOFF.md، CLAUDE.md، _PROJECT_INSTRUCTIONS.md) به‌روز است.

### 2. کجاها فقط ظاهر اتصال دارد؟

پنج توهم اصلی:
1. **Mission Genome** ظاهراً کامل است (۱۲ state، fitness، audit) ولی ۴ state پایانی (`applied/monitored/done/reverted`) فقط enum هستند و `_ops/state/telegram/missions/` اصلاً وجود ندارد — یعنی هیچ production missionی هرگز نساخته شده.
2. **`ms:test`/`ms:review` دکمه‌هایی** که فقط `add_note` می‌زنند (البته صادقانه — UI دروغ نمی‌گوید، ولی اجرا نمی‌کند).
3. **`actions.py`** به‌عنوان registry مرکزی callback معرفی شده ولی کسی آن را import نمی‌کند.
4. **RFC learning loop** در `submitted` گیر می‌کند (`sandbox_result: null`).
5. **Business legs** همه طراحی شده‌اند ولی lead-inbox، ziman-catalog، `/lead` handler همگی وجود ندارند — هیچ E3+ evidence‌ای در کل سیستم نیست.

### 3. اولین اتصال واقعی و کم‌ریسک که باید ساخته شود چیست؟

**`mission_runner.py`** طبق پرامپت CODEX-1 (آماده در `00 - Inbox/`): فقط ۵ اکشن allowlist شده (`code.plan/code.test/code.diff/doctor.review/epistemics.review`) در worktree ایزوله، با artifact در `_agent_reports/missions/<mid>/run-<ts>/`، و وصل کردن خروجی به `mission.record_test`/`record_review`. این **یک گره** همزمان Mission Genome، Action Graph، Approval Queue، code_autonomy و Doctor را زنده می‌کند،Risk آن به‌خاطر allowlist + worktree + deny-list + read-mostly_actions بسیار پایین است، و قبل از `LIVE-ENABLED.flag` هم قابل ساختن/تست است (paper mode).

**پیش‌نیاز:** تأیید مالک برای اجرای پرامپت CODEX-1.
