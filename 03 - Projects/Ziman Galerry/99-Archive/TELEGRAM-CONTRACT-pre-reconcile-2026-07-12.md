---
type: interface
project: ZIMAN
status: proposed
updated: 2026-07-12
---

# TELEGRAM CONTRACT — Ziman limb (dry-run design, NOT live)

Gateway: `_ops/telegram_center/center.py` — leg key `ziman` (exists, VERIFIED).
Activation requires: `TELEGRAM_BOT_TOKEN` + owner allowlist + owner decision. **Not activated by this design.**

## Commands (proposed routing → ZimanLeg read-only/proposal methods)
| Command | Maps to | Side effects |
|---|---|---|
| `/ziman_status` | `status_snapshot()` → `telegram_digest()` | none |
| `/ziman_inventory` | `inventory_report()` (proposal) | proposal only |
| `/ziman_products` | read CATALOG.md summary | none |
| `/ziman_experiments` | list 05-Growth experiment cards | none |
| `/ziman_content` | `draft_content()` (proposal, D4-gated) | proposal only |
| `/ziman_memory` | list pending memory candidates | none |
| `/ziman_decisions` | read VERDICT_QUEUE.md | none |
| `/halt_ziman` | create limb-halt marker (owner only) | fail-closed halt |

## Invariants
- Owner allowlist only; non-owner updates ignored silently.
- No command publishes, sends to customers, spends, or changes prices.
- Approvals via existing ok/no/later callback pattern → approval-file + events.emit.
- STOP-TG-CENTER and STOP-ORGANISM always win.
- Telegram messages are NEVER canonical memory (gateway only).

## Digest format (existing `telegram_digest()`, 3 lines)
```
🖼 Ziman · {money_link}
ظرفیت {ceil}/هفته · موجودی≈{inv} · drafts={n}
propose-only · D4 on · zero external exec
```
