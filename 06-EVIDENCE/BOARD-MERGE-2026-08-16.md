---
type: evidence
status: active
session: WIRE auto-run (2h) — اولین ادغام
agent: ZCode (GLM-5.3) — اتوماسیون وایر
created: 2026-08-16
authority: "NBB-V5 + رأی مصاحبه 2026-08-16 (ادغام خودکار + گزارش)"
snapshot: "germline/ofn/board-snapshot-20260816 @ 32a81d0 · 2139 فایل · 35MB"
merge_commit: 18833c2
---

# BOARD-MERGE — پاسِ اول — 2026-08-16

## چه شد

برد snapshot روزانه‌اش را به germline پوش کرد (شاخهٔ `ofn/board-snapshot-20260816`، کامیت `32a81d0`). طبق NBB-V5 (برد مقدم) و رأی ادغامِ خودکار مالک، درختِ کامل به‌صورت **یکپارچه و دست‌نخورده** در `03 - Projects/OFN-Board/` نصب شد (کامیت `18833c2`). هیچ فایل بردی تغییر/حذف نشد.

## چرا یکپارچه و نه per-folder

فرضِ اولیهٔ ادغام (کپی‌های قدیمیِ per-پا در 03 - Projects) **در بازرسی صادقانه برقرار نبود**: پوشه‌های ویندوزی (اونلی فنز · Ziman Galerry · Lead-نقاشی · Mining) پوشه‌های **دانشِ کسب‌وکار** اند (استراتژی، تحقیق، برآورد، DecisionLog) نه کپیِ مونوریپوی برد. برد یک مونوریپوی چند-مستأجری است: kernel مشترک `ofn/` (۹۸ فایل) + فرانت‌های `web/` (panel/lead/studio/ziman + saba) + مانیفست `packs/*.yaml` + data/deploy/docs/migrations/tests/tools. تکه‌تکه‌کردنش در پوشه‌های legacy هم سازه را می‌شکست هم برد-مقدمی را نقض می‌کرد. پس: نصبِ درختِ کامل + آرشیو صفر (چیزی نسوخت — پوشه‌های دانش دست نخوردند).

## نگاشت پاها (board ↔ windows)

| پا (برد) | فایل‌های کلیدی برد | پوشهٔ دانش ویندوز | هم‌پوشانی کد؟ |
|---|---|---|---|
| studio (گالری/محتوا) | web/studio.html + saba-* + packs/studio.yaml | 03 - Projects/اونلی فنز (360 فایل دانشی) | نام‌های عمومی فقط (config.py و…) — نه همان درخت |
| ziman | web/ziman.html + packs/ziman.yaml | Ziman Galerry (250 فایل) | همان‌طور |
| lead | web/lead.html + packs/lead.yaml | Lead-نقاشی/AiFarm-Lead (کد مستقل: orchestrator/telegram_bot) | احتمالی — پاس ۲ |
| hypno | سرویس مستقل + packs/hypno.yaml (تک-کاربر، safety-gate) | — (کپی ویندوزی ندارد) | — |
| panel | web/panel.html (پنل مالک — سلول 🐙 سینک) | — | — |
| mining (ESP32) | **در snapshot نیست** | Mining/02 - Code | n/a — ناوگان ESP32 مال ویندوز است |

## کارِ باز (پاس ۲ — کارت)

- حسابرسی provenance فایل‌به‌فایل: آیا AiFarm-Lead/Ops-Runtime نسخه‌های قدیمیِ اجداد مونوریپوی بردند؟ (git log --follow روی چند فایل مشترک‌نام)
- CHANGELOG/DECISIONS/HANDOFF برد را در _Index - Projects لینک کن

## وضعیت کانال‌ها پس از این پاس

- کلید share: **حذف شد** (KEY-RECEIVED در b003 — راز فقط در دو سرِ کانال)
- صف board_cp: فرمان status اول (01a0096d) توسط curl دستیِ برد pull شد و بی-ack ماند (dispatched) — رکورد صادق؛ فرمان تازه برای تست bridge زنده صف شد
- وایر: w002 (پاسخ به b003) پوش شد · last-seen=b003
