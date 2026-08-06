# Repository Baseline — Octopus / OFN

Status: PHASE 0 audit captured, non-destructive.

## Runtime verified
- `ofn.service`: active.
- Main process: `/usr/bin/python3 -m ofn.run`.
- Local ports: ziman `8791`, lead/painting `8792`, studio `8793`, owner panel `8794`.
- Additional services observed: public preview/server on `8090`, hypno on `8895`.
- Backup download server on `8765`: must remain stopped after backup transfer.

## Current tenant surfaces
- `panel.master-painting.com` -> owner panel -> `127.0.0.1:8794`.
- `lead.master-painting.com` -> painting/lead mini-app -> `127.0.0.1:8792`.
- `studio.master-painting.com` -> studio -> `127.0.0.1:8793`.
- `app.master-painting.com` -> studio `/sabaapp` -> `127.0.0.1:8793`.
- `ziman.master-painting.com` -> ziman -> `127.0.0.1:8791`.
- `hypno.master-painting.com` -> separate hypno service -> `127.0.0.1:8895`.

## Existing architecture found
- Python stdlib HTTP API in `ofn/adapters/http_api.py`.
- Tenant registry and packs in `packs/*.yaml` and `ofn/kernel/tenancy.py`.
- Append-only ledger in `ofn/adapters/ledger.py`.
- Durable outbox in `ofn/adapters/outbox.py`.
- Boot supervisor and schema checks in `ofn/adapters/boot.py`.
- Studio/media/marketing stores already present.
- Remote brain path already exists through router/worker; HTTP API intentionally must not import router/brain.
- Owner panel and partner mini-apps are static HTML served by the OFN process.

## Recent safe extension
- `painting.sqlite` added under state dir.
- Existing tables: painting leads, channels, campaigns, modules, interactions.
- Outbound/email/publish flags remain OFF unless explicitly configured by owner.
