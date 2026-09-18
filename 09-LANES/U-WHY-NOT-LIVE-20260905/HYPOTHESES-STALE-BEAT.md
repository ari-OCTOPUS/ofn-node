---
type: note
status: active
tags: [octopus, diagnosis, this-host-only]
created: 2026-09-05
updated: 2026-09-05
lane: U-WHY-NOT-LIVE-20260905
---

# Stale-beat hypotheses (instrumented, not yet judged)

Runtime before instrument restart (`debug-f16420.log` runId `stale-beat-1`):
PID 15884 alive, listen 8771, `uptime_s=228` source this-host probe, CPU 4.56s, `ORGANISM-STATE.json` mtime still `2026-09-04T14:46:26+10`.

`_memory/HEARTBEAT.md` last organism lines: START + wiring + telegram poll at `2026-09-05T15:26:18`–`15:26:26`. No later `organism=ok`.

| id | claim | how logs decide |
|---|---|---|
| H12 | First tick blocked before `_write_state` | `tick_enter` without `post_write_state` |
| H13 | Process died | listen_pid gone (pre-restart already REJECTED) |
| H14 | Tick exception path | `tick_error` present |
| H15 | Sleeping 300s after a write | `pre_sleep` plus state mtime advanced |
| H17 | Boot never reached `while True` | `http_bound` without `boot_loop_ready` / `tick_enter` (HEARTBEAT already leans reject) |
| H18 | Heart v2 `_hrt.tick()` blocks (flag file on; `heart_brain` → local Ollama, known hang) | `pre_heart_v2` without `post_heart_v2` |
| H19 | `telemetry.snapshot()` blocks | `post_heart_v2` without `post_snapshot` |

Judged after user repro (`stale-beat-2`, PID 27420):

- H13 REJECTED — process alive (`uptime_s=117`, source this-host probe).
- H17 REJECTED — `http_bound` + `boot_loop_ready` in `debug-f16420.log`.
- H18 REJECTED — `post_heart_v2` present.
- H19 REJECTED — `post_snapshot` present; `telemetry-latest.json` mtime `2026-09-05T15:37:07+10`.
- H21 REJECTED — `post_memory_read` `status=OK`.
- H14 REJECTED — no `tick_error`.
- H15 REJECTED — no `pre_sleep`; state mtime still `2026-09-04T14:46:26+10` at T+117s.
- H12 CONFIRMED — first tick still in body after snapshot; `_write_state` only at tick end. Same tick wrote fitness/replication/fisher/evo-lab worktrees (`_ops/state` mtimes 15:37–15:38). Cause: default `OCTOPUS_PROFILE=paper-full`.

Fix (kept instrumentation): early `_write_state` after bind and after snapshot; B-safe starter uses `OCTOPUS_PROFILE=bare` + paper-full flags forced `0` + `OCTOPUS_LIBRARY_LOOP=1` (no organism Telegram channel).

Post-fix (`runId=post-fix`, PID 18452): API `ts=2026-09-05T15:42:08`, `tick_phase=after_snapshot`, `beat=61575`. Source: `GET http://127.0.0.1:8771/api/organism`.
