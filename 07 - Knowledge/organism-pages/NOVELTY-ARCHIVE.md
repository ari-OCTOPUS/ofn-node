# NOVELTY-ARCHIVE (ماشینی)

> machine-generated · grade=MEASURED · منبع: `_ops/state/novelty/archive.jsonl` + `_ops/debate/SURVIVORS-QUEUE.md`

## عدد صادقانهٔ همگروه (روش: normalize + exact-key + char3-jaccard)

| معیار | مقدار | درجه |
|---|---:|---|
| کل ردیفهای همگروه (مشاهدهشده) | 192 | OBSERVED |
| متن یکتای دقیق | 177 | VERIFIED (بازشماری قطعی) |
| رکوردِ تکرارِ دقیق | 15 | VERIFIED |
| جفتِ کاندیدِ نزدیک (jaccard≥0.80) | 3 | OBSERVED (نه حکم معنایی) |
| بدیعِ رفتاری و replay-پذیر | UNKNOWN | INCONCLUSIVE |

## وضعیتهای پذیرش (آرشیو)

INCOMPLETE · EXACT_DUPLICATE · VARIATION_CANDIDATE · NOVELTY_CANDIDATE · LEARNABLE · ADMITTED · QUARANTINED · RETIRED

- ADMITTED = NOVELTY_CANDIDATE + LEARNABLE + شاهدِ مستقل.
- گیت پیش از مصرف بودجه اجرا میشود؛ هزینه = صفر فراخوان.
- فلگ: `OCTOPUS_WIRE_NOVELTY_GATE` (پیشفرض خاموش؛ fail-soft).
