# PROJECT OVERVIEW — Brushline (CoWork Project)

> نقطهٔ ورودِ یک‌نگاهیِ کلِ پروژه برای هر anAI/انسانِ تازه‌وارد. خلاصهٔ «این پروژه چیست، چه دارد، و قدمِ بعدی کجاست».

---

## ۱. این پروژه چیست
**Brushline** = مغزِ marketing/lead-gen چندایجنتیِ یک کسب‌وکارِ نقاشیِ ساختمان (داخلی/بیرونی) در سیدنیِ استرالیا. محتوا/پاسخ/follow-up را **draft** می‌کند، از سه دروازه (Gate قانون → Human قضاوت → Audit حافظه) رد می‌کند، و به ServiceM8/Tradify **sync** می‌شود — بدونِ بازسازیِ آن‌ها. از ماژولِ خواهر **LANGAR** reuse می‌کند، نه از صفر. درگاهِ Operator = **ربات تلگرام** (تنها کانال).

## ۲. سه Invariant (روحِ پروژه)
- **INV-1:** هیچ publish/spend/پیام بدونِ human approval.
- **INV-2:** PII/مالی هرگز در LANGAR/memory؛ دادهٔ حساس در AU.
- **INV-3:** هر auto-execution = kill switch + spend cap + hash-chained audit.

## ۳. ساختارِ دانش (دو لایه)

| لایه | پوشه | محتوا |
|---|---|---|
| **تئوریِ سیستم** (موجود، کامل) | 00–30، 90 | معماری، حاکمیت، انطباقِ AU، مدلِ مالی، بازار، prompt، spec، threat model |
| **عملیاتِ کسب‌وکار** (جدید) | 40_operations | quoting، SOP، sales scripts، marketing، website، CRM، انطباقِ سطحِ trade |
| **رابط** (جدید) | 50_interface | تلگرام به‌عنوان تنها درگاه |

## ۴. ۱۲ نقشِ agent (نگاشتِ سریع)
Orchestrator · Researcher · Audience/Sentiment · Content/Copy · Asset/Image · Channel-Pub · Lead-Capture + (لایهٔ مدیریتی) Estimation · Sales · Marketing · Operations · Compliance · Knowledge-Manager · Automation. جزئیات و system promptها: `MASTER_INSTRUCTIONS.md` و KB-01/10.

## ۵. وضعیت
- لایهٔ تئوریِ سیستم: **کامل و سازگار** (CONSISTENCY_REPORT).
- لایهٔ عملیاتی: **اضافه شد** (OPS-00..09).
- رابطِ تلگرام: **طراحیِ تئوری آماده** (TG-01).
- **بازماندهٔ پیش‌از‌کد (ورودیِ Operator):**
  - CONFIG: `fx_aud_usd`، Google Places per-request، `spam_penalty_units`، `allowed_operator_chat_ids`، `telegram_bot_token`.
  - KB-02: `avg_margin_per_job`، `enquiry→quote rate`، `quote→job rate`.
  - مرجع: آپلودِ `LANGAR_kit_1/2.pdf`.
  - تأییدِ حقوقیِ NSW: قلم‌های `[verify-NSW]` در OPS-09/KB-12 (DEEP_RESEARCH_PROMPT R-1).

## ۶. قدمِ بعدی
۱. پر کردنِ ورودی‌های §۵. ۲. تصمیم دربارهٔ سگمنتِ Capital Works (KB-00 §۵). ۳. ثبتِ «تصمیمِ ۸: تلگرام» در BLUEPRINT. ۴. شروعِ فاز ۰ (scaffold/reuse) طبقِ ROADMAP.

> برای جزئیات: `PROJECT_MANIFEST` (فهرست/گیت)، `BLUEPRINT` (معماری)، `ROADMAP` (فازها)، `KB-00` (نقشهٔ متصل)، `OPS-00` (نقشهٔ عملیات).
