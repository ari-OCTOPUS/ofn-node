---
type: log
status: active
tags: [changelog, genome-system]
aliases: ["CHANGELOG - genome-system"]
updated: 2026-07-07
---

# CHANGELOG — genome-system

همهٔ نسخه‌ها **propose-only** ساخته و تست شده‌اند. تاریخ: ۲۰۲۶-۰۷-۰۶.
نقشه: [[07 - Knowledge/genome-system/INDEX|INDEX]] · قواعدِ ایجنت‌ها: [[07 - Knowledge/genome-system/HANDOFF|HANDOFF]].

## v0.4.3 — گارد نشت کلید دوطرفه شد در `common/llm.py` (2026-07-07)
- **گپ (کشف بازبینی چندایجنتی):** گارد v0.4.1 فقط جهتِ «کلید غیرآنتروپیک → api.anthropic.com» را می‌بست و با substring چک می‌کرد؛ کلید واقعی `sk-ant-` می‌توانست به هر هاست دیگری (typo در `ANTHROPIC_BASE_URL`) ارسال شود.
- **فیکس:** چک روی hostname واقعی (`urllib.parse.urlsplit`) + جهت معکوس: کلید `sk-ant-*` به هر endpoint غیرآنتروپیک → `RuntimeError` پیش از I/O؛ کلید هرگز echo نمی‌شود. مسیر عمدی DeepSeek (کلید غیر sk-ant به هاست deepseek) دست‌نخورده.
- تست: چک چهارم در `tests/leak_guard_test.py` — ۴/۴ آفلاین سبز.

## v0.4.2 — فیکس race واقعی قفل append در `ledger/ledger.py` (2026-07-07)
- **ریشه:** قفل فایلی O_EXCL بعد از ۳ ثانیه timeout «بی‌قفل ادامه می‌داد»؛ زیر چند تردِ هم‌پروسه (watcher زنده + indexer) که هر append یک fsync دارد، یک ترد timeout می‌کرد، بی‌قفل می‌نوشت و زنجیرهٔ hash فورک می‌شد. ادعای کامنت قدیمی («disk re-read نجات می‌دهد») برای دو نویسندهٔ *هم‌زمان* غلط بود — هر دو همان tail را می‌خوانند.
- **علامت:** `review_test.py` فلیکی (~۱/۳ اجراها: `chain break: prev mismatch`) — کشف جلسهٔ ۲۲.
- **فیکس:** قفل دولایه — لایهٔ ۱: `threading.Lock` سراسری per-path (تردهای یک پروسه قطعی سریالیزه؛ هرگز timeout ندارد) + لایهٔ ۲: همان سایدکار O_EXCL برای بین-پروسه (timeout ۳→۱۰s؛ رفتار never-hang حفظ شد).
- **راستی‌آزمایی:** ۱۲ اجرای پیاپی `review_test.py` = ۱۲/۱۲ سبز (قبلاً ~۱/۳ شکست)؛ هر ۵ فایل تست ژنوم سبز.

## v0.4.1 — فیکس نشت کلید در `common/llm.py` (2026-07-06)
- **تلهٔ نشت بسته شد:** `API_URL` دیگر هاردکد نیست — از `ANTHROPIC_BASE_URL` (با fallback به api.anthropic.com) ساخته می‌شود. در این vault متغیر `ANTHROPIC_API_KEY` جای دیگر عمداً حامل کلید DeepSeek است؛ نسخهٔ قبلی آن کلید را به api.anthropic.com می‌فرستاد.
- **گارد نشت در `_real_transport`:** اگر مقصد api.anthropic.com باشد و کلید با `sk-ant-` شروع نشود → `RuntimeError` پیش از هر I/O شبکه؛ کلید هرگز echo نمی‌شود.
- تست additive: `tests/leak_guard_test.py` (۳ چک، آفلاین). هر ۴ تست قبلی سوئیت هم سبز ماندند.

## v0.4.0 — بازنگری و رفع ایراد (Review & hardening)
هفت ایرادِ واقعی رفع شد (چند تا «قابلیتِ ایمنیِ ادعاشده ولی مرده»):

1. **ledger زیر همزمانی می‌شکست** (watcher زنده + scheduler + backup) → قفلِ append + خواندنِ hashِ آخر از دیسک.
2. **خطِ نیمه‌نوشته** (کرشِ وسطِ نوشتن) readerها را می‌ترکاند → `iter_events` تحمل‌پذیر.
3. **گیتِ بودجهٔ گاردین مرده بود** (هیچ‌کس `daily_cost_usd` نمی‌نوشت) → جمعِ واقعیِ `llm_cost_usd` امروز.
4. **هشدار کهنگیِ بک‌آپ ثابتِ ۰ بود** → سنِ واقعی از timestampِ آخرین بک‌آپ.
5. **گاردین در حلقه tamper را نمی‌گرفت** (هر دور instanceٔ نو) → یک instanceٔ ثابت (baseline سرِ شروع).
6. **indexer در watcher زنده کرش می‌کرد** (sqlite در threadِ واچ‌داگ) → `check_same_thread=False` + lock.
7. **دکتر گزارش‌های خودش را دوباره داوری می‌کرد** → فیلترِ propose-onlyها.

به‌علاوه: `run.py` و `research_loop.py` حالا **resilient** (خطای API/JSON دیگر چرخه/حلقه را نمی‌کُشد).
تست: `tests/review_test.py` (۷/۷ سبز). همهٔ سوئیت‌ها سبز.

## v0.3.0 — مغز + عملیات
- **مغز LLM وصل شد:** `common/llm.py` + router (Haiku / Sonnet 5 / Opus 4.8) + کنترلِ هزینه (metered + cap).
- `run.py` — چرخهٔ `loop`/`full`، **plan-gated** (تا تمام‌نشدنِ `plan.yaml` می‌چرخد، بعد idle).
- **زمان‌بندی:** Cowork task «genome-loop» ۳بار/روز (۹/۱۵/۲۱) + `scripts/install_schedule.ps1` + `scripts/crontab.txt`.
- **بک‌آپ ۳-۲-۱:** `scripts/backup.py` (اولین بک‌آپ گرفته شد → `../_backups/`).
- **`research_loop.py`:** حلقهٔ تحقیقِ زمان‌دار — هر دور research→conclude→report→next-prompt، با ساعتِ واقعی تا ۱ ساعت، budget cap + guardian gate.

## v0.2.0 — ادراک + ایجنت‌ها
- **perception:** `indexer.py` (SQLite FTS5، incremental) + `watcher.py` (رویدادمحور، بدون polling).
- **سه ایجنت** (harness `.py` + role-prompt `.md`): [[07 - Knowledge/genome-system/agents/guardian-architect|Guardian]] · [[07 - Knowledge/genome-system/agents/creativity-blackbox|Creativity]] · [[07 - Knowledge/genome-system/agents/evolutionary-doctor|Doctor]].
- `tests/integration_test.py` — کلِ خط‌لوله سبز.

## v0.1.0 — بنیان + راستی‌آزمایی
- `genome/` (values, gates, metrics, backup, change-protocol) — **read-only**.
- `ledger/ledger.py` (append-only + hash-chain) + `tests/smoke_test.py`.
- [[07 - Knowledge/genome-system/docs/fact-check-report|گزارش راستی‌آزمایی]] — ادعاهای پشتِ طراحی چندمنبعی verify شد (۲ اصلاح، ۱ نیمه‌تأیید).
- [[07 - Knowledge/genome-system/docs/master-prompt-5-phase|پرامپت پنج‌گانهٔ مرحله‌ای]] — نقشهٔ ساخت.
