# LANE REPORT — FAULT-LLMLEARN-20260908

GOV_VERSION=V8 · LADDER=L2
شروع: 2026-09-08 ~11:00 local · پایان: ~12:00 local · شاخه: rescue/octopus-live-tree-20260821
ورودی: مگاپرامپت نیمروز ۲۰۲۶-۰۹-۰۸ (بخش ۳، اولویت‌های ۱، ۳، ۴)

## چه شد (خلاصهٔ ۳۰ ثانیه‌ای)
شکستِ تکرارشوندهٔ `pump/llm_learn` و خوشهٔ `paid-call-failed` **یک ریشهٔ مشترک**
داشتند: مسیرِ paid ارگانیسم سه‌لایه بسته بود — (۱) پینِ FX دیروز با anchorِ اشتباه
(۰۰:۰۰Z به‌جای ۰۶:۰۰Z مرجعِ RBA) ساعت ۱۰ صبح منقضی شد، (۲) بیتِ `OCTOPUS_PAID_COGNITION`
هیچ‌وقت در دیمن نبوده، (۳) fallback محلی هم روی برخوردِ rate-limitِ ۱۰ثانیه‌ای بی‌دریغ
می‌مُرد و هیچ لاگی از علتش نمی‌ماند. هر سه لایه تعمیر شد؛ llm_learn امشب با fallbackِ
محلیِ مقاوم‌شده و مسیرِ paidِ سبز (برای شل‌ها) اجرا می‌شود.

## کارهای انجام‌شده
1. **ریشه‌یابی کامل** (`ROOT-CAUSE-RECEIPT.json`): چهار لایه با شاهد برای هرکدام.
   - تاریخچهٔ llm_learn: ۴ شکست (۰۸-۲۸، ۰۹-۰۴، ۰۹-۰۷، ۰۹-۰۸)؛ موفقیت‌ها همیشه tier=local بودند.
   - paid-calls: ۵ تماسِ موفق در کلِ تاریخ، همه دستیِ شبِ FX-1.
   - توالیِ بلاکرها دیشب/امروز: fx_expired (پینِ کهنهٔ ۰۸-۲۰) → پس از پینِ FX-1: PAID_COGNITION_PAUSED (~۱۱ ساعت) → fx_expired دوباره از ۱۰:۰۱ (نقصِ anchor).
2. **فیکس FX (F1)** (`FX-PIN-CORRECTION-20260908.json`): تصحیحِ anchor پینِ ۰۷-سپتامبر به
   ۰۶:۰۰Z (نرخ/رسید/منبع دست‌نخورده؛ بکاپ `.bak-fxpin-20260908`)؛ اثباتِ زندهٔ رفرشِ RBA
   (بایت‌به‌بایت یکسان؛ ردیفِ ۰۸-سپتامبر هنوز منتشر نشده). گیت سبز شد و **یک فراخوانیِ
   تأییدِ paid طبقِ رویهٔ مستندِ FX-1**: deepseek-v4-flash → «OPERATIONAL»، stop،
   $0.0000281، رسیدِ هزینه `paid-primary-1788830740590`.
3. **فیکس مقاوم‌سازی local (F2+F3)**:
   - `local_llm.py`: دلیلِ هر شکست حالا شاهدِ بی‌محتوای دیسک دارد
     (`state/pulse/local-llm-failures.jsonl`: rate_limited/post_failed/empty_response) + `last_fail_reason()`.
   - `model_router.py`: اگر fallbackِ نهایی فقط به rate-limit خورد، **یک retryِ کران‌دار**
     بعد از پنجره (env `LOCAL_FALLBACK_RETRY_S`، پیش‌فرض ۱۱s، 0=خاموش). تماسِ روزانهٔ
     یادگیری دیگر با یک برخوردِ ۱۰ثانیه‌ای نمی‌میرد.
4. **ری‌استارت تمیزِ ارگانیسم (F4)**: نسخهٔ ۹۰۰ثانیه‌ایِ اسکریپتِ ری‌استارت
   (`restart-organism-patient.ps1`) — چرخهٔ تیک > ۳۰۰s است (علتِ شکستِ ظاهریِ صبح)؛
   PID 25772 خروجِ تمیز کرد، PID **6956** از 11:45:37 تیک می‌زند (تأیید شد).
5. **سؤال «۰ نوتِ سمانتیک» مگاپرامپت — پاسخ: by-design، یال سالم است.**
   ۳۲۲ نوت از ۰۸-۱۱؛ دیروز ۴ نوت؛ امروز صفر چون هر سه رویدادِ برجستهٔ امروز
   (شکستِ llm_learn ×2، خودترمیمیِ lead-naghshi) salience را رد می‌کنند ولی
   **gistِ عیناً تکراری** دارند و گیتِ dedup (اصلاحِ ۰۸-۱۶ ضدِ اسپم ×۶۴) عمداً جلویشان را
   می‌گیرد (سنجش با توابعِ واقعیِ consolidate). محافظه‌کاریِ شناخته‌شده: کلیدِ dedup =
   رشتهٔ summary؛ رخدادهای متمایز با summaryِ یکسان یکی می‌شوند. تغییری ندادم.
6. **تصمیمِ بازی‌نشده → مالک** (`07-HANDOFF/OWNER-DECISION-PAID-COGNITION-20260908.md`):
   روشن‌کردنِ مغزِ paid دیمن = قابلیتِ L3 در نردبانِ V8؛ سطح فعلی L2؛ ایجنت نمی‌تواند
   خودش بازش کند. کارتِ یک‌کلمه‌ای + مراحلِ اجرا/rollback آماده است.

## شواهد
- `ROOT-CAUSE-RECEIPT.json` · `FX-PIN-CORRECTION-20260908.json` · `RUNBOOK-FX-DAILY.md` (همه در همین پوشه)
- `_ops/cortex/pricing_pinned.json` (+ دو بکاپ) · `_ops/state/wedge/rba-f111-fetch-20260908.csv`
- `_ops/state/paid-calls.jsonl` ردیفِ 11:25:40 ok=true · `_ops/state/cortex/cost-receipts.jsonl` trace paid-primary-1788830740590
- کد: `_ops/cortex/local_llm.py` · `_ops/cortex/model_router.py` · تست‌ها: `_ops/tests/test_cortex.py` (t_b3, t_c9)

## تست‌ها
- test_cortex: **8/18** = baseline 6/16 + ۲ تستِ جدیدِ سبز؛ ۱۰ شکستِ **ازقبل** (AttributeError
  روی سمبل‌های غایب در cortex.py: truth_sync_tick/run_cycle/_Handler/hypothesis_brain_run/…) — دست نخورده توسط این لِین.
- test_heart_work **11/11** · test_brain_cortisol 7/10 (۳ شکستِ ازقبلِ هم‌جنس) · test_doctor_selfknowledge سبز.

## چه مانده
- **پینِ ۰۸-سپتامبر**: بعد از ~۱۶:۳۰ local طبق `RUNBOOK-FX-DAILY.md` (پینِ فعلی ۱۶:۰۰ می‌میرد؛ شکافِ ≤۳۰ دقیقه fail-closed).
- **رأی مالک**: مغزِ paid دیمن (کارتِ بالا) + ورودی‌های ماندهٔ مگاپرامپت (شمارهٔ نمایش، دامنهٔ مینی‌اپ، سرویس search/تماس).
- ۱۰ شکستِ ازقبلِ test_cortex/test_brain_cortisol روی cortex.py (لِینِ جداگانه لازم دارد).
- طوفانِ `deep` هر ~۱۰۰ثانیه (۲۲:۵۷→۰۹:۴۶ و ۰۷:۲۱→۰۸:۵۷؛ fail-fast، هزینه صفر): مشاهد شد؛
  با cognitionِ خاموش بی‌ضرر است؛ اگر مالک گزینهٔ B را رأی داد، سقفِ bucket آن را مهار می‌کند.

## افزودنی پس از رأی مالک (~۱۲:۱۰–۱۲:۱۵ local) — «روشن» اجرا شد
مالک روی کارتِ `OWNER-DECISION-PAID-COGNITION-20260908.md` گزینهٔ B را رأی داد (+
الحاقهٔ آزادیِ ارائه‌دهنده: DeepSeek/Claude/هر مدل لازم — ثبت در OWNER-APPROVALS دور ۶،
R4-1/R4-2). اجرا: دو فلگ به `_ops/OCTOPUS-flags.cmd` (pre-image `731227ea75563a28` →
post `56d1e3e031988fbf`)؛ ری‌استارت با پروتکل بومیِ `RESTART-REQUESTED` (خروجِ تمیزِ
۶۹۵۶ بعد از ~۵۹۲ث؛ لانچر مارکر را پاک و PID **5260** را با env تازه بالا آورد)؛
snapshot فلگ‌ها تأیید (`flags-loaded-organism.json` pid=5260، هر دو فلگ حاضر)؛
**اولین تماس paid موفقِ دیمن در تاریخ**: 12:08:35 task=deep primary deepseek-v4-flash ok
(۱۲.۰s). محافظ‌ها دست‌نخورده؛ زیرِ L3 رسمی می‌ماند. جزئیات:
`PAID-COGNITION-EXECUTION-20260908.json`. **پین FX روزانه (بعد از ۱۶:۳۰) حالا مهم‌تر
شد — بدون آن مسیر paid دیمن امشب دوباره بسته می‌شود.**

## Rollback (کامل)
1. `cp _ops/cortex/pricing_pinned.json.bak-fxpin-20260908 _ops/cortex/pricing_pinned.json`
2. `git revert` کامیتِ این لِین (کدِ local_llm/model_router/تست‌ها)
3. حذفِ دو خطِ `set` از `_ops/OCTOPUS-flags.cmd` (بازگشت به pre-image `731227ea…`) + ری‌استارت
(رسیدها و فایل‌های لِین حذف نمی‌شوند — §۱ زنجیرهٔ رسید.)
