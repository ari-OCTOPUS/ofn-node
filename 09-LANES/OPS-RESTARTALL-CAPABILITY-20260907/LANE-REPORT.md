# LANE-REPORT — OPS-RESTARTALL-CAPABILITY-20260907

ORDER=owner chat 2026-09-07 («یک راه راحت‌تر ریستارت کلی هم بساز بعد دیباگ عمیقت رو اجرا بده و پرامپتی برا تست قابلیت‌های مختلفش بزن») · GOV_VERSION=V8 · LADDER=L2
LANE_ID=OPS-RESTARTALL-CAPABILITY-20260907

## ۱) راه راحت ری‌استارت کلی — از قبل بود، امروز اثبات شد

`F:\backup\_ops\RESTART-ALL.bat` (دابل‌کلیک) + `RESTART-ALL.ps1` با `-WhatIf/-Skip` از 2026-08-03 موجود بود؛ no-rebuild رعایت شد. **E2E امروز**: پری‌فلایت سبز (بدون مارکر، ۱۵۲۸ خط CRLF فلگ) → اجرای واقعی → گیت پذیرش ۳ عضو را OK داد (center 764→5428، gateway 10468→4524، live 15068→28592) و **دو جعبهٔ سیاه را لو داد**: (الف) organism مارکر RESTART-REQUESTED را ۳۰۰s نادیده گرفت (کدِ چک موجود در organism.py:563؛ beat می‌تپت؛ علت ناشناخته — پسامورت باز) → قهری کشته شد (15:31:55) و با واچ‌داگ ۱۳ ثانیه بعد احیا شد (**PID 25128، state.started=15:32:09، beat 64303→64305↗**)؛ (ب) cortex same-pid/exit-2 از مسابقهٔ runner با واچ‌داگ — بی‌آسیب چون PID 19728 از 15:07 کد U1 را داشت.

## ۲) دیباگ عمیق (پروب‌های فقط‌خوان، سرویس‌های تازه)

- **HTTP**: 8771 organism / 8772 cortex / 8773 live — هر سه 200 با داشبورد HTML؛ /health روی هر سه 404 (مسیر health وجود ندارد). dashboard 8801: پایین.
- **لجرها همه تازه**: events.jsonl 15:33، reach/ledger 15:35 (۲۸MB)، spine.db 15:32، HEARTBEAT 15:32، calibration-latest 15:27 (با truth_semantics v2).
- **سطح فلگ: ۳۴۸+ فعال** — نقشهٔ واقعی قابلیت‌ها (TG voice/ask/miniapp، lead-pipeline کامل، CORTEX_SELF_MONITOR+TRUTH_BY_CYCLE روشن، STRESS_CALIBRATED روشن، ONE_HEARTBEAT و…) + فلگ‌های پای‌های مرده (MINING_OS/WLOS/FITNESS) = بدهی پیکربندی.
- **بردها**: 180 llama health=ok با qwen3-0.6b؛ 138 ofn active + audit در 215,991 خط.

## ۳) نقشهٔ جعبهٔ سیاه + پرامپت‌های تست

[CAPABILITY-MAP-AND-TEST-PROMPTS.md](CAPABILITY-MAP-AND-TEST-PROMPTS.md) — ۸ تست تلگرامی (T1..T8: از `/now` تا گارد پاسخ مالک) + ۹ جعبهٔ خواندنی (B1..B9) + ۵ کشف امروز.

## MUTATIONS_PERFORMED

RESTART-ALL اجرای واقعی (SERVICE-AFFECTING با GO مالک قبلی+فعلی) · kill قهری organism 19164 (شواهد: نادیده‌گرفتن ۳۰۰s مارکر) · احیا توسط organism-watchdog · پروب‌ها فقط‌خوان · دو فایل lane.
COUNTERS: EXTERNAL_ACTIONS=0 (هیچ پیام/پرداخت) · NEW_LAN_LISTENERS=0
ROLLBACK=نیاز ندارد (سرویس‌ها زنده‌اند)؛ پسامورت organism-marker = باز
NEXT=پچ escalation قهری در RESTART-PROCESS + پسامورت چکِ مارکر + census فلگ‌های مرده + تست‌های T1..T8 توسط مالک
