---
type: owner-runbook
status: open-requires-owner-browser
created: 2026-09-08
tags: [octopus, miniapp, telegram, domain, runbook]
gov: GOV-V8 · LADDER=L2
authority: OWNER-APPROVALS دور پنجم R3-3 («بله، منتشر کن»)
---

# ران‌بوک: میزبانی مینی‌اپ روی دامنهٔ زیمان (۳ کلیک مالک)

## وضعیت فعلی (VERIFIED 2026-09-08 ~10:2x local)

- گیت‌وی: `python telegram_center/miniapp_gateway.py` روی `127.0.0.1:8774` (PID 26100)
- تانل: cloudflared **named tunnel** `octopus-miniapp` → `https://app.master-painting.com`
- تست عمومی همین لحظه: **GET 200** در 0.4s (Server: cloudflare)
- واتچ‌داگ هر ۱۰ دقیقه (OCTOPUS-MiniApp-Watchdog) — آخرین: 10:08 OK
- احراز هویت: initData-HMAC تلگرام — فقط چت مالک؛ برای عموم بسته (همان‌طور رأی داده شد)
- فایل URL: `_ops/state/telegram/miniapp-url.json` (kind=named، stale-after-24h)

یعنی مینی‌اپ **هم‌اکنون منتشر و زنده** است؛ این ران‌بوک فقط برای انتقال آدرس به دامنهٔ زیمان است.

## چرا ایجنت نمی‌تواند تنهایی انجام دهد

`cloudflared tunnel login` و افزودن منطقه به حساب Cloudflare = لاگین مرورگری مالک (GOV-V7: ایجنت با credentials کار نمی‌کند). BotFather هم RED-tier/owner-only است.

## مسیر پیشنهادی: app.ziman-gift.shop (ریسک صفر برای فروشگاه)

دامنهٔ .shop امروز هیچ سرویسی ندارد؛ انتقال NS آن هیچ چیز زنده‌ای را نمی‌شکند. مسیر .com.au مستلزم انتقال DNS کل منطقه به Cloudflare است — Same-Day با راه‌اندازی فروشگاه توصیه نمی‌شود (فلگ‌های proxy با Shopify سازگار نیستند مگر DNS-only، و موج propagation تکرار می‌شود).

### کلیک‌های مالک (یک نشست ~۱۰ دقیقه)

1. **Cloudflare Dashboard** (dash.cloudflare.com) → Add domain `ziman-gift.shop` → Free plan → دو NS را که می‌گوید بردار.
2. **GoDaddy** → ziman-gift.shop → Nameservers → Custom → دو NS بالا را بگذار. (اگر پنل باز نیست، ایجنت بعد از ورود مالک انجام می‌دهد — فقط بگو «آماده».)
3. بعد از فعال‌شدن منطقه در Cloudflare (دقایقی)، در PowerShell لپ‌تاپ:
   ```
   cloudflared tunnel login          # مرورگر باز می‌شود، منطقهٔ ziman-gift.shop را انتخاب کن
   cloudflared tunnel route dns octopus-miniapp app.ziman-gift.shop
   setx OCTOPUS_MINIAPP_HOSTNAME "app.ziman-gift.shop"
   ```
4. **BotFather** → /myapps → اپ فعلی → Edit URL → `https://app.ziman-gift.shop`
5. ری‌استارت تانل: `powershell -File _ops\telegram_center\run-miniapp-tunnel-named.ps1` (واتچ‌داگ تا آن زمان quick-tunnel fallback را زنده نگه می‌دارد؛ بعد از تعویض hostname، اولین tick خودش named را بالا می‌آورد).

### تأیید پایانی (ایجنت)

- GET `https://app.ziman-gift.shop` → 200
- `miniapp-url.json` → kind=named با url جدید
- دکمهٔ web_app در چت مالک با آدرس جدید باز شود

## rollback

`setx OCTOPUS_MINIAPP_HOSTNAME "app.master-painting.com"` + ری‌استارت تانل + BotFather URL قبلی.

## ثبت

رأی R3-3 در OWNER-APPROVALS دور پنجم؛ این سند در UNLOCK-REGISTRY تاریخچه ۲۰۲۶-09-08 ارجاع می‌شود.
