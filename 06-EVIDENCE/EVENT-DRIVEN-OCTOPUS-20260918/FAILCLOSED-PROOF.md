# FAIL-CLOSED PROOF — EVENT-DRIVEN-OCTOPUS-20260918

**ادعا:** اگر ضربان (beat) بایستد، هیچ runnerی در مسیر پول اجرا نمی‌شود؛ و به‌محض بازگشت ضربان، همان رویدادِ نگه‌داشته‌شده پردازش می‌شود.

**روش (واقعی، نه شبیه‌سازی):** سرویس موجود `ofn-heartbeat` روی board138 متوقف شد و تایمر watchdog که آن را برمی‌گرداند موقتاً خاموش شد؛ سپس یک رویداد واقعی (`order_seen`) به اسپاین داده شد.

## ۱) توقف ضربان و کهنه‌شدن

```
$ systemctl stop ofn-sync-watchdog.timer   # temp
$ systemctl stop ofn-heartbeat
# 165s بعد:
beat_age_s at probe: 171.9   fresh: False
probe 2026-09-18T09:16:17Z-8cf32ec5
```

## ۲) گیت‌ها refuse کردند (۵ رسید، هیچ runnerی اجرا نشد)

`state/events/gate-receipts.jsonl`:
```json
{"at":"2026-09-18T09:16:18Z","gate":"orders","kind":"EVENTS_GATED_STALE_BEAT","beat_age_s":191,"trigger":"events:orders","max_age_s":150,"note":"fail-closed: beat stale, runner not started"}
{"at":"2026-09-18T09:16:29Z","gate":"orders","kind":"EVENTS_GATED_STALE_BEAT","beat_age_s":202, ...}
```
(تکرار رسیدها = هر بار که `.path` دوباره trigger شد، گیت باز هم refuse کرد.)

**شاهد دوم:** فایل رویداد در `state/events/inbox/order_seen/` باقی ماند (مصرف نشد) — یعنی نه فقط «اجرا نشد»، بلکه کار هم از دست نرفت:
```
-rw-r--r-- 1 ari ari 294 Sep 18 09:16 2026-09-18T091617Z-8cf32ec5.json
```

## ۳) بازگشت ضربان و پردازش رویدادِ نگه‌داشته‌شده

```
$ systemctl start ofn-heartbeat && systemctl start ofn-sync-watchdog.timer
recovered: beat_age_s 19.1 fresh: True
$ touch inbox/order_seen/2026-09-18T091617Z-8cf32ec5.json   # همان عملیاتی که sweeper ضربان انجام می‌دهد
{"at":"2026-09-18T09:16:54Z","gate":"orders","kind":"EVENTS_RAN","beat_age_s":24,"trigger":"events:orders","files":1,"items":"2026-09-18T091617Z-8cf32ec5.json","duration_s":0,"rc":0}
```
`inbox/order_seen/` خالی و فایل در `processed/orders/` — چرخهٔ کامل: refuse → preserve → recover → run.

## یادداشت

- در تلاش اول (09:09Z) تایمر watchdog در میانهٔ پنجره ضربان را برگرداند و شرط کهنگی هرگز برقرار نشد → تست با خاموش‌کردن موقت watchdog تکرار شد. این خودش نشان می‌دهد heal موجود (watchdog) با fail-closed تعارض ندارد: watchdog ضربان را زنده می‌کند، گیت تا زنده‌شدنش اجرا نمی‌کند.
- تایمرهای غیرپولی (pulse، watchdog، soak، doctor، …) در این مهاجرت دست‌نخورده‌اند و این تست فقط watchdog را ~۳ دقیقه خاموش کرد (با بازگردانی + رسید در همین سند).
