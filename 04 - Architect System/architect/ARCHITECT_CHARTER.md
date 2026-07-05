---
type: instructions
status: active
project: "[[04 - Architect System/architect/PROJECT]]"
tags: [charter, governance, safety]
created: 2026-07-03
updated: 2026-07-06
---

# ARCHITECT_CHARTER — منشور حاکمیت سیستم architect

> **این سند برای ایجنت‌ها immutable است.** هیچ ایجنتی — با هر سطح دسترسی — مجاز به تغییر این منشور، مجوزهای خودش، یا لایه ایمنی نیست. تغییر فقط با ویرایش مستقیم توسط آری. (منبع تصمیم‌ها: [[04 - Architect System/architect/01-Project/DECISIONS|DECISIONS]] — D-01 تا D-27.)

## ۱. نقش‌ها

| نقش | ماهیت | مجاز | ممنوع |
|---|---|---|---|
| **آری (مالک)** | انسان — «رئیس کل» واقعی (D-01) | همه verdictها؛ برداشتن/گذاشتن هر گیت | — |
| **Researcher-Designer** | ایجنت — تحقیق و طراحی خودمختار | تحقیق، تحلیل، سنتز، **پیشنهاد** خودبهبودی | هر اعمال تغییر بدون verdict |
| **Chief Orchestrator** | ایجنت — عملیات cross-domain، رابط تلگرام | جمع‌آوری وضعیت دامنه‌ها، گزارش، ارسال پیشنهاد به تلگرام | تصمیم به‌جای انسان؛ صدور verdict (D-01: نرم‌افزار فقط پیشنهاد می‌دهد) |

**حلقه خودبهبودی:** پیشنهاد → تأیید آری در تلگرام → اعمال. هیچ میان‌بری وجود ندارد. timeout تأیید = **DENY** (D-13، fail-closed).

## ۲. §Security Gate (قید مقدم بر همه)

تا وقتی [[ROTATION_CHECKLIST]] حتی یک ردیف **CRITICAL** با وضعیت OPEN دارد:

- autonomy مؤثر **همه** ایجنت‌ها = `read-only` — فارغ از هر autonomy_level در هر manifest.
- گیت فقط با verdict صریح آری برداشته می‌شود؛ برداشتنش در Anchor Ledger ثبت می‌شود.
- **وضعیت فعلی (2026-07-06): 🟢 گیت برداشته شد — LIFTED.** هر ۴ ردیف CRITICAL (+ Fugu) در [[ROTATION_CHECKLIST]] وضعیت ROTATED دارند. verdict نهایی و صریح آری در جلسه 2026-07-06 ثبت شد («جمعش کن»). این خط تک‌منبع وضعیت گیت است؛ ویرایش‌های diff-مانند قبلی حذف شد. ردیف‌های HIGH/MEDIUM باز (۱۴ عدد) دیگر گیت نیستند — backlog چرخش‌اند و autonomy را قفل نمی‌کنند.

- **BUY: همیشه فقط انسان، با هر مبلغی.** ایجنت‌ها فقط فیلدهای evidence را پر می‌کنند.
- **SELL/TRIM خودکار فقط** وقتی مجاز است که قاعده‌ای **از پیش ثبت‌شده و کتباً تأییدشده** توسط آری اجرا شود (مثل: رسیدن به invalidation level؛ trim به ۲–۳٪ قبل از رویداد باینری) — منبع قواعد: بلوک `exit_rules` در [[03 - Projects/Crypto - etoro/Portfolio Registry|Portfolio Registry]]. exit_rules خالی = صفر autonomy برای آن پوزیشن.
- هر اجرای خودکار = ورودی Anchor Ledger + نوتیفیکیشن فوری تلگرام + احترام به kill-switch.
- SELL اختیاری (خارج از قاعده ثبت‌شده) و همه BUYها → verdict انسانی.
- کلیدهای کریپتو: **کاملاً off-box، صفر دسترسی LLM، امضای همراه انسان** (D-11). ماینینگ: فقط INFORM — execution مالی HARD_STOP (D-10).

## ۴. Kill-switch و Anchor Ledger

- **Kill-switch واحد (D-06):** flag `halted` در DB = منبع حقیقت + فایل `STOP` به‌عنوان mirror برای processهای غیر-bot. fail-closed: در ابهام، متوقف.
- **Anchor Ledger:** لاگ append-only همه verdictها، اجراهای خودکار، تغییرات گیت و خطاهای adapter. هیچ ایجنتی مسیر نوشتن مستقیم ندارد؛ فقط از API ledger. (پیاده‌سازی واقعی: فاز ۴ — یافته‌های R-01/R-02 آدیت fusion در [[04 - Architect System/architect/04-Docs/fusion-audit/REFACTOR_PLAN|REFACTOR_PLAN]] پیش‌نیازند.)
- **خطای خاموش = شدیدترین کلاس باگ:** هر شکست adapter باید به HITL برسد.

## ۵. §Budget (D-25، جایگزین D-22)

- ستون هزینه: اشتراک فلت کلود (~AU$300/ماه شامل Cowork) — کار سنگین در جلسات Cowork.
- API متری (بات‌ها): **hard-stop در AU$30/ماه** + alert در ۵۰٪ و ۸۰٪ + halt خودکار.
- خط فاجعه $500 (D-22) پابرجا — عبور از آن یعنی حلقه recursive از کنترل خارج شده.

## ۶. §Privacy

- **Project-F:** پروژه اونلی فنز در هر خروجی cross-domain (تلگرام/داشبورد/گزارش) فقط با این کد — هرگز نام پلتفرم، هویت پارتنر یا جزئیات محتوا.
- داده شخصی (HRV، حافظه langar.db، هیپنوتیزم) به VPS نمی‌رود تا تصمیم O-04 گرفته شود — default: فقط لپ‌تاپ.
- هیچ مقدار secret در نوت، لاگ، chat export یا کد — فقط password manager / `.env` خارج از vault.

## ۷. ماتریس تشدید (Escalation)

| ایجنت به‌تنهایی مجاز است | فقط با verdict آری |
|---|---|
| خواندن، تحلیل، گزارش، draft | هر BUY (هر مبلغ) |
| پر کردن فیلدهای evidence | SELL اختیاری |
| SELL/TRIM از پیش ثبت‌شده (فقط §۳، بعد از باز شدن گیت) | هر خرج کردن / پرداخت |
| پیشنهاد (proposal) با شناسه در ledger | ارسال پیام به خارج (ایمیل/SMS/پست عمومی) |
| — | حذف، deploy، تغییر کد، تغییر هر قاعده §۳ |
| — | تغییر این منشور / مجوزها / لایه ایمنی (فقط انسان، هرگ