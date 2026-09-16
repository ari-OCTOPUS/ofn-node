# Question Bank

The question bank is how WLOS learns about its user without ever feeling like a survey. It lives in code at `packages/behavior-engine/src/data/question-bank.ts`, is versioned (`QUESTION_BANK_VERSION = '2026.07.0'`), and targets **≥255 tagged questions across 13 domains (A–M)** per spec §5/§8. The file ships the full set of **257 questions** (validated by `packages/behavior-engine/src/behavior.test.ts`); the schema, id format, and selection rules documented here are final. Two rules dominate everything else: **exactly one question per Telegram message, ever**, and consent-gated domains are never selected without consent.

## Question schema, field by field

| Field | Type | Meaning |
|---|---|---|
| `id` | string | Stable id, `<domain letter>-<number>` (e.g. `E-012`). Referenced by `CheckinInstance.questionId` and ask history. **Never reused** once retired |
| `domain` | enum | One of the 13 domains below |
| `fa` | string | Persian text as actually sent (may embed English terms naturally, e.g. "skip") |
| `en` | string | English reference translation (docs, reports, developer sanity) |
| `responseType` | enum | `scale_0_10` \| `yes_no` \| `choice` \| `free_text` \| `number` \| `done_notyet` |
| `choicesFa` | string[]? | Button labels for `choice` questions |
| `sensitivity` | enum | `low` \| `medium` \| `high` — drives storage flags and preview handling |
| `burden` | 1–5 | How much effort answering takes. 1 = one tap, 5 = real reflection |
| `infoGain` | 1–5 | How much the answer teaches the system |
| `consentScope` | scope \| null | `null` = core. `psychology` / `cannabis` questions are hard-gated on those consents |
| `cooldownDays` | number | Minimum days before the question may be asked again (re-asking after cooldown = deliberate revalidation) |
| `prerequisites` | string[] | Question ids that must have been answered first (e.g. `A-002` requires `A-001`) |
| `allowedContexts` | enum[] | Where it may appear: `onboarding` \| `checkin` \| `weekly_review` \| `chat` |
| `contraindications` | enum[] | States that block it: `crisis_mode`, `recent_lapse`, `low_mood_today`, `user_overwhelmed`, `late_evening` |
| `followupIds` | string[] | Natural follow-ups the selector may chain to later |
| `neverInNotificationPreview` | boolean | If true, the question text must never be visible on a lock screen — envelope+reveal flow required |

## Domains

Count targets sum to 255. Consent gating is per-question (`consentScope`), but two domains are gated wholesale.

| Letter | Domain | Count target | Consent gate | Example (en reference) |
|---|---|---|---|---|
| A | weight_history | 15 | core | "When did your weight last change meaningfully?" |
| B | motivation_values | 20 | core | "Why does losing weight matter to you now?" |
| C | self_efficacy | 20 | core | "How confident are you that you can follow today's plan, 0–10?" |
| D | dieting_beliefs | 20 | core; belief-probing items psychology-gated (e.g. D-001) | "After eating more than planned, what do you usually tell yourself?" |
| E | hunger_cravings | 25 | core | "How intense is your hunger right now, 0–10?" |
| F | emotional_context | 25 | **psychology** | "What happened in the hour before this urge?" |
| G | environment | 20 | core | "Which foods are easiest to reach at home?" |
| H | exercise_psychology | 20 | core | "What makes you skip training most often?" |
| I | sleep_recovery | 20 | core | "Roughly how many hours did you sleep last night?" |
| J | social_cultural | 15 | core | "Who supports this goal the most?" |
| K | cannabis | 15 | **cannabis** | "Any use today? (personal pattern-finding only — no judgment)" |
| L | relapse_recovery | 20 | core | "What is the smallest action that would count as restarting?" |
| M | interaction_prefs | 20 | core | "What coaching tone do you prefer?" |

As actually sent, questions are Persian. C-001, for example:

> از ۰ تا ۱۰ چقدر مطمئنی که می‌تونی برنامهٔ امروز رو اجرا کنی؟

## Selection algorithm

Implemented in `packages/behavior-engine/src/selection.ts`. Selection returns **0 or 1** questions — an empty result is normal and means "send no question."

**Step 1 — eligibility filters** (`eligibleQuestions`), all hard gates:

1. Permanent refusal: any history entry with `refusedPermanently` excludes the question forever.
2. Consent: a non-core `consentScope` without that consent granted → out.
3. Context: current context (`checkin`, `chat`, …) must be in `allowedContexts`.
4. Contraindications: any active contraindication listed on the question → out (no belief-probing after a hard day, nothing heavy near sleep).
5. Prerequisites: every id in `prerequisites` must already be answered.
6. Cooldown: last ask day + `cooldownDays` must have passed. This also means an already-answered question can return after its cooldown — that is intentional revalidation, not a bug.

**Step 2 — scoring** each eligible question:

```
base  = (infoGain / (burden + 1)) × domainBoost × novelty
score = base × (0.85 + rng() × 0.3)          // seeded jitter, ±15%
```

- `domainBoost` = 1.5 if the question's domain matches the scheduler slot's topic hint, else 1.
- `novelty` = 0.4 if the question was ever answered before (revalidation is lower priority), else 1.
- The RNG is seeded per day: same-day reruns are deterministic, day-to-day selection varies.

The topic hint comes from the JITAI scheduler slot (`packages/jitai-engine/src/scheduler.ts`):

| Slot topic hint | Biased domains |
|---|---|
| `morning_awareness` | sleep_recovery, self_efficacy, motivation_values |
| `midday_check` | hunger_cravings, environment |
| `evening_risk` | hunger_cravings, emotional_context, environment |
| `reflection` | dieting_beliefs, relapse_recovery, weight_history, social_cultural |
| `risk_window` | hunger_cravings, emotional_context |

Highest score wins. One question, one message.

## Skip semantics

Every question offers a way out, and the answer is honored exactly (`skipCooldownDays`):

| Reply | Effect |
|---|---|
| skip | Cooldown of `max(2, ceil(cooldownDays / 2))` days — half the normal cooldown, minimum 2 days |
| not now | Retry allowed after 1 day |
| never ("don't ask this again") | **Permanent refusal, honored forever** — the id is excluded by the eligibility filter for the life of the system |

## Progressive profiling vs onboarding

Onboarding asks only the minimal set whose `allowedContexts` include `onboarding` — enough to function, nothing more. Everything else is learned gradually: one well-chosen question at a time inside check-ins, chats, and weekly reviews, budgeted by the same daily cap and quiet hours as every other message. The bank is designed so that after months of light-touch questions WLOS knows the user deeply, without a single session that felt like an intake form.

## Sensitive questions: envelope + reveal

Questions with `neverInNotificationPreview: true` (cannabis, emotional context, some belief items) must never put their text where a lock screen could show it. The bot sends a neutral **envelope** — which is also exactly what gets recorded as `OutboundMessage.preview` — and reveals the real question only after a tap:

> یک سؤال شخصی دارم — هر وقت آماده بودی بزن 👇
> [نشونم بده]

Tapping reveals, for example, K-001:

> امروز مصرفی داشتی؟ (فقط برای الگویابی شخصی — بدون قضاوت)

Declining the envelope counts as "not now" — no pressure, no re-send that day.

## Versioning policy

- Any change to the bank — adding, retiring, or editing question text/metadata — bumps `QUESTION_BANK_VERSION` (`year.month.revision`, currently `2026.07.0`).
- **Retired ids are never reused.** History, cooldowns, and `CheckinInstance.questionId` all reference ids; reusing one would silently corrupt ask history.
- Retiring a question keeps its history; it simply becomes ineligible.

## Interaction with self-modification

The weekly meta-learning job (see `docs/self-modification.md`) may create `SelfModProposal` rows with `category = 'question_bank'` — e.g. "retire E-014 (burden 4, answered 1 of 6 asks); add a shorter variant." Like every proposal, these **only take effect with explicit user approval** via the weekly report, and shipping the actual bank edit is a versioned code change: bump the version, never reuse the retired id.
