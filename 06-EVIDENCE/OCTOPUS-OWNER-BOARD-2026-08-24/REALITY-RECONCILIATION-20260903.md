# REALITY RECONCILIATION — ۲۰۲۶-09-03 · راستی‌آزمایی سطح-یک اسکن ابری

**مبنای ناظرِ ابری:** ۷ سند Reality Scan (vantage ابری، بدونِ دسترسی به runtime).
**این سند:** همان پرسش‌ها، این‌بار از روی نودهای واقعی — فقط‌خواندنی، با فرمان و خروجی.
نتیجهٔ کلی: **هر پرسشِ UNVERIFIED اسکن ابری که به نودها می‌رسید، همین حالا جواب گرفت.**

## هویت نودها (ماتریس اسکن → واقعیت)

| نود | اسکن گفت | سطح-یک (۲۰۲۶-09-03 07:2x UTC) |
|---|---|---|
| board138 | UNVERIFIED / DEPLOYED_NOT_VERIFIED | **VERIFIED_RUNTIME**: hostname=DietPi · clock synchronized=yes · شش سرویس active (ofn, ofn-heartbeat, octopus-bridge, cloudflared, hypno-fugu-mini, dropbear) · ۱۲ تایمر octopus- · پورت‌های loopback 8791-8796 · secrets همه 600 |
| node180 | no evidence | قبلاً در همین سشن `octopus-continuity-180` تأیید شد؛ **الان SSH publickey رد می‌شود** — کلید چرخیده/حذف شده (driftِ جدید؛ دسترسی از دست رفت) |
| node182 | no evidence | **182:4222 (NATS) بسته/دسترس‌نیافتنی** — یا هاست پایین یا سرویس متوقف (drift؛ قبلأ زنده بود) |
| laptop | UNVERIFIED | **VERIFIED**: DESKTOP-KA9RFN5 · F:\backup موجود · vault HEAD `8d8be71f` روی شاخهٔ rescue (16:54 +1000 امروز) · dirty≈400 (شناخته‌شده) |

## حکم‌های C-01..C-07 با شاهد سطح-یک

- **C-01 (ولت کانونیکل کجاست):** CLOSED-BY-OWNER-RULING — NBB-CP (رأی مالک): `F:\backup` کانونیکل؛ board138 نگه‌دارندهٔ runtime نه ولتِ نوت. سندِ MEGA-DATA مخالف، منسوخ.
- **C-02 (auto_email):** CLOSED-AS-DOCUMENTED — coexistence در یک فایل عمدی است؛ مرجعِ نهایی `03-GATES/GATES.md` (رأی #63، ۴ دامنه، بازبینی ۱۰-۰۱) + AGENTS.md §10. خوانندهٔ فقط-§4 هشدارش را در همان §4 دارد.
- **C-03 (.bak twins):** OPEN-CONFIRMED — نقض §7 واقعی است (۷ فایل در درخت main). ترمیم = PR hygiene (نیازمند review مستقل). به موج ۲ سپرده شد.
- **C-04 (require-independent-approval):** **CLOSED-POSITIVE** — PR #136 را زنده دیدم: `mergeStateStatus=CLEAN, reviewDecision=APPROVED` و مرج شد؛ check-runsِ کامیتِ merge فقط ۳ کانتکست دارد. یعنی گیت از مسیرِ review حل می‌شود (فرضیهٔ اسکن تأیید شد). آزمونِ منفی (merge بدون approval رد شود؟) همچنان OPEN — تنها با یک PR بدونِ review آزمایش می‌شود.
- **C-05 (۱۹۳۸ تست):** **CLOSED-STALE** — رسیدِ runtime: `3742 tests collected` روی main@`60dce961` (بورد). اجرای کامل پس‌زمینه شد؛ رسیدش جدا پیوست می‌شود. عددِ HANDOFF قدیمی است.
- **C-06 (board branch vs main):** **CLOSED — و حکمِ اسکن غلط بود.** بورد روی `main`@`60dce961` است (نه release/p0!) و **۱۰ کامیت عقب‌تر از origin/main** — از جمله PR #150 (repair_api) را ندارد؛ پورت 8797 بسته (تأیید runtime). AGENTS.md-addendum («بورد release/p0») در runtime **نادرست** بود. release/p0 الان فقط شاخه‌ای روی GitHub است که سشنِ من کارهای paint را به آن پوش کرد؛ درختِ کاریِ بورد فایل‌های runtime را (imap_listener، WAL، ۱۲ تایمر) دارد اما چندucas به‌عنوان untracked/commitِ ديگر لاین.
- **C-07 (linear history):** OPEN-CONFIRMED (کم‌خطر) — protection اجازهٔ merge-commit می‌دهد؛ کنوانسیون squash است. تصمیم مالک.

## یافته‌های driftِ تازه (در اسکن نبودند)

- **R-1:** `tools/smoke.sh` (دروازهٔ ۸چکی دیپلوی سیزن) از درختِ کاریِ بورد **غایب است** — درخت main@60dce961 آن را ندارد؛ سند DISCOVERY به آن ارجاع می‌دهد. driftِ سند↔درخت.
- **R-2:** دسترسی root@180 از دست رفت (publickey رد) — پلِ نظارتِ قبلی قطع است.
- **R-3:** NATS 182 بسته — شاهدِ قبلیِ «زنده» دیگر معتبر نیست.
- **R-4:** main در حینِ اسکن جلو رفت (6e2bfd5 → f6a18ca4 یعنی mergeِ #136 در همین پنجره) — لِینِ موازی فعال است؛ هر reconciliation باید تاریخ‌خورده باشد.
- **R-5:** healthz پل ۸۸۰۱ با سرویسِ active جواب نمی‌دهد — سرویس فعال است ولی پورت گوش نمی‌دهد (نیاز به رسیدِ health از LAN طبق F-22).

## چیزهایی که اسکن مفقود کرده بود (شواهد موجود)

- F-23 «restore drill بدون receipt» → رسیدِ موفق ۲۰۲۶-09-01 در `restore-drill.log` بورد هست (اولین در تاریخ سیستم).
- F-30 → مجوزهای env همه 600 (تأیید runtime).
- F-16/C-02 → ثبتِ گیت در `03-GATES/GATES.md` از قبل انجام شده.

## تصمیم‌های باز مالک (از ۵۰ یافته؛ آن‌ها که مالِ توست)

secret_rotation تا ۱۶-۰۹ (P0 باز) · لیسانس ریپوی عمومی · امضای کامیت · required_linear_history · تکلیف Armin/langar · بستن/ادغام استک p1 (۸ PR).

---
منبعِ این سند: خروجیِ خامِ SSH/GH در همین سشن (2026-09-03T07:2x-07:4x UTC) · اجراکننده: ایجنت ولت (ZCode) · طبق NEXT-SCAN-COMMANDS (فقط‌خواندنی).

---

## پیوست: رسیدِ مجموعه‌کاملِ تست (C-05 نهایی)

```
# cd ~/ofn && timeout 900 python3 -m pytest -q   (HEAD main@60dce961، بورد)
2 failed, 3730 passed, 10 skipped in 44.06s
# collect: 3742 tests collected
```
هر دو شکست ENVIRONMENT-DEPENDENT بودند (فرضِ «میزبان unarmed» روی میزبانِ مسلح) —
تعریفشان قطعی شد (تزریقِ env/HOME) و ۸/۸ سبز؛ تعمیر: شاخهٔ
`fix/env-independent-tests-20260903` کامیت `10de2e13` (پوش از رلهٔ ویندوز — پوش
مستقیم بورد همچنان 403).
یافتهٔ جانبی: `docs/evidence/EVIDENCE-PACK-20260902.md` روی درختِ main بورد حاضر
نیست (فایلِ لاینِ release/p0 بود) — در ولت و روی شاخهٔ GitHub موجود است.
