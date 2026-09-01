# DecisionRecord — D-26 بدن‌های کانونی و تعریف «واقعی»

**تاریخ: ۲۰۲۶-۰۹-۰۱ · حکم صریح مالک در جلسهٔ ابری Cursor · ثبت، نه اجرا**

## منبع

مالک نوشت: «همرو ازم همینجا بگیرو از طرف مالک و شرکا ثبت کن»
سپس: «همشون امضا کردن»

منظور «همرو»: بستهٔ پیشنهادی ایجنت ارشد در همان جلسه (سه رأی + سه موج +
فهرست ممنوع + گیت‌های بسته + کسب‌وکار موازی).

```yaml
speaker: owner
binds_partnership: true
owner_attests_all_signed: true
partner_countersign_status: owner_attested
partners: [maliheh, abbas, saba]
partner_voices_independently_observed: false
implementation_authorized: false
merge_authorized: false
deploy_authorized: false
wire_authorized: false
```

## حکم

1. بدن کسب‌وکار = `ofn-node`. بدن معماری عصبی = والت. مش بعد از قرارداد لبه.
2. والت به مخزن عمومی `ofn-node` merge/push نمی‌شود.
3. مفهوم وقتی واقعی است که هر سه باشد: کد روی بدن کانونی، تست منفی، رسید مستقل.
4. موج‌ها خودکار جلو نمی‌روند. موج ۱ روی والت است و **هنوز شروع نشده**.
5. روی `ofn-node` خانوادهٔ envelope دوم ساخته نمی‌شود.
6. MCP، کلون حافظهٔ ایجنت، توکن قابلیت به‌ازای تسک به‌عنوان ماژول جدید، VBAA-now ممنوع.
7. D1 / D7 / OWNER_KEY / `secret_rotation` / `WIRE_*` بسته می‌مانند.
8. O-3 و S-04 `later` اند.
9. شناسه‌های بی‌نام STAGE-00 حدس نمی‌شوند.
10. مسیر کسب‌وکار موازی از معماری جدا می‌ماند و این پرونده sent/revenue/booking نمی‌سازد.

## آنچه این پرونده نیست

اجازهٔ پیاده‌سازی Envelope/Run Store، باز کردن گیت، یا ارسال به مشتری.
امضای سه شریک در این پرونده **ادعای مالک** است، نه مشاهدهٔ مستقل این ایجنت.
