---
type: owner-review
id: GATE-9-SEE-DIFF
status: ratified-this-sha256
lane: T-LANE-TRIAGE-20260905
created: 2026-09-05
---

# Doctor gate 9 — the diff you asked to see

D4 = SEE-DIFF. This is viewing. It is **not** `allow_sanctum=true`.

## What is not on disk

`OCTOPUS-DOCTOR/90-_meta/state/missions.json` has `missions_open = 0` (vitals: 2 missions, both `merged`). There is no waiting PatchSet that `PatchSet.gate(allow_sanctum=False)` is currently blocking.

Outbox−inbox this session: `doctor-pulse`/`diff` and `voice-test-20260815`/`test` (9 outbox keys, 8 inbox). Stale cards, not a sanctum apply.

IGN-2 (`ign2-pathology-slice-guard`, commit `50d15e4`) passed gates 1–8 and did **not** touch sanctum (`ign2-closeout-receipt.json`: `PASS gates 1-8 (sanctum نه)`).

## What is on disk — the half-thread

`_ops/os_v1/mission_runner.py` is in SANCTUM (`propose.py` SANCTUM tuple includes `mission_runner.py`).

The file header says it was restored on 2026-09-05 by an agent, **not** through the doctor PatchSet pipeline, because sending a guard-hand change through the pipeline would hit gate 9.

| Field | Value | Source |
|---|---|---|
| path | `_ops/os_v1/mission_runner.py` | this host |
| lines | 303 | `Get-Content` count this session |
| sha256 | `522AB60E53591293EFB2CFAE3797AC2AA1C9953AEFBE90990A2A3D16C8FA816A` | `Get-FileHash` this session |

## What the file does (full text is the file itself)

1. `MissionRunner.run` — `git worktree add --no-checkout --detach`, sparse-checkout `/_ops/**` only, baseline suite, apply patch, candidate suite, compare regression (new failures only).
2. Live-tree fingerprint via `git status --porcelain=v1 --untracked-files=no` (untracked outside `_ops` is not in the fingerprint — the file states this limit).
3. `may_merge` requires no new failures, live tree untouched, candidate exit not 124/125, timed_out set unchanged.
4. `MissionRunner.merge` copies named files from the worktree to live only if live matches HEAD, writes a rollback manifest, then commits **only those paths**.
5. The commit message inside `merge()` is hardcoded to the IGN-2 pathology sentence (lines 280–282). A later mission would still get that message unless the file is changed again — that second change would be another gate-9 event.

## Gate 9 rule (unchanged)

From `OCTOPUS-DOCTOR/doctor/propose.py` `PatchSet.gate`: if `touches_sanctum` and not `allow_sanctum`, raise. `allow_sanctum` is owner-only after seeing the full diff.

SANCTUM names: `/tests/`, `test_`, `run_all.py`, `conftest.py`, `propose.py`, `policy_sampler.py`, `honest_metric.py`, `mission_runner.py`, `efe.py`, `router.py`, `channel.py`, `daemon.py`, `outcome_ledger.py`, `10-قوانین/`, `R-0`.

Law: `OCTOPUS-DOCTOR/10-قوانین/R-09-قانونِ-حریم.md`.

## Name collision (both kept)

| ID | Meaning | Status this session |
|---|---|---|
| Doctor gate 9 | sanctum / `allow_sanctum` | this file — shown, not ratified |
| GATES-31 gate 9 | OwnerRelease / M5 | different object; not decided here |

## Follow-up — decided

Owner **RATIFY** for `_ops/os_v1/mission_runner.py` sha256 `522AB60E53591293EFB2CFAE3797AC2AA1C9953AEFBE90990A2A3D16C8FA816A` only.

Receipt: `OWNER-RATIFY-GATE9-MISSION-RUNNER-20260905.json`.

A later edit of this file, or any other SANCTUM path, needs a new viewing + new allow.
