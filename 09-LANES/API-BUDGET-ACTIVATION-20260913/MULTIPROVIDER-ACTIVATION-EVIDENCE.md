---
title: MULTIPROVIDER-ACTIVATION-EVIDENCE
lane: API-BUDGET-ACTIVATION-20260913
date: 2026-09-13
status: ACTIVATED
final_status: MULTI_PROVIDER_COGNITION_ACTIVE (3 paid live + local; 2 configured-but-blocked)
secrets_exposed: none
authority: "owner message 2026-09-13 — 'من مالکم میپذیرم این توکن هارو برای همیشه ذخیره کن'"
---

# Multi-provider cognition — activation evidence

## 1. Credential file installation

| Check | Result |
|---|---|
| Canonical path | `/home/ari/.config/ofn/external-models.env` |
| Existed before this lane | **NO** — the owner believed it was in place; it was not. Installed from the owner's uploaded copy. |
| Owner / group | `ari:ari` |
| Mode | `600` |
| Size / lines / assignments | 16090 bytes / 353 lines / 187 assignments |
| Line endings | CRLF stripped on install (a `\r` inside a value silently corrupts keys) |
| Integrity | local sha256 `fdde145f2733f104b7824566…` == remote sha256 (file-level hash, not a value) |
| Readable by other users | **no** — `/home/ari/.config` is `700`, so no other local user can traverse to it |

## 2. Providers declared and their measured state

| Provider | Enabled | Key present | Models endpoint | Canary | Status |
|---|---|---|---|---|---|
| `local-llamacpp-180` | yes | n/a (no credential) | n/a | health 200 `{"status":"ok"}` | **LIVE**, $0.00 |
| `gemini` | yes | yes | 200, 50 models | served `gemini-3.8-flash`, $0.00014 | **LIVE** |
| `deepseek` | yes | yes | 200, 2 models | served `deepseek-flash`, $0.00156 | **LIVE** |
| `openai` | yes | yes | 200, 130 models | served `gpt-5.6-terra`, $0.00046 | **LIVE** |
| `sakana-fugu` | yes | yes | 200, 8 models | HTTP 429 `usage_limit_reached` | **ACCOUNT_LIMIT_REACHED** |
| `anthropic` | yes | yes | HTTP 400 | HTTP 400 (workspace scope) | **BLOCKED_WORKSPACE_SCOPE** |
| groq, mistral, xai, cohere, together, openrouter, huggingface, custom1/2 | no | placeholder | not queried | not run | DISABLED by owner config |

**Note on Sakana:** the credential is *valid* (its models list returns 200 with 8 models,
including `fugu`, `fugu-ultra`, `fugu-max`, `fugu-ultra-v2.0`). The account window is
exhausted, so it is skipped by name — not deleted, not rotated.

**Note on Anthropic:** verbatim provider error —
`"This API key is not scoped to a workspace, so this request must include the
anthropic-workspace-id header with the ID of the workspace to use."`
The adapter is ready and will use `ANTHROPIC_WORKSPACE_ID` the moment it exists.

## 3. Discovery-driven model correction

`MODEL_DISCOVERY_REQUIRED=true` in the owner's file was correct: two DeepSeek names did
not exist. Resolved against the provider's own list and recorded in
`config/discovered-models.json` (the owner's credential file was **not** rewritten):

| Provider | Configured | Resolved | Why |
|---|---|---|---|
| deepseek | `deepseek-chat` | `deepseek-flash` | configured name absent from the provider's list |
| deepseek | `deepseek-reasoner` | `deepseek-v4-pro` | configured name absent from the provider's list |
| openai / gemini / sakana | all 4 / 4 / 2 names | unchanged | every configured name verified present |
| local | `qwen3-0.6b-q4_0` | unchanged | base overridden to `http://192.168.0.180:8081` (the env declares `127.0.0.1`, which only resolves on node 180; reachability from 138 verified 200) |

## 4. Adapter defects found and fixed

| Defect | Effect | Fix |
|---|---|---|
| Key was passed inside the child **argv** (`python -c "... api_key='…' …"`) | any local user could read the credential from `ps` | spec is now handed to the child over **stdin**; the key never enters argv |
| `load_key()` scanned env files first-match (defect F-2) | a stale key above a fresh one silently won | explicit provider→variable mapping; no scanning |
| OpenAI's new models reject `max_tokens` | HTTP 400 on every call | per-provider `max_tokens_field` = `max_completion_tokens` for OpenAI |
| `gpt-5.6-terra` rejects any non-default temperature | HTTP 400 `unsupported_value` | temperature omitted for providers flagged `omit_temperature` |
| Anthropic org keys need a workspace header | HTTP 400 | `anthropic-workspace-id` supported when `ANTHROPIC_WORKSPACE_ID` is set |

## 5. Budget integrity (shared global contract, unchanged)

* Contract file untouched: `config/api-budget-contract.json`
  (window1 `$20` → window2 `$20` → steady `$10`/24h, `$2`/task, 3 calls/task,
  concurrency 1, `$100`/month, no rollover, no borrowing, uniform conservative book
  price `$20`/Mtok with a `2.6` orchestration multiplier).
* Per-provider canary cap honoured: at most one canary per provider, `$0.25` cap enforced
  in code (`OCTOPUS_API_CANARY_MAX_USD_PER_PROVIDER`), no canary retried after failure.
* **Self-reported breach:** during diagnosis I made two small OpenAI requests
  (`/chat/completions` and `/responses`, 16 output tokens each) **outside** reserve/settle.
  Both are reconciled into the ledger as explicit reserve+settle pairs
  (`diag-reconcile-openai-chat` / `-responses`, $0.00128 each). Total session spend
  including the reconciliation: **$0.082432** of a $20 window.
* Ledger rows: 33. Clock guard, monotonic high-water and "reservation stays counted on
  failure" semantics are unchanged.

## 6. Active routing

```
chain: deterministic → local-llamacpp-180 → gemini → deepseek → openai → WAITING_COGNITION
skipped by name: sakana-fugu (ACCOUNT_LIMIT_REACHED), anthropic (BLOCKED_WORKSPACE_SCOPE)
```
> ⚠️ این ترتیب، حالتِ **لحظهٔ فعال‌سازی** است. با حکم مالک (§11) پیش‌فرض به `deepseek`
> تغییر کرد و جدول فروزن بازنویسی شد؛ ترتیب جاری:
> `deterministic → local-llamacpp-180 → deepseek → gemini → openai → WAITING_COGNITION`.
* Frozen table: `config/provider-routes.json` (schema `octopus.provider-routes.v1`).
* Measured health: `config/provider-health.json`.
* `paid_call()` now selects by health-aware rank instead of registry order, so a
  non-LIVE provider is never silently chosen. Every selection writes a ledger receipt
  (provider + model + cost), and no fallback happens silently.
* **End-to-end proof:** `activation-proof-20260913` selected `gemini`, served
  `gemini-3.8-flash`, cost `$0.00014`, window spend `$0.082432`.
* **Consumer wiring:** the coding worker now has a paid rung (`paid_fallback`) reached
  only after the local node-180 model fails, capped at `$0.25` per call; the worker can
  neither read a credential nor exceed the cap. Wiring verified with a stubbed broker:
  cap `0.25` enforced, receipt `PAID_FALLBACK_RESPONSE` emitted, **zero spend**.

## 7. Exposure checks

| Check | Result |
|---|---|
| Credential value present in any file under `state/` or `/tmp` | **none** — 758 files scanned, values compared in memory, booleans only |
| Credential in receipts / ledger / health / routes / discovery | none (ledger holds provider, model, token counts, costs — no key material) |
| Credential reachable by WILD | **no** — the WILD runtime has no separate local user; `/home/ari/.config` is `700`; `OCTOPUS_ALLOW_WILD_SECRET_ACCESS=false` |
| Credential reachable by node 182 | **no** — the witness tree contains no reference to `external-models`; no key variable is ever sent to 182 |
| Credential reachable by generated code / worktrees / prompts | no — the broker holds the key in-process and the child receives it over stdin; prompts are pattern-screened (`UNSAFE_PROMPT_REJECTED`) |
| Raw keys visible to agents | `OCTOPUS_API_RAW_KEYS_VISIBLE_TO_AGENTS=false`; public accessors return booleans, model names, URLs and counts only |

## 8. Rollback

```bash
# broker (two stages, newest second)
cp /home/ari/ofn/state/api-budget/api_budget.py.pre-routeorder-20260913 \
   /home/ari/ofn/state/api-budget/api_budget.py
cp /home/ari/ofn/state/api-budget/api_budget.py.pre-multiprovider-20260913 \
   /home/ari/ofn/state/api-budget/api_budget.py
# coding worker
cp /home/ari/ofn/state/coding-worker/coding_worker.py.pre-paidrung-20260913 \
   /home/ari/ofn/state/coding-worker/coding_worker.py
# generated config (remove to disable routing)
rm /home/ari/ofn/state/api-budget/config/provider-health.json \
   /home/ari/ofn/state/api-budget/config/provider-routes.json \
   /home/ari/ofn/state/api-budget/config/discovered-models.json
```
The credential file itself is never deleted by a rollback.

## 9. Deployed hashes

| Artifact | sha256 (first 24) |
|---|---|
| `api_budget.py.pre-multiprovider-20260913` (original) | `41605a6910ba2b6e0434c6eb` |
| `api_budget.py` after multi-provider patch | `a327e79e7a920b90718955f2` |
| `api_budget.py` after route-order patch (current) | `b42cf48ab9a0f7493f293109` |
| `coding_worker.py` (before) | `4c4a1a3f1022c76e550cd13e` |
| `coding_worker.py` after paid rung (current) | `9b85869601acfb02a01c4d98` |
| `providers.py` (new module) | deployed, mode `640` |

## 10. Two owner actions remain (nothing else blocks)

1. **Anthropic workspace ID** — set `ANTHROPIC_WORKSPACE_ID` (value from the Anthropic
   console) in the secure file; the adapter is already wired for it.
2. **Sakana account window** — its credential works; the account is rate/usage limited.
   No action needed unless you want it in rotation immediately.

## 11. Owner decision on the budget — 2026-09-13 (recorded after activation)

The owner was asked directly (as required: budget is not an agent decision) and answered:

| Question | Owner answer | Effect |
|---|---|---|
| Shared budget caps now that three providers are live | **UNCHANGED** | window1 `$20` / window2 `$20` / steady `$10` per 24h / `$100` month / `$2` per task / 3 calls per task / concurrency 1 / no rollover / no borrowing — exactly as the original authorization |
| Default provider for ordinary work | **`deepseek`** (was "cheapest healthy" = gemini) | `ROUTE_RANK` changed to `local → deepseek → gemini → openai → sakana → anthropic`; frozen table rewritten with an `owner_decision` block |

Proof of the new default: task `owner-default-proof-20260913` was served by `deepseek-flash`
(cost `$0.00156`). Session spend is now **`$0.083992`** of window1 (35 ledger rows).

Note the caps are **shared, not per provider**: adding providers did not and cannot raise
them. `no_rollover`, `no_borrowing` and `no_automatic_overage` remain `true`.

## 12. Hazard for future changes
`external-models.env` leaves `FUGU_API_KEY` and `OFN_REMOTE_API_KEY` **empty**, and an
empty value in a later `EnvironmentFile=` shadows an earlier one. It is therefore
**not** added to `ofn.service` on purpose: doing so would blank those two variables and
break the legacy `RemoteBrain` path (which still reads `secrets.env`). If that file is
ever loaded into a service environment, those two names must be filled or removed first.

## 13. Anthropic activation + an exposed credential — 2026-09-13

**Anthropic is now LIVE.** The blocker was never the credential: the stored key was valid,
but an org key that is *not* workspace-scoped must name the workspace on every request.
Adding one **identifier** fixed it:

| Step | Detail |
|---|---|
| Change | `ANTHROPIC_WORKSPACE_ID=wrkspc_018nwWxwbbKqgzZbLsZjMn5N` appended to the secure file (a workspace **identifier**, not a credential) |
| Credential used | the one **already in the secure file**; it was never printed, copied or moved |
| File state after | `owner=ari:ari`, `mode=600` (unchanged) |
| Models endpoint | HTTP 200, **11 models** — including every configured name (`claude-haiku-4-5-20251001`, `claude-sonnet-5`, `claude-opus-5`, `claude-fable-5-1`) |
| Canary | one call, `$0.25` cap, served **`claude-sonnet-5`**, cost **`$0.00052`** |
| Route | now a live candidate: `… → openai → anthropic → WAITING_COGNITION` |

Live set is now **four paid providers + the free local rung**; `sakana-fugu` remains the only
skipped provider (`ACCOUNT_LIMIT_REACHED`). Session spend **`$0.084512`** of window1 (37 rows).

### ⚠️ Exposed credential — rotation required, NOT used

A Claude API key was posted **in a chat transcript** (key id `apikey_01HYoiWGnN2BiBxvDMiy8FD3`,
created 2026-09-13, scope OCTOPUS). Under the standing rules this is
`CREDENTIAL_EXPOSURE_REQUIRES_ROTATION`:

* it was **not read into any OCTOPUS surface**, **not stored**, **not used**, and the successful
  canary above did **not** use it;
* it does not appear in the secure file, the ledger, receipts or evidence;
* the owner should **delete that key in the Anthropic console** and, if a new one is ever needed,
  write it **directly into `/home/ari/.config/ofn/external-models.env`** — never into a chat.

Nothing had to be rotated for OCTOPUS to work: the already-stored credential + the workspace
identifier was sufficient. The exposed key can simply be deleted.
