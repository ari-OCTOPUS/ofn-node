# CURRENT-COCKPIT-MAP (M0, read-only, 2026-08-26T23:41:48.785+00:00)

## Runtime
- Service: ofn.service (User=ari, WD=/home/ari/ofn, ExecStart=/usr/bin/python3 -m ofn.run)
- EnvFiles: ~/.config/ofn/node.env + secrets.env (values never read/printed)
- Static shells per port (ofn/run.py ~189): 8791=ziman.html, 8792=lead.html, 8793=studio.html(+/sabaapp), 8794=panel.html (OWNER)
- All bound 127.0.0.1; access via existing tunnel/proxy (Host-header legs); no direct LAN exposure
- Aux: octopus-bridge.service (:8796 board_cp pull), ofn-heartbeat, hypno-fugu-mini (Telegram Web App)
- Panel: web/panel.html 121601 bytes sha256=735134eb3f175cdf486152f3680b1d6fd54e4980c34c08ecb0a88754376dda29, monolithic, 94 fn/ids, single central fetch(), telegram-web-app.js SDK

## Auth
- POST /api/v1/auth/session — Telegram Mini App launch-blob; backend validates identity; journal logs leg/path/status only
- Headers: nosniff, no-referrer, private/no-store on binaries

## Telegram
- ofn: bot_tokens server-side (alert/owner_reads/http_api); panel itself is a Telegram Web App
- OCTOPUS mesh bridge (~/octopus-mesh): shadow/fake, TELEGRAM_BLOCKED_CONFIG — separate path

## Backend
- stdlib http.server ThreadingHTTPServer, zero-dep (~1700 lines)
- 81 routes; owner scope: brain, ask, kill, kill/release, businesses, consent, painting(leads/campaigns/channels/accounts/interactions/dashboard/modules/sources), marketing/run, outbox, orders/settlements, ledger/summary, metrics, events, observability, growth-workbench, mini-apps, mini-webs, approved-manual, core/snapshot
- Effects server-side only; browser has NO direct DB/FS write path
