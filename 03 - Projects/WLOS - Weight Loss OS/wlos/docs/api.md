# WLOS API Reference

Fastify service (`apps/api`, port 8080). Personal-scale: one authenticated coach consumer
plus the Mini App verify endpoint. All timestamps ISO-8601 UTC; daily keys are
Sydney-local `YYYY-MM-DD`.

## Authentication

Coach endpoints require `x-api-key: <COACH_API_KEY>` (constant-time compared; 401
otherwise). The Mini App endpoint authenticates the *payload itself* via Telegram's
initData HMAC — no separate key.

## Endpoints

### GET /health
`200 {"ok":true,"service":"wlos-api","tz":"Australia/Sydney"}` — for compose healthchecks
and UptimeRobot.

### GET /coach/report?format=md|json
Coach-ready weekly report. **403 unless the `coach_sharing` consent is granted** — consent
gates the feature server-side, not just in UI. Cannabis section appears only when the
`cannabis` consent is *also* granted, and then only as an aggregate count.

- `format=md` (default): `text/markdown` — weight trend/σ/slope, avg intake + logging
  completeness vs target, workouts, sleep, engagement, patterns (evidence,
  counterexamples, confidence, "not causal"), plateau pointer, safety flags, active coach
  constraints.
- `format=json`: `{generatedAt, markdown}` envelope (structured fields can be added
  without breaking consumers).

Errors: `401` bad key · `403` consent · `404` no user.

### POST /coach/notes
Body `{author?: string, content: string (3–2000 chars)}` → `201-ish {ok, id, treatment:
"constraint_not_command"}`. Notes are stored in `CoachNote` and treated by agents as
**constraints layered above WLOS suggestions but below safety rules** — a note that
contradicts a safety floor is surfaced to the user, never silently obeyed
(`coach-interface.md`). Every write is audit-logged with actor `coach`.

### GET /coach/notes
All notes, newest first (includes `active` flag).

### POST /miniapp/verify
Body `{initData: string}` → `200 {valid:true, userId, authDate}` or `401
{valid:false, reason: missing_hash|bad_signature|expired}`. Implements the official
scheme: `secret = HMAC_SHA256(key="WebAppData", bot_token)`; sorted key=value lines;
constant-time hash compare; 1h max age. Unit-tested including tamper and wrong-token
cases (`apps/api/src/initdata.test.ts`).

## Webhook (served by the bot app, not this service)

`POST :8081/webhook/telegram` — grammY `webhookCallback` verifying
`X-Telegram-Bot-Api-Secret-Token` against `TELEGRAM_WEBHOOK_SECRET`; duplicate updates
dropped via `ProcessedUpdate`. See `telegram-integration.md`.

## Operational notes

- Rate limiting: Fastify default + single-consumer reality; add `@fastify/rate-limit`
  before any multi-consumer exposure.
- The API never mutates health data — writes flow through the bot (one input channel, one
  audit trail); the sole exception is coach notes, which are constraints, not data.
- CORS: none needed until the Mini App fetches cross-origin; keep same-origin via reverse
  proxy in production.
