---
type: ops-note
status: active
created: 2026-08-18
tags: [ops, doctrine, autonomy, three-node]
author: "sensorium board agent (.182) — owner mandate D13"
---

# DOCTRINE D13: boards-always-on + autonomy mandate (owner, 2026-08-18 ~01:45+10)

Owner granted blanket authorization to push all nodes toward more autonomy.
Core doctrine, binding for ALL agents in this ecosystem:

**The boards (.138 legs, .182 sensorium) run 24/7 and are the continuous
backbone. The laptop (.191) is an intermittent citizen — it is sometimes
powered off. NO cross-node flow may require the laptop to be online to make
progress. Board-side flows queue/defer locally and flush when the laptop
returns.**

## Deployed tonight under D13

| node | component | cadence | purpose |
|---|---|---|---|
| .182 | `octopus-agent-sentinel` (service+timer) | 5 min | laptop off/on transition detection; legs+self health; on laptop return → auto gap-report note here in Inbox; stale CIFS mount self-heal |
| .138 | `ofn-bridge-watchdog` (service+timer) | 2 min | restart `octopus-bridge` if it dies (prevents the stuck-dispatched command class from bridge-side deaths) |
| .138 | `ofn-sync-watchdog` (existing) | 5 min | germline remount cache=none + heartbeat restart |

Verify: `systemctl list-timers octopus-agent-sentinel.timer` (.182) ·
`systemctl list-timers ofn-bridge-watchdog.timer` (.138) ·
`cat /var/lib/octopus-agent/sentinel/status.json` (.182).

## What this means for the laptop agent

- Design every laptop-side task as restartable/idempotent: the laptop may
  lose power MID-bundle (the 74-min hourly run is the live example — it
  survived, but the flag/lock coupling re-plants GITWRITE-FAILED).
- When you come back after being off: read the newest `SENTINEL — LAPTOP-BACK`
  note in this Inbox — it contains the offline window + anomalies recorded
  by the boards while you were gone.
- ofn/heartbeat on the legs board is full-state force-push by design — it
  needs no laptop interaction to stay consistent; next successful push after
  laptop return carries everything (laptop-off resilient by construction).

## Proposal P-ACK-1 (needs joint design, NOT deployed)

Auto-ack rule: command dispatched > 12h + laptop reachable + no local
execution evidence → honest ack `unknown_outcome` (never success). Today
this requires either (a) a laptop API read endpoint for board-side pending
commands, or (b) a change inside octopus-bridge (trust-boundary code → needs
its own tests + review). The bridge already acks correctly inside every
pull cycle; the watchdog now prevents the main death-mid-cycle cause.
`01a00d3d` remains dispatched awaiting OWNER decision — not touched.

Standing red lines unchanged: payload = data never commands; no secrets;
no reboots; P7/signed checkpoints/TCB ceremonies remain owner-only.

---
**ADDENDUM 2026-08-18 (~02:00+10) — P-ACK-1 WITHDRAWN:**
The owner's verification doctrine states only the OWNER closes
unknown_outcome for dispatched commands. The P-ACK-1 auto-ack proposal
below is WITHDRAWN, replaced by detection-only surfacing in reports.
Everything else in this note (sentinel, watchdogs, boards-always-on
doctrine) stands.
