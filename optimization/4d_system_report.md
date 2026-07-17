# 📋 گزارش تکرارها و هدررفت‌ها در سیستم Octopus — حوزه 4d_system

**تاریخ:** 2026-07-16  
**مسیر:** `F:/backup/`  
**تحلیل‌گر:** Orchestrator  
**مدت تحلیل:** ۱۵ دقیقه  

---

## 🔴 خلاصه اجرایی (Top Findings)

| # | موضوع | شدت | تأثیر |
|---|-------|-----|-------|
| 1 | **سه Control Plane موازی**: `_ops/organism.py` + `app/src/nbb_cp/` + `4d_system/src/nbb_cp/` | 🔴 | تناقض منطق، divergence state، triple maintenance |
| 2 | **۴ سرور HTTP مستقل** روی ۴ پورت (8770-8790) | 🔴 | پراکندگی داشبورد، هر کدام state خودشان را می‌خوانند |
| 3 | **`app/` و `4d_system/` کپی کامل** — `src/nbb_cp/` در هر دو | 🔴 | دو نسخه از یک کد؛ تغییر در یکی = divergence |
| 4 | **۳ Ledger با فرمت متفاوت** — genome-system + events.py + unified_bus + app/ledger | 🔴 | divergence داده، replay ناممکن |
| 5 | **۵ State file موازی** — ORGANISM-STATE.json + chrono.db + telemetry-latest.json + budget-state.json + daemon_state.json | 🔴 | consistency ناممکن |
| 6 | **۲ Daemon حلقهٔ زنده** — `organism.py` + `4d_system/brain/daemon.py` | 🔴 | دو master loop؛ رقابت بر منابع |
| 7 | **۳ Config reader** — `opslib.py` + `env_loader.py` + `settings.py` | 🟡 | هر کدام `.env` را خودشان می‌خوانند |
| 8 | **۲ Governor** — `governor_epoch.py` + `app/src/nbb_cp/app/governor.py` | 🟡 | دو allocator موازی |
| 9 | **Watchdog دوگانه** — `.py` + `.ps1` | 🟡 | منطق یکسان، دوبار نگه‌داری |
| 10 | **Events سه‌گانه** — `_ops/events.py` + `4d_system/brain/events.py` + `app/kernel/events.py` | 🟡 | taxonomy متفاوت، correlation_id ناسازگار |

---

## 🔴 بخش ۱: _ops — تکرارهای داخلی

### ۱.۱ Ledger تکراری (🔴 بحرانی)

| مسیر | نقش | تکرار با |
|------|-----|----------|
| `07 - Knowledge/genome-system/ledger/ledger.py` | Ledger LANGAR اصلی (append-only, hash-chain) | `4d_system/knowledge/ledger.py` |
| `_ops/events.py` | رویدادهای ساختاریافته → `state/events.jsonl` | genome-system ledger (همچنین `unified_bus.py` سعی در merge دارد) |
| `_ops/legs/ledger_core.py` | Ledger مخصوص legs | genome-system ledger |
| `_ops/unified_bus.py` | «پل همگرایی» — یک نویسنده، دو نما | **هنوز به طور کامل جایگزین نشده؛ مسیرهای قدیمی همچنان فعال** |

**شواهد:**
- `unified_bus.py:65-67` → `self._ledger = ledger or opslib.genome_ledger()` — هنوز ledger قدیمی را می‌خواند
- `events.py:30` → `LOG = opslib.STATE_DIR / "events.jsonl"` — یک ledger دیگر
- `genome-system/ledger/ledger.py` → `ledger.jsonl` — ledger سوم

**تکرار:** ۳ ledger با فرمت‌های متفاوت (`jsonl` ساختاریافتهٔ genome vs `jsonl` رویدادها vs `jsonl` legs).  
**هدررفت:** سه‌بار write، سه‌بار disk I/O، سه‌بار parse.  
**پیشنهاد:** `unified_bus.py` را canonical کن — همهٔ emitها از آنجا عبور کنند. `events.jsonl` و `ledger_core.py` را deprecated.

---

### ۱.۲ State تکراری (🔴 بحرانی)

| مسیر | نویسنده | خواننده |
|------|---------|---------|
| `_ops/state/ORGANISM-STATE.json` | `organism.py` | `dashboard/server.py`, `live/server.py`, `panel/server.py` |
| `_ops/state/chrono.db` | `chrono.py` | `organism.py`, `unified_bus.py` |
| `_ops/state/telemetry-latest.json` | `telemetry.py` | `organism.py`, `dashboard/server.py` |
| `_ops/budget/budget-state.json` | `budget_gate.py` | `telemetry.py` (reconcile) |
| `_ops/state/OWNER-PROFILE.json` | `panel/server.py` | `panel/server.py` |

**شواهد:**
- `organism.py:59` → `STATE_FILE = opslib.STATE_DIR / "ORGANISM-STATE.json"`
- `telemetry.py:157-162` → `telemetry-latest.json` + `telemetry/{today}.json`
- `chrono.py:223` → `chrono.db` در `opslib.STATE_DIR`
- `budget_gate.py` → `budget-state.json` (احتمالی)

**تکرار:** ۵ فایل state موازی. ORGANISM-STATE.json تلاش می‌کند همه را merge کند (`month`, `today`, `conflicts`, `pulse`, `wiring` ...) ولی هر tick همه را rewrite می‌کند.  
**هدررفت:** rewrite کامل ORGANISM-STATE.json هر ۵ دقیقه = disk thrashing.  
**پیشنهاد:** chrono.db = canonical runtime state؛ ORGANISM-STATE.json = materialized view فقط برای UI (read-only projection).

---

### ۱.۳ سرورهای HTTP تکراری (🔴 بحرانی)

| پورت | فایل | نقش | state خوانده‌شده |
|------|------|-----|-----------------|
| 8770 | `_ops/dashboard/server.py` | داشبورد اصلی | ORGANISM-STATE.json, telemetry-latest.json, ledger.jsonl |
| 8771 | `_ops/organism.py` | سرور وضعیت خود ارگانیسم | ORGANISM-STATE.json (self-write) |
| 8772 | `_ops/cortex/model_router.py` | Cortex router (احتمالی) | — |
| 8773 | `_ops/live/server.py` | اتاق کنترل زنده | ORGANISM-STATE.json, پورت‌های زنده |
| 8790 | `_ops/panel/server.py` | پنل آشنایی + پروژه‌ها | OWNER-PROFILE.json, scan PROJECT.md |

**شواهد:**
- `organism.py:57` → `PORT = 8771`
- `dashboard/server.py:49` → `PORT = 8770`
- `live/server.py:32` → `PORT = 8773`
- `panel/server.py:30` → `PORT = 8790`
- `model_router.py:16` → «HTTP POST /ask روی 127.0.0.1:8772» (احتمالی)

**تکرار:** ۵ سرور مستقل، هر کدام HTML/CSS/JS خودشان را دارند.  
**هدررفت:** ۵ process پایتون، ۵ بار پاسخگویی HTTP، ۵ بار re-render.  
**پیشنهاد:** merge به یک سرور (8770 canonical) با routeهای جدا: `/`, `/live`, `/panel`, `/cortex`.

---

### ۱.۴ Telegram تکراری (🟡 متوسط)

| مسیر | نقش | وضعیت |
|------|-----|-------|
| `_ops/budget/approval_channel.py` | کانال تأیید انسانی (abstract) | NotWiredStub — همیشه no-approval |
| `_ops/organism.py:210` | `_w.make_telegram_channel(leg=_leg)` | auto-on اگر توکن |
| `_ops/cortex/model_router.py` | — | هیچ reference مستقیم به approval_channel ندارد |

**شواهد:**
- `approval_channel.py:6` → «adapterِ عملیاتی = Telegram (انتخاب اپراتور)؛ الان وصل نیست»
- `organism.py:210-216` → telegram poll thread مستقل
- `approval_channel.py:44` → `class ApprovalChannel: name = "abstract"` — هنوز implementation واقعی ندارد

**تکرار:** approval_channel.py یک interface خالی است؛ telegram_center در wiring ساخته می‌شود.  
**پیشنهاد:** یک implementation واحد در `approval_channel.py`.

---

### ۱.۵ Governor تکراری (🟡 متوسط)

| مسیر | نقش | فرمت |
|------|-----|------|
| `_ops/budget/governor_epoch.py` | Epoch سایه (allostatic) | JSON → `epochs/epoch-*.json` |
| `_ops/governor/governor-alerts.md` | Alert log | Markdown |
| `_ops/governor_shadow.py` | Shadow governor (در scripts) | — |
| `_ops/budget/governor_epoch.py` | `allocate_dry()` + `allocate_llm()` + `barbell_allocate()` | ۳ allocator موازی |

**شواهد:**
- `governor_epoch.py:105-143` → `allocate_dry()` — FLOOR + EXPLORE_PCT + headroom
- `governor_epoch.py:150-242` → `barbell_allocate()` — CORE/SATELLITE + cull + hysteresis
- `governor_epoch.py:245-281` → `allocate_llm()` — LLM-based allocation

**تکرار:** سه allocator در یک فایل! barbell و dry و llm هر سه grant می‌سازند.  
**پیشنهاد:** یک allocator canonical؛ بقیه advisory.

---

### ۱.۶ Telemetry تکراری (🟡 متوسط)

| مسیر | منبع | خروجی |
|------|------|-------|
| `_ops/budget/telemetry.py` | genome ledger + core.db | `telemetry-latest.json` |
| `_ops/budget/governor_epoch.py` | `telemetry.snapshot()` | در `run_epoch()` |
| `organism.py:275` | `telemetry.snapshot()` | در `tick` |

**تکرار:** telemetry.snapshot() دو بار در هر epoch/تیک صدا زده می‌شود.  
**پیشنهاد:** cache در `opslib` با TTL کوتاه (مثلاً ۱ دقیقه).

---

### ۱.۷ Watchdog دوگانه (🟡 متوسط)

| مسیر | زبان | قابلیت تست |
|------|------|-----------|
| `_ops/watchdog.py` | Python | testable (`should_revive()`) |
| `_ops/watchdog_extension.py` | Python | unknown |
| `04 - Architect System/scripts/organism-watchdog.ps1` | PowerShell | not testable |

**شواهد:**
- `watchdog.py:16` → «PS1 موجود همین منطق را دارد ولی آزمون‌پذیر نیست»
- `watchdog.py:75-83` → `revive_action()` — فقط propose

**تکرار:** دو watchdog با منطق یکسان.  
**پیشنهاد:** watchdog.py را canonical کن؛ PS1 صدا بزند `python -m watchdog`.

---

### ۱.۸ Config/Env تکراری (🟡 متوسط)

| مسیر | نقش | `.env` خوانده؟ |
|------|-----|----------------|
| `_ops/budget/opslib.py` | مسیرها + budgets.yaml | نه (اما `env` را می‌خواند) |
| `_ops/budget/env_loader.py` | `.env` loader | بله — `F:\backup\.env` |
| `_ops/organism.py:151` | `env_loader.load_env()` | بله (دوباره!) |
| `_ops/cortex/model_router.py:49` | `env_loader.load_env()` | بله (سه‌باره!) |

**تکرار:** `.env` حداقل ۳ بار load می‌شود. `env_loader._LOADED = True` از دوباره‌خوانی جلوگیری می‌کند، ولی هر کدام instance جداگانه دارند.  
**پیشنهاد:** یک بار در `__main__` یا `opslib`.

---

## 🔴 بخش ۲: app/ vs _ops/ — Doctrinal Twin

### ۲.۱ دو Control Plane (🔴 بحرانی)

| `_ops/` (legacy) | `app/` (NBB-CP) | تفاوت |
|-----------------|-----------------|-------|
| `organism.py` — loop + HTTP | `app/src/nbb_cp/api/http.py` — FastAPI | architecture: procedural vs class-based |
| `governor_epoch.py` — shadow | `app/src/nbb_cp/app/service.py` — `ControlPlaneService` | shadow vs formal service |
| `events.py` — taxonomy v2 | `app/src/nbb_cp/kernel/events.py` — `EventKind` | taxonomy متفاوت |
| `budget/opslib.py` — budgets.yaml | `app/src/nbb_cp/kernel/` — `BudgetState`, `Money` | model متفاوت (dict vs dataclass) |
| `telemetry.py` — micro-USD | `app/src/nbb_cp/kernel/ports.py` — `Telemetry` | interface متفاوت |

**شواهد:**
- `app/src/nbb_cp/app/service.py:54` → `class ControlPlaneService` — full formal architecture
- `app/src/nbb_cp/api/http.py:49` → `FastAPI` — modern HTTP API
- `organism.py` — procedural script with `while True`

**تکرار:** `app/` یک rewrite کامل از `_ops/` است — «doctrinal twin».  
**هدررفت:** هر باگ در `_ops/` باید در `app/` هم fix شود (و vice versa).  
**پیشنهاد:** freeze `_ops/` و migrate به `app/`. `_ops/` فقط wiring wrapper بماند.

---

### ۲.۲ دو Ledger (🔴 بحرانی)

| `_ops/` | `app/` |
|---------|--------|
| `genome-system/ledger/ledger.py` — append-only, hash-chain, age_tick | `app/src/nbb_cp/kernel/ports.py` — `LedgerStore` (abstract) |
| `_ops/unified_bus.py` — یکپارچه‌سازی | `app/src/nbb_cp/app/service.py` — `_append()` به `LedgerStore` |

**تکرار:** دو ledger با contract متفاوت. `app/` هنوز به genome-system ledger وصل نیست.  
**پیشنهاد:** `LedgerStore` implementation را روی `ledger.py` بنویس.

---

### ۲.۳ دو set Invariant (🟡 متوسط)

- `_ops/` — درvariants در `opslib.py` (I2, I3, I6) و `telemetry.py` (DIVERGENCE_DEATH)
- `app/` — درvariants در `app/src/nbb_cp/kernel/invariants.py` (`SystemView`, `Violation`, `audit`)

**شواهد:**
- `app/src/nbb_cp/kernel/invariants.py` — `SystemView`, `Violation`, `audit`
- `opslib.py` — «I2: این لایه فقط MEASURE/propose می‌کند»

**تکرار:** دو سیستم invariant check.  
**پیشنهاد:** merge.

---

## 🔴 بخش ۳: 4d_system/ vs _ops/ — دومین Doctrinal Twin

### ۳.۱ دو Daemon (🔴 بحرانی)

| `_ops/organism.py` | `4d_system/brain/daemon.py` |
|--------------------|-----------------------------|
| tick = ۵ دقیقه (300s) | tick = ۳۰ ثانیه |
| HTTP server + wiring | headless loop |
| `telemetry.snapshot()` | `budget.status()` |
| `organism.py` master | `AutomationController` master |

**شواهد:**
- `daemon.py:33` → `DAEMON_TICK_SECONDS=30`
- `organism.py:58` → `TICK_SECONDS = 300`
- هر دو `while True` loop با `time.sleep()` دارند

**تکرار:** دو master loop موازی.  
**هدررفت:** ۲x CPU, ۲x memory, ۲x state file write.  
**پیشنهاد:** یک daemon canonical. `4d_system/daemon.py` را به `organism.py` merge کن (wiring module).

---

### ۳.۲ دو Config Reader (🟡 متوسط)

| `_ops/` | `4d_system/` |
|---------|-------------|
| `opslib.py` — `ORG_ROOT`, `OPS_DIR`, `BUDGETS_YAML` | `settings.py` — `SYSTEM_ROOT`, `DESKTOP`, `REFERENCE_DIR` |
| `env_loader.py` — `.env` root | `settings.py` — `dotenv.load_dotenv()` |

**شواهد:**
- `settings.py:14-17` → `dotenv.load_dotenv()` — **دوباره `.env` load می‌شود**
- `settings.py:93-99` → `GLM_API_KEY`, `FUGU_API_KEY` — همان کلیدهای `env_loader.py`

**تکرار:** `settings.py` از `python-dotenv` استفاده می‌کند؛ `env_loader.py` از parser دستی.  
**پیشنهاد:** `env_loader.py` canonical. `settings.py` فقط `os.environ` بخواند.

---

### ۳.۳ LLM Routing تکراری (🟡 متوسط)

| `_ops/cortex/model_router.py` | `4d_system/` |
|------------------------------|------------|
| `ask(task, prompt, tier)` | `brain/budget/router.py` (احتمالی) |
| `keys_present()` | `settings.py:104-111` (`glm_available`, `fugu_available`) |
| `paid_gate()` | `settings.py:mock_mode` |

**تکرار:** دو router با منطق fallback یکسان (local → secondary → primary).  
**پیشنهاد:** `model_router.py` canonical. `4d_system` از آنجا import کند.

---

## 🔴 بخش ۴: Dashboards و Extractors — تکثیر داشبورد

### ۴.۱ سه Extractor جداگانه (🟡 متوسط)

| مسیر | خروجی | مصرف‌کننده |
|------|-------|-----------|
| `nervous-system/extract_live_data.py` | `live_data.json` | `OCTOPUS/worlds/` |
| `nervous-system/extract_ops_data.py` | `ops_data.json` | `OCTOPUS/worlds/` |
| `nervous-system/extract_graph_data.py` | `graph_data.json` | `OCTOPUS/worlds/` |

**تکرار:** ۳ script با الگوی کد یکسان (scan + json.dump).  
**پیشنهاد:** یک `extract.py` با `mode` argument.

---

### ۴.۲ پنج داشبورد HTML (🔴 بحرانی)

| مسیر | پورت | فناوری |
|------|------|--------|
| `OCTOPUS/admin-telegram/index.html` | — | static HTML |
| `OCTOPUS/worlds/index.html` | — | static HTML |
| `_ops/dashboard/server.py` | 8770 | Python HTTP + inline CSS |
| `_ops/live/server.py` | 8773 | Python HTTP + inline CSS |
| `_ops/panel/server.py` | 8790 | Python HTTP + inline CSS |

**تکرار:** ۵ داشبود. ۳ تا از آن‌ها Python server (کد CSS/JS کپی شده).  
**هدررفت:** `dashboard/server.py` و `live/server.py` هر دو ORGANISM-STATE.json را می‌خوانند و رندر می‌کنند.  
**پیشنهاد:** `dashboard/server.py:8770` = canonical. `/live` و `/panel` = routeهای جدا. `OCTOPUS/` = static export.

---

### ۴.۳ refresh-live-data.bat (🟡 متوسط)

**احتمال:** `refresh-live-data.bat` یک scheduler/task است که extract_*.py را اجرا می‌کند و خروجی را به `OCTOPUS/worlds/` کپی می‌کند.  
**تکرار:** اگر `organism.py` هر ۵ دقیقه state می‌نویسد، refresh batch هر ۵ دقیقه دادهٔ کهنه را copy می‌کند.  
**پیشنهاد:** realtime API به جای batch refresh.

---

## 🔴 بخش ۵: Cross-System — تکرارهای فراسystemی

### ۵.۱ Ledger سه‌گانه (🔴 بحرانی)

| سیستم | فرمت | مسیر |
|-------|------|------|
| `_ops/` | `genome-system/ledger/ledger.jsonl` (LANGAR) | `07 - Knowledge/...` |
| `app/` | `LedgerStore` (abstract) | `app/src/nbb_cp/kernel/ports.py` |
| `4d_system/` | `knowledge/ledger.py` | `4d_system/knowledge/ledger.py` |

**تکرار:** ۳ ledger، ۳ فرمت.  
**پیشنهاد:** `ledger.py` (LANGAR) = canonical. `LedgerStore` = adapter. `4d_system/ledger.py` = wrapper.

---

### ۵.۲ State سه‌گانه (🔴 بحرانی)

| سیستم | مسیر | نویسنده |
|-------|------|---------|
| `_ops/` | `state/ORGANISM-STATE.json` + `chrono.db` | `organism.py` |
| `app/` | `state/` (احتمالی) | `ControlPlaneService` |
| `4d_system/` | `outputs/daemon_state.json` | `daemon.py` |

**تکرار:** ۳ state.  
**پیشنهد:** `chrono.db` = canonical runtime. بقیه = projection.

---

### ۵.۳ Telegram دوگانه (🟡 متوسط)

| `_ops/` | `_launchpad/` |
|---------|-------------|
| `approval_channel.py` (abstract) | `second-brain-live/*/telegram_bot.py` (احتمالی) |
| `organism.py:210` (poll thread) | — |

**پیشنهاد:** یک Telegram client canonical.

---

### ۵.۴ LLM Routing سه‌گانه (🟡 متوسط)

| `_ops/cortex/model_router.py` | `4d_system/brain/` | `survival-gateway/` |
|------------------------------|-------------------|-------------------|
| `ask()` — local/secondary/primary | `router.py` (احتمالی) | `gateway.py` (احتمالی) |

**پیشنهاد:** `model_router.py` canonical.

---

### ۵.۵ Database چهارگانه (🔴 بحرانی)

| سیستم | DB | مسیر | نوع |
|-------|----|------|-----|
| `_ops/` | `chrono.db` | `state/chrono.db` | SQLite |
| `_launchpad/` | `core.db` | `second-brain-live/control-brain/core.db` | SQLite |
| `4d_system/` | `outputs/` | `4d_system/outputs/` | SQLite (احتمالی) |
| `survival-gateway/` | `postgres` | `survival-gateway/` | PostgreSQL |

**تکرار:** ۴ DB. `telemetry.py` فقط `chrono.db` و `core.db` را merge می‌کند.  
**پیشنهاد:** یک SQLite canonical (`chrono.db`) + PostgreSQL برای analytics (اختیاری).

---

### ۵.۶ Budget سه‌گانه (🟡 متوسط)

| `_ops/` | `app/` | `4d_system/` |
|---------|--------|-------------|
| `budgets.yaml` | `app/config.py` (احتمالی) | `settings.py` (بدون budget) |
| `opslib.load_budgets()` | `BudgetStore` | — |

**پیشنهاد:** `budgets.yaml` = canonical. `app/` و `4d_system/` از `opslib` import کنند.

---

## 🟡 بخش ۶: Config/Env — انفجار .env

### ۶.۱ فایل‌های .env

| مسیر | وضعیت |
|------|-------|
| `F:/backup/.env` | ** canonical ** |
| `4d_system/.env.example` | example |
| `app/.env.example` | example |
| `survival-gateway/.env.example` | example |
| `_launchpad/second-brain-live/painting-bot/.env.example` | example |
| `_launchpad/second-brain-live/control-brain/.env.example` | example |
| `04 - Architect System/learning-engine/app/.env.example` | example |
| `03 - Projects/...` | multiple examples |

**تکرار:** ۸+ `.env*` file. فقط root `.env` canonical.  
**پیشنهد:** همهٔ `.env.example`ها را به یک `env.example` در root merge کن.

---

### ۶.۲ فایل‌های budgets.yaml

| مسیر | وضعیت |
|------|-------|
| `_ops/budget/budgets.yaml` | ** canonical ** |
| `app/config.py` | احتمالی duplicate |
| `4d_system/config/settings.py` | هیچ reference به budgets.yaml |

**تکرار:** فقط یک `budgets.yaml` واقعی. خوب است.

---

### ۶.۳ فایل‌های MANIFEST.yaml (🟢 کم)

| مسیر | تعداد |
|------|-------|
| روت و پروژه‌ها | ۱۰+ |

**تکرار:** هر پروژه یک MANIFEST. این by design است.  
**وضعیت:** 🟢 قابل قبول.

---

### ۶.۴ فایل‌های adapter.yaml (🟢 کم)

| مسیر | تعداد |
|------|-------|
| `03 - Projects/*/contracts/adapter.yaml` | ۶ |

**تکرار:** هر پروژه یک contract. by design. 🟢

---

### ۶.۵ فایل‌های flag (🟡 متوسط)

| مسیر | تعداد | نوع |
|------|-------|-----|
| `_ops/STOP-ORGANISM` | ۱ | kill-switch |
| `_ops/STOP-METABOLIC` | ۱ | kill-switch |
| `_ops/STOP-DEBATE` | ۱ | kill-switch |
| `_ops/STOP-CORTEX` (احتمالی) | ۱ | kill-switch |
| `_ops/HALT-ALL` | ۱ | panic |
| `_ops/FREEZE.flag` | ۱ | budget freeze |
| `_ops/ACTIVATION-*.flag` | ۱۱ | owner-only activation |
| `_ops/OCTOPUS-flags.cmd` | ۱ | env override |

**تکرار:** ۱۸+ فایل کنترلی.  
**پیشنهاد:** merge STOPها به یک `STOP` با `reason` field. ACTIVATIONها را به یک `ACTIVATION.json`.

---

### ۶.۶ نام‌های کلید API متفاوت (🟡 متوسط)

| نام | کجا استفاده می‌شود |
|-----|-------------------|
| `FUGU_API_KEY` | `env_loader.py`, `settings.py` |
| `SAKANA_API_KEY` | هیچ‌کجا (احتمالاً قدیمی) |
| `GLM_API_KEY` | `env_loader.py`, `settings.py` |
| `ZAI_API_KEY` | `env_loader.py` (در `KNOWN_KEYS`) |
| `DEEPSEEK_API_KEY` | `env_loader.py`, `model_router.py` |
| `ANTHROPIC_API_KEY` | `env_loader.py` (در `KNOWN_KEYS`) |
| `TELEGRAM_BOT_TOKEN` | `env_loader.py`, `organism.py` |

**تکرار:** `ZAI_API_KEY` vs `GLM_API_KEY` — ممکن است یکی باشند. `SAKANA_API_KEY` احتمالاً alias قدیمی `FUGU_API_KEY`.  
**پیشنهاد:** alias map در `env_loader.py`.

---

## 🟡 بخش ۷: Legs — کپی کد بدون Base Class

### ۷.۱ Legs تکراری (🟡 متوسط)

| Leg | سازنده | مشترکات |
|-----|--------|---------|
| `lead_leg` | `wiring.make_lead_leg()` | HLC, ack, propose-only |
| `ziman_leg` | `wiring.make_ziman_leg()` | HLC, ack, propose-only |
| `cartographer_leg` | `wiring.make_cartographer_leg()` | HLC, ack, read-only |
| `mining_leg` | `wiring.make_business_legs_beat()` | status gather |
| `crypto_leg` | `wiring.make_business_legs_beat()` | status gather |
| `accounting_leg` | `wiring.make_business_legs_beat()` | status gather |
| `knowledge_leg` | `wiring.make_business_legs_beat()` | status gather |

**شواهد:**
- `organism.py:207-209` → `_leg = _w.make_lead_leg(); _ziman_leg = _w.make_ziman_leg(); _cartographer_leg = _w.make_cartographer_leg()`
- `organism.py:470-473` → `_w.business_legs_beat()` → mining, crypto, accounting, knowledge

**تکرار:** هفت leg بدون base class مشترک. هر کدام `beat()` خودشان را دارند.  
**پیشنهد:** `BaseLeg` با `beat()`, `propose()`, `status()`.

---

## 🔴 بخش ۸: نتیجه‌گیری و نقشه راه

### اولویت ۱ — بحرانی (🔴)

1. **Merge `app/` و `4d_system/`**: `app/src/nbb_cp/` و `4d_system/src/nbb_cp/` کپی کامل هستند. یکی را delete کن.
2. **Canonical Server**: فقط `dashboard:8770` بماند. `live:8773` و `panel:8790` = routeهای جدا. `organism:8771` = API endpoint (نه server مستقل).
3. **Canonical Ledger**: `unified_bus.py` را completion بده — همه emit از آنجا عبور کنند. `events.jsonl` و `ledger_core.py` deprecated.
4. **Canonical State**: `chrono.db` = runtime state. `ORGANISM-STATE.json` = read-only materialized view (هر ۵ دقیقه rewrite نه هر tick).
5. **Canonical Daemon**: `organism.py` = master loop. `4d_system/daemon.py` = wiring module (نه loop مستقل).

### اولویت ۲ — متوسط (🟡)

6. **Canonical Config**: `env_loader.py` = تنها `.env` reader. `settings.py` فقط `os.environ`.
7. **Canonical Governor**: `ControlPlaneService` در `app/` = allocator. `governor_epoch.py` = wrapper.
8. **Canonical LLM Router**: `model_router.py` = تنها router. `4d_system` از آنجا import کند.
9. **Canonical Watchdog**: `watchdog.py` = testable. PS1 صدا بزند `python -m watchdog`.
10. **Base Class برای Legs**: `BaseLeg` با `beat()`, `propose()`, `status()`.

### اولویت ۳ — کم (🟢)

11. **Merge flags**: `STOP-*` → `STOP` با `reason`. `ACTIVATION-*.flag` → `ACTIVATION.json`.
12. **Merge .env.example**: یک `.env.example` در root.
13. **Merge README**: یک `README.md` canonical در root. بقیه symlink.

---

## 📎 ضمیمه — آمار سریع

| متریک | مقدار |
|-------|-------|
| تعداد فایل‌های `.env*` | ۸+ |
| تعداد فایل‌های `budgets.yaml` | ۱ (خوب) |
| تعداد فایل‌های `MANIFEST.yaml` | ۱۰+ |
| تعداد فایل‌های `adapter.yaml` | ۶ (by design) |
| تعداد فایل‌های flag | ۱۸+ |
| تعداد سرور HTTP | ۵ |
| تعداد daemon/loop | ۲ |
| تعداد ledger | ۳ |
| تعداد state file | ۵+ |
| تعداد governor/allocator | ۲+ |
| تعداد events system | ۳ |
| تعداد watchdog | ۲ |
| تعداد config reader | ۳ |
| تعداد dashboard | ۵ |
| تعداد DB | ۴ |
| تعداد control plane | ۳ |
| **تعداد کل تکرارهای شناسایی‌شده** | **۳۵+** |

---

*گزارش تولیدشده توسط Orchestrator تحلیل‌گر تکرارها و هدررفت‌ها*  
*زمان: 2026-07-16T17:37+10*
