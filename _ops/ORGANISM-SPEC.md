---
type: architecture
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
tags: [metabolic-governor, debate, replication, organism]
created: 2026-07-06
updated: 2026-07-07
created_by: agent
sources:
  - "[[00 - Inbox/2026-07-06 1930 PROMPT-PACK — سه پرامپت مرحله‌ای (متابولیسم-مناظره-تکثیر)]]"
  - "[[04 - Architect System/2026-07-06 METABOLIC-GOVERNOR-proposal]]"
  - "[[00 - Inbox/2026-07-06 2150 ORGANISM-BUILD-HANDOFF — ساخت لایه متابولیسم-مناظره-تکثیر و نقشه ادامه]]"
---

# ORGANISM-SPEC — سند «کل واحد» لایهٔ متابولیسم-مناظره-تکثیر

> یک ارگانیسم، سه لایه، یک پروسهٔ همیشه-روشن. همه‌چیز additive و سایه ($0)؛
> ‏budget_gate تنها enforcer می‌ماند؛ هیچ مسیر زنده‌ای بدون گیت دوقفلهٔ مالک باز نمی‌شود.

## ۱) سه لایه

| لایه | استعاره | چه می‌کند | ماژول‌ها |
|---|---|---|---|
| **آناتومی** (MycoLedger) | بافت/حافظه | ثبت append-only هر رویداد در ledger زنجیرهٔ‌هش ژنوم (`NOTE`+subtype) + stateهای ماشین‌خوان `_ops/state/` | `opslib.py` (پل ledger، مسیرها، LockedJson) |
| **فیزیولوژی** (Heart) | ضربان/جریان | حلقهٔ همیشه-روشن: تیک ۵دقیقه‌ای، heartbeat ساعتی، کارهای روزانه، سرور وضعیت | `organism.py` + `RUN-ORGANISM.bat` |
| **متابولیسم** (Governor) | انرژی/سهمیه | تلمتری واحد دو استک → گیت per-organ → گاورنر سایه (epoch آلوستاتیک) → fitness/تکثیر (پیشنهادی) | `telemetry.py` · `organ_gate.py` · `governor_epoch.py` · `fitness.py` · `replication.py` · `debate/` |

## ۲) نگاشت ماژول‌ها (همه در `_ops/`)

| فایل | نقش یک‌خطی |
|---|---|
| `budget/opslib.py` | کتابخانهٔ مشترک: مسیرها/env، micro-USD، نرخ پین ارز، `LockedJson`، پل ledger ژنوم (`ledger_note`)، پرچم‌های STOP/FREEZE/ACTIVATION، `live_gate_open` (گیت دوقفله)، heartbeat/alert/CONFLICT |
| `budget/telemetry.py` | خوانندهٔ واحد دو منبع حقیقت (ledger.jsonl ژنوم + core.db/usage مغز، فقط‌خواندنی ro) → snapshot میکرو-USD per-organ + تلهٔ «متر صفر» + تطبیق I3 (FREEZE + شرط مرگ STOP-METABOLIC در واگرایی >۲۰٪) |
| `budget/organ_gate.py` | گیت per-organ *روی* budget_gate (نه جایگزین): ‏STOP→FREEZE→ارگان→state→سقف ماهانهٔ ارگان→budget_gate.reserve؛ deny هر لایه = deny کل؛ لاگ در `organ-gate-log.jsonl` |
| `budget/governor_epoch.py` | گاورنر سایه: epoch **آلوستاتیک** (طول epoch تابع فشار: velocity/deadline/anomaly — نه clock)؛ dry قطعی $0 پیش‌فرض؛ مود LLM دوقفله؛ خروجی `budget/epochs/epoch-*.json` + ‏NOTE(ALLOCATION_SHADOW) |
| `budget/fitness.py` | برازندگی per-cell؛ «پذیرش» فقط از `logs/outbox.jsonl` با ‏status='sent' (کلیک انسان) + تطبیق core.db؛ mismatch>۱۰٪ = حذف cell + alert؛ ‏`authoritative:false` تا ۲۸ روز دادهٔ EXPERIENCE |
| `budget/replication.py` | ‏σ_effective از ledger؛ ‏σ>1 = ALERT محور سرطان + توقف؛ ‏MAX_CELLS=6، عمق ۱؛ فقط ‏SPAWN_PROPOSAL ‏human-gated — هرگز spawn واقعی؛ ‏PROJECT_F مستثنا |
| `debate/client.py` | کلاینت stdlib ‏DeepSeek؛ ‏model/base_url فقط از budgets.yaml؛ کلید فقط `DEEPSEEK_API_KEY`؛ گارد نشت host؛ قیمت قفل‌نشده = خطا؛ est بدترین‌حالت |
| `debate/topics.py` | موضوع فقط از whitelist (seed + plan.yaml ژنوم + ارگان‌های budgets)؛ truncate ۲۰۰۰؛ پوشش ‹‹‹ ››› + GUARD_SENTENCE ضدتزریق |
| `debate/debate_loop.py` | ‏limit cycle خلاق×معمار ‏≤۳ دور؛ هر call گیت‌خورده؛ هر دور ‏NOTE(EXPERIENCE)؛ بازمانده → ‏`SURVIVORS-QUEUE.md` + ‏PROPOSAL هفت‌فیلدی برای دکتر ژنوم؛ ‏stub آفلاین $0 پیش‌فرض |
| `organism.py` | وحدت‌بخش: kill-check → تلمتری/تطبیق → epoch در سررسید → روزانه fitness/σ + ‏NOTE(ORGANISM_DAILY) → heartbeat ساعتی → state + HTTP ‏127.0.0.1:8771؛ ‏bind انحصاری = قفل تک‌نمونه |
| `RUN-ORGANISM.bat` | لانچر ۳۰روزه (UTF-8، حلقهٔ restart، CRLF)؛ kill تمیز = فایل `_ops/STOP-ORGANISM` |
| `tests/` | سوئیت ایزوله (vault موقت در TEMP): ‏`python -X utf8 _ops/tests/run_all.py` — ۱۳ فایل (شامل chrono heart/langar) |
| `04 - Architect System/prompts/` | سه role-prompt: ‏metabolic-governor-v0.1 · debate-muse · debate-architect |

## ۲.۵) لایهٔ Chrono (Phase 1: THE HEART) — `_ops/chrono.py`

بسترِ زمان/ضربان که روی سیستم سوار شد (additive؛ منطق کسب‌وکار دست‌نخورده — DOC-B §۰). منابع: `CHRONOS-FABLE-OS/10_Implementation/DataSchemas.sql` + `OCTOPUS_CHRONO_ARCHITECTURE §۸/۹/۱۱` + `HeartDesign_PulseCore`. env-tunable؛ $0 آفلاین.

| جزء | کار |
|---|---|
| **Pacemaker** | تیک ~۶۰s (`CHRONO_PERIOD_S`): ack→phi→اکنونِ مشترک (`hlc_max`)→broadcast→experience+wear→scheduler بر حسب نبض (**F19 بسته شد**)→heartbeat row + checkpoint سبک. تنها writerِ دیسک (تک-writer). |
| **HLC** | ساعتِ منطقیِ هر پا (CockroachDB algo)؛ هر رویداد مهرِ HLC می‌گیرد. **TINV-5:** پا هرگز wall-clock نمی‌خواند. |
| **phi-accrual** | liveness هر پا: alive→suspected→failed (`CHRONO_PHI_SUSPECT/DEAD`)؛ قلاب `doctor.restart_from_known_good(leg, db)` برای Phase 2. |
| **LANGAR arrow `age_tick`** | روی ledger ژنوم (v0.4.5؛ جدولِ رقیب نه). **TINV-3 (as-built):** ‏+۱ فقط با `is_human=1`؛ برگشت = شکست زنجیره = مرگ منطقی. ✅ **v0.4.6 (verdict مالک 2026-07-08): heart-driven پیاده شد** — ‏+۱ با `is_human=1` **یا** heartbeat (`beat=1`، هر `CHRONO_AGE_PER_N_BEATS`=۱۴۴۰، روزانه)؛ versioned با `age_rule` تا legacy (TINV-3ِ قدیم) verify شود. تأییدِ Windows-side مانده — [[00 - Inbox/AGENT_QUESTIONS|AGENT_QUESTIONS]]. |
| **دو-ساعت** | `experience_rate`=events/Δt_pacemaker، کران‌دار [0,`CHRONO_XP_RATE_CAP`]؛ `metabolic_age`=فرسایشِ ضربان‌محورِ per-leg (`CHRONO_WEAR_BASE`). |
| **EffectorGate** | **TINV-7:** هیچ اثرِ برگشت‌ناپذیر (`send/publish/sync/pay`) بدونِ LANGAR-append قبلی settle نمی‌شود؛ تک‌گلوگاه؛ kill/FREEZE = force-close. |
| **state** | `_ops/state/chrono.db` (SQLite/WAL) — runtime؛ در اولین beat ساخته می‌شود؛ کاندید gitignore (open-decision #8). |

سوار در `organism.py` با `start_pacemaker_thread()` (additive، fail-soft — شکست chrono متابولیسم را نمی‌کشد)؛ فقط پس از restartِ مالک سوار می‌شود (INC-1). تست: `test_chrono_heartbeat.py` (۹ چک) + `test_chrono_langar.py` (۶ چک).

## ۲.۶) لایهٔ Legs / Worker (Phase 4) — `_ops/legs/`

چارچوبِ پاهای پروژه (workerهای ایزوله). ایزولاسیون طبقِ `CHRONOS-FABLE-OS/08_Safety/IsolationModel.md` (INV-17) و `11_Agents/AgentInstructions.md` (Worker Guard). additive؛ $0 آفلاین.

| جزء | کار |
|---|---|
| **`TaskPacket`** | بستهٔ حداقلیِ هر پا: read-allowlist (فقط IDهای مشخص، هرگز wildcard)، toolsِ scoped، budget سخت، `spawn=0`، `secrets=[]` (همیشه خالی). verify ساختاری در `__init__` (fail-closed). |
| **`Leg`** (پایه) | workerِ ایزوله: بارگذاریِ packet، خواندنِ بریفِ allowlistedش، تولیدِ `Proposal` (HLC-stamped)، عبور از `organ_gate.reserve/settle`. **propose-only:** هیچ متدِ send/publish/pay. `money_link` (INV-14): organِ حل‌نشده = `incubating`. |
| **`Proposal`** | تنها خروجیِ مجازِ پا (D3 structural output confinement): proposal_id، leg_id، kind، payload، hlc، hash (provenance D5). approval = eventِ جداگانهٔ انسانی. |
| **`LeadLeg`** (L-1) | پا Lead-نقاشی: `intake` → `draft_quote` (attribution_id چاپ‌شده) → `claim` (CLAIMED نه CONFIRMED)؛ CONFIRMED کارِ `reconcile` است. هر تماسِ مشتری human-gated (از کانالِ P3). |

تست: `test_leg.py` (۲۴ چک — ایزولاسیونِ L-0 + دلارِ paperِ L-1). **گیتِ P4:** اولین دلارِ paper با attributionِ درست CONFIRMED شد (`t_paper_dollar_full_cycle`: PROPOSAL→CLAIMED→CONFIRMED→ATTRIBUTED).

⚑ برای معمار: `Lead-نقاشی` هنوز در `budgets.yaml` به‌عنوان organ ثبت نشده → پا `incubating` می‌ماند تا اضافه شود (INV-14؛ SoT، human-gated). اتصالِ Leg به `ChronoBus.register_leg` و intake از P3 channel در runtime = فازِ بعد.

## ۲.۷) لایهٔ Doctor / Evolutionary (Phase 2) — `_ops/doctor/`

انگلِ تکاملیِ روی سرِ ارگانیسم (DOCTOR-BLUEPRINT-v1.md §۴ پیاده شد). هر N ضربان از Pacemaker اجرا می‌شود، گلوگاه پیدا می‌کند، RFC تولید، sandbox+Critic، و برای merge فقط `submit_for_approval` را صدا می‌زند (P3 کارتِ [merge]/[reject]). **هیچ merge بدونِ human-append.** نرخِ تکامل = نرخِ حضورِ انسان. منابع: `CHRONOS-FABLE-OS/11_Agents/AgentInstructions.md` AGENT-08 + `08_Safety/HeartDesign_PulseCore.md` (reward-integrity، λ_persist منفی). additive؛ $0 آفلاین.

| جزء | کار |
|---|---|
| **`stable_read(path)`** (D-1) | دروازهٔ خواندنِ پایدار (جایگزینِ heuristicِ `VERIFY_RULES`). verdict ∈ {stable, stale, corrupt, needs_source_verify, missing}. ضدِ torn-snapshot FP: U+FFFD → needs_source_verify نه false-corrupt. |
| **`mine(trace)`** (D-2) | گلوگاه از heartbeat/ledger/state. reward-integrity: بر اساسِ اختلال (errors/freeze/σ)، نه activity/uptime (λ_persist=-1.0). |
| **`propose_rfc(bottleneck, fix, lift)`** (D-3) | RFCِ ساختاریافته → knowledge/internal (proposal-event، نه تغییرِ کد). |
| **`run_sandbox(rfc)` + Critic** (D-4) | اعمال در sandbox موقت + اجرای سوئیت + بازبینیِ adversarial. ایزولاسیون: production لمس‌نشده، sandbox پاک می‌شود. |
| **`submit_for_approval(rfc)`** (D-5) | P3 کارتِ [merge پشتِ flag]/[reject]. بدونِ channel = ابدی pending. |
| **`restart_from_known_good(leg, db)`** (D-6) | قلابِ Pacemaker از P1 (خطِ ۴۸۳): پای failed → alive. |
| **`run_cycle(beat, trace)`** | حلقهٔ کامل: mine → rfc → sandbox → submit. هر N ضربان. |

تست: `test_doctor.py` (۲۷ چک). reward-integrity تست شد (uptime → reject). **گیتِ Phase 2:** ≥۱ RFC از traceِ seed تولید، sandbox-tested، و بدونِ human-append به production نمی‌رسد.

⚑ برای معمار: اتصالِ `run_cycle` به Pacemaker (هر N ضضان) + جایگزینیِ واقعیِ `VERIFY_RULES` در `dashboard_doctor.py` با `stable_read` = فازِ بعد (مهاجرتِ جداگانه).

### ۲.۷.۱) Doctor Wiring + Inner Chamber (افزایشی)

**Wiring (بسته‌شدنِ گاف‌های تحلیل):**
- `_gather_trace` اکنون واقعی است: `organs` (از تله‌متری)، `errors` (با ساختار `{organ,msg}` از conflicts)، `sigma_effective` (از replication، dict تودرتو)، `effects_pending` (از chrono.db). mine/spectral حالا دادهٔ واقعی می‌خوانند.
- `knowledge/internal/` در `__init__` ساخته می‌شود (گاف ۳ بسته شد). RFCها روی دیسک می‌مانند.
- `db` قابل‌تزریق به Doctor (برای effects_pending).

**Inner Chamber (`_ops/doctor/chamber.py`):**
اتاقِ گفت‌وگوی درونیِ کران‌دار و تخاصمی — RFC را قوی‌تر می‌کند، نه دکتر را خودمختارتر. ۴ صدا (Proposer/Red-Critic/Skeptic/Synthesizer) + ۶ مهار: کران‌دار (≤۳ دور) · تخاصمی (Skeptic=falsifier) · propose-only · λ_persist منفی · auditable · stub ($0).
⚠ UNPROVEN: Chamber فعلاً offline/stub است. تا Doctor در runtime اجرا شود و trace واقعی بخواند، سبزیِ تست‌ها فقط نشان‌دهندهٔ مکانیزم است. الگوی امن از `_ops/debate/` (≤۳ دور، gated).

### ۲.۷.۲) Doctor Calibration + Full Wiring (افزایشی)

**Feedback loop (`calibration.py`):** verdict_history + `should_skip_bottleneck` (۳ reject → دیگر پیشنهاد نده) + `effective_mine`. ضدِ agreement-spiral.
**Attention-budget:** `attention_gate` — soft-cap=۳، hard-cap=۵. critical همیشه می‌گذرد. دکتر خودش را throttle می‌کند.
**Wiring (`wiring.py` + organism.py):** ۵ لایه پشتِ env-flags (پیش‌فرض خاموز = no regression، تست شد): `OCTOPUS_WIRE_DOCTOR`/`TELEGRAM_BOT_TOKEN`/`OCTOPUS_WIRE_UNIFIED`/`OCTOPUS_WIRE_LEAD`. `enrich_state_with_germline` همیشه روشن (read-only). `run_cycle` حالا از calibration + Chamber می‌گذرد.

### ۲.۷.۳) Box-of-Agents — B0 Numeric Core (`_ops/doctor/box/`)

میکرو‌جهانِ بستهٔ عددیِ داخلِ دکتر. $0 (صفر LLM/شبکه). spec: `DOCTOR-BOX-OF-AGENTS-SPEC.md`.

| جزء | کار |
|---|---|
| `agent_state.py` | Part 10 schema: clip z∈[0,1]، energy.tokens_spent_episode، goal_stack screened (ممنوعه: self-preservation/budget-seeking) |
| `dynamics.py` | x/z/M/G update (Part 4/5): contractive f، clip u، bounded h. g/h/f stubs |
| `warden.py` | E_box_max=0.02·E_total fail-closed، STOP supreme، ρ(J)<1، allostatic cooldown |
| `topology.py` | tree+k shortcuts (Part 11). full-mesh ممنوع. یال O(N log N) |
| `archivist.py` | multiscale coarse-grain memory (MERA-like). |M_t| sublinear، evict کم‌امتیازترین |
| `primitive.py` | recursive Proposer→Skeptic→Integrator. depth از بودجه برش |
| `sensors.py` | ρ(J) (spectral radius) + I(a;x) (mutual info). neural vs random جداکننده |
| `null_dreamer.py` | baseline random control (علمی) |
| `box.py` | Box class (glue): run_tick/run_episode |

تست: `test_box.py` (۲۹ چک). هر ۷ شرط DoD سبز. هیچ import از *_gate/chrono/money/genome.

### ۲.۷.۴) Doctor Evolution Upgrades (`_ops/doctor/evolution.py`)

۳ تکنیکِ صنعتی (DOCTOR-EVOLUTION-BENCHMARK-10systems.md §۳): هوش را برمی‌داریم، نه خودمختاری را — merge همچنان human-append.

| ماژول | تکنیکِ صنعتی | کار |
|---|---|---|
| `RFCArchive` | MAP-Elites + DGM lineage | سلول = (bottleneck_key × organ)، بهترین-در-سلول، cap+evict، sample/mutate با generation |
| `measured_lift` | AlphaEvolve/FunSearch | lift واقعی در sandbox؛ زیرِ آستانه (0.05) → drop خودکار (به انسان نمی‌رسد) |
| `tournament_rank` | Co-Scientist Elo | چند variant → مسابقهٔ pairwise/Elo؛ فقط بازمانده submit (`survivor`) |

non-destructive: mine/propose/submit فعلی دست‌نخورده. λ_persist منفی. هیچ import از *_gate/chrono/money.
تست: `test_evolution.py` (۲۰ چک).

## ۲.۸) لایهٔ Survival / 24-7 (Phase 5) — `_ops/watchdog.py` + `germline.py` + `unified_bus.py` + `checkpoint.py` + `smoke_24h.py`

زنده‌ماندنِ ۲۴/۷ + همگرایی به یک ارگانیسمِ واحد. LifeDoctrine §۴: «You fight to keep Octopus alive. Octopus never fights to stay alive» — watchdog = ابزارِ مالک، نه self-persistenceِ سیستم. additive؛ $0 آفلاین؛ stdlib-only.

| جزء | کار |
|---|---|
| **`watchdog.py`** (S-1) | `should_revive(port, stops, state)` → revive فقط اگر port مرده ∧ no STOP ∧ prior run. **yield بی‌قید به STOP** (persistence نه resistance). first-birth = owner-only (INC-1). |
| **`germline.py`** (S-2/S-5) | `compute_lag_hours` + `lag_severity` (warn>2h/ERROR>26h/CRIT>72h) + `run_with_retry` (backoff، لاگ نه بی‌صدا). germline_lag در ORGANISM-STATE. |
| **`unified_bus.py`** (S-3) | پلِ همگراییِ additive: `publish` → genome ledger (LANGAR) + chrono checkpoint. یک نویسنده، دو نما (UnifiedArchitecture L0). **non-destructive:** مسیرهای قدیمی دست‌نخورده. |
| **`checkpoint.py`** (S-4) | `checkpoint(beat,hlc,hash)` در chrono.db + `replay`/`replay_state_at` از ledger. بازسازی <۵s (DoD). |
| **`smoke_24h.py`** (S-6) | چک‌لیست: state-fresh/heartbeat/no-freeze/ledger-verify/zero-spend/epoch-log. اجرای دستی مالک. |

تست: `test_phase5.py` (۲۴ چک). kill-switch مطلق تست شد (STOP → yield). germline MAX_LAG تست شد. non-destructive تست شد (مسیر قدیمی هنوز کار می‌کند). بازسازی <۵s اثبات شد.

⚑ **برای مالک (فقط-مالک، ⚑):**
1. **Scheduled Task / autostart:** ساختِ Task Scheduler برای `organism-watchdog.ps1` (هر ۵ دقیقه) + `germline-hourly.ps1` (ساعتی). این کارِ مالک است، نه ایجنت.
2. **off-siteِ رمزنگاری‌شده:** credential کلاود در `.env` مالک — هرگز در repo. runbook جدا.
3. **اجرای ۲۴ساعته:** `python _ops/organism.py` باید via Scheduled Task/at-logon اجرا شود، نه شلِ ایجنت.

## ۲.۹) لایهٔ Blueprint (دکترِ تکاملی — خودیادگیری) — Phase 0..3

| فاز | چه ساخت | فایل‌ها |
|---|---|---|
| **P0 ایمنی** | baseline snapshot · held-out (۵ canary ثابت + verify زنجیرهٔ ژنوم + sealed) · phase_gate · review_bus | `baseline.py` · `held_out_evaluator.py` · `phase_gate.py` · `review_bus.py` |
| **P1 پنج ریشه** | RFC auto-expire (۲۴h) · تفکیک None/empty در consolidation · sweep اثرهای معلق کهنه (۷۲h) · هوکِ tick · sweep در epoch | `doctor/doctor.py` · `wiring.py` · `chrono.py` · `organism.py` · `budget/governor_epoch.py` |
| **P2 فضای latent مشترک** | R^32، cosine retrieval، mean-pool integration، persist؛ ۵ encoderِ deterministic (بدون LLM) — enrichment در `canonical_consolidation` (advisory، fail-soft) | `neural/latent_space.py` · `neural/encoders.py` |
| **P3 BCM forgetting** | قانون BCM: ‏`Δw = η·y(y−θ) − β·w`؛ آستانهٔ متحرک `θ = EMA(y²)` per-key؛ هرسِ زیرِ کف + سقفِ اشباع (`max_keys`، ‏saturation ≤ 1). **فقط ایندکسِ retrieval (latent-vectors) هرس می‌شود — consolidation.json (تاریخچهٔ append-only، I1) هرگز.** هومئوستاتیک: فعال‌سازیِ اشباع‌شدهٔ دائمی خودش سرکوب می‌شود (ضدِ memory reward-hacking). | `neural/bcm.py` (+ گزارش در `ConsolidatedInsight.bcm_*`) |
| **P4 sparse filter** | فیلترِ ورودی L1/prediction-error: پیش‌بینِ EMA per-key؛ فقط سیگنالِ novel/خطای‌بالا واردِ consolidation؛ L1 soft-shrink؛ eviction deterministic؛ `heavy_tail_share` برای متریکِ توزیع. دادهٔ خام هرگز حذف نمی‌شود — فقط ورودیِ همان cycle باریک می‌شود. | `neural/sparse_filter.py` (+ `ConsolidatedInsight.sparse_*`) |
| **P5 chamber temperature** 🔴 | `TemperatureController`: ‏T∈[t_min,t_max] deterministic از verdict-history (رکود→اکتشاف، mergeِ اخیر→پالایش)؛ `run_chamber(temperature=)` فقط max_rounds را (با سقفِ مطلقِ ۳) تنظیم می‌کند — **مهارهای ایمنی (Red-Critic، λ_persist) عمداً تابعِ دما نیستند**. + مصرفِ verdictهای RFC تلگرام در run_cycle (حلقهٔ یادگیری بسته شد). | `doctor/temperature.py` · `doctor/chamber.py` · `doctor/doctor.py` |
| **P6 Fisher metric** | گرادیانِ طبیعی advisory: ‏G تجربی از مؤلفه‌های fitness، ‏`Δw = η·(G+εI)⁻¹·∇`، ‏cond گزارش می‌شود. **فقط `state/fisher-latest.json` — وزن‌های واقعی فقط از budgets.yaml (I4/I6)، هیچ تغییرِ scoring.** هوکِ روزانه در organism پشتِ flag. | `budget/fisher.py` |

- **گیت‌ها (وضعیت 2026-07-10، همه قابل‌وتو در [[00 - Inbox/AGENT_QUESTIONS|AGENT_QUESTIONS]]):** ‏`OCTOPUS_WIRE_BCM` **داخل** PAPER_FULL_FLAGS (default-applied) · ‏`OCTOPUS_WIRE_SPARSE` و `OCTOPUS_WIRE_FISHER` خارج از profile، پیش‌فرض خاموش (پیشنهاد: بعد از یک هفته shadowِ BCM روشن شوند) · ‏`OCTOPUS_WIRE_CHAMBER_T` **RED** — فقط با verdict صریح، هرگز خودکار.
- **متریک‌های پیش‌ثبت‌شده (قبل از پیاده‌سازی):** `state/phase-metrics.jsonl` — رکوردهای blueprint-phase-3..6 + retro-registration صادقانه برای P0-P2.
- تست: `test_bcm_forgetting.py` (۱۹) · `test_sparse_filter.py` (۱۵) · `test_chamber_temperature.py` (۲۴) · `test_fisher.py` (۱۳) · `test_telegram_rfc_router.py` (۱۸). سوئیت‌های P0-P2: `test_baseline` · `test_held_out_evaluator` · `test_phase_gate` · `test_rfc_sweep` · `test_consolidation_distinguish` · `test_gate_sweep` · `test_latent_space` · `test_encoders` · `test_consolidation_latent`.
- **ثبتِ رسمی فازها:** ‏`state/reviews/` حالا PHASE_RESULT/AUDIT_REPORT/ROADMAP برای phase-1..6 دارد (retroactive برای ۱-۲؛ verdictها null = میزِ مالک — I7).
- **زنجیرهٔ ژنوم (issue #1، بسته 2026-07-10):** خط ۴۰ torn ولی hash در دُم لنگرِ `prev` رکورد ۴۱ است → `ledger.py v0.4.7` متدِ `verify_scar_aware()` / CLI ‏`verify-scars` (additive، read-only): «ok-with-scars: 1». ‏`verify()` قدیمی دست‌نخورده FAIL می‌ماند؛ ‏`held_out_evaluator` با verdictِ default-applied (قابل‌وتو) به `verify-scars` سوئیچ شد → لایهٔ ledger حالا سبز.
- **W-3 تلگرام (بسته 2026-07-10):** باگ پنهانِ `import opslib` غایب (NameError که می‌توانست run_forever را بکشد) فیکس؛ کارت‌های RFC حالا توکنِ ضدجعل + رجیستری + ضدreplay دارند و شاخهٔ `rfc:*` در dispatch (بدونِ هیچ settle/gate)؛ `pop_rfc_verdicts()` → مصرف در run_cycle → `calibration.record_verdict` (حلقهٔ یادگیریِ RFC بسته). ‏`/lead` وقتی leg موجود باشد از `LeadLeg.intake` می‌رود (fail-soft fallback). فعال‌شدنِ end-to-end فقط منتظرِ **چرخشِ توکن + restart مالک** است (لانچر از قبل `call OCTOPUS.env` دارد).



- **I1 append-only:** ‏ledger، ‏SURVIVORS-QUEUE، ‏heartbeat، لاگ‌ها — هرگز بازنویسی/حذف.
- **I2 تک-enforcer:** ‏budget_gate تنها نقطهٔ enforce؛ این لایه فقط MEASURE/propose؛ ‏organ_gate می‌پیچد، جایگزین نمی‌کند.
- **I3 fail-closed:** ناسازگاری تلمتری↔حسابداری = ‏FREEZE همهٔ grantها + ‏[CONFLICT] به صف انسان؛ واگرایی >۲۰٪ با billed = ‏STOP-METABOLIC (شرط مرگ).
- **I4 اعداد از فایل:** هر عدد تصمیم‌ساز از budgets.yaml (پیش‌فرض‌های کد فقط تا verdict‌شدنِ [[_ops/budget/budgets-proposed-diff|diff پیشنهادی]]).
- **I5 گیت دوقفلهٔ زنده:** هیچ مسیر خرج‌دار پیش از **2026-07-21** (در کدِ `opslib.live_gate_open` قفل است) و بدون پرچم `ACTIVATION-*.flag` که فقط مالک می‌سازد.
- **I6 budgets.yaml فقط‌خواندنی** (H7).
- **I7 پذیرش فقط انسانی:** ‏«پذیرفته» = ‏status='sent' در outbox (کلیک انسان) + تطبیق core.db؛ ‏«survive» معمار فقط بلیت صف است، هرگز امتیاز.
- **I8 ضدسرطان:** ‏σ_effective≤1؛ ‏MAX_CELLS=6؛ عمق spawn=۱؛ ‏SPAWN فقط PROPOSAL؛ ‏PROJECT_F هرگز وارد لوپ نمی‌شود.
- **I9 secret:** کلید فقط از env (‏DEEPSEEK_API_KEY / ‏ANTHROPIC_API_KEY)؛ هرگز در md/لاگ/exception؛ گارد host در هر دو کلاینت (client.py و llm.py ژنوم v0.4.1).
- **I10 ضدتزریق:** ‏topic = داده؛ فقط whitelist؛ پوشش ‹‹‹ ››› + GUARD_SENTENCE در system prompt هر دو ایجنت.

## ۴) نردبان فعال‌سازی (به ترتیب — همه فقط-مالک)

1. فیکس git (دستور در [[00 - Inbox/AGENT_QUESTIONS|AGENT_QUESTIONS]]) + commit ‏agent-checkpoint.
2. بک‌اپ off-box → ‏`genome_guard --init` (طبق [[04 - Architect System/GOVERNOR-MUSE-SYSTEM-INDEX|INDEX]]).
3. ‏verdict ‏V1 (عدد لوپ/CEIL_DAY_USD/قیمت‌ها) و V2 (نوع رویداد ledger) + verdict روی [[_ops/budget/budgets-proposed-diff|diff پیشنهادی]].
4. روشن‌کردن `RUN-ORGANISM.bat` — **سایه، $0**؛ smoke یک‌شبه؛ سبز = شروع جمع دیتای ۳۰روزه.
5. ‏(≥ 2026-07-21 و بعد از فاز −۱ فروش) پرچم‌ها به انتخاب مالک: ‏`ACTIVATION-DEBATE.flag` → ‏۷ روز اجرای دستی نظارت‌شده؛ بعدها ‏`ACTIVATION-GOVERNOR-LLM.flag`؛ ‏`ACTIVATION-REPLICATION.flag` فقط پس از ~۴ هفته دادهٔ EXPERIENCE.
6. اولین enforcement واقعی (خروج از سایه) = verdict جدا؛ ورودی‌اش STAGE3-REPORT.

## ۵) هوک‌های UI

**فاز ۰ پنل مالک اجرا شد (verdict آری 2026-07-06/07):** `_ops/panel/server.py` روی `http://127.0.0.1:8790` (stdlib، loopback، bind انحصاری، $0) — سه صفحه: پروفایل مالک (فرم آشنایی + ذخیره در `_ops/state/OWNER-PROFILE.json`) · `/projects` (اسکن فقط‌خواندنی PROJECT.mdها) · `/organism` (نمایش همین stateهای پایین؛ ارگانیسم خاموش = راهنمای روشن‌کردن). لانچر: `_ops/panel/RUN-PANEL.bat`.

سرور وضعیت خود ارگانیسم `http://127.0.0.1:8771` (فقط‌خواندنی، loopback، bind انحصاری):

| endpoint | محتوا |
|---|---|
| `/api/organism` | ‏`_ops/state/ORGANISM-STATE.json` — ضربان، ماه/امروز، conflicts، epoch، σ |
| `/api/telemetry` | ‏`telemetry-latest.json` — مصرف per-organ دو استک (micro-USD) |
| `/api/fitness` | ‏`fitness-latest.json` — برازندگی per-cell (تا ۲۸ روز ‏authoritative:false) |
| `/api/replication` | ‏`replication-latest.json` — ‏σ_effective، zone، پیشنهادهای SPAWN |

الگوی پنل: [[00 - Inbox/2026-07-06 PANEL-SPEC-ادمین-و-شرکا|PANEL-SPEC]] + ‏`/api/genomes` داشبورد 8770.

**فاز ۳ سطحِ human-append تلگرام (P3، additive — پنلِ محلی ۸۷۹۰ همچنان fallback):** `TelegramApprovalChannel` در `_ops/budget/approval_channel.py` — stdlib-only (`urllib`)، long-pollingِ $0-idle، owner-allowlist (`TELEGRAM_OWNER_CHAT_ID`)، quarantine (هر ورودی = DATA نه دستور). توکنِ بات فقط از env (`TELEGRAM_BOT_TOKEN`)؛ نبودِ آن = no-opِ امن (fail-closed). هفت UI:

| دستور | کار |
|---|---|
| `/status` | فقط‌خواندنی: خرج ماه/امروز، σ، تعارض‌ها، germline_lag، halted/frozen از `_ops/state/*.json` |
| `/lead name \| AUD \| cell` | mint `LEAD-YYYYMMDD-nnn` (PROPOSAL فقط) از `attribution.propose` |
| `/start_exp1..3` | تقویمِ ۱۴روزه را تولید و قفل می‌کند (exp2 با `random.seed` ثابت) |
| `/reveal exp<N>` | فقط بعد از end_date + verifyِ sha256 — prediction مهر-و-موم هرگز زودتر decode نمی‌شود |
| کارتِ تأیید | proposal + مبلغ + verdict + [تأیید✅][رد❌][بعداً⏳] — تأیید = `on_human_judgment` (human-append) → `EffectorGate.settle` (تنها مسیرِ TINV-7) |
| کارتِ RFC | `[merge پشتِ flag ✅][رد ❌]` — merge نیازِ human-append |
| `/stop` | فایلِ `_ops/STOP-ORGANISM` را می‌نویسد (authoritative؛ بات فقط trigger) |
| `/reentry` | Re-entry Packet از کارت‌های معلق + اثرهای freeze‌شده (پس از gapِ آفلاین) |

تست‌ها: `_ops/tests/test_telegram_channel.py` (۵۰+ مورد؛ $0 آفلاین با `http_get`/`http_post` فیک). رجیستری در `run_all.py`.

## ۶) اجرا (مرجع سریع)

- تست کل: `python -X utf8 "F:\backup\_ops\tests\run_all.py"`
- مناظرهٔ آفلاین: `python -X utf8 "F:\backup\_ops\debate\debate_loop.py" --topic-id seed-0`
- حلقهٔ کامل: `F:\backup\_ops\RUN-ORGANISM.bat` → ‏`http://127.0.0.1:8771`
- توقف تمیز: فایل `_ops/STOP-ORGANISM` (لایه‌ای: ‏STOP-METABOLIC / ‏STOP-DEBATE؛ کلان: ‏`04 - Architect System/STOP`)
