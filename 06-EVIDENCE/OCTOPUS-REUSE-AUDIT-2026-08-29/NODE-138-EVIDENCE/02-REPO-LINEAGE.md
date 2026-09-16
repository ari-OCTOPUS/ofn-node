---
type: report
project: "[[04 - Architect System/architect/PROJECT]]"
status: ready
tags: [octopus, node-138, git, lineage]
created: 2026-08-29
updated: 2026-08-29
created_by: agent
language: en
sources:
  - "[[06-EVIDENCE/OCTOPUS-REUSE-AUDIT-2026-08-29/REUSE-MAP]]"
  - "[[06-EVIDENCE/OCTOPUS-REUSE-AUDIT-2026-08-29/P1-RESULT]]"
---

# 02 — Repo lineage

```text
observed_at=2026-08-29T05:31:45Z
method=GIT_OPTIONAL_LOCKS=0_git_read_only
scope=this_host_only
```

No fetch, pull, push, checkout, or commit.

## Trees

### A. Runtime worktree 138 (canonical OFN body)

| Field | Value | Truth |
|---|---|---|
| path | `/home/ari/ofn` | `LIVE_VERIFIED` |
| branch | `integration/138-business-spine-20260828` | `LIVE_VERIFIED` |
| HEAD | `a27eb0536793c7fc040917bb645e9057707298f4` | `LIVE_VERIFIED` |
| upstream | none | `LIVE_VERIFIED` |
| tracked dirty | empty | `LIVE_VERIFIED` |
| untracked | `?? 06-EVIDENCE/` only (prior probe artifacts) | `LIVE_VERIFIED` |
| remotes | `origin` `https://github.com/ari322/ofn-node.git`; `germline` `/mnt/octopus-germline/octopus.git` | `LIVE_VERIFIED` (URL sanitized: no creds) |
| sparse-checkout | unset; worktree not sparse | `LIVE_VERIFIED` |
| relation to runtime | CWD of PID 1351408; **disk HEAD ≠ process start tree** | `LIVE_VERIFIED` |
| class | **LIVE** source; **UNPROVEN** loaded bytes | `LIVE_VERIFIED` |

Last 20 commits on 138 (abbrev):

`a27eb05` 2026-08-29 P1 owner_items → `6881337` spine → `56e9369` discovery → `f09681a` audit → `d3fb20c` rapid-reconcile → `6070f51` polling harness → … → `388594e` is an ancestor (`origin/main`).

source: `git log -20` / `git merge-base --is-ancestor` · method: SSH · observed_at: 2026-08-29T05:31:45Z

### B. Extra worktree on 138

| Field | Value | Truth |
|---|---|---|
| path | `/tmp/ofn-clean-Tw5CvA` | `LIVE_VERIFIED` |
| HEAD | `ae3ced7cd410c463e4df028597b0d69397e5efac` detached | `LIVE_VERIFIED` |
| relation | not `ofn.service` CWD | `LIVE_VERIFIED` |
| class | **UNKNOWN** / leftover clean tree | `LIVE_VERIFIED` path; purpose `UNKNOWN` |

### C. Vault `F:\backup`

| Field | Value | Truth |
|---|---|---|
| path | `F:\backup` | `LIVE_VERIFIED` |
| branch | `rescue/octopus-live-tree-20260821` | `LIVE_VERIFIED` |
| HEAD now | `7d65f2d2e66424c64b85795c7e1de24c838d892b` | `LIVE_VERIFIED` |
| REUSE-MAP `VAULT_HEAD` | `c803dee` | **STALE as tip**; commit still present |
| OFN-Board copy | `03 - Projects/OFN-Board` inside vault tree | `REPO_VERIFIED` |
| `owner_queue_metadata` | **absent** in vault OFN-Board | `REPO_VERIFIED` |
| class | **ARCHIVE/MIRROR of organism+docs**, not 138 runtime | `REPO_VERIFIED` |

### D. Other paths

| Path | Result | Truth |
|---|---|---|
| `/opt/ofn` | does not exist | `LIVE_VERIFIED` |
| `/home/dietpi/ofn` | not visible (home 700) | `LIVE_VERIFIED` |
| GitHub `ari322/ofn-node` `main` | `388594e` on 138 as `origin/main` | `LIVE_VERIFIED` |
| vault census mirror | cited in L191; not re-hashed this session | `DOCUMENTED` |

## SHA search

| SHA | Vault `F:\backup` | 138 `/home/ari/ofn` | Ancestor of 138 HEAD? | Notes | Truth |
|---|---|---|---|---|---|
| `388594e` | YES `388594e048cc…` 2026-08-04 ziman shell | YES `origin/main` | YES | ofn-node main tip in REUSE-MAP | `LIVE_VERIFIED` |
| `32a81d0` | YES board-snapshot-20260816 | YES same family | not checked ancestor | snapshot branch | `LIVE_VERIFIED` present |
| `631913de` | YES `archive/ucp-unconnected` **event_store + command_bus** 2026-08-29 | **ABSENT** | NO | do not port to 138 | `LIVE_VERIFIED` |
| `6070f51` | YES cockpit-v2 polling | YES `ofn/cockpit-v2-20260827` | YES | | `LIVE_VERIFIED` |
| `6881337` | YES tag `spine-138-fetch` | YES parent of P1 | YES | E0 HEAD | `LIVE_VERIFIED` |
| `f09681a` | YES audit-138 | YES | YES | | `LIVE_VERIFIED` |
| `56e9369` | YES discovery-138 | YES | YES | WHAT-IS-DEAD | `LIVE_VERIFIED` |
| `c803dee` | YES 2026-08-23 DoS receipt | **ABSENT** | NO | germline/vault family, unrelated merge-base historically | `LIVE_VERIFIED` |
| `a27eb0536793c7fc040917bb645e9057707298f4` | **ABSENT** | YES **HEAD** | YES | P1; parent **`6881337`** | `LIVE_VERIFIED` |

```text
P1_PARENT=68813370c726a1a650a7cb2fb99207c300358db9
P1_PARENT_WAS=HYPOTHESIS_NOW_LIVE_VERIFIED
P1_FILES=ofn/node.py;ofn/run.py;ofn/adapters/cockpit_v2_read_model.py;tests/test_cockpit_v2_owner_queue.py
```

`merge-base(c803dee, 6881337)` remains empty per REUSE-MAP (`DOCUMENTED`). Confirmed this session: `c803dee` is not an object in `/home/ari/ofn`.
