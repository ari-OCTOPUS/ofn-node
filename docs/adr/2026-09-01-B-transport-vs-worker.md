# ADR-2026-09-01-B — چرا ارسال ۲۰۲۶-۰۹-۰۱ مستقیم از transport رفت، نه worker

وضعیت: ثبتِ پسینی + تصمیمِ آینده

## زمینه
ارسالِ ۵ ایمیل اول از `lead_outbound_transport.send` مستقیم زده شد، نه از
`outbound_worker.send_one`. تفاوت: worker سه لایهٔ اضافه دارد — wire flag،
گیتِ per-effect (`lead_effect_gate.release_and_settle`)، و consent سوم.

## چرا (صادقانه)
`lead_effect_gate` و `consent_store` آن روز هنوز روی بورد deploy نشده بودند
(وابستگی‌های خزانه‌ای) و پاسخِ خریداران منتظر نمی‌ماند. لایه‌های حیاتی
(halt/suppression/WAL/سقف در transport + چکِ سقفِ دستی) فعال بودند.

## تصمیم برای آینده
- ارسال‌های جدیدِ سیستماتیک (فالوآپ، کوت) همچنان از transport می‌روند ولی
  **پیش‌شرطِ** wire flag + چکِ سقف + چکِ suppression را در caller دارند
  (همان‌طور که followup_worker/quote_engine پیاده شدند).
- انتقال به worker.send_one وقتی که lead_effect_gate روی بورد deploy و
  تست شود — تا آن زمان transport+callee-gates لایهٔ استاندارد است.
- این ADR در #64 و در audit trail ارجاع شود تا «مسیر دورزدنِ گیت» تلقی نشود.
