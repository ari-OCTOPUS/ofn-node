# Plateau Investigation Protocol

The initiating user reports a ~3-year weight plateau. WLOS treats "plateau" as a **claim
to investigate**, not a fact — and never as evidence of low willpower.

## Principles

1. A true metabolic plateau is the *last* hypothesis standing, not the first.
2. No calorie reduction until measurement and behavior layers are exhausted.
3. One major variable changes at a time; a few days of scale noise triggers nothing.
4. Medical signals exit the protocol immediately toward professional review.

## Pipeline (`packages/agents/src/plateau.ts`, unit-tested)

```
inputs: daily weights (sparse ok), logged intake, logging completeness,
        weekend–weekday intake gap, steps trend, sleep avg,
        recent training change, sodium/travel spike, medication change, symptoms

Gate 0  n<10 weigh-ins or span<14d      → data_insufficient (collect 14–28d, change nothing)
Gate 1  symptoms/medication change      → medical_review_recommended (no new deficit)
Gate 2  trend already "losing"          → unconfirmed (perceived plateau vs slow progress)
Gate 3  logging<70% | weekend gap>400   → likely_adherence_or_measurement_issue
        | steps declining | sleep<6.5h
Gate 4  new training block | sodium/travel → likely_water_weight_masking (wait 10–14d, waist weekly)
Gate 5  clean data + flat trend         → likely_true_plateau
        confidence: high iff span ≥28d AND logging ≥85%
```

Statistics used (from `nutrition-engine/trends.ts`): 7-day rolling average (min 3 points),
least-squares slope in kg/week and %BW/week, ±0.15%BW/week noise band, missingness, σ, and
**observed TDEE** = mean intake − (Δkg×7700)/days — only when ≥14d span, ≥10 weigh-ins,
≥60% intake logging; always emitted as a range with a stated caveat that under-logging
inflates it.

## Output contract

Every run returns: `status`, `confidence`, `evidence[]`, `competingExplanations[]`,
`nextBestMeasurement` (Persian, concrete), `smallestSafeExperiment` (Persian, concrete),
`reviewInDays`, `observedTdeeEstimate|null`.

## The order of experiments for a confirmed plateau

1. **Measurement accuracy** — two weeks of complete logging (drinks, oils, sauces,
   tastings, weekends). Frequently ends the investigation by itself.
2. **Meal structure** — protein-forward breakfast, planned evening snack.
3. **NEAT** — +1500 steps/day before any intake change.
4. **Sleep/recovery** — earlier wind-down when avg <6.5h.
5. **Only then** a calorie adjustment, capped at −200 kcal, floors always intact,
   reviewed in 14 days.

The acceptance criterion "the three-year plateau protocol does not immediately reduce
calories" is pinned by test: `likely_true_plateau.smallestSafeExperiment` leads with
steps/protein and the calorie option appears only as a bounded last resort.

## What the user sees

`/weekly` carries the current status in plain Persian with the evidence and the single
next experiment. Sample framing (from code):

> «قبل از هر تغییری، دو هفته ثبت کامل‌تر: نوشیدنی‌ها، روغن، سس و آخر هفته‌ها — بدون تغییر رژیم.»

Fugu (`PROMPT_PLATEAU_DEEP_DIVE`) may narrate the deterministic report more warmly but is
explicitly forbidden from changing its status or sanctioning cuts the report didn't.
