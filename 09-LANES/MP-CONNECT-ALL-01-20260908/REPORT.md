---
order: MP-CONNECT-ALL-01
date: 2026-09-08 (عصر — اجرای کامل فازهای فوری)
gov: GOV-V8 / L2
---

# گزارش اجرای MP-CONNECT-ALL-01

```text
ORDER=MP-CONNECT-ALL-01
A_WATCH_TIMER=active ✅            # octopus-shopify-watch.timer هر ۳۰دقیقه؛ اجرای اول 04:13Z موفق؛ state: board138:~/octopus-mesh/state/ziman/store-watch.json + رسید jsonl
B_SYNC_WORKING=yes ✅              # sync_store_watch() در drive_loops (هر ۶ بیت)؛ تست دستی موفق (04:14Z: ok=true, schema=store-watch.v1)؛ لاگ: state/drive/store-sync.jsonl؛ ارگانیسم با کد نو ری‌استارت (PID 26704)
C_MISSIONS_ADDED=1                 # store_order_check (اولویت ۲) — اجرای سه‌نقشی: Director پیکش کرد ✓، حکم صادق FAIL 2/4 (چشم وصل ✓✓ · دامنه بسته ✗ · سفارش صفر ✗ — واقعیتِ منتظر DNS)؛ باگ TZ تازگی فیکس شد
D_D0_OPENED=awaiting_owner_dns     # زنجیرهٔ publish کانال‌ها (رأی W9-2) مسلح؛ با بازشدن قفل خودکار فعال
E_TELNYX=card-ready                # خرید = ورودی مالک؛ حلقهٔ 08-18 در مگاپرامپت §۶ مشخص؛ کلید فقط روی ۱۳۸
F_SURFACES=yes ✅                  # readmodel 1.1 + کارت store (domain_ok/first_order، freshness)
VERIFIED_CASH=0.00
NEXT_SINGLE_ACTION=مالک: DNS (امروز) + خرید Telnyx + کارت متن Hero (B-1)
```

## اتصال‌های برقرارشده (نقشه)

```
[۱۳۸] octopus-shopify-watch.timer (۳۰دقیقه)
   ├─ DNS/صفحهٔ محصول + سفارش‌ها (توکن فقط روی ۱۳۸)
   ├─ state/ziman/store-watch.json + receipts/store-watch.jsonl
   └─ FIRST-ORDER-MARKER.json (وقتی اولین سفارشِ paid آمد)
            │ ssh (نتیجه، نه توکن)
            ▼
[اختاپوس] drive_loops.tick هر ۲ بیت ──(هر ۶ بیت)──▶ sync_store_watch()
   ├─ state/store-watch.json (محلی) ─▶ readmodel کارت store ─▶ پنل/مینی‌اپ
   ├─ MARKER → state/receipts/FIRST-ORDER-RECEIPT.json
   └─ ⇒ قفل CASH_first_order خودکار باز ─▶ task.resume + دوپامین + صف
            ▼
[مغز+کد] three_role: store_order_check (اولویت با درایو: ترسِ پولِ صفر)
```

## قواعد «قاطی نکن» رعایت‌شده

- صفر فلگ wire · صفر دیمن جدید (فقط یک یونیت systemd در خانوادهٔ موجود) · توکن هرگز به لپ‌تاپ نیامد ·
  همه‌چیز idempotent + دوپایه‌رسید · rollback: `sudo systemctl disable --now octopus-shopify-watch.timer` +
  revert کامیت‌های drive_loops/three_role/readmodel.

## رسیدها

- 138: `~/octopus-mesh/bin/store_watch.py` + `/etc/systemd/system/octopus-shopify-watch.{service,timer}` +
  `state/ziman/store-watch.json` + `receipts/store-watch.jsonl`
- laptop: کامیت این گزارش + `state/drive/store-sync.jsonl` + سه‌نقشیِ R-307479757cb7 (store mission)
- ارگانیسم: PID 26704 (ری‌استارت تمیز با کد نو؛ RESTART-ORGANISM.bat)
