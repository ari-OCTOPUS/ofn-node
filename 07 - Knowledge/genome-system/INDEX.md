---
type: moc
status: archived
tags: [moc, genome-system, agent]
aliases: [genome-system, "سیستم ژنوم", "MAP - genome-system"]
updated: 2026-08-07
---

# genome-system — MAP (نقشهٔ canonical)

> **بازنشسته ۲۰۲۶-۰۷-۱۷ (فقط اپِ حلقه):** طبق `STATUS.json` — اپِ حلقهٔ خودبهبود
> (`run.py`/`research_loop.py`/ایجنت‌ها/زمان‌بندیِ ۳بار/روز) بازنشسته شد (صفر
> importer در `_ops`، بدون scheduled task)؛ بخشِ «عملیات» زیر دیگر معتبر نیست.
> `ledger/ledger.jsonl` زنده می‌ماند — مصرف‌شونده توسط `_ops/budget/opslib.genome_ledger()`.

> سیستمِ دانشِ خودبهبودِ امنِ **local-first**. هوشِ گران در نقاطِ تصمیمِ نادر؛
> همه‌چیزِ روزمره ارزان و رویدادمحور؛ و سیستم هرگز نمی‌تواند معیارِ قضاوتِ خودش را
> دور بزند.
>
> **برای ایجنت‌های دیگر:** این سیستم **propose-only** است — قبل از هر تعامل
> [[07 - Knowledge/genome-system/HANDOFF|HANDOFF]] را بخوان.

## شروع از این‌جا
- [[07 - Knowledge/genome-system/README|README]] — نمای کلی + دستورهای اجرا
- [[07 - Knowledge/genome-system/HANDOFF|HANDOFF]] — قواعد برای ایجنت‌های دیگر (الزامی)
- [[07 - Knowledge/genome-system/CHANGELOG|CHANGELOG]] — تاریخچهٔ نسخه‌ها
- `STATUS.json` — وضعیت ماشین‌خوان (برای ایجنت‌ها)

## سند طراحی
- [[07 - Knowledge/genome-system/docs/master-prompt-5-phase|پرامپت پنج‌گانهٔ مرحله‌ای]] — نقشهٔ ساخت (فاز ۰–۴)
- [[07 - Knowledge/genome-system/docs/fact-check-report|گزارش راستی‌آزمایی]] — صحتِ ادعاهای پشتِ طراحی

## ایجنت‌ها (نقش = «ذهن») — همه propose-only
- [[07 - Knowledge/genome-system/agents/guardian-architect|Guardian-Architect]] — کنترل/آنلاین/۲۴ساعته · read-only روی ژنوم · halt
- [[07 - Knowledge/genome-system/agents/creativity-blackbox|Creativity Black-Box]] — ایده‌های مرزِ دیوانگی/نبوغ · read-only کل پروژه
- [[07 - Knowledge/genome-system/agents/evolutionary-doctor|Evolutionary Doctor]] — سلامتِ هفتگی + داوری + red-team

## ژنوم (هستهٔ تغییرناپذیر — READ-ONLY)
- [[07 - Knowledge/genome-system/genome/README|genome/README]] — منطق و قفل
- [[07 - Knowledge/genome-system/genome/genome_change_protocol|پروتکل تغییر ژنوم]] — ۷۲h + دو-کلید
- `genome/values.yaml` · `genome/gates.yaml` · `genome/metrics.yaml` · `genome/backup.yaml`

## کد (بدنه = «مکانیک»)
- `ledger/ledger.py` — حافظهٔ append-only + hash-chain (concurrency-safe)
- `perception/indexer.py` · `perception/watcher.py` — ادراکِ رویدادمحور (بدون polling)
- `agents/guardian.py` · `agents/creativity.py` · `agents/doctor.py` — harnessِ ایجنت‌ها
- `common/llm.py` · `common/router.py` · `common/config.py` — مغز + مسیریاب + ژنوم‌لودر
- `run.py` — یک چرخه (loop/full) · `research_loop.py` — حلقهٔ تحقیقِ زمان‌دار
- `scripts/backup.py` · `scripts/install_schedule.ps1` · `scripts/crontab.txt`
- `tests/` — smoke · integration · llm · review · leak_guard

## عملیات
- اجرا: `python run.py loop` (ارزان، چندبار/روز) یا `full` (هفتگی، با دکتر)
- تحقیق: `python research_loop.py "سوال" --minutes 60 --max-cost 1.0`
- بک‌آپ: `python scripts/backup.py` (۳-۲-۱ → `../_backups/`)
- زمان‌بندی: Cowork task «genome-loop» ۳بار/روز (۹/۱۵/۲۱) — plan-gated
- پلن: [[07 - Knowledge/genome-system/plan.yaml|plan.yaml]] — تا تمام‌نشدن می‌چرخد، بعد idle

## وضعیت
v0.4.3 — فاز ۰–۴ ساخته و تست‌شده · مغز LLM وصل · ۷ ایرادِ ایمنی v0.4.0 + گارد نشت
دوطرفهٔ کلید (v0.4.1/v0.4.3) + فیکس race قفل ledger (v0.4.2) · هر ۵ سوئیت تست سبز.
جزئیات در [[07 - Knowledge/genome-system/CHANGELOG|CHANGELOG]] و `STATUS.json`.
