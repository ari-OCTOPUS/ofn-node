# MIGRATION-PLAN

## M0 — complete

Read-only snapshot on branch `ofn/cockpit-v2-20260827`; old panel untouched.

## M1 — read-only Cockpit V2

- Separate `/cockpit-v2/` shell on the existing owner origin/port.
- Six authenticated GET-only read-model resources: status, nodes, legs, queue, audit, version.
- No command API, effect verb, direct browser storage/DB access, model call, listener, systemd change, Telegram outbound, or business action.
- Static assets and API wiring load at process startup; implementation is tested with an ephemeral loopback server. Live exposure requires a separate owner-approved exact restart of `ofn.service`.
- Data parity is compared, never averaged. Missing or disputed data is UNKNOWN/DEGRADED.

## M2 — owner command fixtures

One Owner Control API shared by Web and Telegram. Approve/deny/pause fixtures only, with no real effect; exact payload binding, expiry, idempotency, first-valid-wins, and receipts.

## M3 — limited owner control

Pause/resume a test leg, exception fixture, restart/replay/expiry/changed-payload tests, and cross-channel receipt parity.

## M4 — production exceptions

Only after fresh E2E GREEN and Telegram owner canary. Standing-policy routine operations remain autonomous; sensitive exceptions use Owner Control API.

## M5 — old-panel retirement

Only after feature parity, owner acceptance, rollback test, and seven days observation. Archive; never delete.

## Rollback invariant

At every step the old panel remains `/` and `/index.html`. Rollback removes/disables only V2 mapping/code, restores the prior approved branch/commit without history rewrite, and restarts only the exact `ofn.service` after explicit owner approval.
