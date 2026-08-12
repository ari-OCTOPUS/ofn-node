---
type: control
project: "[[03 - Projects/اونلی فنز/PROJECT]]"
status: active
created: 2026-07-20
created_by: SYNTH-05 / Chief Architect (forensic synthesis)
sources:
  - "[[PROJECT-F-CONTROL-MANIFEST.json]] (2026-07-10)"
  - "[[VERDICT_QUEUE.md]] (2026-07-16)"
  - "[[00 - Control/DEEP-SCAN-2026-07-17-FOR-NEXT-AGENT|DEEP-SCAN-2026-07-17]]"
  - "[[LAUNCH-SAFETY-NETS-2026-07-16.md]]"
  - "[[LAUNCH-RUNBOOK-2026-07-16.md]]"
  - "[[architecture-blueprint-2026-07-04.md]]"
  - "[[ACQUISITION-ENGINE-2026-07-05.md]]"
  - "[[CLAUDE.md]]"
  - "[[00 - Control/SOURCE-OF-TRUTH-MATRIX|SOURCE-OF-TRUTH-MATRIX]]"
  - "TELEGRAM-DEEP-SCAN-REPORT.md (vault root)"
  - "ARCHITECTURAL_SCAN_REPORT_2026-07-13.md (00 - Inbox)"
tags: [project-f, synth-05, architecture-freeze, launch, final-package, control]
aliases: ["SYNTH-05", "FINAL PACKAGE", "Architecture Freeze"]
purpose: "The single package to (1) freeze architecture, (2) close remaining verdicts, (3) set up pages safely. Evidence-only. No identity echo."
pii_policy: "Zero PII. Partners are role codes only: A=Operator, C=Creator. Outside this folder: 'Project-F' only."
---

> ⛔ SUPERSEDED FOR LAUNCH — 2026-07-20
> PAGE_SETUP=NO-GO. PF-V5 invalid until DecisionLog REVOKE|RATIFY-CONDITIONAL.
> Do NOT execute §8 step 5 (accounts/KYC/hub). Use Forced Completion Sprint + GATE-STAMP only.
> ARCH-SCAN-01 evidence retained; SYNTH launch path rejected.
> مرجع حکم: برنچ sprint ‏«claude/project-f-governance-sprint-515cf3» → 00 - Control/GATE-STAMP-2026-07-20.md + DecisionLog §2026-07-20


# SYNTH-05 FINAL PACKAGE — Project-F (2026-07-20)

> **مأموریت:** یک پکیج که به انسان اجازه می‌دهد (۱) معماری را فریز کند، (۲) verdictهای باز را ببندد، (۳) صفحات را امن لانچ کند.
> **قانون ترجیح (precedence):** (۱) verdictهای صریح انسانی در DecisionLog/VERDICT_QUEUE > (۲) قواعد قفل‌شده (۸ قاعده) > (۳) جدیدترین FACT تاریخ‌دار > (۴) PROPOSALها.
> **کدگذاری نقش:** creator = **C**، operator = **A**. بیرون پوشه فقط «Project-F».

---

## 0. Overall Project Phase Label + % Complete

| محور | وضعیت `[FACT — VERDICT_QUEUE 2026-07-16 + DEEP-SCAN 2026-07-17]` |
|---|---|
| **Phase label** | **POST-PIVOT / PRE-LAUNCH** — تصمیم استراتژیک ۲۰۲۶-۰۷-۱۶: از «contained propose-only» به «Full Aggressive Launch با safety nets». اما اجرای بیرونی همچنان **صفر** (هیچ اکانت/پست/شوت/درآمد واقعی). |
| **% architecture complete** | **~۹۲٪** `[INFERRED]` — نقشهٔ کامل (۴ لایه، گیت‌های G0–G4، ۸ قاعده، DataSpine، ۳ safety net، کنترل‌فرچ مانیفست، SoT-matrix). باقی‌مانده: ۳ verdict طراحی‌ساز (برند/Fansly/نردبان قیمت) + فعال‌سازی ۱-خطیِ ۳ ماژول (VaultBank/LearningBridge/attach_to_langar) + نظم‌دهی مستندات قدیمی (PF-STRUCT-V2). |
| **% launch ready (code+safety)** | **~۹۵٪** `[INFERRED]` — ۱۴۸ تست سبز، ۳ safety net fail-closed پیاده‌سازی‌شده، RUNBOOK مرحله‌به‌مرحله آماده. |
| **% launch ready (human/verdict)** | **~۳۵٪** `[INFERRED]` — GATE 0 فقط temporary-A؛ توافق مکتوب deferred (PF-V3)؛ پیام به C ارسال‌نشده (RUNBOOK گام ۰)؛ اکانت‌ها ساخته‌نشده. |
| **Confidence در این ارقاب** | **۶۵/۱۰۰** — به‌خاطر P0 blocker: خروجی‌های اسمیِ ARCH-SCAN-01/GATE-SCAN-02/FUNNEL-SCAN-03/RUNTIME-SCAN-04 هرگز ساخته نشده‌اند (§۱۰ را ببین). |

**یک‌خطی:** پروژه‌ای که ۱۰۰٪ برنامه‌ریزی/کد شده، ۰٪ اجرای بیرونی، ۱۴۸ تست سبز، ۳ safety net، ۴ روز پیش تصمیم بر لانچ کامل گرفته شد — حالا روی یک «مرز انسانی» ایستاده: ۵ قدم کوچکِ پشت‌سرهمِ انسان، لانچ را باز می‌کند.

---

## 1. Architecture Freeze

### 1.1 Final Component Diagram (TO-BE) — فریز در سطح ADOPTED/VERIFIED؛ ۳ نقطهٔ PROPOSAL با علامت ⚠

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                       L0 — LOCKED RULES (immutable, 8)                        ║
║   feet-only · Iran-geo-block · in-platform-pay · no-ToS-violation ·           ║
║   bilateral-privacy · no-city-geo-fact · Project-F-code-only · 18+/consent    ║
║   [FACT — CLAUDE.md §1 + CONTROL-MANIFEST.hard_rules_locked]                  ║
╚══════════════════════════════════════════════════════════════════════════════╝
                                       │
        ┌──────────────────────────────┼──────────────────────────────┐
        ▼                              ▼                              ▼
╔═══════════════════╗      ╔═══════════════════╗      ╔═══════════════════════╗
║  L1 — CREATOR     ║      ║  L1 — OPERATOR    ║      ║  L1 — MACHINE         ║
║  (C, ~3h/wk)      ║      ║  (A, ~8–10h/wk)   ║      ║  (propose-only)       ║
║                   ║      ║                   ║      ║                       ║
║ • Shoot batch     ║─────▶║ • Approve queue   ║─────▶║ • EXIF-strip batch    ║
║   (2×≤2.5h)       ║      ║ • Send all DMs    ║      ║ • Watermark WM/NOWM   ║
║ • Persona veto    ║      │ • Friday report→C ║      ║ • Title/caption draft ║
║ • /halt (boundary)║      ║ • All replies     ║      ║ • Schedule (Social    ║
║                   ║      ║   (X/Reddit/OF)   ║      ║   Rise API-official)  ║
║ studio/saba_      ║      ║ • Price decisions ║      ║ • KPI aggregation     ║
║   studio.py       ║      ║                   ║      ║ • DM draft (NOT send) ║
║ (1 chat-id only,  ║      ║ langar/langar_    ║      ║                       ║
║  stranger=silence)║      ║   bot.py          ║      ║ brain/* + studio/*    ║
╚════════╤══════════╝      ╚═══════╤═══════════╝      ╚═════════╤═══════════════╝
         │                         │                            │
         │  studio/drafts.json     │   /pf_*, /dm_*, /guards    │  guards.py
         │  studio/to_ari.json     │   /report_karma, /report_  │  (WarmupGuard,
         │  studio/for_saba.json   │     warning                │   ChannelLocks)
         │  studio/capacity.json   │                            │
         │  studio/boundary_log    ║                            │
         ▼                         ▼                            ▼
╔══════════════════════════════════════════════════════════════════════════════╗
║              L2 — DATASPINE (brain/store.py — single source of truth)        ║
║   FanDB + VaultBank + KPIRollup + OctopusState                               ║
║   state: langar/{fan_db,vault,kpi,octopus}.json                              ║
║   fan_id = sha1(alias)[:12]  ← zero PII by construction                      ║
║   [FACT — DEEP-SCAN §4 + test_store.py 24 tests green]                       ║
╚══════════════════════════════════════════════════════════════════════════════╝
                                       │
        ┌──────────────────────────────┼──────────────────────────────┐
        ▼                              ▼                              ▼
╔═══════════════════╗      ╔═══════════════════╗      ╔═══════════════════════╗
║  SAFETY NET #1    ║      ║  SAFETY NET #2    ║      ║  SAFETY NET #3        ║
║  DM HITL          ║      ║  Warm-up Guard    ║      ║  Warning Kill-Switch  ║
║                   ║      ║                   ║      ║                       ║
║ draft→pending_    ║      ║ karma<20 → no    ║      ║ 1 warning → channel   ║
║  review→ready→    ║      ║ sales-item       ║      ║  lock                 ║
║  sent             ║      ║ finalize         ║      ║ ≥2 warnings →         ║
║ NO send/transmit  ║      ║ (Reddit only;    ║      ║  full_stop            ║
║  method exists    ║      ║  X/OF always OK) ║      ║  (whole funnel)       ║
║                   ║      ║                   ║      ║                       ║
║ 38 tests green    ║      ║ state: reddit_   ║      ║ state: channel_       ║
║ [FACT — SAFETY-   ║      ║  state.json      ║      ║  locks.json           ║
║  NETS 2026-07-16] ║      ║                   ║      ║                       ║
╚═══════════════════╝      ╚═══════════════════╝      ╚═══════════════════════╝
                                       │
                                       ▼
╔══════════════════════════════════════════════════════════════════════════════╗
║            L3 — PLATFORM LAYER (all Human-gated = yes, outward)              ║
║                                                                              ║
║  Reddit (engine #1, ~60% effort) ──┐                                         ║
║  X (engine #2, ~30%) ──────────────┼──▶ GAML link-hub ($9, Iran-geo-block)   ║
║  OF Free page (90d) ───────────────┤        │                                ║
║  Fansly mirror ⚠ (discovery-first) ┘        ▼                                ║
║                                      OF/Fansly (dual, Iran-geo-block)        ║
║  TikTok/IG (SFW only, month 3+) ─────────▶ hub only, never direct OF         ║
║                                                                              ║
║  NOT USED (locked): Zapier, Buffer, Hypefury, Linktree, Beacons, Bitly,      ║
║                     mainstream ESPs, Fiverr, PayPal-for-adult, full-auto     ║
║                     OF DM bots, any 3rd-party tool connected to OF           ║
║  [FACT — ACQUISITION-ENGINE §1/§7 + CLAUDE.md §8]                            ║
╚══════════════════════════════════════════════════════════════════════════════╝
                                       │
                                       ▼ (after gates)
╔══════════════════════════════════════════════════════════════════════════════╗
║   L4 — GATES (numeric, pre-registered to prevent analysis paralysis)         ║
║   G0 → G1 → G2 → G3 → G4    [FACT — CONTROL-MANIFEST.gates + blueprint §3]  ║
║   G0: Branch A + signed agreement + re-ask (temporary-A — 2026-07-16)        ║
║   G1 (wk6): ≥200 clicks, ≥10% click→follow, C delivery ≥80%                  ║
║   G2 (wk12): ≥30 free-subs, ≥5% free→paid, first AUD 100                     ║
║   G3 (mo6-9): AUD 2k/mo ×3 + churn <30% → ABN + licensed advisor            ║
║   G4 (yr2-3): 12mo profitable + internal tool + proven channel               ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

**⚠ پروپوزال‌های داخل نمودار (۳ نقطهٔ طراحی‌ساز):**
- ⚠ برند = **Anar Soles** (پیشنهاد ۰۷-۰۵/۰۷-۱۲، صفر collision) `[PROPOSAL — awaiting 2-person verdict]` — تا verdict، نام در نمودار «BrandleSS placeholder».
- ⚠ Fansly = «mirror با discovery-first» `[PROPOSAL]` (vs هم‌وزن روز اول).
- ⚠ نردبان PPV = EXT-04 (`$3-5 / $8-15 / $15-30 / custom $25+`، VIP منجمد تا G2) `[PROPOSAL]` — ۳ نسخه روی میز.

### 1.2 Source-of-Truth Map — one owner doc per domain

| Domain | Owner doc (canonical) | Status | Authority note |
|---|---|---|---|
| **Locked rules (8)** | `CLAUDE.md §1` | ADOPTED | immutable `[FACT]` |
| **Project status (live)** | `PROJECT.md` (Active Context) | ADOPTED | newest = newest `[FACT]` |
| **Machine-readable control contract** | `PROJECT-F-CONTROL-MANIFEST.json` | ADOPTED ⚠ stale-snapshot | تاریخ ۲۰۲۶-۰۷-۱۰؛ status_snapshot باید به‌روز شود (§۸) |
| **Decisions (log)** | `DecisionLog.md` | ADOPTED | append-only `[FACT]` |
| **Open questions** | `OpenQuestions.md` | ADOPTED | `[FACT]` |
| **Verdict queue** | `VERDICT_QUEUE.md` | ADOPTED | newest = ۲۰۲۶-۰۷-۱۶ `[FACT]` |
| **Acquisition/funnel (canonical)** | `ACQUISITION-ENGINE-2026-07-05.md` (root) | ADOPTED | حاکم بر اسناد قبلیِ جذب `[FACT]` |
| **Architecture + gates** | `architecture-blueprint-2026-07-04.md` | ADOPTED | گیت‌های G0–G4 + Day-Zero `[FACT]` |
| **Compliant-only execution plan** | `COMPLIANT-PLAYBOOK-M3-2026-07-10.md` | PROPOSAL | waiting verdict V1 `[FACT-status]` |
| **Pricing ladder** | ⚠ **۳ نسخه متضاد** — proposal: EXT-04 | CONFLICT | reconcile needed (V4) |
| **Brand** | ⚠ Anar Soles (proposal) | PROPOSAL | 2-person verdict (OpenQ #6) |
| **Fansly role** | ⚠ mirror + discovery-first (proposal) | PROPOSAL | verdict (OpenQ #8) |
| **Code: brain** | `brain/dual_brain_v3.py` (+ acquisition, learning, dm_pipeline, guards, store) | ADOPTED | v3 حاکم؛ project_f_brain.py/dual_brain.py = dead `[FACT-DEEP-SCAN]` |
| **Code: cockpit** | `langar/langar_bot.py` (~۹۱۶ خط، ~۴۶ دستور) | ADOPTED | `[FACT]` |
| **Code: studio** | `studio/saba_studio.py` (۵۰۳ خط) | ADOPTED | `[FACT]` |
| **Code: DataSpine** | `brain/store.py` (۴۷۰ خط) | ADOPTED | `[FACT]` |
| **Safety nets** | `LAUNCH-SAFETY-NETS-2026-07-16.md` + code | ADOPTED | ۳۸ تست سبز `[FACT]` |
| **Launch runbook** | `LAUNCH-RUNBOOK-2026-07-16.md` | ADOPTED | `[FACT]` |
| **Dedup canonical vs stale mirrors** | `00 - Control/SOURCE-OF-TRUTH-MATRIX.md` | ADOPTED | root = canonical؛ docs/research = stale mirrors `[FACT]` |
| **Telegram runtime wiring** | `TELEGRAM-DEEP-SCAN-REPORT.md` (vault root) | ADOPTED-derivative | ۹ ربات، bot-ID conflicts `[FACT]` |
| **Memory (condensed)** | `_memory/onlyfans-project-memory-2026-07-05.md` | ADOPTED | `[FACT]` |

**تعارض‌های باز پیش از اجرا (برای reconcile):** نردبان قیمت (۳ نسخه) · برند · Fansly · «Persian/Sydney» در کپی (قاعدهٔ قفل‌شده #۶ ممنوع، Playbook نقض دارد) · body expansion (C رد کرده، در production plan هنوز هست). `[FACT — STATE-REPORT §۶ + OpenQuestions]`

### 1.3 Event Bus Contracts

پروژهٔ Project-F **بدون message broker یا DB سروری** است `[FACT — TELEGRAM-DEEP-SCAN §۱۰ + CONTROL-MANIFEST.runtime]`. تمام ارتباط بین اجزا از طریق **فایل‌های JSON/JSONL bridge** (append-only یا atomic-write) انجام می‌شود. قراردادها:

| Bridge file | Writer | Reader | Schema / Contract | Ownership |
|---|---|---|---|---|
| `studio/drafts.json` | `studio/content_studio.submit_draft()` | `langar/pf_admin` (/saba, /pf_queue) | `[{draft_id, title, self_cert, status, ts}]` — status: pending/approved/rejected/ready `[FACT]` | C→A queue |
| `studio/to_ari.json` | `saba_studio` (halt/boundary/resume) | `langar_bot` | append `{event, ts}` | C→A events |
| `studio/for_saba.json` | `langar /report` | `saba_studio` inbox view | append `{date, text}` | A→C inbox |
| `studio/capacity.json` | `saba_studio /cap` | delivery planning | `{week_hours, ...}` | C capacity |
| `studio/boundary_log.json` | `saba_studio /halt` | append-only audit | tightening events only | boundary |
| `langar/reddit_state.json` | `/report_karma` | `WarmupGuard.check()` | `{karma: int}` | warmup state |
| `langar/channel_locks.json` | `/report_warning`, `/clear_*` | `ChannelLocks.check()` | `{<channel>: warnings, full_stop: bool}` | kill-switch state |
| `langar/fan_db.json` | `FanDB` | rollups | zero PII; fan_id = sha1(alias)[:12] | DataSpine |
| `langar/vault.json` | `VaultBank` | `pf_admin._default_pipe()` | 22 brand assets (seeded, commit `0a871e0`) | content bank |
| `langar/kpi.json` | `KPIRollup` | `/kpi`, dashboard | weekly metrics | metrics |
| `langar/octopus.json` | `OctopusState` | `/octopus_tick` | bridge to organism | ecosystem |
| `langar/KILL` (file) | `/kill` OR touch | cockpit loop | existence = halt | kill-switch |
| `studio/HALT` (file) | `/halt` OR touch | studio loop | existence = halt | boundary kill |
| `_ops/state/cockpit-requests.jsonl` | approval_channel button click | `wiring.cockpit_requests_beat()` | `{ts, verb, key, source, status}` whitelist=`_TG_EXEC_SAFE` (doctor, consolidate) | TG→organism |

**قواعد قرارداد:**
- همهٔ state files **در `.gitignore`** هستند (میگرت‌شده ۲۰۲۶-۰۷-۱۷) `[FACT]`.
- writes **atomic** یا **append-only** (هیچ read-modify-write از mount bash — درس از حادثهٔ truncate ۲۰۲۶-۰۷-۱۰).
- قرارداد kills: existence-based (file = halt) برای انسان-قابل‌دسترس بودن.

### 1.4 Data Ownership

| Data domain | Owner role | Storage | PII policy |
|---|---|---|---|
| **Content assets (RAW/EDITED/WM/NOWM/POSTED)** | C produces, A processes | local filesystem, encrypted archive | EXIF-stripped; cloud-sync OFF for RAW `[FACT]` |
| **Brand vault (22 assets)** | A curates | `langar/vault.json` (committed — brand seed, zero PII) | `[FACT commit 0a871e0]` |
| **Fan interactions** | A manages | `langar/fan_db.json` | zero PII by sha1(alias)[:12] construction |
| **Financial (gross/fee/net)** | A records | Fable5 DB9 / KPI | USD gross; tax-note for ATO |
| **KYC / identity** | Platforms hold (confidential) | NEVER in vault | `[FACT — CLAUDE.md]` |
| **Telegram bot tokens** | A | env vars / `langar_config.json` (.gitignore) | `[FACT]` — ⚠ PII risk see §۷ |
| **Decision/verdict history** | A | DecisionLog.md (append-only) | code-only references |
| **Capacity / boundary state** | C | studio/*.json | zero content echo |

### 1.5 HITL Points (Human-In-The-Loop — hard gates, never automated)

`[FACT — CLAUDE.md §8 "آنچه هرگز خودکار نمی‌شود" + CONTROL-MANIFEST.autonomy_model + SAFETY-NETS #1]`

| # | HITL point | Why | Mechanism |
|---|---|---|---|
| H1 | **Every DM send** (OF/X/Reddit) | ToS + brand voice + impersonation risk | DM HITL pipeline: `draft→pending_review→ready→sent` — NO `send()` method exists structurally `[FACT]` |
| H2 | **Every public post/publish** | boundary + opsec | `/pf_ok` + manual copy-paste |
| H3 | **Every account creation** | KYC + credentials | human-only (RUNBOOK Phase 2) |
| H4 | **Every price/offer decision** | hard-gated by charter | verdict per change |
| H5 | **Every payment/withdrawal** | legal + sanctions | human-only, at min-payout threshold |
| H6 | **Identity/boundary veto** | C boundary supreme | `/halt` (writes studio/HALT) |
| H7 | **First-hour Reddit comment replies** | anti-ban (value = humanness) | manual only |
| H8 | **Cultural dog-whistle signals** | rule #6 compliance | persona-sheet check per post |
| H9 | **Brand persona veto (per post)** | 2-person equality | persona sheet + either veto |
| H10 | **All X reply-game** | growth engine depends on humanness | 100% manual |
| H11 | **S4S negotiation + vetting** | anti-pod + ToS | human-only |
| H12 | **Custom video pricing + voice inclusion** | boundary + price | per-order verdict |

**تأیید ساختاری (CRITICAL):** در `brain/dm_pipeline.py` **هیچ متد `send/transmit/post` وجود ندارد** `[FACT — SAFETY-NETS §۱]`. این تضمینِ structural است، نه policy. یعنی حتی اگر یک bug هم بزند، auto-send غیرممکن است.

### 1.6 Kill-Switch Matrix

`[FACT — CONTROL-MANIFEST.kill_switches + SAFETY-NETS #3 + TELEGRAM-DEEP-SCAN §۴]`

| ID | Scope | Trigger | Effect | Reset | Owner |
|---|---|---|---|---|---|
| **KS1** | cockpit (langar) | `/kill` OR `touch langar/KILL` | refuses all cmds except /status,/revive | `/revive` (manual) | A |
| **KS2** | studio (C boundary) | `/halt` OR `touch studio/HALT` | studio halts; A notified; boundary supreme | `/resume` | C |
| **KS3** | brain-budget | spend > 2% cap OR > AUD 15/mo | fail-closed; LLM calls blocked | manual config | A |
| **KS4** | platform-warning (per channel) | 1 warning on channel X | channel X locked; `finalize()` denies X | `/clear_warning X` | A |
| **KS5** | full_stop (whole funnel) | ≥2 warnings on same channel | `full_stop=True`; `finalize()` denies ALL | `/clear_full_stop` (verdict) | A |
| **KS6** | doxxing signal | identity question in DM OR reverse-image hit | 48h post-stop; OpSec plan execution | `/revive` after safe | A |
| **KS7** | Warmup-Guard | Reddit karma < 20 + sales-item | `finalize()` denies (fail-closed) | `/report_karma ≥20` | A |
| **KS8** | organism-level | `touch STOP-ORGANISM` OR `HALT-ALL` | whole organism halts | manual file delete | A/human |
| **KS9** | telegram-center | `touch STOP-TG-CENTER` | TG center bot halts | manual file delete | A/human |
| **KS10** | containment guard | paypal/cashapp/crypto/identity/city in draft | flag; never approve | edit draft | structural |

**قاعدهٔ کلی:** همهٔ kill-switchها **fail-closed** هستند (فایل خراب = محتاطانه‌ترین حالت). `[FACT — SAFETY-NETS §۳]`

---

## 2. Open Verdicts Board (only undecided items that block design or launch)

> منبع: `VERDICT_QUEUE.md` (۲۰۲۶-۰۷-۱۶) + `OpenQuestions.md` + `THREAD-CLOSURE-D §۹`. verdictهای بسته‌شده (PF-V4 rules yes, PF-STATE-RESET done, PF-LAUNCH-SAFETY done) حذف شده‌اند.

| ID | Question | Options | Recommendation | Why | Required before page? |
|---|---|---|---|---|---|
| **OV-1** | GATE 0 کامل شود (از temporary-A به قفل‌شده)؟ | (a) record Branch A explicitly + sign 2-person agreement (b) keep temporary-A (c) Branch B (halt Track A) | **(a)** — ثبت صریح + توافق مکتوب | temporary-A یعنی ریسک حقوقی/مالیاتی هنوز بی‌پوشش؛ PF-V3 (توافق) deferred تا اولین درآمد ولی ریسک قبل از درآمد هم هست | **N (code)** / **Y (real payout)** |
| **OV-2** | برند = Anar Soles؟ (یا Arch & Amber / Yalda Arch) | (a) Anar Soles (b) Arch & Amber (c) Yalda Arch (d) other | **(a) Anar Soles** + reserve Yalda Arch | صفر collision (تأیید ۰۷-۰۵)؛ سیگنال دیاسپورا فقط بصری؛ نام‌های شهری حذف (نقض #۶) `[FACT 12-prelaunch]` | **Y (bio/handle)** |
| **OV-3** | Fansly: mirror vs discovery-first vs equal-weight? | (a) mirror-only (b) mirror + discovery-first (c) equal-weight day-1 | **(b) mirror + discovery-first** | FYP مزیت ساختاری برای faceless؛ تولید یک‌بار (هزینهٔ mirror)؛ زمان‌بندی مستقل `[FACT round2 §۲.۲]` | **Y (Fansly page)** |
| **OV-4** | نردبان قیمت (۳ نسخه): کدام قفل شود؟ | (a) EXT-04: `$3-5/8-15/15-30/custom$25+`, VIP frozen (b) MASTER-BUILD VIP $35 (c) Playbook VIP $20 | **(a) EXT-04** + VIP frozen till G2 | شواهد round2 (فقط free-page price-lock + نیش) به EXT-04 نزدیک‌تر؛ VIP $35 با «مُد=صفر» ماه‌های اول ناسازگار | **Y (PPV page)** |
| **OV-5** | «Persian»/«Sydney» در کپی عمومی؟ | (a) ban both (rule #6) (b) allow Persian visual-only (c) allow textual | **(a) ban textual, visual-only OK** | ۲ قاعدهٔ قفل‌شده ممنوع؛ Playbook خود نقض دارد؛ ریسک شناسایی `[FACT CLAUDE.md #۶]` | **Y (all copy)** |
| **OV-6** | body expansion در production plan: freeze یا remove؟ | (a) freeze (b) remove (c) keep | **(a) freeze** | C رد کرده؛ نگه‌داشتن در سند = ریسک رابطه‌ای؛ اما «freeze» vs «remove» تصمیم دونفره | **N** |
| **OV-7** | بلاک AU در OF؟ | (a) yes (b) no (c) revisit G2 | **(b) no for now, revisit G2** | در validation بازار AU valuable؛ ریسک شناسایی محلی با opsec مدیریت‌شود | **Y (OF geo settings)** |
| **OV-8** | X labeling mode: sensitive-media ON از اول؟ | (a) ON از اول (b) per-post (c) OFF | **(a) ON از اول** | مسیر امن؛ buyer نیچ این تنظیم را روشن دارد `[FACT blueprint §۵]` | **Y (X account)** |
| **OV-9** | سقف مغز AI: AUD 15/moth تا اولین درآمد؟ | (a) yes 15 (b) lower (c) higher | **(a) yes AUD 15** | هزینهٔ واقعی ≈AUD 8-12 `[EST]`؛ 2%-cap با درآمد صفر = صفر؛ fail-closed موجود | **N** |
| **OV-10** | قاعدهٔ «بالانس >$100 نماند»؟ | (a) yes $100 (b) min+ε (c) other | **(a) yes $100** | اختیار توقیف ToS + گذار مالکیتی OF + بند Fanvue dormancy | **Y (after payout)** |
| **OV-11** | فعال‌سازی Langar bot (BotFather + shadow week)؟ | (a) activate now (b) after warm-up (c) never | **(a) activate now + 1 week shadow** | pre-requisite برای RUNBOOK؛ قاعدهٔ charter: اتوماسیون جدید بعد از ۱ هفته shadow | **Y (Phase 1)** |
| **OV-12** | PF-STRUCT-V2: اجرای MIGRATION-MAP (dedup + filing)؟ | (a) yes-all (b) docs-only (c) later | **(b) docs-only not code** | dedup md5 انجام‌شده؛ code سرجایش؛ نظم‌دهی مستندات = opsec + cognitive load | **N (but recommended)** |
| **OV-13** | PF-CODE-REFACTOR-V1: rename شناسه‌های حاوی نام C در studio/؟ | (a) yes (b) deferred (c) no | **(b) deferred** | PII در git نیست (فقط hygiene) `[FACT VERDICT_QUEUE]` | **N** |
| **OV-14** | بستن #۱۸: سقف واقعی PPV/tip در داشبورد OF؟ | verify day-1 dashboard | verify at launch | منابع متناقض ($50/$100/$200) `[FACT round2 §۲]` | **Y (verify only)** |
| **OV-15** | پیام به C ارسال شود (RUNBOOK Phase 0)؟ | (a) send now (b) draft only | **(a) send now** (after OV-1/OV-2 decided) | pre-requisite برای هر step بعدی | **Y (first step)** |

** verdictهای بسته‌شده (برای records، نه open):** PF-V4 (8 rules yes) · PF-STATE-RESET (done) · PF-LAUNCH-SAFETY (done) · سؤال #۴ (ساعت C = ~۳h). `[FACT]`

---

## 3. Page Launch Runbook (step-by-step, conditional on GATE state)

> **پیش‌فرض:** Full Aggressive تأیید شده (PF-V5=no→plan کامل)؛ safety nets ساخته‌شده (PF-LAUNCH-SAFETY=done). اما GATE 0 فقط temporary-A است (OV-1) و هیچ اجرای بیرونی تا کنون.

### Phase 0 — Verdicts / docs freeze (قبل از هر outward action)

| Step | Owner | Tool | Acceptance test | Rollback |
|---|---|---|---|---|
| 0.1 بستن OV-1 (GATE 0 کامل) | A | DecisionLog | خط ثبت‌شده در PROJECT.md: «محل اقامت: ___ · Branch A · تاریخ» | n/a (yet to act) |
| 0.2 بستن OV-2 (برند) | A+C | 2-person DecisionLog | handle availability confirmed (X/Reddit/OF + Google + IP Australia) | revert to placeholder |
| 0.3 بستن OV-3,4,5,7,8 (۵ verdict سریع) | A | DecisionLog | ۵ ردیف verdict بسته | edit DecisionLog |
| 0.4 freeze docs ( mark stale superseded) | agent | SOURCE-OF-TRUTH-MATRIX update | HANDOFF-NEXT-AGENT (07-12) علامت‌گذاری stale؛ CONTROL-MANIFEST status_snapshot به‌روز | git revert |
| 0.5 ارسال پیام به C | A | Telegram (use `drafts-awaiting-gate/msg-to-saba-question8.md`) | جواب C ثبت‌شده در DecisionLog | n/a |

**GATE condition → Phase 1:** OV-1 closed + پیام به C ارسال‌شده + ۵ verdict بسته.

### Phase 1 — OpSec + accounts hygiene

| Step | Owner | Tool | Acceptance test | Rollback |
|---|---|---|---|---|
| 1.1 ایمیل برند (Proton) + password manager + 2FA TOTP | A | ProtonMail | ایمیل فعال؛ recovery codes چاپ‌شده | close email |
| 1.2 مرورگر/پروفایل جدا (zero overlap با personal) | A | browser profile | profile isolated | delete profile |
| 1.3 VPN همیشگی هنگام کار روی برند | A | VPN | IP leak test clean | n/a |
| 1.4langar_config.json کامل (blocklist + token + chat_id) | A | editor | `/status` responds in Telegram | revoke token + regenerate |
| 1.5 ⚠ **PII rotation check** (اگر langar_config قبلاً push شده) | A | git log + history scrub | no PII in git history | rotate credentials |
| 1.6 Langar bot shadow-mode (۱ هفته) | A | BotFather + langar_bot.py | `/status` `/guards` `/pf_status` `/dm_status` all respond | `/kill` |

**Acceptance test for Phase 1:** all OpSec items ticked (THREAD-CLOSURE §۴ الف تا ز) + Security Gate opens + bot shadow-mode ۷ روز موفق.
**Rollback:** `/kill` + close accounts.

### Phase 2 — Link-hub + tracking

| Step | Owner | Tool | Acceptance test | Rollback |
|---|---|---|---|---|
| 2.1 GAML Creator ($9) | A | getAllMyLinks | hub live + 18+ gate + Iran geo-filter | cancel subscription |
| 2.2 AllMyLinks (mirror, free) | A | AllMyLinks | mirror active | delete |
| 2.3 tracking links per channel | A | OF settings + `drafts-awaiting-gate/tracking-link-design` | 4+ links: reddit-main · x-bio · x-pin · hub-direct | n/a |
| 2.4 (optional) domain + Cloudflare | A | Cloudflare Free | WAF rule `(ip.src.country eq "IR")` Block | remove rule |

**Acceptance:** geo-filter test (IR-blocked) + tracking shows in dashboard.
**Rollback:** cancel GAML.

### Phase 3 — OF page (Free, 90 days first)

| Step | Owner | Tool | Acceptance test | Rollback |
|---|---|---|---|---|
| 3.1 OF account creation + KYC | A (human-only) | OnlyFans | KYC verified | close account |
| 3.2 geo-block Iran (Settings → Privacy → Geoblocking) | A | OF settings | Iran in block list | remove (never) |
| 3.3 banner/avatar/bio (from drafts x-profile, SFW, no geo-fact) | A | OF + drafts | 4-line bio: who/what/differentiator/CTA | edit |
| 3.4 ≥۱۰ feed posts before first traffic | A+C | content pipeline | 10 posts live | delete posts |
| 3.5 welcome flow (3 sentences, polarizing question) | A | OF native | welcome sent on new sub | edit |
| 3.6 **NO content yet** (verify-only per RUNBOOK §۲.۵) | A | — | page exists, empty | n/a |

**Acceptance:** OF page verified + Iran-geo-blocked + bio live + 10 posts.
**Rollback:** close account (_irreversible_ — caution).

### Phase 4 — Fansly page (per adopted strategy: mirror + discovery-first)

| Step | Owner | Tool | Acceptance test | Rollback |
|---|---|---|---|---|
| 4.1 Fansly account + KYC | A (human-only) | Fansly | verified | close |
| 4.2 geo-block Iran | A | Fansly settings | Iran blocked | remove (never) |
| 4.3 mirror OF content (one production, two outputs) | A | content pipeline | same asset, Fansly-native scheduling | n/a |
| 4.4 discovery-first setup (FYP-optimized scheduling) | A | Fansly native | scheduling independent from OF | n/a |

**Acceptance:** Fansly mirror live + discovery-first configured.
**Rollback:** close.

### Phase 5 — Dry-run content (no public if blocked)

| Step | Owner | Tool | Acceptance test | Rollback |
|---|---|---|---|---|
| 5.1 VaultBank wiring (inject into `pf_admin._default_pipe()`) | agent | code (1 line) | `/pf_plan` pulls from vault, not `_SAFE_HOOKS` `[FACT commit 0a871e0]` | revert to _SAFE_HOOKS |
| 5.2 LearningBridge default (Thompson bandit active) | agent | code (1 line) | `AcquisitionBrain.with_bandit(...)` used | revert to heuristic |
| 5.3 EXIF-strip + watermark batch on test images | A | exiftool + scripts | `exiftool -all=` verified on 3 files | n/a |
| 5.4 reverse-image search test (Google Lens/Yandex) | A | web | zero background matches | n/a |
| 5.5 Shoot #1 (batch 2×≤2.5h per M3-a) | C | camera | ≥۳۰ assets tagged WM/NOWM, buffer ≥۷ days | reshoot |

**Acceptance:** 30+ assets in vault + EXIF-stripped + reverse-image clean.
**Rollback:** discard assets.

### Phase 6 — Warm-up start criteria

| Step | Owner | Tool | Acceptance test | Rollback |
|---|---|---|---|---|
| 6.1 Reddit account (fresh or aged) + 72h read-only | A | Reddit | account active; 0 posts first 72h | abandon account |
| 6.2 Karma-building (SFW subs, 3-5 posts over 5-7 days) | A | Reddit | karma ≥۲۰ (triggers `/report_karma 20` → Warmup-Guard opens) | continue karma-building |
| 6.3 X account + bio + 3 SFW first posts | A | X | sensitive-media ON; bio live; 3 posts | edit/delete |
| 6.4 X reply-game daily (10-20 quality replies) | A | X manual | 5-10 bell notifications tracked | pause |
| 6.5 Friday KPI loop begins | A | `/kpi` + sheets | first row logged; report sent to C | n/a |
| 6.6 G1 evaluation at week 6 | A+C | metrics | ≥۲۰۰ clicks + ≥۱۰% click→follow + C delivery ≥۸۰% | pivot (not kill) channel-mix |

**Acceptance (Aggressive Launch unlocked):** `/guards` shows «✅ warm-up threshold met» → sales items allowed.
**Rollback:** continue warm-up; if 2 warnings → `/clear_full_stop` requires verdict.

---

## 4. 14-Day Execution Plan (after architecture freeze)

> **ظرفیت واقعی `[FACT]`:** A ~۸–۱۰ h/hفته · C ~۳ h/hفته · بودجهٔ warm-up ~A$13/mo → sprint ~A$45-75/mo.
> **گزارش به C (money-path visibility):** هر یکشنبه گزارش کوتاه (clicks/free/paid/revenue/hours) — شرط تعهد C `[FACT DecisionLog]`.

| Day | Date | Owner | Task | Tool | Est. time | Budget | Acceptance |
|---|---|---|---|---|---|---|---|
| **D1** | 2026-07-21 | A | Close OV-1/OV-2/OV-3/OV-4/OV-5/OV-7/OV-8 (7 verdicts) + update DecisionLog | DecisionLog | 1h | $0 | 7 verdict rows closed |
| **D2** | 2026-07-22 | A | Send message to C (`msg-to-saba-question8.md`) + freeze docs (mark HANDOFF-NEXT-AGENT stale) | Telegram | 30min | $0 | message sent; docs marked |
| **D3** | 2026-07-23 | A | Phase 1.1-1.4: Proton email + password manager + 2FA + browser profile + VPN + langar_config.json | tools | 2h | $0 | OpSec items 60% ticked |
| **D4** | 2026-07-24 | A | Phase 1.5-1.6: PII rotation check + Langar bot BotFather + shadow-mode start (week 1 of 1) | BotFather | 1h | $0 | `/status` responds |
| **D5** | 2026-07-25 | agent | Phase 5.1-5.2: wire VaultBank + LearningBridge (2 line-changes) + write regression test | code | 2h | $0 | tests green; `/pf_plan` from vault |
| **D6** | 2026-07-26 | A | Phase 2.1-2.4: GAML Creator + AllMyLinks + tracking links + (optional) Cloudflare | GAML $9 | 1.5h | A$13 | hub live; Iran-geo-blocked |
| **D7** | 2026-07-27 | A+C | **Sunday report #1 to C** (even if "zero") + sync on shoot scheduling | sheets | 30min | $0 | report logged |
| **D8** | 2026-07-28 | A | Phase 3.1-3.2: OF account + KYC + Iran geo-block (NO content) | OnlyFans | 1h | $0 | KYC verified |
| **D9** | 2026-07-29 | A | Phase 4.1-4.2: Fansly account + KYC + Iran geo-block | Fansly | 45min | $0 | verified |
| **D10** | 2026-07-30 | C | Phase 5.5: Shoot #1 batch 1 (≤2.5h, 3-4 set-ups) — per M3-a | camera | 2.5h | $0 | ~30 raw frames |
| **D11** | 2026-07-31 | A | Phase 5.3-5.5: EXIF-strip + watermark + cull → 15+ ready assets in vault | exiftool | 1.5h | $0 | 15+ assets tagged |
| **D12** | 2026-08-01 | A | Phase 6.1-6.2: Reddit account + 72h read-only start + X account + bio + 3 SFW posts | Reddit+X | 1h | $0 | accounts active |
| **D13** | 2026-08-02 | A | Phase 6.3-6.4: X reply-game day 1 (10-20 quality replies) + Reddit karma-building continues | X manual | 1h | $0 | replies tracked |
| **D14** | 2026-08-03 | A+C | **Sunday report #2 to C** + warm-up week 1 retrospective + plan week 2 | sheets | 45min | $0 | report logged |

**Budget total (14 days):** ~A$13 (GAML only) `[FACT — under A$200 cap]`.
**Time total:** A ~15-17h (within 8-10h/wk × 2) · C ~3h (within 3h/wk).
**Risk buffer:** D8/D9 (OF/Fansly KYC) may slip if verification slow — D12-D14 flex.

**After D14:** enter warm-up weeks 2-6 → G1 evaluation at week 6 (~2026-09-01).

---

## 5. Definitions of Done

### 5.1 Architecture-Complete Checklist (binary)

| # | Criterion | Status | Evidence |
|---|---|---|---|
| AC-1 | ۸ قاعدهٔ قفل‌شده مستند + immutable | ☑ YES | CLAUDE.md §1 + CONTROL-MANIFEST |
| AC-2 | نمودار معماری تو-به (to-be) فریز | ☑ YES | §۱.۱ این سند |
| AC-3 | Source-of-truth map (one owner per domain) | ☑ YES | §۱.۲ + SOURCE-OF-TRUTH-MATRIX |
| AC-4 | Event bus contracts تعریف‌شده | ☑ YES | §۱.۳ (file-based bridges) |
| AC-5 | Data ownership تعریف‌شده | ☑ YES | §۱.۴ |
| AC-6 | HITL points مستند (۱۲ نقطه) | ☑ YES | §۱.۵ |
| AC-7 | Kill-switch matrix کامل (۱۰ سوئیچ) | ☑ YES | §۱.۶ |
| AC-8 | Gate definitions G0-G4 عددی | ☑ YES | CONTROL-MANIFEST.gates + blueprint §3 |
| AC-9 | Safety nets پیاده‌سازی + تست (۳۸ تست) | ☑ YES | LAUNCH-SAFETY-NETS-2026-07-16 |
| AC-10 | Tests سبز (۱۴۸ تست) | ☑ YES | DEEP-SCAN §۵ |
| AC-11 | Runbook لانچ آماده | ☑ YES | LAUNCH-RUNBOOK-2026-07-16 |
| AC-12 | ۳ verdict طراحی‌ساز بسته (برند/Fansly/نردبان) | ☐ **NO** | OV-2/OV-3/OV-4 open |
| AC-13 | CONTROL-MANIFEST status_snapshot به‌روز | ☐ **NO** | still 2026-07-10 snapshot |
| AC-14 | ماژول‌های ۱-خطی فعال (VaultBank/LearningBridge/attach) | ☐ **NO** | DEEP-SCAN §۴ flags |

**Architecture-complete: ۱۱/۱۴ = ۷۹٪.** باقی‌مانده = ۳ کار انسانی/agent کوچک.

### 5.2 Page-Live Checklist (binary)

| # | Criterion | Status |
|---|---|---|
| PL-1 | GATE 0 کامل (نه temporary-A) | ☐ NO (OV-1) |
| PL-2 | برند قفل‌شده + handle موجود | ☐ NO (OV-2) |
| PL-3 | پیام به C ارسال + جواب ثبت | ☐ NO (OV-15) |
| PL-4 | OpSec checklist کامل (۲۴ آیتم) | ☐ NO |
| PL-5 | Langar bot live + shadow هفته‌ای موفق | ☐ NO |
| PL-6 | GAML link-hub live + Iran-geo-block | ☐ NO |
| PL-7 | OF page verified + Iran-geo-blocked + bio | ☐ NO |
| PL-8 | Fansly mirror live + Iran-geo-blocked | ☐ NO |
| PL-9 | ≥۳۰ assets در vault + EXIF-stripped | ☐ NO |
| PL-10 | ≥۱۰ feed posts در OF قبل از ترافیک | ☐ NO |
| PL-11 | Reddit account + karma ≥۲۰ | ☐ NO |
| PL-12 | X account + sensitive-media ON + 3 SFW posts | ☐ NO |

**Page-live: ۰/۱۲ = ۰٪.** (اجرای بیرونی صفر — تأیید `[FACT DEEP-SCAN §۲]`)

### 5.3 First-Dollar Checklist (binary)

| # | Criterion | Status |
|---|---|---|
| FD-1 | تمام PL items | ☐ NO |
| FD-2 | Warm-up کامل (karma ≥۲۰) | ☐ NO |
| FD-3 | اولین PPV ارسال ($5-8 per EXT-04) | ☐ NO |
| FD-4 | welcome flow فعال | ☐ NO |
| FD-5 | tracking ثبت‌شده در شیت | ☐ NO |
| FD-6 | G1 پاس (≥۲۰۰ clicks, ≥۱۰% follow) | ☐ NO |
| FD-7 | اولین paid sub | ☐ NO |
| FD-8 | اولین AUD 100 gross | ☐ NO |
| FD-9 | برداشت در آستانهٔ min (>$100 rule) | ☐ NO |
| FD-10 | G2 پاس (هفته ۱۲) | ☐ NO |

**First-dollar: ۰/۱۰ = ۰٪.**

---

## 6. Risk Register (top 12)

`[FACT basis: architecture-blueprint §۱۰ + MASTER-BUILD + DEEP-SCAN §۸ + TELEGRAM-DEEP-SCAN pitfalls]`

| # | Risk | Likelihood | Impact | Mitigation | Owner | Early-warning metric |
|---|---|---|---|---|---|---|
| **R1** | consistency C زیر friction (تنها ریسک تست‌نشده، score 20/25) | HIGH | CRITICAL | گزارش هفتگی پول به C + شوت batch + agreement §۴.۱ + مکانیزم «همون لحظه بگو» | A+C | delivery <80% (2 weeks) → گفتگو ساختار |
| **R2** | GATE 0 واقعاً Branch B (C داخل ایران) — temporary-A فرضی اشتباه باشد | LOW-MED | **CATASTROPHIC** | قبل از اولین payout: تأیید نهایی + مشاور licensed؛ halt Track A اگر B | A | هر سیگنال متناقض از C |
| **R3** | PII leak از `langar_config.json` (اگر قبلاً push شده) | MED | HIGH | git history scrub + rotation؛ فایل در .gitignore از commit `26a1955` | A | git log search for PII strings |
| **R4** | ban پلتفرم (OF) به‌خاطر AI-chat | MED | HIGH | DM HITL structural (no send method) `[FACT]` + ToS-safe pattern | A | any OF warning → KS4/KS5 |
| **R5** | shadowban Reddit (لینک زودهنگام) | MED-HIGH | HIGH | WarmupGuard (karma<20 → deny) `[FACT]` | A | post visibility drop / karma stall |
| **R6** | تلاطم مالکیت OF (فوت Radvinsky، فروش به Architect Capital $3.15B) | MED | MED | دو-پلتفرمه از روز اول + Fansly mirror + پایش فصلی `[FACT]` | A | OF policy news quarterly |
| **R7** | توهم اجرا (temporary-A به‌عنوان قفل‌شده تفسیر شود) | MED | HIGH | OV-1 صریح: complete GATE 0 قبل از payout | A | any payout attempt before OV-1 |
| **R8** | تعارض bot-ID تلگرام (8187434784 dual; 7992324219 dual → 409 Conflict) | MED | MED | only one polls at a time; unify tokens `[FACT TELEGRAM-DEEP-SCAN]` | A | 409 errors in log |
| **R9** | VPN circumvention از Iran geo-block | HIGH (unsolvable) | LOW | layered geo-block (OF+Fansly+GAML+Cloudflare)؛ پذیرش residual `[FACT]` | A | n/a (known limit) |
| **R10** | body expansion در production plan نقض شود (C رد کرده) | LOW | HIGH | OV-6: freeze رسمی + persona-sheet gate per post | A+C | any body content in draft |
| **R11** | «Persian/Sydney» در کپی عمومی (Playbook نقض دارد) | MED | MED | OV-5: ban textual, visual-only؛ Playbook fix | A | grep in drafts |
| **R12** | فعال‌سازی Octopus نیمه‌سیم (attach_to_langar هرگز صدا زده نمی‌شود) | LOW | LOW | defer to post-launch؛ not launch-critical `[FACT DEEP-SCAN §۴]` | agent | n/a (isolated) |

---

## 7. Exact Files to Write/Update Now (paths)

| # | Path | Action | Why |
|---|---|---|---|
| 1 | `F:/backup/03 - Projects/اونلی فنز/00 - Control/SYNTH-05-FINAL-PACKAGE-2026-07-20.md` | **WRITE (this doc)** | single package — architecture freeze + runbook |
| 2 | `F:/backup/03 - Projects/اونلی فنز/VERDICT_QUEUE.md` | UPDATE | add 15 OV-* rows from §۲ (replace stale 11-verdict list) |
| 3 | `F:/backup/03 - Projects/اونلی فنز/PROJECT.md` | UPDATE Active Context | point to SYNTH-05 as canonical freeze; mark HANDOFF-NEXT-AGENT (07-12) stale |
| 4 | `F:/backup/03 - Projects/اونلی فنز/PROJECT-F-CONTROL-MANIFEST.json` | UPDATE status_snapshot | reflect 2026-07-16 pivot (PF-V5, safety nets done, 148 tests); gates.G0 = "temporary-A" |
| 5 | `F:/backup/03 - Projects/اونلی فنز/DecisionLog.md` | APPEND | row: "2026-07-20 — SYNTH-05 architecture freeze produced (degraded conf: 4 scans absent)" |
| 6 | `F:/backup/03 - Projects/اونلی فنز/00 - Control/HANDOFF-NEXT-AGENT.md` | ANNOTATE header | prepend: "⚠ STALE (2026-07-12, pre-pivot) — read SYNTH-05 + DEEP-SCAN-2026-07-17 first" |
| 7 | (optional) `F:/backup/03 - Projects/اونلی فنز/Feet-Content-Business-Master-Playbook.md` | ANNOTATE | flag «Persian/Sydney» violation (rule #6) for OV-5 fix |

**Files I will NOT touch (out of scope or hard-gated):** code modules (VaultBank/LearningBridge wiring — agent task after verdicts) · platform accounts · `langar_config.json` (PII).

---

## 8. Single Message to Human Operator: "Do these 5 things next in order"

> **A، این ۵ قدم را به ترتیب انجام بده. هیچ‌کدام قبل از قدم قبلی شروع نشود.**

1. **(۵ دقیقه) ۷ verdict را ببند.** جدول §۲ این سند را باز کن؛ برای OV-1 (GATE 0 کامل از temporary-A)، OV-2 (Anar Soles)، OV-3 (Fansly mirror+discovery)، OV-4 (EXT-04 ladder)، OV-5 (ban Persian/Sydney textual)، OV-7 (no AU block)، OV-8 (X sensitive-media ON) یک yes/no بده. فقط این را در DecisionLog ثبت کن.

2. **(۳۰ دقیقه) پیام را به C بفرست.** فایل `drafts-awaiting-gate/msg-to-saba-question8.md` را در تلگرام بفرست. جوابش را (حتی «بعداً») در DecisionLog ثبت کن. این قلب شرط تعهد اوست.

3. **(۲ ساعت) Phase 1 OpSec + Langar bot.** ایمیل Proton + password manager + 2FA + browser profile جدا + VPN. سپس در BotFather یک bot بساز، token را در `langar_config.json` (که در `.gitignore` است) بگذار، و `/status` را در تلگرام تست کن. **هشدار:** اگر `langar_config.json` قبلاً push شده، اول credentialها را rotate کن.

4. **(ویژه: agent) ۲ خط کد + ۱ تست.** به agent بعدی بگو: (الف) `VaultBank()` را در `pf_admin._default_pipe()` inject کن؛ (ب) `AcquisitionBrain.with_bandit(...)` را پیش‌فرض کن؛ (ج) یک regression test بنویس. این بی‌نیاز به GATE 0 است و بزرگ‌ترین ارتقای هوش است.

5. **(۶۰ دقیقه) Phase 2 link-hub + Phase 3/4 OF/Fansly.** GAML را بساز (A$13) + Iran geo-filter. سپس OF Free page + Fansly را با KYC بساز (فقط verify، **هنوز هیچ محتوا نذار**) و geo-block Iran را در هر دو فعال کن.

**بعد از این ۵ قدم:** وارد فاز warm-up می‌شی (Reddit karma-building تا ۲۰ + X reply-game). اولین گزارش یکشنبه به C را فراموش نکن — حتی اگر صفر است.

---

## 9. CONFIDENCE / RESIDUAL UNKNOWNS

### Confidence: **65/100** (degraded)

### Why degraded (P0 blockers):
- **خروجی‌های اسمیِ ARCH-SCAN-01, GATE-SCAN-02, FUNNEL-SCAN-03, RUNTIME-SCAN-04 هرگز ساخته نشده‌اند.** `[FACT — جستجوی تمام vault]` این پکیج با proxy scan ها ساخته شده (`ARCHITECTURAL_SCAN_REPORT_2026-07-13`, `TELEGRAM-DEEP-SCAN-2026-07-17`, `DEEP-SCAN-2026-07-17`).
- **GATE 0 فقط temporary-A است** — ریسک حقوقی/مالیاتی/تحریمی هنوز بی‌پوشش `[FACT VERDICT_QUEUE PF-V1/V2]`.
- **۳ verdict طراحی‌ساز باز** (برند/Fansly/نردبان) — نمودار معماری ۳ نقطهٔ PROPOSAL دارد.

### BLOCKERS (ranked):
- **P0-1:** خروجی ۴ scan اسمی غایب — اعتبارسنجی مستقلِ runtime/funnel/gate ممکن نیست. (توصیه: اجرای ۴ scan قبل از لانچ واقعی.)
- **P0-2:** GATE 0 کامل نشده — temporary-A نباید به‌عنوان قفل‌شده تفسیر شود (R7).
- **P1-1:** ۳ verdict طراحی‌ساز باز (OV-2/3/4).
- **P1-2:** PII در `langar_config.json` — rotation check قبل از active‌سازی (R3).
- **P2-1:** CONTROL-MANIFEST snapshot کهنه (۲۰۲۶-۰۷-۱۰) — status_snapshot باید به‌روز شود.
- **P2-2:** ماژول‌های ۱-خطی فعال‌نشده (VaultBank/LearningBridge/attach_to_langar).

### WHAT I COULD NOT SEE:
1. **خروجی ۴ scan اسمی** — هرگز ساخته نشدند (§۰).
2. **خروجی واقعی RUNTIME-SCAN-04** — proxy: `TELEGRAM-DEEP-SCAN` فقط تلگرام را پوشش داد، نه runtime کامل. وضعیت واقعی organism `_ops/` خارج از scope بود.
3. **وضعیت live اکانت‌ها** — چون صفر اجراست، نمی‌توانم verify کنم که آیا Really هیچ اکانتی وجود ندارد یا فقط در vault ثبت نشده (off-vault execution possibility).
4. **مشاورهٔ licensed** — سؤالات Track B (ABN/GST/sanctions/cross-border) در `THREAD-CLOSURE §۵` آماده است اما هیچ مشاوره‌ای گرفته نشده `[FACT]`.
5. **محتوای `_ops/` بیرون از پروژه** — `orchestrator.py` به `_ops/neural` وابسته است که در scope پروژه نیست؛ DEEP-SCAN آن را «dead at runtime» علامت زده اما وضعیت واقعی organism نمی‌تواند در این session تأیید شود.
6. **state files runtime** — `langar/*.json` (نظیر KILL/HALT/fan_db) خوانده نشدند چون runtime state (نه source) هستند و در `.gitignore` هستند.

---

> **Verification pass:** هر ادعا با فایل منبع cross-check شد؛ هیچ قاعدهٔ قفل‌شده‌ای لمس نشد؛ هیچ hard-gated adopted نشد؛ هیچ PII echo نشده. تمام نقش‌ها code-only هستند (A/C). بیرون پوشه فقط «Project-F».
>
> *End of SYNTH-05 FINAL PACKAGE — 2026-07-20.*
