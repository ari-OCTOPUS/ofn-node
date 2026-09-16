# Privacy & Consent

Single-user product; the user is the data owner, full stop. Data lives in the user's own
Postgres (Sydney-hosted when deployed to cloud). Nothing is sold, shared, or used to train
anything.

## Consent model

Four scopes, stored as current state (`Consent`) plus an append-only trail
(`ConsentEvent` with source + timestamp):

| Scope | Default | Gates |
|---|---|---|
| `core_health` | ON (required to function) | weight/meals/workouts/sleep logging |
| `psychology` | **OFF** | emotional-context questions, probing belief questions, psych observations, their inclusion in LLM packets |
| `cannabis` | **OFF** | every K-domain question, `CannabisEvent` storage, cannabis pattern template, any LLM exposure |
| `coach_sharing` | **OFF** | the entire coach report; cannabis appears there only if BOTH `coach_sharing` AND `cannabis` are on |

Toggling: onboarding step, `/consent`, `/privacy` inline buttons — instant effect, logged.
Consent checks are enforced at **three layers**: question selection
(`behavior-engine/selection.ts`), pattern scanning (`agents/patterns.ts` skips gated
templates), and the LLM packet firewall (`memory/packet.ts` excludes categories without
consent even when a task requests them). All three layers are unit-tested.

## Minimization & retention

- Meals store what the user typed + a normalized key — no photos ever (product decision).
- `SafetyEvent.detail` holds minimal necessary data; matched regex names, not full text.
- LLM audit (`LlmCall`) stores purpose + category names, never packet content.
- Envelope stashes (`Memory` layer `dynamic_state`) expire in 24h.
- Everything else is kept until deletion — the owner chose full history durability;
  `Memory.expiresAt` exists for future per-layer retention policies.

## User rights, implemented

| Right | Mechanism |
|---|---|
| Inspect | `/patterns` (with confidence + evidence), `/report`, `/weekly`, Mini App later |
| Correct | pattern «درسته/اشتباهه» buttons → `PatternUserCorrection`; user verdict permanently overrides the machine (`userVerdict='rejected'` vetoes reuse) |
| Export | `/export` → complete JSON (`wlos-export-v1`) sent as a Telegram document; `DataExportJob` recorded |
| Delete | `/delete` → typed `DELETE ALL` confirmation → hard purge via FK cascade; `DeletionRequest` trail survives in the request log only |
| Pause | `/pause`, `/snooze`, «امروز دیگه نپرس», permanent per-question refusal |

## Telegram-specific stance

Bot chats are **not end-to-end encrypted** (Telegram cloud encryption). Therefore:
sensitive wording never appears in proactive message previews (envelope+reveal), raw
detail stays in the backend, and the doc string in `/privacy` says this to the user
plainly. Exported files travel through Telegram; the user is told they own the copy.

## Secrets

`TELEGRAM_BOT_TOKEN`, `SAKANA_API_KEY`, `COACH_API_KEY` only via environment / secret
manager; `.env` is gitignored; `.env.example` carries names, never values. Coach endpoint
uses constant-time key comparison. Logs (pino) never print tokens; Telegram ids appear
only in the DB, and `redactIdentifiers` strips ids/emails/phones/handles from anything
LLM-bound.

## Australian context

Data residency target ap-southeast-2 (see `deployment.md`). Cannabis records are legally
sensitive in NSW — flagged in `threat-model.md`; mitigations: OFF-by-default consent,
envelope previews, hard delete, and the user's explicit awareness that they store this
about themselves, for themselves.
