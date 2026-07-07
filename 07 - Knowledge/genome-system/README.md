---
type: reference
status: active
tags: [genome-system, readme]
aliases: ["README - genome-system"]
updated: 2026-07-06
---

# genome-system

> نقشهٔ canonical: [[07 - Knowledge/genome-system/INDEX|INDEX]] · قواعدِ ایجنت‌ها: [[07 - Knowledge/genome-system/HANDOFF|HANDOFF]] · تاریخچه: [[07 - Knowledge/genome-system/CHANGELOG|CHANGELOG]]

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

python tests/smoke_test.py             # تستِ ledger
python tests/integration_test.py       # کلِ خط لوله (perception→creativity→doctor + guardian)
python tests/llm_test.py               # تستِ «مغز» (LLM) آفلاین با fake transport

# یک چرخهٔ کامل — مغز وصل اگر کلید باشد، وگرنه stubِ آفلاین:
ANTHROPIC_API_KEY=sk-...  python run.py <vault>

# راه‌اندازی جزء‌به‌جزء:
python perception/watcher.py <vault> index.db ledger/ledger.jsonl --once   # backfill
python perception/watcher.py <vault> index.db ledger/ledger.jsonl          # live (watchdog)
python agents/guardian.py genome ledger/ledger.jsonl                        # یک tick گاردین
python agents/creativity.py ledger/ledger.jsonl                            # یک PROPOSAL
python agents/doctor.py genome ledger/ledger.jsonl                         # گزارشِ سلامت
bash scripts/lock_genome.sh                                                 # قفلِ read-only ژنوم
```
> **توجه:** `creativity.py` یک `llm_fn` تزریق‌پذیر دارد؛ به‌صورت پیش‌فرض یک stubِ
> آفلاین اجرا می‌شود تا کلِ خط لوله بدونِ کلیدِ API کار کند. برای ایده‌های واقعی،
> یک تابعِ فراخوانِ LLM (tier پیش‌فرض = Sonnet) جای stub بگذار.

## وضعیت
فاز ۰–۴ **کدشده و تست‌شده** و **مغز (LLM) وصل** است:
perception، guardian (halt-on-tamper + loop-guard)، creativity (propose-only +
قراردادِ فروتنی)، doctor (propose-only)، ledger hash-chain، و کلاینتِ LLM با
routerِ tier + کنترلِ هزینه — همه سبز در `smoke_test`, `integration_test`,
`llm_test`. فراخوانِ واقعیِ API از طریق `common/llm.py` آماده است (کلید از
`ANTHROPIC_API_KEY`؛ هیچ کلیدی در کد نیست).

گامِ بعدی: زمان‌بندیِ حلقهٔ هفتگیِ دکتر، بک‌اپِ off-site (restic/rclone)، و
اجرای واقعی با کلید.

> نقشهٔ کاملِ ساخت: `docs/master-prompt-5-phase.md` · راستی‌آزمایی: `docs/fact-check-report.md`
