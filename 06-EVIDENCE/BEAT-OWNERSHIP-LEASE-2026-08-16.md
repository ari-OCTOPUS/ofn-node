---
type: report
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
updated: 2026-08-16
created: 2026-08-16
created_by: agent
tags: [octopus, beat-lease, migration, evidence]
sources:
  - "[[../07 - Knowledge/شناخت-اختاپوس/57-LAPTOP-TO-ARM1-MIGRATION-2026-08-16]]"
  - "[[OCTOPUS-V3-P0-2026-08-16]]"
---

# Beat Ownership Lease — fencing token (unarmed)

TTL به‌تنهایی کافی نیست: پروسهٔ pause شده بعد از انقضا بیدار می‌شود و می‌نویسد. این نشست fencing را SoT کرد. به chrono/organism وصل نشد. freeze زنده نوشته نشد.

## روی دیسک

| قطعه | نقش |
|---|---|
| `_ops/runtime/beat_lease.py` | `BeatLease` · `FileLeaseStore` · `NatsKvLeaseStore` · token=`assert_valid()` |
| `_ops/runtime/beat_lease_cli.py` | `status` / `freeze` / `unfreeze` |
| `_ops/tests/test_beat_lease.py` | ۱۷ تست pytest · ثبت‌نشده در `run_all.py` |
| `_ops/octopus_v3/beat_lease.py` | پروتوتایپ HMAC — fencing نیست؛ سیم نشود |

مسیر زندهٔ پیش‌فرض: `_ops/state/octopus.lease`. تست‌ها فقط tempfile. CLI `status` امشب: VACANT، freeze=no، فایل lease ساخته نشد.

## قرارداد fencing

- `revision` یکنواخت صعودی. `release()` vacate می‌کند، فایل را پاک نمی‌کند (رگرسیون قفل شد).
- اعتبار محلی: monotonic، تا `ttl - margin`. acquire بعدی: بعد از `ttl + margin`. مردهٔ عمدی `۲ × margin`.
- `BEAT-FREEZE.flag` مالک فعلی را هم وسط کار می‌کشد.
- File backend روی UNC/SMB/NFS `RuntimeError` می‌دهد.
- سوراخ باقی: فایل کاملاً خراب ⇒ acquire تازه از revision=1. M2 با NATS KV این را ندارد.

## تست

```text
python -m pytest _ops/tests/test_beat_lease.py -q
17 passed in 16.03s
```

۱۶ تست ورودی Downloads + یک تست منع UNC. HMAC قدیمی: ۱۰/۱۰ جدا.

پوشش: دو holder · steal بعد از انقضا · token اکیداً صعودی · vacate نه delete · freeze · ۸-رشته یک برنده · renewer · ناحیهٔ ایمنی · رویدادهای لجر.

## آنچه عمداً انجام نشد

- `assert_valid()` داخل `chrono.Pacemaker._tick_decision`
- `on_event` به لجر زنده / Arm 2
- حمل token روی نوشتن budget/state
- `freeze` روی درخت زنده
- اسکریپت M0
