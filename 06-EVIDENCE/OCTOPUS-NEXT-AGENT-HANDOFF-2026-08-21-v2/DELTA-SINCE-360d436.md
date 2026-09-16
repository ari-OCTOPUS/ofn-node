# Delta since the original handoff package (HEAD 360d436, 2026-08-21T22:19:58+10)

## 1. Git topology (re-verified this pass — CONFIRMED_FROM_GIT)

- `equip/g10-cognition-20260816` is unchanged, still frozen at `53e527aef95c9bb30a3822e3ac278df59590e1d4`.
- `rescue/octopus-live-tree-20260821` is a **clean fast-forward descendant** of that commit
  (`git merge-base --is-ancestor equip/g10-cognition-20260816 HEAD` → true). No divergence, no
  rebase, no force-push. This resolves an open ambiguity from the prior G0 pass: there is no
  competing rewrite, just linear forward progress on a new branch name.
- Four commits exist between `53e527a` and the current tip, none of which touch
  `_ops/telegram_center` by path (verified with `git log 53e527a..HEAD -- _ops/telegram_center`
  returning empty) — the telegram_center changes visible in `git status` right now are all
  **uncommitted working-tree edits**, not part of these four commits:

| commit | time (local) | subject |
|---|---|---|
| `360d436` | 22:15:42 | chore(rescue): preserve dirty source before consolidation |
| `aa7a795` | 22:21:13 | docs(handoff): preserve observed Octopus state before integration — **this is the original handoff package's own commit** |
| `4ce67d2` | 23:27:24 | fix(repro): track registered organ cartographer slice |
| `c7ec5f5` | 23:27:38 | fix(repro): track registered Wave 1 readonly preflight |

Current HEAD as of this delta: `c7ec5f527243aa50b80bbdc5c790cebe4cb08854`.

## 2. The two "fix(repro)" commits — what they actually did

Contrary to what their subject lines might suggest, neither commit touched
`poll_lease.py` or `transport_subprocess.py`. `c7ec5f5` added two new files outright:
`_ops/nervous_recovery/wave1_readonly.py` (388 lines) and `_ops/tests/test_wave1_preflight.py`
(143 lines). `4ce67d2` added a sibling "organ cartographer" slice (not inspected in this pass —
flagged as UNKNOWN, worth a follow-up read). "fix(repro)" here appears to mean "make this new
module's own tests reproducible," not "fix the pre-existing poll_lease.py reproducibility gap."
**The reproducibility defect the original package and this session's G0 pass both flagged is
still unresolved as of this delta** — confirmed by direct `git status` check, see §4.

## 3. New subsystem discovered: `_ops/nervous_recovery/`

Not present in any prior scan this session (the 91-file telegram/miniapp deep-scan, the G0
capability-matrix, or the original handoff package's CAPABILITY-AND-LOOP-MAP.json all predate
it). Read `wave1_readonly.py`'s module docstring and top-level constants directly
(CONFIRMED_FROM_CURRENT_FILE): it implements a capped, read-only memory-access path
(`CAPABILITY = "memory.read"`, `MAX_READS_PER_CYCLE = 3`, `MAX_HITS = 8`, `TIMEOUT_MS = 250`)
gated by a lock file (`state/wave1/lock.json`) that is explicitly documented as
"Closed by default. Only wave1_closeout may open after verifier PASS" — and a `STOP-WAVE1-READ`
kill-switch file path.

It has real callers and real tests, not orphaned code (CONFIRMED_FROM_GIT / grep, this pass):
`_ops/cortex/model_router.py`, `_ops/nervous_recovery/wave0_verifier.py`,
`_ops/tests/run_all.py`, `_ops/tests/test_nervous_recovery.py`,
`_ops/tests/test_wave0_append_only_gate.py`.

**Live, mid-pass discovery (INFERENCE, not yet independently confirmed):** between the two
`git status` checks this delta pass ran a few minutes apart, two more files appeared under the
same directory, still untracked: `_ops/nervous_recovery/wave1_closeout.py` and
`_ops/nervous_recovery/wave1_verifier.py`. The names — `wave0_verifier.py` already existing,
`wave1_verifier.py` and `wave1_closeout.py` now appearing — are suggestive of exactly the kind
of independent-verifier / gate-closeout machinery every prior plan document in this vault
(`OWNER-ORDER-WAVE1-2026-08-21.md`, `TELEGRAM-COGNITION-DEEP-DEBUG-2026-08-21.md`, the original
handoff package) has been waiting on. **This pass did not read their contents and makes no claim
about what they actually do or whether they constitute real SIG-IV infrastructure.** Flagging
this by name and location only, as REPORTED_NOT_REPRODUCED / next-agent-should-read-this,
specifically so it isn't missed in the noise of 35,000+ untracked files.

## 4. Reproducibility-defect files — hashed this pass (CONFIRMED_FROM_CURRENT_FILE)

| path | size (bytes) | sha256 | git status |
|---|---|---|---|
| `_ops/telegram_center/poll_lease.py` | 21968 | `6a7716990ec9720c5556be2a755864e9e0e09acd8ae4c48db1e7d54c201249a8` | still untracked (`??`) |
| `_ops/telegram_center/transport_subprocess.py` | 783 | `a9438ccfe0e464e4d04c3c3cac56aacb229831f8d0226ab3a53c933933ca377b` | still untracked (`??`) |
| `_ops/nervous_recovery/wave1_readonly.py` | 14047 | `f48b67a04dcb41a2b090fc474c07d42fe84dd287325bba2e1777f1120e1a7142` | tracked as of `c7ec5f5` |
| `_ops/tests/test_wave1_preflight.py` | 5246 | `5114a62c2d48dd6acc8c7a2b9d552702075de0acac2a1baaf306e4f6c893341c` | tracked as of `c7ec5f5` |

`poll_lease.py` grew from an earlier size seen at the very start of this session (~6.8KB) to
21968 bytes now — it has been actively edited across this entire multi-hour window, by a process
this session never observed directly. Treat its current content as a moving target, not a stable
artifact to reason about line-by-line.

## 5. What did NOT change and does not need re-verification

The original package's `CONFLICTS-AND-UNRESOLVED.md`, `CAPABILITY-AND-LOOP-MAP.json`,
`MEMORY-LEARNING-LAB-DOCTOR-STATE.json`, `TELEGRAM-MINIAPP-STATE.json`, and
`OBSIDIAN-AUTHORITY-MAP.json` were not found to be materially outdated by anything this delta
pass observed — the telegram/miniapp architecture facts, the lab 16/8/0 card count, the SIG-IV
gate status, and the owner-order constraints are all still accurate as far as this pass could
tell. This delta does not re-derive them.

## 6. Recommendation for the next agent

Do not treat either handoff folder (this one or the original) as current without re-running
`git log -3` and `git status --porcelain | wc -l` first — the four-file delta above happened in
roughly 70 minutes of wall-clock time, and two more files appeared *during the writing of this
very delta*. If `_ops/nervous_recovery/wave1_verifier.py` and `wave1_closeout.py` are still
present and now tracked, read them before anything else in this package — they may already
answer the SIG-IV question every other document in this vault is still waiting on.
