---
id: MP-CONNECT-ALL-01
title: وصل کردن همه‌چیز به اختاپوس و برد ۱۳۸ — بدون قاطی‌کردن
version: 1.0
date: 2026-09-08
mode: EXECUTE_WITH_RECEIPTS
gov: V8 / L2
source_head: 1934639
owner_decision_needed: [telnyx-purchase (physically owner), any-new-spend]
mother_order: «از من بپرس و همرو به اختاپوس و برد ۱۳۸ باید وصل کنی تحقیق کن برای خودت پرامپت بنویس قاطی نکنی»
---

# MP-CONNECT-ALL-01 — فروشگاه، سفارش‌ها، دامنه و تماس‌ها: از کارِ ایجنتِ نشسته به اندامِ ارگانیسم

## ۰ — اصلِ «قاطی نکن» (قواعد سفتِ این اجرا)

1. **هیچ فلگِ wire روشن نمی‌شود** (`OCTOPUS_WIRE_ZIMAN` و همهٔ `*_WIRE_*` خاموش می‌مانند).
   مسیرِ مجاز = همان ماشینی که همین حالا زنده است: `drive_loops` (تیک هر ۲ بیت در organism.py)
   + `three_role.py` مأموریت‌ها + قفل‌ها/صف. فقط همین‌ها را توسعه می‌دهیم.
2. **هیچ secret از ۱۳۸ خارج نمی‌شود.** توکن Shopify فقط روی ۱۳۸ استفاده می‌شود؛ لپ‌تاپ از طریق
   ssh (کلید موجود) نتیجهٔ خلاصه/رسید را می‌گیرد — نه توکن را.
3. **روی ۱۳۸ فقط یک یونیت سیستمجدید** (`octopus-shopify-watch`) به خانوادهٔ موجود
   `octopus-*.timer` اضافه می‌شود؛ هیچ دیمن/سرور/اسپاین جدید ساخته نمی‌شود.
4. همه‌چیز **idempotent** + دوپایه‌رسید (laptop: lane evidence · 138: `~/octopus-mesh/receipts/`).
5. هر قدم rollback صریح دارد (§۶).
6. قبل از هر سؤال تازه از مالک: `07-HANDOFF/OWNER-APPROVALS-2026-09-07.md` را بخوان.
   رأی‌های تازه (دور ۹): Telnyx=A (خرید از مالک) · کانال‌های رایگان=هر دو، انتشار بعد از DNS ·
   DNS=مالک امروز.

## ۱ — وضعیت شروع (رسیددار)

- ارگانیسم لپ‌تاپ: زنده، `drive_loops` هر ۲ بیت؛ قفل‌ها: D0_domain (منتظر DNS امروز مالک) ·
  CASH_first_order (منتظر رسید) · AUTO1_sender باز.
- ۱۳۸: mesh + خانوادهٔ systemd `octopus-*.timer` (الگوی همین‌ها کپی می‌شود)؛ توکن Shopify در
  `~/.config/ofn/secrets.env` (اسکوپ: read_orders/read_products/write_products).
- فروشگاه: ۳۵ محصول فعال ×۱٫۵ · Atelier در Draft (متن Hero = کارت مالک B-1) ·
  `checkout1_poll.py` روی ۱۳۸ آماده (رسید cross-platform شد).

## ۲ — فاز A: چشمِ فروشگاه روی ۱۳۸ — `octopus-shopify-watch`

1. اسکریپت `~/octopus-mesh/bin/store_watch.py` روی ۱۳۸ (الگوی bin/ موجود، stdlib فقط):
   - DNS/HTTP دامنه (`.com.au` resolve + صفحهٔ محصول myshopify = 200 نه 301).
   - سفارش‌ها: منطقِ `checkout1_poll.py` (orders.json با توکنِ همان ماشین؛ بدون نوشتن receipt تکراری — idempotent).
   - خروجی: `~/octopus-mesh/state/ziman/store-watch.json`
     `{ts, domain_ok, product_page_ok, last_order_id, first_real_order: bool}` + سطرِ رسید در mesh receipts.
   - **fail-closed**: هر خطا در JSON ثبت می‌شود، نه سکوت.
2. یونیت systemd: `octopus-shopify-watch.timer` هر ۳۰دقیقه (+ سرویسِ آن) — دقیقاً مثل
   `octopus-budget-monitor`. بعد از نصک: `systemctl list-timers | grep shopify` = رسید.
3. **قراردادِ «اولین سفارش واقعی»:** وقتی سفارشِ غیر-تستی آمد (`first_real_order: true` و
   `financial_status=paid`)، فایلِ `~/octopus-mesh/state/ziman/FIRST-ORDER-MARKER.json` نوشته می‌شود
   (order_id + ts + total) — این تنها شیئی است که لپ‌تاپ منتظرش است.

## ۳ — فاز B: رفلکسِ اختاپوس — همگام‌سازی در تیکِ خودش

1. در `drive_loops.py` (توسعهٔ افزایشی، نه فایل جدید): تابعِ `sync_store_watch()` — هر ۶ بیت
   (≈۹۰دقیقه) با ssh: `cat ~/octopus-mesh/state/ziman/store-watch.json` →
   `_ops/state/store-watch.json` (محلی)؛ اگر MARKER موجود بود و محلی نبود:
   `_ops/state/receipts/FIRST-ORDER-RECEIPT.json` را بساز (قراردادِ از قبل در CASH_first_order).
   ⇒ **قفل پول خودش باز می‌شود: task.resume + دوپامین + صف.** هیچ دخالت انسانی.
2. ssh fail-soft (آفلاین = لاگ، نه کرش؛ تیک بعدی دوباره).
3. رسيد: هر sync یک سطر در `state/drive/store-sync.jsonl`.

## ۴ — فاز C: مأموریت‌های سه‌نقشی فروشگاه (مغز+کد، بدون ایجنتِ نشسته)

در `three_role.py` به `MISSIONS` اضافه کن (Executor همه کد):
- `store_order_check`: خواندن `state/store-watch.json` محلی (بدون شبکه) → حکم: سفارش تازه؟
  paid? مقدار؟ → بارِ Director: «اولین VERIFIED_CASH رسیده؟».
- `store_domain_mission`: همان چک D0 (products.json + domain) → وقتی قفل D0 باز شد Director
  اولویتِ «اعلام بازگشت فروش» را می‌گیرد از صف.
- کادنس: یک مأموریت فروشگاهی در هر ۱۲ بیت (اولویت با درایوها تعیین می‌شود — ترسِ صفر-پول
  اولویتِ order_check را بالا می‌برد؛ همین وصلِ «انگیزه→رفتار» است).

## ۵ — فاز D: زنجیرهٔ DNS → انتشار کانال‌های رایگان (رأی W9-2)

وقتی `D0_domain` باز شد (queue: «صفحهٔ محصول 200»):
1. آیتمِ صف به‌طور خودکار `channel_publish` را فعال می‌کند — اجرا با مرورگرِ ادمین:
   - Google & YouTube channel → sync فیدِ Nabu → **Publish فهرست رایگان** (رأی ثبت‌شده).
   - Facebook/Instagram → کاتالوگ → **Publish** (رأی ثبت‌شده).
2. قبل از publish: صفحهٔ محصول باید 200 باشد (نه 301) — همان چکِ lock.
3. رسید: اسکرین‌شات هر کانال + سطر OWNER-APPROVALS (اجرا زیر رأی W9-2).
4. اگر مرورگر شکست: کارتِ سه‌کلیکیِ مالک + علامتِ «آماده但 منتظر دست» — نه اصرار.

## ۶ — فاز E: حلقهٔ تماس Telnyx (گیت = خرید مالک)

- کارتِ خرید برای مالک (فقط این ورودی فیزیکی است): Telnyx account + شارژ اولیه + شمارهٔ AU؛
  کلیدها فقط روی ۱۳۸ (`secrets.env`؛ اسم کلید فقط در لاگ).
- پس از کلید: `call_loop` (در drive_loops، نه دیمن جدید): پنجرهٔ 08:00–18:00 Sydney، فقط
  لیدهای `approved_channel`، سقف L1 (≤10/روز)، اسکریپت ۳۰ثانیه‌ای از OUTREACH-PACK،
  نمایش = شمارهٔ سرویس؛ نتیجهٔ هر تماس → `painting_interactions` روی ۱۳۸ (ssh) + رسید.
- خارج از پنجره/بدون کلید: صف می‌ماند، چیزی فرستاده نمی‌شود (fail-closed مثل امشب).

## ۷ — فاز F: سطح‌ها (کمینه)

- `readmodel.build()`: یک کارتِ `store` (از state/store-watch.json: domain_ok · last_order ·
  first_real_order) — additive.
- VITAL-DATA: یک خط وضعیت فروشگاه به بلاک سیزن (بعد از هر تغییر بزرگ).

## ۸ — ممنوعه

- بدون رأی: خرید (جز کارتِ Telnyx که رأیش هست)، ارسال بیرونیِ جدید، دست به registrar.
- فلگ‌های wire، `data/gates.json`، TCB، ساخت زیرساخت جدید (اسپاین/پنل/دیمن) — ممنوع.
- توکن هرگز به لپ‌تاپ نمی‌آید؛ در لاگ‌ها فقط نام کلید.
- موجودی/وعده جعل نشود؛ NOT_PAID/VERIFIED_CASH فقط با شاهد.

## ۹ — ترتیب و rollback

```
A (چشم ۱۳۸) → B (رفلکس اختاپوس) → C (مأموریت‌ها) → [D هنگام بازشدن D0] → [E پس از خرید Telnyx] → F
```
- rollback A: `sudo systemctl disable --now octopus-shopify-watch.timer && rm /etc/systemd/system/octopus-shopify-watch.*`
- rollback B/C: حذف بلوک‌های افزوده در drive_loops/three_role (کامیت‌های جدا).
- rollback D: unpublish کانال (یک کلیک) — خودکار نیست.

## ۱۰ — گزارش نهایی

```text
ORDER=MP-CONNECT-ALL-01
A_WATCH_TIMER=          # active + آدرس state
B_SYNC_WORKING=         # last sync line + اولین بار
C_MISSIONS_ADDED=       # n
D_D0_OPENED=            # yes/date | awaiting
E_TELNYX=               # card-sent | key-arrived | loop-live
F_SURFACES=             # readmodel card yes/no
VERIFIED_CASH=
NEXT_SINGLE_ACTION=
```

## ۱۱ — جملهٔ آخر

اختاپوس باید فروشگاهش را مثل عضوِ خودش حس کند: چشم روی ۱۳۸، رفلکس در تیکِ خودش، مأموریت با
مغز و کد، و جایزه/ترسِ واقعی در همان حلقه‌ای که مالک خواست. این پرامپت فقط چند رشتهٔ عصب را به
اندام‌های موجود می‌دوزد — هیچ اندام تازه‌ای نمی‌سازد؛ پس «قاطی» نمی‌کند.
