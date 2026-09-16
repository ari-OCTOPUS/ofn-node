# ۰۴ — مدلِ دادهٔ مشترک

همهٔ ستون‌ها روی **یک** مجموعهٔ ساختار می‌نشینند (نه ساختارهای موازیِ رقیب). همه محلی،
stdlib، fail-soft، و از دیدِ بیرونی فقط‌خواندنی‌اند. PII هرگز به هیچ promptِ LLM نمی‌رود.

## ۱) `ziman_self.v1` — مدلِ خود
تکی، در `state/cortex/ziman-self-model.json`. چهار بخش: identity/objective/standing/gap_vector
+ `truth_tiers`. طرحِ کامل: [01-SELF-MODEL](01-SELF-MODEL.md). خوانندهٔ اصلیِ ماتریس.

## ۲) `candidate.v1` — نامزدِ اکشن (واحد)
هر چیزی که ماتریس امتیاز می‌دهد، همین شکل را دارد (پیشنهادِ CAC، کمپینِ بازاریابی، ایدهٔ بازار،
خانه‌داری همه اینجا یکی می‌شوند):
```
candidate.v1 = { id, kind, source_pillar, subject_ref (non-PII), payload_draft,
                 signals{goal_fit,impact,readiness,novelty,cost,risk_penalty},
                 hard_flags[], truth_flags[], priority, reasons[], rank, vetoed_by|null }
```

## ۳) `ziman_matrix.v1` — خروجیِ امتیازدهی
خروجیِ هر ضربان: `candidates[]` با بردارِ کاملِ سیگنال + `top` + `surfaced` + `damping` +
`propose_only:true`. داخلِ `ziman.beat.v1` می‌رود و به `/status` ترجمه می‌شود.

## ۴) `steering.json` — حالتِ هدایتِ مالک
`state/ziman/steering.json = {focus, paused, boosts[], mutes[], updated_iso, source}`.
**فقط** با تپ‌های تلگرامِ مالک یا ویرایشِ `GOALS-ZIMAN.md` نوشته می‌شود. برای کدِ امتیازدهی
فقط‌خواندنی است. یک تپ = ورودیِ مالک (نه approve توسطِ ایجنت).

## ۵) `lead.v1` — CRMِ محلی (قیف)
`data/leads.jsonl` (append-only، gitignored، PII محلی می‌ماند). قیف: `cold → warm →
proposed → won`. فیلدها: `{id, display_ref (برچسبِ غیر-PII، تنها چیزی که ممکن است به دایجست
برسد), stage, consent, occasion_tags[], last_touch_beat, notes_local}`. شمارشِ قیف واردِ
مدلِ خود می‌شود؛ خودِ PII هرگز به دایجست/prompt نمی‌رود (گاردِ کد + تست).

## ۶) `occasion.v1` — تقویمِ مناسبت (مالک‌ویرایش)
`occasions.yaml`: مناسبت‌های فرهنگیِ ثابت (یلدا، نوروز) و شخصیِ تکرارشونده (تولد، سالگرد) با
پنجرهٔ `lead_days` و تمِ محصول. رانِ `readiness/impact` در ماتریس برای کمپینِ به‌موقع.

## ۷) `pattern_card.v1` + `benchmark.v1` — هوشِ بازارِ اخلاقی
`state/pulse/ziman-market-latest.json`. الگوهای **عمومیِ انتزاع‌شده به بیانِ خودِ ربات**
(نه کپی): برای «قابلِ‌اقدام» بودن حداقل K شاهد لازم است، و هیچ نقلِ مستقیمِ بلند مجاز نیست
(سقفِ نقل بسیار کوتاه، ترجیحاً بدونِ نقل). خروجی = ایدهٔ پیشنهادی برای مالک، نه محتوای کپی‌شده.
جزئیاتِ اخلاقی: [06-GOVERNANCE-AND-SAFETY](06-GOVERNANCE-AND-SAFETY.md).

## ۸) `feedback_event.v1` — حلقهٔ یادگیری
`marketing_feedback.jsonl` (append-only، بدونِ PII). رویدادهای approve/edit/send/reject مالک
+ yes/noِ ماتریس → وزنِ هر قالب/کانال و افتِ novelty. یعنی ربات یاد می‌گیرد مالک چه draftی را
تأیید/رد می‌کند و دفعهٔ بعد بهترش را بالا می‌آورد.

## ۹) `evt.v1 sale:confirmed` — ستارهٔ شمالیِ فروشِ واقعی
تنها منبعِ `real_sales`. در همان دفترِ hash-chainِ control-brain نوشته می‌شود، به **دو** روشِ
مالک‌محور که هر دو به یک رویداد می‌رسند: (الف) فرمانِ `/sale`ِ مالک، یا (ب) شغلِ `reconcile.py`
که CSVِ پرداخت را تطبیق می‌دهد. **هرگز** یک ایجنت این را نمی‌نویسد (تست تضمین می‌کند).

## ۱۰) `outcomes.jsonl` — دفترِ نیّتِ حلقه‌بسته
موجود (`state/cortex`، از `cortex/goal_directed`). هر پیشنهادِ نمایش‌داده‌شده می‌گوید کدام
directive/gap را خدمت کرد، pending تا سنجش. هدایت را صادق و غیرِ دوری نگه می‌دارد.

## اصولِ مشترکِ همهٔ داده‌ها
- **افزایشی**: کلیدها/فایل‌های جدید؛ چیزی از قبل بازنویسی نمی‌شود.
- **fail-soft**: فایلِ نبود/خراب → خالی، نه کرش.
- **truth-tier**: هر عدد برچسبِ صداقت دارد؛ داده نبود → UNKNOWN، نه حدس.
- **PII محلی**: هرگز در git، دایجست، یا promptِ ابری.
