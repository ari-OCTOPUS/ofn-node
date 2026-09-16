# 4D DAEMON — DIAGNOSE + RESTART PROPOSAL (DIAGNOSE/PROPOSE فقط — بدون اجرا)

run: CL01-191-20260818-2233 · طبق فرمان مالک: «پس از گزارش restart proposal، منتظر دستور صریح مالک بمان.»

## ۱. تشخیص (با شاهد)

```yaml
آخرین اجرای معتبر:    2026-08-16 15:39:45 +10:00 — توقفِ خودخواسته
علت توقف (لاگ):       daemon-launch3.err.log →
                       «task.failed ⚠️ نقضِ مرزِ اعتماد (TCB) — توقفِ حفاظتی»
                       سپس: «daemon: protective HALT (invariant violation) → stopping»
                       «daemon stop · ticks=448 · proposals=0 · errors=0 · git_watcher=0»
قدرت اجرا:           ticks=448 بدون خطا؛ حلقهٔ یادگیری اثبات‌شده در لاگ:
                       memory.read (200 ردیف) · read-back فرضیهٔ #1186 (r16-view:dedup)
                       · خودتنظیمی rho_bias 0.50→0.60 · ردِ خودتغییریِ کم‌تازگی
مورد معلق:            یک decision packet [approve] در صفِ not-configured ماند —
                       یعنی دیمون پیش از HALT یک تأییدِ مالک می‌خواست که هرگز ارسال/پاسخ نشد
وضعیت امروز:          پروسه NOT_FOUND (F1 §1)؛ پاکت service-inventory 02:40 امروز
                       PID=24588 را ادعا کرد که با mtime لاگ‌ها (Aug 16) سازگار نیست → UNVERIFIED
فایل‌های مرتبط:       _ops/state/_unwired_4d_20260816.py = اسکریپت تحلیل فقط-خواندنی
                       (شمارندهٔ caller)؛ خروجی/خطایش صفر‌بایت — خودِ دیمون نیست
```

نتیجه: دیمون **خراب نشده** — طبق طراحی محافظ خودش، آن را خاموش کرده و منتظر تصمیم مالک مانده (پاکت approve کپی‌نشده). قبل از restart باید همان «نقض مرز اعتماد TCB» تعیین تکلیف شود؛ وگرنه با احتمال بالا دوباره HALT می‌کند.

## ۲. پیشنهاد restart (bounded — طبق قیدهای مالک)

```yaml
command:        python -X utf8 4d_system/brain/daemon.py
service_name:   بدون سرویس OS — فقط پروسهٔ دستی (تغییر scheduler/service ممنوع)
working_dir:    F:\backup\4d_system      (اسکریپت با مسیرهای نسبی outputs/ کار می‌کند)
env_source:     بدون تغییر — OCTOPUS_WIRE_MEMORY_GATE همچنان خاموش (پیش‌فرض)؛
                هیچ env راز-محور تازه لازم نیست
log_path:       4d_system/outputs/daemon-launch4.err.log (الگوی existing؛ stdout جدا: launch4.log)
expected:       PID: نامعلوم تا اجرا (ثبت می‌شود) · port: بدون پورت (loop داخلی، بدون listen)
                طبیعت کار: tick هر ~۳۰s (مشاهده‌شده در لاگ) · فایل توقف: outputs/daemon.stop
attempts:       ۱ تلاپ · timeout: حداکثر ۱۰ دقیقه مشاهده فعال (بدون تداخل با scheduler)
pre-check:      tail daemon-launch3.err.log برای اطمینان از همان HALT شناخته‌شده
rollback/kill:  touch F:\backup\4d_system\outputs\daemon.stop   (مسیر توقف رسمی خود دیمون)
                اگر پاسخ نداد: taskkill /PID <pid> /F (فقط همان PID)
post-check:     لاگِ جدید باید ticks را بشمارد و «protective HALT» تازه نداشته باشد؛
                اگر دوباره HALT شد → همان invariant را ثبت و متوقف شو (بدون تلاش دوم)
```

## ۳. پیش‌نیاز تصمیم مالک (قبل از هر restart)

1. پاکت approve معلقِ 15:39:45 را ببین/رد کن — دیمون برای همین ایستاده بود.
2. بگو آیا علت TCB-violation را می‌شناسی (تغییر فایل TCB در آن بازه؟) — بازهٔ Aug 16 بعدازظهر با کامیت‌های آن روز قابل تطبیق است اگر بخواهی بررسی کنم (خواندن git log آن بازه = فقط‌خواندن، آماده).
3. دستور صریح: «restart 4d daemon approved» → فقط آن‌گاه اجرا با بند §۲.

## وضعیت: PROPOSAL_COMPLETE — منتظر دستور مالک. هیچ پروسه‌ای start/stop نشد.
