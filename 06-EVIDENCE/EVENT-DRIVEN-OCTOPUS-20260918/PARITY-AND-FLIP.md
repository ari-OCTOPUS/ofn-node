# PARITY & FLIP — EVENT-DRIVEN-OCTOPUS-20260918

## چرا پاریتی «ساختاری» است، نه فقط تجربی

هر emit داخل **همان تابعی** نشسته که تیک تایمر اجرا می‌کند؛ یعنی هر اثری که مسیر تایمری می‌گذارد، رویدادش را هم می‌سازد (نه یک مسیر موازی). شاهد:
- `send_queue.py` → emit بلافاصله بعد از `SENTLOG.write` (همان رکوردی که تیک ۶ساعته می‌نوشت)
- `reply_alert.py` → emit بلافاصله بعد از `log_inbox(row)` (همان رکوردی که تیک ۲دقیقه‌ای می‌نوشت)
- `imap_listener._receipt` → هر طبقه‌بندی که تیک ۱۵دقیقه‌ای می‌نوشت، حالا رویداد هم می‌شود
- `lead_enrich` / `money_executor` / `discovery_runner` / `revenue_drive` / `go_b3_owner_bind.emit_decision` / `store_watch` → همان‌جا

پس «رویداد جاافتاده» ممکن نیست مگر اینکه اجرای خودِ runner شکست بخورد — که رسید خودش را دارد.

## شاهد شادو (پیش از فلیپ)

`state/events/gate-receipts.jsonl` — نمونهٔ واقعی:
```
08:55:08 leads  SHADOW_WOULD_RUN files=1 items=2026-09-18T084836Z-fd70d9d3.json (trigger=nats:lead_found)
08:55:37 mail   SHADOW_WOULD_RUN files=1 items=2026-09-18T085537Z-13c085b9.json (trigger=nats:mail_seen)
```
(فایل‌ها مصرف و در `state/events/shadow-consumed/` نگه داشته شدند — «می‌دید ولی اجرا نمی‌کرد».)

## فلیپ‌ها (per-kind، در `state/events/mode.json`)

| زمان (UTC) | kind | شاهد پس از فلیپ |
|---|---|---|
| 09:02 | mail, owner, inbound, cards, orders | `09:02:51 mail EVENTS_RAN files=1 duration_s=32 rc=0` + خروجی زندهٔ reply_alert `{"checked":0,"alerts":[]}` |
| 09:06 | leads, idle | زنجیرهٔ lead_found→leads→send (رسیدهای EVENTS_RAN شادو/لایو + `SEND_*` receipts) |
| 09:06→09:08 (موقتاً shadow) | send | پس از رفع F-1 (کرش بولی) و افزودن گارد گیرنده؛ 09:08 برگشت live |
| — | mesh | `octopus-evt-mesh.path` (تریگر فایل‌محور events mesh) |

## چرا فلیپ‌ها **پیش** از غروب تایمرها انجام شد

در تمام پنجرهٔ فلیپ، تایمرهای قدیمی هم فعال بودند: یعنی هر دو مسیر (تایمر + رویداد) همان runnerهای idempotent را صدا می‌زدند (cursor/seen-set/cap). این خودش یک پاریتی عملی است: رویداد هیچ‌چیز را حذف نکرد، فقط زودتر رساند. سپس در Phase 5 تایمر خاموش شد — با preimage و رسید.

## چیزی که پاریتی **نیست** (صادقانه)

- **Shopify**: push ندارد (webhook + HMAC secret موجود نیست) ⇒ سنسور بیت‌محور (۶۰s) نه رویداد دنیای واقعی. در جدول مهاجرت با دلیل ثبت شده.
- **traffic_seen**: هیچ منبع شمارش بازدید/کلیک روی فلیت وجود ندارد؛ امروز «نقطهٔ صفر» است. رشتهٔ رویداد آمادهٔ اتصال به شمارنده است ولی منبعی برای شمردن نبوده.
- **order_seen/payment_seen**: مغازه واقعاً صفر سفارش دارد؛ رویداد واقعی رخ نداده (نه شبیه‌سازی). سیم‌کشی با اسنپ‌شات زنده اثبات شده (`store_watch v2`، ۵۳ محصول، baseline ثبت).
