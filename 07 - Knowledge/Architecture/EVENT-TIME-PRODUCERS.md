---
type: knowledge
status: proposal
tags: [octopus, adr-043, event-time, bitemporal, spine, t38]
created: 2026-08-20
updated: 2026-08-20
created_by: agent B (ZCode) — directive #۶ §۵ (T38)
---

# EVENT-TIME-PRODUCERS — جدول تولیدکننده‌های زمان رویداد (پیشنهاد T38)

> هدف: رفع ADR-043. هر ردیف مشخص می‌کند `occurred_at` هر دامنه باید از کجا
> بیاید تا از `recorded_at` (زمان نوشتن در spine) واقعاً مستقل باشد.
> معیار پذیرش (دستور #۶): stdev توزیع `recorded_at − occurred_at` > 10ms و
> حداقل ۲ منبع مستقل، یکی با تأخیر طبیعی.

| دامنه | producer فعلی | منبع پیشنهادی occurred_at | منبع ساعت | دقت | تأخیر معمول | مستقل؟ |
|---|---|---|---|---|---|---|
| system (beat/state) | `_utc_now_iso()` هنگام نوشتن | زمان تولید نمونه در ماژول مولد (قبل از صف/نوشتن) | ساعت مولد (monotonic→wall) | ~ms | <10ms | پس از تغییر: بله (بدون تأخیر) |
| provider (API) | `_utc_now_iso()` | **response_timestamp سرور** (رسید cost-receipts هم‌اکنون request/response جدا دارد) | ساعت سرور provider | ~ms–s | طبیعی و متغیر (شبکه) | **بله — کاندید ۱ با تأخیر** |
| telegram (ورودی انسانی) | فعلاً در spine با ساعت نوشتن | زمان ارسال پیام از update تلگرام (`message.date`) | ساعت سرور Telegram (ثانیه) | 1s | طبیعی (ثانیه تا ساعت) | **بله — کاندید ۲ با تأخیر** |
| doctor / proposal / neural / lead / ziman | `_utc_now_iso()` | زمان تصمیم/رویداد در ماژول مولد | ساعت مولد | ~ms | <10ms | پس از تغییر: بله (بدون تأخیر) |

## وضعیت امروز (اندازه‌گیری 2026-08-20، n=7,248)

همهٔ دامنه‌ها `NO_INDEPENDENT_EVENT_TIME` (median delta ‏0.01ms؛ stdev حداکثر
7.03ms در system). جزئیات: [[../../06-EVIDENCE/T37-T38-T39-DIRECTIVE-6-2026-08-20]].

## قانون پیاده‌سازی (وقتی مجوز آمد)

1. producer هرگز ساعتِ نوشتن DB را به‌عنوان occurred_at ننویسد؛
   `INELIGIBLE_TEMPORAL_METADATA` بهتر از timestamp قلابی است.
2. هر رویداد `producer` و `producer_sequence` خودش را حفظ کند (ستون‌های موجود spine).
3. پس از استقرار دو producer مستقل: اجرای suite پانزده‌تستی
   (`_ops/tests/test_bitemporal_spine_spec.py`) روی **دادهٔ واقعی**، نه fixture؛
   سپس بررسی گیت `VERIFIED_BITEMPORAL` طبق دستور #۶ §۵.
4. رصد دائمی: گزارش stdev ماهانه در evidence؛ افت زیر 10ms = هشدار تناقض.
