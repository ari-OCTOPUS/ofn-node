---
type: report
status: ready
tags: [governance, architecture, fugu-integration, security]
created: 2026-07-06
updated: 2026-07-06
created_by: agent
sources:
  - "[[04 - Architect System/architect/04-Docs/2026-07-06 0205 MASTER-ARCHITECTURE-SPEC-v1.1-draft]]"
  - "[[_memory/TWO-BRAIN-CONTROL-BLUEPRINT]]"
  - "[[_PROJECT_INSTRUCTIONS]]"
  - "[[_memory/PHASE-0A-EXCLUSION-SPEC]]"
  - "https://sakana.ai/fugu/"
  - "https://openrouter.ai/sakana/fugu-ultra"
---

# بازبینی MASTER-ARCHITECTURE-SPEC v1.1 — یافته‌ها برای verdict آری

> سند در [[04 - Architect System/architect/04-Docs/2026-07-06 0205 MASTER-ARCHITECTURE-SPEC-v1.1-draft|Inbox ثبت شد]] (proposal، نه canonical). این نوت فقط یافته‌های بازبینی است — تصمیم با آری.

## ۱. راستی‌آزمایی Fugu — ارتقا از تک‌منبع به چندمنبع ✅

سند فقط به RuntimeWire استناد کرده بود. web-search مستقل (2026-07-06):

- **Fugu واقعی است** — صفحات رسمی Sakana AI: `sakana.ai/fugu/`، `sakana.ai/fugu-release/`، `console.sakana.ai/pricing`؛ لانچ 2026-06-22؛ conductor مدل 7B بر پایه TRINITY + Conductor (ICLR 2026). در OpenRouter هم لیست شده.
- **قیمت‌ها match:** `fugu-ultra-20260615` = $5/$30/$0.50 per 1M؛ اشتراک $20/$100/$200. ✅
- **⚠️ عدد غایب در سند:** بالای 272K context نرخ تقریباً دو برابر می‌شود ($10/$45/$1.00) و context تا 1M — یعنی **یک call تمام-context می‌تواند به‌تنهایی ~$10+ هزینه داشته باشد**. برای C16 (سقف روزانه) این عدد حیاتی است.
- pool ثابت Ultra شامل مدل‌های GPT/Claude/Gemini از providerهای مختلف است — پایه ادعای C17 درست است.

## ۲. یافته بحرانی جدید — F4 خود-متناقض است 🔴

**F4 (Fugu به‌عنوان «تور دوم» اسکن secret در Gate 3) یعنی فرستادن محتوای مشکوک‌به-secret به یک API خارجی با pool ثابت third-party.** این خودش کانال نشت secret است و مستقیماً ناقض §۱۰ قانون اساسی و ناقض C17 خودِ همین سند. اسکن secret باید ۱۰۰٪ local بماند (gitleaks + regex روی host).
**پیشنهاد:** حذف F4، یا محدودش به metadata-only (نام فایل/الگوی مسیر، هرگز محتوا). این باید قبل از ratify حل شود.

## ۳. تناقض عددی بودجه (C16 هنوز حل نیست)

§۱۴.۶ می‌گوید مصرف Fugu باید در پنجره Normal ($2/روز · $60/ماه) بماند، اما اشتراک Ultra خودش $20–$200/ماه است — یعنی فقط اشتراک می‌تواند از کل سقف ماهانه Normal بزرگ‌تر باشد. باید صریح شود: (الف) کدام tier خریده شده؛ (ب) مصرف subscription-based جدا حساب می‌شود یا داخل سقف؟ (ج) سقف per-call با توجه به نرخ >272K.

## ۴. auto-renew در برابر فلسفه D-22

«auto-renew روشن تا منقضی نشود» با اصل «رشد مصرف = تصمیم آگاهانه انسان، نه خزش خاموش» ناسازگار است. پول human-only است و آری خودش خریده — مشکلی نیست؛ اما حداقل مهار: ردیف «مرور اشتراک Fugu» در Weekly Review + ثبت هزینه ماهانه در ledger. (نکته: پیشنهاد لغو auto-renew نمی‌دهم؛ فقط مرور دوره‌ای.)

## ۵. یک over-claim در §۱۴.۶

«مکانیزم kill از قبل در معماری هست» — دقیق‌تر: در **سند** هست؛ runtime لایه مادر هنوز deploy نشده (فاز ۴ ⏳ طبق SYSTEM_MAP). تا آن موقع تنها kill واقعی برای Fugu = revoke کلید + لغو اشتراک از کنسول (هر دو human-only).

## ۶. نرمال‌سازی‌های انجام‌شده هنگام ثبت (شفافیت کامل)

متن آری عیناً حفظ شد به‌جز: frontmatter با schema سازگار شد (`architecture-spec`→`architecture`؛ کلیدهای `revision/subject/owner/related/supersedes` حذف — مقادیرشان در callout ثبت است)؛ چهار خطای تایپی مدل مبدأ (`آسیم`→آسیب · `dữه`→داده · `هوینت`→هویت · «proposed، proposed» تکراری)؛ ردیف satellite‌ها که «جزئیات در گزارش» بود با مقدار واقعی (Self-Improvement Lab · Tenant Adapters) پر شد؛ لینک‌های خام runtimewire به متن ساده تبدیل شد. اگر عین نسخه اصلی را می‌خواهی، بگو تا untouched هم کنارش ثبت شود.

## ۷. سازگاری با vault — چک شد

- سلسله‌مراتب مرجعیت سند با قانون اساسی سازگار است (خودش را زیر PROJECT_INSTRUCTIONS می‌گذارد ✅).
- §۱۴ (ادغام گزارش Replication Kit) امانت‌دارانه و دقیق است ✅.
- C1–C15 با وضعیت واقعی vault می‌خواند (Gate باز · git نبود · ۴ CRITICAL باز) ✅.
- هر دو validator بعد از ثبت این دو فایل اجرا شود (قانون §۱۱).

## ۸. verdictهای لازم (به ترتیب)

1. **F4:** حذف یا metadata-only؟ (پیشنهاد من: حذف)
2. **C16:** کدام tier خریده شده + سقف روزانه عددی + قاعده >272K.
3. **C17:** ratify سیاست segregation (Ultra فقط غیرحساس؛ Project-F هرگز).
4. ثبت ردیف کلید Fugu در [[ROTATION_CHECKLIST]] (فقط نام سرویس + وضعیت — خودت اضافه کن یا بگو من draft بزنم).
5. ارتقای سند از draft → ratify بعد از حل ۱–۳.
