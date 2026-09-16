# OP-4 — نقشهٔ آمادگیِ زنجیرهٔ پول (walk فقط‌خواندنی + ترمیم مستقر)

تاریخ: 2026-09-09 (اجرای 2026-09-08T20:54Z..21:25Z) · GOV-V8 · L2

## ۶ چک PASS/FAIL

| # | چک | verdict | شاهد |
|---|---|---|---|
| 1 | octopus-shopify-watch.timer فعال روی ۱۳۸ | **PASS** | `systemctl list-timers`: آخرین 20:30:03Z، بعدی 21:00Z، cadence 30min؛ `journalctl`: اجراهای 20:00/20:30 هر دو سالم (`dns_ok=true page_ok=true orders.ok=true`) |
| 2 | store-watch.json سالم و تازه | **PASS (بعد از ترمیم)** | ۱۳۸: `~/octopus-mesh/state/ziman/store-watch.json` همیشه تازه (20:30Z موقع چک). لپ‌تاپ: mirror از 11:48Z مرده بود (ریشه ↓) — بعد از ترمیم، pull موفق 21:20:51Z با دیتای 21:00:03Z |
| 3 | منطق sync_store_watch با MARKER ساختگی tmp | **PASS 4/4** | `op4-sync-marker-sandbox-test.py`: (A) مارکر+بدون رسید⇒رسید ساخته (B) رسید هست⇒بازنویسی نه (C) بدون مارکر⇋هیچ (D) فیلدهای قراردادی order_id/total/financial_status/created_at/witness ✓ — هیچ MARKER واقعی ساخته نشد |
| 4 | NS اتوریتاتِ دامنه | **PASS** | `nslookup ziman-gift.com.au ns73.domaincontrol.com` → **23.227.38.32** (Shopify) |
| 5 | حلقهٔ ارزیابی قفل‌ها زنده | **PASS (بعد از ترمیم)** | drive-state.json ارزیابی 21:23:15Z؛ `CASH_first_order=locked` (صادق — صفر سفارش)؛ store-sync.jsonl ورودی 21:20:51Z ok=true |
| 6 | بدون مارکر جعلی روی ۱۳۸ | **PASS** | `ls ~/octopus-mesh/state/ziman/FIRST-ORDER-MARKER.json` → No such file (همچنین receipts محلی وجود ندارد) |

## یافتهٔ اصلی: حادثهٔ «بازتابِ مرده» (12:50Z→20:57Z — ~۸ ساعت)

- نشانه: store-sync از 11:48Z و drive-state از 12:19:20Z قفل؛ ارگانیسم زنده (beats جلو می‌رفت).
- ریشه: `organism tick error: FileNotFoundError: 'F:\backup\04 - Architect System\prompts\metabolic-governor-v0.1.txt'` — اولین‌بار 2026-09-08T22:50:19 local (12:50:19Z) در governor-alerts. یک checkout در فاصلهٔ 12:19Z..12:50Z هر ۳ فایلِ tracked پوشهٔ prompts/ را از disk محو کرده (sparse: `/*`+`!/*/`). تیک در `_ops/budget/governor_epoch.py:460` (prompt_file.read_text) می‌مرد و هرگز به بلوک drive_loops (organism.py:1426) نمی‌رسید.
- ترمیم (درسِ مستقر، بدون checkout): `git show HEAD:<path>` برای ۳ فایل — metabolic-governor-v0.1.txt (7128B) · debate-architect-role.txt (1673B) · debate-muse-role.txt (1570B).
- بهبود اثبات‌شده: تیکِ بیتِ 66588 (%6==0) در 21:20:51Z سینکِ موفق زد و 21:23:15Z ارزیابیِ drive نوشت. **سقفِ تأخیرِ بازشدنِ قفلِ CASH در صورت سفارشِ واقعی از ~∞ به ~90min (هر ۶ بیت) برگشت.**
- اسکن بقیه: parent-exists روی 51,190 فایلِ tracked → 0 فایلِ محو؛ ۶۹۷ پوشهٔ tracked-غایب = sparse-exclusion عمدی (به‌جز prompts/ که مصرف‌کنندهٔ زنده داشت — ترمیم شد)؛ `4d_system/src/nbb_cp` (۳۴ فایل) غایب ولی فقط cockpit/registry/smoke می‌خوانندش نه تیک زنده — ثبت شد، بازگردانی نشد (نامرتبط با زنجیرهٔ پول).
- خطای بازماندهٔ جدا (از OP-4 خارج، ثبت برای مالک): مغزِ پولیِ cortex روی هر دو tier می‌شکند — مدلِ استدلالی کلِ max_tokens را صرفِ تفکر می‌کند، 0 کاراکتر مرئی (alerts 07:13–07:14 local)؛ fallback = local garbage (glm/ollama). ربطی به این حادثه ندارد.

rollback: حذف ۳ فایلِ بازگردانده (یا `git checkout -- "04 - Architect System/prompts/"`) — بدون اثر جانبی؛ خودِ ارگانیسم تیکِ بعد را می‌گیرد.
