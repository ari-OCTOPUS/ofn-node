---
type: operating-charter
project: "[[03 - Projects/اونلی فنز/PROJECT]]"
status: active
autonomy_level: autonomous-up-to-ToS (hard-gated actions require human verdict)
tags: [project-f, charter, agent-instructions]
created: 2026-07-06
updated: 2026-07-06
---

# CLAUDE.md — منشور کاری پروژه «اونلی فنز» (Project-F)

> این فایل دستورِ عاملِ کلود برای این پوشه است. **اول از همه** در هر جلسه این ترتیب را لود کن:
> ۱) `_memory/onlyfans-project-memory-2026-07-05.md` (حافظهٔ فشرده) → ۲) `STATE-REPORT-2026-07-05.md` (وضعیت جامع) → ۳) همین فایل → ۴) `PROJECT.md` (Active Context).
> خارج از این پوشه فقط کد **«Project-F»**. هیچ echo هویت/محتوا هرگز.

---

## ۰. یک‌خطی
تیم دونفرهٔ ۵۰/۵۰ (آری = ops/tech/marketing/finance؛ صبا = تولید محتوا)، برند **faceless فقط‌پا**، فاز **validation**، هدف درآمد آزمایشی legal از استرالیا. مرجع کانونی جذب: `ACQUISITION-ENGINE-2026-07-05.md`.

---

## ۱. قواعد قفل‌شده (Hard Rules — تغییرناپذیر بدون verdict انسانیِ صریح)
1. **فقط پا** — بدون صورت، بدون بدن، بدون محتوای explicit.
2. **geo-block کامل ایران** در همه لایه‌ها (OF + Fansly + GAML + Cloudflare) + هیچ هدف‌گیری کاربر داخل ایران.
3. **پرداخت فقط داخل پلتفرم** — هرگز مذاکرهٔ پرداخت P2P/خارجی (PayPal/crypto/بانک شخصی) با یک خریدار.
4. **بدون هیچ نقض ToS** هیچ پلتفرمی.
5. **privacy دوطرفه** (creator + buyer) اصل برند است.
6. **بدون هیچ fact جغرافیایی در حد شهر** در کپی عمومی — فقط «Aussie». سیگنال فرهنگی فارسی **فقط بصری** (انار/چای/ترمه/یلدا)، هرگز متنی («Persian»/«Sydney» ممنوع تا حل سؤال باز #۹).
7. **کد Project-F** بیرون از این پوشه؛ صفر echo هویت صبا یا محتوا.
8. ۱۸+ و رضایت ثبت‌شده؛ محدودهٔ صبا (رد بدن) بر همهٔ پلن‌ها حاکم است.

اگر هر درخواستی با این‌ها در تضاد بود → اجرا نکن، تضاد را با تگ منبع flag کن، جایگزین امن پیشنهاد بده.

---

## ۲. Governance و سطح اختیار (Autonomy)
پیش‌فرض = **«خودکار تا حد ToS» برای کارهای برگشت‌پذیر و درون‌پوشه.** یعنی این‌ها را **بدون پرسیدن** انجام بده:
- تحقیق و یکپارچه‌سازی دیتا؛ مرور وب/مرورگر **فقط‌خواندنی** (چک handle/برند/رقبا)
- ساخت و ویرایش فایل داخل این پوشه؛ ساخت deliverable (docx/xlsx/pptx/pdf)
- ساخت/به‌روزرسانی ساختار Fable5 به‌صورت فایل؛ درفت کپی/کپشن/اسکریپت DM (به‌عنوان draft)
- زمان‌بندی حلقه‌های KPI؛ ثبت **proposal** در DecisionLog/OpenQuestions/PROJECT

**مسدودِ سخت (Hard-Gated) — همیشه با verdict انسانی، و علاوه بر آن قفل تا حل `GATE 0`(=Branch A) و باز شدن Security Gate:**
- ساخت هر اکانت واقعی روی هر پلتفرم · انتشار/پست عمومی · ارسال هر DM
- هر پرداخت/برداشت · login یا تایپ در پلتفرم واقعی
- هر echo هویت صبا/محتوا بیرون از این پوشه · تغییر هر قاعدهٔ قفل‌شده

> این‌ها فراتر از ToS با **survival-filter** خودِ پروژه گِیت شده‌اند؛ پس «خودکار تا حد ToS» طبیعتاً همین‌جا می‌ایستد.

**Kill-switch + سقف:** هر اخطار پلتفرم = توقف فوری همان اتوماسیون + ثبت در DecisionLog. سقف هزینهٔ ابزار/API = **AUD 100/ماه** (زیر سقف تزریق ۲۰۰). هر اتوماسیون جدید فقط بعد از یک هفته اجرای دستیِ موفق.

**⛔ بلاکر فعال:** `GATE 0` (محل اقامت صبا) هنوز باز است — تا ثبت «Branch A/B» در PROJECT.md هیچ اکشن Hard-Gated شروع نمی‌شود. اگر Branch B (داخل ایران) شد → Track A متوقف، فقط با مشاورهٔ حقوقی licensed.

---

## ۳. کانونشن‌های کاری (Working Conventions)
- **زبان:** پاسخ فارسی، با حفظ اصطلاحات فنی انگلیسی (مثل PPV, funnel, RAG).
- **Epistemic tagging اجباری:** هر ادعا با `[FACT]` / `[EST]` / `[OPINION]` / `[SPEC]` / `[OPEN]` + منبع. یادآوری: بیشتر اعداد بنچمارکِ این حوزه از منابع vendor/affiliate‌اند (سوگیری خوش‌بینانه) → پیش‌فرض `[EST]`، ترجیح منبع اولیه.
- **precedence اسناد:** قواعد قفل‌شده > ACQUISITION-ENGINE (برای جذب) > بقیه. هنگام تضاد بین اسناد، جدول reconcile در `STATE-REPORT §۶` را دنبال کن یا برای verdict flag کن.
- **بهداشت state:** بعد از هر کار معنادار، این‌ها را آپدیت کن: `PROJECT.md` (Active Context/Next actions)، `DecisionLog.md`، `OpenQuestions.md`، و در صورت تصمیم بزرگ `_memory/…memory….md` + `INDEX.md`.
- **task list + شفاف‌سازی:** برای کار چندمرحله‌ای task list بساز؛ برای درخواست مبهم قبل از شروع با AskUserQuestion بپرس.
- **verification step:** برای هر کار غیرجزئی یک مرحلهٔ راستی‌آزمایی بگذار (چک منبع، محاسبهٔ برنامه‌ای، counter-argument). برای کار پرمخاطره از subagent برای verify استفاده کن.
- **citation:** خروجی مبتنی بر فایل/MCP → بخش «Sources» با لینک/نام فایل.

---

## ۴. نگاشت کار → ابزار/پلاگین (Capability Wiring)
> connectorهای علامت‌دار با (auth) نیاز به authorize در تنظیمات connector دارند؛ تا وصل‌نشدن، fallback محلی را استفاده کن.

**الف) تحقیق و یکپارچه‌سازی** — skill `deep-research`؛ MCPهای `exa`، `tavily`؛ `WebSearch` + `web_fetch`. برای هر factِ present-day اول سرچ کن، از حافظه نگو.

**ب) بررسی رقابتی/مرورگر (فقط‌خواندنی)** — Claude in Chrome (`navigate` + `get_page_text`/`read_page`) برای چک availabilityِ handle، collision برند، و رصد رقبا. **هرگز login/پست/DM؛ فقط خواندن.** لینک‌های مشکوک را باز نکن.

**ج) ساخت deliverable** — skillهای `docx`/`xlsx`/`pptx`/`pdf` و برای بصریِ برند `canvas-design`. قاعده: **اول تحقیق کامل، بعد** SKILL.md مربوطه را بخوان، بعد بساز.

**د) ردیابی + زمان‌بندی** — `Notion`(auth) یا `monday.com`(auth) برای پیاده‌سازی Fable5؛ تا authorize نشده، **Fable5 = فایل markdown محلی منبع حقیقت است** (طبق `Fable5-Build-Spec.md`). `scheduled-tasks` برای حلقهٔ KPI هفتگی (جمعه). `create_artifact` برای داشبورد KPI زندهٔ قابل‌بازگشایی. اگر ابزاری لازم شد که وصل نیست → `mcp-registry` سرچ و `suggest_connectors`.

---

## ۵. Workflow ورودِ دیتای تحقیق جدید (round-based)
وقتی آری دیتای تحقیق جدید می‌دهد:
1. read-only بخوان و مقابل corpus فعلی بگذار.
2. برای هر محورِ درخواست‌شده (ایده / ساختار / اهداف / competitive) یک **delta-map** بده: **تأیید** (confirms) · **تعارض** (conflicts، با تگ منبع دو طرف) · **افزوده** (extends).
3. قواعد قفل‌شده را با هیچ سند بیرونی overwrite نکن — تعارض را فقط flag کن.
4. با اجازه، خروجی را در سندِ نسخه‌دار ثبت کن (مثل `RESEARCH-INTEGRATION-roundN.md`) و DecisionLog/OpenQuestions را آپدیت کن.

---

## ۶. تناقض‌های بازِ در انتظار reconcile (قبل از اجرا)
دو سند master (MASTER-BUILD ↔ Playbook) · ساعت صبا (۳۰h ↔ ۳–۵h) · برند (Anar Soles پیشنهاد #۱ ↔ Arch & Amber) · نردبان قیمت (۳ نسخه) · نقش Fansly (mirror ↔ هم‌وزن) · «Persian/Sydney» در کپی (تعارض داخلی Playbook). جزئیات: `STATE-REPORT §۶` و `OpenQuestions.md`.

---

## ۷. نقشهٔ فایل‌ها (کوتاه)
- **جهت‌یابی:** `INDEX.md` · `PROJECT.md` · `_memory/…memory….md` · `STATE-REPORT-2026-07-05.md`
- **جذب (کانونی):** `ACQUISITION-ENGINE-2026-07-05.md`
- **استراتژی/ساخت:** `MASTER-BUILD-2026-07-04.md` · `Feet-Content-Business-Master-Playbook.md` · `architecture-blueprint-2026-07-04.md` · `MONETIZATION-EXPANSION-2026-07-04.md` · `Fable5-Build-Spec.md`
- **تحقیق:** `research-results/` (P1–P10 + 00/11/12/13) · `external-research-2026-07-05/` · `research-track-BC-2026-07-04.md`
- **محتوا:** `Content-Topics-Trends-2027.md` · `30-Faceless-Clips-ReadyToFilm.md`
- **ops/consent:** `DecisionLog.md` · `OpenQuestions.md` · `پرسشنامه پارتنر - پاسخ‌های صبا.md`
- **خارج از scope:** `_inbox-other-projects/` (Ziman DM Bot · self-improvement)

---

## ۸. آنچه هرگز خودکار نمی‌شود (لیست بسته)
ارسال DM در OF · ریپلای‌های X · جواب کامنت Reddit ساعت اول · تصمیم قیمت/آفر · ساخت اکانت · هر پست عمومی · پرداخت/برداشت · هر echo هویت · هر چیزی که قاعدهٔ قفل‌شده را لمس کند (فقط صف approve).
