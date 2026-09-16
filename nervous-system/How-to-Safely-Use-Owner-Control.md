# How to Safely Use Owner Control · OCTOPUS

> **Purpose:** A runbook for the owner (human-in-the-loop) on how to interact with the OCTOPUS control plane without accidentally triggering live execution.
> **Scope:** Telegram commands, approval queue, batch actions, and emergency stops.
> **Last updated:** Wave 6 (2026-07-13)

---

## 1. Mode Labels Decoded

Every control surface in OCTOPUS has a mode label. These are not decorative — they are safety boundaries.

| Label | Meaning | What You Can Do | What You Cannot Do |
|---|---|---|---|
| **READ-ONLY** | Display only. Zero mutations. | View data, refresh page, copy text | Execute, approve, delete, send |
| **SHADOW MODE** | Advisory display. No live effects. | View recommendations, see blockers | Trades, mining commands, transfers |
| **PROPOSE-ONLY** | Logs intent. Does NOT execute. | Click buttons, log proposals | See actual effects without further approval |
| **OWNER VERDICT** | Requires your explicit ✅/❌. | Approve or deny individual items | Batch-approve all (intentionally blocked) |
| **NOT YET WIRED** | Stub. No backend connection. | Nothing (safely) | Nothing unsafe (because nothing works) |

---

## 2. Telegram Commands (Safe Surface)

The following commands are registered in the bot and are safe to use:

| Command | Mode | What It Does | Risk |
|---|---|---|---|
| `/status` | READ-ONLY | Shows system vitals | None |
| `/queue` | READ-ONLY | Shows approval queue snapshot | None |
| `/approvals` | READ-ONLY | Shows recent approval history | None |
| `/risk` | READ-ONLY | Shows risk radar summary | None |
| `/help` | READ-ONLY | Lists all commands with modes | None |
| `/refresh` | PROPOSE-ONLY | Logs intent to refresh data; does NOT execute | Low (intent logged, no auto-execution) |

**Important:** No command from this list executes irreversible actions. All irreversible actions (spending approval, mining start, wallet transfer) require clicking ✅/❌ on a dedicated approval card with an anti-forgery token.

---

## 3. Approval Queue — How to Verdict

When an item appears in the queue:

1. **Read the details.** Check amount, source, rationale, time-in-queue.
2. **Check the mode label.** If it says DRY-RUN, this is a shadow proposal — no money is at risk yet.
3. **Decide individually.** Each item must be approved or rejected one by one.
4. **Never batch-approve.** The "تأییدِ همه" button is intentionally disabled and shows a warning. This is by design (INV-13).

---

## 4. Emergency Stop

If you need to halt the system immediately:

1. Create the file `_ops/STOP-TG-CENTER` (empty file) — stops the Telegram center loop
2. Create the file `_ops/STOP-ORGANISM` (empty file) — stops the organism heartbeat
3. Both are kill-supreme: the system checks for these files on every cycle and exits cleanly.

---

## 5. Credential Safety

- **Never** paste tokens into chat, HTML, or markdown notes.
- **Only** put secrets in `F:/backup/.env` (already in `.gitignore`).
- The system reads tokens via `env_loader.py`. No hardcoded secrets exist in code.
- If you rotate a token, delete the old one from `.env`, replace it, and restart.

---

## 6. Rollback Awareness

Every action is classified by rollbackability:

| Class | Examples | Can You Undo? |
|---|---|---|
| **Reversible** | Refresh data, toggle panel, copy text | Yes, automatically or by reloading |
| **Irreversible** | Approve spending, execute command, delete data | No — think carefully before ✅ |
| **Requires Manual** | Mining start, wallet transfer, Telegram send | Yes, but requires manual steps |
| **Unknown** | New untested actions | Do not approve without review |

---

## 7. Reporting Issues

If you see:
- A button that suggests execution but is not wired → Report as "control illusion"
- A stale data indicator (>45 min) → Run `refresh-live-data.bat`
- A security warning from `security-checklist.py` → Rotate affected credentials immediately
- An unexpected approval request → Reject it and check the audit trail

---

> **Remember:** The system is designed to be fail-closed. When in doubt, it defaults to **no-op**. Your explicit ✅ is the only path to live execution.
