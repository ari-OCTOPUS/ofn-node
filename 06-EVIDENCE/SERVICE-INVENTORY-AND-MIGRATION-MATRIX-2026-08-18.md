---
type: evidence
created: 2026-08-18
updated: 2026-08-18
tags: [ops, inventory, migration, node-180, laptop]
author: "OCTOPUS ARCHITECT WORKSTATION — staged-migration inventory (propose-only)"
---

# Service inventory and migration matrix — 2026-08-18

Host `DESKTOP-KA9RFN5` · Wi-Fi IPv4 **192.168.0.191** · captured 2026-08-18 ~02:32–02:40 +10.

**Binding truth:** until a Promotion Receipt, `F:\backup` and `E:\germline` remain canonical. **192.168.0.180 is a continuity-candidate only.** Stage 6–8 is not production/pilot proof. Network fix and canonical migration are **separate incidents**. GITWRITE-FAILED was **not** cleared.

**This pass:** read-only on the live tree except these evidence files. No service stopped, started, failed over, or copied. No SSH to boards. No TCB edit. No autonomy change. `.180` not declared canonical.

Classification is exactly one of: `MUST_STAY_ON_LAPTOP` | `CAN_MOVE_TO_180` | `CAN_REPLICATE_TO_180` | `MUST_BE_REDESIGNED` | `UNKNOWN`.

`proposed_target` is a proposal field only. It does not authorize a move.

## Snapshot facts (live)

| Fact | Evidence |
|---|---|
| Hostname | `DESKTOP-KA9RFN5` |
| Laptop LAN | `192.168.0.191` (Wi-Fi DHCP). `.180` not on this host |
| 4d daemon | pid **24588**, cwd `F:\backup\4d_system`, cmd `python -m brain.daemon`, `resumed_at` 2026-08-17T21:08:26, `last_tick_at` 2026-08-18T02:33:35, `kernel.integrity_ok` true |
| board-cp | pid **26932**, `F:\backup\_ops\board_cp\server.py`, listen **0.0.0.0:8801** TLS, flag `OCTOPUS_BOARD_CP=1` |
| organism | pid **7416**, `python -X utf8 organism.py` via `RUN-ORGANISM.bat`, listen **127.0.0.1:8771** and **8777** (8777 purpose unproven in `organism.py`) |
| cortex | pid **15368**, `cortex\cortex.py` via `RUN-CORTEX.bat`, **127.0.0.1:8772** |
| live cockpit | pid **19228**, `live\server.py` via `run-live-headless.bat`, **127.0.0.1:8773** |
| tg-center | pid **27844**, `telegram_center\center.py`, lock port **127.0.0.1:8776**, pulse `tg-center.json` pid 27844 |
| miniapp | pid **22768**, `miniapp_gateway.py`, **127.0.0.1:8774** + cloudflared named tunnel `octopus-miniapp` |
| NATS on laptop | **no** listen 4222/6222/8222, **no** `nats-server` process |
| handshake sidecar | `_ops/handshake/` present; **no** live process |
| GITWRITE-FAILED | **EXISTS** `_ops/backup/GITWRITE-FAILED.flag` mtime 2026-08-16 03:50:24; lock file absent |
| germline-hourly | task Ready, LastResult **0**, last 2026-08-18 01:49; log still `PUSH-FAIL` / bundle-fallback |
| germline-daily | task Ready, LastResult **1**, last 2026-08-17 03:30 |
| TCB | `4d_system/config/trust-boundary.json` + `.sig`; private key present at owner profile path (name only) |
| HALT/STOP | HALT-ALL, STOP-ORGANISM, STOP-TG-CENTER, daemon.stop, daemon.pause, BEAT-FREEZE all **absent** |

## Counts

| Classification | n |
|---|---|
| MUST_STAY_ON_LAPTOP | 20 |
| CAN_MOVE_TO_180 (proposal) | 1 |
| CAN_REPLICATE_TO_180 | 3 |
| MUST_BE_REDESIGNED | 11 |
| UNKNOWN | 2 |
| **Total rows** | **37** |

---

## 1. daemon / heartbeat

### 4d_daemon

| Field | Value |
|---|---|
| service_name | `4d_daemon` |
| current_host | DESKTOP-KA9RFN5 (`192.168.0.191`) |
| executable/config | `C:\Program Files\Python313\python.exe -m brain.daemon` · cwd `F:\backup\4d_system` · TCB files `4d_system/brain/daemon.py`, `automation.py` · settings `4d_system/config/settings.py` · env `4d_system/.env` + `_ops/OCTOPUS-flags.cmd` |
| startup | Manual (HANDOFF: owner restart 2026-08-17 21:08). **No** scheduled watchdog for this pid |
| ports | none listening (headless) |
| state paths | `4d_system/outputs/daemon_state.json` (pid 24588 live) · `4d_system/outputs/4d_experiments.db` · `4d_system/outputs/self_evolved/` · stop/pause `daemon.stop` / `daemon.pause` |
| dependencies | TCB manifest + `.sig` · `OCTOPUS_TCB_MANIFEST_ENFORCE` · LLM keys in `4d_system/.env` · flags.cmd · git_watcher on vault |
| credentials required | `FUGU_API_KEY` · `GLM_API_KEY` · `TELEGRAM_BOT_TOKEN` (4d `.env` names) |
| write targets | `F:\backup\4d_system\outputs\**` · may propose git/self-code (TCB) |
| external effects | paid LLM HTTP if flags allow · optional Telegram digest |
| safe shutdown | create `4d_system/outputs/daemon.stop` or SIGINT; do **not** kill -9 unless hung |
| rollback point | previous `daemon_state.json` + signed `trust-boundary.json` / `.sig` · do not restart under unsigned TCB patches |
| proposed_target | 192.168.0.180 **only after** Promotion Receipt **and** redesign (no dual-write) |
| migration risk | **critical** — vault mutation + TCB + git_watcher |
| **class** | **MUST_BE_REDESIGNED** |

Evidence: live pid 24588 matches `daemon_state.json`. Lift-and-shift while laptop stays canonical = dual-write. Always-on on `.180` needs new write authority, not a copy of the process.

### organism_loop

| Field | Value |
|---|---|
| service_name | `organism_loop` |
| current_host | DESKTOP-KA9RFN5 |
| executable/config | `F:\backup\_ops\organism.py` · launcher `F:\backup\_ops\RUN-ORGANISM.bat` · flags `_ops/OCTOPUS-flags.cmd` · secrets via `env_loader` from `F:\backup\.env` |
| startup | `RUN-ORGANISM.bat` loop + scheduled task `organism-watchdog` → `04 - Architect System\scripts\organism-watchdog.ps1` |
| ports | **127.0.0.1:8771** (status + singleton lock, env `ORGANISM_PORT`) · **127.0.0.1:8777** owned by same pid **7416** (purpose **not** found in `organism.py` this pass) |
| state paths | `_ops/state/pulse/beat-state.json` (beat 4784, halted false) · many `_ops/state/pulse/*.json(l)` |
| dependencies | flags.cmd · `.env` · cortex/live optional · beat_lease **not wired** (`_ops/runtime/beat_lease.py` comments: organism/chrono not imported) |
| credentials required | `TELEGRAM_BOT_TOKEN` · `TELEGRAM_OWNER_CHAT_ID` · other vault `.env` names used by organs |
| write targets | `_ops/state/**` · vault notes via wired organs · genome/ledger if those wires on |
| external effects | Telegram, SMTP/IMAP if flags, LLM providers |
| safe shutdown | create `_ops/STOP-ORGANISM` and wait one tick; global `_ops/HALT-ALL` or `04 - Architect System\STOP` |
| rollback point | STOP file + watchdog yield · `beat-state.json` · do not start a second organism |
| proposed_target | `.180` only with armed beat lease + single writer |
| migration risk | **critical** — two organisms = split-brain / dual budget |
| **class** | **MUST_BE_REDESIGNED** |

### handshake_sidecar

| Field | Value |
|---|---|
| service_name | `handshake_sidecar` |
| current_host | laptop files only; **not a daemon** |
| executable/config | `_ops/handshake/emit_cycle.py` · `_ops/handshake/envelope.py` |
| startup | on-demand python; **no** live process at capture |
| ports | none (curl client to :8801) |
| state paths | `06-EVIDENCE/envelopes/` |
| dependencies | board-cp reachability for 401 probe · daemon_state read |
| credentials required | none for WAVE0 observe (pull without bearer) |
| write targets | evidence envelopes under `06-EVIDENCE/` when run |
| external effects | none beyond local files + localhost curl |
| safe shutdown | n/a (not running) |
| rollback point | leave sidecar unwired from TCB |
| proposed_target | `.180` may **emit observe-only copies**; must not become a second writer of canonical envelopes without owner rule |
| migration risk | low if read-only |
| **class** | **CAN_REPLICATE_TO_180** |

### beat_lease_fencing

| Field | Value |
|---|---|
| service_name | `beat_lease_fencing` |
| current_host | code on laptop; **unarmed** |
| executable/config | `_ops/runtime/beat_lease.py` · freeze `BEAT-FREEZE.flag` (absent) |
| startup | not imported by organism/chrono (file comment) |
| ports | NatsKv backend would need NATS — **none on laptop** |
| state paths | lease files (FileLeaseStore local disk only; SMB forbidden in module docstring) |
| dependencies | for multi-host: NATS KV on a **new** bus — **not** Sensorium `octopus.*` |
| credentials required | none today; NATS creds if redesigned |
| write targets | lease file / future KV |
| external effects | none while unarmed |
| safe shutdown | n/a |
| rollback point | keep unarmed; `BEAT-FREEZE.flag` is the cutover brake |
| proposed_target | `.180` as **future** lease holder only after M2+ redesign |
| migration risk | **critical** if armed on two hosts |
| **class** | **MUST_BE_REDESIGNED** |

---

## 2. schedulers

### windows_task_scheduler

| Field | Value |
|---|---|
| service_name | `windows_task_scheduler` |
| current_host | DESKTOP-KA9RFN5 |
| executable/config | Task Scheduler service · OCTOPUS/germline tasks listed below |
| startup | Windows |
| ports | n/a |
| state paths | `C:\Windows\System32\Tasks\` |
| dependencies | user `Armin` (hourly evidence) |
| credentials required | task-account Windows identity (not copied) |
| write targets | launches writers into `F:\backup` / `E:\germline` |
| external effects | git push to `E:\germline\vault.git` |
| safe shutdown | disable tasks (owner); **not done this pass** |
| rollback point | re-enable same task XML on this host |
| proposed_target | stay until Promotion Receipt; `.180` would need its own scheduler **after** writers move |
| migration risk | high — silent duplicate tasks = dual git write |
| **class** | **MUST_STAY_ON_LAPTOP** |

### watchdog_pack

| Field | Value |
|---|---|
| service_name | `watchdog_pack` |
| current_host | DESKTOP-KA9RFN5 |
| executable/config | tasks: `organism-watchdog` → `04 - Architect System\scripts\organism-watchdog.ps1` · `OCTOPUS-Cortex-Watchdog` → `_ops\cortex-watchdog.ps1` · `OCTOPUS-Live-Watchdog` → `_ops\live-watchdog.ps1` · `OCTOPUS-TG-Center-Watchdog` → `_ops\tg-center-watchdog.ps1` · `OCTOPUS-MiniApp-Watchdog` → `_ops\miniapp-watchdog.ps1` |
| startup | Task Scheduler ~5 min (miniapp ~10 min) |
| ports | probe 8771/8772/8773/8774; tg-center by cmdline + pulse |
| state paths | `_ops/state/*-watchdog-log.txt` · `_ops/state/watchdog.log` |
| dependencies | the five supervised processes; yield to HALT-ALL / STOP-* |
| credentials required | none beyond process env of children |
| write targets | logs under `_ops/state/` · may relaunch BAT/python |
| external effects | restarts Telegram poller / board-facing miniapp |
| safe shutdown | STOP-* files; do not delete tasks this pass |
| rollback point | STOP files + task LastRun history |
| proposed_target | stay with the processes they supervise |
| migration risk | high if watchdogs revive laptop writers after a `.180` cutover |
| **class** | **MUST_STAY_ON_LAPTOP** |

### OCTOPUS-Cockpit-Brain

| Field | Value |
|---|---|
| service_name | `OCTOPUS-Cockpit-Brain` |
| current_host | DESKTOP-KA9RFN5 |
| executable/config | `_ops\cockpit-brain-run.ps1` → `python _ops\cockpit_brain_tick.py` · flag `OCTOPUS_COCKPIT_BRAIN=1` |
| startup | task every ~5 min (Running at capture, LastResult 267009 = still running) |
| ports | none |
| state paths | `_ops/state/cockpit_brain/run.log` · pulse arbiter files |
| dependencies | flags.cmd |
| credentials required | none extra (uses organism state) |
| write targets | `_ops/state/cockpit_brain/` · pulse JSON |
| external effects | none proven beyond local state |
| safe shutdown | disable task or set flag 0 (owner) |
| rollback point | `run.log` |
| proposed_target | laptop until Promotion Receipt |
| migration risk | medium — vault state writes |
| **class** | **MUST_STAY_ON_LAPTOP** |

### OCTOPUS-doctor-day

| Field | Value |
|---|---|
| service_name | `OCTOPUS-doctor-day` |
| current_host | DESKTOP-KA9RFN5 |
| executable/config | `_ops\run_doctor_day.py` → `OCTOPUS-DOCTOR\doctor\cli.py day` (no `--apply`) |
| startup | daily 07:00 · LastResult 0 · last 2026-08-17 07:00 |
| ports | none |
| state paths | doctor outputs under vault (via cli) |
| dependencies | `env_loader` loads `.env` then doctor (doctor itself must not read `.env`) |
| credentials required | vault `.env` names via loader |
| write targets | doctor reports in vault (no merge without `--apply`) |
| external effects | Telegram if doctor TG flags |
| safe shutdown | disable task |
| rollback point | last daily output files |
| proposed_target | laptop |
| migration risk | medium |
| **class** | **MUST_STAY_ON_LAPTOP** |

### OCTOPUS_4d_Consolidation_Tick

| Field | Value |
|---|---|
| service_name | `OCTOPUS 4d Consolidation Tick` |
| current_host | DESKTOP-KA9RFN5 |
| executable/config | `_ops\audit\consolidation_4d_tick.py` cwd `F:\backup` |
| startup | ~6h · LastResult 0 · last 2026-08-17 23:49 · next 2026-08-18 05:49 |
| ports | none |
| state paths | reads `4d_system/outputs/self_evolved/` · writes via ConsolidationCycle |
| dependencies | 4d outputs · flags |
| credentials required | none proven |
| write targets | 4d consolidation state under vault |
| external effects | none proven |
| safe shutdown | disable task |
| rollback point | `frontier.json.bak` exists beside frontier |
| proposed_target | laptop |
| migration risk | medium |
| **class** | **MUST_STAY_ON_LAPTOP** |

### OctopusLiveDataRefresh

| Field | Value |
|---|---|
| service_name | `OctopusLiveDataRefresh` |
| current_host | DESKTOP-KA9RFN5 |
| executable/config | `F:\backup\nervous-system\refresh-live-data.bat` · Python extractors → `nervous-system/*.js` |
| startup | task Running at capture · ~30 min · LastResult 267009 |
| ports | none (reads daemon_state / vault) |
| state paths | `nervous-system/*.js` |
| dependencies | 4d outputs, git, organism state (BAT comments: extractors read-only vs **source** data) |
| credentials required | none |
| write targets | `F:\backup\nervous-system\` (vault write of generated JS) |
| external effects | none |
| safe shutdown | wait for task; do not kill mid-write |
| rollback point | previous JS files in git / worktree |
| proposed_target | laptop until Promotion Receipt |
| migration risk | medium — duplicate refresh = noisy diffs, not dual-beat |
| **class** | **MUST_STAY_ON_LAPTOP** |

### OCTOPUS_Observatory_pair

| Field | Value |
|---|---|
| service_name | `OCTOPUS-Observatory` + `OCTOPUS Observatory Hourly` |
| current_host | DESKTOP-KA9RFN5 |
| executable/config | `python run_observatory.py` cwd `C:\Users\Armin\Desktop\OCTOPUS-NBB-CP-WORKING\nbb-control-plane` · Hourly uses absolute python on same `run_observatory.py` |
| startup | ~1h and ~hourly · LastResult 0 both |
| ports | none proven on laptop NBB API |
| state paths | **outside vault** (Desktop tree) — this pass did not inventory Desktop writes |
| dependencies | Desktop NBB-CP working copy — **not** `F:\backup` SoT |
| credentials required | UNKNOWN (Desktop tree not fully read) |
| write targets | UNKNOWN (Desktop) |
| external effects | UNKNOWN |
| safe shutdown | disable both tasks (owner) — **not done** |
| rollback point | unknown without Desktop SoT |
| proposed_target | cannot lift Desktop path to `.180` as-is |
| migration risk | high — split-brain vs vault NBB-CP code in `4d_system/src/nbb_cp` |
| **class** | **MUST_BE_REDESIGNED** |

---

## 3. NATS / JetStream

### nats-server-laptop

| Field | Value |
|---|---|
| service_name | `nats-server` (laptop) |
| current_host | **absent** |
| executable/config | none found live |
| startup | none |
| ports | 4222/6222/8222 **not listening** |
| state paths | n/a |
| dependencies | n/a |
| credentials required | n/a |
| write targets | n/a |
| external effects | n/a |
| safe shutdown | n/a |
| rollback point | n/a |
| proposed_target | do **not** invent a laptop NATS to “move” |
| migration risk | n/a |
| **class** | **UNKNOWN** |

Evidence: process list + listen table this pass. `organism.py` has no `nats://` match.

### nats-server-sensorium-182

| Field | Value |
|---|---|
| service_name | `nats-server` (Sensorium) |
| current_host | **192.168.0.182** (file evidence, not SSH this pass) |
| executable/config | `/opt/octopus` + NATS · `nats-server.conf` described as TCB-protected on that node |
| startup | board systemd (not verified live from laptop) |
| ports | not observed from this host |
| state paths | Sensorium local (not this vault) |
| dependencies | subjects `octopus.*` · **no** leaf/cluster · disjoint from `continuity.*` |
| credentials required | board-local (not inventoried; not copied) |
| write targets | Sensorium bus only |
| external effects | Sensorium sensors |
| safe shutdown | out of scope (other agent / owner) |
| rollback point | do not interconnect with `.180` |
| proposed_target | **stay on .182**; a `.180` bus would be a **new** `continuity.*` design |
| migration risk | **critical** if someone clusters `.182`↔`.180` |
| **class** | **MUST_BE_REDESIGNED** |

Evidence: Inbox Sensorium charter v2 + SENSORIUM-NODE-ALIGNMENT (file). This agent did **not** SSH to confirm.

---

## 4. API / FastAPI

### nbb_cp_fastapi

| Field | Value |
|---|---|
| service_name | `nbb_cp_fastapi` |
| current_host | code only on laptop |
| executable/config | `4d_system/src/nbb_cp/api/http.py` — FastAPI **optional extra** |
| startup | **not running** (no matching process/port) |
| ports | none |
| state paths | n/a live |
| dependencies | FastAPI extra may be uninstalled |
| credentials required | UNKNOWN |
| write targets | would be ControlPlaneService effects if started |
| external effects | none live |
| safe shutdown | n/a |
| rollback point | keep unstarted |
| proposed_target | not a live duty to move |
| migration risk | starting it on two hosts without INV-4 choke-point design = defect |
| **class** | **UNKNOWN** |

### cortex_loop

| Field | Value |
|---|---|
| service_name | `cortex_loop` |
| current_host | DESKTOP-KA9RFN5 |
| executable/config | `_ops\cortex\cortex.py` · `RUN-CORTEX.bat` · `RESTART-CORTEX.ps1` · port env `CORTEX_PORT` default 8772 |
| startup | BAT + `OCTOPUS-Cortex-Watchdog` |
| ports | **127.0.0.1:8772** |
| state paths | cortex state under `_ops` (STOP-CORTEX absent) |
| dependencies | ollama often (`CORTEX_LOCAL_FIRST` in flags) · organism |
| credentials required | vault `.env` / flags; no extra file proven |
| write targets | `_ops/state` · may call LLM |
| external effects | Ollama localhost · paid LLM if routed |
| safe shutdown | `_ops/STOP-CORTEX` |
| rollback point | watchdog + STOP |
| proposed_target | `.180` only with organism/ollama redesign |
| migration risk | high |
| **class** | **MUST_BE_REDESIGNED** |

### live_cockpit

| Field | Value |
|---|---|
| service_name | `live_cockpit` |
| current_host | DESKTOP-KA9RFN5 |
| executable/config | `_ops\live\server.py` · `run-live-headless.bat` · `LIVE_PORT` 8773 |
| startup | BAT + `OCTOPUS-Live-Watchdog` |
| ports | **127.0.0.1:8773** |
| state paths | live cockpit logs/heartbeat via opslib |
| dependencies | probes organism 8771, cortex 8772, ollama 11434, dashboard 8770; **can relaunch organism BAT** (code in `live/server.py`) |
| credentials required | none extra proven |
| write targets | may create STOP/RESTART markers |
| external effects | local process control |
| safe shutdown | `_ops/STOP-LIVE` (watchdog will not revive) |
| rollback point | STOP-LIVE |
| proposed_target | stay with the processes it can spawn |
| migration risk | high — remote cockpit that starts laptop BAT is a new control plane |
| **class** | **MUST_BE_REDESIGNED** |

(board-cp TLS API is category 6; miniapp 8774 is category 7.)

---

## 5. memory services

### fourd_outputs_memory

| Field | Value |
|---|---|
| service_name | `fourd_outputs_memory` |
| current_host | DESKTOP-KA9RFN5 |
| executable/config | written by `4d_daemon` / consolidation |
| startup | sidecar of 4d daemon |
| ports | none |
| state paths | `4d_system/outputs/4d_experiments.db` · `daemon_state.json` · `self_evolved/frontier.json` |
| dependencies | 4d daemon |
| credentials required | none |
| write targets | those paths (canonical vault) |
| external effects | none |
| safe shutdown | stop daemon cleanly first |
| rollback point | db + frontier.bak |
| proposed_target | stay on canonical vault |
| migration risk | high if replicated as second writer |
| **class** | **MUST_STAY_ON_LAPTOP** |

### semantic_memory

| Field | Value |
|---|---|
| service_name | `semantic_memory` |
| current_host | DESKTOP-KA9RFN5 |
| executable/config | `_ops/state/semantic_memory.jsonl` (read by `poisoning_watch_4d.py`) |
| startup | writers are organism/4d paths (not separately process-listed) |
| ports | none |
| state paths | `_ops/state/semantic_memory.jsonl` |
| dependencies | memory-gate flags |
| credentials required | none |
| write targets | that jsonl |
| external effects | none |
| safe shutdown | n/a as standalone |
| rollback point | file copy / git |
| proposed_target | laptop SoT; read-only mirror allowed later |
| migration risk | medium |
| **class** | **MUST_STAY_ON_LAPTOP** |

### genome_ledger

| Field | Value |
|---|---|
| service_name | `genome_ledger` |
| current_host | DESKTOP-KA9RFN5 |
| executable/config | `07 - Knowledge/genome-system/ledger/ledger.py` · chain `ledger.jsonl` · tip `ledger.jsonl.tip.json` |
| startup | invoked by germline-daily verify; other writers via organism |
| ports | none |
| state paths | `07 - Knowledge/genome-system/ledger/ledger.jsonl` |
| dependencies | git backup gates |
| credentials required | none |
| write targets | ledger.jsonl (canonical) |
| external effects | none |
| safe shutdown | do not write from two hosts |
| rollback point | git + germline bundle |
| proposed_target | laptop until Promotion Receipt |
| migration risk | **critical** — chain fork |
| **class** | **MUST_STAY_ON_LAPTOP** |

### ollama_local_llm

| Field | Value |
|---|---|
| service_name | `ollama_local_llm` |
| current_host | DESKTOP-KA9RFN5 |
| executable/config | `C:\Users\Armin\AppData\Local\Programs\Ollama\ollama.exe` + `llama-server` |
| startup | user install / app |
| ports | **127.0.0.1:11434** (ollama) · **127.0.0.1:9565** (llama-server) |
| state paths | Ollama models under user profile (not vault) |
| dependencies | none on F:\backup mutate |
| credentials required | none |
| write targets | local model cache (not vault) |
| external effects | local inference |
| safe shutdown | stop Ollama app (not done) |
| rollback point | reinstall models |
| proposed_target | `.180` **proposal** as inference runtime |
| migration risk | medium — cortex/organism currently assume localhost |
| **class** | **CAN_MOVE_TO_180** |

### control_brain_core_db

| Field | Value |
|---|---|
| service_name | `control_brain_core_db` |
| current_host | DESKTOP-KA9RFN5 |
| executable/config | `_launchpad\second-brain-live\control-brain\core.db` (copied by germline-hourly whitelist) |
| startup | control-brain process **not** seen in python list this pass |
| ports | none proven |
| state paths | `core.db` · `events.jsonl` under `_launchpad` |
| dependencies | germline hourly robocopy |
| credentials required | UNKNOWN |
| write targets | those files if the brain runs |
| external effects | UNKNOWN |
| safe shutdown | n/a if not running |
| rollback point | germline `state-hourly` copy |
| proposed_target | laptop |
| migration risk | medium |
| **class** | **MUST_STAY_ON_LAPTOP** |

---

## 6. NBB-CP / policy

### board_cp_tls

| Field | Value |
|---|---|
| service_name | `board_cp_tls` |
| current_host | DESKTOP-KA9RFN5 · bind **0.0.0.0:8801** |
| executable/config | `_ops\board_cp\server.py` · `RESTART-BOARDCP.ps1` · flag `OCTOPUS_BOARD_CP` · env `_ops/OCTOPUS.env` |
| startup | launched 2026-08-17 23:51 (pid 26932); restart script kills/starts (script **not** run this pass) |
| ports | **8801/tcp TLS** all-interfaces |
| state paths | `_ops/state/board_cp/commands.sqlite` · TLS `cert.pem`/`key.pem` |
| dependencies | Gate 0: `OCTOPUS_BOARD_CONTROL_URL` + `OCTOPUS_BOARD_CP_BEARER` · flag=1 |
| credentials required | `OCTOPUS_BOARD_CP_BEARER` · TLS key · `OCTOPUS_BOARD_CONTROL_URL` (URL is config, not dumped) |
| write targets | commands.sqlite · heartbeat via opslib |
| external effects | boards **pull/ack** from this listener (LAN). Windows must not POST to board :8796 |
| safe shutdown | do **not** this pass. Documented: stop python `board_cp\server.py` then boards cannot pull |
| rollback point | sqlite + TLS dir · `RESTART-BOARDCP.ps1` (owner) |
| proposed_target | `.180` would be a **new** command authority — not a silent bind move |
| migration risk | **critical** — dual queue / dual pull |
| **class** | **MUST_BE_REDESIGNED** |

### nbb_cp_library

| Field | Value |
|---|---|
| service_name | `nbb_cp_library` |
| current_host | vault code `4d_system/src/nbb_cp/` |
| executable/config | SPEC in `4d_system/docs/` · INV-4 execute choke-point |
| startup | not a live HTTP (see FastAPI UNKNOWN) |
| ports | none |
| state paths | library-only unless API started |
| dependencies | 4d_system |
| credentials required | `NBB_GLOBAL_CAP_CENTS` name in doctrine (not confirmed in live env this pass) |
| write targets | none live |
| external effects | none live |
| safe shutdown | n/a |
| rollback point | git |
| proposed_target | code stays in canonical vault |
| migration risk | low as library; high if a second execute path is stood up |
| **class** | **MUST_STAY_ON_LAPTOP** |

---

## 7. Telegram gateway

### telegram_center

| Field | Value |
|---|---|
| service_name | `telegram_center` |
| current_host | DESKTOP-KA9RFN5 |
| executable/config | `_ops\telegram_center\center.py` · `RUN-TG-CENTER.bat` · WORKLOCK on `center.py` |
| startup | BAT loop + `OCTOPUS-TG-Center-Watchdog` (hung-pulse kill/relaunch) |
| ports | **127.0.0.1:8776** lock (`TG_CENTER_LOCK_PORT`) — not a public HTTP API |
| state paths | `_ops/state/telegram/center-config.json` · `_ops/state/pulse/tg-center.json` · `_ops/state/telegram/approvals/` |
| dependencies | Telegram Bot API · tokens in vault `.env` |
| credentials required | `TG_CENTER_BOT_TOKEN` · `TG_CENTER_CHAT_ID` · `TELEGRAM_BOT_TOKEN` · `TELEGRAM_OWNER_CHAT_ID` · `HH_HUMAN_GUARD_SECRET` (optional) · `OCTOPUS_CB_SECRET` |
| write targets | telegram state · approval files · `_octopus/state/approvals.json` |
| external effects | `api.telegram.org` (poll + send) |
| safe shutdown | `_ops/STOP-TG-CENTER` then wait one poll cycle |
| rollback point | center-config.json + STOP file (prevents dual poller 409) |
| proposed_target | cannot run two pollers; move = redesign single consumer |
| migration risk | **critical** |
| **class** | **MUST_BE_REDESIGNED** |

### miniapp_gateway_and_tunnel

| Field | Value |
|---|---|
| service_name | `miniapp_gateway_and_tunnel` |
| current_host | DESKTOP-KA9RFN5 |
| executable/config | `_ops\telegram_center\miniapp_gateway.py` · `run-miniapp-tunnel-named.ps1` · cloudflared named tunnel `octopus-miniapp` |
| startup | Cursor-parented python 22768 + powershell 19636 + cloudflared 11080 · `OCTOPUS-MiniApp-Watchdog` |
| ports | **127.0.0.1:8774** · cloudflared **127.0.0.1:20241** |
| state paths | miniapp logs under `_ops` |
| dependencies | Cloudflare named-tunnel credentials · Telegram Mini App |
| credentials required | `C:\Users\Armin\.cloudflared\f62ab442-7292-4f42-beb5-b4af4c88c3ae.json` · `cert.pem` · Telegram initData validation secrets in env (names in `.env` / flags: `OCTOPUS_MINIAPP_*`) |
| write targets | local gateway state |
| external effects | public HTTPS via Cloudflare → 8774 |
| safe shutdown | stop tunnel then gateway; watchdog will revive unless STOP pattern exists for miniapp (see watchdog script; not executed) |
| rollback point | named tunnel stays at Cloudflare account; local creds stay on laptop |
| proposed_target | redesign (tunnel identity + 127.0.0.1 bind) |
| migration risk | high — public surface |
| **class** | **MUST_BE_REDESIGNED** |

4d `brain/telegram_bot.py` is TCB-listed; **no** separate process. Treat as part of `4d_daemon`.

---

## 8. monitoring / telemetry

### pulse_telemetry

| Field | Value |
|---|---|
| service_name | `pulse_telemetry` |
| current_host | DESKTOP-KA9RFN5 |
| executable/config | writers: organism/cortex/cockpit · files under `_ops/state/pulse/` |
| startup | as part of loops |
| ports | none |
| state paths | `beat-state.json` · `tg-center.json` · `fourd-health-latest.json` (advisory) · arbiter/heart/math jsonl |
| dependencies | organism/4d |
| credentials required | none |
| write targets | `_ops/state/pulse/` |
| external effects | none |
| safe shutdown | n/a |
| rollback point | files are rolling; git may not track all |
| proposed_target | **read-only mirror** on `.180` |
| migration risk | low if replica is RO; high if a second writer appears |
| **class** | **CAN_REPLICATE_TO_180** |

### poisoning_watch_4d

| Field | Value |
|---|---|
| service_name | `OCTOPUS 4d Poisoning Watch` |
| current_host | DESKTOP-KA9RFN5 |
| executable/config | `_ops\audit\poisoning_watch_4d.py` |
| startup | ~6h · LastResult 0 · last 2026-08-17 22:08 |
| ports | none |
| state paths | append `06-EVIDENCE/POISONING-WATCH-4d.md` |
| dependencies | 4d db · semantic_memory · daemon liveness |
| credentials required | none |
| write targets | `06-EVIDENCE/POISONING-WATCH-4d.md` (canonical vault) |
| external effects | none |
| safe shutdown | disable task |
| rollback point | evidence markdown history |
| proposed_target | laptop |
| migration risk | medium — dual append |
| **class** | **MUST_STAY_ON_LAPTOP** |

---

## 9. Git / bundle jobs

### germline_hourly_git

| Field | Value |
|---|---|
| service_name | `germline-hourly` |
| current_host | DESKTOP-KA9RFN5 |
| executable/config | `04 - Architect System\scripts\germline-hourly.ps1` · dotsources `git-serialize.ps1` |
| startup | scheduled `germline-hourly` · last 2026-08-18 01:49 · LastResult **0** (script treats throttled fail as OK) |
| ports | none |
| state paths | `E:\germline\hourly.log` · `hourly-state.json` · `hourly-latest.bundle` · `_ops/backup/gitwrite.lock` · **`GITWRITE-FAILED.flag`** |
| dependencies | `F:\backup\.git` · `E:\germline\vault.git` |
| credentials required | Windows file ACLs on E: (task user Armin) — not a token file |
| write targets | `E:\germline\vault.git` (push --all / --tags) · bundle fallback · `_ops` robocopy to `E:\germline\state-hourly` |
| external effects | none beyond offbox disk |
| safe shutdown | disable task (owner); do not run overlapping git writers |
| rollback point | `hourly-latest.bundle` · do **not** delete GITWRITE-FAILED |
| proposed_target | **must stay** with canonical git |
| migration risk | **critical** |
| **class** | **MUST_STAY_ON_LAPTOP** |

Live: last log line `2026-08-18 01:53:51 OK PUSH-FAIL (fallback throttled, 0.8h of 6h; push err: ) +state`. Root cause of empty `push err:` is `--tags` reject of `pre-deploy-2026-07-25` (separate evidence). **Separate incident from network / `.180`.**

`git-serialize.ps1` is a library, not a task. Same class as hourly (canonical git lock).

---

## 10. backup

### germline_daily_backup

| Field | Value |
|---|---|
| service_name | `germline-daily` |
| current_host | DESKTOP-KA9RFN5 |
| executable/config | `04 - Architect System\scripts\germline-backup.ps1` |
| startup | 03:30 daily · LastResult **1** on 2026-08-17 03:30 |
| ports | none |
| state paths | `E:\germline\vault-latest.bundle` (mtime 2026-08-07 — **stale vs daily fail**) · `vault-latest.bundle.prev` · `state-latest` · `last_backup_manifest.json` (2026-08-07) |
| dependencies | git fsck · ledger verify · git-serialize lock |
| credentials required | same as hourly |
| write targets | `E:\germline\` only (not live vault writes) |
| external effects | restore-drill clone in `%TEMP%` |
| safe shutdown | disable task |
| rollback point | `vault-latest.bundle` / `.prev` |
| proposed_target | laptop + E: offbox |
| migration risk | **critical** if `.180` pretends to be offbox without E: |
| **class** | **MUST_STAY_ON_LAPTOP** |

### e_germline_offbox

| Field | Value |
|---|---|
| service_name | `e_germline_offbox` |
| current_host | local disk `E:\germline` on this PC |
| executable/config | bare `vault.git` · `octopus.git` · bundles |
| startup | n/a (store) |
| ports | SMB share may exist for boards (not probed this pass) |
| state paths | `E:\germline\**` |
| dependencies | physical E: |
| credentials required | SMB creds live on boards (not read) |
| write targets | offbox only |
| external effects | Sensorium/legs mount RO/RW per alignment note |
| safe shutdown | n/a |
| rollback point | bundles |
| proposed_target | **not** `.180` by default; `.180` ≠ E: |
| migration risk | **critical** |
| **class** | **MUST_STAY_ON_LAPTOP** |

---

## 11. queues

### board_cp_command_queue

| Field | Value |
|---|---|
| service_name | `board_cp_command_queue` |
| current_host | DESKTOP-KA9RFN5 |
| executable/config | `_ops/board_cp/queue.py` · db `_ops/state/board_cp/commands.sqlite` (16384 bytes, mtime 2026-08-17 23:57) · override env `OCTOPUS_BOARD_CP_DB` |
| startup | in-process with board-cp |
| ports | via 8801 |
| state paths | commands.sqlite WAL |
| dependencies | board_cp_tls |
| credentials required | bearer for pull/ack |
| write targets | sqlite |
| external effects | board command dispatch |
| safe shutdown | stop board-cp (not done) |
| rollback point | sqlite file |
| proposed_target | moving listener without moving **the** queue = split brain |
| migration risk | **critical** |
| **class** | **MUST_BE_REDESIGNED** |

### telegram_approval_queues

| Field | Value |
|---|---|
| service_name | `telegram_approval_queues` |
| current_host | DESKTOP-KA9RFN5 |
| executable/config | `_ops/telegram_center/approval_store.py` |
| startup | used by center.py / organism |
| ports | none |
| state paths | `_ops/state/telegram/approvals/*.json` · `_octopus/state/approvals.json` |
| dependencies | telegram_center |
| credentials required | none |
| write targets | those paths (LockedJson) |
| external effects | owner verdicts via Telegram |
| safe shutdown | with telegram_center |
| rollback point | approval json files |
| proposed_target | laptop |
| migration risk | high — dual-write already a known VQ |
| **class** | **MUST_STAY_ON_LAPTOP** |

### fourd_digest_queue

| Field | Value |
|---|---|
| service_name | `fourd_digest_queue` |
| current_host | DESKTOP-KA9RFN5 |
| executable/config | inside 4d daemon (`daemon_state.json` digest.queued **55**, sent_today 0, cap 3) |
| startup | 4d_daemon |
| ports | none |
| state paths | daemon_state.json digest block |
| dependencies | Telegram for flush |
| credentials required | `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` (4d `.env`) |
| write targets | daemon_state |
| external effects | Telegram if flushed |
| safe shutdown | with daemon |
| rollback point | daemon_state |
| proposed_target | laptop |
| migration risk | medium |
| **class** | **MUST_STAY_ON_LAPTOP** |

---

## 12. secrets / credentials

See companion [[SECRET-INVENTORY-REDACTED-2026-08-18]]. SoT files stay on laptop. **Class of the secrets service:** **MUST_STAY_ON_LAPTOP**.

| Field | Value |
|---|---|
| service_name | `secrets_sot` |
| current_host | DESKTOP-KA9RFN5 |
| executable/config | `F:\backup\.env` · `_ops\OCTOPUS.env` · `4d_system\.env` · `C:\Users\Armin\.octopus-signing\octopus-owner-ed25519-private.pem` · cloudflared json |
| startup | loaded by BAT/python at process start |
| ports | n/a |
| state paths | those files (gitignore) |
| dependencies | owner |
| credentials required | (the files themselves) |
| write targets | must not be copied to `.180` by agents |
| external effects | every networked service |
| safe shutdown | n/a |
| rollback point | `.env.bak-20260810` exists (do not commit) |
| proposed_target | laptop until Promotion Receipt + owner-controlled secret provisioning |
| migration risk | **critical** |
| **class** | **MUST_STAY_ON_LAPTOP** |

---

## 13. owner decisions

### owner_verdicts_and_flags

| Field | Value |
|---|---|
| service_name | `owner_verdicts_and_flags` |
| current_host | DESKTOP-KA9RFN5 |
| executable/config | `_ops/owner-verdicts.yaml` (git-tracked, no secrets) · `_ops/OCTOPUS-flags.cmd` (gitignore; env wins) · `02-DECISIONS/` · `04-SYSTEMS/DECISIONS-REGISTRY.yaml` · Inbox OWNER-PENDING |
| startup | read at process start / wiring.effective_flag |
| ports | n/a |
| state paths | those files |
| dependencies | owner |
| credentials required | none in verdicts.yaml by contract |
| write targets | flags.cmd is machine-local; verdicts.yaml is vault SoT |
| external effects | all OCTOPUS_* wires |
| safe shutdown | n/a |
| rollback point | git history of owner-verdicts.yaml · do not dual-edit flags on two hosts |
| proposed_target | laptop |
| migration risk | **critical** — autonomy/flags drift |
| **class** | **MUST_STAY_ON_LAPTOP** |

---

## 14. TCB signing

### tcb_signing_ceremony

| Field | Value |
|---|---|
| service_name | `tcb_signing_ceremony` |
| current_host | DESKTOP-KA9RFN5 (owner profile + vault) |
| executable/config | `4d_system/scripts/generate_trust_boundary.py` · `openssl pkeyutl -sign` · public `F:\backup\_ops\owner-signing\octopus-owner-ed25519-public.pem` · private `C:\Users\Armin\.octopus-signing\octopus-owner-ed25519-private.pem` (exists, 122 bytes) · manifest `4d_system/config/trust-boundary.json` · `trust-boundary.json.sig` (64 bytes) |
| startup | owner ceremony only (EQUIP G2 / JOB-RESEARCH patches still unsigned) |
| ports | none |
| state paths | json + sig · TCB file list includes `brain/daemon.py`, `brain/automation.py` |
| dependencies | openssl · owner |
| credentials required | **private Ed25519 pem** (location only) |
| write targets | json + sig in vault |
| external effects | daemon enforce `OCTOPUS_TCB_MANIFEST_ENFORCE=1` |
| safe shutdown | n/a |
| rollback point | previous signed json+sig pair |
| proposed_target | **must stay** with owner laptop until Promotion Receipt |
| migration risk | **critical** |
| **class** | **MUST_STAY_ON_LAPTOP** |

---

## 15. recovery tools

### recovery_tooling

| Field | Value |
|---|---|
| service_name | `recovery_tooling` |
| current_host | DESKTOP-KA9RFN5 (scripts in vault) |
| executable/config | `_ops/deploy/rollback-from-snapshot.ps1` (default dry-run; snapshots `E:\deploy-snapshots\`) · germline restore-drill inside `germline-backup.ps1` · `_ops/RESTART-BOARDCP.ps1` · `RESTART-ALL.ps1` · `RESTART-CORTEX.ps1` · `RESTART-PROCESS.ps1` · `stop-organism.ps1` · STOP/HALT flag files |
| startup | on-demand; **none run this pass** |
| ports | n/a |
| state paths | `E:\deploy-snapshots\` (not listed in depth this pass) |
| dependencies | live tree `F:\backup` · E: |
| credentials required | none extra |
| write targets | **would** mutate live tree if `-Apply` — not used |
| external effects | process kill/start if restart scripts used — **not used** |
| safe shutdown | n/a |
| rollback point | the tools **are** the rollback; dry-run default |
| proposed_target | **script copies** may live on `.180`; **execution against canonical tree** stays on laptop |
| migration risk | medium for copies; critical if Apply from two hosts |
| **class** | **CAN_REPLICATE_TO_180** |

---

## Out of scope / noted but not classified as OCTOPUS always-on duties

- Cursor / Claude desktop / Phantom MCP node (workstation agents, not organism daemons)
- ExpressVPN local ports 2020–2022 (VPN helper)
- OneDrive / Firefox updater tasks
- Existing `ssh.exe` listeners 5501/5557/9893 — **another agent**; this workstation did not use them
- `_ops/handshake/` is **not** the 4d daemon (confirmed)

## Incident separation (mandatory)

1. **Wi-Fi / SSH / envelopes** — other agent. Not this inventory.
2. **GITWRITE-FAILED / hourly `--tags`** — git identity incident. Does **not** unblock `.180` and `.180` does **not** clear it.
3. **Canonical migration / Promotion Receipt** — not started. `.180` remains continuity-candidate.
