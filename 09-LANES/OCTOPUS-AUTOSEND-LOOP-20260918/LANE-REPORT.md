# LANE REPORT — OCTOPUS-AUTOSEND-LOOP-20260918

GOV_VERSION=V8 · LADDER=L2 · lane declared at session start · worktree: vault (F:\backup) + board138 runtime

## Owner orders executed this lane
1. «ارسالم یک‌کاری کن اختاپوس خودکار هر وقت نیاز دید تایید بگیره و بفرسته در تلگرام نه من و تو»
2. «GO A7» (swap drill)
3. «من این ایمیل ایرتاسکر رو زدم ببین ایرادش چیه»

## What was done

### A. Autonomous approve→send loop (the owner's ask)
Chain now live: **need → card in Telegram WITH buttons → owner tap → automatic send → receipt → confirmation in Telegram.**

| file (on 138) | change | backup |
|---|---|---|
| `state/revenue-drive/owner_ask.py` | decision id (8 hex) per card, inline keyboard (`✅ تأیید و ارسال ایمیل` / `⛔ رد` / `⏸ بعداً`), Persian rendering for known cards, `%d` placeholder fix, 3-attempt send retry (a transient URLError once ate a real card) | `.bak-buttons-20260917T232557Z`, `.bak-retry-20260917T232844Z`, `.bak-fa-20260917T232901Z` |
| `ofn/agents/glass_runner.py` | `callback_query` updates are now spooled to the MONEY lane (identity+channel in payload) and acked; spool-write failure marks the cycle failed so the offset does not advance (G27 contract kept) | `.bak-callback-20260917T232549Z` |
| `state/revenue-drive/owner_reply.py` | consumes `go:<did>:email` / `no:<did>` / `later:<did>`, resolves the card by registry id (never by wording), dispatches to money_tools, marks registry state, answers the owner in-chat | `.bak-buttons-20260917T232557Z`, `.bak-tweak-*`, `.bak-retry-20260917T232844Z` |
| `/etc/systemd/system/octopus-owner-ask.{service,timer}` | NEW — cards are asked every 10 min without any human trigger | — |

**End-to-end proof (receipts in `state/revenue-drive/receipts.jsonl`):**
- simulated tap → `OWNER_DECISION_READ decision=APPROVE source=callback` → `MONEY_BATCH_EMAIL_SENT sent=["TEST-SELF-2"] failed=[]` → `OWNER_DECISION_EXECUTED` → registry card `EXECUTED`.
- the test mail **arrived** in the inbox: `Repainting quote for SELF-TEST-2 — October schedule` (IMAP-verified).
- both test packets were addressed to our OWN mailbox (no lead was touched); test cards carry `test: true`.

**Live state left behind:** card `MONEY-BATCH` (decision id `d3c0fdea`, 5 real packets, channel=email) is PENDING in the owner's Telegram with its button. One tap sends them for real. Of the 5 packets, 4 have email addresses (Absolute Strata, Ace BCM, Acumen Strata, Alldis & Cox) and `QP-20260917-8458` (Agile Strata) is phone-only → it will be reported as failed with reason `NO_EMAIL_ADDRESS_OR_CREDS`, not silently dropped.

### B. A7 swap drill — PASSED with independent witness
See `06-EVIDENCE/A7-SWAP-DRILL-20260918/RECEIPT.md` (PRE/POST JSON + witness pulse gap 23:29:46Z→23:33:20Z). Swap survived reboot via fstab; 45/45 timers back; nothing lost.

### C. Airtasker email diagnosis
Gmail (metadata-only IMAP read): the only Airtasker-related mail ever is Google's 2026-09-07 "you shared account data with airtasker.com" notice; **no alert mail has ever arrived**, and Sent contains nothing to Airtasker. Our side is ready (airtasker branch live in `imap_listener`, parser tested 8/8). ⇒ the missing piece is on the Airtasker side: the account's notification email and/or the saved alert. Register row A3 updated with the exact owner step.

## What failed / limits
- First self-test run failed with `NO_EMAIL_ADDRESS_OR_CREDS` — that was the harness, not the code: a manual `python3 owner_reply.py` lacks the unit's `EnvironmentFile` (GMAIL_*). Re-run through `systemctl start` proved the production path. Worth remembering for every manual test of a service-shaped loop.
- `systemctl reboot` on 138 logs `dbus-org.freedesktop.login1.service failed to load properly ... File exists`; the reboot still happens (boot_id change + pulse gap). Logind unit-file defect, deferred to a later window.
- A7 has no per-item pre-image for the *very* first card send (dedupe entries for old MONEY-BATCH keys were cleared to allow the button card to be sent — the file is a dedupe log, not a receipt ledger).

## Rollback
- Loop: restore any `*.bak-*` listed above over its file; `sudo systemctl disable --now octopus-owner-ask.timer` removes the new timer.
- Cards already sent to Telegram cannot be unsent; tapping ⛔ رd resolves a card without effect.
- A7: nothing mutated.

## Next (not in this lane)
- Wire the reply-answer producer (customer replies already detected by `reply_alert.py`) into the same card+button mechanism so a customer answer is one tap away.
- A4: masked phone-only lead extraction + SMS card through the same approval loop.
- Fix the logind unit-file defect on 138.
