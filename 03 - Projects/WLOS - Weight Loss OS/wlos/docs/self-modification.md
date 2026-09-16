# Meta-Learning & Self-Modification

WLOS is adaptive, but adaptation is governed (spec §9): a weekly meta-learning job reviews how the system itself performed and writes **proposals** — never changes. Every proposal is a `SelfModProposal` row that surfaces in the weekly report with inline approve/reject buttons, and **nothing is applied without the user pressing approve**. This is the "no silent changes" invariant, and it exists because a self-tuning health system that quietly rewrites its own behaviour is exactly the thing this project refuses to be.

## What the weekly job reviews

The job (runs in the worker, once per week) reads only data WLOS already stores:

| Signal | Source |
|---|---|
| Response rate by slot and question type | `CheckinInstance` (`slotKey`, `status`: sent / answered / ignored) |
| Adherence to nutrition targets | `NutritionDailySummary.withinTarget`, logging completeness (`mealsLogged`) |
| Workout completion | `Workout.planned` vs `completed` |
| Sleep consistency | `StateLog` where `kind = 'sleep_hours'` (variance, missing days) |
| Burden complaints | Free-text complaints + `interaction_prefs` (domain M) answers |
| Ignored prompts / backoff state | `NotificationPreference.ignoredStreak`, `backoffMultiplier` |
| Pattern-correction rate | `PatternUserCorrection` (how often the user rejects inferred patterns) |
| Safety incidents | `SafetyEvent` count and levels |
| LLM cost and latency | `LlmCall` (`tokensIn`/`tokensOut`, `latencyMs`, `failureReason`, per provider/model) |

From these it produces zero or more proposals. A quiet week with good response rates should produce nothing — silence is a valid output.

## The proposal record

Each proposal is one `SelfModProposal` row:

| Field | Meaning |
|---|---|
| `category` | `message_budget` \| `quiet_hours` \| `question_bank` \| `schedule` \| `prompt` \| `parameter` \| `code` |
| `title` | One-line human-readable summary |
| `hypothesis` | What the job believes is wrong / improvable |
| `evidence` | Concrete numbers from the review (counts, rates, date ranges) |
| `expectedEffect` | What should improve if applied, and how we'd know |
| `burden` | Expected burden change for the user (default `low`) |
| `risk` | Risk level (default `low`) |
| `rollbackPlan` | Required. How to undo it — a proposal without a rollback plan is invalid |
| `status` | `pending` on creation |

## Proposal lifecycle

```
             ┌─────────┐  user taps ✅   ┌──────────┐   change lands    ┌─────────┐
 created ──▶ │ pending │ ───────────────▶│ approved │ ─────────────────▶│ applied │
             └─────────┘                 └──────────┘                   └─────────┘
                  │  user taps ❌
                  ▼
             ┌──────────┐
             │ rejected │   (decidedAt + decisionNote recorded in both branches)
             └──────────┘
```

- **pending → approved / rejected**: only via the inline buttons in the weekly report (or an explicit chat command). `decidedAt` and `decisionNote` are recorded.
- **approved → applied** (config categories): the worker writes the change to the owning table, sets `appliedAt`, and writes an `AuditLog` entry (`actor: 'system'`) referencing the proposal. The `rollbackPlan` is retained on the row so any applied change can be reverted later.
- **approved (categories `prompt` and `code`)**: these NEVER touch source or runtime. Approval writes a markdown task file to `todo/` (and becomes a GitHub issue once a repo exists) describing the change for the **developer** to implement after their own explicit confirmation. The proposal stays `approved` until the developer ships the change and marks it `applied`.
- **No decision**: the proposal simply stays `pending` and is re-surfaced in the next weekly report. Nothing expires into effect; the job checks existing pending proposals before filing a duplicate in the same category.

An example of the weekly-report surface (Persian, as the user sees it):

> پیشنهاد ۲ از ۳ — پنجرهٔ چک‌این عصر ۳۰ دقیقه زودتر بشه (۲۱:۳۰ ← ۲۱:۰۰)؟
> شواهد: ۹ از ۱۲ پیام بعد از ساعت ۲۱:۰۰ بی‌پاسخ موند.
> [✅ قبول]  [❌ رد]

## What approval writes, category by category

| Category | Effect of approval |
|---|---|
| `message_budget` | Update `NotificationPreference` (`targetCheckinsMin/Max`, `minGapMinutes`; `dailyCap` may only move **down** from 20) |
| `quiet_hours` | Update `NotificationPreference.quietStart` / `quietEnd` |
| `schedule` | Update the slot windows/probabilities the JITAI planner uses for this user |
| `question_bank` | Retire or re-weight questions via ask-history state; actual bank edits ship as a versioned code change (see `docs/question-bank.md`) |
| `parameter` | Update the owning config row, e.g. a new `NutritionTarget` with its `rationale` set to the proposal reference |
| `prompt` | Markdown task file in `todo/` — developer work only, no runtime change |
| `code` | Markdown task file in `todo/` — developer work only, no runtime change |

Every config write above is accompanied by the same trio: proposal row updated, `AuditLog` entry, `rollbackPlan` retained.

## The todo/ task file (prompt and code categories)

Approval of a `prompt` or `code` proposal produces a file like `todo/2026-07-19-add-walk-quicklog.md`:

```markdown
# [selfmod:code] Add /walk one-tap quick-log
Proposal: 3f9a2c… — approved 2026-07-19 (weekly report W29)
Hypothesis: walk logging friction suppresses activity data quality.
Evidence: 14 free-text walk reports manually parsed in the last 30 days.
Expected effect: walks logged via one tap; free-text fallback remains.
Rollback: remove the command registration; data model untouched.
NOTE: implement only after developer confirmation. The bot must never act on this file.
```

The bot's write access ends at creating this file. It does not edit source, open PRs, or run code — the developer reads the file, decides, implements, and only then flips the proposal to `applied`.

## Rolling back an applied change

Every applied proposal keeps its `rollbackPlan`, and rollback is a first-class operation: the user asks (or the developer runs it), the inverse write is applied to the same table, and a second `AuditLog` entry records the revert with a reference back to the proposal. A change that cannot describe its own undo is rejected at proposal-creation time.

## Examples of good proposals

- **`schedule`** — "Move evening slot 30 min earlier." Hypothesis: late-evening prompts land after wind-down. Evidence: 9/12 evening prompts ignored after 21:00 over the last 3 weeks. Expected effect: evening response rate above 50%. Burden: none. Risk: low. Rollback: revert slot window to 20:30–21:30.
- **`question_bank`** — "Retire question E-014, add a shorter variant." Evidence: burden 4, answered 1/6 times asked; the shorter E-001 covers the same signal. Rollback: un-retire (ids are never reused, so the id remains reserved).
- **`message_budget`** — "Lower target check-ins from 3–6 to 3–5 this month." Evidence: two burden complaints + `ignoredStreak` triggering backoff twice. Rollback: restore 3–6.
- **`code`** — "Add a `/walk` one-tap quick-log." Evidence: 14 free-text walk reports parsed manually. Result of approval: a task file in `todo/`, nothing else.

## Guardrails (checked before a proposal is even created)

- Proposals may **never weaken safety rules** — safety-message cap bypass, quiet-hours safety bypass, crisis-mode behaviour, nutrition floors, and escalation logic are out of scope for every category.
- Proposals may **never raise the daily message cap above 20** (Sydney local day). Proposing a *lower* effective budget is fine; 20 is a ceiling, not a dial.
- Proposals may **never touch consent defaults or scopes** — nothing may propose enabling `psychology`, `cannabis`, or `coach_sharing` data use; consent changes only ever come from the user directly.
- `category = code` proposals are **never executed by the bot itself** — no eval, no self-editing, no auto-PR. The bot's write access ends at the `todo/` directory.
- Every applied change must be attributable: `SelfModProposal` row + `AuditLog` entry + retained `rollbackPlan`. If any of the three is missing, the change does not happen.

## Why this design

The alternative — letting the system tune itself silently — fails the trust test this project is built on. The user should be able to answer "why did the bot start messaging me at 20:50 instead of 21:20?" with a specific approved proposal, its evidence, and the button they pressed. Adaptation earns its keep only when every adaptation has a paper trail and an undo.
