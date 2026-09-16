# Telegram Runtime Map

- Generated: 2026-08-20
- Requested baseline: `9bc506f`
- Observed HEAD after concurrent checkpoint: `7836627` (descendant of baseline)
- Mode: polling; no webhook implementation was observed in the live center path.
- Live process: Python PID 8828, lock/listen port 8776.
- Token available to this agent: false (presence check only; no secret read or printed).
- Durable boundary live flag: off. No process restart or live send was performed.

## Active path

`TgClient.poll_updates` → `Center.run_once` → inbound log → owner allowlist → durable intent (opt-in) → dispatch marker → existing handler/brain routing → durable result → deterministic outbox → `TgClient._call_post` → delivery receipt → disk readback → close.

Code anchors:

- Poller and HTTP boundary: `_ops/telegram_center/tg_api.py:671`
- Owner allowlist: `_ops/telegram_center/tg_api.py:373`
- Poll/dispatch and offset: `_ops/telegram_center/center.py:5858`
- Durable ingress binding: `_ops/telegram_center/center.py:2674`
- State machine: `_ops/telegram_center/durable_loop.py:186`
- Dispatch crash marker: `_ops/telegram_center/durable_loop.py:224`
- Outbox delivery boundary: `_ops/telegram_center/durable_loop.py:287`
- Result/closure: `_ops/telegram_center/durable_loop.py:426`
- Existing send receipt join: `_ops/tg_receipts.py:94`

## Truth levels

| Capability | Declared | Implemented | Wired | Observed | Tested | Verified |
|---|---:|---:|---:|---:|---:|---:|
| Owner allowlist | yes | yes | yes | historical | yes | no live re-verification |
| Polling singleton | yes | yes | yes | process/port | yes | partial |
| Durable intent | yes | yes | opt-in | fixture | yes | shadow only |
| Duplicate suppression | yes | yes | opt-in | fixture | yes | shadow only |
| Outbox-first send | yes | yes | opt-in | fixture | yes | shadow only |
| Delivery receipt/readback | yes | yes | opt-in | fixture | yes | shadow only |
| Production closure | yes | no rollout | no | no | no | no |

## First broken edges remaining

1. Live process does not have `OCTOPUS_TG_DURABLE_OUTBOX=1`; production still uses legacy direct send until a controlled restart/canary.
2. `event_bridge.py` marks a content signature seen before direct send (`event_bridge.py:165-170`), so a failed send can be suppressed for 24 hours. It is not routed through the new durable outbox.
3. `tg-send-log` remains an attempt log. The corrected join now refuses explicit `ok=false`, but historical rows without `ok` remain legacy-compatible rather than cryptographically confirmed.
4. Webhook state is unknown externally; code is a polling implementation and explicitly detects Telegram 409 rival pollers.

## Rollback

Leave `OCTOPUS_TG_DURABLE_OUTBOX` unset/off. This preserves the prior direct-send path byte-for-byte. The code additions are additive and no live state migration was performed.
