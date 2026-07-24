# OCTOPUS ACTUATION ALIGNMENT — اختاپوس از استعاره به کد واقعی

> وضعیت: v0.9 (post-UI-audit) · تاریخ: 2026-07-12  
> هدف: هیچ دکمهٔ مرده‌ای نماند؛ هر اندام یا کار می‌کند، یا صادقانه می‌گوید نمی‌تواند.

---

## ۱. نگاشت استعاره → نقش مهندسی

| استعارهٔ اختاپوس | نقش واقعی در سیستم | فایل/ماژول اصلی | وضعیت فعلی |
|---|---|---|---|
| **عقل ۱ (Goal/Policy)** | Goal arbiter، priority queue، approval logic، outward-lock | `langar_bot.py` (`SelfModel.outward_locked`)، `shadow.py`، `governance.py` | ✅ کار می‌کند — GATE 0 واقعی و fail-closed |
| **عقل ۲ (Learning/World-Model)** | Memory، evaluator، calibration، baseline manager، model/router selection | `learning.py` (`ThompsonBandit`)، `acquisition.py`، `archive/` | ⚠️ هسته موجود، ولی به action بیرونی وصل نیست — فقط read-only |
| **قلب ۱ (Truth/Observability)** | Telemetry، ledger، truth-cards، stale detection، provenance | `store.py`، `verify_ledger()`، `langar_log.jsonl`، `truth-cards/` | ✅ کار می‌کند — append-only، هر عدد تگ‌دار |
| **قلب ۲ (Energy/Resources)** | Budget، credits، tokens، rate limits، API quotas | `budget.py` (`CostMeter`)، `langar_bot.py` (`can_spend`) | ✅ کار می‌کند — fail-closed |
| **قلب ۳ (Execution/Actuation)** | Job dispatch، retries، backoff، circuit breakers، delivery confirmation | `runner.py`، `manager.py` (start/stop/test) | ⚠️ start/stop/test موجود، ولی **actuation به channel/API بیرونی ندارد** — همهٔ actionها propose-only یا sandboxed |
| **بازوها (Arms)** | Domain agents / workers with bounded autonomy + local sensing | `ziman-agent/worker.py`، `acquisition_pipeline.py`، `pf_admin.py` | ⚠️ propose-only — فایل می‌نویسند، ولی هیچ کدام به پلتفرم/دنیای واقعی پست/دی‌ام/پابلیش نمی‌کنند |
| **سیستم عصبی** | Event bus + correlation IDs + capability registry + health signals | ❌ **فاقد** — فقط file-based handoff (`.json`، `.md`) | 🔴 **gap اصلی** — هیچ event bus یا pub/sub نیست |
| **بادکش‌ها (Suckers)** | Tool adapters / API connectors / file-system & channel handlers | `telegram.py` (adaptor)، `urllib` raw در `langar_bot.py` | ✅ کار می‌کنند — ولی فقط read/write message، هیچ action اجرایی |

---

## ۲. UI Truthfulness Audit (کاکپیت‌ها)

### ۲.۱ لنگر (`langar_bot.py`) — ⚓

| کنترل | وضعیت قبل | اصلاح انجام‌شده | وضعیت فعلی |
|---|---|---|---|
| `/status` | ✅ کار می‌کرد | — | ✅ executable — truth-card واقعی |
| `/gates` | ✅ کار می‌کرد | — | ✅ executable — GATE 0 واقعی |
| `/verdicts` | ✅ کار می‌کرد | — | ✅ executable — از `THREAD-CLOSURE` می‌خواند |
| `/saba` | ✅ کار می‌کرد | — | ✅ executable — bridge read-only صادقانه |
| `/brief` | ✅ کار می‌کرد | — | ✅ executable — brain offline = 🔒 label |
| `/think` | ✅ کار می‌کرد | — | ✅ executable — heuristic + LLM fallback |
| `/upgrade` | ✅ propose-only | — | ✅ executable — فایل proposal می‌نویسد |
| `/rules` | ✅ کار می‌کرد | — | ✅ executable |
| `/kpi` | ❌ template fake | حذف از `/help` + پیام 🔒 صادقانه | ⚠️ **disabled-with-reason** — explicit: pre-launch + zero data |
| `/report` | ❌ template fake | حذف از `/help` + پیام 🔒 صادقانه | ⚠️ **disabled-with-reason** — explicit: SOP manual until post-launch |
| `/kill` / `/revive` | ✅ کار می‌کرد | — | ✅ executable — fail-safe file-based |

**قاعدهٔ اعمال‌شده:** هر کنترل یا executable واقعی است، یا صریحاً non-executable با دلیل.

### ۲.۲ استودیوی صبا (`saba_studio.py`) — 🎬

| کنترل | وضعیت | برچسب |
|---|---|---|
| `s:new` (ثبت درفت) | ✅ executable — دوکلیده | — |
| `s:drafts` | ✅ executable | — |
| `s:today` | ✅ executable — heuristic | — |
| `s:cal` | ✅ executable | — |
| `s:cap` | ✅ executable — write واقعی | — |
| `s:inbox` | ✅ executable — read + mark-read | — |
| `s:scope` | ✅ executable — boundary write | — |
| `s:rules` | ✅ executable | — |
| `s:brief` | ✅ executable — brain offline = 🔒 label | — |
| `s:trend` | ❌ not-wired | 🔒 **coming-soon** — در ADVANCED_MENU، نه MAIN |
| `s:ppv` | ❌ not-wired | 🔒 **coming-soon** — در ADVANCED_MENU |
| `s:stats` | ❌ not-wired | 🔒 **coming-soon** — در ADVANCED_MENU |
| `s:brief_ai` | ❌ brain not loaded | 🔒 **coming-soon** — در ADVANCED_MENU |

**نتیجه:** صبا قبلاً صادقانه بود — coming-soonها در منوی جداگانه قرار دارند.

---

## ۳. گپ آنالیز (Gap Analysis)

### ۳.۱ gap: سیستم عصبی (Event Bus) — 🔴 HIGH

| بخش | وضعیت فعلی | وضعیت مطلوب | risk |
|---|---|---|---|
| **correlation** | فقط filename + date در نام فایل | `correlation_id` + `trace_id` + `parent_id` | race condition در handoff، گم‌شدن causality |
| **health signals** | فقط `HALT` file + `KILL` file | heartbeat + latency + error-rate per arm | نمی‌توان تشخیص داد کدام بازو کند/مرده است |
| **capability registry** | implicit (کد hard-code) | dynamic registry با advertisement + revocation | UI نمی‌تواند runtime sync کند |
| **event bus** | فایل‌محور (polling) | pub/sub یا message queue lightweight | latency، race، stale read |

**راه‌حل پیشنهادی:** `event_bus.py` lightweight با `asyncio.Queue` یا حتی `watchdog` روی `F:/backup/.bus/` — بدون dependency خارجی.

### ۳.۲ gap: اجرا (Motor Cortex) — 🔴 HIGH

| بخش | وضعیت فعلی | وضعیت مطلوب | risk |
|---|---|---|---|
| **action بیرونی** | هیچ — propose-only | `actuator.py` با dry-run → live → confirm | موجود زنده ولی فلج؛ operator نمی‌تواند actuator را تست کند |
| **delivery confirmation** | فقط "file written" | end-to-end ack + retry + dead-letter | نمی‌دانیم آیا payload واقعاً رسیده یا نه |
| **circuit breaker** | فاقد | per-API / per-channel failure threshold | یک API down = کل pipeline down |

**راه‌حل پیشنهادی:** `actuator.py` با سه حالت: `shadow` (log-only) → `dry-run` (simulate) → `live` (needs approval). این همان motor cortex است.

### ۳.۳ gap: بازخورد ساخت‌یافته (Sensory Loop) — 🟡 MEDIUM

| بخش | وضعیت فعلی | وضعیت مطلوب | risk |
|---|---|---|---|
| **feedback از بازوها** | فقط exit-code/exception | structured telemetry: latency, cost, outcome, drift | نمی‌توان learning brain را calibration کرد |
| **stale detection** | فاقد | TTL + freshness check روی every truth-card | تصمیم بر اساس دادهٔ قدیمی |

### ۳.۴ gap: UI ↔ Capability Sync — 🟡 MEDIUM

| بخش | وضعیت فعلی | وضعیت مطلوب | risk |
|---|---|---|---|
| **dynamic render** | hard-code menu | read from capability registry | دکمهٔ جدید/مرده نیازمند deploy کد است |
| **disabled reason** | static string | dynamic: `disabled because CostMeter.can_spend()==False` | operator نمی‌فهمد چرا یک دکمه خاموش است |

---

## ۴. سطوح حساسیت (Sensitivity Ladder) — وضعیت فعلی

| سطح | تعریف | نمونه | مسئول |
|---|---|---|---|
| 🟢 **LOW** | نوشتن فایل خام، read-only query، shadow | proposal, log, truth-card, `/status` | swarm خودش |
| 🟡 **MEDIUM** | تغییر config محلی، ساخت فایل spec | `capacity.json`, `drafts.json`, SOP | swarm خودش |
| 🔴 **HIGH** | write به `F:/backup` (آرایش دائمی)، اقدام بیرونی، daemon start | publish, DM, payment, API live | **آری (فارسی)** |

**وضعیت فعلی:** هیچ action در swarm به 🔴 نمی‌رسد — همه propose-only یا sandboxed. این feature است، نه bug.

---

## ۵. تصمیم‌های معماری برای v-next

1. **ساخت `event_bus.py`** — priority: 🔴 HIGH  
   → `F:/backup/.bus/` directory با JSONL per topic. Polling-based فعلاً کافی.

2. **ساخت `actuator.py` (motor cortex)** — priority: 🔴 HIGH  
   → حالت shadow/dry-run/live. فقط `/test` واقعی (no side-effect) → `/live` نیازمند approval.

3. **Capability Registry** — priority: 🟡 MEDIUM  
   → `capabilities.json` که هر ماژول در startup خودش را advertise کند. UI در render time می‌خواند.

4. **Dynamic Disabled Reason** — priority: 🟡 MEDIUM  
   → هر control قبل از render، `can_execute()` را چک کند و دلیل را نشان دهد.

5. **Sensory Loop Structured** — priority: 🟡 MEDIUM  
   → هر worker بعد از job، `telemetry.jsonl` بنویسد: `{job_id, duration, cost, error, outcome}`.

---

## ۶. فلسفهٔ نهایی

> «اختاپوس را از یک استعارهٔ زیبا به یک ارگانیسم اجرایی تبدیل کن؛ هر بازو باید حس کند، تصمیم محلی بگیرد، و فقط وقتی به مرکز گزارش دهد که چیزی برای تصمیم‌گیری سطح بالاتر لازم است.»

وضعیت فعلی: **observability و truth-cards زنده‌اند، actuation فلج است.**  
گام بعدی: **motor cortex wiring** (actuator + event bus + capability registry).
