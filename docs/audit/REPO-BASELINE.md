# Repository Baseline — Octopus / OFN

Status: PHASE 0 audit captured, non-destructive. Verified 2026-08-08.

## Runtime verified (2026-08-08)
- `ofn.service`: active (Restart=always, WatchdogSec=30s, MemoryMax=512M).
- Main process: `/usr/bin/python3 -m ofn.run`.
- Local ports (all loopback 127.0.0.1): ziman `8791`, lead/painting `8792`, studio `8793`, owner panel `8794`.
- `ofn-alert.service`: installed, wired via `OnFailure=` on `ofn.service`.
- hypno on `8895` (separate process, not via systemd unit — see note below).

> ⚠️ **Port 8090 — SECURITY RISK (audit 2026-08-08):** A backup download server
> (`/home/ari/ofn-downloads/_serve.py`, PID 2422) is running on `0.0.0.0:8090`
> with **no authentication**, serving a full system backup tarball that contains
> every SQLite database (consent, facts, outbox, products, audience, ledger).
> This is reachable by anyone on the LAN. REPO-BASELINE previously claimed this
> server was on port 8765 and "must remain stopped" — both the port and the
> status were wrong. **Action: `kill 2422` and disable any auto-restart.**
> cloudflared does NOT route 8090 to the internet, so exposure is LAN-only.

## Current tenant surfaces (all via cloudflared tunnel)
- `panel.master-painting.com` -> owner panel -> `127.0.0.1:8794`.
- `lead.master-painting.com` -> painting/lead mini-app -> `127.0.0.1:8792`.
- `studio.master-painting.com` -> studio -> `127.0.0.1:8793`.
- `app.master-painting.com` -> studio `/sabaapp` -> `127.0.0.1:8793`.
- `ziman.master-painting.com` -> ziman -> `127.0.0.1:8791`.
- `hypno.master-painting.com` -> separate hypno service -> `127.0.0.1:8895`.

## Existing architecture found
- Python stdlib HTTP API in `ofn/adapters/http_api.py` (no third-party deps).
- Tenant registry and packs in `packs/*.yaml` and `ofn/kernel/tenancy.py`.
- Append-only, hash-chained ledger in `ofn/adapters/ledger.py`.
- Durable outbox in `ofn/adapters/outbox.py`.
- Boot supervisor and schema checks in `ofn/adapters/boot.py`.
- Studio/media/marketing/painting stores present.
- Remote brain path through router/worker; HTTP API must not import router/brain (audited clean 2026-08-08).
- Owner panel and partner mini-apps are static HTML served by the OFN process.

## Extensions this session (2026-08-08)
- Kill switch: `node.engage_kill`/`release_kill` + 2 endpoints + panel button.
- Live metrics: `ofn/adapters/sysmetrics.py` + `GET /api/v1/owner/metrics`.
- Alert notifier: `ofn/adapters/alert.py` (log always, Telegram opt-in via flag).
- `painting.sqlite` now has: leads, channels, campaigns, modules, interactions,
  sources, b2b_accounts, tenders, vendor_applications.

## Dead env flags (audit 2026-08-08)
> ⚠️ `OFN_WIRE_EMAIL=1` and `OFN_WIRE_PUBLISH=1` are set in node.env but **no
> code reads them** — only `OFN_WIRE_OUTBOUND` is consumed (`config.py:230`).
> Publish is gated by a hardcoded `"off"` at `node.py:842` plus OwnerRelease.
> These dead flags are a future trap: if someone wires them, email/publish
> would silently enable. **Action: set both to `=0` or remove from node.env.**
