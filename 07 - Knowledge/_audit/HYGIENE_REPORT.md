---
title: HYGIENE_REPORT — 07 - Knowledge
created: 2026-07-05
---

# 🧹 HYGIENE_REPORT — بهداشت، نسخه‌ها، نام‌گذاری

## ۱. خوشه‌های نسخه‌ای — وضعیت واقعی بهتر از انتظار

| خوشه | فایل‌ها | وضعیت | پیشنهاد canonical |
|---|---|---|---|
| MAP | `MAP.md` + `MAP.proposal.md` | ✅ حل‌شده — proposal با فرانت‌متر `superseded` علامت خورده | `MAP.md`؛ proposal پس از یک دوره به آرشیو |
| PROJECT | `PROJECT.md` + `PROJECT.v2-proposal.md` | ✅ حل‌شده — همان الگو | `PROJECT.md` |
| jahan-e-fusion | `jahan….pdf` + `jahan…_CORRECTED.md` | ⚠️ نیمه‌حل — MD طبق تصمیم ۸ «جایگزین مرجع PDF» است ولی PDF هنوز کنارش است بدون علامت | canonical = `_CORRECTED.md`؛ PDF → آرشیو یا برچسب «superseded» |
| heart-awareness-map | `heart-awareness-map.pdf` + `-v2.html` + `-v3.html` (ریشه) + `heart-awareness-map.html` (Neuro-HRV-Nof1) | ❌ حل‌نشده — ۴ نسخه، ۲ پوشه، هیچ‌کدام علامت canonical ندارد | پیشنهاد: `Neuro-HRV-Nof1/heart-awareness-map.html` (در context بسته‌ی handoff استفاده می‌شود و مرجع E1–E5 است) canonical؛ بقیه آرشیو. تصمیم نهایی با تو |
| AUDIT لنگر | `AUDIT - لنگر (v1).md` | ✅ قابل‌قبول — v1 تاریخچه است، خروجی‌اش در PERSONA v2 اعمال شده | نگه‌دار؛ اگر AUDIT v2 آمد، v1 آرشیو |
| PROJECT_EXPORT_COMPLETE | snapshot 149KB از کل زیرپروژه | ⚠️ ریسک واگرایی — از ۰۷-۰۲ است و فایل‌های زنده از آن جلو افتاده‌اند (P4–P7) | برچسب صریح «snapshot تاریخی — به‌روز نیست» در سرصفحه، یا حذف پس از اطمینان |

## ۲. پراکندگی فرمت
۱۱ PDF + ۳ HTML در کنار ۸۰ MD. برای RAG/گراف فقط MD قابل‌کوئری است. PDFهای canon فیوژن (masque، mutuality، warp-machine، build-roadmap، multiagent-checklist) و `LANGAR BLUEPRINT` و `PATTERNS OF TRANSFORMATION` و `10 AI VARIABLES` **هیچ نسخه‌ی MD ندارند** — کاندیدای استخراج متن.

## ۳. نام‌گذاری

| مشکل | نمونه | شدت |
|---|---|---|
| دو فاصله در نام پوشه‌ی اصلی | `هیپنوتیزم␣␣و خودآگاهی` | 🟠 مستند شده ولی هر مسیر دستی را می‌شکند |
| غلط املایی پوشه | `تمرینات ورزشب`، `ویتامینای مفید` | 🟡 (با نقشه‌ی Master هم ناسازگار است) |
| فارسی/انگلیسی/فینگلیش مخلوط | `jahan-e-fusion`، `Hamfazi_Qodrat`، `تحقیق مخفی` | 🟡 اصطکاک، نه بحران |
| تصادم case-insensitive | `Roadmap.md` (KB) vs `roadmap.md` (Silabi-Bot) | 🟢 پوشه‌ها جدا؛ فقط برای ابزارهای case-insensitive گیج‌کننده |
| نام فایل با @ و timestamp | `photo_786@02-07-2026_06-58-58.jpg` | 🟢 |

## ۴. ناهمگونی متادیتا
- زیرشاخه‌ی فیوژن هیپنوتیزم: همه `epistemic_status: speculative` گرفته‌اند حتی فایل‌های fiction-canon (مثل `CONTEXT_handoff_EN` که `fiction-canon` دارد ولی THEORY و ۱۰۰-پرامپت‌ها `speculative`اند) — طبق `_TagSpec` باید یکدست شود.
- `Report - HRV` تگ `peer-reviewed` دارد که برای «بریفِ» شواهد شاید overclaim باشد (خود بریف می‌گوید برآوردها احتمالاً بیش‌برآوردند).
- فایل‌های txt (تحقیق مخفی، دیتا، Plan is to copy) فرانت‌متر ندارند.

## ۵. ۲۰ اقدام سریع پیشنهادی (کم‌هزینه → پرهزینه)

1. fix لینک `[[ROTATION_CHECKLIST]]` در PROJECT.md (۳۰ ثانیه).
2. به‌روزرسانی MAP.md: گره «P4 تا P7 نساخته» → کامل.
3. به‌روزرسانی Projects.md و Roadmap.md به وضعیت ۸/۸.
4. تیک‌زدن آیتم توکن در TODO.md با یادداشت «کد اصلاح شد؛ revoke با owner».
5. سرصفحه‌ی «snapshot تاریخی» روی PROJECT_EXPORT_COMPLETE.md.
6. برچسب superseded روی `jahan-e-fusion-gostaresh.pdf`.
7. انتخاب canonical برای heart-awareness-map (تصمیم تو) + علامت‌گذاری سه نسخه‌ی دیگر.
8. تغییرنام `تمرینات ورزشب` → `تمرینات ورزشی` و `ویتامینای مفید` → `ویتامین‌های مفید` (لینک ورودی ندارند؛ امن).
9. فرانت‌متر حداقلی برای `تحقیق مخفی.txt` → تبدیل به `.md` با نام گویا.
10. کپشن/متادیتا برای عکس `photos/`.
11. یکدست‌سازی `epistemic_status` فایل‌های Fusion-World به `fiction-canon` طبق _TagSpec.
12. تصمیم چهار placeholder (خویشتن، فیوژن آگاهی، دیتوکس، ویتامین‌ها): پر یا حذف.
13. افزودن wikilink از INDEX.md (KB) به فایل‌های اصلی — یا حداقل یک MOC پل بین دو رژیم لینک.
14. استخراج MD از `LANGAR BLUEPRINT.pdf` (پرلینک‌ترین PDF مفهومی).
15. استخراج MD از PDFهای canon فیوژن (۵ فایل).
16. ثبت اولین لاگ تمرین واقعی در _Index Practice vs Theory (سیستم آماده است، داده صفر).
17. خروج `Marathon/امواج مغزی/` از vault → cold storage رمزنگاری‌شده (فقط `ARMIN_DNA_REPORT.md` بماند). ⚠️ `دیتا.txt` تمرینات هم مشتق DNA است — همراهش برود یا بی‌هویت‌سازی شود.
18. خروج `GenomeInsight….pdf` (۱.۷MB) همراه مورد ۱۷.
19. بازبینی scope دو `_PROJECT_INSTRUCTIONS` (ریشه‌ی backup vs فیوژن) — یک خط scope بالای هرکدام.
20. اجرای دوره‌ای همین ممیزی (ماهانه) + نگه‌داری خروجی‌ها در `_audit/` با تاریخ.
