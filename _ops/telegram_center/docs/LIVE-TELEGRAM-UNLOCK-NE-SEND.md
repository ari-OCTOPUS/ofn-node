# LIVE-TELEGRAM unlock ≠ send (G05)

stamp: 2026-08-23T09:05:12+10:00
schema: live-telegram-unlock-ne-send/1

## Contract
| Layer | Meaning |
|---|---|
| `LIVE-TELEGRAM.flag` `enabled=true` | **Unlock token** — live *mode* may be considered |
| Writer lock `forbidden_actions` includes `live sendMessage` | Default **send denied** |
| `send_exceptions` TTL rows | Temporary narrow send allow (owner canary only) |
| `live_telegram_gate.evaluate()` | `live_mode_allowed` vs `send_allowed` split |

## Dry-run evidence
- Center reload gate pack (if present): live_mode_allowed=true, send_allowed=false, bridge dry refused
- Wire fix tests: `_ops/tests/test_live_telegram_wire_20260823.py`
- Attach default-off: `_ops/tests/test_poll_sender_bridge_attach_default_off.py`

## Speaking rule
Never claim "Telegram LIVE" from flag alone. Say **unlock armed** vs **send allowed**.
