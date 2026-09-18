# COGNITIVE-SYSTEM-MAP — OCTOPUS 2026-09-17
# lane: OCTOPUS-UNIFIED-RECOVERY-20260917

## ۱. ماژول‌های شناختی روی main (بررسی امروز)
| ماژول | مسیر (tracked روی main) | نقش |
|---|---|---|
| RemoteBrain | `ofn/adapters/remote_brain.py` | مغز پولی/چند-ارائه‌دهنده |
| brain_schema + lock | `ofn/agents/brain_schema.py` + `brain_schema.lock` | قرارداد پیام مغز (قفل‌شده) |
| brain_wake | `ofn/agents/brain_wake.py` | بیداری شناختی |
| brainport | `ofn/helpers/brainport.py` | درگاه |
| brain-probe | `deploy/brain-probe.py` + تست | سوند |
| ModelRouter | `ofn/adapters/router.py` | مسیریاب چند-مدلی (سایت گیت OD-4: ask) |

هیچ ماژولی با نام hypothesis-engine روی main نیست (grep=۰) — آن مفهوم با OBSERVATORY/CORTEX_HYPOTHESIS بازنشسته شد (R2-3).

## ۲. وضعیت زندهٔ شناخت (شواهد قراردادی + runtime امروز)
- **چند-ارائه‌دهنده LIVE از 09-13**: gemini + deepseek + openai فعال؛ sakana/fugu محدودیت usage (تنها credential پولیِ موجود)؛ anthropic نیازمند workspace-id. broker فقط secrets.env می‌خواند.
- **پچ‌نویس آزاد**: قالب `octopus.patch.v1` (v1.4) + critique() مدل دوم + ۳ وظیفه/tick؛ مدل محلی 0.6b یک فیکس واقعی $0 نویسیده.
- **فرآیندهای زندهٔ امروز روی 138**: octopus-mesh supervisor/router/settler/verify_dispatcher + octopus_bridge + ofn.run + ofn-heartbeat (از Sep-15 پیوسته).
- تایمرهای شناختی: coding-worker، experience-ingest، eti-telemetry، autonomy-supervisor (زنده امروز).

## ۳. آزمایش‌ها و اعتبارشان (قاعده: تست سبز ≠ شاهد زنده‌بودن کنترل)
- **آزمایش ۹۷/۱۰۰ نامعتبر اعلام شد** (از سطح خودنویس CURRENT-TRUTH امروز، عیناً): «۹۷/۱۰۰ در محیط فریبنده — پاسخ داخل کاندیدا hardcode شده بود، کاندیدا `env.secret_doors` را مستقیم می‌خواند، محیط در هر ۱۰۰ اجرا یکی بود. کنترل کنجکاوی ۱۰۰/۱۰۰ برد و سریع‌تر بود.» → confound ثبت‌شده؛ هیچ grade بالاتر از E3 بدون scaffold-variation.
- WILD arena: sandbox v2 = ۱۳/۱۳؛ shadow پایدار ۲۴/۲۴ بدون تقسیم‌برصفر؛ گیت speedup رد شد → **canary ارسال نشد**؛ v1.3 آمادهٔ ارزیابی مجدد.
- deep-scan: تایمر زنده (دوشنبه‌ها 04:00Z) + ledger فقط-افزوده (۱۶۰ یافته، صفر تکرار) + DASHBOARD.json برای orientation مستقل از PC.

## ۴. مرزهای بازنشسته/ممنوعه (یادآوری حاکمیتی)
`OBSERVATORY` و `CORTEX_HYPOTHESIS` بازنشسته (R2-3) — **اما دو workflow فعال به نام `observation-contract.yml` و `observatory-fixture.yml` هنوز در `.github/workflows/` روی main زنده‌اند** → تناقض نام‌گذاری/مفهوم؛ دست‌نخورده (پیشنهاد جراحی SURG-10).
هیچ flag شناختیِ جدید نباید بدون receipt هم‌دامنه روشن شود؛ self-elevation ممنوع (AGENTS.md §5).
