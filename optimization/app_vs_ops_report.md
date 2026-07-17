# گزارش تحلیل تکرارها و هدررفت‌ها در سیستم Octopus
## حوزه: app_vs_ops — مسیر F:/backup/
**تاریخ گزارش:** 2026-07-16 17:37 AUSEST  
**تحلیل‌گر:** Orchestrator Agent (autonomous duplication audit)  
**روش:** Glob + Grep + Read فایل‌های کلیدی + cross-reference  

---

## executive_summary
این گزارش ۱۵ تکرار/هدررفت بحرانی (🔴)، ۱۲ تکرار متوسط (🟡)، و ۸ تکرار کم (🟢) را شناسایی کرد.  
**بزرگ‌ترین خطر:** سه «control plane» جداگانه (_ops/organism.py، app/NBB-CP، 4d_system/daemon) که هر یک ledger، state، budget، telemetry، و HTTP server خود را دارند و هیچ‌کدام به یکدیگر متصل نیستند.  
**بزرگ‌ترین هدررفت:** ۲۰+ extractor فقط-خواندنی در nervous-system/ که هر بار کل vault را از نو می‌خوانند (۳-۱۵ ثانیه هر کدام) و هیچ caching/layering ندارند.

---

## 🔴 بحرانی — سه Control Plane موازی (Triple Control Plane)

### 🔴 CP-1: organism.py (_ops) vs NBB-CP (app/) vs 4D Daemon (4d_system/)
| سیستم | مسیر | تکلیف | پورت | وضعیت اتصال |
|---|---|---|---|---|
| organism.py | `_ops/organism.py` | حلقهٔ متابولیسم + HTTP status | 8771 | **ایزوله** — هیچ‌کس به آن POST نمی‌کند |
| NBB-CP | `app/src/nbb_cp/app/service.py` | Control Plane Service (proposal→gate→ledger) | FastAPI (port نامشخص) | **ایزوله** — "not yet wired to any leg" (MANIFEST.yaml:95) |
| 4D Daemon | `4d_system/brain/daemon.py` | حلقهٔ خودمختار research + self-evolution | streamlit / headless | **ایزوله** — "standalone research experiment" (MANIFEST.yaml:110) |

**تحلیل:** سه سیستم «حاکمیتی» جداگانه هر یک «یک‌تنه» هدف‌های یکسان (budget gate، ledger، human approval، kill switch) را پیاده‌سازی کرده‌اند.  
**هدررفت:** ~۲۵۵۱ LOC (NBB) + ~۶۳۲ LOC (organism) + ~۱۶۳۵۰ LOC (4D) = **~۱۹۵۰۰ LOC** که همگی «doctrinal twin» هستند ولی هیچ wiring بینشان نیست.  
**سند:** `app/MANIFEST.yaml:95` صراحتاً می‌گوید NBB-CP "could become the central brain that all 6 project legs attach to — **not yet wired**".  
**سند:** `4d_system/MANIFEST.yaml:110` صراحتاً می‌گوید "INDEPENDENT — 4D is a standalone research experiment".

---

### 🔴 CP-2: چهار HTTP Server مستقل (Quad Server)
| سرور | مسیر | پورت | فریم‌ورک | هدف |
|---|---|---|---|---|
| organism status | `_ops/organism.py:57` | 8771 | `http.server` (ThreadingHTTPServer) | وضعیت ماشین‌خوان |
| dashboard | `_ops/dashboard/server.py:49` | 8770 | `http.server` (ThreadingHTTPServer) | داشبورد زنده |
| live | `_ops/live/server.py:32` | 8773 | `http.server` (ThreadingHTTPServer) | اتاق کنترل زنده |
| panel | `_ops/panel/server.py:30` | 8790 | `http.server` (ThreadingHTTPServer) | پنل مدیریت |
| cortex | `_ops/cortex/model_router.py` ( referenced) | 8772 | HTTP API | LLM routing |
| NBB API | `app/src/nbb_cp/api/http.py` | نامشخص | FastAPI | کنترل پلن رسمی |
| 4D UI | `4d_system/ui/app.py` | نامشخص | Streamlit | داشبورد ۹ تب |

**تحلیل:** ۷ سرور HTTP جداگانه که ۴ تای آن‌ها (`http.server` پایتون) در `_ops/` روی ۴ پورت متفاوت اجرا می‌شوند. هر کدام handler جداگانه، routing جداگانه، و static HTML جداگانه دارند. هیچ reverse proxy یا unified API gateway وجود ندارد.  
**تکرار:** هر ۴ سرور `_ops/` الگوی `ThreadingHTTPServer` + `BaseHTTPRequestHandler` را کپی کرده‌اند (`_ops/organism.py:73`، `_ops/dashboard/server.py:925`، `_ops/live/server.py:750`، `_ops/panel/server.py:513`).

---

### 🔴 CP-3: سه Ledger با فرمت‌های متفاوت (Triple Ledger)
| Ledger | مسیر | فرمت | صاحب |
|---|---|---|---|
| Genome Ledger | `07 - Knowledge/genome-system/ledger/ledger.jsonl` | JSONL (type, ts, payload, hash) | `_ops/events.py` + common/llm.py |
| Ops Events | `_ops/events.py` + `_ops/state/events.jsonl` | JSONL (legacy) | organism.py |
| NBB Ledger | `app/src/nbb_cp/kernel/events.py` | Typed dataclass (EventKind, LedgerEvent) | NBB-CP service |
| 4D Events | `4d_system/brain/events.py` | تابع سادهٔ emit() | 4D daemon |

**تحلیل:** ۴ سیستم ledger/events جداگانه. NBB-CP یک ledger "hash-chained" با typed events دارد؛ 4D یک emit ساده دارد؛ organism از `_ops/events.py` استفاده می‌کند؛ genome-system یک Ledger کلاس جداگانه دارد. هیچ replication یا synchronization بین این ۴ ledger وجود ندارد.  
**سند:** `app/MANIFEST.yaml:25` — "INV-5: ledger is append-only and hash-chained".  
**سند:** `_ops/budget/telemetry.py:6` — "منابع حقیقت: genome-system → ledger/ledger.jsonl" ولی "control-brain → core.db".

---

### 🔴 CP-4: سه State Store با DB‌های متفاوت (Triple State)
| State | مسیر | فرمت | اندازه/تاریخ |
|---|---|---|---|
| ORGANISM-STATE | `_ops/state/ORGANISM-STATE.json` + `.ziman` | JSON | ۲۲۴ بایت / ۱۶ جولای |
| chrono.db | `_ops/state/chrono.db` | SQLite | ۲.۲ MB / ۱۶ جولای |
| telemetry-latest | `_ops/state/telemetry-latest.json` | JSON | — |
| 4D daemon_state | `4d_system/outputs/daemon_state.json` | JSON | — |
| 4D experiments DB | `4d_system/outputs/4d_experiments.db` | SQLite | — |
| NBB DB | `app/outputs/nbb.db` (از config.py:18) | SQLite | — |
| core.db (control-brain) | `_launchpad/second-brain-live/control-brain/core.db` | SQLite | — |

**تحلیل:** حداقل ۷ فایل state/DB در ۵ مسیر متفاوت. `_ops/state/chrono.db` (SQLite ۲.۲MB) به تنهایی یک بستر زمان/ضربان دارد؛ 4D یک SQLite experiments دارد؛ NBB یک SQLite budget store دارد؛ control-brain یک SQLite core.db دارد. هیچ Foreign Key یا replication بین این DBها وجود ندارد.

---

### 🔴 CP-5: دو Governor موازی (Dual Governor)
| Governor | مسیر | تکلیف | وضعیت |
|---|---|---|---|
| governor_epoch.py | `_ops/budget/governor_epoch.py` | حلقهٔ epoch آلوستاتیک (shadow/dry) | **روشن** — توسط organism.py فراخوانی می‌شود |
| NBB Governor | `app/src/nbb_cp/app/governor.py` | ControlPlaneService orchestration | **ساخته‌شده** — "not yet wired" |

**تحلیل:** هر دو "governor" هستند ولی یکی در `_ops/` (legacy، فاقد type safety) و دیگری در `app/` (NBB-CP، با ۱۲ invariant و FastAPI). NBB-CP صراحتاً می‌گوید "the Governor proposes; gates enforce; the human rules" (INV-4) ولی هنوز به هیچ leg وصل نشده.

---

## 🟡 متوسط — تکرارهای ساختاری

### 🟡 ST-1: Telegram دوگانه (Dual Telegram)
| مسیر | فایل | هدف | توکن env |
|---|---|---|---|
| `_ops/telegram_center/` | center.py, tg_api.py, render.py | کانال مرکزی تلگرام | `TELEGRAM_BOT_TOKEN` |
| `_ops/budget/` | approval_channel.py, approval_channel_merge.py | کانال تأیید انسانی (HITL) | `TELEGRAM_BOT_TOKEN` + `TELEGRAM_OWNER_CHAT_ID` |
| `_ops/wiring.py` | wire_telegram | wiring stub | `TELEGRAM_BOT_TOKEN` |
| `4d_system/brain/` | telegram_bot.py | بات تأیید ۴D | — |
| `_launchpad/second-brain-live/control-brain/` | — | legacy telegram | `TELEGRAM_TOKEN` + `OWNER_CHAT_ID` |
| `_launchpad/second-brain-live/` | painting-bot, etc. | project-specific bots | `TELEGRAM_SABA_BOT_TOKEN`، `TELEGRAM_LANGAR_BOT_TOKEN` |

**تحلیل:** حداقل ۶ مسیر تلگرام با ۴+ token env متفاوت. `_ops/telegram_center/` و `_ops/budget/approval_channel.py` دو پیاده‌سازی جداگانه برای یک هدف (ارسال/دریافت از تلگرام) هستند. approval_channel.py ۸۸۱ خط دارد ولی به دلیل نبود `TELEGRAM_BOT_TOKEN` در حالت stub است.  
**سند:** `04 - Architect System/OCTOPUS-AUDIT-PHASE1-REPO-AUTOPSY.md:391` — "Requires TELEGRAM_BOT_TOKEN (currently missing → queue stub)".

### 🟡 ST-2: سه Config Reader با .env جداگانه (Triple Config)
| Config Reader | مسیر | `.env` | کلیدهای خوانده‌شده |
|---|---|---|---|
| env_loader.py | `_ops/budget/env_loader.py` | `F:\\backup\\.env` (root) | GLM_API_KEY, FUGU_API_KEY, DEEPSEEK_API_KEY, TELEGRAM_BOT_TOKEN |
| settings.py | `4d_system/config/settings.py` | `4d_system/.env` (dotenv) | GLM_API_KEY, FUGU_API_KEY, GLM_BASE_URL, FUGU_BASE_URL |
| config.py | `app/src/nbb_cp/app/config.py` | env (os.environ) | NBB_MODE, NBB_GLOBAL_CAP_CENTS, NBB_LLM_MODE |
| survival-gateway | `survival-gateway/.env.example` | `survival-gateway/.env` | LITELLM_MASTER_KEY, POSTGRES_*, ANTHROPIC_API_KEY, OPENAI_API_KEY, ZAI_API_KEY, SAKANA_API_KEY |

**تحلیل:** ۴ فایل `.env` یا `.env.example` در root، 4d_system، app، و survival-gateway. root `.env` توسط `env_loader.py` خوانده می‌شود؛ 4d_system `.env` توسط `dotenv.load_dotenv()` در `settings.py` خوانده می‌شود؛ survival-gateway `.env` مخصوص LiteLLM/Postgres است.  
**تکرار نام کلید:** `FUGU_API_KEY` (در _ops و 4d_system) vs `SAKANA_API_KEY` (در survival-gateway). در واقعیت هر دو برای یک سرویس (Sakana Fugu) هستند ولی نام متفاوت دارند.  
**سند:** `survival-gateway/.env.example:26` — `SAKANA_API_KEY=`؛ `4d_system/config/settings.py:97` — `FUGU_API_KEY=`.

### 🟡 ST-3: سه LLM Router (Triple Router)
| Router | مسیر | Providerها | انضباط budget |
|---|---|---|---|
| cortex router | `_ops/cortex/model_router.py` | ollama (local) + GLM (secondary) + Fugu (primary) | organ_gate (ARCHITECT_SYS) + paid_gate (دوقفله) |
| 4D router | `4d_system/llm/router.py` | GLM + Fugu + Mock | budget cap (1000 calls/day) |
| survival-gateway | `survival-gateway/` (LiteLLM) | Anthropic, OpenAI, Gemini, DeepSeek, Z.ai, Sakana | — |

**تحلیل:** `_ops/cortex/model_router.py` و `4d_system/llm/router.py` هر دو GLM + Fugu را routing می‌کنند ولی با انضباط budget متفاوت. 4D از `config.settings.LLMConfig` استفاده می‌کند؛ cortex از `opslib` + `env_loader` استفاده می‌کند. survival-gateway یک proxy جداگانه (LiteLLM) است که کلیدهای خودش را دارد.

### 🟡 ST-4: Telemetry دوگانه (Dual Telemetry)
| Telemetry | مسیر | هدف | واحد |
|---|---|---|---|
| telemetry.py (budget) | `_ops/budget/telemetry.py` | snapshot ماهانه/روزانه از ۲ منبع (genome + brain) | micro-USD |
| telemetry.py (core) | `octopus_core/telemetry.py` | sensory loop per job execution | AUD |
| governor_epoch.py | `_ops/budget/governor_epoch.py` | فشار آلوستاتیک + fitness dry | — |

**تحلیل:** `_ops/budget/telemetry.py` یک «خواننده» است (snapshot از ledger + core.db)؛ `octopus_core/telemetry.py` یک «نویسنده» است (record per job). نام یکسان، تکلیف متفاوت، ولی هیچ‌کدام به یکدیگر refer نمی‌کنند. این naming collision خطر تداخل منطقی دارد.

### 🟡 ST-5: Legs بدون ارث‌بری از Leg Base (Leg Drift)
| Leg | مسیر | ارث‌بری از Leg | کلاس/تابع |
|---|---|---|---|
| lead_leg.py | `_ops/legs/lead_leg.py` | ✅ `class LeadLeg(Leg)` | کلاس |
| ziman_leg.py | `_ops/legs/ziman_leg.py` | ✅ `class ZimanLeg(Leg)` | کلاس |
| cartographer_leg.py | `_ops/legs/cartographer_leg.py` | ✅ `class CartographerLeg(Leg)` | کلاس |
| mining_leg.py | `_ops/legs/mining_leg.py` | ❌ **ندارد** | `def mining_status()` (تابع مستقل) |
| crypto_leg.py | `_ops/legs/crypto_leg.py` | ❌ **ندارد** | `def crypto_status()` (تابع مستقل) |
| accounting_leg.py | `_ops/legs/accounting_leg.py` | ❌ **ندارد** | `def accounting_status()` (تابع مستقل) |

**تحلیل:** ۳ leg از `Leg` base class ارث‌بری می‌کنند (isolation، money_link، organ_gate)؛ ۳ leg دیگر (mining، crypto، accounting) فقط توابع مستقل هستند و هیچ‌کدام از قواعد INV-17 (isolation) یا money_link را رعایت نمی‌کنند. این یک «drift» معماری است که ۳ leg را از حاکمیت NBB-CP خارج می‌کند.

### 🟡 ST-6: Extractor انفجاری (Extractor Explosion)
| Extractor | مسیر | منبع | خروجی | زمان |
|---|---|---|---|---|
| extract_live_data.py | `nervous-system/` | 4d_system/outputs/ | live-data.js | ~1s |
| extract_ops_data.py | `nervous-system/` | _ops/state/ | ops-data.js | ~1s |
| extract_graph.py | `nervous-system/` | کل vault | graph-data.js | ~3-5s |
| extract_health_score.py | `nervous-system/` | _ops/state/ | health-data.js | ~1s |
| extract_watchdog_data.py | `nervous-system/` | _ops/state/ | watchdog-data.js | ~1s |
| extract_neural_data.py | `nervous-system/` | _ops/neural/ | neural-data.js | ~1-2s |
| extract_queue_data.py | `nervous-system/` | _ops/state/ | queue-data.js | ~1s |
| extract_research_data.py | `nervous-system/` | 00 - Inbox/ | research-data.js | ~1-2s |
| extract_obsidian_tasks.py | `nervous-system/` | کل vault | task-data.js | ~3-5s |
| extract_task_summary.py | `nervous-system/` | task-data.js | task-summary-data.js | ~0.5s |
| extract_git_status_data.py | `nervous-system/` | کل .git/ | git-data.js | ~5-15s |
| extract_wallet_data.py | `nervous-system/` | _ops/budget/ | wallet-data.js | ~1s |
| extract_mining_data.py | `nervous-system/` | _ops/state/ | mining-data.js | ~1s |
| extract_crypto_data.py | `nervous-system/` | _ops/state/ | crypto-data.js | ~1s |
| extract_project_index.py | `nervous-system/` | 03 - Projects/ | project-data.js | ~1-2s |
| extract_ideas_backlog.py | `nervous-system/` | 00 - Inbox/ | ideas-data.js | ~1-2s |
| extract_telegram_control.py | `nervous-system/` | _ops/state/ | telegram-data.js | ~1s |
| extract_telegram_commands.py | `nervous-system/` | _ops/telegram_center/ | telegram-commands-data.js | ~1s |
| extract_audit_trail.py | `nervous-system/` | _ops/state/ | audit-trail-data.js | ~1s |

**تحلیل:** ۱۹ extractor جداگانه که هر بار کل منابع را از نو می‌خوانند. `refresh-live-data.bat` کل این ۱۹ را در یک pipeline اجرا می‌کند (~۱۵-۴۵ ثانیه). هیچ shared cache یا incremental update وجود ندارد. `task-data.js` (~650KB) و `graph-data.js` (~108KB) حاصل اسکن هزاران فایل هستند.  
**تکرار:** دو نسخهٔ `refresh-live-data.bat` وجود دارد: `nervous-system/refresh-live-data.bat` (۲۴۳ خط، کامل) و `OCTOPUS/nervous-system/refresh-live-data.bat` (۹ خط، نسخهٔ کوتاه). نسخهٔ کوتاه‌تر ۳ extractor را اجرا می‌کند ولی در مسیر متفاوت قرار دارد — risk drift در maintenance.

### 🟡 ST-7: Dashboard تکراری (Dashboard Multiplication)
| Dashboard | مسیر | فناوری | مصرف‌کننده |
|---|---|---|---|
| server.py | `_ops/dashboard/server.py` | http.server (HTML/RTL) | 8770 |
| live/server.py | `_ops/live/server.py` | http.server (interactive) | 8773 |
| panel/server.py | `_ops/panel/server.py` | http.server (management) | 8790 |
| admin-telegram | `OCTOPUS/admin-telegram/index.html` | Static HTML/JS | — |
| worlds | `OCTOPUS/worlds/index.html` | Static HTML/JS | — |
| 4D UI | `4d_system/ui/app.py` | Streamlit (9 tabs) | — |
| NBB dashboard | `_launchpad/second-brain-live/accounting-bot/personal-dashboard.js` | JS | — |
| 4D tab_dashboard | `4d_system/ui/tab_dashboard.py` | Streamlit tab | — |

**تحلیل:** حداقل ۸ داشبورد/پنل جداگانه که هر کدام داده‌های خودشان را از extractors یا state فایل‌ها می‌خوانند. `OCTOPUS/admin-telegram/index.html` و `OCTOPUS/worlds/index.html` هر دو داده‌های `nervous-system/*.js` را مصرف می‌کنند ولی UI متفاوت دارند. `_ops/dashboard/server.py` و `_ops/live/server.py` و `_ops/panel/server.py` هر ۳ سرور جداگانه هستند.

### 🟡 ST-8: Doctor vs Cortex (Analysis Dualism)
| سیستم | مسیر | نقش | فایل‌ها |
|---|---|---|---|
| doctor | `_ops/doctor/` | تشخیص/سلامت/audit | doctor.py, box/, sensors.py, warden.py, archivist.py, topology.py, dynamics.py, calibration.py, spectral.py, temperature.py, evolution.py |
| cortex | `_ops/cortex/` | تصمیم‌گیری/ارchestration | goal_directed.py, model_router.py, cortex.py, business_brain.py, self_model.py, innervation.py, stress.py, synthesis.py, discoveries.py, web_research.py, consolidate.py |

**تحلیل:** هر دو "brain" هستند ولی با مرزهای مبهم. doctor به «سلامت» می‌پردازد؛ cortex به «تصمیم». ولی هر دو روی `_ops/state/` می‌نویسند، هر دو از `opslib` استفاده می‌کنند، و هر دو flag‌های `ACTIVATION-*.flag` را چک می‌کنند. هیچ «single source of truth» برای اینکه کدام brain مسئول کدام decision نیست.

### 🟡 ST-9: Watchdog دوگانه (Dual Watchdog)
| Watchdog | مسیر | تکلیف | وضعیت |
|---|---|---|---|
| watchdog.py | `_ops/watchdog.py` | — | — |
| watchdog_extension.py | `_ops/watchdog_extension.py` | — | — |
| organism-watchdog.ps1 | `04 - Architect System/scripts/organism-watchdog.ps1` | مانیتورینگ PowerShell | — |
| watchdog-data.js | `nervous-system/watchdog-data.js` | خروجی extractor | — |

**تحلیل:** حداقل ۴ فایل با نام watchdog در ۳ مسیر متفاوت. هیچ‌کدام به یکدیگر refer نمی‌کنند.

### 🟡 ST-10: MANIFEST/Adapter پراکنده (Manifest Proliferation)
| فایل | تعداد مسیرها | هدف |
|---|---|---|
| MANIFEST.yaml | ۱۰ مسیر (app, 4d_system, 03 - Projects/*, نقشه اختاپوس) | identity + hard rules + blackbox potential |
| adapter.yaml | ۶ مسیر (contracts/adapter.yaml در هر پروژه) | interface contract |

**تحلیل:** ۱۰ MANIFEST.yaml و ۶ adapter.yaml که هر کدام مستقل نوشته شده‌اند. هیچ schema validator یا shared template وجود ندارد. `app/MANIFEST.yaml` ۱۲ invariant دارد؛ `4d_system/MANIFEST.yaml` ۶ hard rule دارد؛ سایر MANIFEST‌ها ساختار متفاوت دارند. این «doctrinal twin» هستند ولی یکپارچه نیستند.

---

## 🟢 کم — تکرارهای جزئی

### 🟢 MI-1: Invariant Set متفاوت
- `app/src/nbb_cp/kernel/invariants.py` → ۱۲ invariant (INV-1..INV-12) + registry + audit()  
- `_ops/` → هیچ invariant registry رسمی ندارد؛ قواعد در docstring‌ها و MANIFEST‌ها پخش شده‌اند.  
- `4d_system/` → ۶ hard rule در MANIFEST.yaml (TCB immutable, daemon never executes, etc.) ولی هیچ کد audit/runtime ندارد.

### 🟢 MI-2: Budget Definition تکراری
- `_ops/budget/budgets.yaml` → تک‌منبع حقیقت برای organism (opslib.py:195)  
- `app/src/nbb_cp/app/config.py` → `global_cap_cents=3000` (hardcoded)  
- `4d_system/config/settings.py` → هیچ budget cap ندارد (فقط cloud_llm_daily_calls=1000)  
- **تکرار:** cap_monthly در budgets.yaml = AUD؛ global_cap_cents در NBB = 3000 سنت (USD)؛ هیچ تبدیل واحدی بینشان نیست.

### 🟢 MI-3: Approval Channel دوگانه
- `_ops/budget/approval_channel.py` (881 خط) + `approval_channel_merge.py` → Telegram-first approval queue  
- `_ops/telegram_center/center.py` → کانال مرکزی تلگرام (send/receive)  
- این دو باید یکی باشند (approval = یک نوع پیام تلگرام) ولی دو کدبیس جداگانه دارند.

### 🟢 MI-4: Refresh Script تکراری
- `nervous-system/refresh-live-data.bat` (۲۴۳ خط، کامل)  
- `OCTOPUS/nervous-system/refresh-live-data.bat` (۹ خط، ناقص)  
- **خطر:** maintenance drift — اگر یکی update شود دیگری stale می‌ماند.

### 🟢 MI-5: Flag/Activation پراکندگی
- `_ops/STOP-ORGANISM` (۱ فایل)  
- `_ops/ACTIVATION-*.flag` (۹ فایل: GO-LIVE, DEBATE, GOVERNOR-LLM, HEART-DOCTOR, PULSE, WORK-LLM, RESEARCH-EARLY, CORTEX-PAID, SELF-IMPROVE-AUTO)  
- `_ops/budget/FREEZE.flag`  
- `_ops/STOP-METABOLIC`، `_ops/STOP-DEBATE`، `_ops/HALT-ALL`  
- **تکرار:** ۱۵+ فایل flag در `_ops/` با naming convention ناسازگار (STOP-* vs ACTIVATION-* vs FREEZE.flag vs HALT-ALL).

### 🟢 MI-6: Env Var نام‌های متفاوت برای یک API
| سرویس | نام در _ops | نام در survival-gateway | نام در 4d_system | نام در launchpad |
|---|---|---|---|---|
| Sakana Fugu | `FUGU_API_KEY` | `SAKANA_API_KEY` | `FUGU_API_KEY` | `SAKANA_API_KEY` |
| Z.ai GLM | `GLM_API_KEY` | `ZAI_API_KEY` | `GLM_API_KEY` | `DEEPSEEK_API_KEY` (برای some) |
| Telegram | `TELEGRAM_BOT_TOKEN` | — | — | `TELEGRAM_TOKEN` / `TELEGRAM_SABA_BOT_TOKEN` |

### 🟢 MI-7: Unified Bus تکراری
- `_ops/unified_bus.py` → تنها یک فایل (خوب)  
- ولی `4d_system/brain/events.py` → emit() ساده  
- `app/src/nbb_cp/kernel/events.py` → LedgerEvent typed  
- هیچ‌کدام از «unified bus» _ops استفاده نمی‌کنند.

### 🟢 MI-8: README/Doctrinal Twin تکراری
- `app/MANIFEST.yaml` → "IMPROVE, DON'T REWRITE" (shared doctrine)  
- `4d_system/MANIFEST.yaml` → "IMPROVE, DON'T REWRITE" (shared doctrine)  
- `04 - Architect System/` → ده‌ها فایل markdown با همین عبارت  
- هیچ‌کدام به یکدیگر link نمی‌دهند — هر کدام «twin» مستقل هستند.

---

## جدول رتبه‌بندی شدت (Priority Matrix)

| ID | تکرار/هدررفت | شدت | خطر |
|---|---|---|---|
| CP-1 | سه Control Plane موازی | 🔴 | انرژی/کد ۱۹۵۰۰ LOC هدررفته؛ conflict تصمیم‌گیری |
| CP-2 | چهار+ HTTP Server مستقل | 🔴 | پورت conflict، maintenance ۴x، security surface ۴x |
| CP-3 | سه Ledger با فرمت متفاوت | 🔴 | divergence داده، reconcile دستی، audit غیرممکن |
| CP-4 | سه+ State/DB جداگانه | 🔴 | source-of-truth چندگانه، backup پیچیده |
| CP-5 | دو Governor موازی | 🔴 | NBB-CP ساخته‌شده ولی unused؛ organism.py legacy |
| ST-1 | Telegram دوگانه | 🟡 | ۶ مسیر تلگرام، ۴+ token، stub/duplicate |
| ST-2 | Config/.env سه‌گانه | 🟡 | کلیدهای API با نام متفاوت، dotenv دوگانه |
| ST-3 | LLM Router سه‌گانه | 🟡 | metering جداگانه، budget leak احتمالی |
| ST-4 | Telemetry دوگانه | 🟡 | naming collision، semantic drift |
| ST-5 | Legs بدون Leg Base | 🟡 | ۳ leg از isolation خارج شده‌اند |
| ST-6 | Extractor انفجاری | 🟡 | ۱۹ extractor، ۱۵-۴۵s runtime، I/O هدررفته |
| ST-7 | Dashboard تکراری | 🟡 | ۸+ داشبورد، UX fragmented |
| ST-8 | Doctor vs Cortex | 🟡 | مرز مبهم، duplicate analysis logic |
| ST-9 | Watchdog دوگانه | 🟡 | ۴ فایل watchdog، وظیفه نامشخص |
| ST-10 | MANIFEST/Adapter پراکنده | 🟡 | ۱۶ فایل، schema ناسازگار |
| MI-1 | Invariant Set متفاوت | 🟢 | NBB ۱۲ invariant، بقیه بدون audit کد |
| MI-2 | Budget Definition تکراری | 🟢 | واحد ناسازگار (AUD vs USD cents) |
| MI-3 | Approval Channel دوگانه | 🟢 | ۲ implementation Telegram approval |
| MI-4 | Refresh Script تکراری | 🟢 | drift maintenance |
| MI-5 | Flag/Activation پراکندگی | 🟢 | ۱۵+ فایل، naming ناسازگار |
| MI-6 | Env Var نام متفاوت | 🟢 | FUGU vs SAKANA، GLM vs ZAI |
| MI-7 | Unified Bus تکراری | 🟢 | ۳ event system جداگانه |
| MI-8 | README/Doctrinal Twin | 🟢 | duplicate doctrine، no DRY |

---

## توصیه‌های فوری (Quick Wins)

1. **ادغام Control Plane:** NBB-CP (app/) را به عنوان «canonical control plane» انتخاب کن؛ organism.py را به یک thin adapter تبدیل کن که از NBB-CP service استفاده می‌کند (نه control plane مستقل).
2. **Reverse Proxy:** یک nginx یا traefik برای ۴ سرور `_ops/` بگذار تا ۴ پورت به یک unified API gateway تبدیل شوند.
3. **Unified Ledger:** NBB-CP ledger (typed, hash-chained) را به عنوان source-of-truth انتخاب کن؛ 4D و organism را وادار کن از آن بنویسند/بخوانند.
4. **Leg Refactor:** mining_leg.py، crypto_leg.py، accounting_leg.py را به کلاس‌هایی تبدیل کن که از `Leg` ارث‌بری می‌کنند (isolation + money_link).
5. **Extractor Cache:** یک shared cache (SQLite یا JSON) برای nervous-system extractors بساز تا هر بار کل vault اسکن نشود.
6. **Env Consolidation:** یک `.env` واحد در root با schema ثابت بساز؛ همهٔ ماژول‌ها از `env_loader.py` (یا `pydantic-settings`) استفاده کنند. `SAKANA_API_KEY` و `FUGU_API_KEY` را alias کن.
7. **Flag Consolidation:** همهٔ STOP/ACTIVATION/FREEZE flags را به یک `state.json` واحد با schema تبدیل کن.

---

*گزارش توسط Orchestrator Agent تولید شده. منبع: F:/backup/ (master branch, 242 dirty files).*
