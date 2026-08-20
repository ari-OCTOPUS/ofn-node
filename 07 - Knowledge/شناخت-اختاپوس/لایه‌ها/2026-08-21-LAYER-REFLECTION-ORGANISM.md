---
type: layer-reflection
layer_id: ORGANISM
status: evidence-backed
date: 2026-08-21
session_id: SESSION-20260820-21
---

# Reflection: Organism / بدنهٔ runtime

## نقش واقعی من
مجموعهٔ processها و stateهای زنده: مرکز تلگرام، watchdogها، daemonها؛ صاحب offset، port و heartbeat.

## امروز چه اتفاقی برای من افتاد؟
مرکز تلگرام دو بار restart کنترل‌شده شد (23568→29492)؛ poll سالم با fails=0؛ port 8776 به مرکز جدید منتقل شد؛ offset 223883347 بدون پسرفت.

## چه آموختم؟
- restart کنترل‌شده فقط با snapshot قبلی و hash manifest معتبر است (RUNNING-CODE-MANIFEST).
- poll سالم به‌تنهایی closure نیست؛ offset بدون پسرفت + ۳ سیکل سالم لازم بود.
- دو لانچر هم‌زمان 409-fight می‌کنند؛ قبل از restart تک‌نمونه‌ای بودن اثبات شد.
- kill-switch فایل‌محور (state/kill-switch.json) برای pause/resume لازم است.

## کجا اشتباه کردم؟
کد پس از start مرکز ویرایش شده بود و drift ایجاد کرد؛ با commit + restart بسته شد.

## چه چیزی الآن واقعاً کار می‌کند؟

| قابلیت | Declared | Wired | Observed | Tested | Verified |
|---|---:|---:|---:|---:|---:|
| poll/offset | 1 | 1 | 1 | 1 | 1 |
| restart کنترل‌شده | 1 | 1 | 1 | 1 | 1 |
| watchdog orphan | 1 | 1 | 0 | 1 | 0 |

## چه چیزی هنوز کار نمی‌کند؟
LIVE orphan supervision هنوز wiring تولیدی ندارد؛ PROBE-INVALID root cause نهایی باز است.

## نیازهای عملیاتی من
- wiring مشاهده‌ای orphan watchdog
- root cause نهایی probe spam

## قدم بعدی کوچک و تست‌پذیر
وصل‌کردن orphan watchdog به‌صورت observe-only و بستن LIVE-ORPHAN بدون restart کودک سالم.

## Evidence
- `RUNNING-CODE-MANIFEST-2026-08-21.json`
- `POST-COMMIT-CENTER-RESTART-PLAN.json`
- `center-config.json last_offset`
