# WLOS — Product Requirements (WLOS-Sydney-1)

A private, persistent, mixed Persian/English AI weight-management operating system on
Telegram for **one user in Sydney, Australia**. It coaches gym, daily calorie tracking,
behavior/psychology (non-clinical), sleep/recovery, cannabis-aware personalization
(consent-gated), and investigates a multi-year weight plateau. It is **not a medical
service** and never presents itself as one.

## Product configuration (owner-decided)

| Setting | Value |
|---|---|
| Use case | Personal, single user |
| Timezone | Australia/Sydney (DST automatic; all daily boundaries = local midnight) |
| Language | Persian-forward with natural English terms; code/DB/docs in English |
| Food logging | **Name + calories only.** No photos, no computer vision, no barcode requirement |
| Message cap | Hard **20/day**; default cadence 3–6 check-ins |
| Quiet hours | 00:00–07:00 (safety bypasses; `/nosleep` suspends) |
| Data durability | Durable from day one; full history until explicit deletion |
| LLM | Sakana Fugu enabled day one; graceful degradation mandatory |
| Expert link | Weekly coach-ready report + protected coach-notes endpoint |
| Self-correction | Weekly self-modification proposals; **user approves every change** |

## Functional requirements → implementation map

| Requirement | Where |
|---|---|
| Onboarding in Persian, one question at a time | `apps/telegram-bot/src/onboarding.ts` |
| Weight logging + 7-day rolling average + trend | `/weight` → `nutrition-engine/trends.ts` |
| Meal logging (name+kcal, fa/en digits, optional macros) | `/meal` + free text → `meal-parser.ts` |
| Workout plans (gym/home/travel/minimum-dose) + readiness gate | `training-engine` |
| BMR/TDEE/targets as ranges with floors | `nutrition-engine/calculations.ts` |
| Randomized context-aware check-ins, one question each | `jitai-engine` + `checkins.ts` |
| 257-question tagged bank, consent/cooldown-aware selection | `behavior-engine` |
| Plateau investigation (never assumes; never cuts calories first) | `agents/plateau.ts` |
| Patterns with evidence/counterexamples/confidence + user veto | `agents/patterns.ts`, `/patterns` |
| Daily/weekly/coach reports | `agents/reports.ts`, `/report`, `/weekly`, `GET /coach/report` |
| Self-modification proposals (approval-gated) | `agents/self-mod.ts` |
| Consent management, export, deletion | `/privacy`, `/consent`, `/export`, `/delete` |
| Crisis handling with AU resources | `safety` package + `/crisis` |
| Fugu deep reasoning with fallback chain | `fugu-provider` |

## Non-negotiable principles (enforced, not aspirational)

1. No diagnosis, no clinician impersonation → content-guard `diagnosis_language` + prompts.
2. No starvation/detox/purge/compensatory-exercise advice → content-guard blocks; calorie
   floors in the math itself.
3. No shame — ever, including cannabis and lapses → content-guard `shame_language`.
4. No raw photos of food → photo messages are politely rejected by design.
5. Sensitive topics never in notification previews → neutral envelope + reveal.
6. Backend owns memory; LLMs receive minimal redacted packets → `memory/packet.ts`.
7. One question per check-in message → selection returns 0 or 1, structurally.
8. Cap/quiet-hours violations are **bugs**, tracked as guardrail metrics with target 0.
9. Every inferred pattern carries evidence count, counterexamples, confidence, `notCausal`.
10. Cannabis features OFF by default, separate consent, neutral language, no instructions.
11. User can inspect, correct, export, delete everything.
12. Basic coaching works with every LLM provider down.

## Out of scope (this phase)

Photo/vision calorie estimation; wearables; multi-user; public deployment; medication or
supplement advice; automatic emergency contact; PDF export (MD/JSON ship now).

## Success criteria

See `evaluation-plan.md` for outcomes and guardrails, and §14 acceptance criteria mapped
in the README. The product goal is **sustainable progress with minimum necessary burden**
— explicitly not engagement maximization.
