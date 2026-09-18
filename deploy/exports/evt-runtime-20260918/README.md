# EVENT-DRIVEN runtime export — board 138 (2026-09-18)

DEEPSCAN-7D defect D7: the entire EVENT-DRIVEN-OCTOPUS runtime (installed on
board 138 between 2026-09-17 and 2026-09-18) existed **only on the board** —
zero git record. A disk loss on 138 would have destroyed the architecture.
This export is the reviewable, hash-pinned snapshot of that runtime.

## What is here (origin paths on 138)

| Export path | Origin on 138 |
|---|---|
| `units/etc/systemd/system/octopus-evt-*.service` (9) | `/etc/systemd/system/` |
| `units/etc/systemd/system/octopus-evt-*.path` (9) | `/etc/systemd/system/` |
| `units/etc/systemd/system/octopus-evt-janitor.{service,timer}` | installed 2026-09-18 by lane OCTOPUS-DEEPSCAN-7D-20260918 (fix D1) |
| `tools/octopus_event_gate.sh` | `/home/ari/ofn/tools/octopus_event_gate.sh` (v2, holds stale-beat files in `state/events/held/`) |
| `tools/octopus_evt_janitor.py` | `/home/ari/ofn/tools/octopus_evt_janitor.py` (new, D1) |
| `state/events-mode.json` | `/home/ari/ofn/state/events/mode.json` — per-gate shadow/live switch |
| `state/standing-authorization.json` | owner grant: email wave, daily_cap 60, expires **2026-10-02T02:58:30Z** |
| `state/channel-authorization.json` | owner grant for the email channel |

No secrets are present (verified: no token/key/env values in any exported file).

## How the runtime works

`octopus-evt-<name>.path` watches event dirs / trigger files → starts
`octopus-evt-<name>.service` → `octopus_event_gate.sh <name> <dirs> -- <cmd>`:
stale beat (>150 s) ⇒ fail-closed hold (`state/events/held/`), shadow mode ⇒
SHADOW_WOULD_RUN receipt only, live mode ⇒ run + move event files to
`processed/` + receipt. Modes per name live in `state/events/mode.json`.

The janitor archives inbox files of kinds with **no consumer path unit**
(`packet_staged`, `packet_sent`, `packet_failed`, `revenue_review`,
`traffic_seen`, `selftest`, `orders`) older than 24 h into
`state/events/archive-inbox/` — move-only, the sha256-chained
`state/events/ledger.jsonl` is never touched.

## Install / rollback (on a DietPi-like board)

Install: copy units to `/etc/systemd/system/`, tools to `~/ofn/tools/`,
`systemctl daemon-reload`, `systemctl enable --now <unit>.path` per consumer,
`octopus-evt-janitor.timer` likewise. Rollback: disable + remove the units and
restore the previous tools files. The authorization files are OWNER GRANTS —
do not install them anywhere without an explicit owner decision.

## Provenance

- Lane: `09-LANES/OCTOPUS-DEEPSCAN-7D-20260918` (vault F:\backup)
- Snapshot taken 2026-09-18 ~11:15Z over SSH from ari@192.168.0.138
- Integrity: see `SHA256SUMS` (computed over the exported copies)
- Live drift risk: board files may keep evolving; this export pins today.
