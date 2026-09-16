---
type: report
status: draft
created_by: agent
tags: [ingestion, afferent, crypto, accounting, sensory-bus, propose-only]
created: 2026-07-09
updated: 2026-07-09
---

# INGESTION-REPORT — پاسِ دادهٔ خام (crypto + accounting)

> propose-only · محلی · $0 · صفر نشتِ PII · **بدونِ git commit** (خط قرمز). ابزار: `_ops/afferent/ingest_raw.py` (uncommitted). همهٔ نوت‌ها draft برای verdict انسانی.

## چه ingest شد

| اولویت | ورودی | خروجی | روش |
|---|---|---|---|
| **P1 Crypto** | ۱۵ JSON (~۱۴۲MB؛ بزرگ‌ها ۵۴/۲۹/۲۵MB) | ۱۵ نوتِ `*-summary.md` کنارِ snapshot در پوشهٔ Crypto | برنامه‌ای (json + introspection): schema + aggregate (سکه‌ها، بازهٔ تاریخ، min/mean/max سری‌های سرآمد). **هرگز full-dump به LLM** |
| **P4 analysis** | ۵ JSONِ آماده | در همان summaryها فولد شد | سیگنال‌های buy/sell/hold + top candidate symbols |
| **P2 Accounting** | ۶ xlsx (PII) | ۶ نوتِ `*-structure.md` **داخلِ پوشهٔ Accounting** (containment) | **stdlib zip/XML، فقط تعداد شیت + ابعاد — صفر مقدار/ردیف/نام خوانده شد** (بدونِ sharedStrings/cell). هرگز به هیچ LLM |

## متریکِ afferent (سیستم دیگر «رؤیا» نمی‌بیند)

- **قبل:** `afferent_ratio = 0.0` → آلارمِ `afferent-deficit` **فعال** (همه رویدادِ درونی، صفر ورودیِ حسی).
- **بعد (۲۱ observation):** `afferent_ratio = 0.512` (crypto+acct) / `0.429` (crypto فقط) → آلارم **خاموش** (بالاتر از آستانهٔ ۰.۱۵).
- یعنی ingestion دقیقاً کارِ خواسته‌شده را کرد: ورودیِ حسیِ واقعی وارد شد.

## راستی‌آزمایی ($0)

- `test_sensory.py` → **۸/۸ سبز** (شامل «no production import» + «no raw_data stored»).
- `pii_flags: []` روی هر ۲۱ observation و هر ۲۱ نوت (چکِ `_contains_pii` روی کلِ متنِ هر نوت پیش از نوشتن).
- **Accounting: صفر ردیف/مقدار/نام** — نوت‌ها فقط نامِ شیت (عمومی: «PS Export»/«Sheet1») + ابعاد (مثل `A1:N7`). گرپِ مستقلِ مقدارِ پولی/PII: تمیز.
- هر summary یک نوتِ `status: draft` (propose-only) است؛ منبعِ خام دست‌نخورده.
- فیدِ sensory_busِ Accounting با لیبلِ کاملاً انتزاعی (`accounting workbook · N sheets`) — بدونِ نام/فایل، cross-domain امن.

## ⚑ برای معمار (deferred / تصمیم)

1. **P2 ستون/جمع:** `openpyxl` نصب نیست و `$0/offline` اجازهٔ نصب نداد — پس فقط **ساختار** (شیت/ابعاد) استخراج شد. استخراجِ نامِ ستون‌ها + جمع/دسته‌ها منتظرِ openpyxl (یا پارسرِ stdlib عمیق‌تر). عمداً partial ماند تا هیچ ریسکِ PII نباشد.
2. **P3 Mining PDF:** هیچ کتابخانهٔ متنِ PDF نیست (fitz/pdfplumber/pypdf/pdfminer همه missing). **deferred** — نیازمندِ ابزارِ PDFِ offline، یا یک پاسِ جدا با Read-tool روی PDFهای استراتژیِ کوچکِ Mining (غیر-PII).
3. **DEEP-RAW-AUDIT §۳:** فایلِ مجزا پیدا نشد؛ نزدیک‌ترین `04 - Architect System/OCTOPUS-RECON-MAP.md`. جدولِ اولویت از خودِ پرامپت گرفته شد.
4. **commit:** طبق خط قرمز هیچ commit زده نشد — ۲۱ نوت + `ingest_raw.py` + این report همه uncommitted، منتظرِ verdict و commitِ مالک.

## پلِ School — «یادگیری از کلاس درسِ اختاپوس» (حلقهٔ بازِ بسته‌شده)

حلقهٔ باز: sensory_bus مشاهده‌ها را به topic_id (لیبلِ School) نگاشت می‌کرد ولی هیچ‌چیز آن‌ها را به
گرافِ curriculum (AwarenessField) تزریق نمی‌کرد → «کلاس درس» هرگز واقعاً یاد نمی‌گرفت. **`_ops/afferent/school_bridge.py`** این را بست:
- AfferentEventها → `AwarenessField.observe` → `tick` (ȧ=−L·a+input) → insightهای **propose-only**.
- **حافظه:** awareness در `_ops/state/school-awareness.json` persist می‌شود → یادگیری بین‌اجراها می‌ماند («بهتر یادش می‌ماند»).
- **اثباتِ end-to-end:** ۳۰ سیگنال یاد گرفته شد · mean_awareness 0.0→0.0417 · topicهای بازار **C02+E02 ignite** · insight: topic-ignited + co-activation (پیشنهادِ یال، human-gated).
- ایزوله: import فقط `curriculum`+`sensory_bus` (read-only)؛ صفر لمسِ organism/wiring/doctor/Project-F (لِینِ زندهٔ GLM).
- تست: `_ops/tests/test_school_bridge.py` → **۵/۵ سبز** (⚑ به run_all اضافه نشد چون GLM همین الان آن فایل را می‌سازد — بعد از تثبیت اضافه شود).

## فایل‌های تولیدشده (propose-only، uncommitted)

- `03 - Projects/Crypto - etoro/*-summary.md` (۱۵)
- `03 - Projects/Accounting/data/حساب کتاب/*-structure.md` (۶)
- `_ops/afferent/ingest_raw.py` (ingester) + `_ops/afferent/school_bridge.py` (پلِ School) + `_ops/tests/test_school_bridge.py`
- `_ops/state/school-awareness.json` (حافظهٔ awareness — runtime)
- همین report
