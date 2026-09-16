---
type: proposal
id: MANIFEST-SCOPE-MIGRATION
created: 2026-08-16 ~06:3x — T2 (پیشنهاد؛ manifest امضاشده دست‌نخورده)
rule: "امضای مالک تنها با رأی مالک بازتولید می‌شود — این سند فقط diff-as-proposal"
---

# مهاجرت دامنهٔ هش: از مغزِ observe-only به اندام‌های اجراکننده (T2)

## وضعیت فعلی [A]
`4d_system/config/trust-boundary.json` (**امضاشده + enforce زنده**) — ۱۴ فایل
TCB، همه در `4d_system/` (brain/llm/config/run) — یعنی لایهٔ **observe-only**
(مغز 4d که اثر بیرونی مستقیم ندارد؛ دیمونش propose-only است).

## پیشنهاد (نسخهٔ ۱ manifest — فقط با رأی و امضای مجدد مالک)

افزودنِ بخش دوم `live_limbs` به همان manifest (بدون حذف بخش اول — مغز هستهٔ
هویتی می‌ماند):

```yaml
live_limbs:                     # پنج اندامِ اثرگذار _ops
  - role: organism
    entry: _ops/organism.py          # sha256 از پروبِ زنده
  - role: center
    entry: _ops/telegram_center/center.py
  - role: gateway
    entry: _ops/telegram_center/gateway.py   # مسیر دقیق از پروب
  - role: live
    entry: _ops/live/server.py
  - role: cortex
    entry: _ops/cortex/cortex.py
```

## diff-as-proposal

| بعد | امروز (امضاشده) | پیشنهادی (v1) |
|---|---|---|
| فایل‌های هش‌شده | ۱۴ × 4d_system (observe-only) | همان ۱۴ + ۵ ورودیِ _ops (اثرگذار) |
| منبع حقیقت هش | build-time (تولید manifest) | + پروبِ runtime (`organism_manifest.py`) برای تازگی |
| violation-semantic | تامpering مغز ⇒ halt | + drift اندام (pid/port/entry-hash) ⇒ گزارش AEB؛ halt فقط پس از رأی جدا |
| امضا | مالک ✓ | **امضای مجدد مالک لازم** |

## چرا halt فوری برای اندام‌ها نه [B]
پنج پروسهٔ _ops هر ری‌استارت PID/ورت می‌گیرند؛ هشِ ورودی پایدار است ولی
فرکانس تغییرِ کدِ پا بالاتر از مغز است — قفلِ سختِ بدون مسیر امضای روان =
فرسایشِ مراسم (درس C-013 خودِ شورا: گارد بیش‌ازحد بسته ⇐ exemptions ⇐ مراسم).
مسیر پیشنهادی: گزارش drift در AEB (پیاده شد [A]) ⇐ ۳۰ روز مشاهده ⇐ رأی.

## آنچه این پیشنهاد عمداً نمی‌کند
تغییر manifest موجود · enforce جدید · لمس TCB — همه منتظر رأی مالک.
