# WLOS Architecture

## Shape

npm-workspaces TypeScript monorepo. Engines are pure, deterministic, unit-tested packages;
apps are thin I/O shells. LLM reasoning is an optional layer that can vanish without
breaking coaching.

```
apps/
  telegram-bot/   grammY bot (polling dev / webhook prod) + BullMQ worker
  api/            Fastify :8080 — coach endpoints, Mini App initData verify
  mini-app/       static RTL scaffold (Phase 5)
packages/
  shared/           tz (DST-safe Sydney), Persian utils, seeded RNG, config, fa catalog
  nutrition-engine/ BMR/TDEE/targets(+floors), rolling averages, trends, observed TDEE, meal parser
  training-engine/  readiness gate, session templates, double progression
  safety/           inbound triage (fa/en), outbound content-guard, SafetyClearance brand, AU resources
  jitai-engine/     day planner (slots+jitter+risk windows), re-evaluation, backoff, utility score
  behavior-engine/  257-question bank, selection engine, COM-B→BCT menu
  agents/           plateau protocol, pattern scanner, reports, self-mod proposals, LLM prompts
  memory/           Prisma client (v7, engine-less, pg adapter), repositories, context-packet firewall
  fugu-provider/    BrainProvider, FuguProvider, MockProvider, FallbackChain, circuit breaker, redaction
prisma/           schema (~36 models) + seed
```

## The two invariant chokepoints

**Inbound** — middleware order in `bot.ts` is a safety property:

```
owner-filter → update-id idempotency → safety triage → routing
```

Crisis-level text short-circuits everything: resources sent, `crisisModeUntil` set,
ordinary coaching suppressed until `/resume`.

**Outbound** — `outbox.ts` is the only send path in the codebase:

```
SafetyClearance (unforgeable) → crisis check → pause/snooze/stop-today
→ quiet hours (00:00–07:00 Sydney) → 20/day hard cap → envelope-if-sensitive → send + ledger
```

`kind='safety'` bypasses cap and quiet hours; every bypass is recorded
(`OutboundMessage.bypassedCap`). Nothing else can bypass anything — the clearance token is
a branded type whose constructor lives only in `@wlos/safety`.

## Scheduling dataflow

```
00:05 Sydney (BullMQ cron, tz-aware)
  └─ planner: sweepIgnored → planDay(seeded RNG) → CheckinInstance rows
       └─ delayed dispatch jobs (jobId = ci-<instanceId>, idempotent)
            └─ dispatch: shouldStillSend? → selectQuestion (consent/cooldown/contraind.)
                 └─ outbox → sent | cancelled(reason)
```

Seed = `f(userId, dayKey)` → reproducible randomness: same day replans identically,
different days differ. Backoff halves check-in probability after 2 ignored prompts and
recovers +0.25 per answered one.

## Memory & LLM boundary

DB is the only long-term memory. Before any Fugu call:

```
task → needs[] (category allowlist) → consent filter → size budget → redactIdentifiers → packet
```

`LlmCall` logs purpose + included categories (never content, never chain-of-thought).
`FallbackChain`: fugu → (optional others) → failure object; callers must branch to
rule-based output. Circuit breaker (3 failures → open 60s), retries with jittered backoff,
monthly token budget hard-stop.

## Data model conventions

- `dayKey` (YYYY-MM-DD, Sydney-local) precomputed on every daily fact; all UTC instants kept too.
- Health events carry `occurredAt/recordedAt/source/confidence` provenance.
- Patterns: unique `(userId, antecedent, outcome)`, evidence + counterexamples + confidence,
  `notCausal=true`, `userVerdict` overrides the machine.
- Append-only: `ConsentEvent`, `AuditLog`, `SafetyEvent`, `MemoryVersion`.

## Agent inventory vs spec §6

Deterministic code: Orchestrator (bot routing), Safety/Triage, Onboarding, Nutrition,
Training, JITAI, Memory, Pattern Discovery, Notification (outbox), Privacy/Consent,
Report, Self-Modification, Escalation (resource routing). LLM-assisted (prompts in
`agents/prompts.ts`, all output re-guarded): weekly synthesis, plateau narration, COM-B
barrier analysis (menu-constrained), Critic. Cannabis-aware and Sleep/Recovery logic live
inside pattern templates + readiness gate rather than as separate processes — one user,
one process, module boundaries instead of microservices.

## Failure behavior

| Failure | Behavior |
|---|---|
| Fugu/all LLMs down | Deterministic coaching continues; weekly narrative degrades to tables |
| Redis down | Bot replies still work; check-ins pause (worker reconnects; catch-up plan on boot) |
| Postgres down | Bot cannot serve (source of truth) — compose restarts + healthchecks |
| Telegram down | Nothing to do; webhook retries are idempotent via `ProcessedUpdate` |

## Scale-up path (documented, not built)

tsc build stage → multi-user = ownership checks already row-scoped by `userId`; Temporal
for durable workflows; pgvector for semantic memory retrieval (schema keeps `Memory.key`
namespaced for it); OpenTelemetry exporters.
