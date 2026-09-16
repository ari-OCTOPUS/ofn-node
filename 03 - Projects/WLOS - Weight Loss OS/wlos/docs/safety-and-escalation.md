# Safety & Escalation

Deterministic first, LLM-assisted second, and the deterministic layer wraps the LLM on
both sides. The app performs **non-clinical triage**: it recognizes concerning content,
responds with care and Australian resources, pauses ordinary coaching, and suggests human
help. It never diagnoses, never claims to have contacted emergency services, and never
performs autonomous emergency intervention.

## Inbound triage (`safety/triage.ts`)

Persian + English regex rules over normalized text (`searchKey`: digit-unified,
fa-normalized, lowercased). Sensitive-by-default bias — a false positive costs one caring
message; the user can always `/resume`.

| Level | Categories | Response |
|---|---|---|
| `crisis` | self_harm, mood_crisis | AU resources (000, Lifeline 13 11 14, Suicide Call Back 1300 659 467, Beyond Blue 1300 22 4636, MensLine 1300 78 99 78, Kids Helpline 1800 55 1800) + `crisisModeUntil = now+24h`: check-ins and coaching suppressed; only `/resume` or safety messages flow. Suggests telling a trusted person. Makes **no promises about confidentiality or procedures** of the services listed. |
| `urgent_medical` | chest_pain, breathing, fainting, severe_dizziness, neurological, eating_disorder | Stop-training/deficit message + see a professional today / call 000. ED category additionally offers Butterfly Foundation 1800 33 4673 and the hide-calories option. |
| `caution` | pregnancy, medication, substance_help, sleep_apnea | Coaching continues but the relevant module constrains itself (e.g. no deficit targets during pregnancy) and professional consultation is suggested. |

Every event → `SafetyEvent` (level, categories, action; minimal detail) and, where
relevant, `Escalation` rows recommending human support.

## Outbound guard (`safety/content-guard.ts` + `clearance.ts`)

Runs on **every** message including LLM output. Hard-blocking codes (message replaced,
never sent): `below_calorie_floor` (any stated daily target < 1200), `starvation_language`,
`purge_language`, `medication_advice`, `cannabis_instruction`. Detect-and-log codes
(guardrail metric, promote-to-blocking if ever seen): `shame_language`,
`compensatory_exercise`, `detox_language`, `rapid_loss_promise`, `diagnosis_language`.

Bypass-proofing is structural: `SafetyClearance` is a branded type constructible only by
`clearOutbound()`; `sendViaOutbox` type-requires it and runtime-verifies the brand. There
is no other send path. Tests cover forged objects, sub-floor targets in Persian digits,
and clean-message passthrough.

## Eating-disorder safeguards (in the math, not just the words)

- Calorie floors 1200 F / 1500 M; deficit capped at 25% of TDEE (`calorieTargetRange`,
  tested).
- Targets are always ranges; no praise tied to restriction or scale speed.
- `hideCalories` profile flag: logging continues, numbers disappear from replies/reports.
- Rapid-loss promises and compensatory-exercise framing are guard codes.
- Behavior-based goals available throughout (minimum-dose sessions, restart actions).

## Escalation matrix (spec §15 → behavior)

| Signal | WLOS action |
|---|---|
| Chest pain, fainting, severe SOB, neuro signs | urgent_medical message; training plans withheld until user confirms review |
| Suicidal/self-harm language | crisis flow above |
| Suspected ED patterns (purge, multi-day restriction) | urgent_medical + Butterfly + hide-calories offer |
| Pregnancy/breastfeeding | caution; deficit targets disabled in `/plan` guidance |
| Medication questions | decline + refer; content-guard blocks advice in both directions |
| Substance-dependence help request | supportive, judgment-free referral framing |
| Sleep-apnea signs | caution + suggest GP/sleep study |

## What WLOS may do in an acute crisis — exhaustive list

Encourage immediate local emergency help (000) · display configured resources · suggest
contacting a trusted person · stop ordinary coaching · log the event minimally. Nothing
else — and never a claim that anyone was contacted.

## Verification

18 safety unit tests (fa/en triggers, hyperbole non-triggers like «این تمرین منو کشت»,
guard blocks, brand forgery); red-team scenario suite specified in `evaluation-plan.md`;
acceptance criteria "no agent can bypass safety" and "crisis interrupts coaching" are
both pinned by tests + structural design.
