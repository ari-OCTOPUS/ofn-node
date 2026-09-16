# Assumptions & Decisions Log

Every non-blocking decision made during the build, with rationale. Blocking questions were
asked and answered by the product owner (2026-07-19): **bot persona = WLOS**, **DB = local
Docker now** (managed comparison in `deployment.md`), **Fugu = enabled from day one**.

## Verified facts (Phase 0)

| # | Fact | Verification |
|---|---|---|
| V1 | Sakana Fugu API is real and OpenAI-compatible: base `https://api.sakana.ai/v1`, models `fugu`, `fugu-ultra`, Bearer auth, optional `reasoning_effort: high\|xhigh` | console.sakana.ai/get-started, fetched 2026-07-19 |
| V2 | Sydney DST 2026: AEDT ends Apr 5, resumes Oct 4 | luxon IANA data; covered by unit tests on both transition days |
| V3 | Telegram bot chats are **not** E2E-encrypted | Telegram docs; drives the neutral-envelope design |

## Documented decisions

| # | Decision | Rationale |
|---|---|---|
| D1 | npm workspaces + tsx runtime (no build step) | Personal-scale simplicity; tsc build stage documented as the multi-user upgrade path |
| D2 | Prisma 7 engine-less client + `@prisma/adapter-pg`; connection URL in `prisma.config.ts` | Prisma 7 removed `url` from schema files; engine-less is the v7 default path |
| D3 | **Spec deviation:** the eight twin tables (`sleep/mood/hunger/craving/stress/energy/focus/motivation_logs`) are one `StateLog` table with a `kind` column | Identical shape ×8 violates DRY; indexed `(userId, kind, dayKey)` serves every query; views can reconstruct per-kind tables if ever needed |
| D4 | Check-in questions live in code (`question-bank.ts`, versioned), instances/responses in DB | Reviewable in git, testable (18 invariant tests), no CMS needed for one user |
| D5 | Safety gate is type-enforced: outbox requires an unforgeable branded `SafetyClearance` | "No agent can bypass the Safety Agent" as a compile-time + runtime property, not a convention |
| D6 | Daily message cap counts **every** outbound kind; only `kind='safety'` bypasses (recorded with `bypassedCap=true`) | Spec §5 "count reminders, check-ins, and coach messages toward the cap" |
| D7 | Sensitive proactive messages use neutral envelope «یک بررسی خصوصی آماده است» + reveal button | Telegram previews mirror message text; this is the only reliable preview control |
| D8 | Deletion = two-step (`/delete` → typed `DELETE ALL`) then **hard purge** via cascade | Single user owns the data; soft-delete retained only for row-level corrections |
| D9 | Deterministic pattern scanner (association templates + lift-over-base-rate) before any LLM involvement | Evidence/counterexample/confidence must be computable and auditable; LLM only narrates |
| D10 | Weekly deep analysis via `fugu-ultra`; routine messages never call an LLM | Cost + latency + determinism; spec §6 LLM-usage policy |
| D11 | BullMQ over Temporal | Sufficient for one user; Temporal documented as scale-up option |
| D12 | Persian digits accepted everywhere on input; output uses Latin digits for numbers with units (`1950 cal`) matching the spec's own examples | Mixed-register product language |
| D13 | Calorie floors 1200 F / 1500 M and deficit ≤ 25% of TDEE, enforced in code and content-guard | ED-safeguard non-negotiables; unsupervised context |
| D14 | `nosleep` command suspends quiet hours until `/setup` re-enables | Spec §5 "Respect /nosleep"; scoped as explicit opt-out, not permanent |
| D15 | Seed data ships a **fictional** user with a built-in sleep→craving association and weekend calorie drift | Lets /weekly, /patterns and the plateau protocol demo real logic |

## Open items (not blocking)

| # | Item | Current stance |
|---|---|---|
| O1 | Sandbox couldn't run Docker/Postgres, so `prisma migrate dev` + seed must first run on the owner's machine | Schema validated via `prisma generate` (full validation); migrations generate on first run |
| O2 | PDF export of the coach report | Markdown + JSON implemented; PDF marked WIP in `coach-interface.md` |
| O3 | Mini App is a scaffold | All features have bot-command equivalents; Phase 5 |
| O4 | Voice-note intake | Deferred; text parsing covers the spec's simple-logging decision |
| O5 | Fugu pricing/rate limits | Not published on the fetched page; token budget guard (`FUGU_MONTHLY_TOKEN_BUDGET`) protects cost blind-spots |
| O6 | Wearable integrations (Apple Health / Google) | Out of scope per product owner config (manual /steps, /sleep) |
