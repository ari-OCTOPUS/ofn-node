# Owner Cockpit Commands

Generated: 2026-08-20

## Existing center commands

The live center already has command routing, owner allowlist, status/panel/task surfaces, approval callbacks, restart controls, and receipt reporting. Exact menus remain governed by `center.py` and its configuration.

## Proposed durable-loop commands (not activated)

- `/loops` — open/shadow-closed/production-closed counts.
- `/loop <id>` — breakpoint, blocker, SLA, closure path, evidence.
- `/task <id>` — durable transition timeline without raw content.
- `/receipts <id>` — result/outbox/delivery/readback receipts.
- `/dlq` — reconciliation/dead-letter summary.
- `/replay <event_id>` — dry-run only by default.
- `/pause` — set new-dispatch kill switch.
- `/resume <nonce>` — resume after health check.

These commands were not added to the live command menu in this session. Doing so requires a controlled live canary and owner-visible behavior change; the underlying registry/read models now exist as artifacts, but claiming cockpit activation would be false.
