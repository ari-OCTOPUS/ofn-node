---
type: reference
status: active
project: "[[03 - Projects/Lead-نقاشی/PROJECT]]"
tags: [lead-gen, pipeline, experiments]
created: 2026-07-03
updated: 2026-07-03
---

# Lead Pipeline & Experiment Log

## Pipeline لیدها (schema)

| تاریخ | منبع | segment | وضعیت | ارزش تخمینی (AUD) | نکته |
|---|---|---|---|---|---|
| — | — | residential \| strata \| builder | new → contacted → quoted → won/lost | — | — |

*(خالی — با اولین لید واقعی پر می‌شود `[To measure]`)*

## قالب آزمایش لیدگیری — **یک آزمایش در هر زمان**

```markdown
## آزمایش #N: <نام>
- فرضیه: __
- کانال: __ · هزینه: __ AUD · بازه: __ هفته
- متریک تصمیم: __ (لید واقعی، نه کلیک)
- نتیجه: __ · verdict: ادامه/چرخش/توقف
```

## آزمایش #۱ — SEGMENT-DISCOVERY (پیش‌ثبت‌شده طبق D5؛ شروع نشده)

- **فرضیه:** «کدام segment (residential / strata / builder) برای یک اپراتور تنها بیشترین ارزش per lead می‌دهد؟»
- کانال: `[To measure — تصمیم مالک]` · هزینه: `[To measure]` · بازه پیشنهادی: ۴ هفته `[Assumption]`
- متریک تصمیم: ارزش تخمینی مجموع لیدهای واقعی ÷ تعداد لید، per segment
- **قاعده:** فیلد segment در PROJECT.md تا پایان این آزمایش `[To measure]` می‌ماند — پیش‌داوری ممنوع.
- نتیجه: — · verdict: —
