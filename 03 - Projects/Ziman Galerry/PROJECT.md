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
updated: 2026-09-07
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


- تمرکز فعلی: سیزن درآمد باز شد ([[ACTIVE-SEASON-REVENUE-ON-LIVE-LOOP-20260907|ACTIVE-SEASON 2026-09-07]])؛ قفسه ۳۵ محصوله زنده، مسیر پول = PayPal Invoice.
- تغییرات اخیر: حسگر پول miswired بود ([[09-LANES/MP-V41-U1-20260907/LANE-REPORT|U1]] — repoint باز)؛ سه‌گانهٔ حساس مالی به آرشیو امن منتقل شد (`09-LANES/R2-SECRETS-20260907/R2-RECEIPT.json`).
- ۳ قدم بعدی: (۱) پیگیری msg38 NOT_PAID تا 2026-09-08T12:10Z؛ (۲) تصمیم CHECKOUT-1 (سه روایت ثبت‌شده)؛ (۳) repoint حسگر confirmed_revenue به زیمان.
- تصمیم‌های باز: تمدید standing GO (۰۹-۱۴)؛ گلوگاه ترافیک (محصول هست، بازدید نیست).

## Progress

- 2026-09-07: سیزن درآمد باز شد؛ R2 رمزهای مالی منتقل؛ حسگر پول miswired مستند شد.
- **۲۰۲۶-۰۸-۰۱ — چه کار می‌کند:** پای زیمان با نبضِ تازه می‌تپد (سایدکار ۱۳:۱۸، ‏beat ‏21180) و دایجستِ تاپیکِ 🖼 را می‌دهد؛ ZimanLeg ‏propose-only، ‏D4، schemaهای محصول/موجودی و biology adapter سرِ جای خود.
- **۲۰۲۶-۰۸-۰۱ — چه مانده:** بی‌تغییر از ۰۷-۱۸ — عددِ ظرفیت از مالک، Product Cardهای واقعی، اجرای سوییتِ زیمان روی ویندوز، و روشن‌کردن یا حذفِ صادقانهٔ `OCTOPUS_ZIMAN_BRANDING`.
- **۲۰۲۶-۰۸-۰۱ — مشکلات شناخته:** `branding: null` یعنی موتورِ برندینگِ ساخته‌شده سه هفته است هیچ خروجی نداده — کدِ زنده‌ای که هرگز صدا نمی‌شود · `drafts_count=0` · ظرفیتِ ۳۰ و موجودیِ ۲۰ هر دو **[تأییدنشده]**اند و خودِ پا این را در دایجست اعلام می‌کند · سه کپیِ runtime هنوز می‌توانند drift کنند.
- چه کار می‌کند: ZimanLeg propose-only، D4، schemaهای محصول/موجودی، CLI محلی و اتصال organism ساخته شده‌اند. biology adapter نیز قلب→اعصاب→زیمان→دکتر را با مرزهای `σ≤1`، STOP-first، advisory-only و human-append پیاده می‌کند.
- چه مانده: اجرای تست‌های biology/wiring روی ویندوز، شمارش مالک، Product Cardهای واقعی، نقشهٔ عکس‌ها و آزمایش انسانی.
- مشکلات شناخته: 30/week و 20 inventory با ورودی مالک 50 محصول سازگار/تأیید نشده‌اند؛ سه کپی runtime می‌توانند drift کنند.

## Next actions

- [ ] ثبت units/week از production owner → تگ [Estimate]
- [ ] بعد از اولین هفته تولید پایدار → ارتقا به [Measured]
- [ ] آزمایش کانال #۱

## نوت‌های مرتبط

- [[03 - Projects/Ziman Galerry/Capacity & Channels|Capacity & Channels]] · [[04 - Architect System/architect/ARCHITECT_CHARTER|ARCHITECT_CHARTER]]
