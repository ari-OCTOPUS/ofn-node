---
title: PROVIDER-INVENTORY
lane: API-BUDGET-ACTIVATION-20260913
date: 2026-09-13
authority: "OCTOPUS — SECURE CREDENTIAL REDISCOVERY (owner authorization, read-only)"
method: read-only
secrets_exposed: none
final_status: MULTI_PROVIDER_PARTIAL_RECOVERY
---

# PROVIDER-INVENTORY — OCTOPUS external model providers

**خلاصهٔ فارسی (TL;DR):** روی همهٔ سطوح مجاز جست‌وجو شد. فقط **یک** اعتبارنامهٔ مدلِ پولی
پیدا شد (Sakana/Fugu) که زیر **سه نام متغیر مختلف** تکرار شده و **هر سه یک مقدار دارند**.
آداپتور DeepSeek در کد هست ولی **کلید ندارد**. مدل محلی نود ۱۸۰ فعال و بدون کلید است.
هیچ کلید OpenAI / Anthropic / Gemini / Groq / OpenRouter / Mistral / xAI روی سطوح
OCTOPUS وجود ندارد. اعتبارنامهٔ جدیدی ساخته نشد و **هیچ مقدار کلیدی خوانده/چاپ/کپی نشد**.

## 0. Rules honored during this inventory

| Constraint | Status |
|---|---|
| No credential value printed / logged / returned | HELD |
| No credential copied or moved | HELD |
| No new credential created | HELD |
| No service modified | HELD |
| No service restarted | HELD |
| No paid API call made | HELD (DNS resolution only, zero cost) |
| No credential file rewritten | HELD |

## 1. Surfaces searched (authorized list)

| Surface | Result |
|---|---|
| `A` `/home/ari/.config/ofn/` (138) — `.env`, `.json`, `.bak` variants | 22 files: **21 at mode `600`**, 1 at `644` (`identity.json` — name-level scan found no credential variable in it); 1 model credential family found |
| `B` systemd on 138 (`ofn.service`, drop-ins, bridge, alert, backup, …) | `EnvironmentFile=-/home/ari/.config/ofn/node.env` + `secrets.env`; no provider keys outside those files |
| `C` OCTOPUS repo + lane worktrees (env-var names / adapters only) | adapters found; **no** committed plaintext credential |
| `D` node 180 via 138 (`root@192.168.0.180`, mesh key) | cognition broker + local llama.cpp; **no** external provider key |
| `E` node 191 | not contacted (retired-until-provisioned) |
| `F` PC/vault known OCTOPUS paths (`F:\backup`, `F:\ofn-node`, `F:\wt-*`) | no provider credential; only a secret-read deny hook |
| agent config surfaces (`~/.claude`, `~/.codex`, `~/.zcode`, `~/.cursor`) | one **personal subscription OAuth** credential (see P-05); no provider API key |

Node 138 egress check (DNS only, no HTTP, no billing): `api.sakana.ai`, `api.deepseek.com`,
`api.openai.com`, `api.anthropic.com`, `generativelanguage.googleapis.com` → **all RESOLVE**.

## 2. Provider records

### P-01 — `sakana-fugu` (Sakana AI, model family `fugu`)

| Field | Value |
|---|---|
| Provider ID | `sakana-fugu` |
| Adapter / code path | `/home/ari/ofn/ofn/helpers/brainport.py` (BrainPort, provider-swappable stub) · `/home/ari/ofn/ofn/adapters/remote_brain.py` (RemoteBrain — the real caller) · `/home/ari/ofn/state/api-budget/api_budget.py` (paid_call, provider string `sakana-fugu`) |
| Expected env-var names | `SAKANA_API_KEY`, `FUGU_API_KEY` (brainport), `OFN_REMOTE_API_KEY` (`ofn/config.py:286` → RemoteBrain → ModelRouter rungs) |
| Optional base-URL var | `SAKANA_BASE_URL` (brainport:29) · `OFN_REMOTE_BASE_URL` (`config.py:292`) · default `https://api.sakana.ai/v1` |
| Expected model-name var | **NONE** — no `*_MODEL` env var is consumed anywhere. Models are literals: `fugu` (standard), `fugu-ultra` (deep). The broker takes its model from contract `model_allowlist[0]` = `fugu` |
| Adapter status | **VERIFIED_LIVE** — code exercised end-to-end; ledger rows exist. Provider currently answers `fugu:usage-limit` ⇒ also **ACCOUNT_LIMIT_REACHED** |
| API shape | **OpenAI-compatible** (`POST {base}/chat/completions`). Provider-specific extras encoded in code: `orchestration_tokens` in `usage` (may be absent), long timeouts (deep model up to 900 s) |
| Health check (no credential exposure) | `getent hosts api.sakana.ai` → RESOLVES (zero cost). Key-in-process metadata check would be `GET {base}/models` — **not implemented**; existing probe `/home/ari/ofn/deploy/brain-probe.py` makes a real billable call, so it is not used here |
| Price / accounting | **AVAILABLE (conservative book price)** — contract `book_usd_per_mtok: 20.0` × `orchestration_multiplier: 2.6`; provider-reported visible tokens + orchestration tokens are parsed. Provider-side invoice price is **not verifiable from this repo** |
| Recommended routing role | paid fallback (`fugu`) and strong-reasoning rung (`fugu-ultra`) — i.e. current `Rung.REMOTE` / `Rung.REMOTE_DEEP` |
| Credential file already contains required key name? | **YES** — `/home/ari/.config/ofn/secrets.env` contains `SAKANA_API_KEY`, `FUGU_API_KEY` and `OFN_REMOTE_API_KEY` (all `non_empty=true`, all three in the same duplicate group `DG-1`; values not read out) |

### P-02 — `deepseek`

| Field | Value |
|---|---|
| Provider ID | `deepseek` |
| Adapter / code path | `/home/ari/ofn/ofn/helpers/brainport.py:12-25` (branch selected by `BRAIN_PROVIDER=deepseek`) |
| Expected env-var names | `DEEPSEEK_API_KEY` |
| Optional base-URL var | `DEEPSEEK_BASE_URL` (default `https://api.deepseek.com/v1`) |
| Expected model-name var | **NONE** — literals in code: `deepseek-chat` (standard tier), `deepseek-reasoner` (hard tier). Selector var is `BRAIN_PROVIDER` |
| Adapter status | **CONFIGURED** (code path present and coherent) but no credential ⇒ **ADAPTER_FOUND_NO_CREDENTIAL** |
| API shape | **OpenAI-compatible** (`/chat/completions` via the shared `_openai_compat` helper) |
| Health check (no credential exposure) | `getent hosts api.deepseek.com` → RESOLVES (zero cost). With a key: `GET {base}/models` (metadata, unbilled) — **not implemented in repo** |
| Price / accounting | **NOT WIRED** — the broker's `paid_call()` always instantiates `RemoteBrain` with `c_model()` (fugu); the deepseek branch never reaches the budget ledger. DeepSeek list pricing is **not encoded** in this repo (`unverified`) |
| Recommended routing role | economy paid fallback (`deepseek-chat`), strong-reasoning alternative (`deepseek-reasoner`) |
| Credential file already contains required key name? | **NO** — `DEEPSEEK_API_KEY` is absent from every file under `/home/ari/.config/ofn/` (name-level check only) |

### P-03 — `local-llamacpp-180` (node 180, `qwen3-0.6b-q4_0`)

| Field | Value |
|---|---|
| Provider ID | `local-llamacpp-180` |
| Adapter / code path | `/var/lib/octopus/cognition-broker/cognition_broker.py` (node 180, mode `700`, root) · `/home/ari/ofn/state/coding-worker/coding_worker.py` (local rung on 138) · `LocalBrain` in `/home/ari/ofn/ofn/adapters/remote_brain.py:162` |
| Expected env-var names | **NONE** (no credential; endpoint and model are literals) |
| Optional base-URL var | **NONE** — endpoint literal `LOCAL_LLM = "http://127.0.0.1:8081"` |
| Expected model-name var | **NONE** — literal `qwen3-0.6b-q4_0` |
| Adapter status | **VERIFIED_LIVE** (no credential needed) |
| API shape | **Provider-specific** — llama.cpp native `POST /completion` with `n_predict`, `cache_prompt`, `stop: ["\n"]`. (llama.cpp also exposes an OpenAI-compatible surface, but the code uses the native one) |
| Health check (no credential exposure) | `curl -s http://127.0.0.1:8081/health` from node 180 — no auth, no cost |
| Price / accounting | **ZERO COST** — not billed, not in the paid ledger |
| Recommended routing role | **FIRST rung, always** (`LOCAL_FIRST_PAID_FALLBACK`, contract `mode`) |
| Credential file already contains required key name? | N/A — no credential exists or is required |

### P-04 — `huggingface` (reference only)

| Field | Value |
|---|---|
| Provider ID | `huggingface` |
| Adapter / code path | **ABSENT** — no adapter, no consumer |
| Expected env-var names | `HF_TOKEN` (name appears only in `docs/octopus-os/07-INCIDENTS.md:120`) |
| Optional base-URL var | none consumed |
| Expected model-name var | none consumed |
| Adapter status | **ABSENT** ⇒ `CREDENTIAL_REFERENCE_ONLY` |
| API shape | n/a (would be provider-specific Hub API) |
| Health check | n/a |
| Price / accounting | n/a |
| Recommended routing role | none |
| Credential file already contains required key name? | **NO** — documented as **expired 2026-09-02T09:15Z**; incident note states no local HF key was found and the expired item was a cloud-agent OAuth session |

### P-05 — `anthropic-claude-subscription` (owner personal OAuth — **do not auto-register**)

| Field | Value |
|---|---|
| Provider ID | `anthropic-claude-subscription` |
| Adapter / code path | **ABSENT** — no OCTOPUS adapter; no consumer found for the discovered variable name anywhere under `/home/ari` or `/etc` |
| Expected env-var names | `E_CODE_OAUTH_TOKEN` (present in `/home/ari/.config/ofn/claude.env`, mode `600`). PC side holds a personal CLI OAuth blob in `~/.claude/.credentials.json` |
| Optional base-URL var | none consumed |
| Expected model-name var | none consumed |
| Adapter status | **ABSENT** ⇒ `CREDENTIAL_FOUND_NO_ADAPTER` |
| API shape | **Provider-specific** — Anthropic Messages API; the discovered item is a **subscription OAuth token, not an API key** |
| Health check | not attempted (would require transmitting a personal subscription token) |
| Price / accounting | **NOT APPLICABLE** — subscription, not metered API; no price could be booked without violating the budget contract's assumptions |
| Recommended routing role | none until an owner decision; if ever approved, only as an independent review provider |
| Credential file already contains required key name? | **N/A — reuse forbidden by standing owner rule** ("Do not reuse an owner's broad personal token"). Classified `CREDENTIAL_EXPOSURE_REQUIRES_ROTATION`-adjacent: it sits in an approved surface at mode 600, but it is a *personal subscription* credential, so it is **excluded from automatic broker registration** and needs a separate explicit owner decision (and a ToS check) before any adapter is written |

### P-06 — `octopus-bridge` (internal control plane — not a model provider)

| Field | Value |
|---|---|
| Provider ID | `octopus-bridge` |
| Adapter / code path | `/home/ari/octopus-bridge/octopus_bridge/config.py:206-209`, `connector.py:82` |
| Expected env-var names | `OCTOPUS_BRIDGE_API_KEY` |
| Optional base-URL var | `OCTOPUS_BRIDGE_CONTROL_URL` |
| Expected model-name var | none |
| Adapter status | **CONFIGURED** (internal, not a model route) |
| API shape | provider-specific internal gateway |
| Health check | not attempted |
| Price / accounting | n/a — internal |
| Recommended routing role | **none** — must never be used as a model route |
| Credential file already contains required key name? | YES — `/home/ari/.config/ofn/octopus-bridge.env` (mode `600`) |

### Non-model credentials present (out of scope for model routing)

`OFN_BOT_TOKEN_OWNER|LEAD|STUDIO|STUDIO_PARTNER|ZIMAN` (Telegram) ·
`OFN_SHOPIFY_ADMIN_TOKEN`, `OFN_SHOPIFY_CLIENT_ID`, `OFN_SHOPIFY_CLIENT_SECRET` ·
`GMAIL_ADDRESS`, `GMAIL_APP_PASSWORD` (SMTP, consumed by `ofn/agents/mail_credentials.py`) ·
`OFN_SESSION_SECRET`, `OFN_REMOTE_API_KEY` (see P-01) · one PC-side MCP OAuth set
(third-party MCP servers — **not** model providers; identifiers withheld).

## 3. Discovery table (secret-free)

| Provider | Variable name(s) | Location | Status |
|---|---|---|---|
| `sakana-fugu` | `SAKANA_API_KEY`, `FUGU_API_KEY`, `OFN_REMOTE_API_KEY` | `/home/ari/.config/ofn/secrets.env` | `CREDENTIAL_FOUND_SECURE` + `ACCOUNT_LIMIT_REACHED` (duplicate group `DG-1`) |
| `deepseek` | `DEEPSEEK_API_KEY`, `DEEPSEEK_BASE_URL` | — (none present) | `ADAPTER_FOUND_NO_CREDENTIAL` |
| `local-llamacpp-180` | — | node 180 `:8081` | `VERIFIED_LIVE` (no credential) |
| `huggingface` | `HF_TOKEN` | docs only (expired) | `CREDENTIAL_REFERENCE_ONLY` |
| `anthropic-claude-subscription` | `E_CODE_OAUTH_TOKEN` | `/home/ari/.config/ofn/claude.env` (mode 600) + PC CLI store | `CREDENTIAL_FOUND_NO_ADAPTER` — **reuse forbidden pending owner decision** |
| `octopus-bridge` | `OCTOPUS_BRIDGE_API_KEY` | `/home/ari/.config/ofn/octopus-bridge.env` | internal, `CREDENTIAL_FOUND_SECURE`, not a model route |

## 4. Findings that change what you should do next

**F-1 — There is exactly ONE paid model credential on the entire authorized surface.**
`SAKANA_API_KEY`, `FUGU_API_KEY` and `OFN_REMOTE_API_KEY` are **the same value**
(verified in-memory; only the equality boolean was computed, nothing was printed).
So "diverse providers" are **not reachable as credentials yet**: the organism has one
account and that account answers `usage-limit`. A different egress IP cannot help —
the limit is account-level, and the broker's billed windows are already conservative
(`$0.0632` reserved of `$20` window-1).

**F-2 — Latent key-selection bug (worth fixing before you add a second key).**
`api_budget.py:222-228` (`load_key`) returns the **first line that matches any of the three
names**, in file order. Today that is harmless because all three hold the same value.
The moment you add a *fresh* key under one name while a stale key remains in another
(e.g. new `SAKANA_API_KEY` while old `OFN_REMOTE_API_KEY` still sits above it), the broker
will silently keep using the stale one. Recommended fix: prefer an explicit
`BRAIN_PROVIDER`/provider→variable mapping instead of first-match-on-name.

**F-3 — A new env file alone activates nothing.** The broker reads exactly one path:
`SECRETS = Path("/home/ari/.config/ofn/secrets.env")` (`api_budget.py:39`), and
`ofn.service` loads only `node.env` + `secrets.env` via `EnvironmentFile=`.
So `external-models.env` must either be **appended into `secrets.env`**, or the broker
must be changed to read it as an additional source (plus an `EnvironmentFile=` line) —
that is a code change and was **not** performed here (read-only directive).

**F-4 — No `*_MODEL` environment variable exists anywhere.** Every model name is a literal
or contract value. The template therefore contains **no** invented model variable.

## 5. Stop conditions — which ones are currently triggered

| Stop condition | Applies to |
|---|---|
| Provider reports usage limit | `sakana-fugu` (P-01) — **triggered**; do not retry blindly |
| Adapter sends credentials to an unverified endpoint | none — base URLs are code literals |
| Registering would expose the credential to WILD / generated code | none — the broker keeps the key in-process |
| Credential is a broad personal token | `anthropic-claude-subscription` (P-05) — **triggered** |
| Credential only in chat/log/history | none found |
| Provider cannot be identified | none |
| File permissions unsafe | **none for credential-bearing files** — 21 of 22 files under `/home/ari/.config/ofn/` are mode `600` (hardened 2026-09-13); the single `644` file is `identity.json`, which holds no credential variable |

## 6. Status

**`MULTI_PROVIDER_PARTIAL_RECOVERY`** — the local model route is live, one paid adapter is
live but account-limited, one paid adapter is code-complete but key-less, and everything
else is absent. **One owner action remains** (see `external-models.env.template`).
