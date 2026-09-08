---
type: megaprompt
status: active-handoff
created: 2026-09-08 ~12:10 local (02:10Z)
tags: [octopus, megaprompt, handoff, audit]
gov: GOV-V8 · LADDER=L2
---

# مگاپرامپت — تحویل نیمروز ۸ سپتامبر ۲۰۲۶

تو ایجنت بعدی‌ای. این سند خودکفاست؛ قبل از هر کاری `AGENTS.md` و `07-HANDOFF/ENGINEERING-ENTRYPOINT-2026-09-04.md` را خوانده‌ای. GOV_VERSION=V8 · LADDER=L2 را اولِ گزارشت بنویس.

## ۱) وضعیت همین الان (همه با رسید)

- **فروشگاه زیمان روی دامنهٔ اصلی جدید زنده است**: `ziman-gift.com.au` = Shopify primary، Connected، TLS Let's Encrypt، صفحهٔ محصول 200 بدون ریدایرکت. رسید: `09-LANES/UNLOCK-REVIEW-20260908/DOMAIN-EXECUTION-STEP3-FINAL.json`. کش DNS محلی ISP تا چند ساعت صفحهٔ قدیمی GoDaddy را نشان می‌دهد — خودش پاک می‌شود؛ سرور نام معتبر (ns73.domaincontrol.com) درست است. `ziman-gift.shop` دست‌نخورده؛ پیشنهاد میزبان مینی‌اپ.
- **قفل‌های امروز باز شدند (رجیستری `01 - Dashboard/UNLOCK-REGISTRY-2026-09-08.md`)**: D0 دامنه · L23/L24/L25 (دیشب) · مرحلهٔ ۲ کامل («yes to all»: METABOLIC VERIFIED بدون تغییر کد، PRODUCTION flag روشن روی ۱۳۸، ۸ گیت moot پاک‌سازی، wire scope مستند) · دور پنجم (هویت تماس=زیمان/شماره pending، سرویس تماس معلق، مینی‌اپ GO).
- **مینی‌اپ زنده**: گیت‌وی :8774 + تانل named → https://app.master-painting.com (GET 200). انتقال به دامنهٔ زیمان = ران‌بوک ۳-کلیکی مالک: `07-HANDOFF/MINIAPP-ZIMAN-DOMAIN-RUNBOOK-2026-09-08.md` (توصیه: app.ziman-gift.shop).
- **اولین پکت‌های hold_external=false روی ۱۳۸ mint شد** (تیک 00:15Z، counter=2، transport ack) — نتیجهٔ رأی مالک دیروز.
- **ارگانیسم**: PID 25772 از 10:39 (پروسهٔ قدیمی 27200 حتی به STOP هم جواب نمی‌داد؛ force-kill با پیش‌چک + revive لانچر). کد جدید: چک D0 روی دامنهٔ جدید با ضد-پارکینگ، مصرف‌کنندهٔ صف `_ops/drive_queue_consumer.py` (فقط با رسید مصرف می‌کند؛ SBX هرگز؛ audit جدا).
- **بکاپ شبانه ریشه‌یابی و رفع شد**: از ~۰۹-۰۲ هر شب rc=1 چون `git fsck --full` روی ۱۸ آبجکت dangling (بی‌ضرر، صفر خرابی واقعی) غیرصفر می‌شد. گیت دقیق شد (فقط خطای واقعی کشنده)؛ خروجی تسک به `E:/germline/daily-last-run.log` رفت. **اجرای تأیید سوم در جریان است** (هر اجرا ~۱ ساعت). زنجیرهٔ کامل یافته: rc=1 از ~۰۹-۰۲ = fsck غیرصفر روی dangling‌های بی‌ضرر + گاه «missing tree» گذرای ناشی از race با نویسندگان همزمان (cat-file همان‌ها را موجود می‌یابد). گیت اکنون corruption-precise + race-hardened است. اگر run-3 (لاگ: `E:/germline/manual-run3-2026-09-08.log`) سبز شد مانیفست باید stamp امروز داشته باشد؛ اگر باز fail شد، لاگ را بخوان و خطِ کشنده را جدا کن.

## ۲) کار ارگانیسم از دیشب ۲۰:۰۰ تا امروز ۱۲:۰۰ (شواهد: `_ops/state/events.jsonl` + archive)

۴۸۷ رویداد. آنچه خودِ ارگانیسم بدون ایجنت انجام داد:
- ضربان و پایش پیوسته تمام شب (۳۵۱ system.heartbeat؛ life_currency روی AMBER با ۱۱ عضو).
- تثبیت حافظه هر ~۱۰ دقیقه، ~۷۵ بار (آرشیو رویدادها).
- لوپ ۷-بخش + مغز دوم هر ~۱.۵ ساعت (۱۰ اجرا؛ هر بار «۳ پیشنهاد / ۲ کسب‌وکار بررسی»).
- pump/health ×۲، gap_report ×۱، web_research ×۱ (کامل).
- **خودترمیمی واقعی ۰۸:۵۲**: عضو lead-naghshi مُرد (phi=17.1) → self-heal خودش دوباره بالا آوردش.
- doctor hallucination-gate فعال (پیشنهاد ویرایش نوت خودشناسی، نسخهٔ ۵۴۷ ساعت ۰۲:۳۴).
- روی ۱۳۸: سکدولر تمام شب تیک زد + ۲ پکت امروزی.

## ۳) ایرادهای باز (اینجا ادامه بده — اولویت‌دار)

1. **`pump/llm_learn` می‌شکند — تکرارشونده**: خطا در ۰۹-۰۷T00:58 (585ms = خطای فوری) و ۰۹-۰۸T01:18 (9.9s = بعد از فراخوانی). علت هنوز نامعلوم؛ trace pump-64845. سنتز مغز یعنی حلقهٔ یادگیری — بالاترین اولویت تعمیر. (نکتهٔ شناخته‌شده: مدل‌های thinking مثل deepseek بدون max_tokens≥200 خروجی خالی می‌دهند.)
2. **`pump/search` بلاک**: «paid-search provider انتخاب نشده» — نیاز به تصمیم (مالک یا ایجنت با رأی).
3. **خوشهٔ paid-call-failed دیشب ۲۲:۲۲–۲۲:۵۹** در provider_router heartbeats — بررسی کن آیا برطرف شده یا مداوم است.
4. **memory-consolidate همیشه «۰ نوت سمانتیک»** — آیا by-design است یا یال تولید نوت شکسته؟ (اگر شکسته باشد حافظهٔ معنایی ارگانیسم خاموش است.)
5. **D0_domain در drive-loop هنوز قفل** فقط به‌خاطر کش DNS محلی (چک fail-closed درست کار می‌کند؛ خودش باز می‌شود).
6. قفل‌های صف هنوز بلااجرا: MSG38 settle در calibration روی ۱۸۲ (verify-dispatch بعدی)، AUTO1 منتظر شمارهٔ مالک، first-order منتظر بازار.

## ۴) ورودی‌های مانده از مالک (دوباره نپرس؛ فقط وقتی رسیدی)

شمارهٔ نمایش تماس‌ها (تلگرام) · ران‌بوک ۳-کلیکی دامنهٔ مینی‌اپ · سرویس search/تماس وقت فعال‌سازی.

## ۵) قواعد که همین امواج ثابت کردند

- پروسهٔ در حال اجرا ممکن است کد تازه را نداشته باشد؛ مسیرهای restart فقط وقتی کار می‌کنند که کدِ در حال اجرا آنها را داشته باشد. برای ری‌استارت: `_ops/agent-restart-organism.ps1` (marker + finally-cleanup + relaunch).
- `git add --sparse` برای دایرکتوری‌های خارج از sparse-checkout.
- رسید جزئی فوراً بنویس — جلسه‌ها وسط کار می‌میرند (کدکس امروز دو بار قطع شد).
- هر عدد بدون منبع = unverified؛ تناقض را با هر دو مقدار ثبت کن.

## مسیرهای شاهد سریع

`01 - Dashboard/UNLOCK-REGISTRY-2026-09-08.md` (تاریخچهٔ کامل) · `07-HANDOFF/OWNER-APPROVALS-2026-09-07.md` (دورهای ۱-۵) · `09-LANES/UNLOCK-REVIEW-20260908/` (رسیدهای دامنه+پیگیری) · `_ops/state/events.jsonl` + `events.archive.jsonl` (کار ارگانیسم) · board138: `~/octopus-mesh/state/owner_dialogue/scheduler_tick.receipt.json` + `standing/counter.json`.
