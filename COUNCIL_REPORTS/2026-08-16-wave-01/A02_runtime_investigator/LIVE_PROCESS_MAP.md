# LIVE PROCESS MAP — A02 Runtime Investigator

Snapshot taken: **2026-08-16T23:44–23:46 +10:00 (AUS Eastern Standard Time)**
Method: `Get-CimInstance Win32_Process` (PID/PPID/name/exe/cmdline/start), `netstat -ano`, `Get-ScheduledTask`. Raw dumps: `raw/processes_snapshot1.json`, `raw/netstat_snapshot1.txt`.
Total processes on host: 339. Repo root: `F:\backup`. HEAD at observation: `028fe81` (2026-08-16T23:27:30+10:00), working tree DIRTY.

## 1. OCTOPUS live process tree

| PID | Process | Parent chain | Started (local) | Command line | Port(s) | Repo | Config source |
|-----|---------|--------------|-----------------|--------------|---------|------|---------------|
| 29028 | python.exe (organism) | 23136 cmd (`RUN-ORGANISM.bat`) ← dead shell | 2026-08-16T12:53:10 | `python -X utf8 organism.py` (cwd `F:\backup\_ops`) | 8771 (status HTTP), 8777 (lead-boundary ingress) | F:\backup working tree @ boot time | `OCTOPUS-flags.cmd` + `.env` via `env_loader` (evidence: `state/flags-loaded-organism.json`, pid=29028) |
| 11144 | python.exe (cortex) | 6796 cmd (`RUN-CORTEX.bat`) ← dead shell | 2026-08-16T13:01:53 | `python -X utf8 cortex\cortex.py` | 8772 | F:\backup | same flow |
| 7852 | python.exe (live cockpit) | 23924 cmd (`run-live-headless.bat`) ← dead shell | 2026-08-16T16:36:56 | `python -X utf8 live\server.py` | 8773 | F:\backup | same flow (launched by `live-watchdog.ps1` schtask) |
| 11724 | python.exe (tg-center) | 19312 cmd (`RUN-TG-CENTER.bat`) ← dead shell | 2026-08-16T16:37:33 | `python -X utf8 telegram_center\center.py` | 8776 | F:\backup | same flow |
| 19076 | python.exe (miniapp gateway) | 7572 (dead) | 2026-08-16T16:43:38 | `python -X utf8 F:\backup\_ops\telegram_center\miniapp_gateway.py` | 8774 (behind public tunnel) | F:\backup | `flags-loaded-miniapp-gateway.json` exists |
| 23464 | python.exe (board_cp) | 2576 (dead) | 2026-08-16T16:42:50 | `python -X utf8 F:\backup\_ops\board_cp\server.py` | 8801 TLS, bind 0.0.0.0 | F:\backup | reads `OCTOPUS.env` + flags at startup (per server.py docstring) |
| 17332 | cloudflared.exe | 12420 powershell (`run-miniapp-tunnel-named.ps1`) ← 7056 (dead) | 2026-08-16T06:58:06 | `cloudflared tunnel --no-autoupdate run --url http://127.0.0.1:8774 octopus-miniapp` | 20241 (local metrics); egress to Cloudflare edge | n/a | named tunnel `app.master-painting.com`; URL file `state/telegram/miniapp-url.json` pid=17332 (MATCHES live) |
| 20192 | ollama.exe | 10416 `ollama app.exe` ← 15488 cmd ← dead | (since ~2026-08-11) | `ollama serve` | 11434 loopback | n/a (installed app) | n/a |
| 9796 | llama-server.exe | 20192 ollama | 2026-08-16T23:41:29 | `--model sha256-183715c4… --port 1495 --host 127.0.0.1 --no-webui --offline -c 4096` | 1495 loopback | n/a | offline mode |

Python interpreter for all OCTOPUS services: **system-wide `C:\Program Files\Python313\python.exe` (Python 3.13.7); no virtualenv** (F-26).

## 2. Git-commit correlation (F-23 — version drift)

- Every service runs from the **`F:\backup` working tree** (scripts `cd /d F:\backup\_ops`).
- Live processes bootstrapped **12:53–16:43**. `_ops/organism.py` mtime **23:01:23**, `_ops/wiring.py` **23:01:15**, `_ops/chrono.py` **14:33:38**; HEAD `028fe81` committed **23:27:30**.
- Therefore the running organism/cortex **predates the 23:01 code edits and the HEAD commit**; modules already imported at boot keep the old code; any lazily-imported module loaded after an edit would run new code — a mixed-version hazard. Working tree is additionally dirty in `_ops/state/*` (runtime writes state inside the repo).
- Exact running-code commit is **not determinable** post-hoc (no boot-hash recorded). Classified: UNKNOWN exact revision; drift itself VERIFIED_LIVE.

## 3. Scheduled jobs sustaining the stack (12 OCTOPUS-related tasks, all State=Ready)

| Task | Cadence | Last run | Action |
|------|---------|----------|--------|
| organism-watchdog | 15 min | 23:52:00 | `F:\backup\04 - Architect System\scripts\organism-watchdog.ps1` |
| OCTOPUS-Cortex-Watchdog | 5 min | 23:54:01 | `_ops/cortex-watchdog.ps1` |
| OCTOPUS-Live-Watchdog | 5 min | 23:53:01 | `_ops/live-watchdog.ps1` |
| OCTOPUS-TG-Center-Watchdog | 5 min | 23:52:01 | `_ops/tg-center-watchdog.ps1` |
| OCTOPUS-MiniApp-Watchdog | 10 min | 23:48:01 | `_ops/miniapp-watchdog.ps1` |
| OCTOPUS-Cockpit-Brain | 5 min | 23:52:24 | `_ops/cockpit-brain-run.ps1` |
| OCTOPUS-Observatory | hourly | 23:36:28 | `python run_observatory.py` (relative path, CWD-dependent) |
| OCTOPUS Observatory Hourly | hourly | 23:06:01 | **`C:\Users\Armin\Desktop\OCTOPUS-NBB-CP-WORKING\nbb-control-plane\run_observatory.py` — OUTSIDE the repo** (F-02) |
| OCTOPUS 4d Consolidation Tick | 6 h | 23:49:01 | `_ops/audit/consolidation_4d_tick.py` |
| OCTOPUS 4d Poisoning Watch | 6 h | 22:08:10 | `_ops/audit/poisoning_watch_4d.py` |
| OCTOPUS-doctor-day | daily 07:00 | 07:00:01 | `_ops/run_doctor_day.py` |
| OctopusLiveDataRefresh | 30 min | 23:28:01 | `F:\backup\nervous-system\refresh-live-data.bat` |

## 4. Zombie / duplicate / orphan / stale-PID analysis (F-25)

- **No duplicate workers**: each OCTOPUS port has exactly one listener; all four `.bat` launchers contain port-occupied guards ("if 8771 already listening → don't start duplicate").
- **No zombies**: all OCTOPUS processes have live parents or dead-but-expected ancestors (launcher shells exited; `.bat` loop supervisors 6796/23136/23924/19312 remain alive by design).
- **No stale PID files**: no `*.pid` files exist on disk; PID-carrying state files match live processes (`miniapp-url.json` pid=17332 ✓, `pulse/tg-center.json` pid=11724 ✓).
- Notable non-OCTOPUS listeners on the host: `fingagent.exe` (0.0.0.0:3653 + 127.0.0.1:48080 — Fing network agent, third party), ExpressVPN services (2020–2022), Cursor/ssh port-forwards, Windows system ports.
- Auditor's own tooling (excluded from the map): ZCode CLI bash/powershell wrappers (PIDs 9808, 22432, 27920, 12420-adjacent none, 18976/29480 ZCode helpers).

## 5. Message buses / queues / databases

- **No broker process** (no NATS/RabbitMQ/Kafka). The "unified bus" is in-process (`_ops/unified_bus.py`) with a file event stream `_ops/state/events.jsonl` (last write 23:11:07 — sparse; F-21). Directory queues exist at `_octopus/queue/{pending,approved,done,rejected}`.
- Telegram ingress: long-poll (mode `long-poll(T-8)`, `channel-status.json` 23:51:09; `pulse/telegram-poll.json` 23:54:56).
- Live SQLite stores (mtime): `chrono.db` 11.8 MB + WAL 4 MB (per-beat, freshest), `spine/spine.db` (23:53), `memory/memory.db` (23:01), `owner_cockpit.db` (20:09), `board_cp/commands.sqlite` (19:05), `receipts/receipts.db` (13:19), `outcomes/outcomes.db` (13:19), `doctor/rfc-verdicts.db` (12:54), `legs/consent.db` (07-22, dormant), `outcomes/funnel.db` (08-02, dormant), `memory.db` (0 bytes, 08-07).
