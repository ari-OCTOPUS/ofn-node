# Telegram Integration

## Modes

- **Development:** long polling (`TELEGRAM_MODE=polling`). `main.ts` deletes any webhook
  then `bot.start()`.
- **Production:** webhook (`TELEGRAM_MODE=webhook`). Fastify on :8081 at
  `/webhook/telegram`; `setWebhook` registers `TELEGRAM_WEBHOOK_URL` with
  `secret_token`, and grammY's `webhookCallback(..., { secretToken })` rejects requests
  whose `X-Telegram-Bot-Api-Secret-Token` doesn't match.

## Hard security properties

| Property | Mechanism |
|---|---|
| Single-user lock | `TELEGRAM_OWNER_CHAT_ID` filter; non-owner updates ignored silently |
| Private chats only | `chat.type !== 'private'` dropped — no group leakage possible |
| Idempotency | `ProcessedUpdate(update_id PK)` insert-or-skip before any handler |
| No secrets in git | tokens only via env / secret manager; `.env` gitignored |
| Preview hygiene | sensitive sends use neutral envelope + reveal button (below) |
| Not E2E | documented stance: Telegram bot chats are cloud-encrypted, not E2E — raw sensitive detail stays in the backend |

## Sensitive-message envelope flow

Proactive messages with `sensitivity: 'high'` (all cannabis questions, emotional-context
questions, anything `neverInNotificationPreview`):

1. Outbox sends only: «یک بررسی خصوصی آماده است.» + [نمایش]
2. Real content is stashed in `Memory(layer='dynamic_state', key='reveal:<messageId>')`
   with a 24h expiry.
3. Tapping [نمایش] edits the message in place to the real question + answer buttons.
4. Lock screens therefore never show cannabis/psychology wording. Direct replies to a
   user-initiated command skip the envelope (the user is actively in the chat).

## Commands (registered via `setMyCommands`)

`/start` `/setup` onboarding · `/today` `/plan` status & targets · `/weight` `/meal`
`/workout` `/hunger` `/mood` `/sleep` `/steps` logging · `/report` `/weekly` `/patterns`
insight · `/privacy` `/consent` `/export` `/delete` data rights · `/pause` `/resume`
`/snooze` `/nosleep` flow control · `/help` `/crisis` support.

Free text routing: onboarding FSM first; then the meal parser (any «name + number» is a
meal — the spec's `«شام ماهی و سبزیجات ۵۵۰»` works without a command); photos/documents
get a polite "no photo processing" reply by design.

## Check-in UX rules (enforced in `checkins.ts`)

- Exactly one question per message; quick-answer buttons per response type
  (0-3 / 4-6 / 7-10, بله/نه, choices), plus always: رد کن · بعداً · امروز دیگه نپرس.
- «بعداً» = 60min snooze; «امروز دیگه نپرس» cancels the rest of today's plan
  (`stopForDayKey`); answers reset the ignore-streak and step backoff toward 1.0.
- Every planned instance re-evaluates immediately before sending (`shouldStillSend`) —
  pause, snooze, crisis, cap, quiet hours, or a stale topic cancel it with a recorded
  reason rather than delivering a zombie prompt.

## Rate/cap model

The 20/day cap counts **all** outbound kinds per Sydney-local `dayKey` from the
`OutboundMessage` ledger — not just check-ins. Safety messages bypass but are recorded
with `bypassedCap=true` so the evaluation plan can audit bypasses.

## Mini App

`POST /miniapp/verify` implements the official initData HMAC scheme
(`secret = HMAC_SHA256("WebAppData", bot_token)`), tamper- and expiry-tested in
`apps/api/src/initdata.test.ts`. The UI itself is a Phase-5 scaffold
(`apps/mini-app/`); every Mini App feature has a bot-command equivalent today.
