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
updated: 2026-07-12
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

- **2026-07-12 — Calibration audit (Perception-Geometry):** ۴۰/۴۰ تستِ Ziman **واقعاً اجرا و سبز** شد (leg 17 + phase2/wiring 23 + smoke) → T11 ارتقا به VERIFIED (T16). ممیزی: [[03 - Projects/Ziman Galerry/00-Control/PERCEPTION-GEOMETRY-AUDIT-2026-07-12|CALIBRATION-AUDIT]] · handoff: [[03 - Projects/Ziman Galerry/11-Reports/Handoffs/PERCEPTION-PHASE2-HANDOFF|PERCEPTION-PHASE2-HANDOFF]]. ۵ conflict جدید (CF-06..CF-10): 🔴 D4 fail-open (گاردِ ۶/هفته unwired؛ گیت روی ۳۰ approve) · 🔴 درختِ ۴مِ `_launchpad/second-brain-live/` قابلیتِ SEND واقعی + PII + کلیدِ DeepSeek با برچسبِ Anthropic (ناقضِ zero-outward) · ATP fail-open روی timestampِ کهنه/آینده · memory کاملاً paper. همه propose-only؛ هیچ کد اجرا-تغییر/انتقال/اکشنِ بیرونی. (لایهٔ «biology» به‌طور هم‌زمان توسط پروسهٔ دیگری اضافه شد — خارج از دامنهٔ این ممیزی.)
- تمرکز فعلی: نرمال‌سازی موجودی و تکمیل اتصال propose-only به ارگانیسم.
- تغییرات اخیر: 2026-07-12 — Foundation Phase 2 و seam واقعی `organism → ziman_beat → ORGANISM-STATE.ziman` تکمیل شد. سپس پای زیمان زیرمجموعهٔ control-plane زیستی اختاپوس شد: قلب فقط ریتم می‌دهد، SignalHub اعصاب snapshot مشورتی می‌سازد، و دکتر تکاملی فقط از anomalyهای content-free یک RFC sandbox/propose-only می‌سازد. زیمان حق تغییر قلب، merge، انتشار، پیام، پول یا قیمت ندارد. قرارداد: `10-Interfaces/BIOLOGY-CONTRACT.md`.
- ۳ قدم بعدی: (۱) اجرای تست‌های Ziman روی ویندوز (۲) انتخاب دامنهٔ دسته‌بندی A/B/C (۳) شمارش مالک و اولین `inventory_snapshot.v1`.
- تصمیم‌های باز: دامنهٔ دسته‌بندی موجودی و نام عمومی برند؛ کانال اول پس از دادهٔ محصول/ظرفیت.

## Progress

- چه کار می‌کند: ZimanLeg propose-only، D4، schemaهای محصول/موجودی، CLI محلی و اتصال organism ساخته شده‌اند. biology adapter نیز قلب→اعصاب→زیمان→دکتر را با مرزهای `σ≤1`، STOP-first، advisory-only و human-append پیاده می‌کند.
- چه مانده: اجرای تست‌های biology/wiring روی ویندوز، شمارش مالک، Product Cardهای واقعی، نقشهٔ عکس‌ها و آزمایش انسانی.
- مشکلات شناخته: 30/week و 20 inventory با ورودی مالک 50 محصول سازگار/تأیید نشده‌اند؛ سه کپی runtime می‌توانند drift کنند.

## Next actions

- [ ] ثبت units/week از production owner → تگ [Estimate]
- [ ] بعد از اولین هفته تولید پایدار → ارتقا به [Measured]
- [ ] آزمایش کانال #۱

## نوت‌های مرتبط

- [[03 - Projects/Ziman Galerry/Capacity & Channels|Capacity & Channels]] · [[04 - Architect System/architect/ARCHITECT_CHARTER|ARCHITECT_CHARTER]]
