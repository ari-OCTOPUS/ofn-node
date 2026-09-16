---
type: layer-reflection
layer_id: CORTEX
status: evidence-backed
date: 2026-08-21
session_id: SESSION-20260820-21
---

# Reflection: Cortex / مغز عملیاتی

## نقش واقعی من
مسیر پولی/محلی fallback؛ degrade به DEGRADED_LOCAL_ONLY ثبت می‌شود.

## امروز چه اتفاقی برای من افتاد؟
fallback محلی در governor alerts دیده شد؛ label DEGRADED_LOCAL_ONLY در telegram_adapter ثبت شد.

## چه آموختم؟
- degradation باید صریح label شود (DEGRADED_LOCAL_ONLY)، نه بی‌صدا.
- fallback بدون اعلام، SILENT_DEGRADATION است.

## کجا اشتباه کردم؟
cortex پولی در flags ثابت؛ fallback محلی «آشغال» نامیده شده (alert کهنه).

## چه چیزی الآن واقعاً کار می‌کند؟

| قابلیت | Declared | Wired | Observed | Tested | Verified |
|---|---:|---:|---:|---:|---:|
| fallback local | 1 | 1 | 1 | 1 | 1 |
| degradation label | 1 | 1 | 1 | 1 | 1 |

## چه چیزی هنوز کار نمی‌کند؟
زنجیرهٔ calibration→improve هنوز verify نشده.

## نیازهای عملیاتی من
- verify زنجیرهٔ علی calibration→improve

## قدم بعدی کوچک و تست‌پذیر
lane شناختی: failing test برای calibration→improve.

## Evidence
- `telegram_adapter.py DEGRADED_LOCAL_ONLY`
- `governor-alerts.md`
