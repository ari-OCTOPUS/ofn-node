---
type: report
status: ready
tags: [learning-engine, architecture, governance, security]
created: 2026-07-06
updated: 2026-07-06
created_by: agent
sources:
  - "[[00 - Inbox/2026-07-06 0215 LEARNING-ENGINE-DEPENDENCY-CONTRACT-v1-draft]]"
  - "[[00 - Inbox/2026-07-06 0215 MASTER-ARCHITECTURE-SPEC-v1.3-draft]]"
  - "[[06 - Architecture Maps/Property Schema]]"
  - "[[_memory/TWO-BRAIN-CONTROL-BLUEPRINT]]"
---

# بازبینی LEARNING-ENGINE-DEPENDENCY-CONTRACT v1 + الحاقیه MASTER v1.3

## الف. وضعیت ثبت

- [[00 - Inbox/2026-07-06 0215 LEARNING-ENGINE-DEPENDENCY-CONTRACT-v1-draft|Learning Engine spec]] و [[00 - Inbox/2026-07-06 0215 MASTER-ARCHITECTURE-SPEC-v1.3-draft|MASTER v1.3]] در Inbox ثبت شدند (proposal).
- نسخه v1.1 با `status: superseded` + `superseded_by` به v1.3 لینک شد — طبق قاعده «انتقال، نه حذف».

## ب. نقاط قوت طراحی Engine (تأیید سازگاری)

طرح spine + typed contracts با DNA این vault می‌خواند: **shadow mode** (فقط خواندن+گزارش) با §Security Gate باز سازگار است؛ «فقط manifest بخوان، eligibility را دوباره حساب نکن» دقیقاً invariant PHASE-0A است؛ halt بدون manifest = fail-closed درست؛ قرارداد L6 (People هرگز نوشته نمی‌شود) و segregation در 3.6/L2c با C17 هم‌راستاست؛ fail-degraded و swappable بودن Engine اصل P7 (بودجه پیچیدگی) را نقض نمی‌کند چون satellite است.

## ج. یافته‌ها (پیش از ratify باید حل شود)

1. **ابهام shadow mode × Fugu (مهم‌ترین):** §۸ می‌گوید shadow «همین حالا ✅» ولی `LEARNING-STATE.json` فیلد `fugu_call_pending` دارد و §۴ Fugu را «پیش‌نیاز داخلی» Engine می‌داند. باید صریح شود: **shadow = صفر فراخوانی خارجی** (نه Fugu، نه partner tools) تا وقتی کلید در ROTATION ثبت و `budget_ceiling_daily` عددی شود — الان `null` است. وگرنه «shadow بی‌ریسک» ادعای دقیقی نیست.
2. **نقض schema در L9 (3.10):** `trigger: loop` خارج از مقادیر مجاز Property Schema است (`telegram|cron|manual`) و کلید `level` وجود ندارد (معادل موجود: `autonomy_level`). ثبت Engine در AGENT_REGISTRY نیاز به گسترش schema با تأیید مالک دارد — ایجنت کلید اختراع نمی‌کند.
3. **قرارداد L8 (HANDOFF) با الگوی موجود نمی‌خواند:** HANDOFF هر جلسه توسط ایجنت تعاملی بازنویسی می‌شود؛ «بخش Learning state» خودکار در آن پایدار نمی‌ماند و استثنای overwrite جدید می‌خواهد. جایگزین منطبق با الگوی ratified موجود: **یک سطر در `_memory/HEARTBEAT.md`** (هر تسک فقط سطر خودش) + wikilink در HANDOFF.
4. **مرجع غایب:** `SELF-LEARNING-LOOP-SPEC` نه در vault است نه در آپلودها — ولی §۱۱ و frontmatter به آن ارجاع می‌دهند و MASTER v1.3 §۱۶ بر آن بنا شده. یا آپلودش کن تا ثبت شود، یا ارجاع‌ها حذف/جایگزین شوند. (هنگام ثبت، wikilinkهایش به متن ساده تبدیل شد تا لینک شکسته نسازد.)
5. **L2c — تطبیق با واقعیت این جلسه:** partnerهای جدول واقعاً الان به‌صورت plugin در Cowork نصب‌اند (Tavily، CockroachDB، monday.com، DataRobot، Fastly و چند مورد دیگر)؛ چند سرویس (monday، Slack، Atlassian، Linear، Notion، Datadog...) **نیاز به authorize از تنظیمات connector دارند** و تا آن موقع غیرفعال‌اند. قواعد ۱–۸ بخش L2c خوب‌اند؛ فقط قاعده ۸ (ثبت هر partner در AGENT_REGISTRY) با یافته ۲ همان مشکل schema را دارد.
6. **سطح‌های L2+ در جدول L2c فعلاً نظری است:** تا Gate باز است، وراثت §Gate همه را read-only می‌کند — جدول باید ستون «تا Gate: read-only» بگیرد تا با AGENT_REGISTRY هم‌زبان شود.

## د. الحاقیه MASTER v1.3

- §۱۶ (حلقه خودیادگیری) و §۱۷ (خلاصه همین Engine) اضافه شده‌اند؛ ساختار سازگار.
- **⚠️ یافته‌های بازبینی v1.1 در v1.3 اعمال نشده‌اند و همگی پابرجا هستند:** F4 هنوز محتوای مشکوک‌به-secret را به API خارجی می‌فرستد (🔴، [[00 - Inbox/2026-07-06 0205 review-master-spec-v1.1|بازبینی v1.1]] §۲)؛ تناقض عددی بودجه اشتراک vs سقف Normal؛ نرخ دوبرابری >272K context غایب؛ همان ۴ خطای تایپی (هنگام ثبت اصلاح و ثبت شد).

## ه. پاسخ پیشنهادی به ۴ تصمیم باز §۱۰ (تصمیم با توست)

1. shadow: **بله، به شرط بند ج-۱** (صفر call خارجی تا کلید+بودجه).
2. `LEARNING-STATE.json`: پوشه Engine خودش (state است نه recall) — پیشنهاد مسیر: `04 - Architect System/learning-engine/`.
3. fallback: **Claude** به‌عنوان fallback اول (همین حالا موجود و تست‌شده)، مدل local فاز بعد — کمترین قطعه جدید.
4. `LEARNING-CONTRACT.yaml` تک‌منبع: بله؛ کنارش در همان پوشه Engine.

## و. verdictهای لازم

1. حل ج-۱ (تعریف سخت shadow) قبل از هر ساختی.
2. verdict گسترش schema برای `trigger: loop` (یا استفاده از `cron` موجود).
3. تکلیف `SELF-LEARNING-LOOP-SPEC` (آپلود یا حذف ارجاع).
4. یافته‌های باز v1.1 (F4، بودجه) — هنوز منتظر verdict قبلی‌اند.
