# genome-system

یک سیستمِ دانشِ شخصیِ **خودبهبود، امن، local-first** برای یک نفر روی یک لپ‌تاپ.
هستهٔ ایده: **هوشِ گران در نقاطِ تصمیمِ نادر؛ همه‌چیزِ روزمره ارزان و رویدادمحور** —
و مهم‌تر: سیستم هرگز نتواند معیارِ قضاوتِ خودش را دور بزند.

## چیدمان
```
genome-system/
├── genome/        هستهٔ تغییرناپذیر (read-only): values, gates, metrics, backup, change-protocol
├── ledger/        حافظهٔ رویداد append-only + hash-chain (ledger.py)
├── common/        config.py (لود ژنوم) · router.py (انتخاب tier مدل)
├── perception/    indexer.py (SQLite FTS5 + fallback) · watcher.py (رویدادمحور، بدون polling)
├── agents/        «ذهن» (role-prompt .md) + «بدن» (کد .py): guardian · creativity · doctor
├── docs/          master-prompt-5-phase · fact-check-report
├── tests/         smoke_test.py (ledger) · integration_test.py (کل خط لوله)
└── scripts/       lock_genome.sh
```
> در `agents/`، فایلِ **`.md` = شرح‌شغل/ذهنِ** ایجنت (پرامپتی که LLM با آن قضاوت
> می‌کند) و فایلِ **`.py` = بدن/سیستمِ‌عصبیِ** ایجنت (مکانیک، گیت‌ها، I/O، ایمنی که
> به‌شکلِ قطعی و غیرقابلِ‌دور‌زدن اجرا می‌شود).

## سه ایجنت
- **Guardian-Architect** — کنترل + آنلاین‌بودن (۲۴ساعته) + نظارتِ معماری. *governed-by*
  ژنوم و روی آن **read-only**؛ heartbeat، اجرای گیتِ بودجه، loop-guard، پاسبانِ ژنوم
  (اگر دستکاری شد → **halt**)، پاسبانِ بک‌اپ. هرگز ژنوم را عوض نمی‌کند.
- **Creativity Black-Box** — read-only روی کل پروژه، ایده‌های مرزِ دیوانگی/نبوغ با
  قالبِ اجباری {why_genius, why_insane, confidence, kill_criteria, smallest_test,
  reversible}. **propose-only** به دکتر؛ ایدهٔ بدونِ kill-criteria در همان مبدأ رد می‌شود.
- **Evolutionary Doctor** — گزارشِ سلامت + داوریِ propose-only + red-team علیه ژنوم
  (`distance_from_genome` باید صفر باشد)؛ هرگز APPLY نمی‌کند.

## اجرا
```bash
pip install -r requirements.txt        # watchdog + PyYAML (فاز ۱ به بعد)

python te