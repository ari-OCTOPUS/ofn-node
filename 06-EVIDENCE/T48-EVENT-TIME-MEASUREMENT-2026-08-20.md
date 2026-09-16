---
type: evidence
task: T48-measurement
tags: [t48, event-time, live-b, measurement, directive-8]
created: 2026-08-20T16:25+10:00
created_by: scheduled task (automation prompt) — executed by agent B
method: live_readonly_probe · spine mode=ro · window ≈ 13:44–16:25 +10 (~65+ min after producers deployed 13:44)
paid_calls: 0 · restarts: 0 · files_touched: only this evidence file
---

# سنجش T48 — توزیع event-time واقعی پس از ~۶۵+ دقیقه (2026-08-20)

## عدد خام (خروجی措 دست‌نخوردهٔ پرس‌وجوی ro)

```json
{
 "n_total": 11,
 "skew_flagged": 0,
 "producers": {
  "provider/router_request_ts": {
   "n": 11,
   "median_ms": 8126.35,
   "stdev_ms": 5426.804,
   "min_ms": 5924.28,
   "max_ms": 21358.56
  }
 }
}
```

ستون‌ها و `legacy_no_event_time` موجودند (migration اعمال شده) — شرط ۳ِ تسک رخ نداد.

## ارزیابی گیت LIVE-B (معیار دستور #۸ §۳)

| گیت | وضعیت | شرح |
|---|---|---|
| independent_sources >= 2 | **✗ (۱ از ۲)** | فقط `provider/router_request_ts` |
| stdev > 10ms در هر دو | ✓ برای provider (5426.8ms ≫ 10ms) | منبع دوم هنوز صفر رویداد |
| late-arriving واقعی >= 1 | **✗ (۰)** | هنوز هیچ |
| suite روی داده واقعی | ✓ PASS (گزارش #۱۰، ‏n=7,296) | جداگانه ثبت شده |
| read paths از decision_time | PROVEN فقط برای مسیر سیم‌شده | بقیهٔ مسیرها باز |

**حکم: ‏LIVE-B = BLOCKED** (دقیقاً همان وضعیتی که مالک در #۱۰/#۱۲ تأیید کرد).

## یادداشت صادقانه — چرا فقط یک producer رویداد دارد

1. **`telegram/telegram_message_date`: ‏n=0** — پیام‌های تلگرامی مالک هنوز
   نرسیده (پیش‌نیاز اعلام‌شدهٔ مالک در دستور #۱۲ §۲؛ بدون poll مصنوعی/backfill).
2. **`provider/provider_server_created`: ‏n=0** — این منبع فقط از کد T52
   (لوله‌کشی `created` سرور) می‌آید که امروز مستقر شد ولی:
   - `brain.daemon` (فراخوان‌کنندهٔ اصلی مسیر پولی) از 19/08 با کد قدیم می‌دود
     و ریاستارت نشد (سرپرست آن `launch5.cmd` بدون حلقهٔ بازیافت — رأی مالک
     #۱۲ §۱: فعلاً نه).
   - organism (کد جدید) رویدادهای موجود ۱۱گانه را از مسیر `router_request_ts`
     تولید کرده — یعنی کد T48 فعال است، فقط منبعِ ساعتِ مستقل هنوز دیده نشده.
   - پروب تک‌فراخوانیِ امضاشده که همین رویداد را می‌سازد، پشت گیت FX منتظر
     انتشار نرخ ۲۰ اوت RBA است (نگهبان v2 فعال؛ آخرین وضعیت BLOCKED_FX_STALE).
3. **تقویم provider موجود (n=11)** هم‌خانوادهٔ خودِ router است
   (DELAY_BEARING_SAME_CLOCK) — برای شرط independence حساب نمی‌شود.

## نتیجهٔ عملیاتی

مسیر بسته شدن LIVE-B دست‌نخورده باقی می‌ماند: (۱) پیام‌های تلگرامی مالک →
producer_2 + نمونهٔ late-arriving؛ (۲) اولین رویداد `provider_server_created`
(از پروب امضاشده پس از انتشار RBA). هر دو ورودی در جریان‌اند؛ این گزارش فقط
وضعیت لحظهٔ سنجش را ثبت می‌کند و حکم نهایی را با دادهٔ کامل‌تر صادر نخواهد کرد
(صدور خودکار LIVE-B مجاز است — دستور #۱۲ §۱۱ — وقتی ورودی‌ها برسند).
