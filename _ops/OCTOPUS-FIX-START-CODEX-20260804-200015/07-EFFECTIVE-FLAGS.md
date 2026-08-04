# 07 — Effective flags (fresh-source simulation)

Ran (read-only, no organism process touched):
```
cmd /c "call F:\backup\_ops\OCTOPUS-flags.cmd && set OCTOPUS_"
```
This simulates what a **fresh boot** of `RUN-ORGANISM.bat` would load into the process
environment right now. It does **not** reflect what the *currently running* organism process
has (that process captured its env at its own earlier start time — see `10-SAFE-RESTART-PLAN.md`).

154 `OCTOPUS_*` variables would be set. Scanned for secret patterns: clean (see
`03-SECRET-SCAN.md`). Cross-checked against the requested/forbidden lists:

**7 requested flags — all present with correct value** (see `06-FLAG-DIFF.md` table).

**5 dangerous flags:**
| Flag | Effective value |
|---|---|
| `OCTOPUS_WIRE_HARVEST` | `0` |
| `OCTOPUS_WIRE_POCKETSMITH` | `0` |
| `OCTOPUS_WIRE_PS_WRITEBACK` | `0` |
| `OCTOPUS_WIRE_MISSION_RUNNER` | `0` |
| `OCTOPUS_NEURAL_LEARNED_APPLY` | absent from file entirely → code default (OFF) applies |

**PASS.** A fresh source of the flags file, right now, would produce exactly the intended
safe state. Full 154-line redacted dump kept out of this report (no secrets in it, but no
reason to duplicate 154 lines of low-signal env noise into a committed markdown file);
available in this session's scratchpad if needed for a future diff.
