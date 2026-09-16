---
type: report
project: "[[04 - Architect System/architect/PROJECT]]"
status: ready
tags: [octopus, p1, commit-audit]
created: 2026-08-29
updated: 2026-08-29
created_by: agent
language: fa
sources:
  - "[[06-EVIDENCE/OCTOPUS-REUSE-AUDIT-2026-08-29/P1-RESULT]]"
  - "[[06-EVIDENCE/OCTOPUS-REUSE-AUDIT-2026-08-29/runtime-provenance-20260828T230743Z/CHECKPOINT]]"
---

# 01 — P1 commit audit

```text
P1_SOURCE_COMMIT=a27eb0536793c7fc040917bb645e9057707298f4
P1_PARENT_SHA=UNKNOWN_INFERRED_6881337
P1_CHANGED_FILE_COUNT=4
P1_CHANGED_FILES=ofn/node.py; ofn/run.py; ofn/adapters/cockpit_v2_read_model.py; tests/test_cockpit_v2_owner_queue.py
P1_FOURTH_FILE_JUSTIFICATION=test_only_behavioral_suite_not_imported_by_ofn.run
P1_DIFF_SHA256=UNKNOWN
P1_TEST_INSTRUMENTATION_TRACKED=YES
P1_TEST_INSTRUMENTATION_RUNTIME_SAFE=YES_IF_TESTS_ONLY
observed_at=2026-08-29T04:50:00Z
method=read_evidence_and_local_patch_copy
scope=this_host_only
truth_status=DOCUMENTED
```

## Why parent and diff hashes are UNKNOWN

`a27eb05` lives on 138 `/home/ari/ofn`. This worktree does not contain that commit. `git show a27eb05` was **not** run (NO_PROCESS / no SSH).

E0 snapshot of the same repo, taken **before** P1, shows HEAD `68813370c726a1a650a7cb2fb99207c300358db9` (`sparse-commit-audit.txt:31`, `CHECKPOINT.md:27`). Loose object `a27eb05` is **absent** from `F:\backup\.git`. Inference that P1's parent is `6881337` is `HYPOTHESIS`: an intervening 138 commit is not ruled out. Patch index lines (`e6564db`, `9f5c75d`, `64d063e`) are **blob** parents of the three production files, not the commit parent.

Local intended diff copy: `runtime-provenance-20260828T230743Z/p1-owner-queue.patch`. That file is a construction artifact, not `git show a27eb05`. Its SHA is not the commit diff SHA.

## Four files

| File | Why needed | Prod or test | Original 3-file allowlist | Runtime behavior | Rollback |
|---|---|---|---|---|---|
| `ofn/node.py` | Add `owner_queue_metadata()` allowlisted derivative of `owner_queue()` | production | YES | YES — new method; unused until callback wired | revert method |
| `ofn/run.py` | Optional callback into existing `CockpitV2ReadModel` seam | production | YES | YES — only if method exists | revert 4 lines |
| `ofn/adapters/cockpit_v2_read_model.py` | Additive `data.owner_items` | production | YES | YES — queue JSON shape + status | revert collect/project |
| `tests/test_cockpit_v2_owner_queue.py` | RED/GREEN for the seam | test | **NO** | NO if `ofn.run` does not import tests | delete file |

### Fourth-file justification

Original verbal allowlist was three production files. The fourth is the 11-test behavioral file named in `P1-RESULT.md:53` and `commit-p1.sh:9`. Guessed-interface test stayed in evidence, not in the commit (`P1-RESULT.md:53`).

`FOURTH_FILE_JUSTIFIED=YES` as **test-only proof**, not as a fourth production module. It does not create an endpoint, table, or queue.

## `owner_items` properties (from local patch copy)

Source: `p1-owner-queue.patch` + `P1-RESULT.md`. Truth: `DOCUMENTED` (patch) / `REPO_VERIFIED` only for the copy on this disk.

| Property | Result | Evidence |
|---|---|---|
| Additive | YES | `data` gains `owner_items`; `items` still `page` from mesh filter (`patch:181-187`) |
| Mutates `items` | NO | `_collect_queue` still feeds `_filter_queue` / `_paginate` |
| Changes mesh ordering | NO | mesh still `_queue_sort_key`; owner rows use a **separate** sort |
| Changes pagination/count | NO for `items`/`total`/`next_cursor` — those remain mesh-only. Owner list is **not** paginated with mesh | `patch:176-187` |
| Changes cache key | `UNKNOWN` — no cache-key symbol in the patch |
| Mixes tenant/node identity | NO if consumers honor `source_kind=business_outbox` and `id=business:<tenant:idem>` | `patch:114-117` |
| Fail-closed when callback absent | YES — `_callback(..., expected=True)` → `None` → `owner_items=null`, `owner_available=False` | `patch:128-132`, `P1-RESULT.md:96` |
| Observable | YES — endpoint becomes `degraded` if owner side unavailable | `patch:189-196` |

### Status-semantic change (not an items mutation)

Before: `unavailable` if mesh `not available`. After: `unavailable` only if **both** mesh and owner unavailable; mesh-ok + owner-missing → `degraded`.

That is an additive field plus a **status** change. Mesh `items` bytes can stay equal while `status` and top-level keys change.

## Instrumentation

`P1-RESULT.md:106`: test instrumentation left in until owner canary after restart.

The RED copy `test_cockpit_v2_owner_queue.red.py:23-55` appends JSON to `OCTOPUS_DEBUG_LOG` if set and POSTs to `OCTOPUS_DEBUG_ENDPOINT` if set (`urllib`, 2s, errors swallowed). `p1-owner-queue.patch` has **zero** debug regions in the three production files.

```text
P1_TEST_INSTRUMENTATION_TRACKED=YES
P1_TEST_INSTRUMENTATION_RUNTIME_SAFE=YES_IF_TESTS_ONLY
```

No `ofn.run` import of the test module was found in vault `ofn/run.py`. `owner_queue_metadata` has **zero** matches under vault `03 - Projects/OFN-Board` — P1 did not land in this tree.

## Runtime boundary

`CHECKPOINT.md`: PID `1351408` started 2026-08-27 11:33 AEST, HEAD then `6881337`. P1 commit is later. Restart was not performed (`P1-RESULT.md:103-105`).

```text
P1_RUNTIME_LOADED=NO
```
