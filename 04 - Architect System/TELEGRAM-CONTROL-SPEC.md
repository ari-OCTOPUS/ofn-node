---
title: Telegram Control Spec
status: active
created: 2026-07-12
updated: 2026-07-12
tags: [octopus, telegram, spec, wave-6, security]
backlinks:
  - "[[WAVE-6-WORKING-NOTE]]"
  - "[[OCTOPUS-CHANNEL-REGISTRY]]"
---

# Telegram Control Spec (CH-15b)

> Safe command surface for the OCTOPUS Telegram bot. Every command has an explicit mode label. No command executes irreversible actions without owner verdict.

## Command Surface

| Command | Mode | Safety Label | Description | Wired |
|---|---|---|---|---|
| `/status` | READ-ONLY | فقط نمایش — هیچ اثری ندارد | System vitals summary | Partial (alias of /now) |
| `/queue` | READ-ONLY | فقط نمایش — هیچ اثری ندارد | Approval queue snapshot | Stub |
| `/approvals` | READ-ONLY | فقط نمایش — هیچ اثری ندارد | Recent approval history | Stub |
| `/risk` | READ-ONLY | فقط نمایش — هیچ اثری ندارد | Risk radar summary | Stub |
| `/help` | READ-ONLY | فقط نمایش — هیچ اثری ندارد | Command list with mode badges | Stub |
| `/refresh` | PROPOSE-ONLY | ثبتِ intent — اجرا بعد از تأییدِ مالک | Request data refresh (logs intent only) | Stub |

## Commands from Existing Code

| Command | Source | Mode | Note |
|---|---|---|---|
| `/now` | `center.py` | READ-ONLY | Implemented — returns status |
| `/start`, `/overview`, `/money`, `/doctor`, `/brain`, `/blueprint`, `/school`, `/safety`, `/alerts` | `approval_channel.py` | READ-ONLY | Menu navigation |
| `/queue` | `approval_channel.py` | READ-ONLY | Shows approval queue |
| `/status` | `approval_channel.py` | READ-ONLY | Organism status |
| `/lead` | `approval_channel.py` | PROPOSE-ONLY | Lead intake (requires owner) |
| `/reentry` | `approval_channel.py` | PROPOSE-ONLY | Re-entry package |
| `/stop` | `approval_channel.py` | OWNER VERDICT | Kill-switch — requires explicit confirmation |

## Safety Boundaries

1. **No live execution from web UI.** The admin-telegram panel displays commands but cannot trigger them.
2. **Owner allowlist.** Only the configured `owner_chat_id` can issue commands or click approval buttons.
3. **Quarantine.** All inbound messages are logged as DATA, not commands, until explicitly routed.
4. **Token isolation.** `TELEGRAM_BOT_TOKEN` is read from env only. No hardcoded tokens. No tokens in logs.
5. **Fail-closed.** If token is missing, all methods are no-op safe.

## Credential Injection Process

1. Owner creates `.env` file in vault root (`F:/backup/.env`)
2. Adds `TELEGRAM_BOT_TOKEN=<token>` and `TELEGRAM_OWNER_CHAT_ID=<chat_id>`
3. `.env` is in `.gitignore` — never committed
4. `env_loader.py` reads `.env` at runtime (idempotent, no overwrite if already in os.environ)
5. `approval_channel.py` and `tg_api.py` read token from env via `os.environ.get()`
6. Masked token (`****`) shown in repr/error messages only

## Architecture

```
Owner Message → Telegram API → poll_once() → allowlist check → quarantine log
                                          ↓
                                    handle_command() / dispatch_callback()
                                          ↓
                                    center.py beat / approval_channel.py card
```

## File References

- `_ops/telegram_center/center.py` — Hub: setup, beat, status, digest
- `_ops/telegram_center/tg_api.py` — Thin HTTP client (stdlib urllib)
- `_ops/telegram_center/render.py` — HTML/text rendering, containment
- `_ops/budget/approval_channel.py` — Approval channel, long-poll, command router
- `nervous-system/extract_telegram_commands.py` — Command registry extractor
- `nervous-system/telegram-commands-data.js` — UI data payload
