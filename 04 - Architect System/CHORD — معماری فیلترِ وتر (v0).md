---
type: architecture
status: active
tags: [octopus, chord, doctor, self-healing, math, safety]
updated: 2026-07-18
parent: "[[OCTOPUS-OS — استراتژی یکپارچه (تلگرام‌محور)]]"
related: "[[ANALYSES/2026-07-18_CHORD-DISCOVERY]]"
---

# CHORD — فیلترِ وترِ ریاضی برای دکترِ تکاملی و خودترمیمی (v0)

> **یک جمله:** هر تعمیر/تغییری قبل از پیشنهاد باید از یک داورِ ریاضیِ شواهدمحور رد شود که
> فاصلهٔ «وضعِ واقعی» تا «وضعِ سالم» را می‌سنجد و اگر شواهد کم بود، صادقانه بگوید «نمی‌دانم».

## چرا «وتر»؟

فیثاغورس در این معماری استعاره نیست؛ متریک است. هر mission یک بردارِ حالت در فضای ۸بعدی
است و وترِ تصمیم، فاصلهٔ اقلیدسیِ وزن‌دارِ آن تا حالتِ هدف:

$$d(x, x^*) = \sqrt{ \tfrac{\sum_i w_i (x_i - x_i^*)^2}{\sum_i w_i} } \in [0,1]$$

- $x$: آنچه واقعاً از لاگ/تست/خروجی دیده‌ایم — نه آنچه LLM می‌گوید.
- $x^*$: تعریفِ «سالم» (targets).
- $w_i$: ریسک و شواهد سنگین‌تر از زیباییِ جوابِ مدل.
- **فاصلهٔ زیاد ≠ مجوزِ تغییرِ زیاد.** شواهدِ کم/تناقض/برگشت‌ناپذیری → UNKNOWN/OBSERVE/APPROVAL.

## ابعاد v0 (همه در [0,1]؛ جهتِ خوب = target)

| بُعد | هدف | وزن | منبعِ نمونه |
|---|---|---|---|
| evidence_quality | 1 | 1.5 | پوشش/قوتِ شواهد |
| test_health | 1 | 1.5 | نتیجهٔ واقعیِ تست |
| goal_alignment | 1 | 1.0 | GOALS-OCTOPUS/mission |
| operational_risk | 0 | **2.0** | دامنهٔ اثرِ تغییر |
| reversibility | 1 | 1.5 | worktree/flag/revert |
| cost_budget | 0 | 0.75 | سهمِ بودجه (paper تا P7) |
| uncertainty | 0 | 1.25 | تناقض + کمبودِ پوشش |
| dependency_health | 1 | 1.0 | ollama/fugu/فایل/سرویس |

> این ابعاد **کیفیتِ تصمیمِ عملیاتی** را می‌سنجند — نه هوش، نه آگاهی، نه روانِ انسان.

## خطِ لوله

مشاهده (لاگ/تست/تلگرام؛ LLM فقط استخراج‌گرِ JSONِ سخت‌گیر با سقفِ قوتِ ۰.۵ از درِ واحدِ
`model_router.ask` — محلی-اولِ Qwen، Fugu فقط کارِ سنگین) → `build_state_vector` (بُعدِ
بی‌شاهد = خنثیِ بدبینانه، نه سالم) → وتر + گیتِ عدم‌قطعیت → policy → `ChordAssessment` →
ledger هش‌زنجیرهٔ خودش + کارتِ تلگرام (فقط render).

## جدولِ حکم (policy v0)

| شرط | Verdict | اجازه‌ها | تأیید مالک |
|---|---|---|---|
| kill-switch / مشاهدهٔ secret-آلوده | BLOCK | – / observe | – |
| پوشش < ۰.۳۵ | UNKNOWN | observe.collect | خیر |
| پوشش < ۰.۶ یا تناقض یا عدم‌قطعیت > ۰.۶ | OBSERVE_MORE | observe.collect | خیر |
| پرچمِ ردهٔ مهم (پول/secret/حذف/ارسال/ژنوم/برگشت‌ناپذیر) | REQUEST_APPROVAL | plan (+test) | **بله** |
| ریسک ≥ ۰.۶ یا برگشت‌پذیری ≤ ۰.۴ | REQUEST_APPROVAL | plan/test | **بله** |
| d ≤ ۰.۱۵ | HEALTHY | observe | خیر |
| در غیرِ این صورت | PROPOSE_PATCH | plan/test/diff/doctor.review | خیر (اجرا هرگز) |

**مرزِ آهنین:** `allowed_actions` هرگز `code.apply`/`code.patch`/`money.move`… ندارد —
اجرای واقعی فقط از مسیرِ موجودِ approval/allowlist/worktree (mission_runner). chord مشاور است.

## جایگاه در ارگانیسم

- خواهرِ `_ops/epistemics` (آگاهیِ سیستمی) — chord = هندسهٔ تصمیمِ تعمیر؛ doctor = تصمیم‌گیر.
- تلگرام پنجرهٔ نازک: کارتِ 🧭 در `/doctor`/`/health` + رأی /approve از مسیرِ موجود.
  وایرینگ به `center.py` فقط در لِینِ سریالِ worktree، پشتِ فلگِ خاموشِ `OCTOPUS_WIRE_CHORD`.
- بُعدِ انسانی/زبانی (تحقیقاتِ مالک دربارهٔ کلمات و شناختِ خویشتن) = **لایهٔ تحقیقِ جدا**:
  [[../03 - Projects/Chord/PROJECT|پروژهٔ Chord]] با برچسبِ اجباریِ سطحِ شواهد
  (established/supported/hypothesis/speculative). ورودش به policy فقط بعد از probeِ موفق.

## نردبانِ فعال‌سازی (هر پله = رأی مالک)

۱) الان: سایهٔ محض — ۳۰/۳۰ تست سبز، هیچ‌کس verdict نمی‌خواند.
۲) فاز C: دکتر کنارِ هر RFC/mission ارزیابیِ chord را **فقط ثبت** می‌کند (worktree).
۳) ارزیابی: ≥۲ هفته دادهٔ جفتی — آیا chord واقعاً خطا/rollback/هزینه را بهتر پیش‌بینی کرد؟
۴) فقط بعدش: `OCTOPUS_WIRE_CHORD=1` برای گیتِ تعمیرهای کم‌ریسک. پول/LIVE = P7، ابدی مالک.

کد: `_ops/chord/` (spec فنی در README همان‌جا) · تست: `_ops/tests/test_chord.py` ·
پرامپتِ ایجنتِ بعدی: [[octopus-build-prompts/CHORD-AGENT-PROMPT-2026-07-18]]
