# WLOS — Weight Loss OS (WLOS-Sydney-1)

Private, persistent, mixed Persian/English AI weight-management system on Telegram for a
single user in Sydney. Gym + calorie coaching, non-clinical behavioral psychology,
JITAI-style randomized check-ins, plateau investigation, cannabis-aware personalization
(consent-gated), safety-first by construction. **Not a medical service.**

> این اپ جایگزین مشاورهٔ پزشکی، روان‌شناسی یا تغذیهٔ تخصصی نیست. /crisis برای منابع اضطراری استرالیا.

## Quick start (local)

```bash
# 0. prerequisites: Node ≥20, Docker
cp .env.example .env               # fill TELEGRAM_BOT_TOKEN (BotFather) + SAKANA_API_KEY
npm install

# 1. infrastructure
docker compose up -d postgres redis

# 2. database
npx prisma migrate dev --name init  # creates schema (first run generates the migration)
npm run seed                        # optional: fictional demo user with 45 days of data

# 3. run (three processes, or `docker compose up -d --build` for everything)
npm run bot      # Telegram bot (polling in dev)
npm run worker   # check-in scheduler (BullMQ)
npm run api      # coach + Mini App API on :8080

# tests / typecheck
npm test         # 135 unit tests
npx tsc --noEmit
```

Production (webhook mode, single VPS): see `docs/deployment.md`.

## Monorepo map

| Path | What |
|---|---|
| `apps/telegram-bot` | grammY bot + outbox (the only send path) + BullMQ worker |
| `apps/api` | Fastify: /coach/report, /coach/notes, /miniapp/verify, /health |
| `apps/mini-app` | RTL dashboard scaffold (Phase 5; every feature has a bot equivalent) |
| `packages/shared` | Sydney-DST-safe time, Persian utils, seeded RNG, config, fa catalog |
| `packages/nutrition-engine` | BMR/TDEE/target ranges + ED floors, trends, observed TDEE, meal parser |
| `packages/training-engine` | readiness safety gate, gym/home/travel/10-min templates, progression |
| `packages/safety` | fa/en crisis triage, outbound content-guard, unforgeable SafetyClearance, AU resources |
| `packages/jitai-engine` | randomized day planner, pre-send re-evaluation, backoff, utility score |
| `packages/behavior-engine` | 257-question tagged bank + consent/cooldown-aware selection, COM-B→BCT menu |
| `packages/agents` | plateau protocol, pattern scanner (evidence/counterexamples), reports, self-mod proposals, LLM prompts |
| `packages/memory` | Prisma 7 client, repositories, LLM context-packet firewall |
| `packages/fugu-provider` | Sakana Fugu (OpenAI-compatible), mock, fallback chain, circuit breaker, redaction |
| `prisma/` | schema (~36 models) + seed |
| `docs/` | 17 documents (architecture, safety, privacy, plateau, deployment…) |
| `todo/` | approved self-modification proposals of category prompt/code land here as tasks |

## Acceptance criteria — status

| # | Criterion | Status |
|---|---|---|
| 1 | Runs locally + prod via Docker | ✅ compose (postgres/redis/migrate/bot/worker/api/backup); *end-to-end Docker run still needs your machine — this workspace had no Docker daemon* |
| 2 | Mixed Persian/English replies | ✅ fa catalog + examples per spec |
| 3 | Daily count never exceeds cap | ✅ ledger-enforced in outbox; tested |
| 4 | Nothing 00:00–07:00 Sydney except urgent | ✅ outbox + planner + re-evaluation; DST-tested |
| 5 | Australia/Sydney incl. DST | ✅ luxon; tests on both 2026 transition days |
| 6 | Food = name + calories; photos rejected | ✅ parser + explicit photo refusal |
| 7 | Patterns: confidence, evidence, user correction | ✅ scanner + /patterns confirm/reject |
| 8 | Cannabis OFF by default, explicit consent | ✅ three consent layers, tested |
| 9 | Self-mod proposals user-approved | ✅ proposals + guardrails (cap≤20, no safety weakening); apply-flow wiring in /weekly is minimal |
| 10 | Export + delete | ✅ /export JSON, /delete + typed confirm |
| 11 | Weekly coach report | ✅ /coach/report md+json (PDF = open item O2) |
| 12 | Fugu failure ≠ coaching failure | ✅ fallback chain + deterministic paths, tested |
| 13 | Crisis language → resources | ✅ fa/en triage, crisis mode, AU numbers |
| 14 | No API keys in git | ✅ env-only, .env gitignored |
| 15 | Backups configured + tested pre-launch | ⚠️ nightly dump container shipped; restore drill documented — run it before launch (`docs/deployment.md`) |
| 16 | Calculations unit-tested | ✅ 135 tests across 10 suites |
| 17 | No sensitive notification previews | ✅ envelope + reveal flow |

## Safety architecture in one paragraph

Inbound: owner-filter → idempotency → deterministic fa/en triage (crisis pauses coaching
and shows 000/Lifeline/Beyond Blue/Butterfly). Outbound: every message needs a branded
`SafetyClearance` that only the safety package can mint; the outbox then applies crisis
mode, pause/snooze, quiet hours, the 20/day cap, and neutral envelopes for sensitive
content. The LLM (Sakana Fugu) sees only consent-filtered, redacted, task-specific
packets and its output goes back through the same guard. Floors (1200/1500 kcal) live in
the arithmetic itself.

## Docs

Start with `docs/product-requirements.md` → `docs/architecture.md`. Changelog in
`CHANGELOG.md`. Every material assumption in `docs/assumptions.md`.
