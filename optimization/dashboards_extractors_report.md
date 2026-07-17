# گزارش تحلیل تکرارها و هدررفت‌های سیستم Octopus
## حوزه: dashboards_extractors — تاریخ: 2026-07-16 17:37 AUSEST

---

## خلاصه اجرایی (Executive Summary)

سیستم Octopus در مسیر `F:/backup/` دچار **تکرارهای معماری گسترده‌ای** است که از رشد موازی و تجمع کدهای آزمایشی در چند مسیر جداگانه (`_ops/`, `app/`, `4d_system/`, `OCTOPUS/`, `nervous-system/`) نشأت گرفته‌اند. شدیدترین تکرارها در لایه‌های **کنترل پلن (Control Plane) دوگانه**، **داشبوردهای موازی**، **لجرها و ایونت‌های تکراری**، و **گیت‌واها و کنفیگ‌های موازی** مشاهده می‌شوند.

| رتبه | شاخص | تعداد | شدت |
|------|------|-------|-----|
| 1 | سرورهای HTTP مستقل | 4 پورت | 🔴 |
| 2 | کنترل پلن‌های موازی | 2 پایگاه کد (app/ + 4d_system/) | 🔴 |
| 3 | لجر و ایونت تکراری | 5+ مسیر | 🔴 |
| 4 | داشبوردهای HTML/JS | 5+ داشبورد | 🔴 |
| 5 | تلگرام ربات‌های تکراری | 10+ فایل | 🟡 |
| 6 | watchgog‌ها | 2 فایل | 🟡 |
| 7 | legs تکراری | کپی کد بدون base class | 🟡 |
| 8 | دکتر vs کورتکس | همپوشانی تحلیل/تصمیم | 🟡 |
| 9 | فایل‌های .env | 10+ فایل | 🟡 |
| 10 | فایل‌های budgets.yaml | 24+ فایل | 🟢 |

---

## ۱. حوزه `_ops/` — تکرارهای داخلی

### ۱.۱ 🔴 فایل‌های ledger تکراری (5+ مسیر)

| مسیر | فرمت | نقش | خط |
|------|------|-----|------|
| `_ops/events.py` | ایونت‌های پایتونی | ledger ایونت درون‌حافظه‌ای | خط 1-100 |
| `_ops/budget/epochs/epoch-*.json` | JSON | epoch تخصیص بودجه | خط — |
| `07 - Knowledge/genome-system/ledger/ledger.jsonl` | JSONL | ledger ژنوم (METRIC) | خط 1 |
| `_ops/budget/ledger_core.py` | پایتون | ledger پایه | خط 1 |
| `4d_system/brain/events.py` | پایتون | ایونت‌های مغز | خط 1 |
| `4d_system/src/nbb_cp/kernel/events.py` | پایتون | ایونت‌های NBB-CP | خط 1 |

**تحلیل:** ۶ مسیر جداگانه ledger/ایونت نگه می‌دارند که هر کدام فرمت متفاوتی دارند. `_ops/events.py` ایونت‌های درون‌حافظه‌ای را مدیریت می‌کند در حالی که `genome-system/ledger/ledger.jsonl` رکوردهای append-only دارد. `ledger_core.py` و `events.py` در `4d_system/` و `app/` هم فرمت‌های دیگری دارند.

**اثر:** هیچ single-source-of-truth برای ایونت‌ها وجود ندارد. reconciliation telemetry ↔ billed در `telemetry.py` خط 166-199 فقط ۲ منبع (genome + brain) را چک می‌کند و بقیه را نمی‌بیند.

### ۱.۲ 🔴 فایل‌های state تکراری (4+ مسیر)

| مسیر | فرمت | نقش | خط |
|------|------|-----|------|
| `_ops/state/ORGANISM-STATE.json` | JSON | state ارگانیسم | `organism.py:59` |
| `_ops/state/cortex/cortex-state.json` | JSON | state کورتکس | `cortex.py:35` |
| `_ops/budget/budget-state.json` | JSON | state بودجه | `opslib.py` |
| `_ops/budget/organ-state.json` | JSON | state ارگان | `opslib.py` |
| `_ops/state/chrono.db` | SQLite | db زمانی | `organism.py:346` |
| `_launchpad/second-brain-live/panels/state.db` | SQLite | state پنل | — |

**تحلیل:** ۶ state store موازی وجود دارد. `ORGANISM-STATE.json` توسط `organism.py` نوشته می‌شود، `cortex-state.json` توسط `cortex.py`، `budget-state.json` و `organ-state.json` توسط `opslib.py`، و `chrono.db` یک SQLite جداگانه است. هیچ reconciliation بین این stateها وجود ندارد.

### ۱.۳ 🟡 مسیرهای تلگرام تکراری (2 مسیر)

| مسیر | نقش | خط |
|------|-----|------|
| `_ops/telegram_center/` (در `wiring.py`) | چنل تلگرام اصلی | `organism.py:210` |
| `_ops/budget/approval_channel.py` | کانال تأیید تلگرام | خط 764, 2772 |

**تحلیل:** `approval_channel.py` یک TelegramApprovalChannel کامل با 3000+ خط است که در مسیر `_ops/budget/` قرار دارد. `wiring.py` (که از `organism.py` import می‌شود) یک `make_telegram_channel` دیگر می‌سازد. این دو سیستم جداگانه هستند که هر دو روی توکن `TELEGRAM_BOT_TOKEN` کار می‌کنند.

**اثر:** دو handler جداگانه برای `/lead` وجود دارد — یکی در `approval_channel.py` و یکی در `panel/server.py` (از طریق `LeadLeg`).

### ۱.۴ 🔴 سرورهای HTTP تکراری (4 سرور، 4 پورت)

| سرور | پورت | مسیر | خط |
|------|------|------|------|
| organism.py | 8771 | `_ops/organism.py` | خط 57, 158 |
| dashboard | 8770 | `_ops/dashboard/server.py` | خط 49 |
| live | 8773 | `_ops/live/server.py` | خط 32 |
| panel | 8790 | `_ops/panel/server.py` | خط 30 |
| cortex | 8772 | `_ops/cortex/cortex.py` | خط 33 |

**تحلیل:** ۵ سرور HTTP مستقل وجود دارد که هر کدام `BaseHTTPRequestHandler` و `ThreadingHTTPServer` خودشان را دارند. الگوی کد یکسان است (allow_reuse_address=False, SO_EXCLUSIVEADDRUSE, threading.Thread daemon). هیچ shared framework یا base class ندارند.

**اثر:** هر سرور ~100-200 خط کد boilerplate تکراری دارد. اگر تغییر امنیتی (مثلاً CORS یا authentication) نیاز باشد، باید ۵ جا تکرار شود.

**کد تکراری:**
```python
class _ExclusiveHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = False
    def server_bind(self):
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()
```
این الگو در `organism.py:73-82`، `dashboard/server.py` (ندارد ولی باید داشته باشد)، `panel/server.py:513-521`، و `cortex.py:335-341` تکرار می‌شود.

### ۱.۵ 🟡 کد کپی‌شده بین legs (بدون base class مؤثر)

| پا | مسیر | خط |
|------|------|------|
| LeadLeg | `_ops/legs/lead_leg.py` | 143 خط |
| ZimanLeg | `_ops/legs/ziman_leg.py` | 549 خط |
| MiningLeg | `_ops/legs/mining_leg.py` | 63 خط |
| CryptoLeg | `_ops/legs/crypto_leg.py` | 144 خط |
| AccountingLeg | `_ops/legs/accounting_leg.py` | 80 خط |
| KnowledgeLeg | `_ops/legs/knowledge_leg.py` | — |
| CartographerLeg | `_ops/legs/cartographer_leg.py` | — |

**تحلیل:** `leg.py` یک `Leg` base class دارد (خط 99) که `LeadLeg` و `ZimanLeg` از آن ارث‌بری می‌کنند. اما `mining_leg.py`، `crypto_leg.py`، و `accounting_leg.py` **ارث‌بری نمی‌کنند** — بلکه فقط توابع سطح ماژول (`mining_status()`, `crypto_status()`, `accounting_status()`) هستند. هیچ base class مشترک برای همهٔ پاها وجود ندارد.

**اثر:** هر پای جدید باید از صفر نوشته شود. الگوی کد مشابه (`age_days`, `fresh()`, `live=True/False`) در ۳ فایل تکرار می‌شود.

**کد تکراری نمونه:**
```python
# crypto_leg.py:43-47
_NAME_TS = re.compile(r"(\d{4})-(\d{2})-(\d{2})-(\d{2})-(\d{2})-(\d{2})")

def _data_age_days(p: Path | None) -> float | None:
    # این الگو در 3 پا تکرار می‌شود
```

### ۱.۶ 🟡 telemetry تکراری (2 فایل)

| مسیر | نقش | خط |
|------|-----|------|
| `_ops/budget/telemetry.py` | تلمتری اصلی (genome + brain) | 205 خط |
| `octopus_core/telemetry.py` | تلمتری octopus_core | — |
| `_ops/tests/test_telemetry.py` | تست تلمتری | — |

**تحلیل:** `telemetry.py` در `_ops/budget/` از `ledger.jsonl` و `core.db` می‌خواند. `governor_epoch.py` هم از `telemetry.snapshot()` استفاده می‌کند. اما `octopus_core/telemetry.py` یک ماژول جداگانه است که احتمالاً نسخه قدیمی است.

### ۱.۷ 🟡 دکتر vs کورتکس — همپوشانی تحلیل/تصمیم

| ویژگی | دکتر (`_ops/doctor/doctor.py`) | کورتکس (`_ops/cortex/cortex.py`) |
|--------|-------------------------------|-----------------------------------|
| تیک/چرخه | هر N ضربان از Pacemaker | هر 120-600 ثانیه |
| تحلیل | metric mining + bottleneck | sweep + coherence + alignment |
| خروجی | RFC + sandbox test | think + journal + state |
| merge | submit_for_approval (human) | align_work_plan (auto-reorder) |
| فایل state | ندارد (stateless) | `cortex-state.json` + `journal.jsonl` |

**تحلیل:** دکتر و کورتکس هر دو "تحلیلگر" سیستم هستند. دکتر روی bottleneck تمرکز دارد و RFC تولید می‌کند. کورتکس روی coherence و alignment تمرکز دارد. هر دو propose-only هستند. اما دکتر از کورتکس برای "think" استفاده نمی‌کند — یعنی دو تحلیلگر جداگانه دارند که با هم ارتباط ندارند.

### ۱.۸ 🟢 لایه‌های config تکراری (4+ خواننده)

| مسیر | نقش | خط |
|------|-----|------|
| `_ops/budget/opslib.py` | config reader اصلی | — |
| `_ops/budget/env_loader.py` | .env loader | خط 13-26 |
| `_ops/OCTOPUS-flags.cmd` | flag overrides | `dashboard/server.py:275` |
| `budgets.yaml` | بودجه | — |
| `OCTOPUS.env` | env vars | — |

**تحلیل:** `env_loader.py` کلیدهای `FUGU_API_KEY` و `GLM_API_KEY` را می‌خواند. `opslib.py` بودجه را از `budgets.yaml` می‌خواند. `dashboard/server.py` از `OCTOPUS-flags.cmd` می‌خواند. `organism.py` و `cortex.py` هر دو `env_loader.load_env()` را صدا می‌زنند. این یعنی .env حداقل ۳ بار خوانده می‌شود.

### ۱.۹ 🟡 watchdog دوگانه

| مسیر | نقش | خط |
|------|-----|------|
| `_ops/watchdog.py` | watchdog پایتون | خط 35 |
| `_ops/organism-watchdog.ps1` | watchdog پاورشل | — |
| `_ops/watchdog_extension.py` | افزونه watchdog | خط 28 |
| `04 - Architect System/scripts/organism-watchdog.ps1` | watchdog دوم | — |

**تحلیل:** ۴ فایل watchdog وجود دارد. `_ops/watchdog.py` و `_ops/organism-watchdog.ps1` هر دو `ORGANISM_PORT = 8771` را چک می‌کنند. `04 - Architect System/scripts/organism-watchdog.ps1` یک کپی است.

---

## ۲. حوزه `app_vs_ops` — دو control plane

### ۲.۱ 🔴 app/ (NBB-CP) vs _ops/organism.py — دو control plane

| ویژگی | `app/src/nbb_cp/` (NBB-CP) | `_ops/` (ارگانیسم) |
|--------|---------------------------|---------------------|
| زبان | انگلیسی | فارسی |
| پایگاه کد | 47 فایل .py | 477 فایل |
| کنترل پلن | `ControlPlaneService` | `organism.py` + `governor_epoch.py` |
| ledger | `kernel/events.py` | `events.py` + `genome-system/ledger/` |
| budget | `kernel/gates.py` | `budget_gate.py` + `organ_gate.py` |
| fitness | `kernel/fitness.py` | `fitness.py` |
| sigma | `kernel/sigma.py` | `replication.py` |
| invariant | 12 invariant | 10 invariant |

**تحلیل:** دو سیستم کنترل کامل وجود دارند که هر دو "ارگانیسم" را مدیریت می‌کنند. `app/` یک سیستم تمیز با 12 invariant است. `_ops/` یک سیستم تولیدی با 10 invariant است. اما منطق یکسانی دارند: proposal → gate → ledger → effect.

**اثر:** تغییر در یکی باید در دیگری هم تکرار شود. `app/` تست‌شده‌تر است ولی `_ops/` فعال‌تر است.

### ۲.۲ 🔴 دو governor

| مسیر | نقش | خط |
|------|-----|------|
| `app/src/nbb_cp/app/governor.py` | governor NBB-CP | — |
| `4d_system/src/nbb_cp/app/governor.py` | governor 4d_system | — |
| `_ops/budget/governor_epoch.py` | governor ارگانیسم | 379 خط |
| `04 - Architect System/scripts/governor_shadow.py` | governor سایه | — |

**تحلیل:** ۴ فایل governor وجود دارد. `governor_epoch.py` تخصیص بودجه را در shadow mode انجام می‌دهد (dry run). `governor.py` در app/ و 4d_system/ احتمالاً نسخه‌های متفاوتی از یک کد هستند.

### ۲.۳ 🔴 دو API HTTP

| مسیر | پورت | نقش |
|------|------|------|
| `app/src/nbb_cp/api/http.py` | — | API رسمی NBB-CP |
| `_ops/organism.py` | 8771 | API ارگانیسم |
| `_ops/cortex/cortex.py` | 8772 | API کورتکس |

### ۲.۴ 🔴 دو ledger

| مسیر | فرمت | نقش |
|------|------|------|
| `app/src/nbb_cp/kernel/events.py` | dataclass | ایونت‌های NBB-CP |
| `4d_system/src/nbb_cp/kernel/events.py` | dataclass | ایونت‌های 4d_system |
| `_ops/events.py` | dict | ایونت‌های ارگانیسم |
| `07 - Knowledge/genome-system/ledger/ledger.jsonl` | JSONL | ledger ژنوم |

**تحلیل:** `app/src/nbb_cp/kernel/events.py` و `4d_system/src/nbb_cp/kernel/events.py` **تقریباً یکسان** هستند (فقط ۱ تفاوت در `circuit_breaker` در `service.py` که به 4d_system اضافه شده). `diff` نشان داد که `service.py` در 4d_system فقط یک متد `trip_breaker_if_unsafe` اضافه دارد (14 خط).

### ۲.۵ 🟢 README.md دو سیستم

| مسیر | وضعیت |
|------|--------|
| `app/README.md` | — |
| `4d_system/README.md` | — |
| `_ops/ORGANISM-SPEC.md` | — |

**تحلیل:** مستندات هر سیستم جداگانه است. "doctrinal twin" هستند ولی بی‌ارتباط.

---

## ۳. حوزه `4d_system`

### ۳.۱ 🔴 4d_system/llm/ از survival-gateway/ عبور نمی‌کند

| مسیر | کلید API | خط |
|------|----------|------|
| `4d_system/llm/router.py` | `GLM_API_KEY` + `FUGU_API_KEY` | خط 97, 103 |
| `4d_system/llm/langchain_models.py` | `FUGU_API_KEY` | خط 52, 99 |
| `4d_system/llm/fugu_client.py` | `FUGU_API_KEY` | خط 53 |
| `survival-gateway/` | — | — |

**تحلیل:** `4d_system/llm/` کلید API را مستقیماً از `.env` می‌خواند و از `survival-gateway/` عبور نمی‌کند. این یعنی دو مسیر جداگانه برای LLM وجود دارد.

### ۳.۲ 🟡 4d_system/brain/daemon.py vs _ops/organism.py

| ویژگی | `4d_system/brain/daemon.py` | `_ops/organism.py` |
|--------|---------------------------|---------------------|
| حلقه | while True | while True |
| تیک | نامشخص | 300 ثانیه |
| state | `daemon_state.json` | `ORGANISM-STATE.json` |
| budget | `4d_system/config/settings.py` | `budgets.yaml` |

**تحلیل:** دو daemon مستقل با دو state store و دو budget store.

### ۳.۳ 🟡 4d_system/config/settings.py vs _ops/budget/opslib.py

| مسیر | نقش |
|------|------|
| `4d_system/config/settings.py` | config 4d_system (FUGU_TIMEOUT, GLM_API_KEY) |
| `_ops/budget/opslib.py` | config اصلی (budgets, FX rate, organ table) |
| `app/src/nbb_cp/app/config.py` | config NBB-CP |

**تحلیل:** ۳ config reader جداگانه. `_ops/budget/opslib.py` 477+ فایل را مدیریت می‌کند در حالی که `config/settings.py` فقط 4d_system را می‌شناسد.

### ۳.۴ 🔴 extractors موازی

| مسیر | خروجی | منبع داده |
|------|--------|-----------|
| `4d_system/outputs/` | daemon_state.json, decision_packets.jsonl | daemon.py |
| `_ops/state/` | ORGANISM-STATE.json, telemetry-latest.json | organism.py |
| `nervous-system/extract_*.py` | live-data.js, ops-data.js | 4d_system + _ops |

**تحلیل:** `extract_live_data.py` از `4d_system/outputs/` می‌خواند. `extract_ops_data.py` از `_ops/state/` می‌خواند. هر دو `*.js` در `nervous-system/` می‌نویسند. این یعنی دو extractor جداگانه روی دو دیتاست متفاوت کار می‌کنند و خروجی‌های جداگانه تولید می‌کنند.

### ۳.۵ 🟡 4d_system/.env.example vs root .env

| مسیر | محتوا |
|------|--------|
| `F:/backup/.env` | کلیدهای واقعی |
| `F:/backup/4d_system/.env` | کلیدهای 4d_system |
| `F:/backup/4d_system/.env.example` | نمونه |
| `F:/backup/survival-gateway/.env` | کلیدهای gateway |

**تحلیل:** ۳ فایل `.env` فعال وجود دارد. `4d_system/.env` ممکن است کلیدهای قدیمی داشته باشد.

---

## ۴. حوزه `dashboards_extractors` (dedicated)

### ۴.۱ 🔴 ۳+ extractor جداگانه

| مسیر | خروجی | منبع | خط |
|------|--------|------|------|
| `nervous-system/extract_live_data.py` | `live-data.js` | `4d_system/outputs/` | 129 |
| `nervous-system/extract_ops_data.py` | `ops-data.js` | `_ops/state/` | 58 |
| `nervous-system/extract_graph.py` | `graph-data.js` | `07 - Knowledge/` | — |
| `OCTOPUS/nervous-system/extract_live_data.py` | `live-data.js` | `4d_system/outputs/` | — |
| `OCTOPUS/nervous-system/extract_ops_data.py` | `ops-data.js` | `_ops/state/` | — |
| `OCTOPUS/nervous-system/extract_graph.py` | `graph-data.js` | `07 - Knowledge/` | — |

**تحلیل:** ۶ extractor وجود دارد — ۳ در `nervous-system/` و ۳ در `OCTOPUS/nervous-system/`. `diff` نشان داد که نسخه‌های `OCTOPUS/` احتمالاً کپی‌های قدیمی هستند. `extract_live_data.py` از `4d_experiments.db` SQLite می‌خواند و `frontier.json` را پارس می‌کند. `extract_ops_data.py` از `ORGANISM-STATE.json` و `fitness-latest.json` می‌خواند.

**اثر:** اگر `4d_system/outputs/` تغییر کند، `nervous-system/extract_live_data.py` باید به‌روز شود. اگر `OCTOPUS/nervous-system/` نسخه قدیمی باشد، داده‌های stale تولید می‌کند.

### ۴.۲ 🔴 ۵+ داشبورد HTML/JS

| مسیر | پورت | نوع |
|------|------|-----|
| `OCTOPUS/admin-telegram/index.html` | — | داشبورد تلگرام |
| `OCTOPUS/worlds/index.html` | — | داشبورد جهان‌ها (۱۱ صفحه) |
| `OCTOPUS/worlds/01-cockpit/index.html` | — | کابین |
| `_ops/dashboard/server.py` | 8770 | داشبورد زنده |
| `_ops/live/server.py` | 8773 | اتاق کنترل زنده |
| `_ops/panel/server.py` | 8790 | پنل آشنایی |

**تحلیل:** ۳ داشبورد HTML استاتیک در `OCTOPUS/` و ۳ سرور HTTP داینامیک در `_ops/` وجود دارد. `OCTOPUS/worlds/` شامل ۱۱ صفحه است (cockpit, ontology, money, twin, galaxy, time, compass, habit, risk, decision). هر کدام HTML جداگانه با CSS و JS inline دارند.

**اثر:** داده‌های `OCTOPUS/worlds/` از `nervous-system/*.js` تغذیه می‌شوند، اما اگر `refresh-live-data.bat` اجرا نشود، داده‌ها stale می‌مانند.

### ۴.۳ 🟡 refresh-live-data.bat

| مسیر | اجرا | خروجی |
|------|------|--------|
| `nervous-system/refresh-live-data.bat` | دستی | همهٔ `extract_*.py` |
| `OCTOPUS/nervous-system/refresh-live-data.bat` | دستی | همهٔ `extract_*.py` |

**تحلیل:** دو batch file کپی شده. هیچ cron یا scheduler خودکار برای refresh داده‌ها وجود ندارد. داده‌ها فقط وقتی تازه می‌شوند که کاربر دستی اجرا کند.

### ۴.۴ 🟡 داده‌های extract_*.js به Octopus/worlds منتقل می‌شوند یا کپی؟

**تحلیل:** `nervous-system/live-data.js` و `nervous-system/ops-data.js` توسط `extract_*.py` تولید می‌شوند. `OCTOPUS/worlds/index.html` با `<script src="../nervous-system/live-data.js">` از آن‌ها استفاده می‌کند. این یعنی **کپی نیست** — بلکه نسخه‌های جداگانه‌ای در `OCTOPUS/nervous-system/` هم exist دارند که ممکن است stale باشند.

### ۴.۵ 🔴 OCTOPUS/nervous-system/ با F:/backup/nervous-system/ متفاوت است

**تحلیل:** دو دایرکتوری `nervous-system/` وجود دارد — یکی در root و یکی در `OCTOPUS/`. `OCTOPUS/nervous-system/extract_*.py` احتمالاً کپی‌های قدیمی از `nervous-system/extract_*.py` هستند. `diff` نشان داد که هر دو نسخه `extract_live_data.py` و `extract_ops_data.py` در هر دو مسیر وجود دارند.

---

## ۵. حوزه `config_env`

### ۵.۱ 🔴 فایل‌های .env (10+ فایل فعال)

| مسیر | نوع | وضعیت |
|------|-----|--------|
| `F:/backup/.env` | فعال | کلیدهای اصلی |
| `F:/backup/4d_system/.env` | فعال | کلیدهای 4d_system |
| `F:/backup/survival-gateway/.env` | فعال | کلیدهای gateway |
| `F:/backup/_launchpad/second-brain-live/control-brain/.env` | فعال | کلیدهای launchpad |
| `F:/backup/_ops/OCTOPUS.env` | فعال | env ارگانیسم |

**تحلیل:** ۵+ فایل `.env` فعال. هر کدام ممکن است کلیدهای متفاوت یا duplicate داشته باشند. `env_loader.py` فقط `F:/backup/.env` را لود می‌کند.

### ۵.۲ 🟡 فایل‌های budgets.yaml (24+ فایل)

**تحلیل:** ۲۴ فایل `budgets.yaml` وجود دارد که بیشتر آن‌ها در `.claude/worktrees/` هستند (worktreeهای git). فقط `F:/backup/_ops/budget/budgets.yaml` فعال است. بقیه آرشیو یا worktree هستند.

### ۵.۳ 🟢 فایل‌های MANIFEST.yaml / adapter.yaml

| مسیر | تعداد |
|------|--------|
| `MANIFEST.yaml` | 5+ |
| `adapter.yaml` | 3+ |

**تحلیل:** هر پروژه یک MANIFEST.yaml دارد. هیچ استاندارد واحد نیست.

### ۵.۴ 🟡 فایل‌های flag (10+ فایل در `_ops/`)

| مسیر | تعداد |
|------|--------|
| `STOP-ORGANISM` | 1 |
| `STOP-CORTEX` | 1 |
| `ACTIVATION-*.flag` | 9+ |
| `FREEZE.flag` | 1 |
| `GITWRITE-FAILED.flag` | 1+ |

**تحلیل:** ۹ فایل `ACTIVATION-*.flag` وجود دارد که هر کدام یک capability را فعال می‌کنند. این مکانیزم امن است (human-gated) ولی مدیریت آن‌ها دشوار است.

### ۵.۵ 🔴 نام‌های متفاوت برای یک API key

| نام | استفاده‌کننده | خط |
|------|-------------|------|
| `FUGU_API_KEY` | `4d_system/llm/`, `env_loader.py` | — |
| `SAKANA_API_KEY` | `_ops/debate/client.py`, `launchpad/` | `client.py:175` |

**تحلیل:** `_ops/debate/client.py:175-176` یک alias دارد: `env_key: "SAKANA_API_KEY"` و `env_key_alias: "FUGU_API_KEY"`. این یعنی کد سعی می‌کند هر دو نام را بخواند. اما `4d_system/llm/fugu_client.py` فقط `FUGU_API_KEY` را می‌خواند.

**اثر:** اگر کاربر `SAKANA_API_KEY` را در `.env` بگذارد، `4d_system/llm/` آن را نمی‌بیند و fail می‌کند.

### ۵.۶ 🟢 config files در پروژه‌های launchpad

| مسیر | پروژه |
|------|--------|
| `_launchpad/second-brain-live/control-brain/config.py` | second-brain |
| `_launchpad/second-brain-live/painting-bot/config.py` | painting-bot |
| `_launchpad/second-brain-live/ziman-agent/ziman/config.py` | ziman-agent |

**تحلیل:** هر پروژه launchpad config خودش را دارد.

---

## ۶. حوزه `cross_system`

### ۶.۱ 🔴 سه فرمت ledger متفاوت

| سیستم | فرمت | مسیر |
|--------|------|------|
| `_ops/` | dict + JSONL | `events.py` + `genome-system/ledger/` |
| `app/` | dataclass + ledger store | `kernel/events.py` |
| `4d_system/` | dataclass + ledger store | `kernel/events.py` |

**تحلیل:** هیچ interoperability بین ledgerهای `_ops/` و `app/` / `4d_system/` وجود ندارد. `telemetry.py` فقط ۲ منبع (genome + brain) را reconcile می‌کند و app/4d_system را نمی‌بیند.

### ۶.۲ 🔴 سه جای state

| سیستم | مسیر state | فرمت |
|--------|-----------|------|
| `_ops/` | `state/ORGANISM-STATE.json`, `state/cortex/`, `state/pulse/` | JSON |
| `4d_system/` | `outputs/daemon_state.json` | JSON |
| `app/` | درون‌حافظه (MemoryLedgerStore) | Python object |

**تحلیل:** ۳ state store جداگانه. هیچ sync یا reconciliation بین آن‌ها نیست.

### ۶.۳ 🟡 تلگرام در دو مسیر

| مسیر | ربات | خط |
|------|------|------|
| `_ops/budget/approval_channel.py` | TelegramApprovalChannel | 3000+ خط |
| `_launchpad/second-brain-live/control-brain/adapters/telegram_bot.py` | TelegramBot | — |
| `4d_system/brain/telegram_bot.py` | TelegramBot | — |
| `03 - Projects/.../telegram_bot.py` | 10+ نسخه | — |

**تحلیل:** 10+ فایل `telegram_bot.py` در پروژه‌های مختلف. هر کدام handler جداگانه دارند.

### ۶.۴ 🔴 سه مسیر LLM routing

| مسیر | نقش | خط |
|------|-----|------|
| `_ops/cortex/model_router.py` | router اصلی (local/ollama/deepseek) | خط 55 |
| `4d_system/llm/router.py` | router 4d_system (GLM/Fugu) | خط 97 |
| `survival-gateway/` | gateway بیرونی | — |

**تحلیل:** `model_router.py:55` فقط `FUGU_API_KEY` را چک می‌کند. `4d_system/llm/router.py:97` هم `GLM_API_KEY` و هم `FUGU_API_KEY` را می‌خواهد. `survival-gateway/` یک gateway جداگانه است که از `litellm` استفاده می‌کند.

**اثر:** ۳ مسیر جداگانه برای LLM call. هر کدام budget tracking متفاوتی دارند. `telemetry.py` فقط genome و brain را track می‌کند — survival-gateway و 4d_system router را نمی‌بیند.

### ۶.۵ 🔴 چهار database SQLite/Postgres

| مسیر | نوع | نقش |
|------|------|-----|
| `_ops/state/chrono.db` | SQLite | chrono (زمان/ضربان) |
| `4d_system/outputs/4d_experiments.db` | SQLite | experiments 4d_system |
| `survival-gateway/postgres` | Postgres | gateway |
| `_launchpad/second-brain-live/panels/state.db` | SQLite | state پنل |

**تحلیل:** ۴ database جداگانه. هیچ replication یا sync بین آن‌ها نیست.

### ۶.۶ 🔴 سه بار تعریف budget

| مسیر | فرمت | نقش |
|------|------|------|
| `_ops/budget/budgets.yaml` | YAML | بودجه اصلی |
| `app/src/nbb_cp/app/config.py` | dataclass | بودجه NBB-CP |
| `4d_system/config/settings.py` | dataclass | بودجه 4d_system |

**تحلیل:** `budgets.yaml` منبع حقیقت است. `app/config.py` و `4d_system/config/settings.py` مقادیر را hardcode یا از .env می‌خوانند. `NBB_GLOBAL_CAP_CENTS=7000` در `4d_system/tests/l1_adapters/test_config.py:40` وجود دارد که ممکن است با `budgets.yaml` هماهنگ نباشد.

---

## ۷. یافته‌های کلیدی با خط دقیق

### ۷.۱ 🔴 سنگین‌ترین تکرار: ControlPlaneService دوگانه

```
app/src/nbb_cp/app/service.py        582 خط
4d_system/src/nbb_cp/app/service.py  596 خط (فقط 14 خط اضافه: trip_breaker_if_unsafe)
```

**خط دقیق:** `diff` در خط 486-499 `service.py` نشان داد که 4d_system فقط `trip_breaker_if_unsafe` اضافه دارد. بقیه کد **بایت‌به‌بایت یکسان** است.

**اثر:** ۱۱۷۸ خط کد برای یک کنترل پلن تکراری. هر تغییر در app/ باید دستی در 4d_system/ کپی شود.

### ۷.۲ 🔴 سنگین‌ترین تکرار: داشبوردها

```
_ops/dashboard/server.py    941 خط  (پورت 8770)
_ops/live/server.py         ~500 خط (پورت 8773)  
_ops/panel/server.py        611 خط  (پورت 8790)
_ops/organism.py            632 خط  (پورت 8771) — includes HTTP server
```

**خط دقیق:** هر کدام `BaseHTTPRequestHandler` و `ThreadingHTTPServer` خودشان را دارند. الگوی boilerplate در هر ۴ فایل تکرار می‌شود.

### ۷.۳ 🔴 سنگین‌ترین تکرار: Extractors

```
nervous-system/extract_live_data.py      129 خط → live-data.js
nervous-system/extract_ops_data.py        58 خط → ops-data.js
nervous-system/extract_graph.py           —    → graph-data.js
nervous-system/extract_telegram_*.py      —    → telegram-data.js
```

**خط دقیق:** `extract_live_data.py:14` از `4d_system/outputs/daemon_state.json` می‌خواند. `extract_ops_data.py:15` از `_ops/state/ORGANISM-STATE.json` می‌خواند. دو extractor جداگانه روی دو state store متفاوت.

### ۷.۴ 🟡 API Key Name Drift

```python
# _ops/debate/client.py:175-176
"env_key": "SAKANA_API_KEY",
"env_key_alias": "FUGU_API_KEY",   # 2026-07-15: مالک FUGU_API_KEY گذاشته

# 4d_system/llm/fugu_client.py:72
"Set FUGU_API_KEY in .env to enable."
```

**اثر:** اگر کاربر `SAKANA_API_KEY` را در `.env` root بگذارد، `_ops/debate/client.py` آن را می‌بیند (با alias) ولی `4d_system/llm/fugu_client.py` آن را نمی‌بیند (فقط `FUGU_API_KEY` را می‌خواند).

---

## ۸. پیشنهادهای خلاصه (Remediation)

### 8.1 🔴 بحرانی — فوری
1. **یکی کردن ControlPlaneService:** `app/` را source-of-truth بگذارید. `4d_system/src/nbb_cp/` را soft-link کنید یا import کنید.
2. **یکی کردن داشبوردها:** `dashboard/server.py` را پایه بگذارید. `live/server.py` و `panel/server.py` را به عنوان route یا iframe به آن اضافه کنید.
3. **یکی کردن HTTP server framework:** یک `http_framework.py` در `_ops/` بسازید که همهٔ سرورها از آن ارث‌بری کنند.
4. **یکی کردن extractors:** یک `extractor.py` واحد بسازید که هر دو منبع (4d_system + _ops) را بخواند و یک `data.js` تولید کند.

### 8.2 🟡 متوسط — ۱-۲ هفته
5. **Base class برای همهٔ legs:** `Leg` base class را گسترش دهید تا `mining_leg.py` و `crypto_leg.py` و `accounting_leg.py` هم از آن ارث‌بری کنند.
6. **یکی کردن telegram handler:** `approval_channel.py` را به عنوان Telegram handler واحد بگذارید. بقیه را حذف کنید.
7. **یکی کردن .env:** فقط `F:/backup/.env` را نگه دارید. بقیه را حذف یا symlink کنید.
8. **Reconciliation بین state stores:** یک `state_reconciler.py` بسازید که `ORGANISM-STATE.json`، `cortex-state.json`، و `daemon_state.json` را مقایسه کند.

### 8.3 🟢 کم — ۱ ماه
9. **حذف worktreeهای قدیمی:** `.claude/worktrees/` 10+ نسخه قدیمی از `budgets.yaml` و `_ops/` دارد. حذف کنید.
10. **یکی کردن ledger formats:** `events.py` در `app/` و `4d_system/` را به `_ops/` import کنید یا برعکس.
11. **Standard API key naming:** یا همه جا `FUGU_API_KEY` یا همه جا `SAKANA_API_KEY`.
12. **Auto-refresh برای extractors:** `refresh-live-data.bat` را به organism tick اضافه کنید یا یک cron job بسازید.

---

## ۹. پیوست: آمار تکرارها

| شاخص | تعداد | توضیح |
|------|-------|-------|
| فایل‌های پایتون در `_ops/` | 477 | شامل test |
| فایل‌های پایتون در `app/` | 47 | NBB-CP |
| فایل‌های پایتون در `4d_system/` | 654 | شامل test + kernel |
| فایل‌های پایتون در `OCTOPUS/` | 55 | HTML/JS |
| فایل‌های پایتون در `nervous-system/` | 61 | extractors |
| فایل‌های `.env` فعال | 5+ | root, 4d_system, survival-gateway, launchpad, _ops |
| فایل‌های `budgets.yaml` | 24+ | فقط ۱ فعال |
| فایل‌های `telegram_bot.py` | 10+ | پروژه‌های مختلف |
| سرورهای HTTP | 5 | organism, dashboard, live, panel, cortex |
| داشبوردها HTML | 11+ | OCTOPUS/worlds/ + admin-telegram |
| state stores | 6 | JSON + SQLite |
| databases | 4 | SQLite + Postgres |
| ledger stores | 6 | متفاوت |
| control planes | 2 | _ops/ + app/4d_system/ |
| governors | 4 | متفاوت |
| extractors | 6 | ۳ نسخه × ۲ مسیر |

---

*گزارش تولیدشده توسط: تحلیل‌گر تکرارها و هدررفت‌های Octopus*
*زمان تولید: 2026-07-16 17:37 AUSEST*
*مسیر: F:/backup/optimization/dashboards_extractors_report.md*
