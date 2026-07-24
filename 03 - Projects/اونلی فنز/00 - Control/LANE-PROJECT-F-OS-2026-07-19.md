---
type: reference
status: active
tags: [octopus, coordination, lanes, parallel-agents, projectf, pf_os]
created: 2026-07-19
updated: 2026-07-19
---

> ## 📊 UPDATE نهایی 2026-07-19 (پایان فازها)
>
> **وضعیت: همه فازها ۰-۷ کامل.** pf_os به‌عنوان یک OS مستقلِ کامل ساخته شد.
>
> | محور | مقدار |
> |------|-------|
> | فایل‌های pf_os/ | ۱۷ (۱۲ `.py` + ۵ `test_*.py` + `RUNBOOK.md`) |
> | خطوط کد | 3294 |
> | تست‌های سبز | **۳۲۸** (کل suite + ۳۸ characterization + singleton + learning + bridge + api + loop) |
> | تستِ مشترک | `test_dual_brain.py` ۹/۹ سبز (نشکست) |
> | Flags | ۴ (همه default-OFF) |
> | Dependencies جدید | **صفر** (stdlib-only) |
>
> **فایل‌های pf_os/:**
> `config, cortex_client, events, brain, saba_link, learning_bus, singleton,
>  bridge, bridge_beat, api, loop, run_saba` + ۵ فایل تست + RUNBOOK.md
>
> **چه ساخته شد:**
> - فاز ۰.۱: رفع باگِ امنیتیِ compliance-bypass در `orchestrator.py:104` (manifest-driven)
> - فاز ۰.۲: رفع ۱۳ تستِ قرمز (علتش `STOP-ORGANISM` بود، نه bug)
> - فاز ۱: package هسته (config/cortex_client/events)
> - فاز ۲: BrainCore + saba_link (پلِ من↔صبا) + ۳۸ characterization test
> - گپ‌های توصیه‌ی ایجنتِ کل: singleton-guard + LearningBus (ThompsonBandit reuse)
> - فاز ۳: حلقه‌ی tick مستقل
> - فاز ۴: REST API با ExclusiveHTTPServer (الگوی organism.py)
> - فاز ۵A: bridge.py (writer به organism)
> - فاز ۵B: bridge_beat.py (consumer-side، آماده‌ی integration در wiring.py وقتی لینِ قلب تمام شد)
> - فاز ۷: RUNBOOK + این update
>
> **کشفِ مهم:** نشتِ PII «آری» در خروجیِ `dual_brain_v3` پیدا و در تستِ characterization
> قفل شد (`test_output_known_leaks_documented`). pf_os در عمل با scrub این را فیلتر می‌کند.
>
> **گزارشِ کامل برای ایجنتِ کل:** `01 - Dashboard/PF-OS-FINAL-REPORT-2026-07-19.md`



# قوانینِ لِین — Project-F OS (ایجنتِ موازی)

> برای لِینِ «جراحیِ قلب» و هر ایجنتِ موازیِ دیگر. هدف: کارِ هم را خراب نکنیم.
> نویسنده: لِینِ «Project-F OS» (2026-07-19). مرجعِ کامل: [[LANE-RULES-parallel-agents-2026-07-19]] · [[../ARCHITECTURE-SOT]].

## ۰) وضعیتِ لحظه‌ای (مهم)

- **نقشِ من:** تبدیلِ Project-F (`03 - Projects/اونلی فنز/`) به یک OS مستقلِ ماژولار با مغزِ LLM-backed، حلقه‌ی tick، REST API، و **پلِ محتاطِ دوطرفه** به ارگانیسمِ اختاپوس.
- **تصمیمِ مالک (2026-07-19):** Scope = `pf_os + پلِ محتاط`. نقش = همان Project-F، ولی محتاط (داخلِ چارچوبِ LANE-RULES).
- **ارگانیسم الان `STOP-ORGANISM` است** — مالک گذاشته. من برنمی‌دارم.
- پلانِ کاملِ تصویب‌شده: ۷ فاز (در `01 - Dashboard/OCTOPUS-DEBUG-REPORT-2026-07-19.md` §۷).

## ۱) فایل‌هایی که لِینِ Project-F مالکِ آن‌هاست — دست نزنید/revert نکنید

| فایل | وضعیت | توضیح |
|------|-------|-------|
| `03 - Projects/اونلی فنز/**` | 🔒 مالِ من | کلِ پروژه‌ی Project-F (brain, langar, studio, orchestrator, pf_os, tests) |
| `03 - Projects/وانلی فنز/**` | 🔒 مالِ من | aliasِ فارسیِ همان پوشه (typosquatter — هر دو مالِ من) |
| `_ops/state/saba-bridge.jsonl` · `.cursor` · `.lock` | 🔒 مالِ من | scaffold پل (الان فقط comment) |
| `octopus_core/integration/langar_integration.py` | 🟡 مشترکِ concept | لِینِ قلب نگرفتش؛ ولی اگر لِینِ قلب `octopus_core/` را گرفت، هماهنگ کنید |

**فلگ‌های من (خاموش بمانند مگر مالک بخواهد):** `OCTOPUS_WIRE_PROJECTF_LOOP` · `OCTOPUS_WIRE_SABA_BRIDGE` · `OCTOPUS_WIRE_PROJECTF_LEG`.

## ۲) نقاطِ برخوردِ احتمالی (محتاط) — اگر مجبور شدم، فقط این بخش‌ها

| فایل مشترک | بخشِ مالِ من | بخشِ مالِ قلب (دست نزنید) |
|------------|--------------|---------------------------|
| `_ops/wiring.py` | افزودنِ `saba_bridge_beat()` + `make_projectf_leg()` + `projectf_beat()` (additive، پشتِ flag) | بقیه‌ی فایل، بخصوصِ بخش‌های heart/fuel |
| `_ops/organism.py` | یک call به `saba_bridge_beat()` در main loop (additive، پشتِ flag) | بقیه، بخصوصِ heart/cortex beat dispatch |
| `_ops/budget/budgets.yaml` | `projects.PROJECT_F` + `partners_default.PROJECT_F` (که از قبل هست) | **بلوکِ `allocation` (core_members/satellite_members) مالِ قلب است — دست نزنید** |

**قاعده:** اگر به بلوکِ مالِ قلب برخورد کردم، **متوقف می‌شوم و از مالک می‌پرسم** (طبقِ LANE-RULES §۴).

## ۳) کارهای انجام‌شده (پایدار، قابلِ commit)

| فاز | کار | تست | وضعیت |
|-----|-----|------|-------|
| ۰.۱ | رفع باگ امنیتیِ compliance-bypass در `orchestrator.py:104` — checks از `PROJECT-F-CONTROL-MANIFEST.json` خوانده می‌شود (نه hardcode) | `tests/test_orchestrator_compliance.py` ۴/۴ | ✅ سبز |
| ۰.۲ | رفع ۱۳ تست قرمز — علتش `_ops/STOP-ORGANISM` بود (نه bug). `setUp` در `studio/test_saba_studio.py` + `langar/test_langar.py` حالا `_global_stop` را stub می‌کند تا تست‌ها از وضعیتِ زنده‌ی ارگانیسم مستقل باشند. | کل suite: **۱۸۱ سبز، صفر قرمز** | ✅ سبز |

> ریشه‌ی ۱۳ تستِ قرمز صادقانه: ارگانیسمِ owner-STOP شده `_ops/STOP-ORGANISM` می‌سازد که `_global_stop()` را True می‌کند و saba/langar را به‌درستی halt می‌کند. رفتارِ production درست بود؛ تست‌ها environment-agnostic شدند.

## ۴) قوانینِ مشترک (طبقِ LANE-RULES §۳)

1. **فقط additive**؛ رفتارِ نو پشتِ فلگِ خاموش.
2. **ویرایشِ کدِ زنده فقط وقتی ارگانیسم خاموش است** (الان هست). از سندباکس: برای ویرایشِ فایلِ موجود از `open(p,'w')`/`Edit`/`Write` استفاده می‌کنم.
3. **هرگز:** پول/LIVE (P7) · مسیرهای `.agentignore` · `center.py` · فلگ/STOP لِینِ دیگر.
4. پاها **propose-only**‌اند.
5. **پیش از پایان:** تست‌های لِینِ خودم سبز + این فایل را به‌روز می‌کنم.
6. **کامیت/merge/ری‌استارت دستِ مالک است.**

## ۵) اگر برخورد دیدید

اگر لازم شد فایلی از لِینِ من را تغییر دهید (مثلاً `saba_studio.py` یا `orchestrator.py`) — **متوقف شوید و از مالک بپرسید**. من هم متقابلاً به `_ops/heart/*`، `_ops/cortex/local_llm.py`، `_ops/cortex/model_router.py`، `_ops/telegram_center/approval_store.py` و بلوکِ `allocation` در `budgets.yaml` دست نمی‌زنم.
