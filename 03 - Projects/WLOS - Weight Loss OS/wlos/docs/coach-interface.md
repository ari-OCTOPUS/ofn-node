# Coach Interface

WLOS is a personal tool, not a medical service — but its owner may work with a real human coach, trainer, or clinician (spec §10). The coach interface does two things: it produces a weekly **Coach-Ready Report** the user can hand to that human, and it accepts **coach notes** back into the system, which every agent treats as constraints. The entire feature is gated by the `coach_sharing` consent scope: if that consent is not granted, no coach-ready report is generated and the `/coach` endpoints refuse to store notes against the user. The AI never claims — in reports, chat, or anywhere else — to replace a regulated clinician's judgment; the report exists precisely so a qualified human can apply theirs.

## Weekly Coach-Ready Report

Generated weekly (worker job), stored as a `Report` row with `kind = 'coach_ready'`. Contents:

| Section | What it contains |
|---|---|
| Weight trend | Raw weigh-ins + rolling averages (the trend line, not day-to-day noise) |
| Nutrition | Average daily calories, **logging completeness** (days with meals logged — so the coach knows how much to trust the averages), protein average vs target |
| Training | Workout adherence: planned vs completed, by kind |
| Sleep | Average hours, consistency |
| Subjective state | Mood / hunger / stress averages (0–10 scales from check-ins) |
| Patterns | Detected patterns **with confidence level and counterexample counts** — always framed as associations, never causal claims (`Pattern.notCausal`) |
| Experiments | Active experiments: hypothesis, dates, outcome measures |
| Plateau status | Whether a plateau is currently flagged and since when |
| Safety flags | Any `SafetyEvent` summary the coach should know about |
| Cannabis summary | **Only if BOTH `coach_sharing` AND `cannabis` consents are granted.** Either consent missing → the section is entirely absent, not redacted |

The completeness numbers matter: an average of 1,900 kcal over 3 logged days and over 7 logged days are different facts, and the report never hides which one the coach is looking at.

Skeleton of the markdown format (values illustrative):

```markdown
# WLOS Coach-Ready Report — week ending 2026-07-19
## Weight        84.2 kg (7-day avg), trend −0.3 kg/wk over 4 wks
## Nutrition     avg 1,910 kcal/day over 6/7 logged days; protein avg 128 g (target 130)
## Training      4/5 planned sessions completed (1 travel substitution)
## Sleep         avg 6.4 h, high variance (5.1–7.8)
## State         mood 6.1 · hunger 5.4 · stress 6.8 (0–10 averages)
## Patterns      "sleep <6h → evening craving": confidence medium, 9 supporting / 2 counterexamples. Association, not causation.
## Experiments   active: earlier dinner window (day 5 of 14)
## Plateau       none flagged
## Safety        none this period
```

## Formats and delivery

- **Available now**: markdown (readable, forwardable) and JSON (for a coach's own tooling). These are the two values of `Report.format`.
- **Not yet implemented**: PDF export. It is planned, honestly: today the markdown file is the printable artifact.
- **Delivery is user-controlled.** The bot sends the report file to the user in Telegram; the **user forwards it** to their coach themselves. The system **never auto-emails or auto-sends anything to a third party** — there is no coach email field anywhere in the schema, by design.

Example of the bot's delivery message (Persian, as the user sees it):

> گزارش هفتگی مربی آماده‌ست 📄 (markdown + JSON)
> خودت تصمیم می‌گیری برای کی بفرستیش — من هیچ‌وقت مستقیم برای کسی نمی‌فرستم.

## Coach notes (inbound)

Coaches send guidance in through the Fastify API, authenticated with the shared `COACH_API_KEY` (see `.env.example`); a Telegram Mini App screen for coaches is planned but not yet implemented.

```bash
curl -X POST https://wlos.example.com/coach/notes \
  -H "Authorization: Bearer $COACH_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"author": "coach-sara", "content": "Keep protein at or above 130 g/day. Deload week starts Monday."}'
```

Request and storage fields:

| Field | Notes |
|---|---|
| `author` | Coach identifier string — coaches have **no WLOS account**; this is a label, not a login |
| `content` | Free text, stored verbatim in `CoachNote.content` and treated as a constraint |
| `active` | Defaults true; a deactivated note stops constraining agents |
| `createdAt` | Set server-side |

The user is always shown active notes — the coach channel is never a hidden side-channel of instructions.

### Managing notes

A note stays active until deactivated. Deactivation (`active = false`) can come from the coach via the same authenticated API, or from the user telling WLOS directly ("ignore the deload note, we changed plan"). Either path is audit-logged (`AuditLog.actor = 'coach'` or `'user'`), and agents pick up the change on their next run. Notes are never edited in place — a correction is a new note plus deactivation of the old one, so the history stays honest.

## How agents treat coach notes: the precedence stack

Coach notes are **constraints**, layered above WLOS's own suggestions but below safety rules:

```
1. Safety rules            (floors, crisis mode, escalation — immovable)
2. Coach notes             (constraints; agents obey, never silently override)
3. WLOS-generated plans    (nutrition targets, training suggestions, experiments)
```

- "Coach said keep protein ≥ 130 g" → the nutrition agent sets `NutritionTarget.proteinG` accordingly and plans around it. WLOS does not "improve" on the coach's number.
- A note that **contradicts a safety floor** (e.g. a calorie target below the safety minimum) is **not silently obeyed and not silently ignored** — it is surfaced to the user so they can resolve it with their coach:

> یادداشت مربی: «کالری روزانه ۱۲۰۰». این از کف ایمنی برنامهٔ من پایین‌تره، پس خودم اعمالش نمی‌کنم.
> لطفاً با مربی‌ات مطرحش کن — تصمیم نهایی با شما دوتاست، نه با من.

- Deactivating a note (`active = false`) releases the constraint; agents pick that up on their next run. Note changes are audit-logged like every other externally-caused change.

## Consent lifecycle

`coach_sharing` behaves like every other consent scope: current state in `Consent`, full append-only history in `ConsentEvent`.

- **Granting** enables weekly coach-ready report generation and note storage from the next cycle.
- **Revoking** stops report generation immediately and deactivates the constraint layer (existing `CoachNote` rows are retained for history but no longer bind agents until consent returns).
- Revoking `cannabis` alone removes the cannabis section from all future reports while leaving the rest of the coach feature intact.
- Reports reflect consent **at generation time**. Revoking consent cannot recall a file the user already forwarded — that is stated to the user plainly rather than implied away.

## Boundaries

- WLOS **never claims to replace** a doctor, dietitian, psychologist, or any regulated clinician. Coach notes inform the system; they do not turn it into a treatment delivery channel.
- The coach has no WLOS account and no read access to the database. Their entire view of the user is the report the user chose to forward; their entire write access is `POST /coach/notes`.
- `COACH_API_KEY` is a single shared secret suitable for the single-user, one-coach reality of this deployment. If that ever changes, per-coach credentials come first.

## Privacy note: sharing over Telegram

The report is sensitive health data. When the user forwards it over Telegram, it inherits Telegram's properties: regular chats are cloud-stored (not end-to-end encrypted), and the coach's device retains the file. Practical guidance for the user, documented here so the bot can repeat it: prefer sending directly to the coach (not to groups), remember that "delete for both" is best-effort once a file has been opened, and the cannabis section only exists in the file at all if both relevant consents were granted at generation time. When in doubt, generate a fresh report after tightening consents — reports reflect consent state at the moment they are built.
