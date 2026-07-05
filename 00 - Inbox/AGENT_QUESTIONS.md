---
type: log
status: active
tags: [agents, escalation]
created: 2026-07-03
updated: 2026-07-04
---

# سوالات ایجنت‌ها — کانال escalation

> وقتی قاعده‌ای راه ایجنت را می‌بندد یا موردی مبهم است، **تنها** کار مجاز: سوال را اینجا append کن و رد شو. مرور هفتگی، بی‌جواب‌ها را به مالک می‌رساند. append-only.

<!-- قالب ورودی:
## YYYY-MM-DD HH:mm — <نام ایجنت>
سوال به فارسی + wikilink نوت‌های مربوط.
-->

## 2026-07-04 16:35 — Claude (Cowork)

رویداد: venv خراب WSL (`karyabi-bot-venv`، symlinkهای `bin/python`) عامل خطای EACCES در لود Obsidian بود؛ با تایید صریح آری حذف شد و سپس آری کل `_Archive` را با PowerShell به بیرون از vault منتقل کرد: `C:\Users\Armin\Desktop\backup-Archive`. چون [[_PROJECT_INSTRUCTIONS|قانون اساسی]] برای ایجنت‌ها فقط‌خواندنی است، این تغییرها **پیشنهاد** می‌شود (ویرایش فقط با آری):

1. §۰ قاعده ۱ و §۲ جدول: مقصد «بازنشسته/باینری» (`_Archive`) دیگر داخل vault نیست. سوال کلیدی: باینری جدید را ایجنت کجا بگذارد؟ پیشنهاد: در `00 - Inbox` بماند + مسیر در HANDOFF فهرست شود؛ انتقال نهایی به `backup-Archive` فقط توسط مالک.
2. §۳ چک‌لیست آرشیو پروژه: مقصد `_Archive/Projects/<سال> - <نام>` → مسیر جدید خارج vault (انتقال توسط مالک).
3. §۱۲: `_Archive/Logs/Cleanup 2026.md` اکنون خارج از vault است — ارجاع آپدیت شود، یا فقط این لاگ به داخل vault برگردد؟
4. `.agentignore` و `.gitignore`: پیشنهاد — خط `_Archive/` به‌عنوان محافظ بماند (اگر پوشه دوباره ساخته شد)، فقط کامنت‌ها آپدیت شوند.
5. ارجاع‌های normative به `_Archive` در: `CLAUDE.md` (محدوده منفی)، [[10 - Telegram processing/SOP|SOP]]، `.claude/rules/telegram.md`، چک‌لیست [[02 - Life OS/Weekly Review|Weekly Review]] — بعد از verdict یک‌جا اصلاح شود.
6. مسیرهای stale در نوت‌های محتوایی (مثل [[03 - Projects/Mining/PROJECT|PROJECT Mining]]: «ماینرها در _Archive» و [[03 - Projects/_Index - Projects|ایندکس پروژه‌ها]]) — بعد از verdict، اصلاح دسته‌ای در یک جلسه.

نکته: [[01 - Dashboard/Home|Home]] (داشبورد ایجنت‌نگه‌دار، طبق سابقه جلسه سوم) همان روز به‌روز شد؛ `_Duplicates` همچنان داخل vault است — اگر بخواهی همین الگو (انتقال به بیرون پس از بررسی) برایش هم اعمال شود، در مرور هفتگی تصمیم بگیر.

## 2026-07-04 — Claude (Cowork) — جلسه ۷: پس از منسجم‌سازی vault

جلسهٔ «backup را منسجم‌تر کن» با ۳ verdict آری (گسترش schema · تغییرنام نسخه‌های غیرریشه · ثبت بک‌لاگ کد/باینری). موارد باز که **آری** تصمیم می‌گیرد:

1. **جابه‌جایی کد لوز به `_code`** (Q3 = فعلاً فقط ثبت): Accounting (`personal-dashboard.js` · `business-dashboard.js` · پوشه‌های `1/`، `2/`، `importer/`) → `03 - Projects/Accounting/_code/`؛ هیپنوتیزم (`langar_redteam.py` · `فیوژن هیپنوتیزم/Silabi-Bot/silabi_bot.py`) → `_code`/`04 - Architect System`. ⚠️ **ریسک:** بات‌های فعال ممکن است این مسیرها را ارجاع دهند؛ قبل از انتقال چک شود.
2. **نام‌های مبهم پوشه:** Accounting `1/` و `2/` → نام توصیفی؛ پوشهٔ فارسی `حساب کتاب/` (xlsxها) — نگه‌داشتن یا انگلیسی‌سازی؟
3. **باینری‌های سطح‌بالای Crypto** (۹ PDF + ۲ zip: `armin briefing…` و غیره) → پیشنهاد زیرپوشهٔ `_docs` یا `Desktop\backup-Archive`. انتقال به آرشیو بیرونی فقط توسط مالک.
4. **کهنگی محتواییِ PROJECT.md** (نه متادیتا): [[03 - Projects/Ziman Galerry/PROJECT|Ziman]] «Current state» پوشه‌های `control-brain/`+`ziman-agent/` را ندارد؛ [[03 - Projects/اونلی فنز/PROJECT|اونلی‌فنز]] چهار سند ۴ ژوئیه را منعکس نمی‌کند. نیازمند refresh با context آری.
5. **لینک bare `[[INDEX]]` مبهم** (Mining/INDEX + architect INDEX) — مثل HANDOFF/ROTATION حل‌شده. اگر بخواهی، نسخهٔ غیرریشه rename شود.
6. **تناقض epistemic_status:** [[07 - Knowledge/هیپنوتیزم  و خودآگاهی/Report - هیپنوتیزم - HRV و خودهیپنوتیزم|Report HRV]] = `peer-reviewed` ولی PROJECT.md هیپنوتیزم می‌گوید «هنوز هیچ نوتی peer-reviewed نیست» — یکی اصلاح شود.
7. **فیلد `project:` خودارجاع** در PROJECT.mdها و ۳ template: آدیت پیشنهاد حذف داد؛ چون ممکن است کوئری‌های Bases (`Projects.base`) وابسته باشند، دست‌نخورده ماند — verdict آری.

انجام‌شدهٔ این جلسه (غیرمخرب، بدون verdict لازم): جزئیات در [[01 - Dashboard/HANDOFF|HANDOFF]] §جلسه هفتم.

## 2026-07-04 — Claude (Cowork) — جلسه ۸: ناوگان تحقیق + مغز زنده

آری خواست «رباتم کامل زنده باشد با همه پروژه‌ها با مغز زنده». ساخته شد: [[05 - Agents/Research Scout Fleet|Research Scout Fleet]] (۲۳ تسک زمان‌بندی، همه propose-only در scout-digests، استثنای صریح گیت آری) + [[01 - Dashboard/Brain|مغز زنده]]. یک اصلاح قانون اساسی نیاز به **ratify آری** دارد (قانون اساسی فقط‌خواندنی برای ایجنت):

1. **§۸ / §۰ قاعده ۱ — نوت دومِ overwrite-مجاز:** تا حالا فقط [[01 - Dashboard/HANDOFF|HANDOFF]] «overwrite مجاز» بود. به‌درخواست مستقیم آری، [[01 - Dashboard/Brain|Brain.md]] هم نوتِ زندهٔ overwrite-مجاز شد (تسک `brain-pulse` هر ۳ ساعت بازنویسی‌اش می‌کند، فقط لینک/state، نه secret). پیشنهاد: یک خط به §۸ اضافه شود که Brain.md را هم مثل HANDOFF استثنا کند. تا ratify، به‌عنوان استثنای owner-directed عمل می‌کند (مثل triage جلسه سوم).
2. **معافیت evaporation:** فایل‌های `_`-دار در scout-digests (`_Mycorrhizal Map`، `_README`) هرگز archived نمی‌شوند — در قاعدهٔ TTL لحاظ شود.
3. این کار پرامپتِ باز [[00 - Inbox/Prompt - اتصال همه پروژه‌ها به مغز کنترل|اتصال همه پروژه‌ها به مغز کنترل]] را عملاً محقق کرد (Brain = همان مغز کنترل خواندنی). اگر منظور، اتصال اجرایی/تلگرامی بود، جدا verdict بده.

جزئیات کامل ناوگان: [[01 - Dashboard/HANDOFF|HANDOFF]] §جلسه‌های ۵–۸.

## 2026-07-06 — Claude (Cowork) — INGEST area «Time-Architecture»

verdict آری روی §۷ گرفته شد (area مستقل + cross-link · kind: area · money_link=محصول/محتوا/خدمت · RFC HRV فقط Propose-only). area ساخته شد (additive-only): [[07 - Knowledge/Time-Architecture/PROJECT|PROJECT]] + theory/claims/experiments/MAP + RFC. تصمیم‌های **باقی‌مانده** که آری verdict می‌دهد:

1. **money_link مشخص:** جهت «محصول/محتوا/خدمت» انتخاب شد ولی offer مشخص هنوز TBD (فعلاً guard_flag `MONEY_LINK_TBD`). چه محصول/محتوا/خدمتی؟
2. **scope کلید `epistemic_status`:** طبق Property Schema این کلید فقط به حوزهٔ هیپنوتیزم scope شده. آیا به area جدید Time-Architecture تعمیم یابد؟ (نیازمند ویرایش Property Schema + `.obsidian/types.json` با تأیید مالک.) تا آن‌موقع سطح اطمینان فقط داخل متن علامت خورده.
3. **نام پوشه:** `Time-Architecture` (لاتین، هم‌راستا با Crypto/Mining/Accounting) — تأیید یا rename به فارسی «معماری زمان»؟
4. **RFC HRV:** آیا به `status: ready` برود؟ اجرا پشت Security Gate + verdict قفل است.
5. **git checkpoint:** این mount فاقد git repo فعال است؛ «commit یک‌فرمانه» ممکن نشد. کل تغییر additive-only است — manifest برگشت‌پذیری در پاسخ چت. اگر repo جایی هست، مسیرش را بده تا checkpoint واقعی بزنیم.
