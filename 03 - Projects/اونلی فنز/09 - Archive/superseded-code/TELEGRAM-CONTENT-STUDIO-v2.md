---
type: proposal
project: "[[03 - Projects/اونلی فنز/PROJECT]]"
status: draft-for-build
created_by: agent
supersedes: "[[TELEGRAM-CONTENT-STUDIO-v1]]"
relates_to: "CLAUDE.md منشورِ Project-F"
tags: [project-f, telegram, content-studio, producer, research-grounded, propose-only]
created: 2026-07-09
updated: 2026-07-09
---

# CONTENT STUDIO v2 — تحقیق‌محور (نیازهای واقعیِ تولیدکننده)

> نسخهٔ v1 + آنچه تحقیقِ بازار نشان داد یک تولیدکنندهٔ محتوای OF واقعاً لازم دارد: تقویم، فیدِ ترند/ایده، پلنِ value-ladder/PPV، آنالیزِ تجمیعی، سگمنت‌بندی. همه workflow-محور، compliant، propose-only. قواعدِ قفل‌شدهٔ منشور حاکم.

## ۱. نیازهای واقعی (از تحقیق) → قابلیتِ بات
| نیازِ تولیدکننده (شواهد) | در بات |
|---|---|
| **value-ladder:** ~۵۵٪ روی wall، بقیه PPV `[FACT]` | 💡 پلنِ محتوا: تفکیکِ wall/PPV |
| **PPV سه‌لایه:** low-ticket/mid/premium، قیمت بر پایهٔ ارزشِ ادراکی `[FACT]` | 💡 پلنِ PPV: سه tier + پیشنهادِ قیمت (draft) |
| **افزایشِ تدریجیِ قیمت → ۳-۴× درآمد** `[FACT]` | 📈 یادآورِ نردبانِ قیمت |
| **KPIها:** churn هدف ۲۵-۳۰٪ · ARPU $۴۰-۸۰ · PPV-unlock ۲۲-۳۵٪ `[FACT]` | 📈 آنالیزِ **تجمیعی** (بدونِ PII فن) |
| **سگمنت:** VIP/معمولی/lurker + ۸۰٪ رابطه/۲۰٪ فروش `[FACT]` | 🎯 نکاتِ سگمنت (draft DM، human-gated) |
| **تقویم:** تمِ فصلی + اجرای ماهانه، زمانِ بهینه `[FACT]` | 🗓 تقویم + پیشنهادِ زمان |
| **تحقیق/ایده:** ترندِ نیش، کپشن/عنوان (AI-draft) `[FACT]` | 🔎 فیدِ ترند/ایده |

## ۲. سطحِ کاربری (HTML غنی)
```
🎬 استودیوی محتوا — Project-F
[📋 بریف‌ها]    [📤 ثبتِ درفت]
[🗓 تقویم]     [🔎 ترند/ایده]
[💡 پلنِ PPV]  [📈 آنالیز]
[🔒 قواعد]     [✋ محدودهٔ من]
```
- **🔎 ترند/ایده:** فیدِ تحقیق — ترندِ نیشِ faceless-feet، زمانِ بهینهٔ پست، ایدهٔ کپشن/عنوان (AI-draft، human-gated). این همان «تحقیقاتی که لازم داری».
- **🗓 تقویم:** تمِ فصلی → اسلاتِ ماهانه؛ پیشنهادِ زمان؛ **هیچ‌چیز خودکار publish نمی‌شود**.
- **💡 پلنِ PPV:** نردبانِ ارزش (wall vs PPV) + سه tier + پیشنهادِ قیمت (draft). پرداخت **فقط درون‌پلتفرم**؛ بات هرگز مذاکرهٔ پرداخت نمی‌کند.
- **📈 آنالیز:** KPIهای **تجمیعی** (churn/ARPU/unlock/retention) + سگمنتِ VIP/معمولی/lurker. **صفر PII فن در بات.**
- **📤 ثبتِ درفت:** شناسه + self-cert (`faceless ✅ · فقط‌پا ✅ · بدون explicit ✅ · ۱۸+/رضایت ✅`). رسانهٔ خام از بات رد نمی‌شود.
- **🔒 قواعد / ✋ محدوده:** چک‌لیستِ قفل‌شده + حاکمیتِ مطلقِ محدودهٔ صبا (یک‌ضربه halt).

## ۳. خطوطِ قرمز (baked)
بات فقط متادیتا/پلن/آنالیزِ تجمیعی — هرگز رسانه/هویت/PII فن · دوکلیده (صبا ثبت → آری تأیید → انتشارِ درون‌پلتفرم) · پرداخت فقط درون‌پلتفرم، صفر مذاکره · faceless-feet + ۱۸+/رضایت با self-cert · محدودهٔ صبا مقدم · geo-block ایران · allowlist/توکنِ جدا · صفر echo بیرونِ پوشه.

## ۴. پرامپتِ GLM
```
تو کارگرِ کدنویسِ Project-F (GLM) هستی. Content Studio را به v2 ببر (تحقیق‌محور). propose-only، sandbox، additive، commit با مالک. منشورِ Project-F حاکم.
بخوان: 03 - Projects/اونلی فنز/TELEGRAM-CONTENT-STUDIO-v2.md + v1 + CLAUDE.md + _ops/budget/approval_channel.py (الگو). PLAN بده. فایل زیرِ پوشهٔ Project-F، بات/توکنِ جدا.
بساز (HTML غنی، §۲): منو + بریف + ثبتِ درفت(self-cert) + تقویم + ترند/ایده(فید) + پلنِ PPV(۳ tier، draft قیمت) + آنالیزِ تجمیعی(churn/ARPU/unlock، بدونِ PII) + قواعد + محدوده.
خطِ قرمز (نقض=رد): فقط متادیتا/پلن/آنالیزِ تجمیعی، هرگز رسانه/هویت/PII فن · دوکلیده با آری · پرداخت فقط درون‌پلتفرم(صفر مذاکره) · self-cert اجباری · محدودهٔ صبا مقدم · geo-block · allowlist جدا · توکن env-only · صفر echo بیرونِ پوشه.
تست‌ها ($0): درفت تا تأییدِ آری «در انتظار» · self-cert اجباری · صفر رسانه/PII در پیام · محدوده→halt · آنالیز فقط تجمیعی · chat_id غیرمجاز ignore. خروجیِ خامِ تست را paste کن.
DoD: v2 تست‌سبز، ایزوله، دوکلیده، صفر رسانه/PII. commit دستِ مالک. هر ابهام → «⚑ برای معمار».
```

## Sources
- [OnlyFans PPV value-ladder (Pseudoface)](https://www.pseudoface.com/guides/start-here/profile-setup/onlyfans-wall-vs-ppv-value-ladder) · [Pricing 2025 (Sirency)](https://sirency.com/blog/onlyfans-pricing-strategy-guide-2025.html)
- [Analytics 15 KPIs (Sirency)](https://www.sirency.com/blog/onlyfans-analytics-metrics-tracking-guide) · [Retention 2026 (Sozee)](https://sozee.ai/resources/onlyfans-retention-best-practices-2026/)
- [Content calendar tools 2026 (Hootsuite)](https://blog.hootsuite.com/content-calendar-tools/)
