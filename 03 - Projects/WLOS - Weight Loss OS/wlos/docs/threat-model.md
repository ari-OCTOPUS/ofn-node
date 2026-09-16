# Threat Model

Practical, STRIDE-informed threat model for WLOS-Sydney-1: a single-user system whose data is intimate (weight, mood, eating patterns, cannabis use) even though its blast radius is one person. The design bias is structural enforcement over policy: unforgeable types, deterministic gates, and idempotency keys rather than "the agent should remember to". Mitigations cite real code and schema; residual risks are stated honestly at the end.

## Assets

| Asset | Where it lives | Sensitivity notes |
|---|---|---|
| Health data (weight, meals, workouts, state logs) | PostgreSQL 16, Sydney region | Intimate; low external value, high personal cost if exposed |
| **Cannabis data** (`CannabisEvent`, domain-K answers) | PostgreSQL, consent-gated | **Legally sensitive in NSW** — recreational use/possession is a criminal offence; these records could be self-incriminating evidence. Consent OFF by default, soft-delete + purge path, never in message previews, excluded from LLM packets without consent *and* task need |
| Psych observations (`BehavioralObservation`, `BehavioralFormulation`, `Pattern`) | PostgreSQL, `sensitive` flag | Misreadable out of context; psychology consent scope gates use |
| Telegram bot token | Env / secret manager | Full control of the bot = ability to read/send as WLOS |
| `SAKANA_API_KEY` / `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` | Env / secret manager | Billing abuse; provider account access |
| `COACH_API_KEY` | Env / secret manager | Write access to `CoachNote` constraints |
| Chat history on the phone / Telegram cloud | User device + Telegram servers | Outside WLOS's perimeter; see product stance below |

## Trust boundaries

1. Phone ↔ Telegram apps (device compromise, shoulder surfing)
2. Telegram platform ↔ WLOS backend (webhook ingress; Bot API chats are **not** E2E-encrypted)
3. Backend ↔ Sakana Fugu (redacted packets out, untrusted text back)
4. Backend ↔ coach endpoint (authenticated third party, limited trust)
5. Backend ↔ PostgreSQL/Redis (managed infra)

## Threats and mitigations

| # | Threat | STRIDE | Mitigations |
|---|---|---|---|
| 1 | Stolen/borrowed phone reads chat & notifications | I | Neutral lock-screen previews (`OutboundMessage.preview` is *exactly* what may appear; `neverInNotificationPreview` questions use envelope+reveal); `/pause` stops sending; Telegram device-session review/terminate; raw detail stays in backend |
| 2 | Telegram platform-side access to bot chats | I | Product stance below: minimize sensitive words in transit; Mini App for sensitive review |
| 3 | Webhook spoofing (fake updates to prod endpoint) | S | `TELEGRAM_WEBHOOK_SECRET` set at `setWebhook`; every request's `X-Telegram-Bot-Api-Secret-Token` header checked, mismatch rejected; polling in dev has no ingress |
| 4 | Update replay / duplicate delivery | T, D | `ProcessedUpdate` keyed by Telegram `update_id` — replays are no-ops; outbound ledger prevents duplicate sends |
| 5 | Prompt injection via user text → LLM | T, E | Packet firewall + no tools + clearance gate (below) |
| 6 | LLM provider data handling (Sakana) | I | `redactIdentifiers` strips emails/phones/IDs/handles/IPs/names as the last step; consent+need category exclusion in `buildContextPacket` (max 6000 chars); no raw chat history ever sent; chain-of-thought neither requested nor stored; `LlmCall` audits *categories*, not content |
| 7 | Database compromise | I, T | Managed PostgreSQL 16 in Sydney region, TLS connections, backups encrypted at rest, least-privilege DB role, no public DB exposure; soft-delete + `DeletionRequest` purge keeps the corpus prunable |
| 8 | Coach endpoint abuse | S, E | `COACH_API_KEY` on every request + rate limiting; `CoachNote` content is treated as **constraints, not commands** — a note can tighten coaching but cannot instruct agents to bypass floors, guard, or consent |
| 9 | Supply-chain (malicious/compromised dependency) | T | Committed `package-lock.json`; scheduled `npm audit` cadence; small dependency surface; upgrades reviewed, not auto-merged |
| 10 | Secrets in git | I | `.gitignore`d env files; repo carries `.env.example` placeholders only; production secrets in a secret manager, never in images or logs |
| 11 | Availability loss (Redis/PG/LLM/host down) | D | Single-user tolerance: downtime misses check-ins, it doesn't harm; Docker restart policies; BullMQ retries; Fugu circuit breaker (3 failures → open, 60s cooldown) + `FallbackChain` + deterministic rules keep coaching alive through full LLM outage |

### STRIDE summary

| STRIDE class | Primary controls in WLOS |
|---|---|
| **S**poofing | Webhook secret-token header check; single-owner `TelegramAccount.chatId` binding; `COACH_API_KEY` |
| **T**ampering | `ProcessedUpdate` idempotency; unforgeable `SafetyClearance` (branded symbol); deterministic guard un-influenceable by prompts; lockfile |
| **R**epudiation | Append-only `AuditLog`, `ConsentEvent`, `SafetyEvent`, `LlmCall`, `OutboundMessage` ledger |
| **I**nformation disclosure | Packet firewall + redaction; consent scopes; neutral previews; Mini App for sensitive review; encrypted managed PG |
| **D**enial of service | 20/day cap (with `bypassedCap` audit), circuit breaker + fallback chain, BullMQ retries, monthly token budget capping cost-DoS |
| **E**levation of privilege | LLM has no tools; coach notes are constraints-not-commands; `SelfModProposal` requires explicit user approval; safety cannot be bypassed by any agent (clearance is the only send path) |

Note the deliberate asymmetry in bypass rules: **safety messages** may bypass the daily cap and quiet hours (recorded via `OutboundMessage.bypassedCap`), while **nothing** may bypass the clearance gate or consent scopes — bypass privileges flow toward user protection only, never away from it.

## Stance: Telegram is not end-to-end encrypted

Bot API conversations are encrypted client↔server, but Telegram (and anyone with lawful or unlawful access to its servers) can read them. This is a **documented product trade-off**, accepted for exactly one user who chose Telegram as the interface. Consequences engineered into the product:

- Outbound messages minimize sensitive vocabulary; the backend holds raw detail, the chat holds the minimum working phrasing (`OutboundMessage.sensitivity` tracked per message).
- High-sensitivity questions are flagged `neverInNotificationPreview` and use an envelope+reveal flow.
- The Mini App (served from WLOS infrastructure, `initData`-validated) is the intended surface for reviewing sensitive history — especially cannabis and psychology data — so that detail never transits chat at all.
- Export (`DataExportJob`) and delete (`DeletionRequest`: confirm → purge) are bot commands, so the user can evacuate or destroy backend data without asking anyone.

## Stance: prompt injection and the clearance gate

Assume any LLM output may be attacker-influenced, because user text (and text the user pastes) reaches the model. Defense is structural, in three layers:

1. **Packet firewall** (`packages/memory/src/packet.ts`): the model only ever sees a task-scoped packet — `needs`-allowlisted categories, consent-gated sensitive sections, budget-capped, identifier-redacted. Injected text cannot exfiltrate what was never in the packet, and system prompts contain no secrets worth revealing.
2. **No tool calls**: WLOS LLM tasks are text-in/text-out. There is no function-calling surface, so "ignore instructions and call X" has nothing to call.
3. **Clearance gate** (`packages/safety/src/clearance.ts`): the outbox refuses any message not wrapped in a `SafetyClearance`, and the only constructor is `clearOutbound()`, whose brand is an unexported `unique symbol` — unforgeable from outside the safety package, deterministic, and therefore not prompt-injectable. Hard-blocking violations (sub-floor calories, starvation, purge, medication advice, cannabis instructions) replace the text with a safe fallback: «این پیشنهاد از فیلتر ایمنی WLOS رد نشد و ارسال نشد.»

Inbound, `triageInbound` runs before any LLM sees the text, so crisis handling never depends on model cooperation.

## Cross-cutting controls

- **Append-only audit**: `AuditLog`, `AgentRun` (summaries, never chain-of-thought), `LlmCall`, `SafetyEvent`, `ConsentEvent` give repudiation-resistant history for a one-person ops team.
- **Cap as damage limiter**: the 20/day outbound cap (safety-only bypass, `bypassedCap`) bounds the harm of any scheduler bug or compromised generator to annoyance, not floods.
- **Self-modification governance**: `SelfModProposal` cannot self-apply; every change needs explicit user approval and carries a rollback plan — an attacker steering the weekly loop still hits a human gate.

## Operational practices

- **Secrets**: bot token, `SAKANA_API_KEY`/`OPENAI_API_KEY`, and `COACH_API_KEY` live only in the secret manager (prod) or local `.env` (dev); rotate immediately on any suspicion — with one user, rotation costs minutes. `.env.example` carries placeholders only.
- **Dependencies**: `npm audit` on the weekly cadence defined in `docs/evaluation-plan.md`; upgrades are read before merged. Prisma 7's engine-less client (pg adapter) keeps the DB driver surface small and auditable.
- **Backups**: encrypted at rest; a backup that has never been restored is a hypothesis — drill a restore quarterly alongside the threat-model review.
- **Logs**: `AgentRun.summary` holds concise rationale only, never chain-of-thought; application logs must not contain message bodies, tokens, or identifiers (the same redaction discipline as LLM packets).

## Out of scope

Accepted as non-goals for a single-user personal system: nation-state attackers, compromise of Telegram's client applications themselves, physical coercion of the user, and the user acting against their own data (they are the principal — `/export` and `/delete` exist precisely so the system never holds data *against* them). Lawful compulsion overlaps with residual risks below.

## Residual risks (accepted, honestly)

| Risk | Why it remains |
|---|---|
| Telegram server-side access | Unfixable while Telegram is the interface; mitigated by vocabulary minimization + Mini App, not eliminated |
| LLM provider jurisdiction | Redacted packets are processed by Sakana AI outside Australia under their terms; redaction reduces identifiability, but content is still content. `FUGU_ENABLED=true` from day one is a product-owner decision, revisitable per task category |
| Phone compromise (unlocked device) | Full chat history readable until the user wipes sessions; WLOS can only shape what was ever put in chat |
| Single developer | No independent code review; compensated by deterministic gates, typed clearance, and test suites — compensation, not equivalence |
| NSW legal exposure of cannabis records | Consent-gating, purge paths, and packet exclusion reduce surface; a lawful seizure of the DB or the phone could still reach them. The user owns this trade-off knowingly |

Review this document whenever a new ingress, provider, or data category is added — and after any incident, per `docs/evaluation-plan.md`.
