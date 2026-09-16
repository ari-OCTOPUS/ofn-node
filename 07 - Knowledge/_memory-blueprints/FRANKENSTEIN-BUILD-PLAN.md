---
type: design
status: superseded
superseded_by: "[[06 - Architecture Maps/MASTER-ARCHITECTURE-2026-07-29]]"
created_by: agent
created: 2026-07-06
updated: 2026-08-07
tags: [doctor, two-brain, build-plan, architecture]
related: "[[_memory/TWO-BRAIN-CONTROL-BLUEPRINT|TWO-BRAIN-CONTROL-BLUEPRINT]] · [[00 - Inbox/2026-07-06 0245 MASTER-ARCHITECTURE-SPEC-v1.4-draft|SPEC v1.4]] · [[00 - Inbox/DOCTOR-SYNTHESIS|DOCTOR-SYNTHESIS]] · [[01 - Dashboard/HANDOFF|HANDOFF]]"
---

# FRANKENSTEIN-BUILD-PLAN — زنده‌کردن اندام‌ها (۸۰٪ طراحی، آمادهٔ ساخت با Fable 5)

> **status: superseded (2026-08-07)** — واژگانِ «دو مغز/فرانکنشتاین» جایگزین شده با معماریِ organism/legs/heart/cortex/doctor/cockpit؛ نگاه کن [[06 - Architecture Maps/MASTER-ARCHITECTURE-2026-07-29|MASTER-ARCHITECTURE-2026-07-29]]. این سند فقط برای تاریخچه نگه داشته شده.

> رکن اصلی ساخت: ارتیفکت `fleet-live-dashboard` (کابین مشترک دو مغز). این سند = نقشهٔ بامبو: طراحی هر اندام تا ۸۰٪ اینجا بسته شده؛ ۲۰٪ باقی = اجرای Fable 5 با همین قراردادها. verdictهای پایه در [[_memory/TWO-BRAIN-CONTROL-BLUEPRINT|بلوپرینت §۷]] بسته شد (2026-07-06).

## ۰. وضعیت پیش‌نیازها (به‌روز 2026-07-06)

- **git** ✅ — vault از `Initial commit after cleanup` زنده است و agent-checkpoint می‌خورد → پیش‌شرط rollback L2 برقرار.
- **§Security Gate** — طبق experience-review 2026-07-06: **باز**. لیست سیاه (charter/secret/پول/پیام خارجی/تغییر گیت) همیشه human-only.
- **بهداشت محتوا** → مسئولش لوپ جداگانهٔ `deploy-lab-loop` روی کپی `backup-deploy-lab` است (۷ چک، merge-back با verdict مالک). اندام‌های مغز (تسک/اسکریپت/ارتیفکت) مستقیم در vault زنده ساخته می‌شوند — دو مسیر موازی، بدون تداخل.

## ۱. اندام‌ها (وضعیت → کاری که Fable 5 می‌کند → معیار پذیرش)

| # | اندام | وضعیت | ساخت (مسیر دقیق) | معیار پذیرش | گارد |
|---|---|---|---|---|---|
| ۱ | 👁 ادراک | ✅ ساخته شد (این جلسه) | تسک `perception-refresh` هر ۲ ساعت → بازتولید `_memory/SYSTEM-STATE.md` | SYSTEM-STATE هرگز کهنه‌تر از ~۲ ساعتِ اپ-باز | propose-only؛ فقط همان یک فایل |
| ۲ | 🩺 تشخیص ستون۱ (سلامت قطعی) | نیمه‌کاره | `04 - Architect System/scripts/dashboard_doctor.py` را سخت کن: خروجی JSON با ۴ کلاس (OK/WARN/FAIL/UNKNOWN)؛ صدازدنش داخل perception-refresh | صفر-LLM؛ اجرای <۳۰ثانیه؛ نتیجه در SYSTEM-STATE | فقط read |
| ۳ | 💬 پیشنهاد (askClaude) | ✅ در ارتیفکت | پچ §۳ این سند: پنل پروژه‌ها + intentهای استاندارد | هر پیشنهاد = propose-only + ثبت ledger | L1؛ بدون write مستقیم |
| ۴ | 🧑‍✈️ verdict | ✅ در ارتیفکت (`sendPrompt`) | — | هر اعمال L2 یک verdict/whitelist-ref دارد | human-only |
| ۵ | 🔧 اعمال محدود (L2) | باز شد (git+گیت) | executor = جلسات Claude Code/تسک‌ها؛ فقط لیست سفید §۳ منشور؛ قرارداد حذف/ساخت/تست در §۲ | صفر نقض invariant؛ هر اعمال یک commit برگشت‌پذیر | whitelist + kill-switch |
| ۶ | 📏 سنجش | ✅ پایه موجود | append دوره‌ای به `_memory/EXPERIENCE-LEDGER.md` بعد از هر burst؛ آستانهٔ عددی بعد از ~۴ هفته داده | هر burst یک ردیف ledger | append-only |
| ۷ | 🧬 جهش‌نامه (ستون۲) | فاز ۳ | `_memory/MUTATION-LEDGER.md` با چرخهٔ FAILURE→REPAIR ([[07 - Knowledge/_doctor-research/active-mutation-ledger|P4]]): قرنطینهٔ ناهنجاری → پیشنهاد ترمیم → verdict | هر شکست → حداکثر یک اصلاح مینیمال؛ رشد کران‌دار (lifecycle نه append بی‌مرز) | verdict مالک برای promote |
| ۸ | 🔁 حلقهٔ فکری (ستون۳) | فاز ۴ | burst کران‌دار: ۳–۵ round، بودجهٔ سخت، kill-switch هر round، کف همگرایی دو-دوره؛ موتور = Claude پلکانی (Haiku→Opus/Fable)، Fugu فقط escalation پشت سقف بودجه | همگرایی یا توقف — هرگز runaway | Gate + بودجهٔ روزانه + ledger |

## ۲. قرارداد حذف / ساخت / تست (معنای رسمی سه دکمه)

- **حذف** = هرگز delete واقعی. `git mv` به `_Duplicates` (تکراری byte-identical) یا `_Archive` (بازنشسته) + ثبت در لاگ + commit → همیشه برگشت‌پذیر.
- **ساخت** = اسکلت از `_Templates` + فرانت‌متر معتبر Property Schema + ثبت در PROJECT.md همان پروژه + wikilink از MOC.
- **تست** = سه لایه: (۱) `validate_frontmatter.py` + `find_broken_links.py`؛ (۲) کد: `node --check`/`py_compile`/npm؛ (۳) «تست قرارداد» اختصاصی هر پروژه که در PROJECT.md‌اش تعریف می‌شود (مثلاً Accounting: import تستی ANZ بدون خطا).

## ۳. پچ ارتیفکت (spec آماده — فقط URL لازم دارد)

ارتیفکت در جلسهٔ دیگری ساخته شده و **URLاش هیچ‌جای vault ثبت نیست** → مالک URL را بدهد، بعد این پچ در یک قدم اعمال می‌شود:

1. پنل «پروژه‌ها» (۸ کارت از جدول §۱ اینستراکشن): هر کارت سه دکمهٔ intent → `sendPrompt`:
   - `تست <پروژه>` / `بساز <پروژه>: <ورودی>` / `آرشیو <پروژه>: <مسیر>` (متن دقیق قرارداد §۲ در پیام تعبیه شود).
2. کارت «deploy-lab»: نمایش آخرین READINESS (X/7 سبز) + دکمهٔ «مرور DONE».
3. ثبت URL در همین سند + HANDOFF بعد از اعمال.

## ۴. ترتیب اجرا برای Fable 5

1. **امروز (بدون verdict جدید):** اندام ۱ ✅ · پچ ارتیفکت (منتظر URL) · اتصال کابین به ۸ PROJECT.md ✅ (این جلسه).
2. **این هفته:** اندام ۲ (سخت‌کردن dashboard_doctor) → اندام ۶ (ریتم ledger).
3. **بعدش با یک verdict:** اندام ۷ (جهش‌نامه) → اندام ۸ (حلقهٔ فکری، آخرین و خطرناک‌ترین — فقط بعد از ۲ هفته کارکرد پایدار ۱–۷).

## ۵. سوال‌های باز مالک (کوتاه)

1. URL ارتیفکت `fleet-live-dashboard` را بده (برای پچ §۳).
2. سقف بودجهٔ روزانهٔ ستون۳ وقتی رسید: پیش‌فرض پیشنهادی AU$1/روز از سقف AU$30/ماه.
