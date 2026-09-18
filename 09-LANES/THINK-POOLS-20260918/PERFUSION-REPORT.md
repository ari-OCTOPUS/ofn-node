# PERFUSION REPORT — فاز ۰ و ۱ (آنژیوگرافی و تشخیص)

اجرای `PERFUSION-DEBUG-MEGAPROMPT.md`. همه‌چیز فقط-خواندنی.
شاهد خام: `evidence/PERFUSION-PROBE.json` · `evidence/PHASE-C-CLASSIFICATION.txt`
پروب: `tools/perfusion_probe.py` (۱۳۸، 2026-09-18T01:33Z)

## جواب کوتاه به سوال مالک: **نه، خون به همهٔ رگ‌ها نمی‌رسد.**

۸۰ یونیت octopus روی ۱۳۸ وجود دارد (۶ running، ۳۷ waiting/تایمر، ۳۷ dead).
۲۲ اندامِ دارای state اندازه‌گیری شد. نتیجه: **استخر قوی ساخته شده ولی به
اندام‌ها وصل نیست**، و دو اندامی که وظیفه‌شان «فکر کردن» است **۶۵ ساعت است
خشک‌اند**.

## جدول اندام × رگ

وضعیت: `PERFUSED` خون می‌رسد · `BLOCKED` رگ بسته با عامل مشخص ·
`ATROPHIED` اندام هست ولی هیچ‌وقت تغذیه نشده · `DORMANT` عمداً خاموش · `UNKNOWN`.

| اندام (state) | رگِ تلمتری | رگِ مغز | رگِ داده | رگِ رسید | رگِ محاسبه | حکم |
|---|---|---|---|---|---|---|
| **revenue-drive** (پول) | ✅ تایمرها | UNKNOWN | ✅ ۱۲۱ نوشتن/۲۴h | ✅ | ❌ | **PERFUSED** (مسیر پول زنده) |
| **autonomy** | ✅ supervisor running | UNKNOWN | ✅ ردیف 01:32Z | ✅ | ❌ | **PERFUSED** |
| **glass (حلقهٔ مالک)** | ✅ `octopus-glass.timer` هر ۱ دقیقه | – | ✅ ولی در `revenue-drive/tg-inbox.jsonl` | ✅ | ❌ | **PERFUSED** (با drift مکانی) |
| **fleet-compute** | ✅ دو تایمر | – | ✅ ۲۷ نوشتن/۲۴h | ✅ | ✅ خودش رگ است | **PERFUSED** |
| eti-telemetry | ✅ | – | ✅ ۵۴۰/۲۴h | – | – | **PERFUSED** |
| deep-scan | ✅ | ❌ | ✅ 00:35Z | ✅ | ❌ | **PERFUSED** (بی‌مغز) |
| ops-agent | ✅ | ❌ | ✅ 0.1h | ✅ | ❌ | **PERFUSED** |
| owner_dialogue | ✅ | – | ✅ 00:57Z | ✅ | ❌ | **PERFUSED** |
| self-model | ✅ | ❌ | ⚠️ ۱ نوشتن ۰.۸h | ✅ | ❌ | **PERFUSED** (نازک) |
| receipts / shadow-verify / evidence | ✅ | – | ✅ | ✅ | – | **PERFUSED** |
| coding-worker | ✅ | ⚠️ llama180 (کد) | ⚠️ ۲ نوشتن | – | ❌ | **PARTIAL** |
| fleet-jobs | ✅ | – | ✅ 0.4h | ⚠️ غیر-durable | ❌ | **BLOCKED** (باس قابل بازپخش نیست) |
| fleet-scheduler | ✅ heartbeat | ⚠️ t3:8193 | ❌ لجر ۰۹-۱۵ یخ | ✅ | ❌ | **BLOCKED** |
| **api-budget (استخر قوی)** | ✅ پروب ساعتی | – | ❌ **لجر ۵۱ ساعت یخ** | ✅ | ❌ | **BLOCKED** |
| **cognition** | ❌ **هیچ تایمری ندارد** | ⚠️ llama180 (کد) | ❌ **۰ نوشتن/۲۴h، ۶۵h** | – | ❌ | **ATROPHIED** |
| durability | ❌ | – | ❌ ۶۵h | – | – | **ATROPHIED** |
| fleet-memory | ❌ | – | ❌ ۴۰h | – | – | **ATROPHIED** |
| fleet-nodes | ❌ | – | ❌ ۴۶.۷h | – | – | **ATROPHIED** |
| state/glass | ❌ (تایمرش جای دیگری می‌نویسد) | – | ❌ ۴۲.۵h | ⚠️ ۰۹-۱۶ | – | **ATROPHIED** (مسیر جایگزین‌شده) |
| of-draft-queue | ❌ | – | ۴۲.۴h | – | – | **DORMANT** (O4 فقط مرورگر مالک) |

## رگِ مغز — چه کسی واقعاً «فکر» را صدا می‌زند؟

فقط **۱۵ فایل** در کل درخت به یک پروایدر وصل‌اند:

| مسیر | نشانه |
|---|---|
| `ofn/adapters/remote_brain.py` | هستهٔ remote_brain |
| `ofn/helpers/brainport.py` | می‌خواند `BRAIN_PROVIDER` را |
| `ofn/adapters/{self_model_producer,trend_sources}.py`, `ofn/assistant_update.py`, `ofn/config.py`, `ofn/run.py` | مصرف‌کننده‌های remote_brain |
| `state/api-budget/{api_budget,provider_failover,providers}.py` | سمت رجیستری/بودجه |
| `state/{coding-worker/coding_worker,cognition/cognition_factory}.py` | llama180 |
| `state/fleet-scheduler/{capaware_scheduler,pb4_test}.py` | t3:8193 |

**یافتهٔ تلخ:** `think_pool` (طبقه‌بندِ صادق + رجیستری که امروز ساختم و ۱۹/۱۹
تست دارد) **صفر مصرف‌کننده** دارد. یعنی خون ساخته شده، رگ وصل نشده.

## چهار انسدادِ اصلی (عامل مشخص)

1. **رگِ مغز به پروایدرِ مُرده pin است** — `BRAIN_PROVIDER=fugu` و
   sakana-fugu در طبقه‌بندی صادق `EXHAUSTED` است (شاهد: `429 usage_limit_reached`).
   عامل: `routing`.
2. **دو اندامِ فکر، خشک** — `cognition` و `fleet-scheduler` هیچ تایمر فعالی
   ندارند و لجرهایشان ۶۵ و ۳ روز یخ است. عامل: `wiring`.
3. **لجر بودجه نیمی نام‌دار نیست و ۵۱ ساعت یخ است** — ۴۹.۴٪ ردیف‌ها
   `provider: unknown`. عامل: `wiring` + `budget`.
4. **مدل رایگان روی ۱۸۰ هیچ‌جا مسیریابی نمی‌شود** (فقط در کدِ
   `coding_worker`/`cognition_factory` دیده می‌شود، آن هم اندام‌های
   خشک). عامل: `routing`.

## ASK-REGISTER (هر سوال با یک کلمه جواب می‌گیرد)

| # | سوال | گزینه‌ها | پیشنهاد من |
|---|---|---|---|
| Q1 | چهار اندامِ خشک (`cognition`, `durability`, `fleet-memory`, `fleet-nodes`) را دوباره تایمر بزنیم یا بایگانی کنیم؟ | `restart` / `archive` | `restart` برای cognition و durability؛ `archive` برای fleet-memory/fleet-nodes (جانشینشان fleet-compute است) |
| Q2 | مسیریابی مغز خودکار از رجیستری تبعیت کند (دیگر روی پروایدر مُرده pin نماند)؟ | `auto` / `pin` | `auto` + امکان pin دستی برای بازتولید |
| Q3 | ستون پروایدر در لجر **اجباری** شود (ردیف بدون نام پروایدر ثبت نشود)؟ | `enforce` / `warn` | `enforce` |
| Q4 | برای کار حجمی، مدل رایگانِ محلی روی ۱۸۰ اول بیاید؟ | `yes` / `no` | `yes` (هزینه صفر، در رجیستری `paid:false`) |
| Q5 | سقف روزانهٔ هر پروایدر برای شروع چقدر؟ | عدد | همان `canary_cap_usd_per_provider: 0.25` که _meta ثبت کرده |
| Q6 | سهم ۵۰٪ لپ‌تاپ الان فعال شود یا بعد از PASS شدن کاناری ۲۴ساعته؟ | `now` / `after` | `after` (کاناری ۱۵ کار موفق، ۲ شکست صادقانه؛ تا تکمیل پنجره صبر) |

## وضعیت کاناری (همان‌زمان)

`fleet-compute`: ۱۵ SUCCEEDED · ۲ FAILED_FINAL (باگ SIGTERM که رفع شد) ·
۳ CANCELLED · ۱ PARKED. ارزیابی نهایی بعد از پنجرهٔ ۲۴ ساعته با
`canary_acceptance.py --since 2026-09-18T01:00:00Z`.

## فاز ۲ (پروپوزال اصلاح — بدون اجرا تا GO)

- **P1 (routing):** `brainport.py` + `remote_brain.py` را به `think_pool.routing_order`
  وصل کن؛ `BRAIN_PROVIDER` فقط به‌عنوان pin دستی بماند. تست جفتی: پروایدر
  EXHAUSTED هرگز انتخاب نشود؛ رایگان اول بیاید.
- **P2 (wiring):** تایمر برای `cognition` (Q1) با پاکت cgroup مثل بقیه.
- **P3 (budget):** ثبت اجباری پروایدر + سقف per-provider (Q3/Q5).
- **P4 (compute):** مصرف‌کنندهٔ واقعی برای برد‌های خالی (شارد تست/ایندکس) —
  همان فاز ۳ مگاپرامپت اصلی.
