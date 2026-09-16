---
type: knowledge
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
tags: [octopus, deep-scan, fix, phi-accrual, flag-drift, shadow-eval, evolution, gateway, evidence-grounded]
created: 2026-08-08
updated: 2026-08-08
created_by: agent
sources:
  - "دیپ‌اسکنِ کامل روی دیسک، ۲۰۲۶-۰۸-۰۸ ~۱۶:۰۰–۱۶:۴۵ — هر ادعا با کدِ زنده / فایلِ raw بررسی شد"
  - "سه فیکس روی chrono.py + evolution.py + doctor.py — هرکدام با تستِ سبز و چکِ رگرشن"
  - "تفسیرِ علتِ واقعیِ هر مشکل، مستقل از هشدارِ گاورنر"
---

# دیپ‌اسکن + سه فیکسِ ریشه‌ای — ۲۰۲۶-۰۸-۰۸ (عصر)

> **هدف:** اختاپوس ۵–۸ ساعت زنده بود. این نوت نتیجهٔ یک دیپ‌اسکنِ کامل و سه فیکسِ
> ریشه‌ای است که در همان جلسه انجام شد. هر فیکس با TDD (تست قرمز → سبز) زده شد و
> تست‌های موجود برای چکِ رگرشن اجرا شدند.

## روش

هیچ هشدار یا گزارشی باور نشد. هر سنجه مستقل از فایل‌های raw خوانده شد:
`events.jsonl`, `ORGANISM-STATE.json`, `flags-loaded-*.json`, `selfheal-events.jsonl`,
`paid-calls.jsonl`, `synthesis-latest.json`, `upgrades-digest.json`.
کدِ زنده اجرا شد (`flag_drift.load_shortfall()`, `parse_flags_file()`, پروسه‌ی والدِ gateway).

## وضعیتِ کلیِ سیستم (snapshot)

| سنجه | مقدار | وضعیت |
|------|-------|-------|
| ضربان قلب | 900s | 🟢 |
| هم‌آهنگی مغز | ۸۹٪ | 🟢 |
| استرس موجود | ۰.۳۸ | 🟢 آرام |
| خرج امروز | AU$0.00 | 🟢 |
| مدارک سند | ۹۷.۷٪ | 🟢 |
| gateway miniapp | up + tunnel up | 🟢 |

**نتیجهٔ اصلی (صادقانه):** ۹۶٪ نرخ پذیرشِ پیشنهادها، ولی `attribution.claimed` هنوز
صفر است. مغزها خوب کار می‌کنند ولی هنوز هیچ لید/اتریبیوشن واقعی‌ای ثبت نشده.

---

## فیکس ۱: سقوطِ ۲۳۶ فلگِ gateway — علتِ واقعی، نه LF

### ادعای گاورنر
«فروپاشیِ پیکربندیِ سرِ boot: ۲۳۶ از ۲۳۷ فلگ به env نرسید (۱۰۰٪). علتِ محتمل: LF.»

### راستی‌آزمایی
- فایل `OCTOPUS-flags.cmd` را با `od -c` بررسی کردم: **CRLF است** (۱۱۹۳ خط `\r\n`، صفر lone-LF). علتِ LF **غلط** بود.
- snapshot‌های per-process را خواندم: چهار پروسهٔ اصلی (organism/center/cortex/live) همگی ۲۴۴ فلگ داشتند، `alarm=False`. فقط **miniapp-gateway** با ۷ فلگ `alarm=True`.
- پروسهٔ والدِ gateway را با `Win32_Process.ParentProcessId` گرفتم: **یک bash command از یک sessionِ قبلیِ ZCode** بود — `cd _ops && OCTOPUS_TG_MINIAPP=1 python ... &` بدونِ source‌کردنِ `OCTOPUS-flags.cmd`.

### علتِ واقعی
gateway با دستورِ دستیِ یک sessionِ قبلی بالا آمده بود، نه با `RESTART-PROCESS.ps1`. هیچ ربطی به LF یا PowerShell نداشت. هر دو اسکریپتِ PowerShell فیکسِ پارسِ `OCTOPUS-flags.cmd` را داشتند (۰۸-۰۵ و ۰۸-۰۶).

### فیکس
`RESTART-PROCESS.ps1 gateway` → pid 18632 (۷ فلگ) کشته، pid 2136 (۲۴۴ فلگ) بالا آمد.
`alarm=False`. gateway سالم HTTP 200 روی `/` و `/miniapp`.

---

## فیکس ۲: لوپِ ری‌استارتِ lead-naghshi — تاریخچهٔ ack مسموم

### علامت
lead-naghshi در سه beatِ پشت‌سرِهم failed شد (phi ۱۹.۸ → ۲۵.۶ → ۳۱.۹) با وجودِ restart در هر بار. خودِ فایلِ failure نوشته بود: «restart علت را برطرف نمی‌کند — تاریخچهٔ ack مسموم است.»

### علتِ ریشه‌ای (در کد)
`restart_from_known_good()` در `doctor.py:809` فقط `leg.state = "alive"` و `leg.hlc = (0, 0)` را ریست می‌کرد. ولی `PhiAccrual.arrivals` (تاریخچهٔ فاصلهٔ ackها، `deque(maxlen=20)`) را دست نمی‌زد. پس beatِ بعد phi را از همان arrivalsِ مسموم محاسبه می‌کرد → leg بلافاصله دوباره failed → restart بعدی → همان لوپ.

### فیکس کد (`_ops/chrono.py`)
۱. متدِ `PhiAccrual.reset(t_ms=None)` اضافه شد: arrivals را پاک + اختیاری یک ackِ تولدِ تمیز.
۲. در `beat_once`، بعد از `restart_from_known_good(leg, self.db)`، حالا `acc.reset(self._clock())` صدا زده می‌شود. یعنی بعد از restart، پنجرهٔ bootstrapِ تمیز شروع می‌شود (phi=0 تا ۲ ackِ جدید).

### تست
- `test_phi_reset_on_restart.py` (جدید): ادعا می‌کند بعد از restart، beatِ بعد leg زنده می‌ماند (نه failed) و دوباره restart نمی‌شود. **سبز.**
- `test_leg_failure_reason.py` (موجود): بدون رگرشن. **سبز.**

### پاکسازی
فایلِ stale `state/legs/lead-naghshi-last-failure.json` (phi=38.97 از ۱۴:۴۸) حذف شد — یک «شاهدِ مرگِ قدیمی» که lead-naghshi از ۱۶:۳۱ زنده بود.

---

## فیکس ۳: shadow-eval واقعی به‌جای stub — up-1363aae4df

### زمینه
deep-synth (فکرِ عمیقِ مغز) این P0 را ۳ بار به‌عنوان اولویتِ اول انتخاب کرد: «`measured_lift._default_eval` هنوز stub است؛ بنابراین وصل‌کردنِ apply_merge یا تکمیلِ self-analysis loop می‌تواند تغییرِ بدون سنجشِ واقعی را ارتقا دهد.»

کشفِ مهم: `apply_merge` **قبلاً وصل شده بود** (`doctor.py:1075`) — وقتی verdictِ merged از تلگرام می‌آید و `OCTOPUS_WIRE_APPLY_MERGE=1` است. پس `up-86a2454554` انجام‌شده بود. تمرکز روی `up-1363aae4df` ماند.

### باگِ ریشه‌ای (در کد)
`_default_eval` در `evolution.py:143` یک **stub** بود — فقط `severity` را به یک عدد تبدیل می‌کرد (`critical→0.5, high→0.3, ...`). هیچ regression را نمی‌دید. یک RFCِ critical همیشه lift=0.5 می‌گرفت حتی اگر suite را می‌شکست. این یعنی tournament_rank می‌توانست یک تغییرِ مخرب را به‌عنوان برنده انتخاب کند.

### فیکس کد (`_ops/doctor/evolution.py` + `_ops/doctor/doctor.py`)
۱. `measured_lift` حالا `suite_fn` قابل‌تزریق می‌پذیرد: `(rfc) → {pass, total, baseline_pass}`.
۲. `_default_eval` اگر `suite_fn` داشته باشد، **suite-delta واقعی** محاسبه می‌کند: `lift = (pass_candidate − pass_baseline) / total`. منفی = regression → drop.
۳. اگر `suite_fn` نباشد، fallback به severity تخمینی برمی‌گردد ولی صادقانه stub-label می‌شود (`"stub estimate: severity=... (no suite_fn)"`) — نه ادعای «measured».
۴. `backward-compat`: eval_fn (اگر داده شود) همیشه ارجح است؛ eval_fn‌های قدیمی با امضای `(rfc, baseline)` همچنان کار می‌کنند.
۵. `doctor.py`: slot `_suite_fn` به `__init__` اضافه شد + `_evolve_rfc` آن را به `measured_lift` تزریق می‌کند.

### تست
- `test_suite_delta_eval.py` (جدید، ۷ ادعا): regression شناسایی می‌شود، fixِ بی‌تأثیر lift=0، fixِ بهبودیافته lift>0، fallback صادقانه، suite_fn به eval می‌رسد، eval_fn ارجح است، stdlib-only. **همه سبز.**
- `test_evolution.py` (موجود، ۲۰ ادعا): **سبز** — رگرشن نیست.
- `test_p0_security_fixes.py` (۱۰/۱۰) + `test_merge_applies_knob.py` (۹/۹): **سبز**.

---

## 📝 کارِ انجام‌شده در این جلسه

| فایل | تغییر |
|------|-------|
| `_ops/chrono.py` | `PhiAccrual.reset()` + ریست بعد از restart |
| `_ops/doctor/evolution.py` | `suite_fn` قابل‌تزریق + fallback صادقانه |
| `_ops/doctor/doctor.py` | `_suite_fn` slot + تزریق در `_evolve_rfc` |
| `_ops/tests/test_phi_reset_on_restart.py` | **نو** — تستِ لوپِ ری‌استارت |
| `_ops/tests/test_suite_delta_eval.py` | **نو** — تستِ suite-delta واقعی |
| `_ops/state/legs/lead-naghshi-last-failure.json` | حذف (stale) |
| gateway | ری‌استارت با فلگ‌های کامل (pid 18632→2136) |
| organism | ری‌استارت با کدِ تازه (این جلسه) |

## درسِ کلیدی

سه مشکلِ این جلسه یک الگوی مشترک داشتند: **علتِ ادعا‌شده (LF، ری‌استارتِ ناکافی، stubِ بی‌خطر) با علتِ واقعی متفاوت بود.** در هر سه، باید زیرِ هشدار را خواند و کد را اجرا کرد:

۱. گاورنر گفت «LF» ولی فایل CRLF بود — علت، دستی‌بالا‌آمدنِ gateway بود.
۲. self-heal گفت «دوباره راه‌انداختم» ولی علت (arrivalsِ مسموم) سرِ جایش ماند.
۳. deep-synth گفت «eval stub است» و درست گفت — ولی stub فقط severity بود و هی regression نمی‌دید.

**توصیهٔ صریح به ایجنتِ بعدی:** سه ناحیهٔ زیر حالا قابلِ اعتمادترند ولی هنوز پشتِ
فلگ‌اند و نیاز به **تغذیهٔ واقعی** دارند:
- `suite_fn` در doctor هنوز `None` است در production (هیچ suite-runnerای تزریق نشده).
  وقتی `OCTOPUS_WIRE_EVOLUTION=1` روشن شود، `_evolve_rfc` به fallback برمی‌گردد تا یک
  suite-runner واقعی به `_suite_fn` وصل شود. این قدمِ بعدی است.
- `_default_eval` مسیرِ suite-delta را دارد ولی به یک harness واقعی نیاز دارد
  (مثلاً اجرای subsetی از `tests/run_all.py` در sandbox).
- lead-naghshi لوپ را شکستیم ولی علتِ اصلیِ «چرا ack نمی‌داد» (phi بالا با silence
  کم) هنوز بررسی نشده — فقط تاریخچه پاک شد.

---

## فازِ کنترل‌پنل (Miniapp Gateway 8774) — ارتقا + تستِ کامل

### ممیزیِ معماری
گیت‌وی یک `ThreadingHTTPServer` روی `127.0.0.1:8774` است با این سطح‌ها:
- **۴ مسیر static** (بدون auth): `/`, `/miniapp`, `/miniapp/app.js`, `/miniapp/style.css`
- **۱۹ مسیر read API** (با owner-auth HMAC): `/api/state` تا `/api/agent-log`
- **۳ مسیر POST** (با owner-auth + rate-limit): `/api/actions`, `/api/ask`, `/api/mirror`
- **proxy** به 8773: فقط `/api/miniapp` (timeout 8s)
- **kill-switch**: فایل `STOP-MINIAPP` → 503

### سه فیکسِ کارایی (miniapp_gateway.py)

| گپ | فیکس |
|----|------|
| `OpsActionEngine.execute` بدون timeout — اگر DB هنگ کند، thread تا ابر باز می‌ماند | `_run_with_timeout(eng.execute, ACTIONS_TIMEOUT_S=15s)` → 504 در انقضای مهلت |
| `ask_vault.query` و `ask_brain.ask` بدون timeout — LLM hang = request hang | `_run_with_timeout(ask_*, ASK_TIMEOUT_S=60s)` → 504 با `reason: vault_timeout`/`brain_timeout` |
| `mirror_room.ask` بدون timeout | `_run_with_timeout(mirror_room.ask, MIRROR_TIMEOUT_S=45s)` → 504 |
| `_log_hit` فقط `/api/miniapp` را authed می‌شمرد — بقیه‌ی ۱۹ مسیر هم auth دارند ولی `authed=false` ثبت می‌شد | حالا هر `/api/*` با ۲xx = `authed=true` |

`_run_with_timeout` یک thread-based timeout است (daemon=True) که در `_log_hit` اضافه شد. تستِ مستقیم: تابعِ سریع فوراً برمی‌گردد، `time.sleep(5)` با timeout 0.5s → `TimeoutError`.

### نتایجِ تست

**Functional (baseline + بعد از تغییرات):**
- همه‌ی ۱۳ read endpoint با auth: **200** ✅
- همه‌ی ۴ static endpoint: **200** ✅
- بدون auth: **403** ✅
- method اشتباه: **405** ✅
- مسیر ناموجود: **404** ✅
- body >64KB: **413** ✅
- هیچ رگرسنی پس از تغییرات.

**Security:**
- replay با auth_date منقضی (۱ ساعت پیش): **403** ✅
- hash دستکاری‌شده: **403** ✅
- user ID غیرمالک: **403** ✅

**Soak ۱۰ دقیقه (probe هر ۵s):**
- **۶۳۰ probe، ۶۳۰ موفق، ۰ شکست — ۱۰۰٪ نرخ موفقیت** ✅
- کندترین endpoint: `/api/ask` (avg ۱۲s، p95 ۴۶s — LLM محلی qwen2.5)
- سریع‌ترین: `/api/current-truth` (avg ۸ms)

**Soak ۳۰ دقیقه (probe هر ۸s):**
- **۱۸۱۸ probe، ۱۸۱۸ موفق، ۰ شکست — ۱۰۰٪ نرخ موفقیت** ✅
- `/api/ask` بهبود یافت: avg از ۱۲s به ۹.۳s (cache گرم شد)

**Leak detection (memory/handles/threads):**
| زمان | Working Set | Handles | Threads |
|------|-------------|---------|---------|
| baseline (۰m) | 37 MB | 142 | 4 |
| بعد از ۱۰m (۶۳۰ req) | 42.7 MB | 140 | 4 |
| بعد از ۴۰m (۲۴۴۸ req) | 42 MB | 144 | 4 |

**هیچ memory/handle/thread leak‌ای نیست.** Working Set تثبیت شد، Handles ثابت، Threads همیشه 4 (timeout wrapperها daemon=True به‌درستی cleanup می‌شوند).

**Soak ۱۲۰ دقیقه:** در حال اجرا (نتایج در `_ops/state/soak-120m.json`).

### فایل‌هایِ این فاز
- `_ops/telegram_center/miniapp_gateway.py` — ۳ timeout wrapper + authed tracking fix
- `_ops/tests/soak_gateway.py` — **نو** — soak runner با auto-refresh initData

### ⚠️ یافته‌ی بحرانی — باگِ ProgrammingError در /api/actions (فیکس شد)

این مهم‌ترین کشفِ تست‌هایِ واقعی بود. **soak test‌ها ۱۰۰٪ سبز بودند ولی هیچ write‌ای
از gateway کار نمی‌کرد** — دقیقاً همان دلیلی که مالک گفت «تست روی اتفاقاتِ واقعی، نه
فقط بالابودن».

**علت:** فیکسِ timeout-wrapper من (`_run_with_timeout`) action‌ها را در **thread جدا**
اجرا می‌کند. ولی SQLite connection‌ها به‌طور پیش‌فرض `check_same_thread=True` دارند — یعنی
امکان استفاده در thread دیگری را نمی‌دهند. وقتی gateway یک `lead.create` می‌گرفت،
`OpsActionEngine.execute` در threadِ timeout اجرا می‌شد و `IdempotencyStore` (که در
`runtime.py` ساخته می‌شود) `ProgrammingError` پرتاب می‌کرد. gateway این را `500 ERROR`
می‌گرداند ولی از بیرون endpoint «سالم» به‌نظر می‌رسید چون ۲۰۰/۴۰۳ می‌داد.

**soak test چرا نگرفتش؟** چون soak فقط status code را چک می‌کرد نه محتوای پاسخ را.
`/api/ask` در soak `200` برمی‌گرداند چون `{"ok":false}` هم `200` است. ولی `/api/actions`
در soak تست نشده بود با write واقعی. **درس:** soak فقط پایداریِ اتصال را ثابت می‌کند،
نه صحتِ منطق را.

**فیکس:** سه SQLite connection در `runtime.py` و `ops_actions.py` را `check_same_thread=False`
کردم (`IdempotencyStore`، `OutboundEffectStore`، `OctopusOpsDB`). WAL mode + این پرچم،
استفاده‌ی امن از چند thread را ممکن می‌کند. بعد از فیکس، کلِ زنجیره‌ی ارزش کار کرد:

| عمل | نتیجه |
|------|--------|
| lead.create | APPLIED ✅ |
| lead.add_note | APPLIED ✅ |
| lead.update_stage | APPLIED (new→warm) ✅ |
| task.create | APPLIED ✅ |
| value.record_event | APPLIED ✅ |

همه از gateway → DB با شاهدِ مستقیم.

### doctor cycle هم تست شد
`doc.run_cycle(beat=999, trace={'errors_24h':3})` یک RFC واقعی ساخت:
`RFC-dbb5c2cd` («۳ خطا در ۲۴ ساعت»، status: submitted-no-channel) و در
`knowledge/internal/` و `rfcs.json` ثبت شد.

---
