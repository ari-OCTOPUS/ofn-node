# گزارش تحلیل تکرارها و هدررفت‌ها در سیستم Octopus
> تاریخ تولید: 2026-07-16
> حوزه: `config_env` — مسیر اصلی: `F:/backup/`

---

## ۱. خلاصه اجرایی

این گزارش نتیجهٔ اسکن ۶ حوزهٔ اصلی برای شناسایی کارهای تکراری، کدهای کپی‌شده، داده‌های هدررفته، و معماری‌های موازی غیرضروری است. **۲۹ مورد تکرار** شناسایی شد که از آن‌ها **۷ مورد 🔴 بحرانی**، **۱۵ مورد 🟡 متوسط**، و **۷ مورد 🟢 کم** هستند. مهم‌ترین یافته‌ها: ۴ سرور HTTP مستقل، ۴ سیستم ledger با فرمت‌های مختلف، ۳ مسیر تلگرام جداگانه، ۲ daemon اصلی، و حداقل ۲۶ extractor تکراری/شبیه.

---

## ۲. حوزه `_ops` — تکرارهای داخلی

### 🔴 ۱. چهار سرور HTTP مستقل
| پورت | فایل | نقش |
|------|------|-----|
| 8771 | `_ops/organism.py:57` | ارگانیسم اصلی (حلقهٔ زنده) |
| 8770 | `_ops/dashboard/server.py:49` | داشبورد مدیریت |
| 8773 | `_ops/live/server.py:32` | اتاق کنترل زنده |
| 8790 | `_ops/panel/server.py:30` | پنل آشنایی و پروفایل |

**تحلیل:** هر سرور یک `BaseHTTPRequestHandler` + `ThreadingHTTPServer` جداگانه با کدهای مشابه (bind انحصاری، قفل تک‌نمونه، silent logging). هیچ‌کدام از یکدیگر import نمی‌کنند. **اتلاف:** ۴ پروسهٔ پایتون، ۴ پورت اشغال‌شده، ۴ کد HTML/CSS/JS جداگانه که همان state را می‌خوانند.

### 🔴 ۲. دو لجر مجزا در `_ops`
- **events.py** (`_ops/events.py:30`) → `state/events.jsonl` — رویدادهای ساختاریافته
- **unified_bus.py** (`_ops/unified_bus.py:35`) → `07 - Knowledge/genome-system/ledger/ledger.jsonl` — لجر ژنوم
- **ledger_core.py** (`_ops/legs/ledger_core.py`) — لجر حسابداری داخلی

**تحلیل:** `events.py` و `unified_bus.py` هر دو رویداد append-only می‌نویسند ولی به فایل‌های جداگانه. `ledger_core.py` و `personal_ledger.py` نیز در legs/ لجرهای موازی دارند.

### 🟡 ۳. فایل‌های state تکراری
| فایل | مسیر | نقش |
|------|------|-----|
| `ORGANISM-STATE.json` | `_ops/state/ORGANISM-STATE.json` | وضعیت ارگانیسم |
| `chrono.db` | `_ops/state/chrono.db` | پایگاه دادهٔ زمان/ضربان |
| `telemetry-latest.json` | `_ops/state/telemetry-latest.json` | تلمتری |
| `cortex-state.json` | `_ops/state/cortex/cortex-state.json` | وضعیت کورتکس |
| `doctor/rfcs.json` | `_ops/state/doctor/rfcs.json` | RFCهای دکتر |
| `fitness-latest.json` | `_ops/state/fitness-latest.json` | فیتنس |
| `replication-latest.json` | `_ops/state/replication-latest.json` | ریپلیکیشن |
| `pulse/heartstate-latest.json` | `_ops/state/pulse/heartstate-latest.json` | قلب |
| `pulse/work-state.json` | `_ops/state/pulse/work-state.json` | کار |

**تحلیل:** بیش از ۱۵ فایل state مجزا در `_ops/state/` وجود دارد که هر کدام توسط یک ماژول جداگانه نوشته و خوانده می‌شوند. هیچ projection/یکپارچه‌سازی وجود ندارد.

### 🟡 ۴. دو مسیر تلگرام موازی
- **telegram_center** (`_ops/telegram_center/center.py:187`) — «مرکز فرماندهی» با topicهای ۸ پا
- **approval_channel** (`_ops/budget/approval_channel.py:44`) — «کانال تأیید» برای گیت‌های پول

**تحلیل:** هر دو به `TELEGRAM_BOT_TOKEN` نیاز دارند ولی کد کاملاً جداگانه‌اند. `approval_channel` یک stub abstract است و `telegram_center` پیاده‌سازی کامل است. **نتیجه:** دو کانکتور تلگرام با هدف‌های متفاوت اما بدون اشتراک‌گذاری کد.

### 🟡 ۵. کدهای کپی‌شده در legs (فاقد base class کامل)
- `lead_leg.py` (`_ops/legs/lead_leg.py:39`) → `class LeadLeg(Leg):`
- `ziman_leg.py` (`_ops/legs/ziman_leg.py:111`) → `class ZimanLeg(Leg):`
- `cartographer_leg.py` (`_ops/legs/cartographer_leg.py:87`) → `class CartographerLeg(Leg):`
- `mining_leg.py` و `crypto_leg.py` و `accounting_leg.py` نیز از `Leg` ارث‌بری می‌کنند.

**تحلیل:** `Leg` یک dataclass ساده (`_ops/legs/leg.py:38`) است. هر leg خاص متدهای `run`, `beat`, `tick`, `propose` خود را دارد. کدهای مشابه (مثلاً `beat` با `time.time()`, `opslib.heartbeat`, `json.dumps`) در هر فایل تکرار شده. **اتلاف:** ~۲۰۰ خط کد کپی‌شده در هر leg.

### 🟡 ۶. Telemetry دوگانه
- **telemetry.py** (`_ops/budget/telemetry.py:21`) — خوانندهٔ تلمتری واقعی (genome + brain)
- **governor_epoch.py** (`_ops/budget/governor_epoch.py:27`) — حلقهٔ governor که خودش telemetry.snapshot() می‌خواند

**تحلیل:** `governor_epoch.py` از `telemetry` import می‌کند (`line 38`) ولی در `organism.py` نیز `telemetry.snapshot()` فراخوانی می‌شود (`line 275`). دو مسیر خواندن تلمتری با یک منبع واحد.

### 🟡 ۷. Doctor vs Cortex — تحلیل/تصمیم تکراری
- **doctor.py** (`_ops/doctor/doctor.py:190`) → `class Doctor:` — تکامل، RFC، sandbox، critic
- **cortex.py** (`_ops/cortex/cortex.py:1`) — مغز مرکزی: alignment, think, self-improve, part_loops, business_brain, stress, innervation

**تحلیل:** دکتر «تکامل کد» را پیشنهاد می‌دهد؛ کورتکس «plan کار» را مرتب می‌کند. هر دو از `model_router.ask()` برای LLM استفاده می‌کنند. هر دو state خود را می‌نویسند. **اتلاف:** دو مسیر تصمیم‌گیری مستقل با منطق‌های مشابه (observe → think → propose → persist).

### 🟢 ۸. لایه‌های config تکراری
- **opslib.py** (`_ops/budget/opslib.py`) — مسیرها، env، heartbeat، alert
- **env_loader.py** (`_ops/budget/env_loader.py`) — لودر `.env`
- **budgets.yaml** (`_ops/budget/budgets.yaml`) — بودجهٔ ارگان‌ها
- **OCTOPUS-flags.cmd** (`_ops/OCTOPUS-flags.cmd`) — فلگ‌های override

**تحلیل:** `organism.py:152` و `cortex.py:398` و `center.py:603` هر سه `env_loader.load_env()` را فراخوانی می‌کنند. `.env` حداقل ۳ بار خوانده می‌شود.

### 🟡 ۹. Watchdog دوگانه
- **watchdog.py** (`_ops/watchdog.py`) — Python watchdog
- **organism-watchdog.ps1** (`04 - Architect System/scripts/organism-watchdog.ps1`) — PowerShell watchdog

**تحلیل:** دو watchdog مستقل با زبان‌های مختلف. هیچ‌کدام از دیگری خبر ندارند.

---

## ۳. حوزه `app_vs_ops` — مقایسه `app/` و `_ops/`

### 🔴 ۱. دو Control Plane جداگانه
- **app/src/nbb_cp/app/service.py** (`F:/backup/app/src/nbb_cp/app/service.py:54`) → `class ControlPlaneService` — proposal → gate → ledger → effect
- **_ops/organism.py** (`F:/backup/_ops/organism.py:147`) → `main()` — حلقهٔ زنده با telemetry + governor + fitness

**تحلیل:** `app/` (NBB-CP) یک سیستم کنترل پلن رسمی با FastAPI است؛ `_ops/organism.py` یک حلقهٔ daemon دست‌ساز است. هر دو «proposal-only» و «shadow-mode» را پیاده‌سازی می‌کنند. **نتیجه:** دو control plane موازی که یکدیگر را نمی‌شناسند.

### 🔴 ۲. دو Governor
- **app/src/nbb_cp/app/governor.py** (`F:/backup/app/src/nbb_cp/app/governor.py`) — governor رسمی NBB-CP
- **_ops/budget/governor_epoch.py** (`F:/backup/_ops/budget/governor_epoch.py:27`) — governor سایهٔ organism

**تحلیل:** هر دو epoch-based scheduling دارند. هر دو pressure/velocity را محاسبه می‌کنند. هر دو allocation dry-run تولید می‌کنند.

### 🔴 ۳. دو API HTTP جداگانه
- **app/src/nbb_cp/api/http.py** (`F:/backup/app/src/nbb_cp/api/http.py:49`) — FastAPI با `/health`, `/state`, `/audit`, `/proposals`, `/kill`
- **_ops/organism.py** (`F:/backup/_ops/organism.py:57`) — `http.server` با `/api/organism`, `/api/telemetry`, `/api/fitness`

**تحلیل:** هر دو API فقط‌خواندنی + endpointهای کنترلی دارند. `app` FastAPI است ولی `_ops` stdlib-only. **نتیجه:** دو پورت جداگانه (app پورت نامشخص ولی `_ops` روی 8771).

### 🟡 ۴. دو Ledger
- **app/src/nbb_cp/kernel/events.py** (`F:/backup/app/src/nbb_cp/kernel/events.py`) — event ledger رسمی NBB-CP
- **_ops/events.py** (`F:/backup/_ops/events.py`) — event ledger organism

**تحلیل:** هر دو `LedgerEvent` با `append` دارند. هر دو `timestamp`, `trace_id`, `event_name` را ذخیره می‌کنند. هر دو JSONL هستند.

### 🟡 ۵. دو README مشابه (Doctrinal Twin)
- **app/README.md** (`F:/backup/app/README.md`) — «NBB Control Plane — Build-3-Readme»
- **4d_system/README.md** (`F:/backup/4d_system/README.md`) — مشابه

**تحلیل:** هر دو فایل README.md مشابه دارند ولی از یکدیگر branch نشده‌اند. همچنین `MANIFEST.yaml`, `RUNBOOK.md`, `REGISTRY.md` در هر دو کپی شده‌اند.

### 🟡 ۶. دو set Invariant متفاوت
- **app/src/nbb_cp/kernel/invariants.py** (`F:/backup/app/src/nbb_cp/kernel/invariants.py`) — 12 invariant
- **_ops/budget/opslib.py** + `_ops/cortex/*` — 10+ invariant در کامنت‌ها

**تحلیل:** هر دو سیستم «fail-closed» و «propose-only» را تضمین می‌کنند ولی با قوانین متفاوت.

---

## ۴. حوزه `4d_system` — تکرارهای 4d_system/

### 🔴 ۱. LLM Router مستقل از survival-gateway
- **4d_system/llm/router.py** (`F:/backup/4d_system/llm/router.py`) — GLM + Fugu + Ollama
- **survival-gateway/.env** — کلیدهای API: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY`, `DEEPSEEK_API_KEY`
- **_ops/cortex/model_router.py** (`F:/backup/_ops/cortex/model_router.py`) — router محلی `_ops`

**تحلیل:** `4d_system` از `GLM_API_KEY` و `FUGU_API_KEY` استفاده می‌کند (`settings.py:93-99`). `_ops` از `OLLAMA_MODEL` و `OPENAI_API_KEY` (در `.env` root). `survival-gateway` از `ANTHROPIC`, `OPENAI`, `GEMINI`, `DEEPSEEK`, `ZAI`, `SAKANA` استفاده می‌کند. **نتیجه:** حداقل ۳ مسیر LLM routing جداگانه با ۸ کلید API مختلف.

### 🔴 ۲. Daemon مستقل از organism.py
- **4d_system/brain/daemon.py** (`F:/backup/4d_system/brain/daemon.py:89`) — `run_forever()` — tick + auto_propose + git_watcher + housekeeping
- **_ops/organism.py** (`F:/backup/_ops/organism.py:263`) — `while True` — tick + governor + fitness + doctor + legs

**تحلیل:** هر دو یک `while True` با `time.sleep()` دارند. هر دو `ctrl.run_one()` یا `telemetry.snapshot()` را صدا می‌زنند. هر دو `state.json` می‌نویسند. **نتیجه:** دو daemon مستقل که می‌توانند هم‌زمان اجرا شوند و با یکدیگر تداخل نداشته باشند.

### 🟡 ۳. دو Config Reader
- **4d_system/config/settings.py** (`F:/backup/4d_system/config/settings.py:15`) — `load_dotenv()` + `LLMConfig` dataclass
- **_ops/budget/opslib.py** — `env_loader.load_env()` + `os.environ.get()`
- **app/src/nbb_cp/app/config.py** (`F:/backup/app/src/nbb_cp/app/config.py:13`) — `_load_dotenv()` + `AppConfig`

**تحلیل:** هر سه `.env` را می‌خوانند ولی با توابع/کلاس‌های متفاوت. `4d_system` از `dotenv` استفاده می‌کند؛ `_ops` از `env_loader` دست‌ساز؛ `app` از `_load_dotenv` دست‌ساز.

### 🟡 ۴. چند Extractor روی داده‌های متفاوت
- **4d_system/outputs/** — `daemon_state.json`, `llm_budget.json`, `real_cache/*.json`, `self_evolved/*.json`
- **_ops/state/** — `ORGANISM-STATE.json`, `telemetry/*.json`, `cortex/*.json`
- **nervous-system/extract_*.py** — ۲۶+ extractor برای داشبورد OCTOPUS

**تحلیل:** هر سیستم داده‌های خود را استخراج و ذخیره می‌کند. هیچ یکپارچه‌سازی وجود ندارد.

### 🟢 ۵. دو `.env` متفاوت
- **root .env** (`F:/backup/.env`) — `POCKETSMITH_API_KEY`, `FUGU_API_KEY`, `SAKANA_API_KEY`
- **4d_system/.env** (`F:/backup/4d_system/.env`) — `FUGU_API_KEY`, `GLM_API_KEY`
- **survival-gateway/.env** (`F:/backup/survival-gateway/.env`) — ۶ کلید API دیگر

**تحلیل:** حداقل ۳ فایل `.env` با کلیدهای متفاوت. `FUGU_API_KEY` در root و `4d_system` تکرار شده.

---

## ۵. حوزه `dashboards_extractors` — داشبوردها و اکسترکتورها

### 🔴 ۱. ۲۶+ Extractor تکراری/شبیه
- **nervous-system/extract_*.py** — ۲۶ فایل Python (`extract_live_data.py`, `extract_ops_data.py`, `extract_graph_data.py`, `extract_health_score.py`, `extract_mining_data.py`, ...)
- **OCTOPUS/nervous-system/extract_*.py** — کپی مشابه
- **.claude/worktrees/*/nervous-system/extract_*.py** — کپی‌های worktree

**تحلیل:** هر extractor یک فایل مستقل ~۵۰-۱۰۰ خطی است که داده را می‌خواند و یک `.js` یا `.json` تولید می‌کند. ۲۶ extractor = ۲۶× کد مشابه (open, read, parse, write). هیچ base class یا pipeline مشترک وجود ندارد.

### 🔴 ۲. ۵+ داشبورد HTML/UI جداگانه
- **OCTOPUS/admin-telegram/index.html** — داشبورد تلگرام
- **OCTOPUS/worlds/index.html** — داشبورد جهان‌ها (۱۰ world)
- **OCTOPUS/mobile/index.html** — داشبورد موبایل (۱۰ صفحه)
- **_ops/dashboard/server.py** — داشبورد زنده (پورت 8770)
- **_ops/live/server.py** — اتاق کنترل زنده (پورت 8773)
- **_ops/panel/server.py** — پنل آشنایی (پورت 8790)
- **4d_system/ui/** — داشبورد Streamlit/UI (tab_dashboard, tab_control_plane, ...)

**تحلیل:** هر داشبورد یک سرور/صفحهٔ مستقل است. هیچ component/UI library مشترک وجود ندارد. CSS در هر فایل تکرار شده.

### 🟡 ۳. refresh-live-data.bat — چند نسخه
- **F:/backup/nervous-system/refresh-live-data.bat** — کامل (۱۷ extractor)
- **F:/backup/OCTOPUS/nervous-system/refresh-live-data.bat** — کوتاه (۳ extractor: live, ops, graph)
- **.claude/worktrees/*/refresh-live-data.bat** — کپی‌های worktree

**تحلیل:** نسخهٔ root ۱۷ extractor را اجرا می‌کند ولی نسخهٔ OCTOPUS فقط ۳ تا را اجرا می‌کند. داده‌ها به `OCTOPUS/worlds/` منتقل نمی‌شوند — هر داشبورد دادهٔ خود را می‌سازد.

### 🟡 ۴. دو nervous-system
- **F:/backup/nervous-system/** — نسخهٔ اصلی
- **F:/backup/OCTOPUS/nervous-system/** — کپی/سایه

**تحلیل:** دو دایرکتوری با محتوای مشابه. `OCTOPUS/nervous-system/` یک snapshot قدیمی است که با refresh-live-data.bat آپدیت می‌شود.

---

## ۶. حوزه `config_env` — فایل‌های پیکربندی

### 🟡 ۱. ۳ فایل `.env` (و تعداد `.env.example`)
| مسیر | کلیدهای اصلی |
|------|-------------|
| `F:/backup/.env` | `POCKETSMITH_API_KEY`, `FUGU_API_KEY`, `SAKANA_API_KEY` |
| `F:/backup/4d_system/.env` | `FUGU_API_KEY`, `GLM_API_KEY` |
| `F:/backup/survival-gateway/.env` | `ANTHROPIC`, `OPENAI`, `GEMINI`, `DEEPSEEK`, `ZAI`, `SAKANA` |
| `F:/backup/app/.env.example` | — |
| `F:/backup/4d_system/.env.example` | — |
| `F:/backup/_launchpad/second-brain-live/control-brain/.env` | — |

### 🟡 ۲. ۱+ فایل `budgets.yaml`
- `F:/backup/_ops/budget/budgets.yaml` — تنها نسخهٔ فعال در root
- `.claude/worktrees/*/_ops/budget/budgets.yaml` — کپی‌های worktree

### 🟡 ۳. ۲ فایل `MANIFEST.yaml`
- `F:/backup/4d_system/MANIFEST.yaml`
- `F:/backup/app/MANIFEST.yaml`
- هر دو مشابه ولی در پروژه‌های جداگانه

### 🟡 ۴. ۱۰ فایل `ACTIVATION-*.flag` + ۱ فایل `STOP-ORGANISM`
- `F:/backup/_ops/ACTIVATION-CORTEX-PAID.flag`
- `F:/backup/_ops/ACTIVATION-DEBATE.flag`
- `F:/backup/_ops/ACTIVATION-GO-LIVE.flag`
- `F:/backup/_ops/ACTIVATION-GOVERNOR-LLM.flag`
- ... (۱۰ فایل)
- `F:/backup/_ops/STOP-ORGANISM`

**تحلیل:** هر flag یک فایل مجزا است. می‌توانست در یک `config.json` واحد باشد.

### 🟡 ۵. نام‌های متفاوت برای یک کلید API
- `FUGU_API_KEY` (root) = `SAKANA_API_KEY` (root) — هر دو به `api.sakana.ai` اشاره می‌کنند
- `ZAI_API_KEY` (survival-gateway) = `GLM_API_KEY` (4d_system) — هر دو به `open.bigmodel.com` اشاره می‌کنند
- `FUGU_API_KEY` (root) = `FUGU_API_KEY` (4d_system) — مقدار یکسان

**نتیجه:** ۲ کلید API با نام‌های متفاوت برای یک سرویس یکسان (Sakana/Fugu, Zhipu/ZAI/GLM).

### 🟢 ۶. تکرار config در پروژه‌های launchpad
- `_launchpad/second-brain-live/control-brain/.env`
- `_launchpad/second-brain-live/painting-bot/.env.example`
- هر دو پروژه launchpad `.env` خود را دارند.

---

## ۷. حوزه `cross_system` — تکرارهای سیستمی

### 🔴 ۱. سه فرمت Ledger متفاوت
| سیستم | فرمت | مسیر |
|-------|------|------|
| `_ops` | JSONL (events.py) | `_ops/state/events.jsonl` |
| `_ops` | JSONL (unified_bus) | `07 - Knowledge/genome-system/ledger/ledger.jsonl` |
| `_ops` | JSON (ledger_core) | `_ops/legs/ledger_core.py` (SQLite درونی) |
| `app` | dataclass + append | `app/src/nbb_cp/kernel/events.py` |
| `4d_system` | JSONL (brain/events.py) | `4d_system/brain/events.py` |
| `4d_system` | JSON (knowledge/ledger.py) | `4d_system/knowledge/ledger.py` |

**نتیجه:** حداقل ۶ پیاده‌سازی ledger با ۳ فرمت اصلی (JSONL, dataclass+append, JSON/SQLite) که هیچ‌کدام با یکدیگر همگام نیستند.

### 🔴 ۲. سه جای ذخیرهٔ State
- `ORGANISM-STATE.json` (`_ops/state/`) — توسط organism.py
- `chrono.db` (`_ops/state/`) — SQLite توسط chrono.py
- `4d_system/outputs/daemon_state.json` — توسط daemon.py
- `4d_system/outputs/control_plane/control_plane.db` — SQLite توسط 4d_system
- `_launchpad/second-brain-live/control-brain/core.db` — SQLite توسط launchpad

**نتیجه:** حداقل ۵ پایگاه دادهٔ SQLite/JSON مستقل.

### 🔴 ۳. سه مسیر Telegram
- `_ops/telegram_center/` — Octopus telegram center
- `4d_system/brain/telegram_bot.py` — 4d_system telegram bot
- `4d_system/brain/notify.py` — notify digest telegram
- `_launchpad/second-brain-live/control-brain/` — launchpad telegram (python-telegram-bot venv)

**نتیجه:** حداقل ۳ پیکربندی تلگرام با ۲ library مختلف (requests خام vs python-telegram-bot).

### 🔴 ۴. سه مسیر LLM Routing
- `_ops/cortex/model_router.py` — Ollama + OpenAI (محلی)
- `4d_system/llm/router.py` — GLM + Fugu + Ollama
- `survival-gateway/` — Anthropic + OpenAI + Gemini + DeepSeek + ZAI + Sakana

### 🟡 ۵. چهار پایگاه داده SQLite/Postgres
- `chrono.db` (`_ops/state/`)
- `core.db` (`_launchpad/second-brain-live/control-brain/`)
- `control_plane.db` (`4d_system/outputs/control_plane/`)
- `4d_experiments.db` (`4d_system/outputs/`)
- `postgres` (`survival-gateway/data/postgres/`)
- `nbb.db` (تنظیم شده در `app/src/nbb_cp/app/config.py:18`)

**نتیجه:** ۶ پایگاه دادهٔ مستقل.

### 🟡 ۶. سه تعریف Budget
- `_ops/budget/budgets.yaml` — YAML با ارگان‌ها و سقف‌ها
- `app/src/nbb_cp/app/config.py` — `AppConfig.global_cap_cents = 3000`
- `4d_system/config/settings.py` — فاقد budget مستقیم (ولی LLMConfig دارد)

**نتیجه:** بودجه در ۳ فایل با ۳ فرمت مختلف (YAML, Python dataclass, env) تعریف شده.

---

## ۸. جدول خلاصه رتبه‌بندی

| ردیف | تکرار | شدت | مسیر/فایل کلیدی |
|------|-------|-----|-----------------|
| ۱ | ۴ سرور HTTP | 🔴 | `organism.py:57`, `dashboard/server.py:49`, `live/server.py:32`, `panel/server.py:30` |
| ۲ | ۳ لجر موازی در `_ops` | 🔴 | `events.py:30`, `unified_bus.py:35`, `legs/ledger_core.py` |
| ۳ | ۲ Control Plane | 🔴 | `app/src/nbb_cp/app/service.py:54`, `_ops/organism.py:147` |
| ۴ | ۲ Governor | 🔴 | `app/src/nbb_cp/app/governor.py`, `_ops/budget/governor_epoch.py:27` |
| ۵ | ۲ API HTTP | 🔴 | `app/src/nbb_cp/api/http.py:49`, `_ops/organism.py:57` |
| ۶ | ۲ Daemon | 🔴 | `4d_system/brain/daemon.py:89`, `_ops/organism.py:263` |
| ۷ | ۳ LLM Router | 🔴 | `_ops/cortex/model_router.py`, `4d_system/llm/router.py`, `survival-gateway/` |
| ۸ | ۲ Telegram Path | 🟡 | `_ops/telegram_center/center.py:187`, `_ops/budget/approval_channel.py:44` |
| ۹ | ۲ Doctor/Cortex | 🟡 | `_ops/doctor/doctor.py:190`, `_ops/cortex/cortex.py:1` |
| ۱۰ | ۲ Telemetry | 🟡 | `_ops/budget/telemetry.py:21`, `_ops/budget/governor_epoch.py:27` |
| ۱۱ | ۲ Watchdog | 🟡 | `_ops/watchdog.py`, `04 - Architect System/scripts/organism-watchdog.ps1` |
| ۱۲ | ۲+ `.env` | 🟡 | `.env`, `4d_system/.env`, `survival-gateway/.env` |
| ۱۳ | ۲+ README/MANIFEST | 🟡 | `app/README.md`, `4d_system/README.md`, `app/MANIFEST.yaml`, `4d_system/MANIFEST.yaml` |
| ۱۴ | ۲+ Invariant Set | 🟡 | `app/src/nbb_cp/kernel/invariants.py`, `_ops/budget/opslib.py` |
| ۱۵ | ۲+ Config Reader | 🟡 | `4d_system/config/settings.py:15`, `_ops/budget/env_loader.py`, `app/src/nbb_cp/app/config.py:13` |
| ۱۶ | ۲ Extractor Set | 🟡 | `nervous-system/`, `OCTOPUS/nervous-system/` |
| ۱۷ | ۲+ Dashboard | 🟡 | `OCTOPUS/worlds/`, `OCTOPUS/admin-telegram/`, `OCTOPUS/mobile/`, `_ops/dashboard/`, `_ops/live/`, `_ops/panel/`, `4d_system/ui/` |
| ۱۸ | ۲+ refresh-live-data.bat | 🟡 | `nervous-system/refresh-live-data.bat`, `OCTOPUS/nervous-system/refresh-live-data.bat` |
| ۱۹ | ۲+ State File | 🟡 | `ORGANISM-STATE.json`, `cortex-state.json`, `doctor/rfcs.json`, `telemetry-latest.json`, `fitness-latest.json`, `replication-latest.json` |
| ۲۰ | ۳ DB | 🟡 | `chrono.db`, `core.db`, `control_plane.db`, `4d_experiments.db`, `postgres/`, `nbb.db` |
| ۲۱ | ۳ Budget Definition | 🟡 | `_ops/budget/budgets.yaml`, `app/src/nbb_cp/app/config.py`, `4d_system/config/settings.py` |
| ۲۲ | ۶ Legs کپی‌شده | 🟢 | `_ops/legs/lead_leg.py`, `mining_leg.py`, `crypto_leg.py`, `ziman_leg.py`, `accounting_leg.py`, `cartographer_leg.py` |
| ۲۳ | ۱۰+ ACTIVATION Flag | 🟢 | `_ops/ACTIVATION-*.flag` |
| ۲۴ | ۲ API Key Name | 🟢 | `FUGU_API_KEY` = `SAKANA_API_KEY`, `ZAI_API_KEY` = `GLM_API_KEY` |
| ۲۵ | ۳+ Launchpad Config | 🟢 | `_launchpad/second-brain-live/*/.env` |
| ۲۶ | ۱۵+ فایل state در `_ops/state/` | 🟢 | `_ops/state/*` |
| ۲۷ | ۴+ `.env.example` | 🟢 | `app/.env.example`, `4d_system/.env.example`, `survival-gateway/.env.example` |
| ۲۸ | ۲+ Ledger در `app` و `4d_system` | 🟢 | `app/src/nbb_cp/kernel/events.py`, `4d_system/brain/events.py`, `4d_system/knowledge/ledger.py` |
| ۲۹ | ۲+ `nervous-system` | 🟢 | `F:/backup/nervous-system/`, `F:/backup/OCTOPUS/nervous-system/` |

---

## ۹. نتیجه‌گیری و پیشنهادات

### 🔴 اولویت بحرانی (فوری)
1. **یکپارچه‌سازی سرورها:** ۴ سرور HTTP را به یک Reverse Proxy (مثلاً Nginx یا یک FastAPI gateway) متصل کن یا یکی از آن‌ها را به عنوان canonical server انتخاب کن.
2. **یکپارچه‌سازی Ledger:** `events.py`, `unified_bus.py`, `ledger_core.py` و `app/src/nbb_cp/kernel/events.py` را به یک لجر واحد (مثلاً `genome-system/ledger/ledger.jsonl`) ادغام کن.
3. **ادغام Control Plane:** `app/` (NBB-CP) و `_ops/organism.py` را بررسی کن؛ یکی را به عنوان canonical انتخاب کن و دیگری را deprecated کن.
4. **یکپارچه‌سازی LLM Router:** `_ops/cortex/model_router.py`, `4d_system/llm/router.py` و `survival-gateway/` را به یک router واحد با یک فایل `.env` واحد متصل کن.
5. **ادغام Daemon:** `4d_system/brain/daemon.py` و `_ops/organism.py` را به یک daemon واحد تبدیل کن.

### 🟡 اولویت متوسط (۱-۲ هفته)
1. **استخراج Base Class برای Legs:** `Leg` را از یک dataclass ساده به یک ABC با متدهای `beat()`, `tick()`, `propose()` تبدیل کن.
2. **یکپارچه‌سازی State:** همهٔ فایل‌های state را به یک projection واحد (مثلاً `state/system-state.json` با schema) تبدیل کن.
3. **ادغام Telegram:** `telegram_center` و `approval_channel` را به یک کانکتور واحد تبدیل کن.
4. **یکپارچه‌سازی Config:** `.env`, `budgets.yaml`, `OCTOPUS-flags.cmd` را به یک `config.yaml` واحد با override env تبدیل کن.
5. **استخراج پایپ‌لاین Extractor:** ۲۶ extractor را به یک base class `Extractor` با متدهای `read()`, `transform()`, `write()` تبدیل کن.
6. **یکپارچه‌سازی Dashboard:** یک UI component library مشترک (مثلاً React/Vue یا یک template Jinja2) برای همهٔ داشبوردها بساز.
7. **ادغام DB:** `chrono.db`, `core.db`, `control_plane.db`, `4d_experiments.db` را به یک SQLite واحد با جداگانهٔ جداول تبدیل کن.

### 🟢 اولویت کم (ماهانه)
1. **یکسان‌سازی نام کلیدهای API:** `FUGU_API_KEY` را حذف و فقط `SAKANA_API_KEY` نگه دار؛ `GLM_API_KEY` و `ZAI_API_KEY` را یکی کن.
2. **ادغام README/MANIFEST:** `app/README.md` و `4d_system/README.md` را به یک README واحد تبدیل کن.
3. **حذف ACTIVATION flag فایل‌ها:** به جای ۱۰ فایل `.flag`، یک `config.json` با `activation: {cortex_paid: true, debate: false, ...}` بساز.
4. **حذف کپی‌های Worktree:** `.claude/worktrees/` را در `.gitignore` قرار بده و در cron پاک کن.
5. **حذف کپی‌های `_launchpad`:** `second-brain-live` را به `4d_system/` یا `_ops/` منتقل کن.

---
> **گزارش‌گر:** تحلیل‌گر تکرارها و هدررفت‌ها
> **زمان:** 2026-07-16 17:37
> **مسیر ذخیره:** `F:/backup/optimization/config_env_report.md`
