---
merge_domain: live-state
merge_key: dc03a:board138:lineage:63938eb0
lane: OCTOPUS-LIVE-STATE-20260917
mission: DC-03A-BOARD138-LIVE-LINEAGE
owner_decision: DC-03=الف
mode: STRICT_READ_ONLY
mutations_performed: 0
secrets_read: 0
services_touched: 0
board: 138
captured_at_local: 2026-09-17T11:45+10:00
captured_at_utc: 2026-09-17T01:45Z
---

# DC-03A — board 138 runtime lineage (read-only capture)

Raw transcript: `RAW-DC03A-BOARD138-LINEAGE.log` (113 KB, complete, unedited).

## Result block

```
BOARD=138
REPO_ROOT=/home/ari/ofn
REMOTE_URLS=germline /mnt/octopus-germline/octopus.git (fetch,push) ; origin https://github.com/ari-OCTOPUS/ofn-node.git (fetch,push)
CURRENT_BRANCH=main
HEAD_SHA=63938eb01141030f6c9c56f8e1c51ec76e46458c
HEAD_SUBJECT=hold_external opened per owner vote 2026-09-07 (UNLOCK-REGISTRY L23, laptop structured round-1): default False in brain_wake/brain_schema/release_pipeline + tests updated; external effects now under GOV-V7 ALLOW_WITH_RECEIPT + L2 OWNER-CANCEL; spec locks flipped same day (receipt GO-EXT2-HOLD-EXTERNAL-OPEN-20260907); 33/33 tests green
WORKTREE_STATUS=DIRTY
MAIN_IS_ANCESTOR=UNKNOWN
HEAD_IS_ANCESTOR_OF_MAIN=UNKNOWN
RUNTIME_63938EB_PRESENT=YES
CANONICAL_DBA9971_PRESENT_LOCALLY=NO
WINDOWS_0DA921B_PRESENT_LOCALLY=NO
HALT_FILES_FOUND=NONE
HALT_ALL_FILES_FOUND=NONE
HALT_CONSUMERS_FOUND=215 files / 472 lines (HALT family regex); operative oracle callers = 4 production files / 6 call sites
HALT_ALL_CONSUMERS_FOUND=2 files / 3 lines
MUTATIONS_PERFORMED=0
SECRETS_READ=0
SERVICES_TOUCHED=0
VERDICT=UNRESOLVED
BLOCKERS=dba9971a absent locally (ancestry undecidable without a forbidden fetch); 0da921b1 absent locally; worktree DIRTY (5 tracked modified); local origin/main ref is stale (1b53773a != canonical dba9971a)
NEXT_SAFE_ACTION=owner-authorized READ-ONLY remote query, e.g. `git ls-remote origin` (contacts remote, writes no refs) or an authorized fetch, to obtain dba9971a and 0da921b1 so ancestry becomes decidable
```

## Why `UNKNOWN` and not `NO` — the important distinction

Both ancestry probes exited **128**, and git emitted `fatal: Not a valid commit name
dba9971a802653b4f56a1194da49e49551e04c54` (the message appeared late in the stream because
unbuffered stderr surfaced after the following `printf` header).

Exit 128 is a **git error**, not the boolean answer. `git merge-base --is-ancestor` returns
**1** for a genuine "no", and **128** when the object does not exist locally. Since
`git cat-file -t dba9971a…` answers `fatal: could not get object info`, the canonical commit is
simply **not in this clone**, so the ancestry question cannot be answered here at all.

Reporting `NO` would have been a fabricated answer. The correct value is `UNKNOWN`.

## Local refs (no fetch performed — these are this clone's last-known state)

| ref | sha | note |
|---|---|---|
| `refs/heads/main` (HEAD) | `63938eb0` | the runtime |
| `refs/remotes/origin/main` | `1b53773a` | **stale** local tracking ref; equals the merge-base with HEAD |
| `refs/remotes/germline/master` | `3f062e23` | second remote (local bare mirror on `/mnt`) |
| canonical target | `dba9971a…` | **ABSENT** |
| Windows-clone target | `0da921b1…` | **ABSENT** |

`git merge-base HEAD origin/main` returns `1b53773a` — i.e. the local tracking ref is a strict
ancestor of HEAD, which is what produces `## main...origin/main [ahead 8]`. That count is
**relative to a stale ref**, not to the GitHub canonical tip, so it must not be read as
"8 commits ahead of main".

## Worktree is DIRTY — 5 modified tracked files

```
 M data/gates.json                     |   22 +-
 M ofn/adapters/self_model_producer.py | 1139 ++++++++++++++--------------
 M ofn/agents/glass_runner.py          |  160 ++++-
 M ofn/agents/imap_listener.py         |   20 +
 M tools/leads_master.json             |  432 ++++++++++++-
 5 files changed, 1222 insertions(+), 551 deletions(-)
```
plus many untracked runtime artifacts (`?? 09-LANES/ECONOMIC-LEARNING/runs/auto-*`,
`?? data/state/`, `?? eti/`, `?? notes/of-drafts-20260916/`, a `.bak-20260911T102433Z` file, …).

Note the overlap with the earlier live-state finding: `tools/leads_master.json` is modified in
the worktree **and** is the exact path that the revenue-drive service cannot write under its
sandbox (`ProtectHome=read-only`). The file has diverged from its committed blob.

## HALT inventory — the single oracle, and the `HALT` vs `HALT-ALL` divergence

**No file named `HALT` and no file named `HALT-ALL` exists anywhere under the repo (maxdepth 4).**
Confirmed independently at runtime: `HALT_FLAG.exists() == False`.

The entire halt authority is one function, `ofn/budget/opslib.py:28`:

```python
HALT_FLAG = OFN_ROOT / "HALT-ALL"          # line 20
OFN_ROOT  = HOME / "ofn"                   # line 18  -> /home/ari/ofn

def master_halted() -> str | None:
    """None=اجازه؛ متنِ دلیل=توقف. fail-closed."""
    try:
        if _os.environ.get("HALT_SURVIVAL_LOOP") == "1":
            return "HALT_SURVIVAL_LOOP=1"
        if HALT_FLAG.exists():
            return f"halt-flag:{HALT_FLAG}"
        return None
    except Exception as e:
        return f"halt-check-error:{type(e).__name__}"
```

There are exactly **two** halt triggers: env `HALT_SURVIVAL_LOOP=1`, or the file
`/home/ari/ofn/HALT-ALL`. **A file named plain `HALT` is never consulted by this oracle** — it
would be inert. This confirms, from source, the `HALT` vs `HALT-ALL` divergence that the
parallel recovery lane flagged.

Live read (read-only import, no writes): `master_halted() = None` → **runtime is NOT halted**.
The env var is absent from the process environment and appears in none of
`octopus-revenue-drive.service`, `/etc/systemd/system/octopus-wire.env`,
`/home/ari/.config/ofn/secrets.env` (name-only grep, values never printed).

`HALT-ALL` reference sites — 2 files, 3 lines, complete:
- `ofn/budget/opslib.py:6` (docstring, Persian)
- `ofn/budget/opslib.py:20` (`HALT_FLAG = OFN_ROOT / "HALT-ALL"`) ← **the oracle**
- `ofn/agents/outbound_worker.py:213` (comment: fail-closed, zero sends under halt)

`master_halted()` call sites — 6 files, 9 lines: production callers are
`ofn/agents/capability_token.py:87`, `ofn/agents/outbound_worker.py:214` and `:451`,
`ofn/agents/quote_pipeline.py:79`, `ofn/agents/release_pipeline.py:106` and `:184`; plus the
definition at `ofn/budget/opslib.py:28` and one mock in `tests/test_capability_token.py:219`.

The 215-file / 472-line count is the broad `HALT` family regex and is dominated by
documentation and receipts (`docs/octopus-os/07-INCIDENTS.md` alone has 47 lines) plus
similarly-named modules (`ofn/kernel/halt_latch.py`, `ofn/adapters/halt_log.py`,
`ofn/adapters/halt_flag.py`, `ofn/kernel/halt.py`). Only the sites listed above gate the runtime.

## Compliance

`git pull/fetch/push/rebase/merge/reset/checkout` — none executed. No file created, touched,
modified or deleted on 138. No HALT/HALT-ALL created. No service started, stopped, restarted,
enabled, disabled or killed. No token, secret, wiring, env, systemd, firewall or runtime change.
No secret value read or printed. "Healthy" was not inferred from ping or SSH anywhere in this
report — the halt verdict comes from executing the actual oracle.

The one deviation from the literal command set, stated plainly: the original `git grep` was
piped through `head -n 300`, which truncated the HALT consumer list, so the grep was re-run with
`-l`/`-h` counting to obtain true totals. Read-only, local, no mutation.

`MUTATIONS_PERFORMED=0 · SECRETS_READ=0 · SERVICES_TOUCHED=0`
