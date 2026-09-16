---
type: prompt
status: ready
tags: [dashboard, automation]
created: 2026-07-04
updated: 2026-07-04
---

# Prompt — System Dashboard Artifact (داشبورد زندهٔ کل سیستم)

> این پرامپت را هر بار که داشبورد باید تازه شود به ایجنت بده (یا تسک زمان‌بندی `system-dashboard` اجرایش می‌کند). **idempotent است:** اگر چیزی تغییر نکرده باشد، هیچ فایلی نوشته نمی‌شود.

## قرارداد

- خروجی فقط **یک فایل**: `01 - Dashboard/SYSTEM-DASHBOARD.html` — overwrite مجاز (استثنای owner-directed، verdict آری 2026-07-04؛ فایل مشتق است، نه نوت canonical).
- **هیچ secret، مسیر قرنطینه، یا محتوای `_Archive`/`_Duplicates`/`09 - People` وارد HTML نشود.** از [[ROTATION_CHECKLIST]] فقط «شمار ردیف‌های باز/بسته»، هرگز نام کلید/سرویس.
- **قاعدهٔ Project-F:** برای پروژهٔ اونلی فنز خارج از پوشه‌اش فقط کد «Project-F» و state ژنریک (فاز/Track) — هیچ نام، جزئیات محتوا یا اطلاعات شناسایی‌پذیر.
- تک‌فایل self-contained، **بدون CDN** (باید آفلاین باز شود)، RTL فارسی.

## فاز ۱ — اسکن (read-only)

1. `01 - Dashboard/HANDOFF.md` + `01 - Dashboard/Brain.md` — گیت‌ها، جلسات، تصمیم‌های باز.
2. **۸ مغز پروژه:** شش `03 - Projects/*/PROJECT.md` (فیلدهای status/risk_level/autonomy_level + بخش‌های Active Context/Open blockers/Next actions) + فیوژن (`07 - Knowledge/هیپنوتیزم  و خودآگاهی/فیوژن هیپنوتیزم/00_Knowledge_Base/`) + brushline (`03 - Projects/Lead-نقاشی/AiFarm-Lead/Ai farm- sister Painting/brushline/00_governance/`). برای هر مغز، وجود ۴ فایل کیت (PROJECT/INDEX/DecisionLog/OpenQuestions) و `updated:` هر کدام.
3. `05 - Agents/AGENT_REGISTRY.md` + `05 - Agents/Research Scout Fleet.md` — شمار تسک‌های زمان‌بندی و آخرین synthesis در `00 - Inbox/scout-digests/`.
4. `_memory/LIVING-BRAIN-BLUEPRINT.md` — وضعیت ۵ گام نقشهٔ راه.
5. خروجی هر دو اسکریپت `04 - Architect System/scripts/` (فقط اعداد خلاصه).

## فاز ۲ — مدل

یک JSON با schema ثابت بساز:

```json
{"generated":"ISO-8601","model_hash":"sha256",
 "gates":{"rotation_critical_open":n,"gitleaks_done":bool,"git_init":bool,"brain_overwrite_ratified":bool},
 "brains":[{"name":"","path":"","status":"","risk":"","autonomy":"","kit":{"project":1,"index":1,"decisionlog":1,"openquestions":1},"focus":"","blockers_n":0,"next":["حداکثر ۳"]}],
 "fleet":{"tasks_n":0,"last_synthesis":"YYYY-MM-DD"},
 "roadmap":[{"step":1,"state":"pending|done|gated|partial"}],
 "metrics":{"notes":0,"broken_links":0,"frontmatter_errors":0,"tierA_links":0}}
```

`model_hash` = sha256 روی JSON **بدون** فیلدهای `generated` و `model_hash`.

## فاز ۳ — تصمیم بازسازی (وفق‌دادن خودکار)

hash قبلی را از کامنت `<!-- model-hash: … -->` داخل HTML فعلی بخوان. **برابر → پایان، بدون هیچ نوشتنی.** متفاوت → رندر مجدد + بخش «تغییرات از نسخهٔ قبل» با diff فیلد‌به‌فیلد مدل قدیم (از `<script type="application/json" id="model">` نسخهٔ قبلی) و مدل نو.

## فاز ۴ — رندر

بخش‌ها به‌ترتیب: هدر (generated + hash کوتاه) · گیت‌ها (نوار هشدار اگر rotation باز) · هرم سه‌طبقه (SVG inline ساده) · کارت ۸ مغز (رنگ risk، درصد کیت، focus، شمار blocker، ≤۳ قدم بعد، لینک `obsidian://open?vault=backup&file=<URL-encoded>`) · ناوگان · نقشهٔ راه ۵گامی · متریک‌ها · تغییرات از نسخهٔ قبل · مدل خام در `<script type="application/json" id="model">`. فیلتر سمت‌کلاینت (risk/status) با JS خالص مجاز.

## فاز ۵ — اعتبار پیش از نوشتن

1. parse با `python3 -m html.parser` (یا معادل) — بدون خطا.
2. grep محافظ روی خروجی: هیچ تطبیقی با الگوهای کلید (`sk-`, `api[_-]?key`, `token`, `seed`, `BEGIN.*KEY`) — تطبیق یعنی توقف کامل و گزارش.
3. اگر نوت md هم لمس شد (نباید بشود): هر دو validator.

## فاز ۶ — ماژول Doctor (عیب‌یابی + تکمیل)

1. اجرا: `python3 "04 - Architect System/scripts/dashboard_doctor.py"` از ریشهٔ vault → JSON یافته‌ها (چک‌ها: کیت ناقص، index-drift، UTF-8 خراب، basename تکراری، PROJECT کهنه، سلامت خود HTML: hash/لینک‌های مرده/الگوی secret) + `health_score`.
2. خروجی Doctor را در بخش «🩺 Doctor» داشبورد رندر کن (جدول شدت‌دار + score) و خلاصه‌اش را وارد مدل کن (`doctor` key) — یعنی هر یافتهٔ نو خودش hash را عوض می‌کند و بازرندر می‌آورد.
3. **اجرای زمان‌بندی: فقط گزارش (propose-only).** اعمال هر تکمیل (افزودن به INDEX، ساخت فایل کیت، rename، تعمیر بایت) فقط در جلسهٔ تعاملی با verdict آری.
4. یافتهٔ `CRITICAL` (خصوصاً `html-secret`) → علاوه بر رندر، در گزارش پایان اجرا برجسته شود.

## حلقهٔ بهبود

هر اجرا: شکست/false-positive را با تاریخ به انتهای همین نوت append کن. این نوت سند زنده است.

- **2026-07-04:** false-positive شناخته‌شده — `index-drift` بعد از ویرایش ویندوزیِ همان INDEX در همان جلسه، به‌خاطر stale-view سندباکس (یافتهٔ M1). قبل از گزارش، مشکوک‌ها را از سمت ویندوز verify کن.
- **2026-07-04:** `dup-basename` روی pointerهای عمدی `MOVED - *.md` بی‌ارزش است — در دور بعدی Doctor، الگوی `MOVED - ` به whitelist اضافه شود (تغییر اسکریپت با verdict).
- **2026-07-04 (v4 تابلوی تمرکز):** دو FP اسکن رفع شد — (۱) کیت فیوژن باید در `00_Knowledge_Base` چک شود نه ریشهٔ هیپنوتیزم (فاز ۱.۲ همین پرامپت؛ قبلاً ۱/۴ گزارش می‌شد، واقعی ۴/۴). (۲) آمار خام دایرکتوری باید `.agentignore` را رعایت کند (**/_code/ و .git خارج از شمارش) وگرنه اعداد `04 - Architect System` چند برابر باد می‌کنند.
- **2026-07-05 (چرخهٔ بسته):** از این پس درس‌های قابل‌اقدام این حلقه علاوه بر append اینجا، به‌صورت ردیف در [[_memory/EXPERIENCE-LEDGER|EXPERIENCE-LEDGER]] هم انباشته می‌شوند (حافظهٔ canonical چرخه؛ verdict هفتگی با تسک `experience-review`). دو درس نو: utf8-corrupt بعد از ویرایش ویندوزی = همان کلاس stale-view (از ویندوز verify کن) · هر تسک زمان‌بندی نو = ثبت هم‌زمان در AGENT_REGISTRY.
