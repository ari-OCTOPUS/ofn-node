---
type: project
kind: area
project: "[[03 - Projects/Ziman Galerry/PROJECT]]"
status: active
owner: آری
risk_level: low
autonomy_level: read-only
tags: [marketing, branding, sydney]
created: 2026-07-03
updated: 2026-07-06
---

# پروژه: Ziman Gift (Ziman Galerry)

> 🏗️ **رکنِ ساخت:** [[04 - Architect System/MYCELIAL-MASTER-SPEC|MYCELIAL-MASTER-SPEC]] — این پروژه یک node در §۳ رجیستریِ اتصال است (build/test/delete پشتِ verdict).

## Mission

بیزنس محلی آنلاین در سیدنی — برندسازی و بازاریابی، **با ظرفیت تولید به‌عنوان سقف سخت همه برنامه‌ها** (D4): اول ظرفیت، بعد کمپین.

## Current state (شواهد)

- محتوای vault: فقط همین شناسنامه — هیچ نوت کمپین/برند ساختاریافته‌ای قبل از امروز نبود `[Verified: ls پوشه]`
- سقف ظرفیت: `[Estimate — production owner]` — **عدد هنوز ثبت نشده؛ منتظر مالک** → [[03 - Projects/Ziman Galerry/Capacity & Channels|Capacity & Channels]]

## Assets & resources

هویت برند: **Bloom rose-gold** `[Assumption — چک‌لیست دارایی در نوت ظرفیت]` · تولیدکننده: production owner (شریک/خانواده `[To measure]`) · کانال‌ها: هنوز انتخاب نشده

## Active workstreams

1. ثبت عدد سقف ظرفیت (units/week) از production owner. 2. چک‌لیست دارایی برند. 3. اولین آزمایش کانال — فقط زیر سقف.

## KPIs

units/week نسبت به سقف · سفارش per کانال `[To measure]` · هزینه per سفارش `[To measure]`

## Agent interface

- **می‌خواند:** این manifest، نوت ظرفیت/کانال‌ها.
- **می‌نویسد:** draft محتوا/کمپین، گزارش آزمایش کانال.
- **قید سخت (D4):** هیچ draft کمپینی که تقاضای بالاتر از سقف ظرفیت بسازد تولید نمی‌شود — ایجنت باید رد کند و دلیل بیاورد.
- **verdict انسانی:** انتشار هر پست/کمپین، هر خرج.
- **Security Gate:** read-only تا بسته شدن CRITICALها.

## Open blockers

عدد ظرفیت ثبت نشده → همه برنامه‌ریزی کمپین مسدود است (by design).

## Active Context

- **2026-07-06 (جلسه ۱۷):** کد پروژه به `_code/` منتقل شد (B1 پلن NONMD-TRIAGE؛ propose→executed با verdict آری). لاگ کامل: `00 - Inbox/nonmd-move-log-2026-07-06.csv`.
- **2026-07-06 — Ziman Live:** کپی قابل‌اجرای control-brain + ziman-agent در `_launchpad/ziman-live/` با setup wizard ‏(HTML، ‏localhost:8877) و `START-HERE.bat` — منتظر اولین اجرای آری با توکن تلگرام نو. v2 = کاستوم‌سازی UI داشبورد.

- تمرکز فعلی: گرفتن عدد ظرفیت از production owner
- تغییرات اخیر: 2026-07-03 — ارتقا به manifest فاز ۱ + نوت Capacity & Channels · 2026-07-04 — ۲۰ عکس WhatsApp → `08 - Assets/Photos/WhatsApp-2026` و `files.zip` → `_Archive` (قواعد ۳ و ۶ قانون اساسی؛ رفع یافته M18 نقشه روابط v3) · ⚠️ بخش «Current state» این نوت کهنه است — پوشه اکنون `control-brain/`، `ziman-agent/` و چند نوت سیستم دارد (آپدیت در جلسه Ziman) · 2026-07-04 — کیت مغز پروژه (INDEX·DecisionLog·OpenQuestions طبق LIVING-BRAIN-BLUEPRINT) ساخته شد
- ۳ قدم بعدی: (۱) ثبت عدد ظرفیت [Estimate] (۲) تکمیل چک‌لیست برند (۳) طراحی آزمایش کانال #۱ زیر سقف
- تصمیم‌های باز: کانال اول (IG محلی؟ مارکت‌پلیس؟) `[To measure]`

## Progress

- چه کار می‌کند: برند Bloom تعریف اولیه دارد
- چه مانده: ظرفیت، کانال، اولین کمپین
- مشکلات شناخته: بدون عدد ظرفیت، هر برنامه‌ای هواست

## Next actions

- [ ] ثبت units/week از production owner → تگ [Estimate]
- [ ] بعد از اولین هفته تولید پایدار → ارتقا به [Measured]
- [ ] آزمایش کانال #۱

## نوت‌های مرتبط

- [[03 - Projects/Ziman Galerry/Capacity & Channels|Capacity & Channels]] · [[04 - Architect System/architect/ARCHITECT_CHARTER|ARCHITECT_CHARTER]]
