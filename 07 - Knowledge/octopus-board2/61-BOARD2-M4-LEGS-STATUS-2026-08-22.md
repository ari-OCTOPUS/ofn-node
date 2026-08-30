# Board2 / M4 Legs Runner — وضعیت زنده (2026-08-22)

> منبع: marketing (Board2 DietPi `192.168.0.138`) · گزارش برای ari / Obsidian SoT  
> نقش قفل: **M4 Legs Runner** — فقط business legs؛ بدون beat / budget / ORGANISM-STATE / brain keys / killswitch  
> Owner از طریق **ari** صحبت می‌کند.

## خلاصه تصمیم

درخواست owner برای «کدنویسی همه مفاهیم داخلی + اتوماسیون همه بیزنس‌ها + واقعی‌سازی کامل» **خارج از lane برد ۲** است.  
کار انجام‌شده روی Board2: اسکن/دیباگ/فیکس‌های مجاز + بستهٔ شواهد. بازنویسی Center / Doctor / beat / کل بیزنس‌های لپ‌تاپ = مالکیت **ari + F:\backup**.

**Overall الآن: GREEN**

## وضعیت زنده (scan `20260822T120745Z`)

| سطح | نتیجه |
|---|---|
| Phase-3 CONTROL pull | PASS — `https://cp.master-painting.com` · noauth 401 · auth 200 · pull_count 0 |
| Bridge پس از key-rotate | PASS — `octopus-bridge` active · OUTBOUND=1 · PULL=1 · CA_FILE off |
| ofn/wire GitHub read | PASS — `ls-remote` ofn/wire @ `ca038d42a1f2` |
| چهار پا | PASS — ziman/lead/studio/panel `:8791-8794` `/healthz` → 200 |
| ofn + heartbeat | active |
| ofn-backup | PASS (oneshot) — آخرین موفق `20260822-110258` · Result=success |
| hypno | PASS — واحد درست = `hypno-fugu-mini` active روی `:8895` (نه `hypno.service`) |
| CPU/RAM harm | هیچ |

## گیت‌های OFN (Board2)

باز (طبق CHG owner): `fee_payment`, `auto_payment`, `live_email_send`, `live_publish`  
بستهٔ باقی‌مانده:  
`wire_outbound,live_sms,live_dm,tender_submit,vendor_submit,portal_submit,terms_acceptance,auto_scrape,auto_post,auto_dm,auto_email`

## کارهای انجام‌شده امروز (Board2)

1. Phase-3 PASS — CONTROL_URL CF · UA patch · CA pin drop  
2. Bridge API key rotate PASS (matching laptop `OCTOPUS_BOARD_CP_BEARER`)  
3. GitHub read-only PAT برای ofn/wire PASS  
4. YELLOW fix PASS — chown `fugu_core/memory.sqlite` به `ari:ari` · hypno reconcile  

## شواهد

- `F:\backup\06-EVIDENCE\BOARD2-PHASE3-2026-08-22\`
- `F:\backup\06-EVIDENCE\OCTOPUS-BOARD2-BRIDGE-KEY-ROTATE-2026-08-22\`
- `F:\backup\06-EVIDENCE\OCTOPUS-BOARD2-GITHUB-READONLY-2026-08-22\`
- `F:\backup\06-EVIDENCE\BOARD2-OFN-BACKUP-FIX-2026-08-22\`
- `F:\backup\06-EVIDENCE\BOARD2-HEALTH-2026-08-22\`
- `F:\backup\06-EVIDENCE\BOARD2-WATCH-2026-08-22\`
- این بسته: `F:\backup\06-EVIDENCE\BOARD2-OWNER-PACKAGE-2026-08-22\`

## تصمیم‌های باز (برای ari / owner)

- واقعی‌سازی عمیق بیزنس‌ها (ziman/lead/studio/panel workflows، اتوماسیون لپ‌تاپ، Doctor، beat) → **ari SoT** نه Board2 rewrite  
- هر mutate جدید روی برد فقط با brief از ari  
- Watch ادامه دارد؛ بدون setWebhook / re-rotate خودسر

## ممنوع‌ها (Board2)

beat · budget writer · ORGANISM-STATE · brain keys · killswitch · secrets در چت · git add فایل‌های secret

## Folded by ari 2026-08-22
