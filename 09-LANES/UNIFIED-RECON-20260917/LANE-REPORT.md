# LANE-REPORT — UNIFIED-RECON-20260917
GOV_VERSION=V8 · LADDER=L2 · LANE=UNIFIED-RECON-20260917 · mode READ_ONLY_FIRST

## چه شد (what was done)
1. **Preflight ریموت verify شد**: ۱۶۴/۳/۳/۴ شاخه (ls-remote)، HEADهای هر چهار repo byte-exact، چهار PR ممیزی merged=true (با GET؛ لیست merged=null برمی‌گرداند — تله). اختلاف ۱۶۹/۱۶۴ = صفحه‌بندی. **۲ فایل از ۴ deliverable اعلامی ایجنت ریموت (REPO-INVENTORY.csv و BRANCH-LEDGER.csv) هرگز وجود نداشتند** — این lane هر دو را ساخت.
2. **فاز یک کامل**: شمارش پنجره (۲۳۲ commit یکتای ofn-node، صفر روی main؛ Armin=۲، langar=۲، vbaa=۰)، ruleset جزئی (فقط main؛ ۴ قاعده)، workflows تفکیک authored/dynamic، tags/releases، ۲ alert باز telegram_bot_token.
3. **فاز دو**: SYSTEM-GRAPH/MAP، CANONICAL-BODY-REGISTRY، INTERFACE-MATRIX، SUPERSESSION-LEDGER. کشف‌ها: ۱۲ نسخهٔ CURRENT-TRUTH (۱ canonical + ۱ auto + ۱ نامعلوم + ۹ استاب)، بدنهٔ موازی repo↔vault (۱۸۷ مسیر: ۱۸۰ غایب، ۷ متفاوت)، GAP قرارداد انتقال vbaa.
4. **فاز سه (تست، کلون‌های ایزوله)**: ofn-node@dba9971 → 9664P/6F(همان ۶ pre-existing)/28S/8192sub، 211s؛ langar → 13+22 مستقیم سبز، pytest COLLECTION_FAILURE؛ vbaa → 23P+1xf+2xp؛ Armin → TESTS_ABSENT.
5. **runtime 138 فقط‌خواندنی**: langar غایب (unit+service)، engine نقاشی حاضر، WAL زنده ۰ بایت، ۱۱+ timer فعال.
6. **فاز چهار (census)**: walk کامل F:\backup با hash/manifest/link-graph/dup/orphan/collision/sensitive(نام-فقط) + اسکن .obsidian کل درایو F. اعداد: `census/CENSUS-SUMMARY.json`.
7. **فاز پنج (wave-1 فقط افزاینده)**: ۱۳ فایل overlay جدید (00-HOME، ۳ MOC ریپو+۱، ۳ MOC پای، 90-MIRRORS). **هیچ move/rename/edit؛ CURRENT-TRUTH سوم ساخته نشد** (به‌جایش CURRENT-TRUTH-INDEX.md پوینتر).

## چه ماند (what remains)
- G1..G7 مهاجرت بسته‌اند (snapshot کامل نیازمند توقف sync مالک؛ dry-run/rollback/link-rewrite تمرین‌ها اجرا نشدند — عمداً، پشت گیت).
- بازبینی runtime 180/182؛ re-measure خط P1 synthesizer در langar؛ CI تازه روی headهای PR فانل؛ resolve تناقض AUTO1.
- VAULT-CENSUS.jsonl و MANIFEST و LINK-GRAPH کامل در `F:\recon-clones-20260917\census-out\` نگه داشته شدند (داخل والت کپی نشدند تا baseline census تمیز بماند — مسیرشان در NOTE.txt ثبت است).

## چه شکست (what failed)
- اولین اجرای census با ValueError (فایل روی mount \\.\NUL) مرد → اصلاح try/except، اجرای دوم موفق.
- دو فایل اعلامی ایجنت ریموت موجود نبود (بالا).
- ls-remote/fetch کند (دیسک F کند ~۴.۵MB/s هش) → census زمان‌بر شد ولی کامل شد.

## شواهد (evidence paths)
همه در `09-LANES/UNIFIED-RECON-20260917/`: پنج ledger/matrix فاز ۱، پنج آرتیفکت فاز ۲، کارت‌های تصمیم، طرح مهاجرت، گزارش اصلی، پوشهٔ census/. کلون‌ها و لاگ‌ها: `F:\recon-clones-20260917\` (pytest-ofn-main.log، window-commits-*.tsv، census-out/).

## rollback
همهٔ اثرات این lane **افزاینده** است: پوشهٔ `09-LANES/UNIFIED-RECON-20260917/` + ۱۳ فایل overlay در ۵ پوشهٔ جدید. بازگشت = حذف همان‌ها (یا revert کامیت لوکال). هیچ فایل موجودی تغییری نخورد (گزارش git status در RECON-REPORT). `F:\recon-clones-20260917\` خارج از والت است و حذفش بی‌اثر به والت.

## وضعیت گیت‌ها
G0=PARTIAL→DONE(census کامل) · G1..G7=PENDING · REMOTE_MUTATIONS=0 · DELETE=0 · OVERWRITE=0
