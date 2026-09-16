# Services Runtime Map — protocol and port

Generated: 2026-08-21  
Purpose: prevent wrong-protocol probes and wrong-server restarts (2026-08-21 incident: port 8801 probed with plain HTTP was misread as wedged; the smoke suite actually targets 8774).

| Port | Process (observed PID) | Protocol | Service | Notes |
|---|---|---|---|---|
| 8771 | 9904 (organism) | HTTP (local) | organism spine/cockpit | |
| 8772 | 17164 (cortex) | HTTP (local) | cortex | |
| 8773 | 27124 (live/server.py) | HTTP (local) | live cockpit (read + owner actions) | launcher `RUN-LIVE.bat` |
| 8774 | miniapp_gateway.py | HTTP + Telegram WebApp HMAC auth | miniapp gateway — target of `test_live_control_panel_smoke.py` | authenticated endpoints return 403 without `X-Tg-Init-Data` |
| 8776 | telegram_center/center.py | none (socket lock) | center singleton lock | not HTTP |
| 8801 | board_cp/server.py | **HTTPS (TLS)** | board control panel | plain HTTP probes get connection-reset; TLS returns 404 for unknown paths — do not classify as wedged on HTTP reset |
| 20241/20242 | cloudflared | TLS tunnels | cloudflare tunnels | |

## Supervision note (MISSING_SUPERVISION loop)

- `test_live_control_panel_smoke` failure was traced to the miniapp gateway (8774) whose parent launcher had exited (orphan). The gateway itself was alive; the smoke's `cache-ttl` check saw `items=[]` transiently and passed on rerun (53/53).
- Registered as `LOOP-LIVE-ORPHAN-MISSING-SUPERVISION`: a watchdog with orphan detection is required instead of manual discovery.

## Restart discipline

- Only the Telegram center has been restarted this session (twice, controlled, via `arm-canary.ps1`).
- board_cp was restarted once via `RESTART-BOARDCP.ps1` during the wrong-port investigation — it was healthy on its TLS protocol; the restart was harmless but unnecessary (documented).
