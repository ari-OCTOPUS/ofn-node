# Behavioral Science in WLOS

WLOS is a personal-use behavior-support system, not a medical or psychotherapy service. This document maps each framework the product draws on to the data structures and logic that operationalize it. The standing rule: a framework earns its place only if it changes a column, a scoring function, or a message rule — name-dropping is not implementation. Ground truth is `prisma/schema.prisma` plus the `packages/behavior-engine`, `packages/jitai-engine`, and `packages/safety` sources cited below.

## Framework → implementation map

| Framework | Operationalized as | Where |
|---|---|---|
| COM-B + Behaviour Change Wheel | `Barrier.combCapability/combOpportunity/combMotivation` + vetted intervention menu | `packages/behavior-engine/src/comb.ts` |
| BCT Taxonomy v1 | `Strategy.bctCode` referencing a fixed 10-item menu | `comb.ts` (`INTERVENTION_MENU`) |
| Motivational Interviewing | Reflect / open-question / autonomy-support reply style; change-talk detection is a **future** LLM task | reply-composition rules |
| CBT-informed functional analysis | `BehavioralFormulation` 10-link chain with `confidence` + `evidenceCount` | `prisma/schema.prisma` |
| Self-Determination Theory | Autonomy language rules, minimum-dose competence wins, social-support mapping | content-guard + menu + domain J |
| Implementation intentions / WOOP | If-then plans stored as `Strategy` rows (BCT 1.4) | `Strategy` |
| Relapse prevention | Smallest-restart-action + no-shame recovery script; `recent_lapse` contraindication | question bank + `selection.ts` |
| Stimulus control / env. restructuring | Environment-domain (G) questions feeding `Strategy` (BCTs 12.3, 12.5, 8.3) | question bank + menu |
| Self-monitoring with burden mgmt | `burden` on every question, `burdenScore` in utility, backoff, skip semantics | `utility.ts`, `scheduler.ts` |
| Identity-based habits | Behavior-goal-over-scale-goal (BCT 1.2); `Memory.layer='identity'` | menu + `Memory` |
| Self-compassion | Shame language machine-detected on every outbound message; no-shame restart scripts | `packages/safety/src/content-guard.ts` |
| Temporal discounting awareness | `immediateReward` vs `delayedConsequence` made explicit per formulation | `BehavioralFormulation` |
| EAST (Easy, Attractive, Social, Timely) | Design checklist applied to every intervention and prompt | menu + JITAI engine |
| EMA (ecological momentary assessment) | `CheckinInstance`/`CheckinResponse` + `StateLog` 0–10 momentary scales | schema + scheduler |
| JITAI | Utility-scored, context-re-evaluated prompt delivery | `packages/jitai-engine` |
| n-of-1 self-experiments | `Experiment` → `ExperimentResult` lifecycle with stop conditions | schema |

## COM-B and the Behaviour Change Wheel

Every `Barrier` row carries three COM-B columns — `combCapability`, `combOpportunity`, `combMotivation` — each `sufficient | limited | unknown`. `candidatesFor(profile)` in `comb.ts` returns intervention candidates whose `targets` hit the components marked `limited`; if nothing is limited it returns only low-burden options. The LLM may *propose* a classification from what the user says, but the intervention menu is a deterministic table in code: BCTs cannot be hallucinated into existence. `unknown` is a first-class value — it drives the next diagnostic question rather than a guessed intervention.

## BCT Taxonomy (BCTTv1)

`Strategy.bctCode` ties each tactic to a BCTTv1-style reference so strategies are auditable against a real taxonomy. The full vetted menu (bilingual labels live in code):

| BCT | Intervention | Targets | Burden |
|---|---|---|---|
| 12.5 | Prepare equipment in advance (reduce start friction) | opportunity | low |
| 8.7 | 10-minute minimum-dose workout | motivation, capability | low |
| 1.4 | If-then plan (implementation intention) | motivation | low |
| 12.1 | Move training to a higher-energy window | motivation | medium |
| 12.3 | Reduce trigger-food accessibility | opportunity | medium |
| 2.3 | Simplify self-monitoring | capability | low |
| 3.1 | Enlist specific social support | opportunity | medium |
| 1.2 | Behavior goal over scale goal | motivation | low |
| 11.3 | Planned evening snack | motivation | low |
| 8.3 | Pre-portion snacks | opportunity | low |

Strategies move `candidate → testing → kept → discarded` — the same lifecycle vocabulary the n-of-1 layer uses, so a BCT is retained on evidence, not on enthusiasm.

## Motivational Interviewing

MI shapes *how* replies are written, not what data is stored: reflect before advising, prefer open questions, ask permission before offering a plan, and never argue the user into change. Example reflection: «پس شب‌ها بعد از یک روز پراسترس بیشتر سراغ خوراکی می‌ری — درست فهمیدم؟». Example autonomy support: «خودت فکر می‌کنی کدوم گزینه برات شدنی‌تره؟». Classifying change talk vs sustain talk is explicitly a **future** LLM task; today MI exists as composition rules plus the guard that blocks the anti-MI failure mode (shaming, prescribing, diagnosing).

## CBT-informed functional analysis — not psychotherapy

WLOS borrows CBT's *functional chain*, not its therapy. `BehavioralFormulation` stores Situation → Trigger → Thought → Emotion → Urge → Behavior → `immediateReward` → `delayedConsequence` → `alternativeResponse` → `experimentOutcome`. Every link is nullable — chains fill in over weeks from check-in answers, never from one conversation. `confidence` starts at `hypothesis` and `evidenceCount` at 1; a formulation is only surfaced to the user as a tentative "does this fit?" question. No thought-challenging scripts, no cognitive-distortion labels, no treatment framing.

## Self-Determination Theory

- **Autonomy**: choices are offered, never imposed; every check-in supports skip / not-now / never (`skipCooldownDays` in `selection.ts`); `refusedPermanently` is honored forever. Controlling or shaming phrasing is machine-detected outbound (`shame_language` in `content-guard.ts`).
- **Competence**: engineered through minimum-dose wins — `Workout.kind` includes `minimum_dose`, and BCT 8.7 ("فقط ۱۰ دقیقه؛ اگر خواستی ادامه بده») exists so success is reachable on bad days.
- **Relatedness**: domain J (`social_cultural`) questions map who helps and who undermines; BCT 3.1 turns that map into a concrete support activation.

## Implementation intentions and WOOP

If-then plans are `Strategy` rows with `bctCode='1.4'`, written in the user's own words: «اگر ساعت ۹ شب هوس شیرینی کردم، آن‌گاه اول چای می‌ریزم و میوهٔ آماده را برمی‌دارم». WOOP structures the weekly review conversation: Wish and Outcome come from `UserProfile.goalNote` and motivation-domain answers; Obstacle is a `Barrier`; Plan becomes the if-then `Strategy`. Nothing new to store — WOOP is a traversal order over existing tables.

## Relapse prevention

A lapse is data, not failure. The recovery script pairs a no-shame frame with the smallest restart action: «دیروز هر چی بود، تمام شد. کوچک‌ترین قدم امروز: ثبت وعدهٔ بعدی. همین.» Domain L (`relapse_recovery`) questions build the personal lapse playbook *in calm periods*, because `recent_lapse` is a selection contraindication — WLOS does not probe beliefs right after a hard day. The abstinence-violation spiral ("I broke the diet, so the day is ruined") is the exact pattern the formulation chain is designed to catch as `thought` → `behavior`.

## Stimulus control and environmental restructuring

Domain G (`environment`) questions inventory where trigger foods live, what is visible, and what is pre-prepared. Answers feed opportunity-targeted BCTs (12.3 remove triggers, 12.5 prepare equipment, 8.3 pre-portion) — changing the environment is usually cheaper than resisting it, which is why these dominate the low/medium-burden end of the menu.

## Self-monitoring with burden management

Self-monitoring is the engine and also the main burnout risk, so burden is priced everywhere: each question carries `burden` 1–5 and is scored `infoGain / (burden + 1)`; the JITAI utility subtracts `burdenScore`, `repetitionPenalty`, and `interruptionCost`; two ignored prompts halve check-in frequency (`nextBackoff`, floor 0.25, recovery +0.25 per answered prompt); BCT 2.3 exists to simplify logging itself; `Experiment.burdenEstimate` prices experiments before they start; `hideCalories` removes numbers from view when numbers themselves are the stressor.

## Identity, self-compassion, temporal discounting

- **Identity-based habits**: BCT 1.2 reframes targets from scale numbers to identity-consistent behaviors ("someone who trains on travel days"); durable self-descriptions live in `Memory.layer='identity'` with provenance.
- **Self-compassion**: operationalized negatively (shame language is machine-detected on every outbound message — see `docs/threat-model.md` for the enforcement token) and positively (recovery scripts model kind self-talk).
- **Temporal discounting**: the formulation chain forces `immediateReward` and `delayedConsequence` to be named side by side, and planned alternatives (11.3 planned evening snack) supply a *present-tense* reward instead of asking for willpower.

## EAST

Every proposed intervention is checked against EAST: **Easy** (minimum dose, friction removal, one question per message), **Attractive** (framing wins, not lectures), **Social** (BCT 3.1), **Timely** (deliver at risk windows, not on a clock — the JITAI layer below). EAST is a rejection filter for clever-but-heavy ideas.

## The question bank as measurement instrument

All of the above depends on asking good questions at low cost. The bank (`packages/behavior-engine/src/question-types.ts`) is versioned in code; every question carries Persian text + English reference, a response type (`scale_0_10 | yes_no | choice | free_text | number | done_notyet`), `burden` and `infoGain` (1–5), `cooldownDays`, `prerequisites`, allowed contexts (`onboarding | checkin | weekly_review | chat`), contraindications, and a consent scope. Thirteen domains:

| Domain | Key | Feeds | Consent |
|---|---|---|---|
| A | `weight_history` | baseline narrative, expectation-setting | core |
| B | `motivation_values` | SDT autonomy anchors, WOOP wish/outcome | core |
| C | `self_efficacy` | primary outcome trend (see evaluation plan) | core |
| D | `dieting_beliefs` | all-or-nothing belief detection → formulations | core |
| E | `hunger_cravings` | risk windows, planned-snack strategies | core |
| F | `emotional_context` | formulation emotion/urge links | **psychology** |
| G | `environment` | stimulus-control strategies | core |
| H | `exercise_psychology` | minimum-dose calibration | core |
| I | `sleep_recovery` | sleep→craving patterns | core |
| J | `social_cultural` | relatedness map, BCT 3.1 | core |
| K | `cannabis` | neutral use↔hunger observation | **cannabis** |
| L | `relapse_recovery` | personal lapse playbook | core |
| M | `interaction_prefs` | burden tuning, self-mod proposals | core |

Selection (`selection.ts`) returns **at most one** question per message: filter by permanent refusals, consent, context, contraindications, prerequisites, and cooldown; then rank by `infoGain/(burden+1)` × slot-topic bias (1.5) × revalidation discount (0.4 for ever-answered questions) × seeded jitter (0.85–1.15). Skips are graded: "never" bans forever, "not now" retries after a day, plain skip waits `max(2, cooldown/2)` days.

## EMA, JITAI, and n-of-1: the measurement and delivery spine

**EMA.** Check-ins are momentary sampling, not surveys: `planDay()` places 3–6 prompts across four windows (morning / midday / pre-evening / evening) with seeded jitter (`mulberry32(seed(dayKey:timezone))` — deterministic per day, varied across days), plus up to 2 extras in predicted risk windows. Quiet hours 00:00–07:00 and a 120-minute minimum gap hold by construction. Answers land in `CheckinResponse` and 0–10 `StateLog` scales (`mood`, `hunger`, `craving`, `stress`, `energy`, `focus`, `motivation`, `sleep_hours`).

**JITAI.** Right-moment delivery is a scored decision. `utilityScore()` multiplies information gain × actionability × context relevance × response likelihood, then subtracts weighted burden, repetition, privacy exposure, and interruption costs (send threshold 0.15). Weights are static config — no uncontrolled RL in production. Every planned prompt is re-evaluated at fire time (`shouldStillSend`): crisis mode, pause, snooze, daily cap, quiet hours, or an already-answered topic cancels it. A stale prompt is cancelled, not delivered.

**n-of-1.** Hypotheses graduate to `Experiment` rows: hypothesis, baseline, intervention, start/end day keys, primary outcome, explicit `stopConditions`, and `burdenEstimate` — all fixed *before* the experiment runs. `ExperimentResult` records outcome, confidence, and a decision (`retain | modify | discard`). One variable at a time; the person is the trial.

## What the psychology layer must never do

1. **No diagnosis, ever.** WLOS never labels the user with a disorder, in either language. `diagnosis_language` is machine-detected on all outbound text — including LLM output — and concerns route to human professionals via `Escalation` and the AU resource list.
2. **No pathologizing skipped answers.** A skip is scheduling signal, not clinical signal. Skip / not-now / never adjust cooldowns, ignored prompts trigger backoff, and `refusedPermanently` is permanent. Silence must never appear in a formulation as "avoidance."
3. **No single-answer inference.** Nothing becomes a `Pattern` from one data point. Patterns require accumulating `evidenceCount` against `counterexampleCount`, climb `hypothesis → low → medium → high` confidence, carry `notCausal=true` by default, and store a `nextValidationQuestion` — WLOS asks before it believes. A user correction (`PatternUserCorrection`, `userVerdict`) overrides any inference outright.
4. **No probing at the wrong moment.** `crisisModeUntil` suppresses ordinary coaching entirely; contraindications (`crisis_mode`, `recent_lapse`, `low_mood_today`, `user_overwhelmed`, `late_evening`) hard-filter question selection.
5. **No sensitive use without consent.** Emotional-context (F) and cannabis (K) domains, and any observation flagged `sensitive`, require the corresponding consent scope before they are asked, stored for use, or included in any LLM packet.
