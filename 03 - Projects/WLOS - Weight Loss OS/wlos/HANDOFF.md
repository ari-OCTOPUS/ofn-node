# HANDOFF — for the next agent

**Project:** WLOS (Weight Loss OS, WLOS-Sydney-1) · **State:** v0.1.1, vertical slice complete & debugged · **Date:** 2026-07-19

Read order: this file → `docs/product-requirements.md` → `docs/architecture.md` → `docs/assumptions.md` (all decisions D1–D15, open items O1–O6).

## 1. Verified state (do not re-litigate, re-verify)

```
npm install            # postinstall runs `prisma generate`
npm test               # 135/135 tests, 10 suites — ALL GREEN
npx tsc --noEmit       # 0 errors (TypeScript 7, strict)
docker compose config  # syntax valid (works without .env; secrets never baked into image)
```

Never run live here: real Telegram polling (needs owner's `TELEGRAM_BOT_TOKEN`), `prisma migrate dev` + seed (needs running Postgres), full `docker compose up` (build sandbox had no daemon). These are the FIRST things to do on a machine with Docker.

## 2. Debug pass just completed (v0.1.1) — what was found & fixed

| # | Severity | Bug | Fix |
|---|---|---|---|
| 1 | critical | Weekly-nudge cron job landed in the `wlos-plan` queue whose worker ignored `job.name` → every Sunday 18:00 the day-planner re-ran | worker branches on `job.name`; nudge now sends one outbox-gated coach message |
| 2 | critical | `planUserDay` not idempotent → any double-run (cron + boot catch-up race, restarts) duplicated check-ins | guard: skip if any `CheckinInstance` exists for `(userId, dayKey)` |
| 3 | critical/security | No `.dockerignore` → `COPY . .` baked **`.env` (bot token, API keys)** and host `node_modules` into the image | `.dockerignore` added (.env, node_modules, .git, backups, generated) |
| 4 | build | `postinstall: prisma generate` broke Docker `npm ci` (prisma/ not yet copied) | Dockerfile copies `prisma/` + `prisma.config.ts` before `npm ci` |
| 5 | ops | Backup container used `date +%%H:%%M` — compose doesn't interpolate `%`, cron string compared against literal `%H:%M` → **backups never fired** | single `%` |
| 6 | logic | `/steps 8` hit the generic 0–10 scale branch first → wrote `StateLog(kind='steps')` instead of steps summary | steps handled first, own range guard, Persian digits normalized |
| 7 | UX/promise | `MEAL_TOO_HIGH` promised a «تایید» confirm flow that didn't exist | implemented: resend with «تایید/confirm» → accepted, `confirmedHigh=true` |
| 8 | fragile | `data.endsWith('male')` sex-parse trap (`'female'.endsWith('male')===true`), dynamic `InputFile` imports, dead `void x` refs, unused imports | all cleaned |
| 9 | ops | compose hard-failed without `.env` even for `up -d postgres redis` | `env_file: {path: .env, required: false}` |

All 135 tests + typecheck re-verified green after these fixes. Commits: `326ab87` (v0.1.0), `9ea187d` (postinstall), then the v0.1.1 debug commit.

## 3. Invariants you must not break (tested and/or structural)

1. **Outbox is the only send path.** `sendViaOutbox` requires a branded `SafetyClearance` mintable only by `@wlos/safety.clearOutbound()`. Never add a raw `api.sendMessage` call site (the two `ctx.replyWithDocument` export flows + post-deletion farewell are the sanctioned exceptions).
2. **Cap 20/day counts every kind; only `kind='safety'` bypasses** (recorded `bypassedCap=true`). Quiet hours 00:00–07:00 Sydney; `quietSuspended` only via `/nosleep`.
3. **One question per check-in message.** Selection returns 0 or 1. Ever.
4. **Consent gates in three layers** (question selection, pattern templates, LLM packet firewall) — keep all three when adding features; tests pin each.
5. **Plateau protocol never cuts calories first**; floors 1200F/1500M live in `calorieTargetRange` AND the content-guard.
6. **LLM is advisory, guard is law.** Fugu output re-passes `clearOutbound`. Fugu never gets identifiers, raw history, or unconsented categories.
7. **dayKey = Sydney-local day everywhere.** Use `localDayKey`/`utcAtLocalMinutes` (clock-time semantics — already DST-tested). Never `new Date().toISOString().slice(0,10)` for user-facing days.
8. **Self-mod proposals never auto-apply**; `validateApplication` blocks cap>20, safety weakening, code/prompt execution.

## 4. Repo map (117 TS files; also see README table)

```
apps/telegram-bot/src: bot.ts(routing+middleware) outbox.ts(THE gate) onboarding.ts
                       commands.ts checkins.ts(plan/dispatch/sweep) worker.ts(BullMQ) main.ts
apps/api/src:          main.ts(coach+miniapp endpoints) initdata.ts(+test)
apps/mini-app:         scaffold only (Phase 5)
packages/shared:       time.ts persian.ts rng.ts types.ts config.ts i18n/fa.ts
packages/nutrition-engine: calculations.ts trends.ts meal-parser.ts
packages/safety:       triage.ts content-guard.ts clearance.ts resources.ts
packages/jitai-engine: scheduler.ts utility.ts
packages/behavior-engine: question-types.ts selection.ts comb.ts data/question-bank.ts(257q)
packages/training-engine: readiness.ts templates.ts progression.ts
packages/agents:       plateau.ts patterns.ts reports.ts self-mod.ts prompts.ts
packages/memory:       client.ts repos.ts packet.ts (+generated prisma client, gitignored)
packages/fugu-provider: fugu.ts chain.ts circuit.ts mock.ts redact.ts types.ts
prisma/: schema.prisma(~36 models) seed.ts   docs/: 17 files   todo/: self-mod task drop
```

## 5. Next tasks, in order (owner-approved roadmap)

1. **First live run** (owner machine): `.env` → `docker compose up -d postgres redis` → `npx prisma migrate dev --name init` → `npm run seed` → `npm run bot|worker|api` → test `/start`…`/weekly` end-to-end. Fix whatever only-live-Telegram reveals (callback payload length limits, RTL rendering quirks).
2. **Backup restore drill** before real use — `docs/deployment.md` §backup (acceptance #15 is ⚠️ until done).
3. **Wire Fugu weekly synthesis call**: `agents/prompts.ts` + `fugu-provider` are ready; add the weekly job step (worker) building a packet via `memory/packet.ts` → `FallbackChain.reason` → zod-parse → append LLM narrative to `/weekly` when `ok`. Everything already degrades without it.
4. **Self-mod approve/reject inline buttons** in `/weekly` (drafting + guardrails exist in `agents/self-mod.ts`; persistence model `SelfModProposal` exists; only the button wiring + `todo/` file writer remain).
5. **Mini App Phase 5** (`apps/mini-app/README.md` has the plan; `/miniapp/verify` is done+tested).
6. **PDF coach report** (O2), voice intake (O4), managed-DB migration when leaving local Docker (`docs/deployment.md` comparison, data must stay ap-southeast-2).

## 6. Gotchas the hard way taught us

- **Prisma 7:** no `url` in schema — it lives in `prisma.config.ts`; generator is engine-less `prisma-client` with `output=packages/memory/src/generated`; runtime needs `@prisma/adapter-pg`. In restricted networks the CLI still tries to fetch schema-engine → workaround used here: `PRISMA_SCHEMA_ENGINE_BINARY=<stub>` (not needed on normal machines).
- **luxon DST:** `plus({minutes})` is elapsed time, NOT clock time — that bug was caught by the 2026-10-04 test. `utcAtLocalMinutes` uses `.set({hour,minute})` on purpose.
- **BullMQ:** one queue per job family OR branch on `job.name` — never assume a queue has one job type (bug #1 above). `jobId: ci-<instanceId>` gives dispatch dedupe.
- **Telegram previews mirror message text** — sensitivity='high' auto-wraps in the neutral envelope; reveal stash lives in `Memory(layer=dynamic_state, key=reveal:<msgId>)`, 24h expiry.
- **zod v4, vitest v4, TS 7** — pinned in package.json; zod v3 syntax used is compatible.

## 7. Working method expected by the owner

Persian-forward replies to the owner; English code/docs. Ask only blocking questions; document non-blocking decisions in `docs/assumptions.md`. Run `npm test` + `npx tsc --noEmit` after every material change. Never claim a feature works without code + tests + run instructions. Keep `CHANGELOG.md` current. Never commit secrets; never auto-apply self-mod proposals; never weaken a safety invariant (§3).
