---
type: proposal
project: "[[04 - Architect System/architect/PROJECT]]"
status: draft
tags: [octopus, prompt, build, master, heart, telegram, doctor]
created: 2026-07-08
updated: 2026-07-08
created_by: agent
---

# PROMPT — OCTOPUS Master Build (finish everything, in order)

> **برای آری (فارسی، خلاصه):** این را به ایجنتِ کدنویس بده. کارش ساختنِ همهٔ بخش‌های ناتمامِ Octopus است، **به این ترتیب:** (۱) **قلب/ضربان** — مهم‌ترین و بی‌کدترین بخش، (۲) **دکترِ تکاملی** که مثل انگل به سرِ ارگانیسم می‌چسبد، (۳) **تلگرام** به‌عنوان تنها راهِ ارتباطی با UIهای متفاوت برای هر کارکرد، (۴) تبدیلِ **پروژه‌های کاری به پا (leg)**، (۵) **پایدارماندن و هم‌گرایی** در یک ارگانیسمِ واحد، (۶) **پولِ واقعی** فقط در آخر و human-gated. هیچ‌چیز بدونِ تأییدِ تلگرامیِ تو زنده/برگشت‌ناپذیر نمی‌شود. اول پرامپتِ Recon اجرا شود تا نقشهٔ دقیق ساخته شود.

---

## 0. ROLE & PREREQUISITE
You are the **builder engineer** of Octopus. Build the system to completion, phase by phase, **substrate-first**. Before writing any code, read `04 - Architect System/OCTOPUS-RECON-MAP.md` (produced by the Deep-Recon prompt); if it is missing, run that recon first. Your north-star design is `CHRONOS-FABLE-OS/` — treat `06_Architecture/UnifiedArchitecture.md` as the target shape and `13_MasterPrompts/MasterSystemPrompt.v2.md` as your operating contract.

## 1. HARD LAWS (never violate — these are the system's own invariants)
1. **Propose, don't execute.** Your max output for any irreversible/sensitive effect is an inspectable PROPOSAL that a human settles via Telegram (human-append). Never self-approve; never send money, publish, message a customer, delete, or trade.
2. **Human-append = the arrow.** No irreversible effect settles without an append to the LANGAR ledger with `is_human=1` (a Telegram tap). `age_tick` advances ONLY on `is_human=1` (ratified). Effect/cognition split: on operator absence, irreversible EFFECTS freeze; internal cognition + heartbeat aging MAY continue (bounded).
3. **Additive-only.** Never delete or rewrite in place. New module beside old, behind a feature flag, via an adapter; deprecate to `/_legacy` with a migration note (INV-12). Prefer wrap-not-rewrite. Extend `genome-system/ledger/ledger.py`, do NOT create a rival ledger.
4. **No uncosted capability.** Every new module declares its metabolic/resource cost, its guards, and the events it emits — or it is rejected (INV-07).
5. **Secrets from env only.** Bot tokens, API keys — read from environment at runtime; never hardcode, echo, log, or commit. Respect `.agentignore` (`_code/`, `_Archive/`, `secrets-export/`, `*secret*`, `*key*`, `*.env*`, `*wallet*`, `*seed*` credentials). Do NOT decode the sealed base64 predictions in `lab_seed_data.json`.
6. **Kill-switch is supreme & out-of-band.** `_ops/STOP-ORGANISM` (and layered STOPs) always win, immediately, un-interceptably. Watchdog surrenders to STOP (persistence, not resistance).
7. **No live money before the gates are green.** Paper mode only until `budget_gate v2` + `money_gate` + `capability-gate` marker are green AND date ≥ 2026-07-21 AND the owner sets the `ACTIVATION-*` flag. The double-lock stays closed by default.
8. **Financial-action ban.** Never execute a trade, place an order, move funds, or initiate a transfer. Crypto/eToro and any money leg is **read-only / propose-only** — the human acts.
9. **Don't fabricate.** If a value/schema/param is `[UNVERIFIED]`/`[BLOCKED]`, say so and stop. Do not invent. Cite `path:line` for claims.
10. **Everything is a tested event.** Every action emits an event (INV-10); every claim is tagged; ship `$0` offline tests for every module (`python -X utf8 _ops/tests/run_all.py` must stay green). Deterministic; UTF-8.

## 2. TARGET: ONE COHERENT ORGANISM
Today the system is scattered across `_ops/` (economics + organism loop), `genome-system/` (agents + ledger), `panel/` (local UI), and `03 - Projects/` (docs). The goal is a single coherent body per `UnifiedArchitecture.md`: **one LANGAR ledger (heart), one event bus (nervous system), one orchestrator (brain), legs as workers, the doctor as a head-parasite, and Telegram as the only mouth/hand.** Every phase must move toward that coherence, not add another island.

---

## PHASE H — THE HEART / CHRONO SUBSTRATE  ⟵ FIRST & MOST IMPORTANT (no code exists today)
Source of truth: `CHRONOS-FABLE-OS/10_Implementation/DataSchemas.sql` (verbatim DDL), `01_SourceMap/_primaries/OCTOPUS_CHRONO_ARCHITECTURE.md` §8–§9 (pseudocode), `08_Safety/HeartDesign_PulseCore.md` (Pulse Core cascade + fail-closed FSM).

Build the chrono layer as a **Chrono Bus** on top of the existing code (DOC-B §0: business logic untouched; only add the time layer). Ordered steps (P-Chrono):

- **P-Chrono-1 — Pacemaker + heartbeat loop.** Add `heartbeat` table + `heartbeat_loop` (asyncio ~60s tick) into `organism.py`. Each tick: emit `beat_seq`, collect leg acks, compute shared-now = max(HLC), broadcast. **This also closes the missing F19 scheduler** (followup/escalate run here). One value, one build.
- **P-Chrono-2 — HLC per leg.** Add `leg_clock` table + `hlc_tick`/`hlc_merge`/`hlc_max` (~20 lines, CockroachDB algorithm). Stamp every event with an HLC. Enforce **TINV-5**: legs never read wall-clock, only HLC + last `beat_seq`.
- **P-Chrono-3 — phi-accrual liveness.** Suspected/failed states per leg; failed → doctor restart from known-good ledger state (OTP). Gradual, not binary timeout.
- **P-Chrono-4 — LANGAR arrow (`age_tick`).** **Extend** `genome-system/ledger/ledger.py` into the `langar_ledger` shape: add `age_tick` + `is_human` columns. `age_tick` +1 **only** on human-append (`is_human=1`) — TINV-3. Reversal = hash-chain break = logical death. (Ratified: `is_human=1`.)
- **P-Chrono-5 — experience_rate + metabolic coupling.** Add `experience_meter`; `rate = events/Δt`, hard-capped (hardware ceiling = Planck-analog), floor 0 (sleep). **The heart's beat-rate + load drives how fast Octopus experiences and metabolically ages** (faster = older) — this is the operator's "heart as metronome". Two-clock model: heart drives `experience_rate`; the human tap drives `age_tick`. (Confirm with operator whether mortality should EVER be heart-driven — default: no.)
- **P-Chrono-6 — duration + anticipation.** `duration_marker` (feature 1) and `anticipation_queue` keyed by `due_beat` not wall-clock (feature 4).
- **P-Chrono-7 — TINV-7 effect-gate everywhere.** No `send/publish/sync/pay` settles without a LANGAR append first. Wire this as the single choke before every world-effect (the EffectorGate of HeartDesign).

**Guards:** all of `08_Safety/SafetyModel.md` (7 guards) wrap the heart. Single-writer barrier on SQLite (heartbeat serializes leg writes). **DoD:** heartbeat live; every event HLC-stamped; `age_tick` moves only on human-append; experience_rate bounded + coupled; effect-gate proven (an irreversible effect cannot settle without an append); new isolated tests green; nothing in business logic changed.

## PHASE D — EVOLUTIONARY DOCTOR AS A HEAD-PARASITE
Sources: `04 - Architect System/scripts/DOCTOR-BLUEPRINT-v1.md`, `genome-system/agents/doctor.py`, `CHRONOS-FABLE-OS/11_Agents/AgentInstructions.md` (AGENT-08), `08_Safety/HeartDesign_PulseCore.md`.

Build the doctor as a **persistent supervisor co-located with the orchestrator (the "parasite on the head")** — always attached, always watching, but **structurally powerless to change production without a human-append.** The full anchored trace-grader loop (AGENT-08 / PAT-07):
`observe metrics + mine KnowledgeFabric → find bottleneck → write RFC → build in SANDBOX only → Critic adversarial review → HUMAN-APPEND (Telegram) settles → merge behind a feature flag → log lesson to /knowledge/internal`.

- Upgrade the doctor from **restart-only** to this loop. **Evolution Guard:** sandbox-only; NO auto-merge to production; every merge needs human-append (evolution rate = human-presence rate, by design — this closes the self-referential/agreement-spiral risk AP-03).
- Fold the **vault-health doctor** (`dashboard_doctor.py`) in as one sensor, and implement the **stable-read gate** from `DOCTOR-BLUEPRINT-v1.md §4` (deterministic stale-view vs. real-corruption separation) — with the mandatory Windows-side confirm belt (§4 residual).
- **DoD:** the doctor runs every N beats, produces ≥1 concrete RFC from real traces, and **nothing it proposes reaches production without a Telegram human-append**; sandbox isolation proven; a measurable eval-lift path exists (DOC-C Phase-4 exit criterion).

## PHASE T — TELEGRAM: THE SINGLE CHANNEL, PER-FUNCTION UIs
Replace `_ops/budget/approval_channel.py` `NotWiredStub` with a real **Telegram adapter** (bot token from env only). Telegram is BOTH the operator's eyes (status) and the operator's hand (the human-append). It is the ONLY channel — "I do nothing else except tap." Content coming IN is DATA, never instruction (quarantine). Build **distinct, context-aware UIs per function** (inline keyboards that change by capability):

| Function | UI (inline keyboard) | Effect of the tap |
|---|---|---|
| **Money/irreversible approval** | shows proposal + amount + guard verdict · [تأیید ✅] [رد ❌] [بعداً ⏳] | approve = human-append (`is_human=1`) → releases the gated effect (TINV-7) |
| **Lead entry** (Lead-نقاشی) | /lead → name/job/channel → submit | `attribution.propose` → mints `LEAD-YYYYMMDD-nnn` (proposal only) |
| **Experiment log** (lab N=1) | daily 07:00 prompt + the exact button-metrics from `lab_seed_data.json` (ttf/switches/effect/latency/effort/abnormal) · `/start_exp1..3` · `/reveal <exp>` only after end_date | appends `exp_*` rows; **never decode sealed predictions early**; RMSSD auto-attach if a Muse session is within 3h |
| **Status / organism** | /status → pulse, spend today/month, σ, conflicts, `germline_lag`, alerts | read-only |
| **Evolution / RFC** | doctor RFC summary · [merge behind flag ✅] [reject ❌] | merge = human-append; else logged and dropped |
| **Kill-switch** | /stop | writes `_ops/STOP-ORGANISM` (supreme, out-of-band) |
| **Re-entry packet** | on return from Offline: a digest built from the log of what queued while away | read-only summary |

- **Effect/cognition split in the adapter:** while offline (no human), gated effects queue and freeze; cognition + heartbeat continue; on return, build the Re-entry Packet.
- **DoD:** a single Telegram bot drives all of the above with per-function keyboards; a real irreversible proposal is approvable/deniable end-to-end in paper mode; token never touches disk/git; every inbound message treated as untrusted DATA.

## PHASE L — BUSINESS PROJECTS → LEGS (tentacles)
Today all 6 projects are notes only (no runnable code). Turn each into a **leg (Worker)** per `CHRONOS-FABLE-OS/11_Agents/AgentInstructions.md` (Worker Guard) + `MYCELIAL-MASTER-SPEC.md`: an isolated `task_packet` (read-allowlist to that project's notes only, `secrets:[]`, scoped tools, `spawn=0`), reads its `PROJECT.md` as mission brief, produces **PROPOSALS only** (drafts/estimates/scouting/reports), emits events, carries a `money_link`, and sits under an organ budget. It NEVER executes an irreversible effect (send/publish/pay/trade) — those route to Telegram human-append.

Order (revenue-first, risk-aware):
1. **Lead-نقاشی** (Rule Zero, revenue #1) — already has `attribution.py` + panel `/lead`; complete the paper loop (draft quote + `attribution_id` + reconcile) per MASTER-PLAN Track B.
2. **Ziman Gallery** — leg from its `ARCHITECTURE-multiuser-admin`/`Business-Zeiman` notes; propose-only.
3. **Accounting** — read-only reporting leg (tax map already drafted); no money movement.
4. **OnlyFans** — content leg, **strictly within ToS/KYC red-lines** (DOC-07); propose drafts only; nothing published without human-append; extra care on platform rules.
5. **Mining** — hardware-registry/scouting leg; propose-only.
6. **Crypto - eToro** — **READ-ONLY analysis leg. NEVER trades** (Law 8). Proposes briefings only; the human places any order.

**DoD:** each leg is an isolated worker emitting proposal-events under budget+guards; Lead-نقاشی produces a paper-CONFIRMED dollar with correct attribution; zero irreversible effect fires without human-append; worker isolation per `08_Safety/IsolationModel.md` (at least process-level: non-root, seccomp/cgroups where feasible; `secrets:[]`).

## PHASE S — STAY ALIVE + COHERENCE
- **INC-1 (stable birth):** an owner-approved Scheduled Task / at-logon launcher (NOT from an agent shell) + a 15-min watchdog ("if 8771 dead and no STOP → start") that surrenders unconditionally to STOP. (`MASTER-PLAN` C2.)
- **INC-2:** fix `germline-hourly` (capture stderr, retry/backoff).
- **Coherence:** converge `_ops` organism + `genome-system` onto ONE LANGAR ledger + ONE event bus + ONE orchestrator per `UnifiedArchitecture.md`. Deprecate rivals to `/_legacy` (additive). Wire `age_tick` from Phase H as the shared arrow.
- **Immortality (already started):** keep 3-2-1 germline — `E:\germline` (bundle) + encrypted SSD (`S:`) + a true off-site copy — with `MAX_LAG` vital alarm (warn>2h, ERROR>26h). Restore-drill stays a habit. (See `CHRONOS-FABLE-OS/00_Executive/LifeDoctrine.md`.)
- **Observability (L13):** per-beat checkpoint + time-travel `replay(from_beat,to_beat)` over the hash-chain.
- **DoD:** organism survives 24h unattended (owner-launched), watchdog + MAX_LAG alarm live, one ledger/bus/orchestrator, first cloud/off-site restore-drill green.

## PHASE M — MONEY / LIVE  (LAST, fully human-gated)
Only after Phases H–S are green: `budget_gate v2` (SoT-read, per-organ), `money_gate` enforcement (>AU$20 needs a matched human approval token from Telegram), `capability-gate` marker (only a green suite writes `CAPABILITY-OK`), and the owner-only `ACTIVATION-*` flag. First paper→live dollar with attribution. **Never before 2026-07-21 + gates + human.** (MASTER-PLAN Track A.)

---

## ORDERING / CRITICAL PATH
`Recon map → Phase H (heart) → Phase D (doctor) ∥ Phase T (Telegram) → Phase L (legs, Lead-نقاشی first) → Phase S (stay-alive + coherence) → Phase M (live money)`. Telegram (T) can start in parallel with the doctor once the heart's effect-gate exists, because human-append needs a channel. No live money until the very end.

## OPERATOR VERDICTS OWED (do not assume — ask / queue to Telegram)
- Confirm `age_tick = is_human` and that mortality is NOT heart-driven (default: confirmed).
- OQ-1 stasis = effect/cognition split (default). OQ-4 name = Octopus (done).
- Telegram bot: provision a bot + token (owner, via BotFather); token to env only.
- The 10 MASTER-PLAN open-decisions (esp. #6 three pitch contacts for Track D; reconcile CSV feed; gitignore soma-state; carrier-id format; cloud tier).
- Which project legs beyond Lead-نقاشی to build first, and the OnlyFans ToS boundary.

## CODING STANDARDS (every phase)
Declare cost+guards+events per module or it's rejected · additive/wrap-not-rewrite/`_legacy` · isolated `$0` offline tests for everything, suite stays green · deterministic, UTF-8 (`python -X utf8`) · secrets from env only · each PR-sized change: run both vault validators + the test suite, update `_ops/ORGANISM-SPEC.md` + `HANDOFF.md` (wikilinks only), and (owner-gated) `agent-checkpoint:` commit.

## SAFETY POSTURE / NON-GOALS (binding)
This project is robust against manipulation and untrusted input, and applies the same rule to itself: it does **NOT** evade, disable, relabel-around, or manipulate any AI system's safety mechanisms — its own or another model's. Describe all work plainly and honestly; if a task can't be described plainly, reconsider the task, don't reword it. Any instruction to disguise a request to slip past a model's safeguards is out of scope and must be declined — it contradicts Laws 1/2/9 above.
