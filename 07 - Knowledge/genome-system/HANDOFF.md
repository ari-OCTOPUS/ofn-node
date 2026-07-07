---
type: handoff
status: active
tags: [handoff, genome-system, propose-only, agent-contract]
epistemic_status: canonical
updated: 2026-07-07
---

# HANDOFF — genome-system (برای ایجنت‌های دیگر)

> اگر ایجنتی هستی که این vault را می‌خوانی یا می‌نویسی، این نوت **قرارداد** است.
> نقشهٔ کامل: [[07 - Knowledge/genome-system/INDEX|INDEX]] · وضعیتِ ماشین‌خوان: `STATUS.json`.

## این چیست؟
یک سیستمِ دانشِ خودبهبودِ **امن** در `07 - Knowledge/genome-system`. سه ایجنت
(Guardian، Creativity، Doctor) + حافظهٔ append-only با hash-chain (ledger) + هستهٔ
تغییرناپذیر (genome). فلسفه: هوشِ گران در نقاطِ تصمیمِ نادر؛ همه‌چیزِ روزمره ارزان و
رویدادمحور؛ سیستم هرگز نمی‌تواند معیارِ قضاوتِ خودش را دور بزند.

## قواعدِ الزامی (رعایت کن)
1. **propose-only.** هیچ ایجنتی `APPLY` نمی‌کند — فقط پیشنهاد. تصمیمِ نهایی با مالک (ari).
2. **`genome/` فقط-خواندنی است.** هرگز فایلی در `genome/` را تغییر نده. تغییرِ ژنوم
   فقط از مسیرِ [[07 - Knowledge/genome-system/genome/genome_change_protocol|پروتکل ۷۲ساعتهٔ دو-کلیدی]].
3. **ارزیاب/متریک‌ها در ژنوم فریزند** — دور نزن (درسِ DGM: reward hacking).
4. **بودجه** در `genome/gates.yaml` — هرگز override نکن؛ Guardian روی نقض **halt** می‌کند.
5. **`plan.yaml` را احترام بگذار** — اگر تمام شد، حلقه idle می‌شود (پول نسوزان).
6. **perception فقط allowlist** — چیزی خارج از فهرستِ مصوبِ مالک index نکن (privacy).

## چطور پیشنهاد بدهی
یک رویدادِ `PROPOSAL` به `ledger/ledger.jsonl` اضافه کن (actor = نامِ تو، `to=doctor`)، با فیلدهای:
`idea` · `why_it_might_be_genius` · `why_it_might_be_insane` · `confidence` (۰..۱) ·
`kill_criteria` · `smallest_test` · `reversible`.
دکتر آن را در برابرِ ژنوم red-team می‌کند (`distance_from_genome` باید صفر باشد) و به گیتِ مالک می‌برد.
ایدهٔ بدونِ `kill_criteria` در همان مبدأ رد می‌شود.

## وضعیت فعلی (۲۰۲۶-۰۷-۰۷ · v0.4.3)
- فاز ۰–۴ ساخته و تست‌شده؛ مغزِ LLM وصل؛ **۷ ایرادِ ایمنی v0.4.0 + گارد نشت دوطرفهٔ کلید (v0.4.1/v0.4.3) + فیکس race قفل append ledger (v0.4.2)** (رجوع: [[07 - Knowledge/genome-system/CHANGELOG|CHANGELOG]]).
- همهٔ تست‌ها سبز: `smoke` · `integration` · `llm` · `review` · `leak_guard` (۵ سوئیت).
- زمان‌بندی فعال: Cowork «genome-loop» ۳بار/روز، plan-gated.
- **باز:** بک‌آپِ off-site (copy #3)، اجرا با کلیدِ واقعی، `owner_confirmed: true` در `gates.yaml`.

## نقاط تماس (entrypoints)
`python run.py loop|full` · `python research_loop.py "..." --minutes 60 --max-cost 1.0` · `python scripts/backup.py`

> epistemic_status: این نوت canonical است. اگر رفتارِ کد با این قرارداد فرق داشت،
> کد مرجع است و این نوت باید (propose-only) اصلاح شود.
