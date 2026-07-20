# Fugu Integration

Sakana Fugu is WLOS's deep-reasoning provider — verified real (July 2026) via the official
console: OpenAI-compatible API at `https://api.sakana.ai/v1`, Bearer auth with
`SAKANA_API_KEY`, models `fugu` (default) and `fugu-ultra` (deep), optional
`reasoning_effort: high|xhigh`. Product owner decision: **enabled from day one**, with the
absolute requirement that all basic coaching survives total provider failure.

## Division of labor

| Work | Engine |
|---|---|
| Calorie math, trends, targets, scheduling, safety, parsing, reports | deterministic code — never an LLM |
| Weekly synthesis (10-question review) | `fugu-ultra`, `PROMPT_WEEKLY_SYNTHESIS`, JSON output |
| Plateau narration (status is immutable input) | `fugu`, `PROMPT_PLATEAU_DEEP_DIVE` |
| COM-B barrier analysis (menu-constrained BCT picks) | `fugu`, `PROMPT_BARRIER_ANALYSIS` |
| Plan/message critique | `fugu`, `PROMPT_CRITIC` |

Expected volume: a handful of calls per week. `FUGU_MONTHLY_TOKEN_BUDGET` (default 2M
tokens) is a hard stop enforced *before* each request.

## Request pipeline

```
task → memory selection (task-relevant only)
     → packet firewall (needs[] allowlist + consent exclusion + size cap)   memory/packet.ts
     → redactIdentifiers (emails/phones/ids/handles/names)                  fugu-provider/redact.ts
     → FuguProvider.reason({system, packet, model, jsonMode})               fugu-provider/fugu.ts
     → zod-parse JSON → deterministic content-guard on any user-facing text
     → outbox (SafetyClearance required)
```

Fugu never owns memory, never sees raw history, never receives identifiers, and never has
tool access. `LlmCall` records provider/model/purpose/dataCategories/tokens/latency/ok —
not content, not chain-of-thought (prompts explicitly request conclusions only).

## Resilience (all unit-tested with a mocked fetch)

- Timeout 45s via AbortController; retries ×2 with exponential backoff + jitter on
  408/429/5xx.
- Circuit breaker: 3 consecutive failures → open 60s → half-open probe.
- `FallbackChain`: fugu → (optional OpenAI/Anthropic when keys provided) → typed failure.
- Failure taxonomy: `disabled | no_key | timeout | http_error | circuit_open |
  budget_exceeded | invalid_response` — callers branch to rule-based output on any of
  them; `/weekly` renders the full deterministic report regardless.
- `MockProvider` powers tests and LLM-free development.

## Configuration

```
FUGU_ENABLED=true
SAKANA_API_KEY=            # console.sakana.ai/api-keys — secret manager in prod
SAKANA_BASE_URL=https://api.sakana.ai/v1
FUGU_MODEL_DEFAULT=fugu
FUGU_MODEL_DEEP=fugu-ultra
FUGU_MONTHLY_TOKEN_BUDGET=2000000
```

Base URL and model names are config, not code — if Sakana revises endpoints, this is a
one-line change. Fugu's "custom model pool" (excluding specific downstream providers) can
be set in the Sakana console; WLOS doesn't depend on pool composition.

## Prompt-side safety

`WLOS_SYSTEM_CORE` embeds the non-negotiables (no diagnosis, floors, no shame, cannabis
neutrality, hypothesis-vs-fact language, Persian-forward output, no CoT exposure) into
every call — but the *enforcement* remains the deterministic guard on the way out. The
LLM is advisory; the guard is law. Known cost blind-spot: Fugu pricing/rate limits weren't
published on the fetched page (`assumptions.md` O5) — the token budget guard caps exposure.
