# RECEIPT — A7 SWAP DRILL (owner GO 2026-09-18 «GO A7»)

**Lane:** OCTOPUS-AUTOSEND-LOOP-20260918 · **Node:** board138 (192.168.0.138) ·
**Window:** 2026-09-17 23:29:54Z (PRE) → 23:31:5x reboot → 23:33:20Z (witness pulse resumed)

## What the drill proves
That the 2 GB swapfile added on 2026-09-17 (S1POL-SWAP-138) is **persistent across a
reboot** (fstab entry honoured) and that the whole 45-timer organism comes back
unattended — including the automation deployed minutes earlier.

## Evidence (files in this folder)
| field | PRE | POST |
|---|---|---|
| boot_id | 4f3f2c05-5703-4cbb-92c3-6fed8ff708bd | changed (real reboot) |
| uptime | 2 days 22:50 | up 0 minutes |
| swap | /swapfile 2097148 KB, 2048 used | **/swapfile 2097148 KB, 0 used — came up by itself** |
| running services | 20 | 22 |
| timers | 45 | 45 (**none lost**) |
| failed units | 1 (smartmontools.service — pre-existing) | 1 (same unit) |
| ofn HEAD / dirty | fe0c55e0 / 48 files | fe0c55e0 / 48 files (unchanged) |
| octopus-owner-ask.timer | active | active |
| owner-ask registry cards | 3 | 3 |
| Shopify token present | yes (38 chars) | yes (38 chars) |

**Witness (independent, hub-side):** `06-EVIDENCE/FLEET-HEARTBEAT-CANONICAL.md` —
the hub consumer stopped recording pulses for 138 exactly during the reboot and they
resumed on their own:
`23:29:46Z` → *(gap — reboot)* → `23:33:20Z 138 load1=1.51` → `23:34:21Z 138 load1=2.11`.
The executor is 138; the witness is the hub on the laptop — not the same process.

## Notes / honest limits
- `systemctl reboot` printed `Call to Reboot failed: Unit dbus-org.freedesktop.login1.service
  failed to load properly ... File exists` — the logout/wall-message path is broken on this
  image, **but the reboot itself executed** (boot_id changed, 110 s of SSH down, pulse gap).
  This logind unit-file oddity is a real (minor) defect worth fixing on a later window; it
  does not affect `reboot -f` semantics or the drill result.
- Swap used 0 after boot is expected (cold start).

## Rollback
No state was mutated by the drill. If the drill had failed to return, the fallback is the
documented physical access path; nothing else was required here.
