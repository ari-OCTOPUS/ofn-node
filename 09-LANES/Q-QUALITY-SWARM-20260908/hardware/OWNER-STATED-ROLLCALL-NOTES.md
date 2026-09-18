---
type: evidence
lane: Q-QUALITY-SWARM-20260908
created: 2026-09-08
gov: V8
ladder: L2
---

# OWNER-STATED roll-call — notes (no assumption)

CSV: `OWNER-STATED-ROLLCALL.csv`  
Columns required: `board_type, serial, mac, claimed_location, powered_on`

## Source (only)

| Claim | Value | Source |
|---|---|---|
| Fleet count | 16 Orange Pi 5 Pro + 140 ESP32 (+ 2 FPGA excluded) | `03 - Projects/Mining/Hardware Registry & Runbook.md` §1, owner rewrite 2026-07-28; D-008 |
| Physical state | all off (`powered_on=false`) | same table, column «وضعیتِ فیزیکی» |
| Location | Sydney, one site | same file §1; D-009 (two-site plan is research-only, not executed) |
| Per-device serial | not stated | same file §2: «این جدول عمداً خالی است» |
| Per-device MAC | not stated | same file §2; IP/SSH never written here |

FPGA rows are omitted: the prompt asked only Orange Pi / ESP32.

## What was not invented

- No serial numbers
- No MAC addresses
- No IP / Tailscale names
- No health / last-seen
- Skeleton IDs `OPI-01…16` / `ESP-001…140` exist in the registry as **empty slots**, not as measured identity. They were **not** copied into `serial`.

Row count: **156** = 16 + 140. Source: Hardware Registry §1.

## First device to power

Owner order of fill (`Hardware Registry & Runbook.md` §2): **OPI-01 first** (Orange Pi), then other OPI, **ESP32s after at least one OPI is stable**.

No owner-stated «first ESP32». Designating `ESP-001` as first-to-power would be an assumption. Status: `OWNER_DECISION`.
