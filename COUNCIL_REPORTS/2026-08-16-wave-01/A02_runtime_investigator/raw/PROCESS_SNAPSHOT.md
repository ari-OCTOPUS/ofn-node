# LIVE PROCESS MAP — snapshot 2026-08-16T23:50+10:00 (non-invasive, read-only)

Method: `Get-CimInstance Win32_Process` (CommandLine), `netstat -ano`, file mtime observation.
No service was started, stopped, restarted or probed actively.

## OCTOPUS-related live processes (T0)

| PID | Name | Started (local) | CommandLine | Maps to |
|---|---|---|---|---|
| 29028 | python.exe | 2026-08-16 12:53:10 | `python -X utf8 organism.py` | Organism main loop. Matches `ORGANISM-STATE.json.started=2026-08-16T12:53:10`. Holds 127.0.0.1:8771 (status server, code: `_ops/organism.py:63 PORT=8771`) and 8777 |
| 11144 | python.exe | 2026-08-16 13:01:53 | `python -X utf8 cortex\cortex.py` | Second process-brain ("cortex — مرکزی کنترل‌گر", owner-vote role). 127.0.0.1:8772 (`_ops/cortex/cortex.py:33`) |
| 7852 | python.exe | 2026-08-16 16:36:56 | `python -X utf8 live\server.py` | "Live control room" web service. 127.0.0.1:8773 (`_ops/live/server.py:32`) |
| 11724 | python.exe | 2026-08-16 16:37:33 | `python -X utf8 telegram_center\center.py` | Telegram cockpit center (long-poll). Lock port 127.0.0.1:8776 (`_ops/telegram_center/center.py:5959`) |
| 19076 | python.exe | 2026-08-16 16:43:38 | `python -X utf8 F:\backup\_ops\telegram_center\miniapp_gateway.py` | Telegram MiniApp gateway (initData HMAC wall). 127.0.0.1:8774 |
| 23464 | python.exe | 2026-08-16 16:42:50 | `python -X utf8 F:\backup\_ops\board_cp\server.py` | Board control-panel TLS server. Bound **0.0.0.0:8801** (default bind `0.0.0.0`, `_ops/board_cp/server.py:144`) |
| 17332 | cloudflared.exe | 2026-08-16 06:58:06 | `cloudflared.exe tunnel --no-autoupdate run --url http://127.0.0.1:8774 octopus-miniapp` | **Public internet tunnel** -> local MiniApp gateway 8774 |
| 20192 | ollama.exe | 2026-08-14 11:42:27 | `ollama.exe serve` | Local model server 127.0.0.1:11434 (provider fallback tier) |

Non-OCTOPUS listeners present on host: ExpressVPN services (3928/5076/5112), fingagent.exe (13644, ports 3653/48080), Windows system ports.

## Impersonation / provenance notes
- All OCTOPUS python processes run from `F:\backup\_ops` (relative entry scripts) except board_cp/miniapp_gateway which use absolute `F:\backup\_ops\...` paths.
- No process runs from `4d_system/` — 4d_system is NOT a live process (matches CURRENT-TRUTH.md "4d_system / Super-Governor: وصل نیست").
- Single-instance locks are port binds (8771 organism, 8772 cortex, 8776 tg-center) — code-verified docstrings "قفل تک‌نمونه".

## Observation
Snapshot taken while all processes were running; nothing was restarted or signaled.
