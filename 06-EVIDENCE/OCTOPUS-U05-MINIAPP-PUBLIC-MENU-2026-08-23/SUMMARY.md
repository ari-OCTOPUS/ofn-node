# OCTOPUS-U05 MiniApp Public Menu — 2026-08-23

**Status: PASS**

## What was true
- Gateway `miniapp_gateway.py` PID listening `127.0.0.1:8774` and serving MiniApp shell (`/` and `/miniapp` → 200).
- Named tunnel `octopus-miniapp` → `http://127.0.0.1:8774`.
- Public `https://app.master-painting.com/` and `/miniapp` → HTTPS 200 MiniApp shell (no longer 403).
- Candidate state `miniapp-url.json`: url=`https://app.master-painting.com` kind=named (verified by live GET; not invented).

## What changed
1. Backup `F:\backup\_ops\OCTOPUS.env.bak-u05-20260823`
2. Set durable in `OCTOPUS.env`:
   - `OCTOPUS_TG_MINIAPP=1`
   - `OCTOPUS_MINIAPP_URL=https://app.master-painting.com`
   - kept `OCTOPUS_PF_MINIAPP=1`
3. User env (HKCU):
   - set `OCTOPUS_TG_MINIAPP=1`
   - replaced stale `trycloudflare` URL with verified named URL

## Prove
- Center path sim: resolved ops MiniApp URL present → **not** CONFIG_NEEDED for missing URL.
- agi2027 `/ui` sim: `OK_URL_PRESENT`.
- `miniapp_registration.status` (READ-ONLY): `registered` / `menu_button=web_app` / `menu_matches_live_url=true`.

## Menu button
**SKIP_ALREADY_MATCHING** — did **not** call `setChatMenuButton` (already matches live URL; mutate unnecessary).

## Holds
None for U05 close criteria.

## Owner action
None required for U05. Optional: recycle long-lived `telegram_center` / control-plane processes started before env apply so they pick up new env without relying on JSON freshness alone.
