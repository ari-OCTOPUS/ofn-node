# 10 — Safe restart plan (not executed)

This run does **not** restart the organism — restart is explicitly out of scope for this
session (master instruction §2: "no blind live activation," "restart کور ممنوع").

## Current state

- `_ops/state/ORGANISM-STATE.json` was written ~3 minutes before this check (organism is
  actively ticking).
- That process's environment was captured at whatever time it last booted — **before**
  today's flag edits (`OCTOPUS_INTERACTION_LOG`, `OCTOPUS_ARM_SENSITIVE_DEFAULT`, etc.) were
  made to `OCTOPUS-flags.cmd`. Env vars a process inherited at exec() time do not update
  live from a file changing on disk.
- `arm_gate_enforcing: false` in the live state file reflects `OCTOPUS_REQUIRE_ARM` being
  unset in that process's env — unrelated to and unaffected by today's edits, since
  `OCTOPUS_REQUIRE_ARM` was never on the owner-approved list to begin with (only the
  narrower `OCTOPUS_ARM_SENSITIVE_DEFAULT` was).

## If/when the owner decides to restart

1. Confirm no in-flight mission/paid-call is mid-flight (check `_ops/state/missions.json`,
   `paid-calls.jsonl` tail) — a restart mid-call is safe per the existing
   `STOP-ORGANISM`/`RESTART-REQUESTED` protocol (`RUN-ORGANISM.bat` never deletes
   `STOP-ORGANISM` itself — the owner kill-switch cannot be silently revoked by any
   automated path), but is still worth a glance.
2. The safe path already exists in the codebase: create `_ops/RESTART-REQUESTED`, or use the
   dashboard's restart control, rather than killing the process directly.
3. On restart, `RUN-ORGANISM.bat:26` re-sources `OCTOPUS-flags.cmd` — the 7 flags become
   effective for the new process immediately, no code change needed.
4. Expected observable effect after restart: `OCTOPUS_ARM_SENSITIVE_DEFAULT=1` and
   `OCTOPUS_INTERACTION_LOG=1` become live in the new process's env. **Important caveat**
   (see `12-ARM-GATE-CURRENT-TRUTH.md`): `OCTOPUS_ARM_SENSITIVE_DEFAULT=1` currently has
   **zero behavioral effect** even after restart, because `arm_gate.guard()` is not called
   from any production code path yet. Restarting alone does not close the P0 gap; wiring
   does (separate owner decision, see `14-ARM-GATE-PATCH-REPORT.md`).

**This run does not recommend restarting yet** — recommend deciding on the arm_gate wiring
question first (§`28-OWNER-DECISIONS.md`), since a restart done now would create a false
sense that arm-gating is active when it structurally is not.
