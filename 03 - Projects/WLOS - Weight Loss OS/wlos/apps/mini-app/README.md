# WLOS Mini App — scaffold (Phase 5, WIP)

**Status: honest scaffold.** The vertical slice ships the bot + API first (per spec §13
build order). This folder contains a static, RTL, single-file dashboard shell that:

- runs inside Telegram as a Mini App (`window.Telegram.WebApp`)
- sends `initData` to `POST /miniapp/verify` (already implemented + tested in `apps/api`)
- renders placeholder cards for: today, weight trend, consents, patterns

## What is already real on the backend

| Mini App screen | Backing implementation |
|---|---|
| initData auth | `apps/api/src/initdata.ts` (HMAC-validated, unit-tested) |
| Consent management | `Consent`/`ConsentEvent` tables + bot `/privacy` |
| Patterns review | `Pattern` + corrections via bot `/patterns` |
| Export / delete | bot `/export`, `/delete` |
| Coach report | `GET /coach/report` |

## Next steps (Phase 5)

1. Replace `index.html` with a Vite + React + `react-i18next` RTL app.
2. Wire `GET /miniapp/*` data endpoints (add session issuance after verify).
3. Register the app with @BotFather (`/newapp`) and set `MINI_APP_URL`.

Until then, every Mini App feature has a bot-command equivalent — nothing is blocked.
