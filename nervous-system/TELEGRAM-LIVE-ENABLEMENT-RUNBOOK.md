# TELEGRAM LIVE ENABLEMENT RUNBOOK

## What This Is
One-page instruction for the owner to move the Telegram control surface from **shadow** (handlers wired, credentials missing) to **live** (handlers wired, credentials present).

---

## Current State (Verified)

| Component | Status |
|-----------|--------|
| `/status` handler | ✅ implemented in `center.py:_cmd_status` |
| `/queue` handler | ✅ implemented in `center.py:_cmd_queue` |
| `/approvals` handler | ✅ implemented in `center.py:_cmd_approvals` |
| `/risk` handler | ✅ implemented in `center.py:_cmd_risk` |
| `/help` handler | ✅ implemented in `center.py:_cmd_help` |
| `/refresh` handler | ✅ implemented in `center.py:_cmd_refresh` (propose-only) |
| Callback verdicts (ok/no/later) | ✅ implemented in `center.py:_handle_callback` |
| Audit logging | ✅ wired: callbacks and refresh log to `action-audit.jsonl` |
| Approval state machine | ✅ `approval_state_machine.py` — explicit transitions |
| TgClient (Bot API) | ✅ `tg_api.py` — stdlib-only, fail-closed |
| env loader | ✅ `env_loader.py` — reads `.env` from vault root |
| Tests | ✅ 46/46 pass |
| CI gate | ✅ 19/19 schema + UI contract pass |

**The only missing piece is credential injection.**

---

## Step 1: Create `.env` File

Create `F:\backup\.env` with these two lines (and any other keys you already have):

```
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN_HERE
TELEGRAM_OWNER_CHAT_ID=YOUR_NUMERIC_CHAT_ID_HERE
```

**Do NOT commit this file.** `.gitignore` already ignores `*.env`.

### How to get these values

**TELEGRAM_BOT_TOKEN:**
1. Open Telegram, message @BotFather
2. Send `/newbot` or use existing bot
3. Copy the token (looks like `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

**TELEGRAM_OWNER_CHAT_ID:**
1. Open Telegram, message @userinfobot
2. It replies with your numeric ID (e.g., `12345678`)
3. Copy that number

---

## Step 2: Verify env Loader Sees Them

```bash
cd F:\backup\_ops\budget
python env_loader.py
```

Expected output (values hidden, only set/not-set):
```
TELEGRAM_BOT_TOKEN: set
TELEGRAM_OWNER_CHAT_ID: set
```

If either says `not-set`, check the `.env` file path and format.

---

## Step 3: Start the Telegram Center

```bash
cd F:\backup\_ops\telegram_center
python center.py
```

If credentials are present:
```
tg-center: زنده — kill تمیز: فایلِ _ops/STOP-TG-CENTER را بساز
```

If credentials are missing:
```
tg-center: not wired (TELEGRAM_BOT_TOKEN/چت پیکربندی نشده) — خروجِ امنِ no-op
```

---

## Step 4: Verify in Admin Dashboard

Open `F:\backup\OCTOPUS\admin-telegram\index.html` in a browser.

The Telegram panel should now show:
- **🔌 handlers** — `X/Y wired` (green)
- **🔑 creds** — `present` (green)
- **وضعیتِ واقعی** — `✓ handlers wired + creds present`

---

## Step 5: Test Live Commands

In Telegram, send these to your bot:

```
/status
/queue
/risk
/help
```

All should respond immediately (read-only, zero risk).

Test propose-only:
```
/refresh
```
Should reply: "Intent ثبت شد ✅" and create an audit entry.

---

## Safety Checklist Before Going Live

- [ ] `.env` exists and is NOT in git
- [ ] `env_loader.py` reports both keys as `set`
- [ ] `center.py` starts without "not wired" message
- [ ] Admin UI shows `creds: present`
- [ ] `/status` responds in Telegram
- [ ] Non-owner messages are silently ignored (test from another account)
- [ ] `STOP-TG-CENTER` file stops the loop instantly

---

## Rollback

To disable live mode instantly:

1. Create `F:\backup\_ops\STOP-TG-CENTER` (empty file)
2. Or delete/rename `.env`
3. Or revoke the token via @BotFather

Any of these makes the center exit safely on the next poll cycle.

---

## What Happens After Live

| Surface | Mode |
|---------|------|
| `/status` | READ-ONLY live |
| `/queue` | READ-ONLY live |
| `/approvals` | READ-ONLY live |
| `/risk` | READ-ONLY live |
| `/help` | READ-ONLY live |
| `/refresh` | PROPOSE-ONLY live (intent logged, no auto-execution) |
| Callback ✅/❌ | OWNER VERDICT live (records to approval file + audit log) |

**No action executes without owner verdict.** The system remains fail-closed.

---

## Troubleshooting

**"tg-center: not wired"**
→ `.env` not found or keys misspelled. Check `env_loader.py` output.

**"creds: missing" in admin UI**
→ Re-run `refresh-live-data.bat` after creating `.env`.

**Bot responds to `/status` but not callbacks**
→ Ensure the bot has `callback_query` permission. Check @BotFather settings.

**Audit log not growing**
→ Check `_ops/state/action-audit.jsonl` exists and is writable.

---

## File Reference

| File | Role |
|------|------|
| `_ops/telegram_center/center.py` | Main hub — handlers + poll loop |
| `_ops/telegram_center/tg_api.py` | Telegram Bot API client |
| `_ops/budget/env_loader.py` | `.env` reader |
| `nervous-system/extract_telegram_commands.py` | Command registry extractor |
| `nervous-system/audit_logger.py` | Audit trail writer |
| `_ops/state/action-audit.jsonl` | Audit log (append-only) |
| `_ops/state/approval-log.jsonl` | Approval state transitions |

---

*Runbook version: Wave 6+ · Generated: 2026-07-13*
