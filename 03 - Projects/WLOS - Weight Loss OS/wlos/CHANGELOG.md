# Changelog

## 0.1.1 — 2026-07-19 · full debug pass (9 fixes)

- **critical** worker: weekly-nudge job re-ran the day planner every Sunday 18:00
  (queue worker ignored `job.name`) → branch on name; nudge is now one outbox-gated message.
- **critical** `planUserDay` made idempotent — double-runs can no longer duplicate check-ins.
- **critical/security** added `.dockerignore` — `.env` (secrets) and `node_modules` were
  being baked into the Docker image by `COPY . .`.
- **build** Dockerfile copies `prisma/` + `prisma.config.ts` before `npm ci` so the
  `postinstall` prisma generate works in-image.
- **ops** backup container cron string used `%%H:%%M` (compose doesn't interpolate `%`) —
  backups would never fire; fixed to `%H:%M`.
- **ops** `env_file` now `required: false` — `docker compose up -d postgres redis` works
  before `.env` exists.
- **logic** `/steps <n≤10>` wrote a 0–10 StateLog instead of a steps summary; steps now
  parsed first with its own range guard + Persian-digit normalization.
- **UX** implemented the promised >3000 kcal confirm flow: resend with «تایید»/confirm →
  saved with `confirmedHigh=true`; catalog text updated with an example.
- **cleanup** sex-callback endsWith trap, static `InputFile` import, dead `void` refs,
  unused imports. Re-verified: 135/135 tests, tsc clean, compose syntax valid.
- Added `HANDOFF.md` for the next agent.

## 0.1.0 — 2026-07-19 · initial vertical slice (WLOS-Sydney-1)

### Verified (Phase 0)
- Sakana Fugu API confirmed real & OpenAI-compatible (`https://api.sakana.ai/v1`,
  `fugu`/`fugu-ultra`) — product owner enabled it from day one.

### Added — engines (all unit-tested, 122 tests total)
- `shared`: Sydney-DST-safe time (tested on both 2026 transitions), Persian digit/text
  normalization, seeded RNG, zod config, Persian message catalog.
- `nutrition-engine`: Mifflin-St Jeor, TDEE ranges, calorie targets with ED floors
  (1200F/1500M, ≤25% deficit), protein/fiber targets, rolling averages with gaps,
  slope/trend classification, observed-TDEE with quality gates, fa/en meal & weight parser.
- `safety`: fa/en inbound triage (crisis/urgent/caution), outbound content-guard
  (sub-floor calories, starvation, purge, medication, cannabis-instruction hard-block;
  shame/detox/diagnosis logged), unforgeable `SafetyClearance` brand, AU resources.
- `jitai-engine`: randomized slot planner (jitter, min-gap, risk windows, quiet hours by
  construction — 1000-seeded-day invariant test), pre-send re-evaluation, ignore-backoff,
  utility scoring.
- `behavior-engine`: 257-question tagged bank (13 domains, consent-gated K/F domains),
  selection engine (consent/cooldown/prereq/contraindication/permanent-refusal),
  COM-B→BCT vetted intervention menu.
- `training-engine`: readiness gate (impairment → never loaded training), gym A/B,
  home/travel/minimum-dose templates, double progression + deload.
- `agents`: plateau protocol (6-gate, never cuts calories first), association scanner
  with lift-over-base-rate confidence, daily/weekly/coach report builders, self-mod
  proposal drafting with guardrails, Fugu prompt set.
- `fugu-provider`: FuguProvider (timeout/retry/circuit/budget), MockProvider,
  FallbackChain, identifier redaction.
- `memory`: Prisma 7 engine-less client (pg adapter), repositories, consent-aware LLM
  packet firewall.

### Added — apps
- Telegram bot: onboarding FSM, 20+ commands, free-text meal logging, photo refusal,
  crisis interception, consent toggles, pattern corrections, export/delete, outbox with
  cap/quiet/envelope enforcement; polling + webhook modes.
- Worker: BullMQ planner (00:05 Sydney) + delayed dispatch with re-evaluation + mid-day
  catch-up + ignored-sweep.
- API: /health, consent-gated /coach/report (md/json), /coach/notes (constraints),
  /miniapp/verify (HMAC initData, tested).
- Mini-app: RTL scaffold (Phase 5) with backend verify wired.

### Added — data & ops
- Prisma schema (~36 models) with dayKey convention, provenance fields, append-only
  consent/audit/safety trails; seed with fictional 45-day plateau dataset.
- docker-compose (postgres, redis, migrate, bot, worker, api, nightly 02:30 backup),
  Dockerfile, .env.example.
- 17 docs incl. threat model, evaluation plan, deployment comparison, plateau protocol.

### Known gaps (tracked in docs/assumptions.md)
- O1 migrations/seed need first run on a machine with Docker (sandbox had no daemon).
- O2 coach-report PDF; O3 Mini App UI; O4 voice intake; O5 Fugu pricing unknown → token
  budget guard; self-mod approve/apply buttons minimal in /weekly.
