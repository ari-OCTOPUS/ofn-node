# 09 — Dangerous flags check

| Flag | Required state | On-disk (`_ops/OCTOPUS-flags.cmd`) | Effective (fresh source) |
|---|---|---|---|
| `OCTOPUS_WIRE_HARVEST` | 0 | `=0` (line 25) | `0` |
| `OCTOPUS_WIRE_POCKETSMITH` | 0 | `=0` (line 267) | `0` |
| `OCTOPUS_WIRE_PS_WRITEBACK` | 0 | `=0` (line 297) | `0` |
| `OCTOPUS_WIRE_MISSION_RUNNER` | 0 | `=0` (line 340) | `0` |
| `OCTOPUS_NEURAL_LEARNED_APPLY` | 0 / off | not in file | absent → code default OFF |

**PASS — no HALT condition.** All five dangerous flags are confirmed off both on disk and
in a fresh-source simulation. No owner-approved arming of any of these five happened in this
run, and none should — none are on the owner-approved list.
