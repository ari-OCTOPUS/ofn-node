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

- **🚨 دامنهٔ `ziman-gift.com` مرده (2026-09-07T11:50Z، NXDOMAIN در 8.8.8.8/1.1.1.1/محلی):** صفحات محصول Shopify به این دامنه ۳۰۱ می‌شوند ⇒ مشتری نمی‌تواند صفحه را باز کند؛ صفر فروش ممکن است. خود فروشگاه سالم است (`ziman-gift.myshopify.com/products.json` = 200؛ ZM-GALLERY-0013 با A$45 موجود). (رسید: three-role run R-059570492a64)
  **رأی مالک (2026-09-07 شب):** اتصال مستقیم myshopify — مسیر ایجنت بسته است (توکن فقط read_orders+read_products+write_products؛ domains=404؛ permalinkها هم 301). **قدم باقی: خود مالک، ۲ دقیقه — Shopify admin → Settings → Domains → حذف ziman-gift.com یا myshopify primary.** تمدید دامنه بعداً.
- عدد ظرفیت ثبت نشده → برنامه‌ریزی کمپین مسدود (by design).

## Active Context


- سیزن درآمد فعال؛ msg38 ددلاین 2026-09-08T12:10Z (حامل state روی mesh؛ از laptop قابل خواندن نیست).
- **CHECKOUT-1 self-buy توسط مالک لغو شد** (OWNER-GO-OWNER-ANSWERS-20260907 آیتم ۱) — اثبات ریل = اولین سفارش واقعی؛ O-5 قطعی: PayPal Invoice (آیتم ۴).
- باز: تمدید GO (۰۹-۱۴)؛ گلوگاه ترافیک؛ **دامنهٔ مرده (فوق)**.

## Progress

- 2026-09-07 (شب): مأموریت سه‌نقشی G-3 اجرا شد — کاتالوگ زنده، ZM-GALLERY-0013 سالم (قیمت/موجودی/تصاویر PASS) ولی دامنهٔ مشتری NXDOMAIN → حکم نهایی: no. `checkout1_poll.py` ویندوز-ساز شد.
- 2026-09-07: تحویل مینی‌اپ + مینی‌اپ تلگرام زنده؛ U2 v2 task را resolve می‌کند.
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
