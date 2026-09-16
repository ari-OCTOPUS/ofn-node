---
type: layer-reflection
layer_id: DOCTOR
status: evidence-backed
date: 2026-08-21
session_id: SESSION-20260820-21
---

# Reflection: Doctor and diagnosis

## نقش واقعی من
اسکن‌ها و missionها؛ doctor-link کارت‌های صف‌شده را با client مرکز می‌فرستد.

## امروز چه اتفاقی برای من افتاد؟
doctor-link cursor فعال؛ قانون single-open mission بدون timeout هنوز باز است.

## چه آموختم؟
- mission بدون timeout → deadlock بالقوه؛ quarantine/replacement لازم است.
- doctor-pulse intent باید با مرکز هم‌منطقه باشد.

## کجا اشتباه کردم؟
doctor mission deadlock در فهرست باز؛ در این نشست patch نشد.

## چه چیزی الآن واقعاً کار می‌کند؟

| قابلیت | Declared | Wired | Observed | Tested | Verified |
|---|---:|---:|---:|---:|---:|
| doctor-link | 1 | 1 | 1 | 1 | 1 |
| mission timeout | 1 | 1 | 0 | 0 | 0 |

## چه چیزی هنوز کار نمی‌کند؟
mission timeout/quarantine/replacement.

## نیازهای عملیاتی من
- mission timeout + quarantine + replacement

## قدم بعدی کوچک و تست‌پذیر
واحد timeout mission.

## Evidence
- `doctor-link-cursor.json`
- `LOOP-REGISTRY incidents`
