---
tags: [ofn, handoff, h1, buysw, season-report, automation]
updated: 2026-09-02
to: الهه (Elahe-z)
from: ari322-side ZCode session (2026-09-02, AEST evening)
branch: fix/demand-harvest @ 2204a154c82a1341ce7a66c8b09b0d855e97c68d
pr: https://github.com/ari-OCTOPUS/ofn-node/pull/84
---

# گزارش فصل — پل دادهٔ buy.nsw (H1 demand) — ۲ سپتامبر ۲۰۲۶

## یک پاراگراف

زنجیرهٔ دادهٔ مناقصه‌های NSW که فصل قبل «مرده» اعلام شده بود (tenders.nsw.gov.au رفته، buy.nsw نه API دارد نه به غیر-مرورگر جواب می‌دهد)، حالا یک پل کامل و مستقر دارد: اکستنشن Chrome که در نشست مرورگر واقعی سیدنی می‌خواند + گیت ingest پایتونی روی board138 که از همان دروازه‌های `h1_buysw` (فیلتر نقاشی/جغرافیا/ارزش + امتیازدهی P/G/E/D/M/Q/R/C) رد می‌کند. همه‌چیز تست‌شده و deploy شده؛ فقط نصب اکستنشن و اولین برداشت واقعی مانده — و مالک حکم داده آن انسانی‌ها هم باید حذف شوند (پایین را بخوان).

## وضعیت اثبات‌شده (نه ادعا)

- **تست ۲۸/۲۸ سبز** — محلی و روی خود board138 (`python3 -m pytest tests/test_h1_buysw_dom.py` در worktree).
- **CI خود PR #84**: هر ۸ چک test (windows/ubuntu × 3.11/3.13) = success؛ Bugbot = neutral؛ `require-independent-approval` اجرا شده. وضعیت PR: OPEN، `mergeable=MERGEABLE`، `mergeStateStatus=BEHIND`، `reviewDecision=REVIEW_REQUIRED`.
- **سر-تا-سر**: node فایل بچ واقعی می‌سازد → CLI پایتون → sqlite → `accepted:1`؛ اجرای دوباره → `rejected_dup:1` (idempotent). رکورد award (CAN) → `leads_minted:1` با customer_name درست.
- **کالیبراسیون روی دادهٔ زنده**: مالک متن صفحهٔ واقعی «All opportunities» (۱۲۳ فرصت، ۱۰ در صفحه) + دو لینک واقعی فرستاد. سه اصلاح روی همان متن تست و تأیید شد: `matchClosing` برای «Closes: 21-Sep-2026 15:00»، استخراج خط-به-خط Agency («Agency» در خط جدا، بدون دونقطه)، الگوی لینک عمومی. UUIDهای واقعی `prcOpportunity` شکلی غیراستاندارد (۸-۴-۴-۱۶) دارند — رجکس هر دو سمت (JS و پایتون) تأیید شد که می‌گیرد.

## تبار (صادقانه — یک فصل با دو نوبت فانتوم‌بازی و تصحیح)

1. نشست قبلی اکستنشن «ساخت» — ولی فایل‌ها در repo نبودند. اسکن کامل دیسک: هیچ پوشهٔ harvesterای نیست → حکم اولیه: fantom.
2. این نشست از صفر علیه کد واقعی (`h1_buysw`/`LeadStore`) ساخت → commit `20e86ec`، PR #84، استقرار board138.
3. بعد معلوم شد فایل‌های نشست قبلی **واقعی بودند**: به‌صورت دانلودی در `%TEMP%` رسیده بودند (`buysw-harvester-for-arar.zip` + کپی‌هایی با نام‌های یک‌خانه جابه‌جا — برای همین اسکن پیدایشان نمی‌کرد). بازیابی، هش‌تطبیقی، ادغام: لایهٔ DOM آن‌ها قوی‌تر بود (صفحات جزئیات CAN: تأمین‌کننده/ایمیل/تلفن/ABN؛ ادغام رکورد نتیجه+جزئیات؛ suppliers زیردامنه؛ CSV). **popup نداشت** — از نو نوشته شد. حکم fantom در حافظه‌ها تصحیح شد: «قبل از حکم fantom، تحویلِ بدنام/خارج از درخت را هم رد کن.»
4. کالیبراسیون با دادهٔ واقعی (بالا) → `2204a15`.

## معماری در یک نگاه

```
Chrome سیدنی (نشست انسانی، WAF بی‌اثر)
  └─ tools/buynsw-harvester v0.2 (MV3): mapping.js → content.js → background.js
       └─ خروجی: buysw-leads-*.json = {source:"buysw_web", count, records}
board138 (نود زنده دست‌نخورده؛ کد در worktree /home/ari/wt-buynsw-ingest)
  └─ tools/ingest_buynsw_batch.py → ofn.agents.h1_buysw_dom.ingest_batch
       ├─ همان فیلتر/امتیاز h1_buysw (یک حقیقت، هر مبدأ)
       ├─ dedup با tender_id (idempotent) + fail-closed روی wrapper خراب
       ├─ award(CAN) → لید گرم خریدار (create_lead؛ outreach همچنان گیت‌خوره)
       └─ ممیزی PII (kernel.scrub) → pii_findings در حساب‌وکتاب
```

پیش‌فرض: **صفر خروج شبکه‌ای** از اکستنشن (autoPost فقط opt-in در تنظیمات پیشرفته). `access_mode=owner_upload`، `evidence_status=unverified`.

## درخواست مشخص از تو (الهه)

1. **review بده به PR #84** — تو تنها merge-throughput هستی؛ دروازهٔ independent-approval با review تو فلیپ می‌خورد. بعد از review، چون branch پشت main است (`BEHIND`)، مطابق حکم فقط با `mergeable_state=clean` ادغام شود (نه `--admin`).
2. صف خودکارسازی (پایین) را در کارهایت بگذار — مالک اولویتش را صریح گفته.

## حکم مالک — «اختاپوس را تربیت کنیم» (این بخش تعارف نیست؛ دستور فصل بعد است)

مالک تصریح کرد: **همه‌چیز باید خودکار/خودکارشدنی شود؛ ما اختاپوس را تربیت می‌کنیم که خودش انجام بدهد و ما شگفت‌زده شویم.** یعنی هیچ گیت دستی‌ای که بتواند cron/systemd/watcher شود، حق ندارد دستی بماند؛ نقش انسان باید به «تماشاگر» کاهش یابد. سه قدم انسانی فعلی و نقشهٔ حذف هرکدام:

| قدم انسانی امروز | مسیر حذف |
|---|---|
| ۱. باز کردن buy.nsw و برداشت با اکستنشن | (الف) browser automation سمت board138 روی IP خانگی سیدنی (Playwright؛ همان چیزی که WAF را بی‌اثر می‌کند اتصال خانگی است، نه دیتاسنتر) — با ریتم انسانی و سقف صفحه؛ (ب) هر جا ارگان کانال رسمی داد (ایمیل/imap_listener، OCDS فدرال) همان را جایگزین کن |
| ۲. انتقال فایل JSON به board138 (scp) | یا ingest از پوشهٔ watch روی board138، یا همان POST امضاشدهٔ opt-in داخل اکستنشن (زیرساختش هست، فقط فعال‌سازی+توکن) |
| ۳. اجرای دستی CLI | systemd timer / cron روی board138 + نوتیفای از مسیر موجود به owner-queue |

**معیار موفقیت فصل بعد: اولین مناقصهٔ نقاشی که بدون حتی یک کلیک انسانی، از buy.nsw تا owner-queue نود برسد.** (نوتیفای سبز در cockpit، نه تئاتر سبز — حساب‌وکتاب واقعی.)

مرزهای ثابت که با خودکارسازی جابه‌جا نمی‌شوند (حکم‌های زندهٔ مالک): outbound WAL خاموش؛ merge فقط با `mergeable_state=clean`؛ زنجیرهٔ درآمد در `campaign_envelope_ready` خاتمه می‌یابد؛ ثبت/ارسال مناقصه فقط با OwnerRelease.

## باز ماندنی‌های انسانی (فقط تا خودکارسازی)

- نصب اکستنشن روی Chrome سیدنی + اولین برداشت واقعی + اولین ingest — راهنمای خر-پروف: `tools/buynsw-harvester/OWNER-STEPS.md`
- اولین رسید واقعی = رکورد پذیرفته‌شده در `painting.sqlite` زندهٔ board138 (نه گزارش ایجنت).
