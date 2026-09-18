# BOARD138-CAPABILITY-MAP — measured 2026-09-08 (lane OCTOPUS-138-WIRING-20260908)

GOV_VERSION=V8 · LADDER=L2
All values below are LIVE PROBES (ssh BatchMode, read-only) with timestamps.
Probe windows: 03:21:36Z / 03:22:02Z / 03:22:36Z / 03:23:41Z (2026-09-08 UTC).

## Host & resources (measured)
- Host: DietPi · up 21d20h40m · load 0.96/1.07/1.12
- RAM: 3910 MB total, **3279 MB available** (no swap)
- Disk: 58G root, 40G free (29% used)

## Reachability from laptop (measured)
- `ssh -o BatchMode=yes board138 'echo ok'` → OK, **0.198s** round-trip (03:23:41Z)
- Full inventory batch (~15 commands) → **0.593s** (03:21:36Z)

## Services & runtime (measured)
- `ofn.service` = **active**; PID 3905410 owns 127.0.0.1:8791–8794
- Octopus fleet RUNNING: octopus-bridge (board half of board_cp pull protocol),
  octopus-control-router (control plane), octopus-cycle-settler (reconciliation),
  octopus-router (queue loop), octopus-supervisor (worker health + SAFE_HALT),
  octopus-verify-dispatcher (auto verify dispatch + settle)
- Timers ACTIVE (next-fire measured): ofn-bridge-watchdog 2min · ofn-sync-watchdog
  ~5min · budget-monitor 5min · glass 5min · mesh-consume 5min · **imap 8min** ·
  quote 20min · plus absence / brainwake / doctor / drill / heartbeat waiting
- **octopus-drill.service = FAILED** (measured twice, 03:22–03:23Z) — incident, untouched

## Listeners (ss -tln, measured 03:21:36Z)
- 0.0.0.0:22 · 127.0.0.1:20241 (owner not visible without root) ·
  127.0.0.1:8791–8794 (ofn PID 3905410) · 8796 (pid 2986615) · 8895 (pid 2986309)
- **:8081 NOT LISTENING** · **:11434 NOT LISTENING**

## Brains on 138 (measured — CONTRADICTION with memory, resolution: null, status: open)
- llama.cpp :8081 → `Connection refused` (03:22:02Z); no llama process in `ps aux`;
  no llama-server/llama-cli binary found under /home/ari (maxdepth 3)
- Ollama :11434 → connection refused (not installed/not running)
- ⇒ Memory claim "llama 8081" is **stale as of 2026-09-08**; do not plan against it
  without owner GO to reinstall/restart. Red line kept: we did NOT start anything.

## Browser on 138 (measured)
- chromium/chromium-browser/google-chrome: **absent** (dpkg -l empty; /usr/bin scan empty)
- ⇒ PR #141 / ziman_tender_harvest browser pattern currently has NO runtime on 138.

## Non-observations (honest)
- journalctl for octopus-bridge returned nothing for user `ari` (journal permission
  gap — observability limitation, not service failure).
- mesh/audit trees not enumerated this session (git-less by design; pre-image
  receipts only). VITAL-DATA cites audit 233k+ rows on standing-GO.
