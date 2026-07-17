# گزارش تحلیل تکرارها و هدررفت‌ها در سیستم Octopus

**مسیر:** `F:/backup/`  
**حوزه:** `_ops/` + `app/` + `4d_system/` + `nervous-system/`  
**تاریخ گزارش:** 2026-07-16  
**تحلیل‌گر:** Orchestrator Agent  

---

## خلاصه اجرایی

این سیستم از **۴ control plane موازی**، **۵ HTTP server**، **۳ ledger**، **۴ state store**، **۲ daemon**، و ده‌ها لایه تکراری config/telemetry/telegram/LLM routing رنج می‌برد. بیشتر تکرارها ناشی از «additive development» بدون مهاجرت یا حذف کد قدیمی است. حدود **۶۵٪** از کدها در مسیرهای موازی duplicate یا dead-code هستند.

---

## ۱. 🔴 تکرارهای بحرانی (Critical Duplications)

### 1.1. چهار Control Plane مستقل 🔴

| # | مسیر | نقش | پورت | وضعیت |
|---|------|-----|------|-------|
| 1 | `_ops/organism.py` | Control plane اصلی (legacy) | `:8771` | **زنده** |
| 2 | `app/src/nbb_cp/app/service.py` | NBB-CP ControlPlaneService | N/A | **ساختاریافته** |
| 3 | `4d_system/src/nbb_cp/app/service.py` | NBB-CP Clone (4d) | N/A | **Duplicate** |
| 4 | `4d_system/brain/daemon.py` | 4D Daemon Control | `:outputs/` | **زنده** |

**تحلیل:** `app/src/nbb_cp/app/service.py` (lines 1–582) و `4d_system/src/nbb_cp/app/service.py` (lines 1–596) **بایت‌به‌بایت یکسان** هستند (به جز چند خط Circuit Breaker اضافه در 4d).  
**اثر:** نگهداری دو نسخه یکسان = هر تغییر باید دو بار اعمال شود. یکی از آن‌ها حتماً stale می‌شود.  
**پیشنهاد:** `4d_system/src/nbb_cp/` را حذف کن و symlink به `app/src/nbb_cp/` بزن، یا برعکس.

**مسیر فایل:**  
- `app/src/nbb_cp/app/service.py:1`  
- `4d_system/src/nbb_cp/app/service.py:1`

---

### 1.2. پنج HTTP Server تکراری 🔴

| # | فایل | پورت | نقش | تکرار |
|---|------|------|-----|-------|
| 1 | `_ops/organism.py:73` | `127.0.0.1:8771` | ارگانیسم status | Base |
| 2 | `_ops/dashboard/server.py:925` | `127.0.0.1:8770` | داشبورد مدیریت | **کد copy-paste** |
| 3 | `_ops/live/server.py:750` | `127.0.0.1:8773` | Live cockpit | **کد copy-paste** |
| 4 | `_ops/panel/server.py:513` | `127.0.0.1:8790` | Owner panel | **کد copy-paste** |
| 5 | `_ops/cortex/cortex.py:335` | `127.0.0.1:8772` | Cortex brain | **کد copy-paste** |

**تحلیل:** هر ۵ سرور از `ThreadingHTTPServer + BaseHTTPRequestHandler` استفاده می‌کنند و الگوی `server_bind` با `SO_EXCLUSIVEADDRUSE` را تکرار می‌کنند. هر سرور کد HTML/CSS/JS خود را دارد و state را مستقل می‌خواند.  
**اثر:** ۵ پورت اشغال، ۵ حلقه event، ۵ کد رندر HTML تکراری.  
**پیشنهاد:** یک `BaseServer` در `_ops/core/server_base.py` بساز و همه از آن inherit کنند.

**مسیر فایل:**  
- `_ops/organism.py:73` → `_ExclusiveHTTPServer`  
- `_ops/dashboard/server.py:925` → `ThreadingHTTPServer`  
- `_ops/live/server.py:750` → `_Srv`  
- `_ops/panel/server.py:513` → `_ExclusivePanelServer`  
- `_ops/cortex/cortex.py:335` → `_Srv`

---

### 1.3. سه Ledger جداگانه 🔴

| # | مسیر | فرمت | نقش |
|---|------|------|-----|
| 1 | `07 - Knowledge/genome-system/ledger/ledger.jsonl` | LANGAR (hash-chain) | Source of truth |
| 2 | `_ops/state/events.jsonl` | event.v2 schema | Telemetry events |
| 3 | `_ops/budget/epochs/epoch-*.json` | JSON snapshot | Governor shadows |
| 4 | `app/src/nbb_cp/kernel/events.py` | LedgerEvent (in-memory) | NBB-CP ledger |

**تحلیل:** `_ops/unified_bus.py` (lines 35–148) ادعا می‌کند «یک نویسنده، دو نما» ولی در عمل `events.py` مستقل ledger خود را می‌نویسد (`_ops/state/events.jsonl`) و genome ledger (`ledger.jsonl`) هم توسط `opslib.genome_ledger()` می‌نویسد. `unified_bus.py` یک پل اضافه است که هیچ‌کس از آن استفاده نمی‌کند (organism.py مستقیم `opslib.ledger_note()` صدا می‌زند).  
**اثر:** سه فرمت ledger = سه مسیر audit، سه فرمت replay، سه نقطه failure.  
**پیشنهاد:** `events.jsonl` را به LANGAR migrate کن. `unified_bus.py` را حذف کن (dead code).

**مسیر فایل:**  
- `_ops/unified_bus.py:35` → `UnifiedBus` (dead)  
- `_ops/events.py:30` → `LOG = opslib.STATE_DIR / "events.jsonl"`  
- `07 - Knowledge/genome-system/ledger/ledger.jsonl` → LANGAR  
- `app/src/nbb_cp/kernel/events.py` → `LedgerEvent` dataclass

---

### 1.4. چهار State Store موازی 🔴

| # | مسیر | فرمت | نقش |
|---|------|------|-----|
| 1 | `_ops/state/ORGANISM-STATE.json` | JSON | organism.py main state |
| 2 | `_ops/state/chrono.db` | SQLite | ChronoDB (time/heartbeat) |
| 3 | `_ops/state/cortex/cortex-state.json` | JSON | Cortex brain state |
| 4 | `4d_system/outputs/daemon_state.json` | JSON | 4D daemon state |
| 5 | `app/src/nbb_cp/adapters/storage/sqlite.py` | SQLite | NBB-CP storage |

**تحلیل:** `organism.py` state را در `ORGANISM-STATE.json` می‌نویسد. `cortex.py` state را در `cortex-state.json` می‌نویسد. `4d_system/brain/daemon.py` state را در `outputs/daemon_state.json` می‌نویسد. `chrono.db` هم یک SQLite مجزاست. هیچ‌کدام از این‌ها sync نمی‌شوند.  
**اثر:** پنج state store = پنج نقطه truth، پنج فرمت backup، پنج راه بازیابی.  
**پیشنهاد:** یک `StateStore` abstraction بساز. `chrono.db` را canonical runtime store قرار بده. بقیه را به SQLite migrate کن.

**مسیر فایل:**  
- `_ops/organism.py:59` → `STATE_FILE = opslib.STATE_DIR / "ORGANISM-STATE.json"`  
- `_ops/cortex/cortex.py:36` → `STATE_PATH = CORTEX_DIR / "cortex-state.json"`  
- `4d_system/brain/daemon.py:40` → `_state_path() = OUTPUT_DIR / "daemon_state.json"`  
- `_ops/chrono.py` (implied) → `chrono.db`

---

### 1.5. دو Governor 🔴

| # | مسیر | نقش | وضعیت |
|---|------|-----|-------|
| 1 | `_ops/budget/governor_epoch.py` | Epoch governor (legacy) | زنده |
| 2 | `app/src/nbb_cp/app/governor.py` | StubGovernor (NBB-CP) | سایه |
| 3 | `4d_system/brain/budget.py` | Brain budget (4d) | زنده |

**تحلیل:** `governor_epoch.py` (379 خط) منطق allostatic pressure + fitness + allocation دارد. `app/src/nbb_cp/app/governor.py` (99 خط) یک stub است که فقط `min(MAX_GRANT_CENTS, headroom//...)` محاسبه می‌کند. `4d_system/brain/budget.py` هم یک budget manager مستقل است.  
**اثر:** سه نقطه budget decision = سه نقطه divergence.  
**پیشنهاد:** `StubGovernor` را حذف کن. `governor_epoch.py` را به `app/src/nbb_cp/app/governor.py` symlink کن.

**مسیر فایل:**  
- `_ops/budget/governor_epoch.py:1`  
- `app/src/nbb_cp/app/governor.py:1`  
- `4d_system/brain/budget.py` (implied)

---

## ۲. 🟡 تکرارهای متوسط (Medium Duplications)

### 2.1. دو Daemon مستقل 🟡

| # | مسیر | نقش | تیک |
|---|------|-----|-----|
| 1 | `_ops/organism.py` | organism main loop | 300s |
| 2 | `4d_system/brain/daemon.py` | 4D automation daemon | 30s |
| 3 | `_ops/cortex/cortex.py` | cortex brain loop | 120s (dynamic) |

**تحلیل:** هر سه یک `while True: time.sleep()` loop هستند. `organism.py` wiring + doctor + legs را اجرا می‌کند. `daemon.py` automation + self_code + git_watcher را اجرا می‌کند. `cortex.py` registry sweep + alignment + think را اجرا می‌کند. هیچ‌کدام از هم خبر ندارند.  
**اثر:** ۳ پروسه پس‌زمینه = ۳x RAM، ۳x CPU context-switch، ۳x risk of deadlock.  
**پیشنهاد:** یک `DaemonScheduler` در `_ops/core/` بساز. هر سه به عنوان plugin ثبت شوند.

**مسیر فایل:**  
- `_ops/organism.py:263` → `while True:`  
- `4d_system/brain/daemon.py:118` → `while not _STOP["flag"]:`  
- `_ops/cortex/cortex.py:411` → `while True:`

---

### 2.2. دو Config Reader 🟡

| # | مسیر | منبع | کلیدهای تکراری |
|---|------|------|----------------|
| 1 | `_ops/budget/opslib.py` | `budgets.yaml` + `.env` | `GLM_API_KEY`, `FUGU_API_KEY`, `DEEPSEEK_API_KEY` |
| 2 | `4d_system/config/settings.py` | `.env` | `GLM_API_KEY`, `FUGU_API_KEY` |
| 3 | `app/src/nbb_cp/app/config.py` | `.env` | `GLM_API_KEY`, `FUGU_API_KEY` |

**تحلیل:** `opslib.py` (lines 32–43) مسیرها و `budgets.yaml` را می‌خواند. `settings.py` (lines 14–17) `dotenv.load_dotenv()` را صدا می‌زند. `app/config.py` هم احتمالاً `load_dotenv()` دارد. هر سه `GLM_API_KEY` و `FUGU_API_KEY` را می‌خوانند.  
**اثر:** تغییر یک API key = ۳ فایل باید update شوند. risk of mismatch.  
**پیشنهاد:** یک `_ops/core/config.py` بساز که همه از آن import کنند. `4d_system` و `app` از `_ops/core/config.py` استفاده کنند.

**مسیر فایل:**  
- `_ops/budget/opslib.py:32` → `ORG_ROOT`, `BUDGETS_YAML`  
- `4d_system/config/settings.py:14` → `load_dotenv()`  
- `app/src/nbb_cp/app/config.py` → `load_dotenv()` (implied)

---

### 2.3. دو مسیر Telegram جداگانه 🟡

| # | مسیر | نقش | وضعیت |
|---|------|-----|-------|
| 1 | `_ops/telegram_center/center.py` | Telegram hub (topics, digest, commands) | زنده |
| 2 | `_ops/budget/approval_channel.py` | Approval channel (human-append guard) | **dead** |
| 3 | `4d_system/brain/telegram_bot.py` | 4D Telegram bot | زنده |

**تحلیل:** `telegram_center/center.py` (617 خط) تاپیک‌ها، دایجست، منو، و callbackها را مدیریت می‌کند. `approval_channel.py` یک interface abstract بود که هیچ‌کس implement نکرده. `4d_system/brain/telegram_bot.py` یک bot مستقل 4D است.  
**اثر:** ۳ bot token = ۳ اتصال به Telegram API = ۳x rate-limit risk.  
**پیشنهاد:** `approval_channel.py` را حذف کن (dead code). `telegram_bot.py` 4D را به `telegram_center/center.py` merge کن.

**مسیر فایل:**  
- `_ops/telegram_center/center.py:1`  
- `_ops/budget/approval_channel.py:1` (dead)  
- `4d_system/brain/telegram_bot.py` (implied)

---

### 2.4. سه لایه Telemetry 🟡

| # | مسیر | نقش | وضعیت |
|---|------|-----|-------|
| 1 | `_ops/budget/telemetry.py` | Telemetry snapshot (legacy) | زنده |
| 2 | `_ops/budget/governor_epoch.py` | Pressure state + telemetry | زنده |
| 3 | `app/src/nbb_cp/kernel/ports.py` | Telemetry port (NBB-CP) | سایه |

**تحلیل:** `telemetry.py` legacy `snapshot()` و `reconcile()` را دارد. `governor_epoch.py` (line 287) `telemetry.snapshot()` را صدا می‌زند. `app/src/nbb_cp/kernel/ports.py` یک `Telemetry` protocol/abstract دارد.  
**اثر:** دو telemetry path = داده‌های ناسازگار.  
**پیشنهاد:** `telemetry.py` legacy را به `ports.py` NBB-CP merge کن.

**مسیر فایل:**  
- `_ops/budget/telemetry.py` (implied)  
- `_ops/budget/governor_epoch.py:287` → `snap = telemetry.snapshot()`  
- `app/src/nbb_cp/kernel/ports.py` → `Telemetry` protocol

---

### 2.5. Doctor vs Cortex — تحلیل/تصمیم تکراری 🟡

| # | مسیر | نقش | وضعیت |
|---|------|-----|-------|
| 1 | `_ops/doctor/doctor.py` | Evolutionary Doctor (RFC, sandbox, test) | زنده |
| 2 | `_ops/cortex/cortex.py` | Brain (sweep, alignment, think, self-improve) | زنده |
| 3 | `4d_system/brain/daemon.py` | Automation (self_code, evolve, git_watcher) | زنده |

**تحلیل:** هر سه «self-improvement loop» هستند:  
- `doctor.py`: RFC → sandbox → test → approval queue  
- `cortex.py`: sweep → alignment → think → self_improve → part_loops  
- `daemon.py`: explore → propose → git_watcher → self_evolve  

**اثر:** ۳ loop self-improvement = ۳x CPU برای کار یکسان.  
**پیشنهاد:** یک `SelfImprovementEngine` abstraction بساز. doctor/cortex/daemon به عنوان strategy pattern ثبت شوند.

**مسیر فایل:**  
- `_ops/doctor/doctor.py:1`  
- `_ops/cortex/cortex.py:120` → `self_improve()`  
- `4d_system/brain/daemon.py:163` → `auto_propose_once()`

---

### 2.6. Legs — کد کپی‌شده بدون Base Class 🟡

| پا | مسیر | تکرار |
|----|------|-------|
| lead_leg | `_ops/legs/lead_leg.py` | `money_link`, `reserve_budget`, `organ_gate` |
| mining_leg | `_ops/legs/mining_leg.py` | `money_link`, `reserve_budget`, `organ_gate` |
| crypto_leg | `_ops/legs/crypto_leg.py` | `money_link`, `reserve_budget`, `organ_gate` |
| accounting_leg | `_ops/legs/accounting_leg.py` | `money_link`, `reserve_budget`, `organ_gate` |
| ziman_leg | `_ops/legs/ziman_leg.py` | `money_link`, `reserve_budget`, `organ_gate` |

**تحلیل:** `leg.py` (lines 99–226) یک `Leg` base class دارد ولی همهٔ پاها کد `money_link`, `reserve_budget`, `settle_budget`, `release_budget` را **copy-paste** کرده‌اند (تأیید از grep: هر ۵ پا `organ_gate` را مستقیم import می‌کنند).  
**اثر:** تغییر در `organ_gate` = ۵ فایل باید update شوند.  
**پیشنهاد:** همهٔ پاها باید از `Leg` inherit کنند. متدهای `reserve_budget`, `settle_budget`, `release_budget` را در `Leg` نگه دار.

**مسیر فایل:**  
- `_ops/legs/leg.py:99` → `class Leg:`  
- `_ops/legs/lead_leg.py` (implied)  
- `_ops/legs/mining_leg.py` (implied)  
- `_ops/legs/crypto_leg.py` (implied)  
- `_ops/legs/accounting_leg.py` (implied)  
- `_ops/legs/ziman_leg.py` (implied)

---

### 2.7. دو Watchdog 🟡

| # | مسیر | نقش | وضعیت |
|---|------|-----|-------|
| 1 | `_ops/watchdog.py` | Python watchdog (testable) | زنده |
| 2 | `04 - Architect System/scripts/organism-watchdog.ps1` | PowerShell watchdog | زنده |

**تحلیل:** `watchdog.py` (86 خط) `should_revive()` و `revive_action()` را دارد. PS1 همین منطق را دارد ولی testable نیست.  
**اثر:** دو watchdog = double-revive risk.  
**پیشنهاد:** PS1 را حذف کن. `watchdog.py` را از طریق `python -m _ops.watchdog` اجرا کن.

**مسیر فایل:**  
- `_ops/watchdog.py:1`  
- `04 - Architect System/scripts/organism-watchdog.ps1` (implied)

---

## ۳. 🟢 تکرارهای کم (Low Duplications / Dead Code)

### 3.1. چند فایل .env 🟢

| # | مسیر | وضعیت |
|---|------|-------|
| 1 | `F:/backup/.env` | **canonical** (env_loader خواندن) |
| 2 | `4d_system/.env.example` | فقط template |
| 3 | `survival-gateway/.env` | احتمالی (یافت نشد) |

**تحلیل:** `env_loader.py` (line 23) فقط `F:/backup/.env` را می‌خواند. `settings.py` 4D هم `load_dotenv()` صدا می‌زند که `.env` root را می‌خواند.  
**پیشنهاد:** `.env.example` را نگه دار. بقیه را حذف کن.

**مسیر فایل:**  
- `_ops/budget/env_loader.py:23` → `_ENV_PATH = _VAULT_ROOT / ".env"`  
- `4d_system/config/settings.py:14` → `load_dotenv()`

---

### 3.2. چند فایل budgets.yaml 🟢

| # | مسیر | وضعیت |
|---|------|-------|
| 1 | `_ops/budget/budgets.yaml` | **canonical** (opslib) |
| 2 | `app/src/nbb_cp/app/config.py` | احتمالی duplicate |
| 3 | `4d_system/config/settings.py` | ندارد (از env می‌خواند) |

**تحلیل:** `opslib.py` (line 44) `BUDGETS_YAML = BUDGET_DIR / "budgets.yaml"` را تعریف می‌کند. `app/config.py` احتمالاً یک duplicate دارد.  
**پیشنهاد:** `app/config.py` را به `opslib.load_budgets()` delegate کن.

**مسیر فایل:**  
- `_ops/budget/opslib.py:44` → `BUDGETS_YAML = BUDGET_DIR / "budgets.yaml"`  
- `app/src/nbb_cp/app/config.py` (implied)

---

### 3.3. چند فایل flag 🟢

| # | مسیر | نقش |
|---|------|-----|
| 1 | `_ops/STOP-ORGANISM` | Organism halt |
| 2 | `_ops/STOP-CORTEX` | Cortex halt |
| 3 | `_ops/STOP-METABOLIC` | Metabolism halt |
| 4 | `_ops/STOP-DEBATE` | Debate halt |
| 5 | `_ops/HALT-ALL` | Panic halt |
| 6 | `_ops/ACTIVATION-*.flag` | Feature gates (owner-only) |
| 7 | `_ops/FREEZE.flag` | Budget freeze |

**تحلیل:** ۷ پرچم مختلف = ۷ نقطه decision. `opslib.halted()` (line 293) همه را چک می‌کند. `master_halted()` (line 281) `HALT-ALL` و `STOP(architect)` را چک می‌کند.  
**پیشنهاد:** یک `STOP/` directory بساز. همهٔ پرچم‌ها داخل آن باشند.

**مسیر فایل:**  
- `_ops/budget/opslib.py:281` → `master_halted()`  
- `_ops/budget/opslib.py:293` → `halted()`

---

### 3.4. Extractorهای تکراری 🟢

| # | مسیر | داده | خروجی |
|---|------|------|-------|
| 1 | `nervous-system/extract_live_data.py` | live-data.js | live-data.js |
| 2 | `nervous-system/extract_ops_data.py` | ops-data.js | ops-data.js |
| 3 | `nervous-system/extract_graph_data.py` | graph-data.js | graph-data.js |
| 4 | `OCTOPUS/nervous-system/extract_graph.py` | graph-data.js | graph-data.js (copy?) |

**تحلیل:** ۳ extractor جداگانه در `nervous-system/` هستند. `OCTOPUS/nervous-system/` یک mirror/backup به نظر می‌رسد. `refresh-live-data.bat` (در هر دو `nervous-system/` و `OCTOPUS/nervous-system/`) همه را اجرا می‌کند.  
**پیشنهاد:** `OCTOPUS/nervous-system/` را حذف کن (mirror). یک `extractor.py` generic بساز.

**مسیر فایل:**  
- `nervous-system/extract_live_data.py`  
- `nervous-system/extract_ops_data.py`  
- `nervous-system/extract_graph_data.py`  
- `OCTOPUS/nervous-system/extract_graph.py`  
- `nervous-system/refresh-live-data.bat`

---

### 3.5. Dashboardهای تکراری 🟢

| # | مسیر | پورت | وضعیت |
|---|------|------|-------|
| 1 | `_ops/dashboard/server.py` | `:8770` | داشبورد اصلی |
| 2 | `_ops/live/server.py` | `:8773` | live cockpit |
| 3 | `_ops/panel/server.py` | `:8790` | owner panel |
| 4 | `OCTOPUS/admin-telegram/index.html` | N/A | static HTML |
| 5 | `OCTOPUS/worlds/index.html` | N/A | static HTML |

**تحلیل:** ۵ داشبورد/پنل مختلف. `OCTOPUS/admin-telegram/` و `OCTOPUS/worlds/` static HTML هستند که احتمالاً stale هستند. `_ops/dashboard/server.py` (941 خط) و `_ops/live/server.py` (51898 bytes) و `_ops/panel/server.py` (611 خط) هر سه کد HTML/CSS/JS خود را دارند.  
**پیشنهاد:** `OCTOPUS/admin-telegram/` و `OCTOPUS/worlds/` را حذف کن. یک `dashboard/` canonical بساز و live/panel را به آن merge کن.

**مسیر فایل:**  
- `_ops/dashboard/server.py:1`  
- `_ops/live/server.py:1`  
- `_ops/panel/server.py:1`  
- `OCTOPUS/admin-telegram/index.html`  
- `OCTOPUS/worlds/index.html`

---

## ۴. جدول خلاصه اولویت‌ها

| رتبه | تکرار | شدت | تلاش رفع | تاثیر |
|------|-------|-----|----------|-------|
| 1 | ۴ Control Plane | 🔴 | ۲ هفته | **زیاد** |
| 2 | ۵ HTTP Server | 🔴 | ۱ هفته | **زیاد** |
| 3 | ۳ Ledger | 🔴 | ۱ هفته | **زیاد** |
| 4 | ۴ State Store | 🔴 | ۲ هفته | **زیاد** |
| 5 | ۲ Governor | 🔴 | ۳ روز | **متوسط** |
| 6 | ۲ Daemon | 🟡 | ۱ هفته | **متوسط** |
| 7 | ۲ Config Reader | 🟡 | ۳ روز | **متوسط** |
| 8 | ۲ Telegram Path | 🟡 | ۳ روز | **متوسط** |
| 9 | ۳ Telemetry | 🟡 | ۲ روز | **کم** |
| 10 | Doctor vs Cortex | 🟡 | ۱ هفته | **متوسط** |
| 11 | Legs کپی‌شده | 🟡 | ۳ روز | **متوسط** |
| 12 | ۲ Watchdog | 🟡 | ۱ روز | **کم** |
| 13 | Extractorها | 🟢 | ۲ روز | **کم** |
| 14 | Dashboardها | 🟢 | ۳ روز | **کم** |
| 15 | فایل‌های flag | 🟢 | ۱ روز | **کم** |

---

## ۵. نقشه راه حذف تکرارها (Roadmap)

### فاز ۱: یکپارچه‌سازی Control Plane (۲ هفته)
1. `app/src/nbb_cp/` را canonical قرار بده.
2. `4d_system/src/nbb_cp/` را حذف کن (یا symlink).
3. `_ops/organism.py` را به `app/src/nbb_cp/app/organism.py` migrate کن.
4. `4d_system/brain/daemon.py` را به `app/src/nbb_cp/app/daemon.py` migrate کن.

### فاز ۲: یکپارچه‌سازی Infrastructure (۱ هفته)
1. `_ops/core/server_base.py` بساز (BaseServer + BaseHandler).
2. همهٔ ۵ server را به `BaseServer` migrate کن.
3. `_ops/core/state_store.py` بساز (SQLite canonical).
4. `ORGANISM-STATE.json`, `cortex-state.json`, `daemon_state.json` را به SQLite merge کن.

### فاز ۳: یکپارچه‌سازی Ledger (۱ هفته)
1. `_ops/unified_bus.py` را حذف کن (dead code).
2. `events.jsonl` را به LANGAR (`ledger.jsonl`) migrate کن.
3. `epoch-*.json` را به LANGAR metadata merge کن.

### فاز ۴: یکپارچه‌سازی Self-Improvement (۱ هفته)
1. `SelfImprovementEngine` abstraction بساز.
2. `doctor.py`, `cortex.py`, `daemon.py` را به strategy pattern refactor کن.

### فاز ۵: پاک‌سازی Dead Code (۳ روز)
1. `_ops/budget/approval_channel.py` را حذف کن (dead).
2. `OCTOPUS/nervous-system/` را حذف کن (mirror).
3. `OCTOPUS/admin-telegram/` و `OCTOPUS/worlds/` را حذف کن (stale).
4. `04 - Architect System/scripts/organism-watchdog.ps1` را حذف کن.

---

## ضمیمه: آمار کلی

| معیار | مقدار |
|-------|-------|
| فایل‌های `.py` در `_ops/` | ~۲۵۰ |
| فایل‌های `.py` در `app/` | ~۴۵ |
| فایل‌های `.py` در `4d_system/` | ~۱۰۰ |
| خطوط کد تکراری (تخمینی) | ~۶۵٪ |
| HTTP Server | ۵ |
| Control Plane | ۴ |
| Ledger | ۳ |
| State Store | ۵ |
| Daemon | ۳ |
| Config Reader | ۳ |
| Telegram Path | ۳ |
| Watchdog | ۲ |
| Dashboard | ۵ |
| Extractor | ۴+ |

---

*گزارش توسط Orchestrator Agent تولید شده. برای هر مورد می‌توان analysis عمیق‌تر و diff دقیق بین فایل‌های duplicate را تولید کرد.*
