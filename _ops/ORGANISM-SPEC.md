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
| `tests/` | سوئیت ایزوله (vault موقت در TEMP): ‏`python -X utf8 _ops/tests/run_all.py` — ۶ فایل، ۳۲ چک |
| `04 - Architect System/prompts/` | سه role-prompt: ‏metabolic-governor-v0.1 · debate-muse · debate-architect |

## ۳) ناوردی‌ها (نقض = شکست/توقف)

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

## ۶) اجرا (مرجع سریع)

- تست کل: `python -X utf8 "F:\backup\_ops\tests\run_all.py"`
- مناظرهٔ آفلاین: `python -X utf8 "F:\backup\_ops\debate\debate_loop.py" --topic-id seed-0`
- حلقهٔ کامل: `F:\backup\_ops\RUN-ORGANISM.bat` → ‏`http://127.0.0.1:8771`
- توقف تمیز: فایل `_ops/STOP-ORGANISM` (لایه‌ای: ‏STOP-METABOLIC / ‏STOP-DEBATE؛ کلان: ‏`04 - Architect System/STOP`)
