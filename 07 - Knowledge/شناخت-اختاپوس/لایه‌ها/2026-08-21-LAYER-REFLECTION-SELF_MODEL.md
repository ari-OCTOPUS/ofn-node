---
type: layer-reflection
layer_id: SELF_MODEL
status: evidence-backed
date: 2026-08-21
session_id: SESSION-20260820-21
---

# Reflection: Self-model and calibration

## نقش واقعی من
self_knowledge با confidence، calibration probe، self_insight card، cockpit tiers.

## امروز چه اتفاقی برای من افتاد؟
self_insight.card از اسکن ۱۳۰ ثانیه‌ای به journal-based تبدیل شد (root cause timeout suite).

## چه آموختم؟
- render نباید اسکن سراسری اجرا کند؛ card باید از journal بخواند.
- confidence ثابت 0.4 باید با EMA مبتنی بر receipt جایگزین شود.
- probe همیشه-True ممنوع؛ self-audit باید probe معتبر داشته باشد.

## کجا اشتباه کردم؟
confidence ثابت و cockpit tiers بدون مصرف واقعی باز مانده.

## چه چیزی الآن واقعاً کار می‌کند؟

| قابلیت | Declared | Wired | Observed | Tested | Verified |
|---|---:|---:|---:|---:|---:|
| self_insight card | 1 | 1 | 1 | 1 | 1 |
| self_knowledge EMA | 1 | 1 | 0 | 0 | 0 |
| cockpit tiers | 1 | 1 | 0 | 0 | 0 |

## چه چیزی هنوز کار نمی‌کند؟
EMA و tiers و shadow cycle اجرا نشده.

## نیازهای عملیاتی من
- EMA receipt-backed
- cockpit tiers مصرف‌کننده
- self_insight shadow cycle

## قدم بعدی کوچک و تست‌پذیر
self_knowledge EMA با failing test اول.

## Evidence
- `84a8a96 (journal card)`
- `TRIAGE-51-FAILURES`
