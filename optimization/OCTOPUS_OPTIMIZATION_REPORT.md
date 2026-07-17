# گزارش نهایی بهینه‌سازی هوشمند سیستم Octopus

**تاریخ:** ۲۰۲۶-۰۷-۱۶  
**مسیر:** `F:/backup/`  
**روش:** تحلیل موازی ۶ حوزه توسط ۶ عامل اکتشاف‌گر + سنتز یکپارچه توسط Orchestrator  
**زبان:** فارسی (نام‌فایل‌ها و مسیرها به انگلیسی)

---

## ۱. خلاصه اجرایی

سیستم Octopus در مسیر `F:/backup` دچار **پدیده‌ای به نام «تکثیر ارگانیک معماری»** (Architecture Organic Multiplication) است. این پدیده زمانی رخ می‌دهد که یک سیستم در طول زمان از طریق «توسعه افزایشی» (Additive Development) رشد کند، بدون اینکه کدهای قدیمی حذف یا بازآرایی شوند. نتیجه: یک «ارگانیسم» با **چند مغز، چند قلب، چند سیستم گردش خون، و چند سیستم عصبی** است که همگی به صورت موازی کار می‌کنند ولی با هم هماهنگ نیستند.

### ۱.۱. شش سطح هدررفت اصلی

| رتبه | هدررفت | تعداد | شدت | هدررفت انرژی/داده |
|------|---------|-------|-----|-------------------|
| ۱ | **Control Plane های چندگانه** | ۳-۴ مغز | 🔴 | ~۱۹,۵۰۰ خط کد تکراری؛ تصمیم‌گیری موازی |
| ۲ | **سرورهای HTTP پراکنده** | ۵-۷ سرور | 🔴 | ۵ پورت، ۵ پروسه، ۵× RAM/CPU |
| ۳ | **Ledger/Lajer شکسته** | ۳-۶ فرمت | 🔴 | سه‌بار نوشتن، سه‌بار پارس، audit غیرممکن |
| ۴ | **State Store تکثیر یافته** | ۵-۷ فایل/DB | 🔴 | ۵ نقطه truth، ۵ مسیر backup، sync ناممکن |
| ۵ | **Config/Env پاشیده** | ۳+ خواننده، ۵+ .env | 🟡 | `.env` ۳ بار لود، نام کلید API ناسازگار |
| ۶ | **استخراج‌کننده‌ها انفجاری** | ۱۸-۲۶ اسکریپت | 🟡 | ۱۵-۴۵ ثانیه I/O تکراری، هیچ cache ندارند |

**تخمین کل هدررفت:**
- **کد:** ~۶۵٪ از کدها (تقریباً ۱۷,۰۰۰ از ~۲۶,۰۰۰ خط) تکراری، dead code، یا کپی‌شده هستند.
- **CPU/RAM:** ۵ پروسه پایتون پس‌زمینه = حداقل ۵۰۰MB RAM ثابت + ۵× context-switch.
- **Disk I/O:** هر ۵ دقیقه ORGANISM-STATE.json کامل rewrite می‌شود + ۵ ledger جداگانه append.
- **انرژی انسانی:** هر تغییر در لایه‌ای (مثلاً API key) باید در ۳-۵ فایل تکرار شود.

---

## ۲. طبقه‌بندی هدررفت‌ها — با شواهد دقیق

### ۲.۱. 🔴 Control Plane Proliferation — سه مغز موازی

سیستم Octopus ۳ تا «مغز حاکمیتی» کامل دارد که هر کدام **حلقهٔ while True + time.sleep()** خودشان را دارند، state خودشان را می‌نویسند، ledger خودشان را دارند، budget gate خودشان را دارند، و هیچ‌کدام از هم خبر ندارند.

| مغز | مسیر | حلقه | پورت | state | ledger | وضعیت |
|-----|------|------|------|-------|--------|-------|
| ارگانیسم | `_ops/organism.py:263` | `while True` (300s) | ۸۷۷۱ | `ORGANISM-STATE.json` | `events.jsonl` | **زنده** |
| NBB-CP | `app/src/nbb_cp/app/service.py:54` | `run_demo_epoch()` | FastAPI | In-memory | `LedgerEvent` | **ساخت‌یافته ولی بی‌اتصال** |
| ۴D Daemon | `4d_system/brain/daemon.py:118` | `while not _STOP` (30s) | headless | `daemon_state.json` | `emit()` | **زنده** |
| NBB-CP کپی | `4d_system/src/nbb_cp/app/service.py:1` | — | — | — | — | **بایت‌به‌بایت کپی از app/** |

**شواهد:**
- `app/src/nbb_cp/app/service.py` (۵۸۲ خط) و `4d_system/src/nbb_cp/app/service.py` (۵۹۶ خط) **تقریباً بایت‌به‌بایت یکسان** هستند. diff = فقط ۱۴ خط (`trip_breaker_if_safe` در ۴D). (_ops_report.md:1.1)
- `app/MANIFEST.yaml:95` صراحتاً می‌گوید: «could become the central brain... **not yet wired**». (app_vs_ops_report.md:CP-1)
- `4d_system/MANIFEST.yaml:110` صراحتاً می‌گوید: «INDEPENDENT — 4D is a standalone research experiment». (app_vs_ops_report.md:CP-1)
- هر ۳ مغز telemetry خودشان را می‌نویسند (`telemetry-latest.json`, `epoch-*.json`, `daemon_state.json`). هیچ reconcile بینشان نیست.

**هدررفت:** ~۱۹,۵۰۰ خط کد برای کار یکسان (proposal → gate → ledger → effect). هر باگ در یکی باید در بقیه هم fix شود. این هدررفت عظیم‌ترین و خطرناک‌ترین تکرار سیستم است.

**پیشنهاد:**
> **یکی از دو مغز را انتخاب کن:** یا `app/` (NBB-CP) را canonical بگذار (چون تست‌شده‌تر، ۱۲ invariant، FastAPI، typed) و `_ops/organism.py` را به یک thin wrapper/adaptor تبدیل کن؛ یا برعکس. **هرگز هر دو را هم‌زمان نگه ندار.**

---

### ۲.۲. 🔴 Server Sprawl — پنج سرور HTTP کپی‌شده

۵ سرور HTTP در `_ops/` وجود دارد که هر کدام از `ThreadingHTTPServer + BaseHTTPRequestHandler` استفاده می‌کنند و الگوی `SO_EXCLUSIVEADDRUSE` را کپی کرده‌اند. هیچ reverse proxy یا unified gateway ندارند.

| سرور | مسیر | پورت | خطوط کد | تکرار |
|------|------|------|---------|-------|
| ارگانیسم | `_ops/organism.py:57` | ۸۷۷۱ | ۶۳۲ | Base (با HTTP داخلی) |
| داشبورد | `_ops/dashboard/server.py:49` | ۸۷۷۰ | ۹۴۱ | کپی کامل HTTP boilerplate |
| اتاق زنده | `_ops/live/server.py:32` | ۸۷۷۳ | ~۵۰۰ | کپی کامل HTTP boilerplate |
| پنل مدیریت | `_ops/panel/server.py:30` | ۸۷۹۰ | ۶۱۱ | کپی کامل HTTP boilerplate |
| کورتکس | `_ops/cortex/cortex.py:335` | ۸۷۷۲ | — | کپی کامل HTTP boilerplate |

**کد تکراری (boilerplate):**
```python
# در organism.py:73-82، panel/server.py:513-521، cortex.py:335-341
class _ExclusiveHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = False
    def server_bind(self):
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()
```
(_ops_report.md:1.2, dashboards_extractors_report.md:1.4)

**هدررفت:** ۵ پورت اشغال، ۵ پروسه پایتون، ۵ حلقه event، ۵ کد HTML/CSS/JS تکراری. هر تغییر امنیتی (مثلاً CORS، auth) باید ۵ بار تکرار شود.

**پیشنهاد:**
> یک `_ops/core/http_framework.py` بساز با `BaseServer` و `BaseHandler`. همه ۵ سرور را به یک FastAPI یا یک `http.server` واحد با routeهای `/dashboard`، `/live`، `/panel`، `/api/organism`، `/cortex` merge کن. **فقط یک پورت بماند.**

---

### ۲.۳. 🔴 Ledger/Lajer Fragmentation — شش لجر با سه فرمت

حداقل ۶ پیاده‌سازی ledger/events با ۳ فرمت متفاوت وجود دارد که هیچ‌کدام با هم sync نیستند.

| لجر | مسیر | فرمت | نویسنده | وضعیت |
|-----|------|------|---------|-------|
| genome-system | `07 - Knowledge/genome-system/ledger/ledger.jsonl` | LANGAR (hash-chain) | `opslib.genome_ledger()` | **Source of Truth** |
| ops events | `_ops/state/events.jsonl` | JSONL (schema v2) | `_ops/events.py:30` | زنده |
| unified_bus | `_ops/unified_bus.py:79` | LANGAR + JSONL | `UnifiedBus` (dead) | **dead code** |
| NBB-CP | `app/src/nbb_cp/kernel/events.py` | dataclass `LedgerEvent` | `ControlPlaneService` | سایه |
| ۴D brain | `4d_system/brain/events.py` | تابع `emit()` | daemon | زنده |
| ۴D knowledge | `4d_system/knowledge/ledger.py` | JSON | brain | زنده |
| gate log | `_ops/budget/organ-gate-log.jsonl` | JSONL | organ_gate | زنده |

**شواهد:**
- `_ops/unified_bus.py` (lines 35-148) ادعا می‌کند «یک نویسنده، دو نما» ولی در عمل **هیچ‌کس از `UnifiedBus` استفاده نمی‌کند.** `organism.py` مستقیم `opslib.ledger_note()` صدا می‌زند. (_ops_report.md:1.3)
- `events.jsonl` توسط **دو نویسنده** مستقل نوشته می‌شود: `events.py` (مستقیم) و `unified_bus.py` (از طریق `publish()`). risk of race condition. (cross_system_report.md:1.1)
- `telemetry.py` فقط ۲ منبع (genome + brain) را reconcile می‌کند و app/4d_system را نمی‌بیند. (app_vs_ops_report.md:CP-3)

**هدررفت:** سه‌بار نوشتن، سه‌بار پارس، سه مسیر audit، divergence داده، replay ناممکن. ۲ نویسنده بدون coordination = risk of torn write.

**پیشنهاد:**
> `genome-system/ledger/ledger.jsonl` (LANGAR) را به عنوان **تنها source of truth** انتخاب کن. همه emitها از `_ops/unified_bus.py` (بعد از repair) عبور کنند. `events.jsonl` را به LANGAR migrate کن. `unified_bus.py` را بازنویسی کن (نه حذف — چون اسمش خوب است). NBB-CP و 4D را ملزم به read/write از LANGAR کن.

---

### ۲.۴. 🔴 State Store Multiplication — هفت فایل state/DB

State در حداقل ۷ فایل/پایگاه‌داده در ۵ مسیر متفاوت ذخیره می‌شود. هیچ sync یا reconstruction path واحد ندارد.

| state | مسیر | فرمت | نویسنده | اندازه |
|-------|------|------|---------|--------|
| ORGANISM-STATE | `_ops/state/ORGANISM-STATE.json` | JSON | organism.py | ۲۲۴ بایت |
| chrono | `_ops/state/chrono.db` | SQLite | chrono.py | ۲.۲ MB |
| telemetry | `_ops/state/telemetry-latest.json` | JSON | telemetry.py | — |
| cortex | `_ops/state/cortex/cortex-state.json` | JSON | cortex.py | — |
| budget | `_ops/budget/budget-state.json` | JSON | budget_gate.py | — |
| daemon | `4d_system/outputs/daemon_state.json` | JSON | daemon.py | — |
| experiments | `4d_system/outputs/4d_experiments.db` | SQLite | daemon | — |
| NBB | `app/outputs/nbb.db` | SQLite | NBB-CP | — |
| core | `_launchpad/second-brain-live/control-brain/core.db` | SQLite | launchpad | — |

**شواهد:**
- `ORGANISM-STATE.json` هر ۵ دقیقه (هر tick) **کامل rewrite** می‌شود. این disk thrashing است. (_ops_report.md:1.4)
- `chrono.db` (SQLite ۲.۲MB) به تنهایی یک بستر زمان/ضربان دارد؛ چرا ORGANISM-STATE.json هم heartbeat دارد؟ (app_vs_ops_report.md:CP-4)
- هیچ Foreign Key یا replication بین این DBها وجود ندارد. (cross_system_report.md:2.1)

**هدررفت:** ۵ نقطه truth، ۵ فرمت backup، ۵ راه بازیابی. ORGANISM-STATE.json rewrite کامل = disk thrashing.

**پیشنهاد:**
> `chrono.db` را به عنوان **canonical runtime state store** انتخاب کن. `ORGANISM-STATE.json` را به یک **materialized view** (read-only projection) تبدیل کن که فقط وقتی UI درخواست می‌دهد ساخته شود. همه stateهای دیگر را به SQLite migrate کن (جدول‌های جداگانه در یک DB).

---

### ۲.۵. 🟡 Config/Env Drift — پاشیدگی کانفیگ

#### ۲.۵.۱. سه خواننده .env

| خواننده | مسیر | روش | کلیدهای تکراری |
|---------|------|-----|----------------|
| env_loader | `_ops/budget/env_loader.py:23` | parser دستی | GLM, FUGU, DEEPSEEK, TELEGRAM |
| settings (4D) | `4d_system/config/settings.py:14` | `dotenv.load_dotenv()` | GLM, FUGU |
| config (NBB) | `app/src/nbb_cp/app/config.py` | `os.environ.get()` | — |
| opslib | `_ops/budget/opslib.py:32` | `os.environ.get()` | — |

**شواهد:**
- `.env` حداقل **۳ بار** load می‌شود. `env_loader._LOADED = True` از دوباره‌خوانی جلوگیری می‌کند، ولی هر کدام instance جداگانه دارند. (4d_system_report.md:1.8)
- `organism.py:151` و `cortex.py:398` و `center.py:603` هر سه `env_loader.load_env()` را فراخوانی می‌کنند. (config_env_report.md:2.8)

#### ۲.۵.۲. نام کلید API ناسازگار

| سرویس | نام در _ops | نام در gateway | نام در 4D | نام در launchpad |
|-------|-------------|----------------|-----------|-----------------|
| Sakana/Fugu | `FUGU_API_KEY` | `SAKANA_API_KEY` | `FUGU_API_KEY` | `SAKANA_API_KEY` |
| Zhipu/GLM | `GLM_API_KEY` | `ZAI_API_KEY` | `GLM_API_KEY` | `DEEPSEEK_API_KEY` |
| Telegram | `TELEGRAM_BOT_TOKEN` | — | — | `TELEGRAM_TOKEN` |

**شواهد:**
- `_ops/debate/client.py:175-176` یک alias دارد: `env_key: "SAKANA_API_KEY"` و `env_key_alias: "FUGU_API_KEY"`. (app_vs_ops_report.md:ST-2)
- `4d_system/llm/fugu_client.py:72` فقط `FUGU_API_KEY` را می‌خواند. اگر کاربر `SAKANA_API_KEY` را در `.env` بگذارد، ۴D آن را نمی‌بیند و fail می‌کند. (app_vs_ops_report.md:ST-2)

**هدررفت:** تغییر یک API key = ۳-۵ فایل باید update شوند. risk of mismatch. startup ۳ بار parse .env.

**پیشنهاد:**
> یک `_ops/core/config.py` بساز که همه از آن import کنند. فقط یک بار `.env` را لود کن (در `__main__` یا `opslib`). alias map بساز: `SAKANA_API_KEY` → `FUGU_API_KEY` (هر دو معتبر). فقط یک نام canonical نگه دار.

---

### ۲.۶. 🟡 Telegram Bot Multiplication — شش بات تلگرام

| مسیر | نقش | توکن | وضعیت |
|------|-----|------|-------|
| `_ops/telegram_center/center.py` | کانال مرکزی (topics, digest, commands) | `TELEGRAM_BOT_TOKEN` | زنده |
| `_ops/budget/approval_channel.py` | کانال تأیید انسانی (HITL) | — | **dead code / stub** |
| `_ops/wiring.py` | wire_telegram | `TELEGRAM_BOT_TOKEN` | زنده |
| `4d_system/brain/telegram_bot.py` | بات ۴D | — | زنده |
| `4d_system/brain/notify.py` | notify digest | — | زنده |
| `_launchpad/second-brain-live/control-brain/` | legacy telegram | `TELEGRAM_TOKEN` | — |
| `_launchpad/second-brain-live/*/telegram_bot.py` | project bots | متغیر | — |

**شواهد:**
- `approval_channel.py` (۸۸۱ خط) یک interface abstract است که **هیچ‌کس implement نکرده** (_ops_report.md:2.3)
- دو handler جداگانه برای `/lead` وجود دارد: یکی در `approval_channel.py` و یکی در `panel/server.py` (از طریق `LeadLeg`). (dashboards_extractors_report.md:1.3)
- دو library متفاوت: `requests` (raw) در `_ops/` vs `python-telegram-bot` در `launchpad/`. (config_env_report.md:6.3)

**هدررفت:** ۳-۶ اتصال به Telegram API = ۳-۶× rate-limit risk. ۲ handler برای یک دستور.

**پیشنهاد:**
> `telegram_center/center.py` را canonical بگذار. `approval_channel.py` را حذف کن (dead code). `4d_system/brain/telegram_bot.py` و `notify.py` را به `telegram_center` merge کن. launchpad bots را به یک shared Telegram client تبدیل کن.

---

### ۲.۷. 🟡 LLM Router Duplication — سه مسیر routing

| Router | مسیر | Providerها | Budget Tracking |
|--------|------|------------|---------------|
| cortex | `_ops/cortex/model_router.py` | ollama + GLM + Fugu + DeepSeek | organ_gate + paid_gate |
| ۴D | `4d_system/llm/router.py` | GLM + Fugu + Ollama | 1000 calls/day cap |
| gateway | `survival-gateway/` (LiteLLM) | Anthropic + OpenAI + Gemini + DeepSeek + ZAI + Sakana | spend logs |

**شواهد:**
- `4d_system/llm/` کلید API را مستقیماً از `.env` می‌خواند و از `survival-gateway/` عبور نمی‌کند. (dashboards_extractors_report.md:3.1)
- `telemetry.py` فقط genome و brain را track می‌کند — survival-gateway و 4D router را نمی‌بیند. (app_vs_ops_report.md:ST-3)
- ۸ کلید API مختلف برای ۳ مسیر جداگانه. (config_env_report.md:6.4)

**هدررفت:** ۳ مسیر budget tracking = budget leak احتمالی. ۸ کلید API = ۸× risk of leakage. 4D از gateway عبور نمی‌کند = inconsistent.

**پیشنهاد:**
> `survival-gateway/` (LiteLLM) را به عنوان **canonical LLM router** انتخاب کن. همه درخواست‌ها (cortex، 4D، debate) از gateway عبور کنند. Gateway spend logs = single source of truth for budget. `model_router.py` و `4d_system/llm/router.py` را به thin wrappers تبدیل کن که فقط به gateway proxy می‌کنند.

---

### ۲.۸. 🟡 Extractor Explosion — انفجار استخراج‌کننده‌ها

۱۹-۲۶ اسکریپت `extract_*.py` در `nervous-system/` وجود دارد که هر کدام:
- یک فایل منبع را می‌خوانند
- پردازش می‌کنند
- یک فایل `.js` تولید می‌کنند
- هیچ shared base class یا cache ندارند

| extractor | مسیر | منبع | خروجی | زمان |
|-----------|------|------|-------|------|
| extract_live_data.py | `nervous-system/` | `4d_system/outputs/` | `live-data.js` | ~1s |
| extract_ops_data.py | `nervous-system/` | `_ops/state/` | `ops-data.js` | ~1s |
| extract_graph.py | `nervous-system/` | کل vault | `graph-data.js` | ~3-5s |
| extract_git_status_data.py | `nervous-system/` | کل `.git/` | `git-data.js` | ~5-15s |
| ... | ... | ... | ... | ... |
| **۱۸+ مورد** | | | | **~۱۵-۴۵s کل** |

**شواهد:**
- `refresh-live-data.bat` (۲۴۳ خط) همه را در یک pipeline اجرا می‌کند. (config_env_report.md:5.4)
- دو نسخه `refresh-live-data.bat` وجود دارد: `nervous-system/` (کامل) و `OCTOPUS/nervous-system/` (۹ خط، ناقص). drift risk. (app_vs_ops_report.md:MI-4)
- دو دایرکتوری `nervous-system/` وجود دارد: یکی در root و یکی در `OCTOPUS/`. نسخه OCTOPUS احتمالاً stale است. (dashboards_extractors_report.md:4.5)
- `task-data.js` (~650KB) و `graph-data.js` (~108KB) حاصل اسکن هزاران فایل هستند. (app_vs_ops_report.md:ST-6)

**هدررفت:** ۱۵-۴۵ ثانیه I/O تکراری در هر refresh. هیچ incremental update. کل vault هر بار از نو اسکن می‌شود.

**پیشنهاد:**
> یک `extractor.py` واحد با `Extractor` base class بساز (`read()`, `transform()`, `write()`). Shared cache با mtime/TTL بگذار (SQLite یا JSON). Incremental update: فقط فایل‌هایی که تغییر کرده‌اند را دوباره بخوان. `OCTOPUS/nervous-system/` را حذف کن (mirror stale).

---

### ۲.۹. 🟡 Dashboard Multiplication — هشت داشبورد

| داشبورد | مسیر | پورت | تکنولوژی | وضعیت |
|---------|------|------|----------|-------|
| داشبورد اصلی | `_ops/dashboard/server.py` | ۸۷۷۰ | Python HTTP + inline CSS | زنده |
| اتاق زنده | `_ops/live/server.py` | ۸۷۷۳ | Python HTTP + inline CSS | زنده |
| پنل مدیریت | `_ops/panel/server.py` | ۸۷۹۰ | Python HTTP + inline CSS | زنده |
| admin-telegram | `OCTOPUS/admin-telegram/index.html` | — | Static HTML | احتمالاً stale |
| worlds | `OCTOPUS/worlds/index.html` | — | Static HTML (۱۱ صفحه) | احتمالاً stale |
| mobile | `OCTOPUS/mobile/index.html` | — | Static HTML | احتمالاً stale |
| ۴D UI | `4d_system/ui/app.py` | — | Streamlit (۹ تب) | زنده |
| ۴D tab_dashboard | `4d_system/ui/tab_dashboard.py` | — | Streamlit tab | زنده |

**شواهد:**
- `OCTOPUS/worlds/` شامل ۱۱ صفحه است (cockpit, ontology, money, twin, galaxy, time, compass, habit, risk, decision). هر کدام HTML جداگانه با CSS و JS inline دارند. (dashboards_extractors_report.md:4.2)
- `_ops/dashboard/server.py` و `_ops/live/server.py` هر دو `ORGANISM-STATE.json` را می‌خوانند و رندر می‌کنند. (dashboards_extractors_report.md:4.2)
- هیچ component/UI library مشترک وجود ندارد. (config_env_report.md:5.2)

**هدررفت:** ۸ داشبورد = ۸× کد HTML/CSS/JS. هر تغییر UI باید ۸ بار تکرار شود.

**پیشنهاد:**
> `dashboard/server.py:8770` را canonical بگذار. `/live` و `/panel` را به routeهای جدا تبدیل کن (نه سرور جدا). `OCTOPUS/admin-telegram/` و `OCTOPUS/worlds/` را حذف کن (stale) یا به static export از داشبورد canonical تبدیل کن. ۴D Streamlit UI را به یک route در داشبورد canonical تبدیل کن.

---

### ۲.۱۰. 🟢 Dead Code & Stale Mirrors — کد مرده و آینه‌های کهنه

| فایل/مسیر | نقش | وضعیت | دلیل |
|-----------|-----|-------|------|
| `_ops/unified_bus.py` | پل همگرایی ledger | **dead** | هیچ‌کس از `UnifiedBus` استفاده نمی‌کند |
| `_ops/budget/approval_channel.py` | کانال تأیید | **dead/stub** | هیچ‌کس implement نکرده |
| `OCTOPUS/nervous-system/` | mirror extractors | **stale** | کپی از `nervous-system/` root |
| `OCTOPUS/nervous-system/refresh-live-data.bat` | نسخه کوتاه | **stale** | ۹ خط vs ۲۴۳ خط نسخه اصلی |
| `04 - Architect System/scripts/organism-watchdog.ps1` | watchdog کپی | **duplicate** | کپی از `_ops/organism-watchdog.ps1` |
| `.claude/worktrees/` | worktreeهای قدیمی | **clutter** | ۱۰+ نسخه قدیمی budgets.yaml و _ops/ |

**شواهد:**
- `unified_bus.py` (lines 35-148) ادعا می‌کند «یک نویسنده، دو نما» ولی `organism.py` مستقیم `opslib.ledger_note()` صدا می‌زند. (_ops_report.md:1.3)
- `approval_channel.py` (881 خط) یک interface abstract است که هیچ‌کس implement نکرده. (_ops_report.md:2.3)
- `diff` بین `app/src/nbb_cp/app/service.py` و `4d_system/src/nbb_cp/app/service.py` = فقط ۱۴ خط. (app_vs_ops_report.md:CP-1)

**هدررفت:** ~۱۰۰۰+ خط dead code. ~۵۰MB+ clutter در worktrees. Maintenance burden فقط برای فایل‌هایی که هیچ‌کس استفاده نمی‌کند.

**پیشنهاد:**
> حذف سریع (quick wins): `unified_bus.py` را حذف کن (در صورت نیاز دوباره بساز). `approval_channel.py` را حذف کن. `OCTOPUS/nervous-system/` را حذف کن. `04 - Architect System/scripts/organism-watchdog.ps1` را حذف کن. `.claude/worktrees/` را در `.gitignore` بگذار و پاک کن.

---

## ۳. جدول یکپارچه اولویت‌ها (Impact vs Effort)

این جدول تمام ۲۹ تکرار را در یک نگاه نشان می‌دهد:

| ردیف | تکرار | شدت | تلاش رفع | تأثیر | فاز |
|------|-------|-----|----------|-------|-----|
| ۱ | **ادغام ۳ Control Plane** | 🔴 | ۲ هفته | **بسیار زیاد** | فاز ۲ |
| ۲ | **یکی کردن ۵ سرور HTTP** | 🔴 | ۱ هفته | **بسیار زیاد** | فاز ۱ |
| ۳ | **یکی کردن Ledgerها** | 🔴 | ۱ هفته | **زیاد** | فاز ۲ |
| ۴ | **یکی کردن State Stores** | 🔴 | ۲ هفته | **زیاد** | فاز ۲ |
| ۵ | **حذف کد مرده** | 🔴 | ۱ روز | **متوسط** | فاز ۱ |
| ۶ | **یکی کردن Daemonها** | 🟡 | ۱ هفته | **متوسط** | فاز ۲ |
| ۷ | **Base Class برای Legs** | 🟡 | ۳ روز | **متوسط** | فاز ۲ |
| ۸ | **یکی کردن Telegram** | 🟡 | ۳ روز | **متوسط** | فاز ۲ |
| ۹ | **یکی کردن LLM Router** | 🟡 | ۳ روز | **متوسط** | فاز ۲ |
| ۱۰ | **استخراج‌کننده‌ها (cache)** | 🟡 | ۲-۳ روز | **متوسط** | فاز ۱ |
| ۱۱ | **یکی کردن Config/.env** | 🟡 | ۱ روز | **کم** | فاز ۱ |
| ۱۲ | **یکی کردن Dashboardها** | 🟡 | ۳ روز | **کم** | فاز ۳ |
| ۱۳ | **یکی کردن Watchdogها** | 🟡 | ۱ روز | **کم** | فاز ۱ |
| ۱۴ | **یکی کردن Doctor/Cortex** | 🟡 | ۱ هفته | **متوسط** | فاز ۳ |
| ۱۵ | **merge .env.example** | 🟢 | ۱ ساعت | **کم** | فاز ۱ |
| ۱۶ | **merge README/MANIFEST** | 🟢 | ۱ ساعت | **کم** | فاز ۳ |
| ۱۷ | **پاک کردن worktrees** | 🟢 | ۱ ساعت | **کم** | فاز ۱ |
| ۱۸ | **standard API key names** | 🟢 | ۱ ساعت | **کم** | فاز ۱ |

---

## ۴. نقشه راه ۳ فازه بهینه‌سازی

### فاز ۱: Stabilize (تثبیت) — هفته ۱
**هدف:** حذف هدررفت‌های فوری بدون risk. هیچ کد زنده را نمی‌زنیم، فقط کد مرده و clutter را حذف می‌کنیم.

**روز ۱-۲: حذف کد مرده (Quick Wins)**
1. حذف `_ops/unified_bus.py` (dead code) — **۱ ساعت**
2. حذف `_ops/budget/approval_channel.py` (dead code) — **۱ ساعت**
3. حذف `OCTOPUS/nervous-system/` (stale mirror) — **۱ ساعت**
4. حذف `04 - Architect System/scripts/organism-watchdog.ps1` (duplicate) — **۳۰ دقیقه**
5. حذف `.claude/worktrees/` (clutter) — **۳۰ دقیقه**

**روز ۳-۴: یکی کردن Config**
6. ساخت `_ops/core/config.py` (canonical config reader) — **۱ روز**
7. alias map برای API key names (`SAKANA_API_KEY` ↔ `FUGU_API_KEY`) — **۱ ساعت**
8. merge ۵ `.env.example` به یک `env.example` در root — **۱ ساعت**
9. merge ۱۸+ فایل flag به `state/flags.json` — **۱ روز**

**روز ۵-۷: استخراج‌کننده‌ها**
10. ساخت `extractor.py` با `Extractor` base class — **۱ روز**
11. Shared cache با mtime/TTL — **۱ روز**
12. Incremental update برای vault scan — **۱ روز**

**خروجی فاز ۱:** ~۲۰۰۰ خط کد حذف شده. I/O استخراج‌کننده‌ها ۵۰-۷۰٪ کاهش.

---

### فاز ۲: Consolidate (یکپارچه‌سازی) — هفته ۲-۴
**هدف:** ادغام زیرسیستم‌های موازی به یک canonical. این فاز risk دارد و نیاز به تست دارد.

**هفته ۲: Control Plane و State**
1. انتخاب canonical control plane: **NBB-CP (`app/`)** — چون تست‌شده‌تر (۱۲ invariant، ۲۰۷ test، FastAPI، typed).
2. تبدیل `_ops/organism.py` به thin adapter که از `ControlPlaneService` استفاده می‌کند.
3. حذف `4d_system/src/nbb_cp/` (کپی از app/) — soft-link یا import.
4. merge `4d_system/brain/daemon.py` به `organism.py` (wiring module، نه loop مستقل).
5. `chrono.db` = canonical runtime state. `ORGANISM-STATE.json` = materialized view.

**هفته ۳: Ledger و Server**
6. `genome-system/ledger/ledger.jsonl` (LANGAR) = canonical ledger.
7. `events.jsonl` را به LANGAR migrate کن.
8. `app/src/nbb_cp/kernel/events.py` را به LANGAR adapter تبدیل کن.
9. ساخت `_ops/core/http_framework.py` (BaseServer + BaseHandler).
10. merge ۵ سرور HTTP به یک سرور (۸۷۷۰ canonical) با routeهای `/dashboard`، `/live`، `/panel`، `/api/*`.

**هفته ۴: LLM Router و Telegram**
11. `survival-gateway/` (LiteLLM) = canonical LLM router.
12. `model_router.py` و `4d_system/llm/router.py` را به thin proxy تبدیل کن.
13. `telegram_center/center.py` = canonical Telegram client.
14. merge `4d_system/brain/telegram_bot.py` و `notify.py` به `telegram_center`.
15. `BaseLeg` ABC با `beat()`، `propose()`، `status()` — mining/crypto/accounting از آن ارث‌بری کنند.

**خروجی فاز ۲:** ~۱۰,۰۰۰ خط کد حذف/merge شده. ۱ پورت HTTP، ۱ ledger، ۱ state store، ۱ control plane.

---

### فاز ۳: Optimize (بهینه‌سازی) — ماه ۲
**هدف:** بهینه‌سازی‌های هوشمندانه که بعد از یکپارچه‌سازی ممکن است.

1. **Real-time API به جای batch refresh:** به جای `refresh-live-data.bat` هر ۳۰ دقیقه، یک WebSocket/SSE endpoint بساز که UI را real-time update کند.
2. **Dashboard واحد:** یک React/Vue app واحد بساز که از API canonical می‌خواند. OCTOPUS static HTML را deprecated کن.
3. **Doctor/Cortex merge:** یک `SelfImprovementEngine` abstraction بساز. doctor و cortex به عنوان strategy pattern ثبت شوند.
4. **Database واحد:** همه SQLiteها (chrono.db، core.db، nbb.db، 4d_experiments.db) را به یک SQLite با schema جداگانه ادغام کن. PostgreSQL gateway را حفظ کن (analytics).
5. **README واحد:** یک `README.md` canonical در root. بقیه symlink.

**خروجی فاز ۳:** سیستم «اختاپوس» از یک ارگانیسم با «چند مغز، چند قلب» به یک ارگانیسم با «یک مغز، یک قلب، یک سیستم گردش خون» تبدیل می‌شود.

---

## ۵. آمار یکپارچه (Unified Metrics)

| معیار | قبل | بعد (فاز ۳) | کاهش |
|-------|-----|-------------|------|
| خطوط کد .py | ~۲۶,۰۰۰ | ~۱۵,۰۰۰ | **۴۲٪** |
| سرور HTTP | ۵ | ۱ | **۸۰٪** |
| Control Plane | ۳-۴ | ۱ | **۷۵٪** |
| Ledger | ۶ فرمت | ۱ فرمت (LANGAR) | **۸۳٪** |
| State Store | ۷ فایل/DB | ۱ SQLite + ۱ view | **۸۶٪** |
| Config Reader | ۳+ | ۱ | **۶۷٪** |
| Telegram Path | ۶+ | ۱ | **۸۳٪** |
| LLM Router | ۳ | ۱ (LiteLLM gateway) | **۶۷٪** |
| Extractor | ۱۸-۲۶ | ۱ framework + plugins | **۹۵٪** |
| Dashboard | ۸ | ۱ | **۸۸٪** |
| Watchdog | ۲-۴ | ۱ | **۷۵٪** |
| .env فایل | ۵+ | ۱ | **۸۰٪** |
| فایل flag | ۱۸+ | ۱ JSON | **۹۵٪** |
| پورت اشغال | ۵ | ۱ | **۸۰٪** |
| RAM ثابت (تخمین) | ~۵۰۰MB | ~۱۵۰MB | **۷۰٪** |
| Disk I/O هر ۵ دقیقه | rewrite کامل | incremental update | **~۸۰٪** |
| زمان refresh extractors | ۱۵-۴۵s | ~۵s (cache) | **~۷۰٪** |

---

## ۶. نتیجه‌گیری

سیستم Octopus یک معماری فکری بسیار قدرتمند دارد: یک ارگانیسم مولتی‌ایجنتی با حاکمیت بودجه، انسان در حلقه، و self-improvement. اما این معماری در سطح **پیاده‌سازی** به «تکثیر ارگانیک» دچار شده: به جای یک مغز، سه مغز؛ به جای یک قلب، دو قلب؛ به جای یک سیستم گردش خون، سه سیستم.

این تکثیر نتیجهٔ طبیعی توسعه افزایشی (additive development) است: هر بار که یک «brain» جدید (NBB-CP، 4D) ساخته شده، به جای اینکه روی brain قبلی build شود، از صفر rewrite شده. هر بار یک داشبورد جدید ساخته شده، به جای اینکه به داشبورد قبلی اضافه شود، یک سرور جدید ساخته شده.

**بهینه‌سازی کلیدی یک کلمه است: «یکی» (One).**
- **One Control Plane** — NBB-CP canonical
- **One HTTP Server** — port 8770 canonical
- **One Ledger** — LANGAR
- **One State Store** — chrono.db
- **One Config Reader** — `_ops/core/config.py`
- **One Telegram Client** — `telegram_center`
- **One LLM Router** — `survival-gateway`
- **One Extractor Framework** — with cache
- **One Dashboard** — with routes
- **One Watchdog** — `watchdog.py`

> **هر چیزی که دو تا باشد، هدررفت است.**

---

## ضمائم

### A. لیست ۶ گزارش موازی
1. `_ops_report.md` — تکرارهای داخلی `_ops/`
2. `app_vs_ops_report.md` — مقایسه `app/` و `_ops/`
3. `4d_system_report.md` — تکرارهای `4d_system/`
4. `dashboards_extractors_report.md` — داشبوردها و استخراج‌کننده‌ها
5. `config_env_report.md` — کانفیگ و محیط
6. `cross_system_report.md` — تکرارهای فراسystemی

### B. مسیرهای کلیدی برای شروع فاز ۱
- `F:/backup/_ops/unified_bus.py` → حذف
- `F:/backup/_ops/budget/approval_channel.py` → حذف
- `F:/backup/OCTOPUS/nervous-system/` → حذف
- `F:/backup/4d_system/src/nbb_cp/` → حذف (یا symlink به `app/src/nbb_cp/`)
- `F:/backup/04 - Architect System/scripts/organism-watchdog.ps1` → حذف
- `F:/backup/.claude/worktrees/` → پاک کردن

### C. نکتهٔ مهم دربارهٔ Security
در طول بهینه‌سازی، **هیچ فایل `.env` را حذف نکن.** فقط `.env`های اضافی (مثلاً `4d_system/.env` اگر duplicate باشد) را بررسی کن. اگر `4d_system/.env` کلیدهای متفاوتی دارد، آن‌ها را به `.env` root منتقل کن و سپس `4d_system/.env` را حذف کن. **هرگز secretها را نابود نکن.**

---

*این گزارش توسط Orchestrator Agent با تحلیل موازی ۶ حوزه تولید شده است.*  
*زمان تولید: ۲۰۲۶-۰۷-۱۶*  
*مسیر: `F:/backup/optimization/OCTOPUS_OPTIMIZATION_REPORT.md`*
