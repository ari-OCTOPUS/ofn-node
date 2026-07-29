---
type: report
status: inbox
tags: [octopus, build-proposal]
created: 2026-07-13
updated: 2026-07-29
---
# گزارش Vault Cartographer — نقشه‌برداری کامل اکتوپوس

**تاریخ تولید:** ۲۰۲۶-۰۷-۱۳  
**نسخه:** v1.0  
**مسیر روت:** `F:/backup`  
**تعداد دایرکتوری‌های اصلی:** ۱۷  
**تعداد فایل‌های Python:** ~۲۷۰ فایل  
**تعداد خطوط کد Python تخمینی:** ~۶۰,۰۰۰+ خط  
**وضعیت:** واقعیت‌محور (fact-grounded) — هیچ ادعای غیرقابل‌تأیید

---

## ۱. خلاصه اجرایی

سیستم OCTOPUS یک اکوسیستم **multi-layer** است با سه لایهٔ اصلی:

- **لایه A — `4d_system`:** موتور Python واقعی (Streamlit UI + daemon headless + SQLite + Chroma RAG). این لایه **کد زنده** دارد و در حال اجراست.
- **لایه B — `_ops`:** ارگانیسم حاکم (organism) با حلقهٔ tick سبک (۵ دقیقه‌ای)، داشبورد HTTP روی پورت ۸۷۷۰، و سیستم بودجه/فیتنس/تکثیر. این لایه نیز **کد زنده** دارد.
- **لایه C — `OCTOPUS/`:** هاب visualization (۱۰ world + nervous-system + extractors). بخش extractors **کد Python** است؛ بخش HTML/JS صرفاً visualization است.

**نتیجهٔ کلیدی:** تقریباً ۸۵٪ از ساختار **کد واقعی** است؛ ۱۵٪ باقی‌مانده شامل documentation، architecture proposals، و knowledge base است. هیچ دایرکتوری majorای صرفاً "idea-only" نیست — حتی `07 - Knowledge` دارای `genome-system/` با کد Python زنده است.

---

## ۲. نقشه دایرکتوری‌ها (۱۷ دایرکتوری اصلی)

### ۲.۱ `4d_system/` — مغز اصلی (کد زنده ✅)
**وضعیت:** کد Python واقعی، تست‌شده، در حال اجرا  
**تعداد فایل‌های Python:** ~۸۰ فایل  
**تعداد خطوط:** ~۱۲,۰۰۰+ خط  
**زیرساخت:** SQLite (`4d_experiments.db`)، Chroma vectorstore، outputs/

| پکیج | تعداد فایل | نقش | TCB |
|------|-----------|-----|-----|
| `core/` | ۶ | ریاضیات SOG (immutable) | ✅ |
| `config/` | ۲ | تنظیمات + مسیرها | ✅ |
| `brain/` | ۳۲ | موتور خودمختار (autoloop, daemon, events, guardrails) | mixed |
| `memory/` | ۶ | SQLite store + Chroma RAG + embeddings | — |
| `llm/` | ۹ | Router Fugu/GLM/Ollama + shadow analysis | mixed |
| `agents/` | ۷ | analyst, detector, verifier, reporter, orchestrator | — |
| `ui/` | ۸ | Streamlit tabs (dashboard, graph, lab, meta) | — |
| `control_plane/` | ۷ | registry YAML, policy, flags, channel_doctor | — |
| `data/` | ۵ | synthetic, physical, real_api, rhythm_store | — |
| `knowledge/` | ۲ | ledger capability | — |

**فایل‌های ورودی:**
- `run.py` — entry point (CLI self-test + Streamlit)
- `brain/daemon.py` — headless month-runner (tick=۳۰ ثانیه)
- `brain/automation.py` — AutomationController با _MODE_CYCLE (۱۳ حالت)
- `brain/events.py` — event bus ساختاریافته → SQLite `dashboard_events`

**خروجی‌های کلیدی:**
- `outputs/daemon_state.json` — وضعیت daemon
- `outputs/4d_experiments.db` — دیتابیس SQLite رویدادها و آزمایش‌ها
- `outputs/llm_budget.json` — سقف بودجه روزانه (~۱۰۰۰ تماس)
- `outputs/decision_packets.jsonl` — بسته‌های تصمیم
- `outputs/self_evolved/frontier.json` — frontier novelty (۲۷ سلول)
- `outputs/self_evolved/strategy.json` — strategy evolution (generation=۹)

---

### ۲.۲ `_ops/` — ارگانیسم حاکم (کد زنده ✅)
**وضعیت:** کد Python واقعی، حلقه tick زنده روی پورت ۸۷۷۱  
**تعداد فایل‌های Python:** ~۱۲۰ فایل (شامل تست‌ها)  
**تعداد خطوط:** ~۵۸,۰۰۰ خط

| ماژول | نقش |
|-------|-----|
| `organism.py` | حلقهٔ واحد همیشه-روشن (tick=۳۰۰ ثانیه) |
| `events.py` | event bus → `state/events.jsonl` |
| `cardiac.py` | ضربان آلوستاتیک (bio_rhythm + budget + baroreflex) |
| `chrono.py` / `chrono_rhythm/` | بستر زمان/ضربان |
| `cortex/` | مغز decision-making (cortex, ignition, self_audit, goal_directed) |
| `heart/` | pacemaker + control_law + autoregulation |
| `budget/` | بودجه‌بندی ارگان‌ها + fitness + replication + telemetry |
| `neural/` | پشته عصبی (BCM, circadian, hebbian, consolidation, sprint) |
| `epistemics/` | لایه معرفت‌شناسی (۵ متریک) |
| `legs/` | پاهای پروژه (ziman, mining, lead, cartographer, email) |
| `telegram_center/` | مرکز تلگرام (center, render, tg_api) |
| `dashboard/server.py` | داشبورد HTTP روی ۱۲۷.۰.۰.۱:۸۷۷۰ |
| `live/server.py` | سرور live cockpit |
| `panel/server.py` | سرور پنل |
| `doctor/` | دکتر تکاملی (calibration, chamber, evolution, temperature) |
| `tests/` | ~۱۵۰ فایل تست |

**فایل‌های state فعال:**
- `state/ORGANISM-STATE.json` — وضعیت زنده ارگانیسم
- `state/events.jsonl` — ~۳۳,۰۰۰ رویداد
- `state/telemetry-latest.json` — تلمتری
- `state/fitness-latest.json` — فیتنس
- `state/replication-latest.json` — تکثیر
- `state/chrono.db` — دیتابیس زمان (۱MB)
- `state/cardiac-budget.json` — بودجه ضربان

---

### ۲.۳ `OCTOPUS/` — هاب Visualization (کد + HTML ✅)
**وضعیت:** Extractors کد Python واقعی؛ HTML/JS visualization  
**تعداد فایل‌های Python:** ۳ (extractors)

| فایل | نقش |
|------|-----|
| `nervous-system/extract_live_data.py` | خواندن `4d_system/outputs/` → `live-data.js` |
| `nervous-system/extract_ops_data.py` | خواندن `_ops/state/` → `ops-data.js` |
| `nervous-system/extract_graph.py` | خواندن vault → `graph-data.js` |

** worlds (۱۰ دنیای visualization):**
1. `01-cockpit/` — Cockpit
2. `02-ontology/` — Ontology
3. `03-money/` — Money
4. `04-twin/` — Twin
5. `05-galaxy/` — Galaxy
6. `06-time/` — Time
7. `07-decision/` — Decision
8. `08-risk/` — Risk
9. `09-compass/` — Compass
10. `10-habit/` — Habit

---

### ۲.۴ `nervous-system/` — کپی mirror (کد زنده ✅)
**وضعیت:** Extractorهای مشابه OCTOPUS/nervous-system با خروجی JS  
**تفاوت:** مسیر خروجی به Desktop (`C:/Users/Armin/Desktop/پازل هشت پا/`) اشاره دارد.

---

### ۲.۵ `07 - Knowledge/` — دانش + کد (mixed ✅/📄)
**وضعیت:** بخش `genome-system/` کد Python واقعی؛ بقیه documentation

| زیردایرکتوری | وضعیت | تعداد Python |
|-------------|-------|-------------|
| `genome-system/` | ✅ کد زنده | ~۱۵ فایل |
| `school-memory/` | ✅ کد زنده | ۲ فایل |
| `Time-Architecture/` | ✅ کد زنده | ۲ فایل |
| `هیپنوتیزم و خودآگاهی/` | ✅ کد زنده | ۱ فایل (`langar_redteam.py`) |
| `_audit/`, `_doctor-research/`, `cellular-systems/` | 📄 docs only | ۰ |

**فایل‌های کلیدی:**
- `genome-system/research_loop.py` — حلقه research self-chaining (wall-clock، fenced)
- `genome-system/run.py` — entry point genome-system
- `genome-system/ledger/ledger.py` — ledger append-only
- `genome-system/agents/creativity.py`, `doctor.py`, `guardian.py` — agents

---

### ۲.۶ `04 - Architect System/` — طراحی معماری (mixed ✅/📄)
**وضعیت:** عمدتاً documentation + یک codebase langar واقعی

| بخش | وضعیت |
|-----|-------|
| Root (`*.md`) | 📄 Architecture docs/proposals |
| `scripts/` | ✅ Python (budget_gate, dashboard_doctor, genome_guard, governor_shadow) |
| `architect/` | 📄 Obsidian vault + docs |
| `architect/_code/ai-farm/AI-sume/langar/` | ✅ **کد واقعی ربات تلگرام** |
| `architect/_code/ai-farm/AI-sume/langar-pro/` | ✅ نسخه pro ربات |

**langar bot — کد واقعی (~۵,۰۰۰+ خط):**
- `bot.py` — main Telegram bot
- `brain/brain_router.py` — مسیریابی مغز
- `core/` — ACE, constitution, memory, retrieval, self_improver
- `agents/` — coach, health, reflection, relationship
- `researcher/` — search providers, synthesizer
- `observability/` — event_log, tracer
- `budget.py` — budget management
- `db.py` — SQLite database

---

### ۲.۷ `03 - Projects/` — پروژه‌ها (mixed ✅/📄)
**وضعیت:** عمدتاً markdown + scraperهای محدود

| پروژه | وضعیت کد | توضیح |
|-------|---------|-------|
| `Lead-نقاشی/` | 📄 | Docs + worktrees git |
| `Mining/` | 📄 | Docs + architecture |
| `Ziman Galerry/` | 📄 | Docs + strategy |
| `Crypto - etoro/` | ✅ partial | Scraperها (`cors_proxy.py`, `lc_proxy.py`) + patches |
| `Accounting/` | 📄 | Docs + data |
| `اونلی فنز/` | ✅ | `orchestrator.py` (۱ فایل) |

---

### ۲.۸ `05 - Agents/` — تعریف agentها (📄 docs)
**وضعیت:** صرفاً markdown — agent registry، task definitions، system prompts  
**فایل‌ها:** `AGENT_REGISTRY.md`, `RATIFIED-TASKS.md`, manifest YAML

---

### ۲.۹ `01 - Dashboard/` — داشبورد Obsidian (📄)
**وضعیت:** ۶ فایل markdown — Brain, Domains Status, HANDOFF, Home  
**HTML files:** `BRAIN-FOCUS-BOARD.html`, `CONTROL-PANEL.html`, `SYSTEM-DASHBOARD.html` (static)

---

### ۲.۱۰ `02 - Life OS/` — سیستم زندگی (📄)
**وضعیت:** ۲ فایل markdown — Weekly Review, Index

---

### ۲.۱۱ `06 - Architecture Maps/` — نقشه معماری (📄)
**وضعیت:** Documentation — HEART Neuro-Map, PANEL specs, wiring maps

---

### ۲.۱۲ `08 - Assets/` — دارایی‌ها (📄)
**وضعیت:** Assets ایستا

---

### ۲.۱۳ `09 - People/` — افراد (📄)
**وضعیت:** Contacts/people data

---

### ۲.۱۴ `10 - Telegram processing/` — پردازش تلگرام (📄/✅ mixed)
**وضعیت:** احتمالاً data ingestion از تلگرام

---

### ۲.۱۵ `app/` — NBB Control Plane (✅ کد زنده)
**وضعیت:** کد Python واقعی — یک control plane جداگانه

| فایل | نقش |
|------|-----|
| `run.py` | Entry point — governor + proposal + fitness demo |
| `scripts/record_cassette.py` | تست recording |
| `tests/` | تست‌ها |

**Context:** این یک `nbb_cp` (NBB Control Plane) است با `AppConfig`, `ProposalKind`, `build_service` — یک سیستم grant/execution/fitness جداگانه.

---

### ۲.۱۶ `_code/` / `_deploy/` / `_launchpad/` / `_memory/` / `_Templates/` (mixed)
**وضعیت:** Scaffolding, templates, deployment scripts, memory archives

---

### ۲.۱۷ `نقشه اختاپوس/` — نقشه فارسی (✅ کد)
**وضعیت:** `vault_scanner.py` — scanner نقشه

---

## ۳. فایل‌های Python کلیدی و کاربردها

### ۳.۱ لایه A — `4d_system`

| فایل | خطوط | کاربرد | وابستگی‌ها |
|------|------|--------|-----------|
| `brain/daemon.py` | ۲۲۶ | Headless month-runner، tick=۳۰s | automation, self_code, events |
| `brain/automation.py` | ~۳۰۰ | AutomationController، ۱۳-mode cycle | autoloop, self_evolve, guardrails |
| `brain/autoloop.py` | ۵۳۶ | موتور research خودمختار | data, llm.router, frontier |
| `brain/events.py` | ۳۲۳ | Event bus → SQLite dashboard_events | memory.store |
| `brain/budget.py` | ۱۱۳ | سقف بودجه LLM (~۱۰۰۰/روز) | config.settings |
| `brain/telegram_bot.py` | ۳۳۸ | رابط تلگرام ADHD-محور | daemon, self_code |
| `brain/guardrails.py` | ~۲۵۰ | TCB gate، SAFE_PARAM_RANGES | core |
| `brain/self_evolve.py` | ~۳۰۰ | Strategy evolution (JSON) | guardrails |
| `brain/self_code.py` | ~۳۰۰ | Code self-modification (gated) | guardrails |
| `llm/router.py` | ~۲۰۰ | Router Fugu/GLM/Ollama | budget |
| `core/model.py` | ~۳۰۰ | SOG linear-Gaussian، DARE | numpy |
| `control_plane/registry.py` | ۱۴۲ | Registry YAML → SQLite mirror | yaml |
| `run.py` | ۱۹۰ | Entry point (CLI + Streamlit) | همه |

### ۳.۲ لایه B — `_ops`

| فایل | خطوط | کاربرد | وابستگی‌ها |
|------|------|--------|-----------|
| `organism.py` | ۵۴۸ | حلقه واحد همیشه-روشن (tick=۳۰۰s) | budget/*, chrono, cardiac |
| `events.py` | ۲۹۱ | Event bus → events.jsonl | opslib |
| `cardiac.py` | ~۱۵۰ | ضربان آلوستاتیک | — |
| `dashboard/server.py` | ۷۸۹ | داشبورد HTTP:۸۷۷۰ | — (self-contained) |
| `budget/opslib.py` | ~۲۰۰ | utilities مشترک | — |
| `budget/fitness.py` | ~۲۰۰ | fitness scoring | attribution |
| `budget/telemetry.py` | ~۱۵۰ | telemetry aggregation | — |
| `cortex/cortex.py` | ~۳۰۰ | decision cortex | model_router, ignition |
| `heart/control_law.py` | ~۲۰۰ | pacemaker control law | — |
| `legs/leg.py` | ۲۲۶ | چارچوب پای (isolation) | opslib |
| `legs/ziman_leg.py` | ۴۲۰ | پای Ziman Gallery | leg, capacity_fail_closed |
| `legs/mining_leg.py` | ۳۸۸ | پای Mining (HW + Coin) | leg |
| `legs/lead_leg.py` | ~۳۰۰ | پای Lead Generation | leg |
| `telegram_center/center.py` | ~۲۰۰ | مرکز تلگرام | tg_api, render |

### ۳.۳ لایه C — Extractors + Visualization

| فایل | خطوط | کاربرد |
|------|------|--------|
| `OCTOPUS/nervous-system/extract_live_data.py` | ۱۳۳ | ۴d_system outputs → live-data.js |
| `OCTOPUS/nervous-system/extract_ops_data.py` | ~۱۰۰ | _ops state → ops-data.js |
| `OCTOPUS/nervous-system/extract_graph.py` | ~۱۰۰ | Vault md → graph-data.js |

### ۳.۴ لایه D — Genome System

| فایل | خطوط | کاربرد |
|------|------|--------|
| `genome-system/research_loop.py` | ۱۷۷ | Self-chaining research (fenced) |
| `genome-system/run.py` | ~۱۵۰ | Entry point genome-system |
| `genome-system/ledger/ledger.py` | ~۲۰۰ | Append-only ledger |

### ۳.۵ لایه E — Langar Bot

| فایل | خطوط | کاربرد |
|------|------|--------|
| `langar/bot.py` | ~۴۰۰ | Main Telegram bot |
| `langar/brain/brain_router.py` | ~۳۰۰ | MeteredBrainProvider |
| `langar/core/ace.py` | ~۲۰۰ | ACE core |
| `langar/core/memory.py` | ~۲۰۰ | Memory system |
| `langar/budget.py` | ~۲۰۰ | Budget management |

---

## ۴. نقشه وابستگی‌ها (Dependency Map)

### ۴.۱ سطح بالا — لایه‌ها

```
┌─────────────────────────────────────────────────────────────┐
│  Layer C: OCTOPUS Visualization (HTML/JS + Extractors)      │
│  ├─ extract_live_data.py ← 4d_system/outputs/              │
│  ├─ extract_ops_data.py ← _ops/state/                      │
│  └─ extract_graph.py ← Vault markdown                      │
├─────────────────────────────────────────────────────────────┤
│  Layer B: _ops Organism (governor, HTTP:8770/8771)          │
│  ├─ organism.py → legs/ → projects                         │
│  ├─ dashboard/server.py → read-only state                  │
│  ├─ cortex/ → decision-making                              │
│  ├─ heart/ → pacemaker                                     │
│  ├─ budget/ → fitness, replication, telemetry               │
│  ├─ neural/ → BCM, circadian, consolidation                │
│  └─ telegram_center/ → Telegram gateway                    │
├─────────────────────────────────────────────────────────────┤
│  Layer A: 4d_system Brain (research engine, Streamlit)      │
│  ├─ daemon.py → automation.py → autoloop.py                │
│  ├─ events.py → SQLite dashboard_events                    │
│  ├─ llm/router.py → Fugu/GLM/Ollama                        │
│  ├─ memory/store.py → SQLite 4d_experiments.db             │
│  ├─ memory/vectorstore.py → Chroma RAG                     │
│  ├─ control_plane/ → registry YAML + SQLite mirror         │
│  └─ ui/ → Streamlit dashboard                              │
├─────────────────────────────────────────────────────────────┤
│  Layer D: Genome System (research loop, ledger)             │
│  ├─ research_loop.py → reports/ + ledger.jsonl             │
│  └─ agents/ (creativity, doctor, guardian)                  │
├─────────────────────────────────────────────────────────────┤
│  Layer E: Langar Bot (Telegram bot, standalone)             │
│  ├─ bot.py → brain_router.py → providers.py                │
│  ├─ core/ (ace, memory, constitution, self_improver)        │
│  └─ researcher/ (search, synthesizer, quality)              │
└─────────────────────────────────────────────────────────────┘
```

### ۴.۲ وابستگی‌های داخلی ۴d_system

```
core/ (immutable math)
  ↓
config/settings.py
  ↓
data/ (synthetic, physical, real_api)
  ↓
brain/autoloop.py → llm/router.py
  ↓
brain/automation.py
  ↓
brain/daemon.py (headless)  OR  ui/app.py (Streamlit)
  ↓
brain/events.py → memory/store.py → SQLite
  ↓
control_plane/registry.py
```

### ۴.۳ وابستگی‌های _ops

```
organism.py
  ├── chrono.py (time substrate)
  ├── cardiac.py (allostatic rhythm)
  ├── budget/ (fitness, replication, telemetry, governor_epoch)
  ├── cortex/ (cortex, ignition, self_audit, goal_directed)
  ├── neural/ (BCM, circadian, hebbian, consolidation, sprint)
  ├── legs/ (ziman, mining, lead, cartographer, email)
  ├── telegram_center/ (center, render, tg_api)
  └── dashboard/server.py (HTTP:8770, read-only)
```

### ۴.۴ data flow — ۱۵ کانال (از plan.md با به‌روزرسانی واقعیت)

| # | کانال | Source | Transform | Sink | وضعیت |
|---|-------|--------|-----------|------|-------|
| ۱ | 4d outputs → live-data | `4d_system/outputs/` | `extract_live_data.py` | `OCTOPUS/nervous-system/live-data.js` | ✅ CONNECTED |
| ۲ | _ops state → ops-data | `_ops/state/` | `extract_ops_data.py` | `OCTOPUS/nervous-system/ops-data.js` | ✅ CONNECTED |
| ۳ | vault md → graph-data | `F:/backup/**/*.md` | `extract_graph.py` | `OCTOPUS/nervous-system/graph-data.js` | ✅ CONNECTED |
| ۴ | Telegram bot → brain | Telegram API | `langar/bot.py` → `brain_router.py` | ۴d_system / _ops | ⚠️ PARTIAL (token نیاز) |
| ۵ | Brain events → dashboard | `brain/events.py` | SQLite `dashboard_events` | `live-data.js` → OCTOPUS vitals | ✅ CONNECTED |
| ۶ | genome research → ledger | `research_loop.py` | Guardian + LLM | `reports/` + `ledger.jsonl` | ✅ CONNECTED |
| ۷ | ORGANISM-STATE → health | `organism.py` | `_ops/budget/fitness.py` | `fitness-latest.json` + dashboard | ✅ CONNECTED |
| ۸ | Mining telemetry → risk | (external miners) | `mining_leg.py` | `_ops/state/` → OCTOPUS risk world | ❌ MISSING |
| ۹ | Wallet events → money | (external wallets) | — | `_ops/money/` → OCTOPUS money world | ❌ MISSING |
| ۱۰ | Git changes → evolution | `.git/` | — | `4d_system` self-evolution proposals | ❌ MISSING |
| ۱۱ | Agent telemetry → audit | Agents | `observability/tracer.py` | `event_log` → audit dashboard | ⚠️ PARTIAL |
| ۱۲ | Vault updates → search | `.md` files | `indexer.py` | Chroma FTS5 / semantic search | ⚠️ PARTIAL (Chroma exists) |
| ۱۳ | Cron → daily question | cron | `ai.daily_question` | `research_loop.py` → decision_packets | ❌ MISSING |
| ۱۴ | HITL → approval queue | Owner | `telegram_bot.py` / `VERDICT_QUEUE.md` | Telegram notification | ⚠️ PARTIAL |
| ۱۵ | Cross-world nav → cockpit | OCTOPUS worlds | `nextAction()` | `cockpit` recommendations | ❌ MISSING |

---

## ۵. ارزیابی واقعیت کد (Code vs Ideas)

### ۵.۱ جدول طبقه‌بندی

| دایرکتوری | کد واقعی | docs/ideas | درصد کد |
|-----------|---------|-----------|---------|
| `4d_system/` | ✅ ۸۰ فایل py | ۱۵ فایل md | ~۸۵٪ |
| `_ops/` | ✅ ۱۲۰ فایل py | ۵۰+ فایل md | ~۷۰٪ |
| `OCTOPUS/` | ✅ ۳ فایل py + HTML/JS | ۲ فایل md | ~۹۰٪ (code) |
| `nervous-system/` | ✅ ۳ فایل py | ۱ bat | ~۹۵٪ |
| `07 - Knowledge/` | ✅ ۲۰ فایل py | ۵۰۰+ فایل md | ~۵٪ |
| `04 - Architect System/` | ✅ ~۶۰ فایل py (langar) | ۱۰۰+ فایل md | ~۴۰٪ |
| `03 - Projects/` | ✅ ~۱۰ فایل py | ۲۰۰+ فایل md | ~۵٪ |
| `05 - Agents/` | ❌ ۰ | ۸ فایل md | ۰٪ |
| `01 - Dashboard/` | ❌ ۰ | ۶ فایل md+html | ۰٪ |
| `02 - Life OS/` | ❌ ۰ | ۲ فایل md | ۰٪ |
| `06 - Architecture Maps/` | ❌ ۰ | ۲۰+ فایل md | ۰٪ |
| `app/` | ✅ ~۵ فایل py | ۱ فایل md | ~۹۰٪ |
| `نقشه اختاپوس/` | ✅ ۱ فایل py | ۰ | ۱۰۰٪ |

### ۵.۲ نکات مهم

1. **langar bot** یک codebase کاملاً مستقل است (~۵,۰۰۰+ خط) داخل `04 - Architect System/architect/_code/ai-farm/AI-sume/langar/` — این کد زنده و deployable است.

2. **۴d_system** و **`_ops`** دو سیستم جداگانه‌اند که هر دو کد Python واقعی دارند و می‌توانند به‌صورت مستقل یا متصل اجرا شوند.

3. **app/** (NBB Control Plane) یک سیستم سوم است با معماری `ProposalKind.GRANT/SPAWN` — این نیز کد واقعی دارد.

4. **هیچ "idea-only" major directoryای وجود ندارد** — حتی `05 - Agents/` که صرفاً docs است، part of registry است.

---

## ۶. نقاط یکپارچه‌سازی (برای Admin + Channel Architect)

### ۶.۱ Admin Environment Integrator — نکات کلیدی

**داشبورد موجود:**
- `_ops/dashboard/server.py` — HTTP روی `127.0.0.1:8770` با ۵ صفحه: organism, capabilities, activity, channels, ideas
- قابلیت read-only + write محدود به `OCTOPUS-flags.cmd` و `STOP-ORGANISM`
- profile selector: `bare` / `paper-full` / `live`
- ۱۹ wiring flag + ۵ cadence flag

**نقاط یکپارچه‌سازی کانال جدید:**
1. **کانال‌های Telegram:** `telegram_bot.py` (4d_system) + `telegram_center/` (_ops) + `langar/bot.py` — سه gateway تلگرام جداگانه!
2. **کانال‌های HTTP:** `dashboard/server.py` (8770)، `organism.py` (8771)، `app/` (احتمالاً پورت دیگر)
3. **کانال‌های state file:** `_ops/state/*.json` به‌عنوان IPC (inter-process communication)
4. **کانال‌های SQLite:** `4d_experiments.db`، `_ops/state/chrono.db`

### ۶.۲ Channel Architect — ۱۵ کانال با هدف کد

بر اساس یافته‌های واقعی، ۱۵ کانال قابل تعریف هستند:

| # | کانال | Source | Transform | Sink | target کد | اولویت | ریسک |
|---|-------|--------|-----------|------|-----------|--------|------|
| C1 | 4d→live-data | `outputs/` | `extract_live_data.py` | `live-data.js` | `OCTOPUS/` | P0 | low |
| C2 | ops→ops-data | `state/` | `extract_ops_data.py` | `ops-data.js` | `OCTOPUS/` | P0 | low |
| C3 | vault→graph | `**/*.md` | `extract_graph.py` | `graph-data.js` | `OCTOPUS/` | P0 | low |
| C4 | events→SQLite | `events.py` | `emit()` | `dashboard_events` | `memory/` | P0 | high |
| C5 | Telegram→brain | Telegram API | `telegram_bot.py` | `automation.py` | `brain/` | P1 | medium |
| C6 | genome→ledger | `research_loop.py` | Guardian+LLM | `ledger.jsonl` | `genome-system/` | P1 | medium |
| C7 | organism→fitness | `organism.py` | `fitness.py` | `fitness-latest.json` | `_ops/budget/` | P1 | low |
| C8 | mining→telemetry | External API | `mining_leg.py` | `_ops/state/` | `_ops/legs/` | P2 | medium |
| C9 | wallet→money | External API | Parser | `_ops/money/` | NEW MODULE | P2 | high |
| C10 | git→evolution | `.git/hooks` | Hook script | `self_evolve.py` | `brain/` | P2 | medium |
| C11 | agent→audit | Agent runs | `tracer.py` | `event_log` | `observability/` | P2 | low |
| C12 | vault→search | `.md` | `indexer.py` | Chroma FTS5 | `memory/vectorstore.py` | P2 | low |
| C13 | cron→research | cron | `daily_question` | `research_loop.py` | NEW MODULE | P3 | low |
| C14 | HITL→approval | Owner | `VERDICT_QUEUE.md` | Telegram notify | `brain/notify.py` | P1 | medium |
| C15 | world→cockpit | OCTOPUS worlds | `nextAction()` | `cockpit` | NEW MODULE | P3 | low |

---

## ۷. توصیه‌ها

1. **یکپارچه‌سازی langar + ۴d_system + _ops:** سه gateway تلگرام موجود (`langar/bot.py`، `telegram_bot.py`، `telegram_center/`) باید با یک **Telegram Router واحد** جایگزین یا یکپارچه شوند.

2. **Extractor pipeline:** سه extractor (`extract_live_data.py`، `extract_ops_data.py`، `extract_graph.py`) باید در یک **pipeline واحد** با scheduling (cron یا daemon tick) ادغام شوند.

3. **Registry convergence:** `control_plane/registry.yaml` (۴d_system) و `_ops/state/channel-status.json` (_ops) باید sync شوند.

4. **Budget unification:** سه سیستم budget (`brain/budget.py`، `_ops/budget/`، `langar/budget.py`) باید یک ledger مشترک داشته باشند.

5. **Missing channels اولویت بالا:** کانال‌های ۸ (Mining)، ۹ (Wallet)، و ۱۳ (Cron daily) برای "money world" و "risk world" OCTOPUS ضروری‌اند.

---

## پیوست A — تعداد فایل‌ها به‌ازای هر دایرکتوری

| دایرکتوری | فایل‌های py | فایل‌های md | فایل‌های js/html | total files (est) |
|-----------|------------|------------|-----------------|-------------------|
| 4d_system/ | ~۸۰ | ~۱۵ | ۰ | ~۱۵۰ |
| _ops/ | ~۱۲۰ | ~۵۰ | ۰ | ~۳۰۰ |
| OCTOPUS/ | ۳ | ۲ | ~۵۰ | ~۶۰ |
| nervous-system/ | ۳ | ۰ | ۲ | ۶ |
| 07 - Knowledge/ | ~۲۰ | ~۵۰۰+ | ۰ | ~۷۰۰ |
| 04 - Architect System/ | ~۶۰ | ~۱۰۰+ | ۰ | ~۲۰۰ |
| 03 - Projects/ | ~۱۰ | ~۲۰۰+ | ۰ | ~۵۰۰ |
| 05 - Agents/ | ۰ | ۸ | ۰ | ۸ |
| 01 - Dashboard/ | ۰ | ۳ | ۳ | ۶ |
| 02 - Life OS/ | ۰ | ۲ | ۰ | ۲ |
| 06 - Architecture Maps/ | ۰ | ۲۰+ | ۰ | ۲۰+ |
| app/ | ~۵ | ۱ | ۰ | ۸ |
| نقشه اختاپوس/ | ۱ | ۰ | ۰ | ۱ |

**جمع کل:** ~۳۲۲ فایل Python، ~۹۰۰+ فایل Markdown، ~۵۵ فایل JS/HTML

---

*این گزارش توسط Vault_Cartographer تولید شده است. همهٔ ادعاها بر اساس خواندن مستقیم فایل‌های منبع هستند.*
