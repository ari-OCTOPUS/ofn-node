---
type: project
kind: project
project: "[[03 - Projects/WLOS - Weight Loss OS/PROJECT]]"
status: active
owner: آری
start: 2026-07-19
tags: [health, coaching, telegram]
created: 2026-07-20
updated: 2026-07-20
---

# پروژه: WLOS — Weight Loss OS (WLOS-Sydney-1)

**هدف:** سیستم‌عامل شخصیِ کاهش وزن مالک — کوچ تلگرامی فارسی‌محور با چک‌این روزانه، موتور تغذیه/تمرین، و لایه‌های ایمنی چندگانه. ساخته‌شده در جلسهٔ ابری جدا؛ نسخهٔ v0.1.1 (vertical slice کامل + دیباگ‌شده، 135/135 تست سبز، هنوز live run نشده).

**نقش در اکوسیستم:** به‌دستور مالک (2026-07-20): «بده دست مغز اصلی باشه برای تعامل و شناخت با من» — یعنی WLOS اندامِ «شناختِ مالک» برای مغز اصلی OCTOPUS است، نه یک پای درآمدی. اتصال به cortex فقط از مسیر bridge پیشنهادی flag-off (پایین) و همیشه propose-only.

## مرزهای حریم خصوصی (سفت — قابل مذاکره نیست)

- دادهٔ سلامت/وزن/رفتار = دادهٔ دستهٔ ویژهٔ مالک. **هرگز** وارد چت، نوت، HANDOFF، لاگ یا commit نمی‌شود.
- DB (پستگرس محلی) و `.env` آن بیرون از git می‌مانند؛ `.env.example` عمداً وارد vault نشد (در زیپ Downloads مانده).
- bridge به cortex فقط خلاصهٔ sanitized و بدون شناسه‌ها را می‌خواند — همان قراردادی که خود WLOS برای Fugu دارد (LLM advisory، بدون هویت/تاریخچهٔ خام).

## کد و اسناد

- کد: `wlos/` (monorepo TS — bot/api/worker + ۱۰ پکیج؛ ~117 فایل TS؛ Prisma ~36 مدل)
- شروع خواندن: `wlos/HANDOFF.md` → `wlos/docs/product-requirements.md` → `wlos/docs/architecture.md` → `wlos/docs/assumptions.md`
- ثابت‌های امنیتی تست‌شده (خلاصه): Outbox تنها مسیر ارسال (SafetyClearance)؛ سقف ۲۰ پیام/روز + ساعت سکوت 00–07 سیدنی؛ یک سؤال در هر چک‌این؛ سه لایهٔ consent؛ کف کالری 1200F/1500M؛ LLM مشاور است نه قانون؛ self-mod هرگز auto-apply نمی‌شود.

## Active Context

- تمرکز فعلی: ورود به vault (2026-07-20) + تعیین نقش «اندام شناخت مالک» برای مغز اصلی.
- تغییرات اخیر: 2026-07-20 — کد v0.1.1 از zip وارد شد (بدون `.env.example`)؛ این شناسنامه ساخته شد.
- ۳ قدم بعدی: (۱) اولین اجرای زنده روی ماشین مالک: `.env` → `docker compose up -d postgres redis` → `prisma migrate dev` → seed → bot/worker/api → تست `/start` تا `/weekly` (۲) درسِ backup/restore پیش از استفادهٔ واقعی (۳) بعد از پایان اسکنِ حافظهٔ OCTOPUS: bridge حداقلیِ flag-off در `_ops/cortex/` (فقط خواندن خلاصهٔ sanitized هفتگی، default OFF).
- تصمیم‌های باز: زمان اولین live run (فقط مالک — نیاز به `TELEGRAM_BOT_TOKEN` جدا)؛ آیا خلاصهٔ هفتگی WLOS اصلاً وارد state ارگانیسم بشود یا فقط on-demand خوانده شود (رأی مالک).

## Progress

- چه کار می‌کند: vertical slice کامل: onboarding، چک‌این، موتور تغذیه (پارس فارسی)، triage ایمنی، JITAI، بانک ۲۵۷ سؤال، گزارش هفتگی؛ 135/135 تست + tsc سبز؛ ۹ باگ (۳ بحرانی، از جمله secret-baking داکر) در v0.1.1 رفع شده.
- چه مانده: اولین live run؛ درسِ restore؛ اتصال Fugu برای سنتز هفتگی؛ دکمه‌های self-mod؛ Mini App (فاز ۵)؛ bridge به مغز OCTOPUS (flag-off، بعد از اسکن).
- مشکلات شناخته: هرچه فقط-در-live معلوم می‌شود (محدودیت callback، رندر RTL)؛ acceptance #15 (restore drill) هنوز ⚠️.

## Next actions

- [ ] (مالک) اولین live run طبق `wlos/HANDOFF.md` §5.1
- [ ] (مالک) درس backup/restore — `wlos/docs/deployment.md` §backup
- [ ] (ایجنت، بعد از اتمام delta-scan) bridge پیشنهادی flag-off به cortex — propose-only، بدون PII، default OFF
- [ ] (مالک) رأی: سطح دسترسی مغز اصلی به خلاصه‌های WLOS

## نوت‌های مرتبط

- `wlos/HANDOFF.md` (نقشهٔ کامل repo + گوچاها) · `wlos/docs/` (۱۷ سند)
- [[04 - Architect System/ANALYSES/2026-07-20_LEGS-DEEP-SCAN|LEGS-DEEP-SCAN]] (زمینهٔ تصمیم الحاق)
