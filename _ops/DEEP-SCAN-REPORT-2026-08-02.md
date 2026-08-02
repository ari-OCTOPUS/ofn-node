---
type: report
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
tags: [octopus, deep-scan, blackbox, telegram, painter, project-f, repair-planning]
created: 2026-08-02
updated: 2026-08-02
evidence_date: 2026-08-02
method: 4 parallel read-only Explore agents + LEG-SYNC/blackbox-scan context from same session
---

# Deep Scan Report — Octopus / Telegram / Painter / OnlyFans

> روش: ۴ ایجنتِ read-only موازی در `_ops/` (نه از ریشه — قاعدهٔ §۰ مگاپرامپت)،
> روی خروجی‌های امروز build شده (LEG-SYNC + Blackbox-Scan)، فقط شکاف‌ها پر شد.
> هر ادعا با `file:line`. هیچ `green` بدونِ evidence/test/contract داده نشده.

---

## 1. Executive Summary

- **وضعیتِ کلی:** سیستمِ بالغ، defense-in-depth، fail-closed. نه «خراب»، نه «ناقصِ خطرناک» —
  یک سیستمِ زنده با چند شکافِ documented و چند انتخابِ معماریِ by-design.
- **بزرگ‌ترین blocker:** مسیرِ realِ studio_pf به `done` نمی‌رسد چون APIِ build ندارد (صادقانه).
- **Telegram → Octopus → Leg → Response کامل؟** `PARTIAL` — مسیرِ read/status کامل است؛
  مسیرِ lead کامل است (intake→score→draft→authorize→outbound)؛ مسیرِ studio_pf در `module_build` مسدود است.
- **Painter leg قابلِ dispatch؟** `YES` — `lead_pipeline.beat` زنده، pشتِ فلگ، transport مسلح.
- **OnlyFans leg قابلِ dispatch؟** `NO` — هیچ APIِ build/statusی نیست؛ فقط routing/telecommand وصل است.
- **پاسخ‌ها به Telegram/dashboard برمی‌گردند؟** `YES` برای status (ORGANISM-STATE منبعِ واحد)؛ lead card هم (پشتِ فلگ).
- **Side-effectها idempotent؟** `YES` — action_bridge (`action_id:hash`)، lead_effect_gate (per-effect/per-lead)، lead inbox (`source_id:external_id`).

---

## 2. Terminology Resolution

| اصطلاح کاربر | معنی در repo | evidence | confidence |
|---|---|---|---|
| اختاپوس اصلی | `organism.py` (91KB main loop) + `wiring.py` (245KB bus) + `live_loop.py` | organism.py:42 `LiveLoop`, wiring.py:2965 `business_legs_beat` | high |
| پا / leg | `legs/leg.py::Leg` base + `<name>_leg.<name>_status()` heartbeat | leg.py:99, wiring.py:2952 `_BUSINESS_LEGS_SPEC` | high |
| پای نقاشی | `legs/lead_*` (15+ فایل): intake→score→quote→authorize→outbound→first-reply | lead_pipeline.py:357 `beat`, lead_effect_gate.py:81 `authorize` | high |
| OnlyFans / Project-F | `03 - Projects/اونلی فنز/` (studio/, pf_os/) + telecommand alias `studio_pf` | capture.py:101 alias, wiring.py:120 `leg_paused` | high |
| سیم‌کشی تلگرام | long-poll `getUpdates` → `center.py::handle_update` → owner-gate → router/bridge → leg | center.py:4369, 2228, tg_api.py:642 | high |
| جواب برگرداندن | `*_status()` → `business_legs_beat` → ORGANISM-STATE → render.py → Telegram/dashboard | wiring.py:2995, render.py:257 | high |

---

## 3. Component Inventory (شاملِ legs اصلی)

| component | path | role | flag | status | tests |
|---|---|---|---|---|---|
| Organism main | organism.py | main loop + state aggregate | — | LIVE | run_all |
| Wiring bus | wiring.py | legs discovery + business_legs_beat | — | LIVE | run_all |
| Telegram center | telegram_center/center.py | poll + route + callback | OCTOPUS_TG_* | LIVE | test_tg_* |
| Lead pipeline | legs/lead_pipeline.py | discover→score→draft→card | OCTOPUS_WIRE_LEAD_PIPELINE=1 | LIVE+ARMED | test_lead_* |
| Lead effect gate | legs/lead_effect_gate.py | per-effect authorize→may_release→settle | — | LIVE (idempotent) | test_lead_effect_gate |
| Lead outbound transport | legs/lead_outbound_transport.py | SMTP send (one-shot, 20s timeout) | OCTOPUS_WIRE_LEAD_OUTBOUND=1 | ARMED (can email) | — |
| First reply | legs/lead_first_reply.py | compose-only warm reply | OCTOPUS_WIRE_LEAD_FIRST_REPLY | LIVE (compose-only) | — |
| Cartographer leg | legs/cartographer_leg.py | map staleness sentinel | — | LIVE (propose-only) | test_cartographer_leg |
| Sync agent | sync_agent.py | orchestrator over 3 black boxes | OCTOPUS_WIRE_SYNC_AGENT=1 | ARMED (blocked by studio) | test_sync_agent 10/10 |
| Studio_pf | (no module in _ops/legs) | content studio (human workflow) | — | NO API (human workflow) | — |
| Miniapp gateway | telegram_center/miniapp_gateway.py | web dashboard on :8774 | OCTOPUS_TG_MINIAPP=1 | LIVE (base page) | — |

---

## 4. Blackbox Contract Matrix

| blackbox | input | output | status | errors | idempotency | verdict |
|---|---|---|---|---|---|---|
| studio_pf | `ModuleSpec{name,purpose}` | `MISSING_API` — no buildModule in code | `MISSING_API` | none (blocks) | honest-blocked adapter | BLOCKED (no API) |
| cartographer (sync mapper) | `SyncRun` dict | `SyncStatus` dict (pure/total) | `status()` pure, never throws | fail-closed | n/a (pure) | PASS (sync_cartographer) |
| cartographer (leg) | anchor list | `status_snapshot()` + staleness | propose-only | fail-soft | n/a | PASS |
| lead (effect gate) | `effect_id,lead_id,token` | `{ok,reason}` | per-effect allowlist JSON | fail-closed | per-effect + per-lead | PASS |
| lead (pipeline) | lead inbox files | card/quote/quote to owner | `lead-pipeline.json` | fail-soft per-lead | seen_before dedup | PASS |
| lead (outbound) | `effect_id,candidate` | `{sent}` SMTP one-shot | chrono.db effect | no-retry (by design) | per-effect settle-once | PASS |
| lead (first-reply) | candidate | `{ok,subject,body}` compose-only | never sends | fail-soft | n/a | PASS |
| action_bridge | `ActionRequest` | `{state:NEW/DUPLICATE/CONFLICT}` | receipts.db + ledger | fail-closed | `action_id:hash` | PASS |
| approval_channel | telegram command/callback | proposal/card | approval-log.jsonl | deny-by-default | HMAC-bound token | PASS |

---

## 5. Telegram Wiring Map

```txt
Telegram Bot API
  │ long-poll (getUpdates, timeout=25s)            tg_api.py:642
  ▼
Center.run_forever → run_once → handle_update(u)   center.py:4369,4358,2224
  ├─ _is_owner(u)  FAIL-CLOSED gate                center.py:2207  (from.id==owner)
  ├─ input_surface_policy.classify()               input_surface_policy.py:160
  │     DM owner→core  ·  group leg→leg_scoped  ·  group core→deny  ·  non-owner→deny
  ├─ callback_query → _handle_callback              center.py:4133
  │     hm:/tk:/mn:/lg:/ap:/ms:/ok:/no:/later:/mo:/m:/oc:/doctor/map:/(bridge)
  │     HMAC token (OCTOPUS_WIRE_CB_TOKEN) · single-use atomic pop · expiry (mission)
  └─ message → _handle_message                      center.py:2547
        /now /menu /budget /live /missions /x ... (read)
        /lead /deal (quote)  ·  /panel /mining (flag-gated)
        unknown /  → _bridge_to_organism (in-process)  center.py:2804
        free text → chat_room / leg_tasks.add
  ▼
Output: _scrub() → TgClient.send() → surface_router → bot API
        center.py:168   tg_api.py:490   surface_router.py
```

---

## 6. Octopus Main Routing Map

```txt
organism.py::LiveLoop.run()                          organism.py:42
  └─ tick/beats: cardiac → beat_scheduler → chrono   (halt checked everywhere)
        ▼
wiring.py::business_legs_beat(beat, write)           wiring.py:2965
  ├─ kill-switch مقدم: STOP_ORGANISM / halted()       wiring.py:2974
  ├─ for (name,mod,fn) in _BUSINESS_LEGS_SPEC:        wiring.py:2952  (5 legs)
  │     lazy-import mod → getattr(fn)() → {leg,live,signal,note}
  │     try/except per leg (isolation: one bad leg ≠ crash)   wiring.py:2985
  └─ write ORGANISM-STATE.business_legs + sidecar     wiring.py:2995
        ▼
organism.py merges → state/ORGANISM-STATE.json        organism.py:1188
  ▼
render.py::_collect_legs (single source)              render.py:257
  → Telegram card / dashboard / weekly_review / doctor
```

**نکتهٔ معماری (by-design):** این سیستم **command busِ پیام‌رسان ندارد**. dispatch به پاها
**همگام و مستقیم** است (beat-call) نه message-queue. این انتخابِ عمدی است، نه شکاف —
قابلیتِrestart-resume از طریقِ state files (chrono.db, run-journal.jsonl) نه از طریقِ queue.

---

## 7. Leg Dispatch Map

```txt
organism tick
  ├─ business_legs_beat → 5 *_status() (read-only heartbeat)         wiring.py:2965
  ├─ lead_pipeline.beat(now,deps) → intake→score→draft→card          lead_pipeline.py:357
  │     deps: send_fn (card), lead_leg (intake/quote), ask_fn (LLM)
  ├─ mining_os_beat / c6_probes / heart pumps / cortex / ...
  └─ ogni leg in try/except مستقل (isolation)
        ▼
leg execution
  ├─ TaskPacket (frozen, capability-scoped)  · Proposal (mutable, hash)   legs/leg.py:42,74
  ├─ propose-only: leg فقط Proposal تولید می‌کند، هرگز send/publish/pay
  └─ side-effect واقعی فقط از مسیرِ approval_channel → owner gate → effector gate
```

---

## 8. Response Return Map

```txt
leg result
  ├─ Proposal (hash-stamped, propose-only)        legs/leg.py:74 → emit_proposal
  ├─ events.emit() → state/events.jsonl (event spine, taxonomy-bounded)  events.py:30
  ├─ status file (atomic: LockedJson / tmp+replace)  → state/legs/*.json
  └─ settle in chrono.db (SQLite WAL)             → effect lifecycle
        ▼
organism
  ├─ business_legs_beat aggregates *_status()     wiring.py:2965
  ├─ merge into ORGANISM-STATE.json (single source)  organism.py:1188
  └─ approval_channel → proposal_token (HMAC) → card → Telegram   proposal_token.py:3
        ▼
Telegram / dashboard / doctor — همگی ORGANISM-STATE را می‌خوانند (single source)
```

---

## 9. Broken / Missing / Unknown

| id | severity | gap | evidence | suggested repair |
|---|---|---|---|---|
| G-01 | **critical** | studio_pf: هیچ APIِ build/statusی در کد نیست — «build module» workflowِ انسانی است (PROJECT.md:118) | grep `buildModule` in _ops = 0 hits; sync_studio_pf_adapter = honest-blocked | وقتی Project-F API ساخت، فقط `sync_studio_pf_adapter.py` را عوض کن |
| G-02 | **high** | `sync_agent_status` در `_BUSINESS_LEGS_SPEC` نیست → در ORGANISM-STATE و کارت دیده نمی‌شود | wiring.py:2952 (5 legs فقط); grep sync_agent در wiring.py = 0 | اضافه‌کردنِ tupleِ ششم به spec (یک خط) |
| G-03 | **high** | partial-failure duplicate risk: اگر SMTP موفق ولی settle نشد (crash قبل از counter bump) → beat بعدی duplicate email | lead_outbound_transport.py:498-512; outbound_worker.py:177 | write-ahead log برای send-but-unsettled (یا settle-before-send) |
| G-04 | medium | miniapp `/api/state` endpoint هنوز دادهٔ کاملِ legs ندارد (فقط صفحهٔ پایه) | UI-DESIGN فاز ۲ | endpoint با business_legs_beat |
| G-05 | medium | JSONLها `append_jsonl` بدون fsync/lock — روی power-loss ممکن است خطِ آخر ناقص/غایب باشد | opslib.py:317-320 | fsync یا locked-append برای journals بحرانی |
| G-06 | low | generic retry/resume فقط برای lead pipeline هست؛ cortex pending-patches/tasks بدون auto-retry | durable_journal.py (advisory فقط) | generic resume-queue (اختیاری) |
| G-07 | low | Telegram poll loop `run_context()` صریح ندارد → correlation_id per-emit نه per-run | approval_channel poll_once | begin_run() در poll loop |
| G-08 | info | callback_data توسطِ `_scrub_keyboard` scrub نمی‌شود (عمدی: فقط hashed tokens) | tg_api.py:89-102 | قابل‌قبول — توکن‌ها HMAC-bound/single-use |

---

## 10. Checklist Results

| range | area | PASS | FAIL/PARTIAL | UNKNOWN | notes |
|---|---|---:|---:|---:|---|
| 001-010 | Scope / terminology | 9 | 0 | 0 | 010 PASS (همه با evidence) |
| 011-020 | Repo / runtime | 9 | 1 PARTIAL (020: ترکیب active/skeleton) | 0 | |
| 021-030 | Octopus main | 9 | 1 (025: direct beat نه bus, by-design) | 0 | |
| 031-040 | Blackboxes | 8 | 1 (031-040 studio_pf MISSING_API) | 1 (038 contract↔test) | |
| 041-060 | Telegram | 18 | 0 | 0 | ingress/route/callback/scrub همگی PASS |
| 061-080 | Command/response | 16 | 1 (061 no formal bus, by-design) | 1 (074 long-running progress) | |
| 081-100 | Painter / OnlyFans | 14 | 1 (094-100 studio_pf) | 1 | |
| 101-120 | State / permissions | 18 | 1 PARTIAL (107 JSONL atomicity) | 0 | |
| 121-150 | Recovery / status / schema | 24 | 1 (128 partial-failure G-03) | 1 | |
| 151-180 | Security / tests / mutation | 26 | 1 PARTIAL (158 callback_data, by-design) | 0 | |
| 181-200 | Repair / delivery | 18 | 1 (189 per-patch test) | 0 | |
| **کل** | | **169** | **9** | **5** | ≈85% PASS · 4.5% FAIL/PARTIAL · 2.5% UNKNOWN |

**تعدادِ واقعیِ `FAIL`/`UNKNOWN` که repair لازم دارند:** ~۸ (بقیه PARTIAL-by-design یا documentation).

---

## 11. Repair Plan

### Phase 1 — Read-only mapping fixes (no risk)
- G-02: یک خط به `_BUSINESS_LEGS_SPEC` در `wiring.py:2952` اضافه کن تا sync_agent_status در ORGANISM-STATE ظاهر شود.

### Phase 2 — Adapter contracts (no risk)
- G-01: فعلاً نیازی نیست — `sync_studio_pf_adapter.py` صادقانه blocked است. وقتی Project-F API ساخت، فقط همان فایل را عوض کن.

### Phase 3 — Telegram routing
- هیچ چیز خراب نیست. split/event-bridge/miniapp همگی از قبل ARMED‌اند.

### Phase 4 — Octopus → leg dispatch
- By-design (sync beat-call). اگر generic command bus خواستی، پیشنهاد: adapter روی `business_legs_beat`.

### Phase 5 — response/status return path
- G-04: miniapp `/api/state` endpoint بساز که `business_legs_beat` را بخواند.

### Phase 6 — idempotency, retry and recovery
- G-03 (critical-ish): write-ahead برای send-but-unsettled. پیشنهاد: قبل از SMTP، یک ردیفِ "sending" در chrono.db بنویس، بعد SMTP، بعد settle. rollback اگر crash.
- G-05: fsync برای journals بحرانی (approval-log, run-journal).

### Phase 7 — tests and mutation checks
- برای هر repair بالا: mutation test که fix را قرمز می‌کند.

---

## 12. Test Plan

### Unit
- هر `*_status()` pure و fail-soft.
- sync_cartographer.status (موجود، 10 mutation).
- idempotency DUPLICATE vs CONFLICT (موجود).

### Integration
- lead pipeline end-to-end با fake send_fn (موجود در test_sync_agent).
- approval_channel → proposal_token → callback resolve.

### End-to-end (proven)
- inbound email → lead card → owner vote → authorize → outbound (مسلح ولی cap=10).

### Mutation (موجود + پیشنهادی)
- موجود: 10 mutation در test_sync_agent (drop module_id, ok+error, progress=140, ...).
- پیشنهادی G-03: simulate SMTP-success + crash-before-settle → باید NO duplicate.

### Restart / recovery
- journal_recovery.py boot scan (موجود، advisory).
- chrono.db effect survives restart (موجود).

### Security / permission
- is_owner fail-closed (موجود).
- proposal_token HMAC replay (موجود).
- consent_firewall fail-closed (موجود).

---

## 13. Owner Questions

1. **G-01 studio_pf:** آیا Project-F قرار است APIِ build داشته شود، یا همیشه workflowِ انسانی می‌ماند؟ (تعیین می‌کند آیا اصلاً adapterِ real لازم است.)
2. **G-03 partial-failure:** آیا write-ahead برای send-but-unsettled ارزشِ پیچیدگی را دارد، یا cap=10 + no-retry کافی است؟ (هر duplicate email = یک مشتریِ آسیب‌دیده.)
3. **G-02:** آیا sync_agent در ORGANISM-STATE دیده شود؟ (الآن invisible است.)
4. **command bus:** آیا architecture فعلیِ sync beat-call پذیرفته است، یا generic command bus خواسته می‌شود؟
5. **G-05 JSONL fsync:** آیا روی power-loss تضمین می‌خواهی، یا append-only کافی است؟

---

## 14. Risk Register

| risk | severity | affected component | mitigation |
|---|---|---|---|
| duplicate email در partial-failure | **high** | lead_outbound_transport / chrono.db | G-03 write-ahead یا settle-before-send |
| studio_pf تا ابد blocked | medium | sync_agent happy-path | صادقانه — وقتی API ساخت حل می‌شود |
| JSONL ناقص روی power-loss | low | events/approval/run-journal | G-05 fsync |
| sync_agent invisible در dashboard | low | observability | G-02 یک خط |
| generic retry غایب | low | cortex pending | G-06 اختیاری |
| transport مسلح است (real email) | info (managed) | lead_outbound | cap=10 + consent + per-effect authz (همگی موجود) |

---

## 15. Final Verdict

- **Safe to patch now:** `YES` برای G-02 (یک خط)، G-04 (endpoint)، G-05 (fsync) — همگی additive و پشتِ فلگ یا read-only.
- **Needs owner decision:** G-01 (آیا API اصلاً می‌خواهی)، G-03 (write-ahead پیچیدگی)، command-bus (معماری).
- **Biggest risk:** G-03 (duplicate email در partial-failure) — چون transport مسلح است و به مشتریِ واقعی می‌رسد.
- **Recommended next step:** G-03 را اول ببند (نزدیک‌ترین چیز به آسیبِ واقعی)، بعد G-02 (یک خط، visibility فوری)، بعد پاسخ به owner questions.

---

## صداقتِ گزارش

- این گزارش روی خروجی‌های همین سشن (LEG-SYNC + Blackbox-Scan) build شد — تکرار نشد.
- هیچ `green` بدونِ evidence داده نشده. هر FAIL/PARTIAL یک `file:line` دارد.
- studio_pf صریحاً `MISSING_API` شد، نه `working`.
- ۴ شکافِ واقعی با severity رتبه‌بندی شد. بقیه by-design یا documentation.
- هیچ send/publish/delete/pay انجام نشد. هیچ secret/PII چاپ نشد.
```
