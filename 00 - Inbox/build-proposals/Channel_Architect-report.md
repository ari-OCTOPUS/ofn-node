---
type: report
status: inbox
tags: [octopus, build-proposal]
created: 2026-07-12
updated: 2026-07-29
---
# گزارشِ Channel_Architect — نقشهٔ کانال‌ها و سیم‌کشیِ OCTOPUS

> **نقش:** Channel_Architect | **تاریخ:** 2026-07-12 | **ریشه:** `F:/backup`  
> این گزارش سه مأموریتِ موازی را در یک سند ادغام می‌کند: **Vault Cartographer** + **Admin Environment Integrator** + **Channel Architect**.

---

## ۱. Vault Cartographer — فهرستِ فضای کاری و نقشهٔ وابستگی‌ها

### ۱-۱. فهرستِ دایرکتوری‌های اصلی (Code vs Ideas-only)

| دایرکتوری | وضعیت | حجم تقریبی | توضیح |
|---|---|---|---|
| `4d_system/` | **🟢 Real Code** | ~2.5 MB | مغزِ پژوهشی (SOG/Brain): daemon، autoloop، events، budget، frontier، self-evolution، telegram bot |
| `_ops/` | **🟢 Real Code** | ~7.5 MB | ارگانیسمِ حاکم (Governance Organism): organism.py، wiring.py، unified_bus.py، budget/، legs/، chrono.db |
| `nervous-system/` | **🟢 Real Code** | ~5 KB | سه اکسترکتور: `extract_live_data.py`، `extract_ops_data.py`، `extract_graph.py` |
| `OCTOPUS/` | **🟢 Real Code** | ~76 MB | هابِ ویژوال (۱۰ دنیا + octo-core.js + graph-data.js + live-data.js + ops-data.js) |
| `app/` | **🟢 Real Code** | ~500 KB | NBB Control Plane (demo/run.py — separate codebase) |
| `survival-gateway/` | **🟢 Real Code** | ~200 KB | Docker/LiteLLM gateway |
| `01 - Dashboard/` | **🟡 Hybrid** | ~375 KB | HTML dashboards (CONTROL-PANEL.html، SYSTEM-DASHBOARD.html) — UI rendering، نه business logic |
| `05 - Agents/` | **🔴 Ideas-only** | ~50 KB | Markdown manifests (AGENT_REGISTRY.md، RATIFIED-TASKS.md) — فایل‌های text، بدون کد اجرایی |
| `06 - Architecture Maps/` | **🔴 Ideas-only** | ~200 KB | ADRها، URCP، RISK-LADDER — فقط مستندات معماری |
| `02 - Life OS/` | **🔴 Stub** | ~5 KB | خالی/نیمه‌ساخته — صرفاً placeholder |
| `09 - People/` | **🔴 Stub** | ~1 KB | خالی/نیمه‌ساخته — صرفاً placeholder |
| `03 - Projects/` | **🟡 Hybrid** | ~170 MB | پروژه‌های کسب‌وکار (Lead-نقاشی، Mining، Ziman، Crypto، Project-F، Accounting) — عمدتاً markdown + asset |
| `07 - Knowledge/` | **🟡 Hybrid** | ~5.3 MB | genome-system/ (code: research_loop.py، run.py) + school-memory/ (code: curriculum.py) + بقیه markdown |
| `00 - Inbox/` | **🟡 Raw** | ~2.1 MB | ورودی خام + scout-digests — unstructured |
| `_memory/` | **🟡 Data** | ~50 KB | حافظهٔ ماندگار (HEARTBEAT، EXPERIENCE-LEDGER) — append-only data |
| `_code/` | **🟡 Archive** | ~3.2 MB | آینهٔ کد قدیمی — احتمالاً کهنه |
| `_launchpad/` | **🟡 Scripts** | ~200 KB | پایپ‌لاین زندهٔ ربات‌ها — partially active |
| `10 - Telegram processing/` | **🟡 SOP** | ~20 KB | routing + SOP — procedural docs |
| `_Archive/` / `_Duplicates/` | **🔴 Storage** | — | مقصد انتقال/حذف |
| `.obsidian/` | **🔴 Config** | — | تنظیمات Obsidian |
| `.git/` | **🔴 VCS** | ~229 MB | تاریخچهٔ گیت |

**خلاصه:** از ۳۶ آیتم top-level، **۵ دایرکتوری کدِ اجراییِ واقعی** دارند (`4d_system`، `_ops`، `nervous-system`، `OCTOPUS`، `app`، `survival-gateway`)، **۴ دایرکتوری hybrid** (کد + markdown) و **بقیه ideas-only / stub / data / archive** هستند.

### ۱-۲. فایل‌های کلیدی Python و هدفِ هر کدام

#### 4d_system/ (Research Brain — مغزِ پژوهشی)

| فایل | هدف | وابستگی‌ها | وضعیت |
|---|---|---|---|
| `run.py` | Entry point دوگانه: CLI self-test + Streamlit dashboard | همهٔ ماژول‌های داخلی | 🟢 Active |
| `brain/daemon.py` | حلقهٔ بی‌مراقب (headless daemon): tick هر ۳۰s، auto_propose، housekeeping | automation.py، budget.py، notify.py، self_code.py | 🟢 Active |
| `brain/autoloop.py` | موتور پژوهشِ خودمختار: تولید داده → تحلیل → insight → frontier | core.model، llm.router، memory.store | 🟢 Active |
| `brain/automation.py` | AutomationController: run_one() گامِ خودمختار | brain.graph، llm.router | 🟢 Active |
| `brain/events.py` | گذرگاهِ رویدادِ ساختاریافته → SQLite dashboard_events | memory.store | 🟢 Active |
| `brain/budget.py` | مدیریتِ بودجهٔ ابری (cap، by_provider، remaining) | config.settings | 🟢 Active |
| `brain/self_code.py` | پیشنهادِ خودکارِ بهبودِ کد + git + TCB + rollback | git CLI، config.settings | 🟢 Active |
| `brain/self_evolve.py` | خودارتقاییِ ساختاری (system evolution) | self_code.py | 🟢 Active |
| `brain/frontier.py` | مرزِ دانش (knowledge frontier): record + query | memory.store | 🟢 Active |
| `brain/hypotheses.py` | مدیریتِ فرضیه‌ها | memory.store | 🟢 Active |
| `brain/telegram_bot.py` | رابطِ تلگرام (long-polling): status، goal، pending، pause/resume | daemon.py، self_code.py، budget.py | 🟢 Active |
| `brain/graph.py` | LangGraph pipeline: run_experiment_streaming() | langgraph، core.model | 🟢 Active |
| `brain/tools.py` | ابزارهای ۵گانهٔ LLM | config.settings | 🟢 Active |
| `brain/vault_sync.py` | sync با Obsidian (create_discovery_note) | pathlib | 🟢 Active |
| `brain/notify.py` | digest queue + flush ( Telegram/stdout ) | config.settings | 🟢 Active |
| `brain/housekeeping.py` | cleanup دوره‌ای | pathlib | 🟢 Active |
| `brain/reflection.py` | خودانعکاسی (self-reflection) | memory.store | 🟢 Active |
| `brain/research_agenda.py` | اهدافِ پژوهشی (goals_now) | pathlib | 🟢 Active |
| `brain/self_growth.py` | خودنگاره (self-portrait) + learned capabilities | memory.store | 🟢 Active |
| `agents/*.py` | ۵ agent: analyst، detector، orchestrator، reporter، verifier | base.py | 🟢 Active |
| `core/model.py` | مدلِ ریاضیِ 4D (anchors، self-test) | numpy | 🟢 Active |
| `llm/langchain_models.py` | adapter LangChain | langchain_core | 🟢 Active |
| `llm/router.py` | router LLM (Fugu → GLM → Ollama) | config.settings | 🟢 Active |
| `memory/store.py` | SQLite persistence (experiments، reflections) | sqlite3 | 🟢 Active |
| `memory/vectorstore.py` | RAG index (vault chunks) | chromadb/faiss | 🟡 Optional |
| `config/settings.py` | تنظیمات مرکزی (paths، env) | pathlib | 🟢 Active |
| `ui/app.py` | Streamlit UI (dashboard) | streamlit | 🟢 Active |

#### _ops/ (Governance Organism — ارگانیسمِ حاکم)

| فایل | هدف | وابستگی‌ها | وضعیت |
|---|---|---|---|
| `organism.py` | حلقهٔ همیشه‌روشن (تیک ۵ دقیقه): telemetry → fitness → epoch → HTTP :8771 | wiring.py، telemetry.py، fitness.py، governor_epoch.py | 🟢 Active |
| `wiring.py` | اتصالِ ۵ لایه (chrono، telegram، legs، doctor، survival) — boot profile + beat dispatch | opslib.py، unified_bus.py | 🟢 Active |
| `unified_bus.py` | پلِ همگرایی: publish → genome ledger + chrono checkpoint | opslib.py، checkpoint.py | 🟢 Active |
| `telemetry.py` | snapshot + reconcile (FREEZE/CONFLICT detection) | opslib.py | 🟢 Active |
| `fitness.py` | compute fitness (authoritative sigma) | opslib.py | 🟢 Active |
| `governor_epoch.py` | epoch governor (dry-run پیش‌فرض) | opslib.py | 🟢 Active |
| `replication.py` | sigma evaluation + zone | opslib.py | 🟢 Active |
| `cardiac.py` | CARDIAC-ALLOMETRY layer (dynamic tick period) | opslib.py | 🟡 Flagged off |
| `checkpoint.py` | chrono checkpoint (beat، hlc، ledger_hash) | chrono.py | 🟢 Active |
| `chrono.py` | HLC + EffectorGate + ChronoDB | sqlite3 | 🟢 Active |
| `events.py` | unified event log (7 event types + Envelope + Incident) | opslib.py | 🟢 Active |
| `brain/cockpit.py` | Brain Cockpit v1 (Telegram HTML) | pathlib | 🟢 Active |
| `budget/opslib.py` | هستهٔ opslib (state_dir، budgets.yaml، heartbeat، alert) | pathlib، yaml | 🟢 Active |
| `budget/approval_channel.py` | TelegramApprovalChannel (gate + ledger injection) | chrono.py | 🟢 Active |
| `budget/capability_gate.py` | gate قابلیت (capability gate) | opslib.py | 🟢 Active |
| `budget/env_loader.py` | .env loader (secrets) | pathlib | 🟢 Active |
| `budget/cockpit_readmodel.py` | readmodel cockpit | pathlib | 🟢 Active |
| `legs/lead_leg.py` | LeadLeg (PAINTING organ) | leg.py، opslib.py | 🟢 Active |
| `legs/ziman_leg.py` | ZimanLeg (ZIMAN organ) | leg.py، opslib.py | 🟢 Active |
| `legs/mining_leg.py` | MiningLeg (MINING organ — default off) | leg.py، opslib.py | 🔴 Security Gate off |
| `legs/cartographer_leg.py` | CartographerLeg (read-only sentinel) | leg.py، opslib.py | 🟡 Flagged off |
| `legs/leg.py` | TaskPacket + base leg | opslib.py | 🟢 Active |
| `afferent/sensory_bus.py` | sensory bus (observations) | school_bridge.py | 🟢 Active |
| `afferent/school_bridge.py` | SchoolBridge (awareness vector) | opslib.py | 🟢 Active |
| `vault_updater*.py` | ۳ فایل: gate + apply + updater (patch propose-only) | opslib.py | 🟢 Active |
| `registry_scan.py` | URCP registry scan (۱۳ موجودیت) | pathlib | 🟢 Active |
| `watchdog.py` | watchdog (health monitoring) | opslib.py | 🟢 Active |
| `live_loop.py` | LiveLoop (spinal cord: bus + publish/subscribe) | unified_bus.py | 🟢 Active |
| `durable_journal.py` | journal ماندگار | pathlib | 🟢 Active |
| `phase_gate.py` | phase gate manager | opslib.py | 🟢 Active |
| `review_bus.py` | review bus (RFC/audit) | opslib.py | 🟢 Active |
| `idea_graph.py` | موتور ایده-گراف | opslib.py | 🟡 Flagged off |
| `epistemics/run_offloop.py` | epistemics compute_all | opslib.py | 🟡 Flagged off |
| `neural/neural_driver.py` | NeuralDriver (reflex + nociceptor) | opslib.py | 🟢 Active |
| `neural/hebbian.py` | HebbianAssociator | opslib.py | 🟢 Active |
| `neural/consolidation.py` | ConsolidationCycle | opslib.py | 🟢 Active |
| `neural/rhythm.py` | Rhythm (mode_color GREEN/AMBER/RED) | opslib.py | 🟢 Active |
| `neural/circadian.py` | CircadianMap | opslib.py | 🟢 Active |
| `neural/sprint.py` | SprintRunner | opslib.py | 🟢 Active |
| `smoke_*.py` | smoke tests (۳ فایل) | — | 🟢 Active |

#### nervous-system/ (Extractors — اکسترکتورها)

| فایل | هدف | منبع | سینک | وضعیت |
|---|---|---|---|---|
| `extract_live_data.py` | خواندنِ `4d_system/outputs` → `live-data.js` | daemon_state.json، experiments.db، frontier.json | `live-data.js` | 🟢 Active |
| `extract_ops_data.py` | خواندنِ `_ops/state` → `ops-data.js` | ORGANISM-STATE.json، fitness-latest.json، cardiac-budget.json | `ops-data.js` | 🟢 Active |
| `extract_graph.py` | افزودن freshness به `graph-data.js` | OCTOPUS/worlds/graph-data.js | graph-data.js (overwrite) | 🟢 Active |
| `refresh-live-data.bat` | زنجیرهٔ اجرای ۳ اکسترکتور + Windows Scheduled Task | — | — | 🟢 Active |

#### OCTOPUS/worlds/ (Visualization Hub — هابِ ویژوال)

| فایل | هدف | وضعیت |
|---|---|---|
| `index.html` | هاب مرکزی (۱۰ دنیا + vitals + navigation) | 🟢 Active |
| `octo-core.js` | هستهٔ مشترک (graph + live data + UI) | 🟢 Active |
| `octo-data.js` | **API واحد داده** (new — target) | 🟡 Planned |
| `octo-info.js` | overlay ریاضی | 🟢 Active |
| `graph-data.js` | دادهٔ گراف (vault nodes/edges) | 🟢 Active |
| `worlds/01-cockpit/index.html` | دنیای ۱: کاکپیت | 🟢 Active |
| `worlds/02-ontology/index.html` | دنیای ۲: هستی‌شناسی | 🟢 Active |
| `worlds/03-money/index.html` | دنیای ۳: پول | 🟢 Active |
| `worlds/04-twin/index.html` | دنیای ۴: دوقلو | 🟢 Active |
| `worlds/05-galaxy/index.html` | دنیای ۵: کهکشان | 🟢 Active |
| `worlds/06-time/index.html` | دنیای ۶: زمان | 🟢 Active |
| `worlds/07-decision/index.html` | دنیای ۷: تصمیم | 🟢 Active |
| `worlds/08-risk/index.html` | دنیای ۸: ریسک | 🟢 Active |
| `worlds/09-compass/index.html` | دنیای ۹: قطب‌نما | 🟢 Active |
| `worlds/10-habit/index.html` | دنیای ۱۰: عادت | 🟢 Active |

#### app/ (NBB Control Plane)

| فایل | هدف | وضعیت |
|---|---|---|
| `run.py` | Demo entrypoint: shadow epoch + KPI snapshot | 🟢 Active (demo) |

### ۱-۳. نقشهٔ وابستگی‌ها (Dependency Map)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              LAYER 0: SOURCES (منابع)                           │
├─────────────────────────────────────────────────────────────────────────────────┤
│  F:/backup/4d_system/outputs/          F:/backup/_ops/state/                  │
│  ├── daemon_state.json                 ├── ORGANISM-STATE.json                 │
│  ├── experiments.db (SQLite)           ├── fitness-latest.json                 │
│  ├── decision_packets.jsonl          ├── cardiac-budget.json                 │
│  ├── frontier.json                     ├── telemetry-latest.json               │
│  └── self_evolved/                     ├── replication-latest.json               │
│                                        └── chrono.db (SQLite)                  │
│  F:/backup/ (Vault MD files)                                                    │
│  └── 03 - Projects/ 07 - Knowledge/ ... → wikilinks → graph-data.js             │
├─────────────────────────────────────────────────────────────────────────────────┤
│                              LAYER 1: EXTRACTORS (اکسترکتورها)                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│  nervous-system/extract_live_data.py  ──→  nervous-system/live-data.js           │
│  nervous-system/extract_ops_data.py   ──→  nervous-system/ops-data.js            │
│  nervous-system/extract_graph.py      ──→  OCTOPUS/worlds/graph-data.js            │
│  refresh-live-data.bat (Windows Scheduled Task، هر ۳۰ دقیقه)                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│                              LAYER 2: DATA CORE (هستهٔ داده)                     │
├─────────────────────────────────────────────────────────────────────────────────┤
│  OCTOPUS/worlds/octo-data.js  ←  هدف: API واحد (LIVE_DATA + OPS_DATA + GRAPH)   │
│  OCTOPUS/worlds/octo-core.js  ←  هستهٔ مشترک فعلی (جداگانه در هر دنیا)           │
├─────────────────────────────────────────────────────────────────────────────────┤
│                              LAYER 3: VISUALIZATION (ویژوال)                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│  OCTOPUS/worlds/01-cockpit → 02-ontology → 03-money → ... → 10-habit           │
│  OCTOPUS/index.html (هاب مرکزی) + mobile/ + dream/                             │
├─────────────────────────────────────────────────────────────────────────────────┤
│                              LAYER 4: GOVERNANCE (حکمرانی)                     │
├─────────────────────────────────────────────────────────────────────────────────┤
│  _ops/organism.py (port 8771)  ←  _ops/wiring.py  ←  _ops/unified_bus.py        │
│  ├── chrono (HLC + EffectorGate)                                                 │
│  ├── budget/ (governor + gate + approval_channel)                                │
│  ├── legs/ (lead + ziman + mining + cartographer)                                │
│  ├── neural/ (driver + hebbian + consolidation + rhythm + circadian + sprint)  │
│  └── brain/cockpit.py (Telegram cockpit)                                        │
├─────────────────────────────────────────────────────────────────────────────────┤
│                              LAYER 5: RESEARCH BRAIN (مغز پژوهشی)                │
├─────────────────────────────────────────────────────────────────────────────────┤
│  4d_system/brain/daemon.py  ←  4d_system/brain/autoloop.py                      │
│  ├── automation.py (controller)                                                  │
│  ├── graph.py (LangGraph pipeline)                                               │
│  ├── self_code.py (auto-propose + git + TCB)                                     │
│  ├── self_evolve.py (system evolution)                                           │
│  ├── frontier.py (knowledge frontier)                                            │
│  ├── events.py (dashboard_events SQLite)                                         │
│  ├── budget.py (cloud budget)                                                    │
│  ├── telegram_bot.py (owner chat)                                                │
│  └── ui/app.py (Streamlit dashboard)                                             │
├─────────────────────────────────────────────────────────────────────────────────┤
│                              LAYER 6: HUMAN INTERFACE (رابط انسان)               │
├─────────────────────────────────────────────────────────────────────────────────┤
│  Telegram bot (long-poll)  ←  _ops/budget/approval_channel.py                  │
│  Streamlit dashboard (4d_system)  ←  ui/app.py                                  │
│  HTML dashboards (01 - Dashboard/)  ←  CONTROL-PANEL.html + SYSTEM-DASHBOARD.html│
│  OCTOPUS worlds (browser)  ←  ۱۰ دنیا + octo-core.js                             │
└─────────────────────────────────────────────────────────────────────────────────┘
```

**کلید وابستگی‌های حیاتی:**
1. `organism.py` → `wiring.py` → `unified_bus.py` → `chrono.db` (حلقهٔ زنده)
2. `daemon.py` → `automation.py` → `autoloop.py` → `frontier.py` → `memory.store` (پژوهش)
3. `extract_live_data.py` → `daemon_state.json` + `experiments.db` → `live-data.js` (ویژوال)
4. `extract_ops_data.py` → `ORGANISM-STATE.json` → `ops-data.js` (ویژوال)
5. `approval_channel.py` → `telegram_bot.py` + `EffectorGate` → `owner chat` (HITL)
6. `events.py` → `dashboard_events` SQLite → `extract_live_data.py` → `live-data.js` (events)
7. `self_code.py` → `git` + `TCB` + `proposals` → `telegram_bot.py` (owner approval)
8. `wiring.py` → `make_*` factories → `organism.py` tick (boot + beat)
9. `unified_bus.py` → `ledger.append` + `checkpoint` → `chrono.db` (audit trail)
10. `4d_system` ↔ `_ops` → **هنوز سیم‌کشیِ مستقیم نیست** (دو پیاده‌سازیِ هم‌دکترین)

---

## ۲. Admin Environment Integrator — بررسیِ UI موجود و نقاطِ اتصالِ کانال جدید

### ۲-۱. ۰۱ - Dashboard/ (داشبوردها)

| فایل | نوع | هدف | وضعیت | نقاطِ اتصالِ کانال |
|---|---|---|---|---|
| `CONTROL-PANEL.html` | HTML (static، embedded JSON) | کاکپیتِ واحد: Doctor console + Build Spine + 8 brain cards + fleet + metrics + roadmap + reflexion | 🟡 Stale (generated 2026-07-05) | **تلگرام:** doctor findings → owner chat؛ **Streamlit:** realtime data feed؛ **OCTOPUS:** world navigation signals |
| `SYSTEM-DASHBOARD.html` | HTML (static) | داشبورد سیستم (legacy — merged into CONTROL-PANEL) | 🔴 Retired | — |
| `BRAIN-FOCUS-BOARD.html` | HTML (static) | focus board (legacy — merged into CONTROL-PANEL) | 🔴 Retired | — |
| `Brain.md` | Markdown | وضعیت زندهٔ مغز (هر ۳ ساعت) | 🟢 Active | **Channel:** `_ops/Brain.md` → `01 - Dashboard/Brain.md` (sync) |
| `Home.md` | Markdown | خانه (entry point) | 🟢 Active | **Channel:** `HOME.md` → `OCTOPUS/worlds/01-cockpit/` (home navigation) |
| `HANDOFF.md` | Markdown | handoff بینِ sessions | 🟢 Active | **Channel:** `HANDOFF.md` → `OCTOPUS/worlds/07-decision/` (decision context) |
| `Domans Status.md` | Markdown | وضعیت ۸ دامنه | 🟡 Stale (2026-07-03) | **Channel:** `Domains Status.md` → `OCTOPUS/worlds/08-risk/` (risk map) |
| `Scout Digests.base` | Base | digestهای اسکات | 🟡 Raw | **Channel:** `00 - Inbox/` → `Scout Digests.base` → `OCTOPUS/worlds/05-galaxy/` (intelligence) |
| `Inbox.base` | Base | inbox خام | 🟡 Raw | **Channel:** `00 - Inbox/` → `Inbox.base` → `OCTOPUS/worlds/01-cockpit/` (pending tasks) |

**نکتهٔ کلیدی:** CONTROL-PANEL.html داده‌اش را از embedded JSON `<script type="application/json" id="model">` می‌خواند — **هیچ data pipeline زنده‌ای ندارد**. برای کانال‌سازی باید:
- یا یک JSON generator جدید ساخت (مثل `extract_panel_data.py`)
- یا CONTROL-PANEL را به `octo-data.js` وصل کرد
- یا یک WebSocket/Server-Sent Events layer اضافه کرد (با توجه به static HTML، گزینهٔ اول منطقی‌تر است)

### ۲-۲. ۰۵ - Agents/ (عامل‌ها)

**هیچ کدِ اجرایی‌ای ندارد.** فقط markdown فایل‌ها:
- `AGENT_REGISTRY.md` — لیست ۱۳ موجودیت URCP
- `RATIFIED-TASKS.md` — تسک‌های ratified
- `Vault Cartographer.md` — spec نقشه‌بردار
- `Research Scout Fleet.md` — spec ناوگان اسکات
- `Mycelium Scout.md` — spec مایسیلیوم
- `Vault Operator SYSTEM-PROMPT v2.md` — prompt سیستم
- `vault-cartographer.manifest.yaml` — manifest YAML
- `_Index - Agents.md` — index

**نقاطِ اتصالِ کانال برای Agent UI:**
- کانالِ `AGENT_REGISTRY.md` → `OCTOPUS/worlds/05-galaxy/` (agent swarm visualization)
- کانالِ `RATIFIED-TASKS.md` → `OCTOPUS/worlds/07-decision/` (decision queue)
- کانالِ `_ops/registry_scan.py` → `AGENT_REGISTRY.md` (auto-update registry)

### ۲-۳. langar bot (رابطِ تلگرام)

رابطِ تلگرام در دو سطح وجود دارد:

**سطح ۱: 4d_system/brain/telegram_bot.py**
- نوع: long-polling (no webhook)
- security: فقط `TELEGRAM_CHAT_ID` مالک
- قابلیت‌ها: `/status`، `/goal`، `/pending`، `/pause`، `/resume`، `/portrait`
- approve/reject: `self_code.approve(pid)` / `self_code.reject(pid)`
- داده: از `daemon.py`، `self_code.py`، `budget.py`، `frontier.py`، `research_agenda.py` می‌خواند
- سینک: پیامِ تلگرام به owner

**سطح ۲: _ops/budget/approval_channel.py + brain/cockpit.py**
- نوع: TelegramApprovalChannel (gate + ledger injection)
- قابلیت‌ها: approve queue + cockpit HTML + organism status
- داده: از `_ops/state/` می‌خواند
- سینک: پیامِ تلگرام به owner + HTML cockpit

**نقاطِ اتصالِ کانال جدید برای تلگرام:**
1. `organism.py` → `approval_channel.py` → `telegram_bot` (HITL/owner-gate) — **CHANNEL-14**
2. `cockpit.py` → `telegram_bot` (brain cockpit digest) — **CHANNEL-15**
3. `self_code.py` → `telegram_bot` (pending proposals alert) — **CHANNEL-4**
4. `events.py` → `telegram_bot` (critical event alert) — **CHANNEL-16**
5. `watchdog.py` → `telegram_bot` (health alert) — **CHANNEL-17**

### ۲-۴. ادغام‌های موجود (Existing Integrations)

| کانال | منبع | تبدیل | سینک | وضعیت |
|---|---|---|---|---|
| 4d_system outputs → live-data.js | `daemon_state.json` + `experiments.db` + `frontier.json` | `extract_live_data.py` | `nervous-system/live-data.js` | 🟢 Exists |
| _ops state → ops-data.js | `ORGANISM-STATE.json` + `fitness-latest.json` + `cardiac-budget.json` | `extract_ops_data.py` | `nervous-system/ops-data.js` | 🟢 Exists |
| Vault MD → graph-data.js | Vault markdown files + wikilinks | `extract_graph.py` (freshness only) | `OCTOPUS/worlds/graph-data.js` | 🟢 Exists (partial) |
| Telegram bot → brain_router | Owner chat messages | `telegram_bot.py` route_command / route_callback | `self_code.approve/reject` + `daemon pause/resume` | 🟢 Exists (partial) |
| 4d_system events → SQLite | `events.emit()` | `brain/events.py` | `4d_system/outputs/4d_experiments.db` | 🟢 Exists |
| _ops organism → HTTP API | `organism.py` tick | `_StatusHandler` | `127.0.0.1:8771/api/organism` | 🟢 Exists |

---

## ۳. Channel Architect — ۱۸ کانالِ显式 (Source → Transform → Sink)

### قراردادِ نام‌گذاری:
- **CH-XX**: شمارهٔ کانال
- **Source**: منبعِ حقیقت (read-only)
- **Transform**: تبدیل/پردازش
- **Sink**: سینکِ نهایی (UI یا store یا action)
- **Priority**: P0 (حیاتی) → P1 (high) → P2 (medium) → P3 (low)
- **Risk**: R1 (ایمن، read-only) → R2 (moderate، propose-only) → R3 (high، needs owner-gate) → R4 (critical، money/execution)
- **Code Target**: فایل/ماژول هدف برای پیاده‌سازی

---

### CH-01: 4d_system outputs → live-data.js hardening

| فیلد | مقدار |
|---|---|
| **Source** | `4d_system/outputs/daemon_state.json` + `4d_experiments.db` + `self_evolved/frontier.json` |
| **Transform** | `nervous-system/extract_live_data.py` (تقویت: error handling + freshness + delta detect) |
| **Sink** | `nervous-system/live-data.js` → `window.LIVE_DATA` |
| **Priority** | **P0** |
| **Risk** | **R1** (read-only، additive) |
| **Code Target** | `nervous-system/extract_live_data.py` (refactor) + `OCTOPUS/worlds/octo-data.js` (new) |
| **وضعیت فعلی** | 🟡 Exists، نیازمند hardening: delta detection، stale flag، fallback graceful |
| **توضیح** | اکسترکتور فعلی فایل‌ها را می‌خواند ولی هیچ «کهنگی» یا «delta» نمی‌سنجد. باید: (۱) `generated` timestamp را با `now()` مقایسه کند، (۲) اگر داده کهنه (>45min) → stale flag، (۳) اگر فایل غایب → graceful null، (۴) delta بینِ دو run را log کند. |

---

### CH-02: _ops state → ops-data.js hardening

| فیلد | مقدار |
|---|---|
| **Source** | `_ops/state/ORGANISM-STATE.json` + `fitness-latest.json` + `cardiac-budget.json` |
| **Transform** | `nervous-system/extract_ops_data.py` (تقویت: error handling + freshness + wiring status) |
| **Sink** | `nervous-system/ops-data.js` → `window.OPS_DATA` |
| **Priority** | **P0** |
| **Risk** | **R1** (read-only، additive) |
| **Code Target** | `nervous-system/extract_ops_data.py` (refactor) + `OCTOPUS/worlds/octo-data.js` (new) |
| **وضعیت فعلی** | 🟡 Exists، نیازمند hardening: `_ops/budget/budgets.yaml` را هم بخواند، `wiring_summary` را بگنجاند |
| **توضیح** | اکسترکتور فعلی ۳ فایل JSON می‌خواند. باید: (۱) `_ops/budget/budgets.yaml` را بخواند (cap_monthly، organs)، (۲) `wiring_summary` از `wiring.py` بگیرد، (۳) `_ops/budget/epochs/` را بخواند (trend)، (۴) `_ops/governor-alerts.md` را بخواند (active alerts). |

---

### CH-03: Vault MD → graph-data.js hardening

| فیلد | مقدار |
|---|---|
| **Source** | کلِ vault (`.md` files + wikilinks) |
| **Transform** | `nervous-system/extract_graph.py` (تقویت: full graph build، not just freshness) |
| **Sink** | `OCTOPUS/worlds/graph-data.js` → `window.OCTOPUS_GRAPH` |
| **Priority** | **P0** |
| **Risk** | **R1** (read-only) |
| **Code Target** | `nervous-system/extract_graph.py` (rewrite) + `OCTOPUS/worlds/octo-data.js` (new) |
| **وضعیت فعلی** | 🟡 Exists (partial): فقط freshness metadata اضافه می‌کند؛ graph اصلی دستی/ثابت است |
| **توضیح** | اکسترکتور فعلی فقط `generated` timestamp را به graph-data.js موجود inject می‌کند. باید: (۱) کلِ vault را scan کند (markdown + wikilinks)، (۲) nodes/edges/groups را بسازد، (۳) `Project-F` و `09 - People` را prune کند (privacy)، (۴) freshness هر node را بگنجاند. **⚠️ احتیاج به vault scanner دارد.** |

---

### CH-04: Telegram bot → langar command router → brain_router

| فیلد | مقدار |
|---|---|
| **Source** | Owner Telegram messages (`TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID`) |
| **Transform** | `4d_system/brain/telegram_bot.py` (route_command / route_callback) |
| **Sink** | `self_code.approve/reject` + `daemon pause/resume` + `_ops/budget/approval_channel.py` |
| **Priority** | **P1** |
| **Risk** | **R2** (propose-only، but affects daemon state) |
| **Code Target** | `4d_system/brain/telegram_bot.py` (refactor) + `_ops/budget/approval_channel.py` (merge) |
| **وضعیت فعلی** | 🟡 Partial: دو bot مجزا (`4d_system/brain/telegram_bot.py` و `_ops/budget/approval_channel.py`) — نیاز به unify |
| **توضیح** | دو رابطِ تلگرامِ مجزا وجود دارد: (۱) 4d_system bot (status/goal/pending/portrait) و (۲) _ops approval_channel (gate + ledger). باید یک Unified Telegram Bot ساخت که هر دو را cover کند. Channel target: `4d_system/brain/telegram_bot.py` را به `_ops/budget/approval_channel.py` وصل کند. |

---

### CH-05: 4d_system brain events → SQLite dashboard_events → live-data.js

| فیلد | مقدار |
|---|---|
| **Source** | `4d_system/brain/events.py` (emit) |
| **Transform** | `4d_system/brain/events.py` → SQLite `dashboard_events` → `extract_live_data.py` |
| **Sink** | `live-data.js` → `window.LIVE_DATA.events` |
| **Priority** | **P0** |
| **Risk** | **R1** (read-only) |
| **Code Target** | `4d_system/brain/events.py` (already exists) + `nervous-system/extract_live_data.py` (already reads) |
| **وضعیت فعلی** | 🟢 Exists: `events.py` → `4d_experiments.db` → `extract_live_data.py` → `live-data.js` |
| **توضیح** | این کانال کاملاً کار می‌کند. فقط نیاز به hardening دارد: (۱) `latest_of()` و `get_summary()` را هم expose کن، (۲) approval_state = pending/rejected/approved را به `live-data.js` بفرست. |

---

### CH-06: genome-system research_loop → genome-system/ledger → Obsidian notes

| فیلد | مقدار |
|---|---|
| **Source** | `07 - Knowledge/genome-system/research_loop.py` |
| **Transform** | `research_loop.py` → `run.py` → Obsidian vault sync |
| **Sink** | Obsidian notes (`.md` files in vault) |
| **Priority** | **P2** |
| **Risk** | **R1** (read-only، write to vault is append-only) |
| **Code Target** | `07 - Knowledge/genome-system/run.py` + `4d_system/brain/vault_sync.py` |
| **وضعیت فعلی** | 🟡 Partial: `vault_sync.py` (`create_discovery_note`) از `autoloop.py` صدا زده می‌شود؛ `research_loop.py` جداست |
| **توضیح** | `genome-system/research_loop.py` و `run.py` یک loop جداگانه دارند. باید: (۱) خروجیِ `research_loop.py` را به `vault_sync.py` وصل کند، (۲) ledger/genome را به Obsidian notes sync کند، (۳) از `unified_bus.py` برای audit trail استفاده کند. |

---

### CH-07: _ops/ORGANISM-STATE → fitness-latest → admin dashboard health scoring

| فیلد | مقدار |
|---|---|
| **Source** | `_ops/state/ORGANISM-STATE.json` + `fitness-latest.json` |
| **Transform** | `_ops/fitness.py` (compute) + `_ops/telemetry.py` (snapshot) → health score |
| **Sink** | `01 - Dashboard/CONTROL-PANEL.html` (doctor.effective_score) + `OCTOPUS/worlds/01-cockpit/` |
| **Priority** | **P1** |
| **Risk** | **R1** (read-only) |
| **Code Target** | `nervous-system/extract_health_score.py` (new) + `OCTOPUS/worlds/octo-data.js` |
| **وضعیت فعلی** | 🟡 Partial: `fitness.py` و `telemetry.py` compute می‌کنند ولی داده به dashboard نمی‌رسد (CONTROL-PANEL.json embedded و stale است) |
| **توضیح** | باید یک اکسترکتور جدید ساخت: `extract_health_score.py` که از `ORGANISM-STATE.json` + `fitness-latest.json` + `telemetry-latest.json` یک health score ترکیبی بسازد → `health-data.js` → `OCTOPUS/worlds/01-cockpit/`. |

---

### CH-08: Mining fleet telemetry → _ops/state → OCTOPUS risk world

| فیلد | مقدار |
|---|---|
| **Source** | Mining fleet (hardware sensors: temperature، hashrate، node status) — currently MISSING |
| **Transform** | `_ops/legs/mining_leg.py` (tick) → `mining_beat()` → `ORGANISM-STATE.json` |
| **Sink** | `OCTOPUS/worlds/08-risk/index.html` (risk visualization) |
| **Priority** | **P2** |
| **Risk** | **R3** (needs Security Gate: Mining default off، SSH/wallet seed rotation required) |
| **Code Target** | `_ops/legs/mining_leg.py` (extend) + `nervous-system/extract_mining_data.py` (new) + `OCTOPUS/worlds/08-risk/` |
| **وضعیت فعلی** | 🔴 Missing: `mining_leg.py` موجود است ولی default off (`OCTOPUS_WIRE_MINING=0`)؛ هیچ telemetry واقعی نمی‌خواند |
| **توضیح** | این کانال «read-only floor» دارد: mining_leg می‌تواند status را بخواند (electricity_mood، nodes_running، thermal_warn) ولی هیچ SSH/wallet/miner-control ندارد. باید: (۱) `OCTOPUS_WIRE_MINING=1` با verdict مالک، (۲) `extract_mining_data.py` بسازد، (۳) داده به `OCTOPUS/worlds/08-risk/` بفرستد. |

---

### CH-09: Wallet/transaction events → _ops/money → OCTOPUS money world

| فیلد | مقدار |
|---|---|
| **Source** | Wallet/transaction events (currently MISSING — no real wallet connected) |
| **Transform** | `_ops/budget/capability_gate.py` + `reconcile.py` → `budgets.yaml` → `ORGANISM-STATE.json` |
| **Sink** | `OCTOPUS/worlds/03-money/index.html` |
| **Priority** | **P2** |
| **Risk** | **R4** (CRITICAL: money/execution — capability gate closed until owner verdict) |
| **Code Target** | `_ops/budget/reconcile.py` (new/extend) + `nervous-system/extract_money_data.py` (new) + `OCTOPUS/worlds/03-money/` |
| **وضعیت فعلی** | 🔴 Missing: `_ops/budget/budgets.yaml` موجود ولی هیچ transaction event واقعی نمی‌آید؛ `reconcile.py` وجود دارد ولی `OCTOPUS_WIRE_RECONCILE` flagged off |
| **توضیح** | این کانال به «پول واقعی» نیاز دارد. فعلاً فقط shadow mode: `run.py` (NBB CP) demo اجرا می‌کند. باید: (۱) `OCTOPUS_WIRE_RECONCILE=1` با verdict مالک، (۲) transaction source را وصل کند (manual CSV یا API exchange)، (۳) `extract_money_data.py` بسازد. |

---

### CH-10: Code repo changes → git hooks → 4d_system self-evolution proposals

| فیلد | مقدار |
|---|---|
| **Source** | Git repository changes (`.git/hooks/post-commit` یا polling) |
| **Transform** | `git diff` + `self_code.py` (`auto_propose_once`) → `proposals` list |
| **Sink** | `4d_system/brain/self_code.py` (pending) → `telegram_bot.py` (owner approval) |
| **Priority** | **P1** |
| **Risk** | **R2** (propose-only: no auto-apply، TCB + rollback required) |
| **Code Target** | `.git/hooks/post-commit` (new) یا `4d_system/brain/git_watcher.py` (new) + `self_code.py` |
| **وضعیت فعلی** | 🟡 Partial: `daemon.py` هر N tick `auto_propose_once` می‌زند ولی **trigger آن tick-based است نه git-based**. `self_code.py` proposals را می‌سازد ولی git hook ندارد. |
| **توضیح** | باید: (۱) یا `.git/hooks/post-commit` ساخت (ولی Windows Git hook execution محدود است) یا (۲) یک `git_watcher.py` polling-based ساخت که `git diff --name-only` را چک کند → اگر تغییر → `self_code.auto_propose_once` trigger کند. |

---

### CH-11: Agent telemetry → tracer.py → event_log → audit dashboard

| فیلد | مقدار |
|---|---|
| **Source** | Agent executions (4d_system agents + _ops legs) |
| **Transform** | `tracer.py` (new) → `event_log` (structured) → `audit dashboard` |
| **Sink** | `OCTOPUS/worlds/04-twin/index.html` (twin/audit world) + `01 - Dashboard/` |
| **Priority** | **P1** |
| **Risk** | **R1** (read-only، observability) |
| **Code Target** | `_ops/observability/tracer.py` (new) + `nervous-system/extract_audit_data.py` (new) + `OCTOPUS/worlds/04-twin/` |
| **وضعیت فعلی** | 🔴 Missing: هیچ `tracer.py` موجود نیست؛ `events.py` فقط ۷ event type دارد ولی trace/span ندارد |
| **توضیح** | باید: (۱) `tracer.py` بسازد (context manager + decorator) که هر function call را trace کند (duration، args hash، result status)، (۲) به `unified_bus.publish()` بفرستد، (۳) `extract_audit_data.py` از ledger بخواند → `audit-data.js` → `OCTOPUS/worlds/04-twin/`. |

---

### CH-12: Vault note updates → indexer.py → FTS5 → semantic search API

| فیلد | مقدار |
|---|---|
| **Source** | Vault markdown notes (`.md` files) |
| **Transform** | `indexer.py` (new) → FTS5 SQLite + vector embedding → semantic search |
| **Sink** | `OCTOPUS/worlds/02-ontology/index.html` (ontology world) + `4d_system/memory/vectorstore.py` |
| **Priority** | **P2** |
| **Risk** | **R1** (read-only، index) |
| **Code Target** | `nervous-system/indexer.py` (new) + `4d_system/memory/vectorstore.py` (extend) + `OCTOPUS/worlds/02-ontology/` |
| **وضعیت فعلی** | 🟡 Partial: `4d_system/memory/vectorstore.py` (`index_vault`) موجود ولی **هیچ scheduled re-index ندارد**؛ FTS5 وجود ندارد |
| **توضیح** | باید: (۱) `indexer.py` scheduled (cron یا Windows Task) بسازد که vault را scan کند → FTS5 index + vector embedding، (۲) `OCTOPUS/worlds/02-ontology/` را به semantic search API وصل کند، (۳) `vectorstore.py` را به incremental update تبدیل کند. |

---

### CH-13: Cron jobs → ai.daily_question → research_loop → decision_packets

| فیلد | مقدار |
|---|---|
| **Source** | Cron/scheduled jobs (Windows Task Scheduler یا `_ops/chrono.py` scheduler) |
| **Transform** | `ai.daily_question` (new) → `research_loop.py` → `decision_packets.jsonl` |
| **Sink** | `4d_system/outputs/decision_packets.jsonl` + `OCTOPUS/worlds/07-decision/` |
| **Priority** | **P2** |
| **Risk** | **R2** (propose-only: daily question generates packets، no auto-execute) |
| **Code Target** | `_ops/cortex/daily_question.py` (new) + `07 - Knowledge/genome-system/research_loop.py` + `OCTOPUS/worlds/07-decision/` |
| **وضعیت فعلی** | 🔴 Missing: هیچ cron jobِ خودکارِ daily question نیست؛ `research_loop.py` جداگانه و دستی اجرا می‌شود |
| **توضیح** | باید: (۱) `daily_question.py` بسازد که هر ۲۴ ساعت یک «سؤال روزانه» از agenda بسازد، (۲) به `research_loop.py` بفرستد، (۳) نتیجه را به `decision_packets.jsonl` append کند، (۴) `OCTOPUS/worlds/07-decision/` را به packets وصل کند. |

---

### CH-14: HITL/Owner-Gate → approval queue → Telegram notification → owner verdict

| فیلد | مقدار |
|---|---|
| **Source** | Approval queue (`_ops/budget/approval_channel.py` + `4d_system/brain/self_code.py`) |
| **Transform** | `approval_queue` consolidation → `telegram_bot.py` alert + `cockpit.py` HTML |
| **Sink** | Owner Telegram chat + `CONTROL-PANEL.html` + `OCTOPUS/worlds/01-cockpit/` |
| **Priority** | **P0** |
| **Risk** | **R2** (propose-only: human-append، TINV-7) |
| **Code Target** | `_ops/budget/approval_channel.py` (extend) + `4d_system/brain/telegram_bot.py` (extend) + `nervous-system/extract_queue_data.py` (new) |
| **وضعیت فعلی** | 🟡 Partial: approval queue در `_ops` و `self_code` به‌صورت مجزا exists؛ هیچ unified queue نیست |
| **توضیح** | این **مهم‌ترین کانالِ HITL** است. باید: (۱) یک approval queue واحد بسازد (unify `_ops` + `4d_system`)، (۲) به telegram bot وصل کند (alert + inline keyboard)، (۳) به `OCTOPUS/worlds/01-cockpit/` badge بفرستد، (۴) `EffectorGate` را تزریق کند (settle فقط از gate). |

---

### CH-15: Cross-world navigation signals → nextAction() → cockpit recommendations

| فیلد | مقدار |
|---|---|
| **Source** | `OCTOPUS/worlds/octo-data.js` (`nextAction()` API) + `LIVE_DATA.packets` + `OPS_DATA.proposals` |
| **Transform** | `octo-data.js` (priority scoring: packets → action ranking) |
| **Sink** | `OCTOPUS/worlds/01-cockpit/index.html` + `OCTOPUS/worlds/*/index.html` (navigation header) |
| **Priority** | **P1** |
| **Risk** | **R1** (read-only، UI) |
| **Code Target** | `OCTOPUS/worlds/octo-data.js` (new) + `OCTOPUS/worlds/shared-ui.js` (new/extend) + هر ۱۰ دنیا (refactor) |
| **وضعیت فعلی** | 🔴 Missing: هیچ `octo-data.js` یا `nextAction()` موجود نیست؛ هر دنیا جداگانه پارس می‌کند |
| **توضیح** | این کانال هستهٔ Dataflow Wiring Prompt است. باید: (۱) `octo-data.js` بسازد (API واحد)، (۲) `nextAction()` را پیاده‌سازی کند (priority: packets > proposals > stale alerts)، (۳) هدرِ مشترک (vitals + navigation + owner-gate badge) به هر ۱۰ دنیا اضافه کند. |

---

### CH-16: Neural stack telemetry → rhythm + circadian → OCTOPUS vitals bar

| فیلد | مقدار |
|---|---|
| **Source** | `_ops/neural/rhythm.py` (mode_color) + `_ops/neural/circadian.py` (readiness) + `_ops/neural/neural_driver.py` (pain/reflex) |
| **Transform** | `wiring.py` (`rhythm_beat` + `circadian_readiness` + `neural_beat`) → `organism.py` state |
| **Sink** | `OCTOPUS/worlds/01-cockpit/index.html` (vitals bar) + `OCTOPUS/worlds/06-time/index.html` (circadian) |
| **Priority** | **P1** |
| **Risk** | **R1** (read-only، advisory) |
| **Code Target** | `nervous-system/extract_neural_data.py` (new) + `OCTOPUS/worlds/octo-data.js` + `OCTOPUS/worlds/01-cockpit/` + `OCTOPUS/worlds/06-time/` |
| **وضعیت فعلی** | 🟡 Partial: neural stack در `_ops` compute می‌کند ولی داده به OCTOPUS نمی‌رسد |
| **توضیح** | باید: (۱) `extract_neural_data.py` بسازد که از `ORGANISM-STATE.json` (که حالا rhythm/circadian دارد) بخواند، (۲) `neural-data.js` بسازد، (۳) به `OCTOPUS/worlds/01-cockpit/` (mode_color bar) و `06-time/` (circadian map) بفرستد. |

---

### CH-17: Watchdog health alerts → unified_bus → Telegram + dashboard

| فیلد | مقدار |
|---|---|
| **Source** | `_ops/watchdog.py` (health monitoring) + `_ops/governor-alerts.md` (governor alerts) |
| **Transform** | `watchdog.py` → `unified_bus.publish("WATCHDOG_ALERT", ...)` → `approval_channel.py` |
| **Sink** | Owner Telegram + `OCTOPUS/worlds/08-risk/index.html` + `01 - Dashboard/CONTROL-PANEL.html` |
| **Priority** | **P1** |
| **Risk** | **R1** (read-only، alert) |
| **Code Target** | `_ops/watchdog.py` (extend) + `nervous-system/extract_watchdog_data.py` (new) + `OCTOPUS/worlds/08-risk/` |
| **وضعیت فعلی** | 🟡 Partial: `watchdog.py` موجود ولی به unified_bus وصل نیست؛ `governor-alerts.md` static است |
| **توضیح** | باید: (۱) `watchdog.py` را به `unified_bus.publish()` وصل کند، (۲) `extract_watchdog_data.py` بسازد که از ledger بخواند، (۳) داده به `OCTOPUS/worlds/08-risk/` و `CONTROL-PANEL.html` بفرستد. |

---

### CH-18: OCTOPUS world user actions → feedback log → 4d_system learning

| فیلد | مقدار |
|---|---|
| **Source** | User clicks/interactions in OCTOPUS worlds (browser) |
| **Transform** | `localStorage` / `feedback.json` → `nervous-system/collect_feedback.py` (new) → `unified_bus.publish("USER_FEEDBACK", ...)` |
| **Sink** | `_ops/` ledger + `4d_system/brain/self_growth.py` (learned capabilities) |
| **Priority** | **P3** |
| **Risk** | **R1** (read-only feedback، no PII) |
| **Code Target** | `OCTOPUS/worlds/feedback.js` (new) + `nervous-system/collect_feedback.py` (new) + `_ops/unified_bus.py` |
| **وضعیت فعلی** | 🔴 Missing: هیچ feedback channel از OCTOPUS به _ops/4d_system نیست |
| **توضیح** | کانالِ «آموزش از بازخوردِ کاربر». باید: (۱) `feedback.js` در OCTOPUS اضافه کند ( anonymized: world_id + action_type + timestamp)، (۲) `collect_feedback.py` آن را بخواند → `unified_bus.publish()`، (۳) `self_growth.py` آن را برای learning استفاده کند. |

---

## ۴. جدولِ خلاصهٔ ۱۸ کانال

| # | نامِ کانال | Priority | Risk | وضعیت فعلی | Code Target اصلی | وابستگی‌های کلیدی |
|---|---|---|---|---|---|---|
| CH-01 | 4d_system → live-data.js | **P0** | R1 | 🟡 Exists (needs hardening) | `extract_live_data.py` (refactor) | `daemon_state.json`، `experiments.db` |
| CH-02 | _ops → ops-data.js | **P0** | R1 | 🟡 Exists (needs hardening) | `extract_ops_data.py` (refactor) | `ORGANISM-STATE.json`، `fitness-latest.json` |
| CH-03 | Vault MD → graph-data.js | **P0** | R1 | 🟡 Partial | `extract_graph.py` (rewrite) | Vault `.md` files |
| CH-04 | Telegram → brain_router | **P1** | R2 | 🟡 Partial | `telegram_bot.py` + `approval_channel.py` | `TELEGRAM_BOT_TOKEN` |
| CH-05 | 4d events → live-data.js | **P0** | R1 | 🟢 Exists | `events.py` + `extract_live_data.py` | `dashboard_events` SQLite |
| CH-06 | research_loop → Obsidian | **P2** | R1 | 🟡 Partial | `run.py` + `vault_sync.py` | `genome-system/` |
| CH-07 | ORGANISM-STATE → health score | **P1** | R1 | 🟡 Partial | `extract_health_score.py` (new) | `fitness.py`، `telemetry.py` |
| CH-08 | Mining telemetry → risk world | **P2** | R3 | 🔴 Missing | `mining_leg.py` + `extract_mining_data.py` | `OCTOPUS_WIRE_MINING` |
| CH-09 | Wallet → money world | **P2** | R4 | 🔴 Missing | `reconcile.py` + `extract_money_data.py` | Capability gate + owner verdict |
| CH-10 | Git changes → self-evolution | **P1** | R2 | 🟡 Partial | `git_watcher.py` (new) + `self_code.py` | Git hooks / polling |
| CH-11 | Agent telemetry → audit | **P1** | R1 | 🔴 Missing | `tracer.py` (new) + `extract_audit_data.py` | `unified_bus.py` |
| CH-12 | Vault → FTS5 search | **P2** | R1 | 🟡 Partial | `indexer.py` (new) + `vectorstore.py` | Vault `.md` files |
| CH-13 | Cron → daily question | **P2** | R2 | 🔴 Missing | `daily_question.py` (new) + `research_loop.py` | Windows Task Scheduler |
| CH-14 | HITL → approval queue → Telegram | **P0** | R2 | 🟡 Partial | `approval_channel.py` + `telegram_bot.py` | `EffectorGate` |
| CH-15 | Cross-world → nextAction() | **P1** | R1 | 🔴 Missing | `octo-data.js` (new) + `shared-ui.js` | همهٔ ۱۰ دنیا |
| CH-16 | Neural telemetry → vitals | **P1** | R1 | 🟡 Partial | `extract_neural_data.py` (new) | `rhythm.py`، `circadian.py` |
| CH-17 | Watchdog → Telegram + risk | **P1** | R1 | 🟡 Partial | `watchdog.py` + `extract_watchdog_data.py` | `governor-alerts.md` |
| CH-18 | User feedback → learning | **P3** | R1 | 🔴 Missing | `feedback.js` + `collect_feedback.py` | `localStorage`، `unified_bus` |

---

## ۵. اولویت‌بندیِ ساخت (Build Waves)

### Wave 1 (P0 Channels — باید فوراً ساخته شوند)
1. **CH-01**: `extract_live_data.py` hardening (delta + stale + fallback)
2. **CH-02**: `extract_ops_data.py` hardening (budgets.yaml + wiring + epochs)
3. **CH-03**: `extract_graph.py` rewrite (full vault scan + graph build + privacy prune)
4. **CH-05**: `events.py` exposure (latest + summary + approval_state)
5. **CH-14**: Unified approval queue (HITL/owner-gate — حیاتی‌ترین کانالِ human-in-the-loop)

### Wave 2 (P1 Channels — پس از Wave 1)
6. **CH-15**: `octo-data.js` + `shared-ui.js` + world refactor (data backbone)
7. **CH-04**: Telegram bot unify (merge 4d_system + _ops bots)
8. **CH-07**: Health score extractor + cockpit integration
9. **CH-10**: Git watcher + self-evolution trigger
10. **CH-11**: Agent tracer + audit dashboard
11. **CH-16**: Neural telemetry → OCTOPUS vitals
12. **CH-17**: Watchdog → unified alerts

### Wave 3 (P2 Channels — قابلیت‌های پیشرفته)
13. **CH-06**: Genome-system → Obsidian sync
14. **CH-08**: Mining telemetry (پس از Security Gate lift)
15. **CH-09**: Wallet/transaction (پس از capability gate + owner verdict)
16. **CH-12**: Vault indexer + FTS5 + semantic search
17. **CH-13**: Cron daily question → decision packets

### Wave 4 (P3 Channels — polish + learning)
18. **CH-18**: User feedback → self_growth

---

## ۶. نقاطِ حساس و خطر (Risk Register)

| # | خطر | شدت | کانال‌های مرتبط | راهِ کاهش |
|---|---|---|---|---|
| 1 | **دو رابطِ تلگرامِ مجزا** (4d_system vs _ops) — fragmented owner experience | HIGH | CH-04، CH-14 | Unified Telegram Bot: یک bot که هر دو را cover کند |
| 2 | **OCTOPUS worlds هیچ data backbone ندارند** — هر دنیا جدا پارس می‌کند | HIGH | CH-15، CH-01 تا CH-03 | `octo-data.js`: یک API واحد برای همهٔ دنیاها |
| 3 | **CONTROL-PANEL.html stale است** (generated 2026-07-05) | MEDIUM | CH-07، CH-17 | JSON generator جدید یا وصل به `octo-data.js` |
| 4 | **Mining/Wallet/Money کانال‌ها به Security Gate نیاز دارند** — default off | MEDIUM | CH-08، CH-09 | Owner verdict صریح برای lift کردن gate؛ propose-only تا آن زمان |
| 5 | **4d_system ↔ _ops هنوز سیم‌کشیِ مستقیم ندارند** — two implementations | MEDIUM | CH-05، CH-14، CH-17 | `unified_bus.py` bridge: 4d_system events را به _ops ledger بفرست |
| 6 | **Vault graph-data.js دستی/ثابت است** — not auto-generated | MEDIUM | CH-03 | `extract_graph.py` rewrite با vault scanner |
| 7 | **Feedback channel از OCTOPUS به brain missing است** — system cannot learn from user | LOW | CH-18 | `feedback.js` + `collect_feedback.py` (Wave 4) |
| 8 | **No cron/scheduled daily question** — research loop is manual | LOW | CH-13 | Windows Task Scheduler یا `chrono.py` scheduler |

---

## ۷. یک‌خطی

> **سیستم OCTOPUS دارای ۵ لایهٔ اصلی است:** Sources (4d_system + _ops + Vault) → Extractors (۳ اکسترکتور) → Data Core (octo-data.js — missing) → Visualization (۱۰ دنیا) → Governance (organism + wiring + unified_bus). ۱۸ کانالِ显式 شناسایی شد: ۵ کانال P0 (باید فوراً ساخته شوند)، ۷ کانال P1 (Wave 2)، ۵ کانال P2 (Wave 3)، و ۱ کانال P3 (Wave 4). بحرانی‌ترین گلوگاه: **عدمِ Data Backbone واحد** (هر دنیا جدا پارس می‌کند) + **دو رابطِ تلگرامِ مجزا** + **CONTROL-PANEL stale**. راه‌حل: `octo-data.js` + `shared-ui.js` + Unified Telegram Bot.

---

*گزارشِ Channel_Architect  
تهیه‌شده برای OCTOPUS Swarm — Phase 0 → Phase 1*
