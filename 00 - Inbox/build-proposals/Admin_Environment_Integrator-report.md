# گزارش Admin_Environment_Integrator — OCTOPUS Project

> **تاریخ بازرسی:** ۲۰۲۶-۰۷-۱۲  
> **مسئول:** Admin_Environment_Integrator  
> **ریشه پروژه:** `F:/backup`  
> **وضعیت:** Inspection Complete — No Code Written  

---

## ۱. چکیده اجرایی (Executive Summary)

سیستم OCTOPUS یک **معماری هیبریدی دوگانه** است:
- **لایهٔ بالا (OCTOPUS Organism):** اکوسیستم زندهٔ Python در `_ops/` با چرخهٔ ضربان (cardiac-budget)، سیم‌کشی پویا (wiring)، و ناوگان ایجنت‌ها — اینجا **کد واقعی** اجرا می‌شود.
- **لایهٔ میانی (4D System):** موتور پژوهش خودمختار با daemon، autoloop، telegram bot، و event bus — **کد واقعی** با SQLite ledger.
- **لایهٔ پایین (NBB Control Plane):** کنترل‌پلن قراردادی در `app/` با FastAPI، gates مالی، و audit — **کد واقعی و تست‌شده**.
- **لایهٔ نمایش (Dashboard):** فایل‌های HTML ایستا با JSON embedشده که توسط تسک‌های زمان‌بندی Cowork بازتولید می‌شوند — **کد ندارند، مشتق هستند**.

**یافتهٔ کلیدی:** کانال‌های یکپارچه‌سازیِ جدید باید در مرز بین **لایهٔ زندهٔ OCTOPUS** و **لایهٔ مشتقٔ Dashboard** تعریف شوند. اکثر channelهای plan.md قبلاً وجود دارند (PARTIAL/CONNECTED) اما `hardening` نیاز دارند.

---

## ۲. بازرسی ۰۱ - Dashboard/ (پنل‌های مدیریتی)

### ۲.۱ SYSTEM-DASHBOARD.html
- **وضعیت:** ⛔ بازنشسته (retired ۲۰۲۶-۰۷-۰۵)
- **نوع:** HTML تک‌فایل، بدون CDN، آفلاین، RTL
- **مدل داده:** JSON embedشده در `<script id="model">` — idempotent، hash_sha256
- **قابلیت‌ها:** فیلتر risk/status، نمایش ۸ مغز پروژه، متریک‌ها (notes/broken_links/frontmatter_errors)، Doctor (raw/effective score)، ناوگان، نقشهٔ راه
- **گیت‌ها:** rotation_critical_open=4، gitleaks=false، git_init=false
- **نکته:** در CONTROL-PANEL ادغام شده؛ تسک زمان‌بندی‌اش disabled است

### ۲.۲ CONTROL-PANEL.html (فعال)
- **وضعیت:** 🟢 کاکپیت یکپارچهٔ فعال
- **نوع:** HTML تک‌فایل، light-mode، تعاملی (askClaude/sendPrompt)
- **بخش‌ها:**
  - 🩺 کنسول Doctor — پرسش زنده با Haiku
  - 🏗️ Build Spine — اندام‌های افقی (EffectorGate, Anchor Ledger, Budget guard, Kill-switch, Scout Fleet, Doctor)
  - milestoneهای ساخت M0–M8 با target file
  - verdictهای فقط-انسان (git init, lift Security Gate, DNA/PII cold-storage)
  - ۸ کارت مغز با risk sorting
  - ناوگان + Scout Intelligence
  - متریک‌های زندهٔ validator
  - چرخهٔ خودبهبودی (Reflexion)
- **محدودیت:** دکمه‌های «ساخت/تحویل» فقط `sendPrompt()` به چت می‌فرستند — هیچ اقدام مخرب/مالی مستقیم

### ۲.۳ BRAIN-FOCUS-BOARD.html
- **وضعیت:** 🟡 نسخهٔ قدیمی‌تر (v18)، هنوز کار می‌کند اما superseded
- **قابلیت‌های اضافی نسبت به CONTROL-PANEL:** raw directory table، self-improve panel با health trend SVG، delta کپی‌پذیر
- **model_hash:** `ddeacc51…` — idempotent

### ۲.۴ نتیجهٔ Dashboard
| معیار | وضعیت |
|---|---|
| سرور/live backend | ❌ ندارد — همگی static HTML |
| auto-refresh | ❌ ندارد — تسک زمان‌بندی Cowork بازتولید می‌کند |
| RTL Persian | ✅ کامل |
| offline | ✅ بله |
| interactive actions | ⚠️ propose-only (sendPrompt) |
| mobile responsive | ✅ نسبی (max-width + grid) |

**نیازمندی یکپارچه‌سازی:** یک **live-data injector** (WebSocket یا SSE یا polling ساده) برای تغذیهٔ real-time از `nervous-system/*.js` به داشبورد.

---

## ۳. بازرسی ۰۵ - Agents/ (رجیستری ایجنت‌ها)

### ۳.۱ محتوا
- `AGENT_REGISTRY.md` — رجیستری اعلانی (declarative) ایجنت‌های برنامه‌ریزی‌شده
- `RATIFIED-TASKS.md` — ۶ تسک هستهٔ ratified برای خودترمیمی
- `Research Scout Fleet.md` / `Mycelium Scout.md` — طراحی ناوگان اسکات
- `Vault Cartographer.md` / `Vault-Cartographer-LIMB.md` — تعریف Vault Cartographer
- `vault-cartographer.manifest.yaml` — مانیفست نمونه

### ۳.۲ نتیجهٔ کلیدی
- **هیچ کد Python در این دایرکتوری نیست** — همه مشخصات markdown هستند.
- ایجنت‌ها در فاز ۴ (post-rotation) deploy می‌شوند.
- اکنون execution از طریق **Cowork scheduled tasks** انجام می‌شود (prompt-based، نه daemon-based).
- `vault-cartographer` به‌عنوان **limb/OLP-1** با parent=Architect تعریف شده و boot-coupled است.

---

## ۴. بازرسی app/ (NBB Control Plane — کد واقعی)

### ۴.۱ معماری لایه‌ای
```
src/nbb_cp/
├── kernel/          # L0 — مدل‌های دامنه، gates، invariants، fitness، budget math
├── adapters/        # L1 — SQLite store، LLM cassettes/mock، telemetry noop، runtime system
├── app/             # L2 — ControlPlaneService، StubGovernor، bootstrap، config
├── api/             # L3 — FastAPI HTTP API
└── tests/           # L0_kernel / L1_adapters / L2_replay
```

### ۴.۲ ControlPlaneService (service.py)
- **مسئولیت:** Single orchestration path — proposal → gate → ledger → effect
- **State:** disposable projections (soma) rebuilt from ledger (genome)
- **Gates:** spawn_gate, budget_gate, effector_gate
- **Execution modes:** SHADOW (default) vs LIVE
- **Safety:** Kill-switch threading.RLock، approval TTL، idempotency (`_executed` set)
- **Saga compensation:** grant committed but ledger failed → release reservation
- **Audit:** `run_audit()` → violations list

### ۴.۳ StubGovernor (governor.py)
- **وضعیت:** Stub (قانون deterministic: per_organ = min(500, headroom // (2*n)))
- **Phase 1 plan:** جایگزینی با LangGraph agent از طریق LLMPort
- **قابلیت test:** L2 replay با cassettes

### ۴.۴ HTTP API (api/http.py)
| Endpoint | Method | وضعیت |
|---|---|---|
| /health | GET | 🟢 |
| /state | GET | 🟢 |
| /audit | GET | 🟢 |
| /proposals | POST | 🟢 (201/409/422) |
| /proposals/{id}/verdict | POST | 🟢 (200/404/422) |
| /proposals/{id}/execute | POST | 🟢 (200/409/404) |
| /kill | POST | 🟢 |
| /resume | POST | 🟢 |

**نیاز:** `pip install -e .[api]` برای FastAPI — اختیاری است.

### ۴.۵ نتیجهٔ NBB
این یک **کنترل‌پلن production-ready** با:
- ✅ SQLite ledger append-only
- ✅ CAS concurrency control
- ✅ Three-bucket cost accounting (input/output/orchestration)
- ✅ Fail-closed invariant checking
- ✅ Test coverage (L0/L1/L2)

**نقطهٔ یکپارچه‌سازی:** API می‌تواند به‌عنوان **sink** برای channelهای approve/kill/record_spend عمل کند.

---

## ۵. بازرسی Langar Bot (تلگرام)

### ۵.۱ brain/telegram_bot.py
- **نوع:** long-polling (نه webhook)
- **امنیت:** owner-only (`TELEGRAM_CHAT_ID` whitelist)
- **کامندها:**
  - `/start` / `/status` — snapshot daemon + budget + frontier + pending proposals
  - `/goal` — mission FA + current goal
  - `/pending` — لیست پیشنهادهای کد (self_code.list_pending())
  - `/pause` / `/resume` — ساخت/حذف `outputs/daemon.pause`
  - `/portrait` — self_growth learned capabilities
  - `/help`
- **callback buttons:** approve:{pid} / reject:{pid} → self_code.approve/reject
- **پیکربندی:** `.env` (TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)

### ۵.۲ brain/notify.py
- **Decision Packet format:** `[ALERT] · CONTEXT · WHY NOW · OPTIONS · RECOMMENDATION · CONSEQUENCE`
- **مقصد:** Telegram (best-effort) + `outputs/decision_packets.jsonl` (always)
- **Digest:** queue + flush ≤ NOTIFY_MAX_PER_DAY (default 3)
- **throttle:** ۲۰ ثانیه فاصله بین ارسال‌ها

### ۵.۳ نتیجهٔ Langar
| قابلیت | وضعیت |
|---|---|
| ارسال پیام به مالک | 🟢 (اگر token تنظیم شده) |
| دریافت پاسخ از مالک | ⚠️ partial — callback approve/reject کار می‌کند، اما conversational نیست |
| pause/resume daemon | 🟢 via daemon.pause file |
| poll decision packets | ❌ ندارد — داشبورد باید بخواند |

**نیازمندی یکپارچه‌سازی:** یک **reverse channel** از داشبورد/OCTOPUS به telegram bot برای push notificationهای real-time (مثلاً HITL approval queue).

---

## ۶. بازرسی ۴d_system/ (موتور پژوهش)

### ۶.۱ brain/events.py — Event Bus
- **ذخیره‌سازی:** SQLite `dashboard_events` در `outputs/4d_experiments.db`
- **event_names:** task.started, task.completed, task.failed, task.blocked, handoff.created, system.heartbeat, approval.required
- **approval_state:** {unknown, not_required, pending, approved, rejected} — همیشه صریح
- **API:** `emit()`, `get_recent()`, `latest_of()`, `get_summary()`, `counts()`, `resolve_latest_approval()`

### ۶.۲ brain/daemon.py
- **حلقهٔ اصلی:** tick هر ۳۰ ثانیه (قابل تنظیم)
- **قابلیت‌ها:**
  - گام خودمختار (AutomationController.run_one)
  - auto_propose_every (self_code)
  - flush_digest (notify)
  - housekeeping + self_portrait
- **کنترل:** `daemon.stop` (فایل) / `daemon.pause` (فایل) / SIGINT/SIGTERM
- **state:** `outputs/daemon_state.json`

### ۶.۳ control_plane/registry.yaml
- **subsystem:** ۲۴ ردیف با status ∈ {CONNECTED, PARTIAL, MISSING, UNKNOWN}
- **channel:** ۲۰ ردیف با risk_tier و authority
- **نمونهٔ MISSING:** `financial_nervous` — «جز data feeds بازار، لایهٔ مالیِ جدا در repo وجود ندارد»

---

## ۷. بازرسی _ops/ (OCTOPUS Organism)

### ۷.۱ state/ORGANISM-STATE.json
- **chrono beat:** ۳۲۵۰
- **epoch_mode:** allostatic (تابع فشار، نه clock)
- **wiring:** ۲۵ سیم (bool) — wire_doctor, wire_telegram, wire_unified, wire_lead, wire_mining, …
- **legs:** lead-naghshi (alive), mining-fleet (incubating), vault-cartographer (incubating)
- **cardiac budget:** spent=۳۶۳/۳۶۴، daily_cap=۲۸۸، depleted=true
- **germline_lag_h:** ۰.۷ (ok)

### ۷.۲ سایر فایل‌های state
- `fitness-latest.json` — weights (value=0.3, urgency=0.25, efficiency=0.2, human=0.2, waste=0.05)
- `cardiac-budget.json` — spent/resting
- `events.jsonl` — لاگ ساختاریافتهٔ رویدادها

### ۷.۳ نتیجهٔ OCTOPUS
این لایه **کاملاً زنده** است و به‌صورت مستقل از ۴d_system می‌تیکد. کانال‌های یکپارچه‌سازی باید از `wiring` استفاده کنند تا فعال/غیرفعال شوند.

---

## ۸. بازرسی nervous-system/ (استخراج‌کننده‌ها)

### ۸.۱ extract_live_data.py
- **source:** `4d_system/outputs/` (daemon_state.json, decision_packets.jsonl, frontier.json, 4d_experiments.db)
- **sink:** `nervous-system/live-data.js`
- **داده‌ها:** SOG identity/drift/healthy، events (total/by_name/by_status/by_agent/recent)، frontier cells، budget، packets، daemon ticks

### ۸.۲ extract_ops_data.py
- **source:** `_ops/state/` (ORGANISM-STATE.json, fitness-latest.json, cardiac-budget.json)
- **sink:** `nervous-system/ops-data.js`
- **داده‌ها:** money (month/today/confirmed/claimed/spend/projects)، time (chrono_beat/metabolic_age/wires_on/epoch_mode)

### ۸.۳ extract_graph.py
- **source:** `OCTOPUS/worlds/graph-data.js`
- **sink:** همان فایل (فقط generated timestamp refresh)

### ۸.۴ refresh-live-data.bat
- یک فایل batch ساده برای refresh دستی

**نتیجه:** Extractorها **کد Python واقعی** هستند و به‌خوبی کار می‌کنند. نیاز به **زمان‌بندی خودکار** (cron یا daemon tick) دارند.

---

## ۹. نقشهٔ یکپارچه‌سازی کانال‌ها (Channel Integration Map)

### ۹.۱ کانال‌های موجود (Connected / Partial)
| # | کانال | source | transform | sink | وضعیت |
|---|---|---|---|---|---|
| ۱ | events_bus | brain/events.py | SQLite INSERT | 4d_experiments.db::dashboard_events | CONNECTED |
| ۲ | daemon_tick | brain/daemon.py | JSON write | outputs/daemon_state.json | CONNECTED |
| ۳ | automation_cycle | brain/automation.py | emit → bus | events_bus | CONNECTED |
| ۴ | autoloop_research | brain/autoloop.py | analyze + save | memory_sql + frontier | PARTIAL |
| ۵ | sog_analysis | core/ | math → JSON | conclusions.json + experiments table | CONNECTED |
| ۶ | frontier_novelty | brain/frontier.py | record → JSON | outputs/self_evolved/frontier.json | CONNECTED |
| ۷ | self_evolve_strategy | brain/self_evolve.py | JSON write | strategy.json | CONNECTED |
| ۸ | self_code_pipeline | brain/self_code.py | propose→test→meta | outputs/self_code_proposals/ | CONNECTED |
| ۹ | guardrails_invariants | brain/guardrails.py | check → bus/halt | events_bus | CONNECTED |
| ۱۰ | budget_cloud | brain/budget.py | counter → JSON | outputs/llm_budget.json | CONNECTED |
| ۱۱ | llm_router_channel | llm/router.py | route + shadow | budget + llm_shadow.jsonl | PARTIAL |
| ۱۲ | telegram_owner | brain/telegram_bot.py | long-poll → API | Telegram API + decision_packets.jsonl | PARTIAL |
| ۱۳ | notify_packets | brain/notify.py | format + queue | decision_packets.jsonl + Telegram | CONNECTED |
| ۱۴ | ui_dashboard | ui/tab_dashboard.py | read bus | Streamlit display | CONNECTED |
| ۱۵ | backup_housekeeping | brain/backup.py | copy → dir | outputs/backups/ | CONNECTED |
| ۱۶ | memory_sqlite | memory/store.py | SQL | 4d_experiments.db | CONNECTED |
| ۱۷ | live_data_extract | extract_live_data.py | DB+JSON read → JS | nervous-system/live-data.js | EXISTS (manual) |
| ۱۸ | ops_data_extract | extract_ops_data.py | JSON read → JS | nervous-system/ops-data.js | EXISTS (manual) |
| ۱۹ | graph_freshness | extract_graph.py | timestamp update | OCTOPUS/worlds/graph-data.js | EXISTS (manual) |
| ۲۰ | nbb_control_plane | app/src/nbb_cp/ | proposal→gate→ledger | SQLite + FastAPI | CONNECTED (tests pass) |

### ۹.۲ کانال‌های MISSING / نیازمند ساخت
| # | کانال | source | transform | sink | اولویت | ریسک |
|---|---|---|---|---|---|---|
| A | mining_telemetry | Mining fleet API / local scripts | normalize → JSON | _ops/state/mining-telemetry.json + OCTOPUS risk world | HIGH | MEDIUM |
| B | wallet_events | Wallet APIs (etoro/exchanges) | normalize → JSON | _ops/state/wallet-events.json + OCTOPUS money world | HIGH | HIGH (مالی) |
| C | git_hooks | `.git/hooks/post-commit` | diff → proposal | 4d_system/outputs/self_code_proposals/ | MEDIUM | MEDIUM |
| D | agent_telemetry | _ops/events.jsonl / unified_bus.py | aggregate → tracer | audit dashboard + panel doctor | MEDIUM | LOW |
| E | vault_indexer | Vault markdown files | FTS5 + vector index | semantic search API | MEDIUM | LOW |
| F | cron_daily_question | cron job | ai.daily_question → research_loop | decision_packets.jsonl | LOW | LOW |
| G | hitl_approval_queue | decision_packets.jsonl | poll → notify → wait | Telegram notification + owner verdict | HIGH | MEDIUM |
| H | cross_world_nav | OCTOPUS worlds/ | nextAction() → recommendation | cockpit UI | MEDIUM | LOW |
| I | live_data_auto_refresh | daemon tick / cron | run extract_live_data.py | nervous-system/live-data.js | HIGH | LOW |
| J | ops_data_auto_refresh | organism.py tick | run extract_ops_data.py | nervous-system/ops-data.js | HIGH | LOW |
| K | nbb_to_octopus | NBB ledger events | translate → ORGANISM-STATE | _ops/state/ORGANISM-STATE.json | MEDIUM | MEDIUM |
| L | dashboard_to_telegram | CONTROL-PANEL user click | sendPrompt → queue | Telegram bot | LOW | LOW |
| M | cardiac_budget_alert | _ops/cardiac-budget.json | threshold check → alert | notify.py → Telegram | HIGH | LOW |
| N | vault_sync_auto | brain/vault_sync.py | watch → sync | Obsidian vault | MEDIUM | LOW |
| O | discovery_to_graph | brain/autoloop.py / frontier.py | format → node/edge | OCTOPUS/worlds/graph-data.js | MEDIUM | LOW |

---

## ۱۰. مشخصات فنی ۱۵ کانال (Channel Specs)

### Ch-01: Mining Fleet Telemetry → OCTOPUS Risk World
- **Source:** `_ops/legs/mining/` یا APIهای محلی (nicehash, xmrig)
- **Transform:** `scripts/normalize_mining_telemetry.py` — hashrate, temp, power, efficiency
- **Sink:** `_ops/state/mining-telemetry.json` + `OCTOPUS/worlds/08-risk/`
- **Code Target:** `_ops/legs/mining/telemetry_bridge.py`
- **Priority:** P1 (HIGH)
- **Risk:** MEDIUM — نیاز به SSH/local access یا API key
- **Notes:** در registry.yaml به‌عنوان MISSING شناسایی شده

### Ch-02: Wallet/Transaction Events → OCTOPUS Money World
- **Source:** eToro API / exchange APIs / manual CSV
- **Transform:** `scripts/normalize_wallet_events.py` — deposit, withdrawal, position open/close
- **Sink:** `_ops/state/wallet-events.json` + `OCTOPUS/worlds/03-money/`
- **Code Target:** `_ops/legs/wallet_bridge.py`
- **Priority:** P1 (HIGH)
- **Risk:** HIGH — دادهٔ مالی واقعی؛ نیاز به encryption + audit trail
- **Notes:** در ORGANISM-STATE، mining.money_link="incubating"

### Ch-03: Auto-Refresh Live-Data Extractor
- **Source:** `4d_system/outputs/*`
- **Transform:** `extract_live_data.py` (موجود)
- **Sink:** `nervous-system/live-data.js`
- **Code Target:** اضافه کردن trigger در `brain/daemon.py` (tick % N == 0)
- **Priority:** P1 (HIGH)
- **Risk:** LOW — idempotent، read-only
- **Notes:** اکنون manual است؛ نیاز به scheduling خودکار

### Ch-04: Auto-Refresh Ops-Data Extractor
- **Source:** `_ops/state/*`
- **Transform:** `extract_ops_data.py` (موجود)
- **Sink:** `nervous-system/ops-data.js`
- **Code Target:** اضافه کردن trigger در `_ops/organism.py` یا cron
- **Priority:** P1 (HIGH)
- **Risk:** LOW

### Ch-05: Cardiac Budget Alert → Telegram
- **Source:** `_ops/state/cardiac-budget.json` (spent vs daily_cap)
- **Transform:** threshold check (`spent >= cap * 0.8`)
- **Sink:** `brain/notify.py` → Telegram
- **Code Target:** `_ops/budget_alert.py` + hook در `notify.py`
- **Priority:** P1 (HIGH)
- **Risk:** LOW — read-only + notify
- **Notes:** اکنون depleted=true بدون alert فوری

### Ch-06: HITL Approval Queue → Telegram Push
- **Source:** `outputs/decision_packets.jsonl` (approval_state=pending)
- **Transform:** poll every N seconds → format → push
- **Sink:** Telegram bot (owner)
- **Code Target:** `brain/telegram_bot.py` — اضافه کردن `poll_approval_queue()`
- **Priority:** P1 (HIGH)
- **Risk:** MEDIUM — نیاز به idempotency (message_id dedup)
- **Notes:** اکنون approve/reject فقط از داخل داشبورد کار می‌کند

### Ch-07: Git Hooks → Self-Evolution Proposals
- **Source:** `.git/hooks/post-commit`
- **Transform:** diff stat → proposal template
- **Sink:** `4d_system/outputs/self_code_proposals/`
- **Code Target:** `.git/hooks/post-commit` (bash) + `brain/self_code.py::ingest_diff()`
- **Priority:** P2 (MEDIUM)
- **Risk:** MEDIUM — می‌تواند noise تولید کند

### Ch-08: Agent Telemetry → Audit Dashboard
- **Source:** `_ops/events.jsonl` + `unified_bus.py`
- **Transform:** aggregate by agent_id → tracer metrics
- **Sink:** `OCTOPUS/worlds/01-cockpit/` یا panel doctor
- **Code Target:** `_ops/telemetry_aggregator.py`
- **Priority:** P2 (MEDIUM)
- **Risk:** LOW

### Ch-09: Vault Indexer → Semantic Search API
- **Source:** Vault markdown files (F:/backup/**/*.md)
- **Transform:** chunk → embed (Chroma) + FTS5
- **Sink:** `outputs/chroma_db/` + SQLite FTS5 table
- **Code Target:** `memory/vectorstore.py::index_vault()` + `memory/store.py::add_fts5()`
- **Priority:** P2 (MEDIUM)
- **Risk:** LOW
- **Notes:** chroma_rag در registry.yaml PARTIAL است

### Ch-10: Cross-World Navigation Signals
- **Source:** OCTOPUS worlds/ (۰۱ تا ۱۰)
- **Transform:** user context → nextAction() heuristic
- **Sink:** `OCTOPUS/worlds/index.html` یا CONTROL-PANEL
- **Code Target:** `OCTOPUS/octo-core.js::recommendNext()`
- **Priority:** P2 (MEDIUM)
- **Risk:** LOW

### Ch-11: NBB Ledger → ORGANISM-STATE Sync
- **Source:** `app/` (NBB SQLite ledger)
- **Transform:** translate events → organism state update
- **Sink:** `_ops/state/ORGANISM-STATE.json`
- **Code Target:** `_ops/adapters/nbb_sync.py`
- **Priority:** P2 (MEDIUM)
- **Risk:** MEDIUM — دو منبع حقیقت (dual source of truth)

### Ch-12: Dashboard Click → Telegram Delivery
- **Source:** CONTROL-PANEL.html (user click)
- **Transform:** sendPrompt → queue in decision_packets
- **Sink:** Telegram bot
- **Code Target:** `brain/notify.py::queue_for_digest()` + `telegram_bot.py`
- **Priority:** P3 (LOW)
- **Risk:** LOW

### Ch-13: Discovery → Graph Data
- **Source:** `brain/frontier.py` / `brain/autoloop.py`
- **Transform:** pattern → node/edge JSON
- **Sink:** `OCTOPUS/worlds/graph-data.js`
- **Code Target:** `brain/vault_sync.py::sync_discovery_to_graph()`
- **Priority:** P2 (MEDIUM)
- **Risk:** LOW

### Ch-14: Cron Daily Question → Research Loop
- **Source:** Cron job (`0 9 * * *`)
- **Transform:** trigger `brain/autoloop.py` with daily_question seed
- **Sink:** decision_packets.jsonl + frontier.json
- **Code Target:** `scripts/daily_question.py`
- **Priority:** P3 (LOW)
- **Risk:** LOW

### Ch-15: Vault Sync Auto-Watch
- **Source:** Vault file system changes
- **Transform:** watchdir → debounce → sync
- **Sink:** Obsidian vault (two-way)
- **Code Target:** `brain/vault_sync.py` + `watchdog` library
- **Priority:** P2 (MEDIUM)
- **Risk:** LOW
- **Notes:** vault_obsidian در registry.yaml UNKNOWN است

---

## ۱۱. وابستگی‌ها و نقطه‌های شکننده (Dependency & Risk Analysis)

### ۱۱.۱ Dependency Graph (خلاصه)
```
4d_system/outputs/           _ops/state/
    ├── daemon_state.json  ─────┐    ├── ORGANISM-STATE.json ───┐
    ├── 4d_experiments.db  ─────┼────┤    ├── fitness-latest.json    │
    ├── frontier.json      ─────┤    │    ├── cardiac-budget.json    │
    ├── decision_packets.jsonl ─┘    │    └── events.jsonl          │
    └── self_evolved/               │                             │
           │                        │                             │
           ▼                        ▼                             ▼
    nervous-system/            OCTOPUS/worlds/              01 - Dashboard/
    ├── live-data.js           ├── graph-data.js            ├── CONTROL-PANEL.html
    └── ops-data.js            └── 01-cockpit/ ...          └── BRAIN-FOCUS-BOARD.html
           │                                                       ▲
           └──────────────────────► app/ (NBB) ◄────────────────────┘
                                      ├── SQLite ledger
                                      ├── FastAPI
                                      └── StubGovernor
```

### ۱۱.۲ نقاط شکنندهٔ شناسایی‌شده
| # | نقطهٔ شکننده | شدت | راه‌حل پیشنهادی |
|---|---|---|---|
| ۱ | دو منبع حقیقت: ۴d_system vs _ops | MEDIUM | یکپارچه‌سازی با NBB ledger به‌عنوان source of truth |
| ۲ | daemon_state.json manual write — race condition احتمالی | MEDIUM | استفاده از file lock یا atomic rename |
| ۳ | telegram_bot token در .env plaintext | MEDIUM | استفاده از Windows Credential Manager یا keyring |
| ۴ | decision_packets.jsonl بدون rotate — رشد نامحدود | LOW | logrotate یا size-based archiving |
| ۵ | CONTROL-PANEL فاقت backend live — stale data | HIGH | اضافه کردن auto-refresh (SSE/polling) |
| ۶ | _ops/cardiac-budget depleted=true بدون alert | HIGH | Ch-05: budget alert channel |
| ۷ | vault_obsidian status=UNKNOWN | MEDIUM | Ch-15: auto-watch sync |
| ۸ | financial_nervous status=MISSING | HIGH | Ch-01 و Ch-02: mining + wallet channels |

### ۱۱.۳ گیت‌های امنیتی فعال
- **rotation CRITICAL:** ۴ ردیف باز (طبق SYSTEM-DASHBOARD) — در CONTROL-PANEL به ۰ تغییر کرده (ناهماهنگی!)
- **gitleaks:** ❌ انجام نشده
- **git init:** ❌ (SYSTEM-DASHBOARD) vs ✅ (BRAIN-FOCUS-BOARD) — **ناهماهنگی داده!**
- **ratify Brain.md:** ❌ (SYSTEM-DASHBOARD) vs ✅ (BRAIN-FOCUS-BOARD) — **ناهماهنگی داده!**

**یافتهٔ بحرانی:** دو داشبورد (SYSTEM-DASHBOARD vs BRAIN-FOCUS-BOARD vs CONTROL-PANEL) gateهای متفاوتی نشان می‌دهند. CONTROL-PANEL gateها را بروزتر نشان می‌دهد.

---

## ۱۲. توصیه‌های اولویت‌دار برای Code Builder Swarm

### موج ۱ (P1 — باید ساخته شود)
1. **Ch-03 + Ch-04:** Auto-refresh extractorها — hook در daemon tick و organism tick
2. **Ch-05:** Cardiac budget alert — threshold + notify
3. **Ch-06:** HITL approval queue → Telegram — poll + push
4. **Ch-01 + Ch-02:** Mining + wallet telemetry — normalize + OCTOPUS sink

### موج ۲ (P2 — باید ساخته شود)
5. **Ch-07:** Git hooks → self-evolution
6. **Ch-08:** Agent telemetry → audit dashboard
7. **Ch-09:** Vault indexer → semantic search
8. **Ch-10:** Cross-world navigation
9. **Ch-11:** NBB ledger → ORGANISM-STATE sync

### موج ۳ (P3 — اختیاری)
10. **Ch-12:** Dashboard → Telegram delivery
11. **Ch-13:** Discovery → Graph data
12. **Ch-14:** Cron daily question
13. **Ch-15:** Vault sync auto-watch

---

## ۱۳. پیوست: فایل‌های کلیدی و هدفشان

| مسیر | نوع | هدف | کد واقعی؟ |
|---|---|---|---|
| `4d_system/brain/telegram_bot.py` | Python | Owner Telegram bot | ✅ |
| `4d_system/brain/events.py` | Python | Structured event bus (SQLite) | ✅ |
| `4d_system/brain/daemon.py` | Python | Headless month-runner | ✅ |
| `4d_system/brain/notify.py` | Python | Decision packets + digest | ✅ |
| `4d_system/brain/autoloop.py` | Python | Research autoloop engine | ✅ |
| `4d_system/control_plane/registry.yaml` | YAML | Subsystem + channel registry | ✅ |
| `app/src/nbb_cp/app/service.py` | Python | ControlPlaneService (ledger, gates) | ✅ |
| `app/src/nbb_cp/api/http.py` | Python | FastAPI HTTP API | ✅ |
| `nervous-system/extract_live_data.py` | Python | 4d_system → live-data.js | ✅ |
| `nervous-system/extract_ops_data.py` | Python | _ops → ops-data.js | ✅ |
| `_ops/organism.py` | Python | OCTOPUS organism core | ✅ |
| `_ops/wiring.py` | Python | Wiring configuration | ✅ |
| `_ops/state/ORGANISM-STATE.json` | JSON | Live organism state | ✅ (runtime) |
| `01 - Dashboard/CONTROL-PANEL.html` | HTML | Unified cockpit | ⚠️ static generated |
| `05 - Agents/AGENT_REGISTRY.md` | Markdown | Agent definitions | ❌ spec only |

---

*گزارش کامل شد. هیچ کدی نوشته نشده — فقط بازرسی، نقشه‌برداری، و مشخصات.*
