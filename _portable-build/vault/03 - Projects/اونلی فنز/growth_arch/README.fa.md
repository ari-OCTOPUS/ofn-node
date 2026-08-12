---
type: runbook
project: "[[03 - Projects/اونلی فنز/PROJECT]]"
status: active
tags: [creator-business, marketing, tooling]
created: 2026-08-03
updated: 2026-08-03
---

# growth_arch — باستان‌شناسِ رشد

ماژولِ **آفلاین**ِ تحلیلِ معماریِ رشد. ورودی را انسان دستی می‌دهد؛ ماژول امتیاز می‌دهد، «کارتِ معماری» استخراج می‌کند و از رویشان **فرضیهٔ آزمایش** می‌سازد. هیچ داده‌ای جمع نمی‌کند و هیچ اقدامی انجام نمی‌دهد.

- زبان: Node.js خالص (فقط stdlib) — بدون هیچ dependency ِ بیرونی، بدون `npm install`.
- نیازمندی: Node ‏>= 18 (روی v24.8.0 راستی‌آزمایی شد).

---

## این ماژول چه می‌کند

۱. **امتیازدهی** به هر entity در شش بُعد: `growth`، `engagement`، `replicability`، `authenticity`، `conversion`، `target_fit` و یک `total` ِ وزن‌دار (همه در بازهٔ ۰ تا ۱).
۲. **کارتِ معماری** برای هر entityِ برتر: ستون‌های محتوا، الگوهای قلاب، ساختار روایت، ریتم انتشار، حلقهٔ رشد، مسیر تبدیل، مدل درآمد، منابعِ لازم، توصیه‌ها و ریسک‌ها.
۳. **خوشه‌بندی** کارت‌های شبیه به هم.
۴. **طرحِ آزمایش**: برای هر کارت یک فرضیه با variantها، سنجه‌های موفقیت، guardrail و قاعدهٔ تصمیم — به‌علاوهٔ یک نقشهٔ ۳۰روزه.
۵. **گزارشِ شواهد**: شمارشِ شواهد، میانگین اطمینان، و «نقاط ضعف» (مثلاً `Low evidence count: 1`).

---

## ورودی — schema

فایل ورودی یک JSON با این شکل است (نمونهٔ کامل: `fixtures/sample_entities.json`؛ schema ِ رسمی: `contracts/analyze-input.v1.json`).

### ریشه

| کلید | لازم؟ | توضیح |
|---|---|---|
| `schema_version` | خیر | مثلاً `growth-archaeologist.v1` |
| `job` | خیر | `job_id`، `tenant`، `created_at` |
| `settings` | خیر | پایین را ببین |
| `entities` | **بله** | آرایه، ۱ تا ۵۰۰ آیتم |

### `settings`

`target_niche` · `target_market` · `language` · `product` · `target_audience` · `min_evidence` (پیش‌فرض **۲**) · `top_n` (پیش‌فرض ۵).
`target_niche` / `product` / `target_audience` مبنای محاسبهٔ `target_fit` هستند؛ `min_evidence` آستانه‌ای است که زیرش هشدارِ کمبودِ شواهد صادر می‌شود.

### هر `entity`

تنها فیلدِ **الزامی** `name` است؛ بقیه اختیاری‌اند ولی هرچه کمتر بدهی، امتیازها بی‌معناتر می‌شوند.

`entity_id` · `name` (الزامی) · `handle` · `entity_type` (`creator|company|brand|founder`) · `primary_platform` (`tiktok|youtube|instagram|linkedin|x|reddit|web|newsletter|podcast|other`) · `country` · `niche` · `audience_problem` · `positioning` · `discovered_at` · `first_growth_evidence_at` · `followers_previous` · `followers_current` · `tags[]` · `evidence[]` · `content[]`

### هر آیتمِ `evidence`

`id` · `source_url` · `source_type` (مثلاً `platform_snapshot`، `content_sample`، `landing_page`) · `published_at` · `claim` (جملهٔ خودِ شاهد) · `metric_name` · `metric_value` · `confidence` (عدد ۰ تا ۱ — قضاوتِ خودت دربارهٔ اتکاپذیریِ منبع).

### هر آیتمِ `content`

`id` · `url` · `platform` · `published_at` · `title` · `hook` · `hook_type` (`story|proof|demo|question|problem|contrarian|…`) · `format` · `topic` · `emotional_trigger` · `proof_type` (`data|demo|case_study|before_after|testimonial|expertise|transparent_failure`) · `cta` (`buy|join|subscribe|download|book_call|comment|save|share`) · `narrative_steps[]` · `evidence_ids[]` · `metrics: { views, likes, comments, shares, saves }`.

> نکته: `url` و `source_url` فقط **اعتبارسنجیِ شکلی** می‌شوند (باید URL معتبر باشند). هرگز باز نمی‌شوند و درخواستی به آن‌ها ارسال نمی‌شود.

---

## اجرا

از داخلِ همین پوشه:

```bash
# تست‌ها (باید ۷/۷ سبز و exit=0 باشد)
node --test test/*.test.js

# تحلیل
node src/cli.js analyze --input fixtures/sample_entities.json --out output

# بازتولیدِ فایل‌های contracts
node src/cli.js schemas --out contracts
```

- در **PowerShell** گلاب را کوتیشن بگذار تا خودِ Node بازش کند: `node --test "test/*.test.js"` (یا فایل‌ها را صریح بنویس). فرمِ `node --test test/` روی Node ‏v24 کار **نمی‌کند** — آرگومان را ماژول فرض می‌کند و `MODULE_NOT_FOUND` می‌دهد.
- خروجی‌ها همیشه در `output/` نوشته می‌شوند و در `.gitignore` ِ همین پوشه نادیده گرفته شده‌اند — آرتیفکتِ اجرا هستند، نه کد. پوشه در صورت نبود خودکار ساخته می‌شود.
- خروجی **قطعی (deterministic)** است: همان ورودی ⇒ همان بایت‌ها (شناسه‌ها sha1 ِ محتوا هستند).

## خروجی‌ها (در `output/`)

| فایل | محتوا |
|---|---|
| `analysis.json` | همه‌چیز: خلاصه، entityهای برتر، کارت‌ها، خوشه‌ها، طرحِ آزمایش، نقشهٔ ۳۰روزه، گزارشِ شواهد، هشدارها |
| `architecture_cards.json` | فقط کارت‌های معماری |
| `content_hypotheses.json` | فقط طرحِ آزمایش (فرضیه‌ها + variantها) |
| `30_day_experiment_plan.json` | نقشهٔ هفته‌به‌هفتهٔ ۳۰روزه |
| `top_creators.json` / `top_creators.csv` | جدولِ رتبه‌بندی |
| `evidence_report.json` / `evidence_report.md` | گزارشِ شواهد؛ نسخهٔ md برای خواندنِ انسانی |

---

## مرزهای صریح (خواندنش الزامی است)

- **آفلاین است.** هیچ scraping، هیچ تماسِ شبکه‌ای، هیچ اجرای پروسه. ماژول فقط `node:fs/promises`، `node:path` و `node:crypto` را import می‌کند و بس. **نباید** هرگز به شبکه وصل شود؛ اگر روزی کسی adapter ِ شبکه‌ای به آن اضافه کرد، آن یک تغییرِ ماهیت است و رأیِ مالک می‌خواهد (پروندهٔ باز: `src/providers/sourceCollector.js` — یک کلاسِ انتزاعیِ خالی است که فقط `throw` می‌کند، ولی عمداً به‌عنوان نقطهٔ اتصالِ adapterهای آینده نوشته شده).
- **داده را انسان دستی می‌دهد.** ماژول هیچ چیزی را «کشف» نمی‌کند؛ فقط چیزی را که تو در JSON نوشتی مرتب و امتیازدهی می‌کند.
- **خروجی فرضیه است، نه حقیقت.** خودِ ماژول این را در `source_quality_notes` می‌نویسد: «امتیاز بالا بدون evidence کافی فقط فرضیه است، نه نتیجه قطعی.» امتیازِ ۰.۹ روی یک entity با یک شاهد، یک عدد است نه یک واقعیت. همیشه اول `warnings` و `evidence_count` را نگاه کن.
- **propose-only.** هیچ اکشنِ بیرونی ندارد: نه پیام می‌فرستد، نه پست می‌کند، نه چیزی را منتشر می‌کند. تنها اثرش نوشتنِ فایل در `output/` است. هر اقدامی روی خروجی‌اش، تصمیمِ انسان است.
- **هویت بیرون نمی‌رود.** طبق قواعدِ قفل‌شدهٔ پروژه، هیچ خروجی‌ای نباید نامِ شهر، قومیت یا هویتِ کسی را حمل کند. **ماژول این را برایت اعمال نمی‌کند** — فیلدهای `name`، `handle` و `country` عیناً از ورودی به `analysis.json` و `architecture_cards.json` منتقل می‌شوند. نقطهٔ کنترل، همان JSON ِ ورودی است که خودت می‌نویسی: اگر نباید بیرون برود، اول از ورودی حذفش کن.
