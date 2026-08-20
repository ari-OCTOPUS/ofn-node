---
type: layer-reflection
layer_id: TESTS
status: evidence-backed
date: 2026-08-21
session_id: SESSION-20260820-21
---

# Reflection: Tests and verification

## نقش واقعی من
run_all با fast/slow lanes و timeouts؛ registry ثبت تست؛ verifier مستقل.

## امروز چه اتفاقی برای من افتاد؟
۵۶ تست سبز در ۵ suite (canary 12، conflict 6، durable 15، reconciliation 8، closed-loop 15)؛ verifier پنجرهٔ C سبز؛ triage ۵۱ فایل baseline.

## چه آموختم؟
- ثبت تست با اجرای تست فرق دارد؛ counts جدا نگه داشته شد.
- تست‌های کهنه علیه قرارداد جدید، regression نیستند؛ طبقه‌بندی triage لازم است.
- نمونهٔ صفر PASS نیست؛ non-empty sample لازم است.
- verifier باید authoritative verdict را preserve کند (merge_preserved).

## کجا اشتباه کردم؟
memory gate suite کهنه (F3)؛ دو تست timeout.

## چه چیزی الآن واقعاً کار می‌کند؟

| قابلیت | Declared | Wired | Observed | Tested | Verified |
|---|---:|---:|---:|---:|---:|
| guard suites | 1 | 1 | 1 | 1 | 1 |
| scoped verifier | 1 | 1 | 1 | 1 | 1 |
| timeout isolation | 1 | 1 | 1 | 1 | 1 |

## چه چیزی هنوز کار نمی‌کند؟
memory gate suite؛ timeout دو تست.

## نیازهای عملیاتی من
- تعمیر memory gate
- ایزوله‌سازی timeout

## قدم بعدی کوچک و تست‌پذیر
تعمیر memory gate با failing-test-first.

## Evidence
- `run_all.py registry`
- `execution-manifest.jsonl`
- `SESSION-HARVEST tests`
