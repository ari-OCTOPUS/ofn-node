---
type: evidence
created: 2026-08-18
updated: 2026-08-18
tags: [ops, germline, hourly-push, p3, tcb]
author: "custodian-191"
---

# P3 ceremony — PATCH_TESTED · TCB_APPROVED · ACTIVATED

Limited ceremony for hourly push diagnostics. This is **not** a 4d `daemon.py` / `automation.py` TCB sign.

## Status

| token | value |
|---|---|
| PATCH_TESTED | yes |
| TCB_APPROVED | yes (P3 allowlist only) |
| ACTIVATED | yes (wired into existing `\germline-hourly`) |
| SCHEDULED_CYCLE_OBSERVED | **no** |
| DIAGNOSTICS_VERIFIED | **no** |
| ROLLED_BACK | no |
| HALTED | no |

`E:\germline\hourly-push-errors.jsonl` does not exist yet. Last hourly line: `2026-08-18 03:50:30 FAIL git-write lock TIMEOUT`. `gitwrite.lock` was in use (mtime 03:30+10). Flag `GITWRITE-FAILED` was **not** cleared. Lock was **not** stolen. Timer was **not** changed. Success was **not** simulated.

## Allowlist

- `04 - Architect System/scripts/hourly-push-error-capture.ps1`
- `04 - Architect System/scripts/germline-hourly.ps1`
- `04 - Architect System/scripts/test-hourly-push-error-capture.ps1`

Push argv still `push --quiet $BARE --all` then `--tags`. Fallback/remotes/credentials unchanged.

## Tests (offline)

- `test-hourly-push-error-capture.ps1` **PASS** — redact, failure `REMOTE_NOT_FOUND`, success `NONE`, lock `LOCK_FAILURE`, `--tags` `REF_REJECTED`, schema v1, phases `all`/`tags`/`github_wire` separate
- `test-git-serialize.ps1` **PASS** — temp repo only
- not registered in `_ops/tests/run_all.py`

## Hashes (2026-08-18T04:16:12+10)

| file | sha256 |
|---|---|
| hourly-push-error-capture.ps1 | `697d47e5a7465ffb9e74b5d6025ccde1a85cdabfd434f8b1ceae05a211a8344f` |
| germline-hourly.ps1 | `78a8ff095e01caff7dc0d7bc676660d6754a9c818017724250337d1f346d2171` |
| test-hourly-push-error-capture.ps1 | `3afd6212c149b63850ee29816bda5804be5df5dc240a582b650d750ba7365c97` |
| germline-hourly.diff | `c82a394141df263f662792d47b5cd397ed199a4bd6c675597d86804f2300a2eb` |

Archive: `06-EVIDENCE/p3-tcb-2026-08-18/`

`github_wire` rows are `remote_class=absent` (no GitHub remote on `F:\backup`). That skip is **not** a GitHub heartbeat.
