---
type: report
project: "[[04 - Architect System/architect/PROJECT]]"
status: ready
tags: [octopus, p1, runtime-plan]
created: 2026-08-29
updated: 2026-08-29
created_by: agent
language: fa
sources:
  - "[[06-EVIDENCE/OCTOPUS-REUSE-AUDIT-2026-08-29/runtime-provenance-20260828T230743Z/CHECKPOINT]]"
  - "[[03 - Projects/OFN-Board/deploy/systemd/ofn.service]]"
---

# 10 — P1 runtime activation plan (do not execute)

```text
RESTART_PERFORMED=NO
observed_at=2026-08-29T04:50:00Z
live_pid_now=UNKNOWN
truth_status=DOCUMENTED
```

| Field | Value | Source |
|---|---|---|
| current live PID | **1351408** last proven | `CHECKPOINT.md:24` (28–29 Aug). **Now: UNKNOWN** |
| current loaded code hash | UNKNOWN (no memory dump). Disk at E0 matched `/home/ari/ofn` import, not PID bytes | `CHECKPOINT.md:52-53` |
| current repo HEAD (E0) | `68813370c726a1a650a7cb2fb99207c300358db9` | `CHECKPOINT.md:27` |
| later claimed HEAD | `a27eb0536793c7fc040917bb645e9057707298f4` | `P1-RESULT.md:19` |
| target commit | `a27eb05` | owner accepted P1 source |
| unit name | `ofn.service` | vault unit + systemd-show evidence |
| ExecStart | `/usr/bin/python3 -m ofn.run` | `ofn.service:49` |
| working directory | `/home/ari/ofn` | `ofn.service:39` |
| user/home | `ari` / `/home/ari` | `ofn.service:37-39` |
| env files | `node.env`, `secrets.env` — **do not read** | `ofn.service:40-41` |
| Type | notify, WatchdogSec=30, Restart=always | `ofn.service:24-30` |

## Preflight (owner)

1. Confirm PID still 1351408 or record the new one.
2. `GIT_OPTIONAL_LOCKS=0 git -C /home/ari/ofn rev-parse HEAD` expect `a27eb05` if that is the load target.
3. Confirm ExecStart unchanged. No `OFN_KEEP_GATES_OPEN`.
4. Backup: unit file + `git status` porcelain only. Do not copy secrets.

## Restart command (requires owner approval)

```text
systemctl restart ofn.service
```

Maximum acceptable downtime: UNKNOWN (owner). Watchdog/Restart=always implies short gap if start succeeds (`TimeoutStartSec=45`).

## Post-restart proof

| Check | Accept |
|---|---|
| MainPID | ≠ 1351408 |
| loaded commit | `LOADED_COMMIT=a27eb05…` via import path hash of `cockpit_v2_read_model.py` + `node.py` |
| `OWNER_ITEMS_PRESENT` | true on authenticated V2 queue |
| `MESH_ITEMS_PARITY` | true vs pre-restart shadow shape |
| `PII_LEAKS` | 0 on allowlisted projection |
| callback failure | `degraded` or `UNKNOWN`, not fake empty-success |
| full suite | no **new** failures; `test_greeting_name` remains historical |
| frontend | `FRONTEND_EXPECTATION=EXPLICIT` — still will **not** render `owner_items` until `queue.js` changes |

## Automatic rollback trigger

UNKNOWN — not defined in unit. Manual: `systemctl restart` again on previous known-good tree. Do not `reset --hard` without GO.

Restart alone **does not** complete P1 end-to-end.
