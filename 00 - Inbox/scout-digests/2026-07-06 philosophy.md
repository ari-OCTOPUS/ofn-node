---
type: research
status: inbox
project: "[[04 - Architect System/architect/PROJECT]]"
created_by: agent
sources:
  - https://sites.stat.washington.edu/raftery/Research/PDF/Gneiting2007jasa.pdf
  - https://goodjudgment.com/about/the-science-of-superforecasting/
  - https://aiimpacts.org/evidence-on-good-forecasting-practices-from-the-good-judgment-project/
  - https://en.wikipedia.org/wiki/Calibrated_probability_assessment
  - http://www.hubbardresearch.com/wp-content/uploads/2019/06/Introduction-to-Calibrating-Probability-Assessments-Hubbard-Decision-Research.pdf
  - https://www.gatherthink.com/p/improving-your-forecasting-ability
  - https://en.wikipedia.org/wiki/Brier_score
tags: [research, philosophy]
created: 2026-07-06
updated: 2026-07-06
---

# Philosophy (decision theory: minimal calibration loop) — Research Digest 2026-07-06

> Picks up spore 1 from [[00 - Inbox/scout-digests/2026-07-04 philosophy|2026-07-04 philosophy]]: "what is the minimal decision-journal + proper-scoring schema that could be bolted onto scout-digests and Ari's real bets to create a calibration loop without heavy tooling?" Deliberately leaves spore 2 (measuring epistemic independence between scouts) for a later run — deep-diving one thread beats splitting today's budget.

## Today's question

What is the smallest decision-journal + scoring schema — grounded in the proper-scoring-rule and calibration-training literature — that turns real bets (crypto exits, lead-gen spend, coin picks) into an actual calibration signal, not just a log?

## Findings

1. **The Brier score is a *strictly proper* scoring rule — mathematically, the only way to maximize your expected score is to report your true belief.** Gneiting & Raftery (2007) formalize this: a scoring rule is proper if the forecaster's expected score is maximized by stating probability F when F is the truth, rather than hedging toward some other G; the Brier score (mean squared error between stated probability and outcome) is a canonical strictly-proper rule. → **Self-building system + Ari:** this is *why* the schema must be "probability + outcome," not "confidence: high/medium/low." Vague confidence language can't be scored and can't punish hedging; a number in [0,1] scored against a 1/0 outcome is the one format that mathematically rewards honesty over optics — for a scout's `epistemic_status` field or for Ari's own crypto-exit calls. [Gneiting & Raftery 2007](https://sites.stat.washington.edu/raftery/Research/PDF/Gneiting2007jasa.pdf)

2. **In the Good Judgment Project, ~50% of the accuracy gap between average forecasters and superforecasters was pure noise reduction, 25% information, 25% bias reduction — and rounding superforecasters' probabilities to the nearest 0.05 measurably hurt their scores.** Fine-grained numeric probabilities aren't pedantry; the granularity itself carries signal. → **Self-building system + Ari:** a solo operator has no team (the GJP's other two levers — teaming and aggregation — aren't available), so the two usable levers are *training* (repetition + feedback) and *noise reduction* (force an actual percentage, not a gut "probably"). The schema should reject bucketed confidence and require a specific number. [Good Judgment: Science of Superforecasting](https://goodjudgment.com/about/the-science-of-superforecasting/)

3. **Calibration is trainable through repeated small-stakes probability judgments with fast feedback, and the skill transfers into the person's real domain of expertise.** Hubbard's calibration-training method and the general calibrated-probability-assessment literature show people move from systematic over/under-confidence to genuine calibration mainly through volume of practice + immediate scoring, not through big high-stakes decisions (which are too rare to generate enough feedback cycles). → **Self-building system + Ari:** three crypto exits and a couple of coin picks a year is not enough repetitions to calibrate on. The schema needs a cheap *supplementary* stream — short-horizon, low-stakes forecasts (e.g. "will this lead reply within 48h?", "will this coin's 24h volume be up tomorrow?") — purely to accumulate scoreable reps between the rare big bets. [Calibrated probability assessment](https://en.wikipedia.org/wiki/Calibrated_probability_assessment) · [Hubbard: Introduction to Calibrating Probability Assessments](http://www.hubbardresearch.com/wp-content/uploads/2019/06/Introduction-to-Calibrating-Probability-Assessments-Hubbard-Decision-Research.pdf)

4. **Among the individual-level training techniques GJP tested, "comparison classes" (reference-class / base-rate anchoring) was one of the few consistently correlated with better accuracy.** Forecasters who explicitly asked "how often do situations like this actually resolve this way?" before giving a number outperformed those who reasoned from the specifics of the case alone. → **Self-building system + Ari:** the journal's one-line "reasoning" field shouldn't just be narrative justification — it should name a comparison class first ("last 5 similar leads converted in ~30%") *then* the probability. This is a near-free addition to the schema that the literature specifically flags as working. [AI Impacts: Evidence on good forecasting practices from GJP](https://aiimpacts.org/evidence-on-good-forecasting-practices-from-the-good-judgment-project/)

5. **The minimal viable decision journal already exists in the practitioner literature as five fields, with three non-negotiable disciplines: record before the verdict, confront every forecast at its deadline without exception, and only interpret the score in series (never a single Brier score in isolation).** Fields: date, decision/event description, probability (0–1), one-line reasoning, and outcome (1/0) at resolution; Brier score per item = (probability − outcome)², and the *average* over N items is the actual calibration signal. → **Self-building system + Ari:** spore 1 asked for a schema "without heavy tooling" — this is it, verbatim, and it needs no new app: a 6-column table (date · decision · probability · reasoning/comparison-class · resolution date · outcome) in a single Obsidian note, one row per real bet plus one row per cheap supplementary forecast (Finding 3), scored monthly. [GatherThink: Improving Your Forecasting Ability by Tracking Your Predictions](https://www.gatherthink.com/p/improving-your-forecasting-ability) · [Brier score](https://en.wikipedia.org/wiki/Brier_score)

## Mycorrhizal links

- [[00 - Inbox/scout-digests/2026-07-04 philosophy]] — this digest is the direct answer to that one's spore 1; the two should be read together before any promotion to Knowledge.
- [[06 - Architecture Maps/Property Schema]] — `epistemic_status` already distinguishes verified/speculative for digest claims; the 6-column schema above (Finding 5) is the natural extension of that same discipline to Ari's *real-world* bets, not just scout claims.
- [[03 - Projects/Crypto - etoro/PROJECT]] — crypto exits are the paradigm case of a resolvable, dated, scoreable bet this schema targets directly.

## Cross-domain (mandatory)

Feeds **`crypto`** and **`mining`** most directly (exit rules and coin picks are exactly the "real bets" this schema is built for), and closes the loop opened in the previous philosophy digest for **`selfimprove`**/`fleet-selection`: the same Brier-over-series logic (Finding 5) could score whether a *promoted* fleet finding actually paid off, giving `fleet-selection`'s weekly review an objective number instead of a vibe.

## Spores (open questions for next run)

- Concretely: what would a first month of the 6-column journal look like if seeded only with Ari's next 3 real bets (one crypto exit, one lead-spend decision, one coin pick) plus ~10 cheap 48-hour forecasts — is 13 data points enough to produce a meaningful first Brier average, or does the "interpret only in series" rule (Finding 5) mean it's premature to score before ~30?
- Revisiting 2026-07-04's still-open spore: how do we measure epistemic independence between scouts (shared-source overlap, correlated priors) so "requisite variety" is verified rather than assumed?
