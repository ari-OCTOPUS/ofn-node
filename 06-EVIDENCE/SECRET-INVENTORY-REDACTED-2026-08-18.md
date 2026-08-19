---
type: evidence
created: 2026-08-18
updated: 2026-08-18
tags: [ops, secrets, inventory, redacted, node-180]
author: "OCTOPUS ARCHITECT WORKSTATION — names and locations only"
---

# Secret inventory (redacted) — 2026-08-18

**Rule:** names and filesystem locations only. No values, no prefixes, no lengths of secrets, no bearer material, no `.env` bodies.

Host `DESKTOP-KA9RFN5`. Classification of the secrets SoT: **MUST_STAY_ON_LAPTOP** until a Promotion Receipt. This agent did **not** copy secrets to `.180`.

## Files that hold secrets (SoT)

| Location | Role | Notes |
|---|---|---|
| `F:\backup\.env` | vault organism / Telegram / LLM / mail | loaded by `env_loader` from `RUN-ORGANISM.bat` comment |
| `F:\backup\.env.bak-20260810` | backup of vault `.env` | present; do not commit |
| `F:\backup\_ops\OCTOPUS.env` | board-cp bearer + bind/url + miniapp flag | parsed by `RESTART-BOARDCP.ps1` and `board_cp/server.py` |
| `F:\backup\4d_system\.env` | 4d daemon LLM + Telegram | cwd of pid 24588 |
| `C:\Users\Armin\.octopus-signing\octopus-owner-ed25519-private.pem` | TCB signing private key | exists; **never copy** |
| `F:\backup\_ops\owner-signing\octopus-owner-ed25519-public.pem` | TCB verify public key | not a secret; listed for pairing |
| `F:\backup\_ops\state\board_cp\tls\key.pem` | board-cp TLS private key | exists with `cert.pem` |
| `F:\backup\_ops\state\board_cp\tls\cert.pem` | board-cp TLS cert | public-ish; pin target for boards |
| `C:\Users\Armin\.cloudflared\f62ab442-7292-4f42-beb5-b4af4c88c3ae.json` | named-tunnel credentials | used by `cloudflared … octopus-miniapp` |
| `C:\Users\Armin\.cloudflared\cert.pem` | cloudflared account cert | present |

## Explicitly not secret (tracked / flags)

| Location | Role |
|---|---|
| `F:\backup\_ops\owner-verdicts.yaml` | owner knobs; contract forbids secrets |
| `F:\backup\_ops\OCTOPUS-flags.cmd` | non-secret flag overrides (`set KEY=VALUE`); gitignore because it *might* grow a secret — treat as sensitive anyway, **do not dump** |
| `F:\backup\4d_system\.env.example` | names only template |
| `F:\backup\4d_system\config\trust-boundary.json` | digests + public key path |
| `F:\backup\4d_system\config\trust-boundary.json.sig` | signature bytes (not the private key) |

## Key **names** observed (values never recorded)

### `F:\backup\.env`

`POCKETSMITH_API_KEY` · `FUGU_API_KEY` · `SAKANA_API_KEY` · `ZAI_API_KEY` · `GLM_API_KEY` · `DEEPSEEK_API_KEY` · `TELEGRAM_BOT_TOKEN` · `TELEGRAM_OWNER_CHAT_ID` · `TG_ZIMAN_STUDIO_BOT_TOKEN` · `TG_ZIMAN_STUDIO_ALLOWED_IDS` · `TG_CENTER_BOT_TOKEN` · `TG_CENTER_CHAT_ID` · `GMAIL_ADDRESS` · `GMAIL_APP_PASSWORD` · `OCTOPUS_CB_SECRET` · `OCTOPUS_DOCTOR_CHAT_ID` · `OCTOPUS_DOCTOR_TG_MODE` · `OCTOPUS_WIRE_VAULT_RAG`

(`FUGU_API_KEY` name appeared more than once in the key-name scan — duplicate lines possible.)

### `F:\backup\4d_system\.env`

`FUGU_API_KEY` · `FUGU_BASE_URL` · `FUGU_MODEL` · `GLM_API_KEY` · `GLM_BASE_URL` · `GLM_MODEL` · `MOCK_MODE` · `REFERENCE_DIR` · `TELEGRAM_BOT_TOKEN` · `TELEGRAM_CHAT_ID` · `SELF_CODE_ENABLED` · `LLM_DAILY_CALL_CAP` · `NOTIFY_MAX_PER_DAY` · `DAEMON_TICK_SECONDS`

### `F:\backup\_ops\OCTOPUS.env` (names)

`OCTOPUS_PF_MINIAPP` · `OCTOPUS_BOARD_CP_BEARER` · `OCTOPUS_BOARD_CP` · `OCTOPUS_BOARD_CONTROL_URL` · `OCTOPUS_BOARD_CP_PORT` · `OCTOPUS_BOARD_CP_BIND`

Presence-only (no values): `OCTOPUS_BOARD_CP_BEARER` is **set**; `OCTOPUS_BOARD_CONTROL_URL` is **set**.

### Names referenced in code / BAT (may live in `.env` or process env)

`HH_HUMAN_GUARD_SECRET` · `OCTOPUS_BOARD_CP_DB` · `OCTOPUS_BOARD_CP_TLS_DIR` · `OCTOPUS_MINIAPP_URL` · `OCTOPUS_MINIAPP_HOSTNAME` · `OCTOPUS_SMTP_USER` · `OCTOPUS_SMTP_HOST` · `OCTOPUS_SMTP_FROM` · `OCTOPUS_SMTP_PORT` · `OCTOPUS_IMAP_USE_GMAIL` · `OCTOPUS_SMTP_USE_GMAIL`

4d daemon **process env key names** also included `ANTHROPIC_BASE_URL` · `API_TIMEOUT_MS` · `FUGU_API_KEY` · `GLM_API_KEY` (values not recorded).

### `_ops/OCTOPUS-flags.cmd`

Hundreds of `OCTOPUS_*` / `CORTEX_*` / `OLLAMA_*` **flag names**. Not listed in full here (not secret by contract). Treat the file as machine-local SoT for wires. Do not replicate blindly to `.180` (autonomy drift).

## Credential classes vs migration

| Class | Locations | Move heuristic |
|---|---|---|
| Canonical vault secrets | `F:\backup\.env` | MUST_STAY_ON_LAPTOP |
| 4d daemon secrets | `4d_system/.env` | MUST_STAY_ON_LAPTOP |
| Board-cp bearer + TLS key | `OCTOPUS.env` + `tls/key.pem` | MUST_STAY until redesigned command authority |
| TCB private key | user profile `.octopus-signing\` | MUST_STAY_ON_LAPTOP |
| Cloudflare tunnel json | `.cloudflared\*.json` | MUST_STAY / redesign (account-bound) |
| Telegram bot tokens | vault `.env` names above | MUST_STAY (two pollers = 409) |
| LLM provider keys | vault + 4d `.env` | MUST_STAY; provisioning to `.180` is owner work, not agent copy |
| Gmail app password | `GMAIL_APP_PASSWORD` in vault `.env` | MUST_STAY |
| PocketSmith | `POCKETSMITH_API_KEY` | MUST_STAY |
| SMB passwords on boards | mentioned in alignment note as board-local `/root/.smbcred` | **not read**; not on this inventory disk as SoT |

## Redaction / ignore

- `.agentignore` / gitignore cover `.env` and similar — do not echo bodies into HANDOFF or chat.
- `ofn-bearer.key` / `secrets-export/` on boards: **not opened**.
- Process environment dumps were filtered to **key names** only.
