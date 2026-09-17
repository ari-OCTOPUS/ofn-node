# CROSS-REPO-INTERFACE-MATRIX — OCTOPUS unified recon 2026-09-17

هر ردیف یک جفت است؛ «interface» فقط با شاهد کد/فایل/runtime اثبات می‌شود، نه با نام یا نیت.
وضعیت‌ها: `WIRED` (کد فعال)، `DOC_ONLY` (فقط سند)، `NONE_FOUND` (جستجو شد، چیزی نبود)، `GAP` (قرارداد لازم وجود ندارد)، `UNKNOWN`.

| از | به | interface ادعا شده | وضعیت | شاهد (همین نشست) |
|---|---|---|---|---|
| Armin | ofn-node | سند→runtime نقاشی | `DOC_ONLY` | SCAN.md (merge 4193de1): engine در ofn-node/138 است؛ هیچ کد/interface در Armin نیست (۵ فایل، همه سند) |
| ofn-node (packs/lead.yaml, web/lead.html) | board138 runtime | deploy موتور لید نقاشی | `WIRED` | tree روی main + فایل‌های زندهٔ همسان روی 138 (ls، mtime Sep 2) |
| ofn-node (octopus-*) | board138 | fleet زنده | `WIRED` | ۱۱+ timer فعال، LAST/PASSED در دقیقه‌های اخیر (ssh فقط‌خواندنی 23:47Z) |
| langar | ofn-node | هیچ | `NONE_FOUND` | صفر import متقابل (grep دو طرف)؛ صفر ارجاع langar روی main |
| langar (langar_bot.service) | hosts 138/180/182 | deploy سرویس | `NONE_FOUND on 138 (live)` / `UNKNOWN 180,182` | فایل service در repo track شده ولی روی 138 نصب نیست؛ ممیزی 08-27 برای هر سه می‌گوید نبود |
| langar-pro synthesizer | langar/researcher | call signature | `DOC claim P1 bug — re-measure نه‌شده` | def در synthesizer.py:21 و caller در researcher.py:61 موجود؛ اختلاف امضا در متن ممیزی merge شده ثبت شده، این نشست دوباره اندازه‌گیری نشد |
| vbaa-patches (_ops/vbaa/*) | ofn-node | adoption سه primitive امنیتی | `NONE_FOUND` + `GAP` | 0 مسیر `_ops/vbaa` روی main؛ فقط یک ذکر doc در deep-scan؛ قرارداد انتقال وجود ندارد |
| vault (F:\backup) | ofn-node | آینهٔ ساختار | `PARALLEL_DIVERGENT` | 187 مسیر: 180 غایب در والت، 7 موجود همگی متفاوت (mirror-comparison.csv) |
| vault stubs | canonical CURRENT-TRUTH | pointer | `WIRED` (استاب‌ها) | 9 استاب 360B مسیر canonical را نام می‌برند (D-34/MIRROR-01 owner GO) |
| OCTOPUS/CURRENT-TRUTH.md | canonical CURRENT-TRUTH | سطح خودنویس | `AUTO_SURFACE` | frontmatter octopus-auto + timestamp خودکار |
| owner → repos | — | کانال حاکمیتی | `DOC_ONLY→GOV` | AGENTS.md: مسیر TG تحت GOV-V7/V8 با رسید |

## قراردادهای غایب (GAP — ساخته نشدند، فقط ثبت شدند)
1. **vault → vbaa-patches → ofn-node artifact transfer**: هیچ قرارداد provenance/test/adoption-receiptای بین سه بدنه وجود ندارد.
2. **CRM writer ↔ call_log table**: #261 جدول می‌سازد بدون writer؛ #248 writer دارد بدون جدول؛ PR سومِ اتصال وجود ندارد.
3. **duplication policy بین بدنهٔ موازی repo و vault**: ۷ فایل same-path متفاوت بدون قاعدهٔ canonical.
