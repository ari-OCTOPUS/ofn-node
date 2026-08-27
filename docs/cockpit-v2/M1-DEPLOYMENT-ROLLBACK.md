# Cockpit V2 M1 Deployment and Rollback

## Safety state

- Branch: `ofn/cockpit-v2-20260827`
- Legacy panel remains `/home/ari/ofn/web/panel.html` and the default `/`/`/index.html` owner shell.
- Baseline legacy panel SHA-256: `735134eb3f175cdf486152f3680b1d6fd54e4980c34c08ecb0a88754376dda29`.
- M1 creates no command endpoint, effect path, listener, systemd unit, credential, Telegram outbound message, business task, or external action.
- `BOARD-138-USAGE-GUIDE-FOR-BUSINESS-AUTONOMY-DIRECTIVE.md` is not attached. Its absence does not block read-only M1, but M2/effect phases remain gated.

## Why a restart is required

`ofn.run` loads static assets and constructs `ApiApp` once during process startup. New `/cockpit-v2/` assets and `/api/v2/owner/*` routes cannot appear in the live process until `ofn.service` is restarted.

M1 implementation and tests do **not** restart the service. They use an ephemeral loopback server on an OS-assigned port (`serve(app, 0)`) and leave production listeners unchanged.

## Proposed owner-controlled activation

After code review and explicit owner approval:

1. Confirm the deployed branch/commit and a clean worktree.
2. Re-run focused M1 tests and the complete regression suite.
3. Confirm `web/panel.html` still has the pinned SHA-256.
4. Capture current `ofn.service` state, listener set, and last journal entries.
5. Run the exact command only: `sudo systemctl restart ofn.service`.
6. Verify the exact service: `systemctl is-active ofn.service`, `systemctl show ofn.service -p MainPID,NRestarts`.
7. Verify existing owner root bytes and authenticated v1 endpoints.
8. Verify `/cockpit-v2/` and all V2 assets on the same owner origin.
9. Verify no listener was added, Telegram had no outbound action, and browser reads caused no mutation.

No wildcard `systemctl` operation is permitted.

## Rollback

If activation fails:

1. Restore the previously approved OFN branch/commit (do not rewrite history).
2. Run the exact command `sudo systemctl restart ofn.service`.
3. Verify `/` and `/index.html` return the pinned legacy panel bytes.
4. Verify existing v1 owner/partner shells and APIs.
5. Preserve M1 logs and evidence; do not delete the V2 branch or documents.

The old panel is always the rollback target and remains present throughout M1.
