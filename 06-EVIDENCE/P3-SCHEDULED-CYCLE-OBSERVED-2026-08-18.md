---
type: evidence
created: 2026-08-18
updated: 2026-08-18
tags: [ops, germline, hourly-push, p3]
author: "custodian-191"
---

# P3 — scheduled cycle observed · DIAGNOSTICS_VERIFIED

Writer health is **not** claimed. `GLOBAL_GITWRITE_FAILED` stays **OPEN**. Flag not cleared. Lock not stolen.

## Cycle `\germline-hourly` 2026-08-18 09:49 (+10)

Natural schedule. Not invoked by this observer.

| field | observation |
|---|---|
| lock acquisition | SUCCESS · new file mtime `09:49:11` · age ~0s |
| lock during push | `lock_state=held` on all three JSONL phases |
| lock release | SUCCESS · absent by `09:51:03` · still absent at task Ready |
| `--all` | exit 0 · `NONE` · 30 local heads match `vault.git` (0 mismatch, 0 missing) |
| `--tags` | exit 1 · `REF_REJECTED` · `pre-deploy-2026-07-25` local `dab81a82` ≠ vault `9c49f174` |
| `github_wire` | separate row · `remote_class=absent` · skip, not a heartbeat |
| JSONL | present · 18 rows · schema ok · no URL/token hits · sha256 `23a9ae8a10b7c01427980a248c67100d78f9d9bc819372e757a93b76e6625d2c` |
| hourly.log | `2026-08-18 09:56:49  OK PUSH-FAIL (fallback throttled, 1.4h of 6h; push err: To E:\germline\vault.git) +state` |
| task result `0` | throttled PUSH-FAIL exits 0 in the existing script · **not** writer-healthy |
| GITWRITE-FAILED.flag | still present · mtime `03:50:30` unchanged |

Same `--all`/`--tags`/`github_wire` split and `REF_REJECTED` class also appeared on natural cycles `04:49` `05:49` `06:49` `07:49` `08:49`.

P3 status: **DIAGNOSTICS_VERIFIED**. Option R/M still not chosen.

Machine: `06-EVIDENCE/canonical/receipts/P3-scheduled-cycle-observed-2026-08-18.json`
