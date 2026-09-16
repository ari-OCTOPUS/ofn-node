# PREFLIGHT FINDINGS — 2026-08-21 (integrity defect + repair)

سند یافتههای اجرای پیش-تأیید بستهٔ verifier در هدهای d301339 و cc267048.
این سند را جلسهٔ پیادهساز نوشته؛ verifier مستقل باید همه را مستقل بازتولید کند.

## یافتهٔ ۱ — ادعای «۱۶۳/۱۶۳ exact-HEAD» در d301339 بازتولیدپذیر نیست

- اجرای پیش-تأیید در worktree دقیقِ d301339 (درخت commitشدهٔ خالص):
  **۱۶۲/۱۶۳** — فقط `closed-loop` شکست: **۱۴/۱۵** (exit=1).
  شکست: `test_free_text_hears_brains_without_model` — «A5 receipts must exist
  for free-text» (مسیر exception در `telegram_adapter._hear_brains` → خروجی
  fallback با `a5_receipts: []`).
- ریشه: `_ops/organs/__init__.py`، `_ops/organs/flags.py` و
  `_ops/organs/cognition_inbox.py` **در هیچ commitای از این شاخه نیستند**
  (untracked؛ فقط در درخت زنده وجود دارند؛ روی شاخهٔ `agent_C` در b936a0f
  commit شدهاند). ولی `telegram_adapter.py` و `test_telegram_closed_loop_20260820.py`
  (هر دو commitشده) همین ماژولها را import میکنند.
- نتیجه: شواهد قبلی (receiptهای `SECURITY-TEST-RECEIPTS.jsonl` با ادعای
  exact-HEAD) از اجرا در **درخت زنده** به دست آمده که این فایلهای untracked
  را داشت؛ بنابراین «exact-HEAD» بودن آن بازتولیدپذیر نیست — یک نقص
  یکپارچگی شواهد است، نه «سبز با rerun».

## یافتهٔ ۲ — side effect اجرای محلی صفر بود

- در هر دو اجرا (d301339 و cc267048)، هش قبل/بعد حافظه
  (`research-ingest.jsonl`، `self-loop-ingest.jsonl`)، مینیاپ و سندلاگ
  بایتی یکسان بود؛ delta سندلاگ صفر؛ `production_path_delta: []`.
- `send_log` بین دو اجرا تغییر کرد (۰۸۵f… → ad3f…) ولی **درون پنجرهٔ اجرای
  اختصاصی نه** — drift پیشینهٔ ارگانیسم زنده، طبق همان طبقهبندی قبلی
  (live-background)، نه اثر فیکسچرها.

## تعمیر (شاخهٔ جدا، حداقلی — طبق پروتکل مگاپرامپت ۱)

- شاخه: `repair/organs-suite-reproducible-20260821`
- commit: `cc267048075b0f64bd56c8ac59074d8a43233ae2` (فرزندِ d301339)
- محتوا: دقیقاً همان سه فایلِ درخت زنده که شواهد قبلی عملاً با آنها اجرا شده
  (`_ops/organs/__init__.py`، `flags.py`، `cognition_inbox.py`)؛ بدون هیچ
  تغییر رفتاری. WIRING.json محتوایی تفاوت ندارد (فقط EOL).
- پیش-تأیید در cc267048: **۱۶۳/۱۶۳ سبز**، `all_pass: true`،
  `production_path_delta: []`، side effect اجرای محلی صفر.
- رأی preflight: `confirmed=true`، `verifier_independent=false` →
  terminal_state همچنان `IMPLEMENTATION_COMPLETE_VERIFICATION_PENDING`.

## وضعیت و گیت بعدی

- ادعای قبلی («۱۶۳/۱۶۳ در d301339») **باطل/غیرقابل بازتولید** ثبت میشود.
- هدِ اعلامشدهٔ بعدی (declared descendant) برای verification مستقل:
  **cc267048** (یا فرزند بعدیِ دارای شواهد).
- نکته: در حین همین جلسه، شاخهٔ اصلی توسط ارگانیسم زنده به
  `f314cb0` (اصلاحات bounded I/O برای hangهای زنده) جلو رفت؛ cc267048 همچنان
  فرزندِ d301339 و هدِ پایدارِ اعلامشده است؛ هنگام merge می‌توان organs-commit
  را روی هدِ جدید rebase کرد و شواهد را در هدِ نهایی بازتولید نمود.
- گیت بعدی مطابق فرمان مالک: اجرای **مگاپرامپت ۱** توسط یک جلسهٔ واقعاً جدا
  با هویت مستقل؛ PASS مستقل در cc267048 می‌تواند `WAVE1_CANARY_READY` را مجاز
  کند؛ هیچ ارسال زنده‌ای بدون آن.
- هیچ چیز در این بسته جعل یا بازنویسی نشده؛ همهٔ خروجیها append-only در همین پوشه.
