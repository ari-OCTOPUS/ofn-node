# README FIRST — v2 delta on top of OCTOPUS-NEXT-AGENT-HANDOFF-2026-08-21

**This is NOT a full replacement of the sibling folder
`../OCTOPUS-NEXT-AGENT-HANDOFF-2026-08-21/`.** That package (generated 2026-08-21T22:19:58+10,
HEAD `360d4361b144fbeb17b43bc1e8e564ff9860fbcd`) is thorough, already reused this session's G0
outputs, and does not need to be redone. Read it first, in the order its own README-FIRST.md
gives, before reading anything here.

This `-v2` folder exists only because the live tree kept moving — fast — in the window between
that package's generation and this one being asked for again. Rather than duplicate ~145KB of
still-accurate material, this folder documents **only the delta**: what changed, and one
significant new discovery. That's why it has 4 files, not 15 — the instruction that asked for a
`-v2` suffix on collision was explicit that additive, non-duplicating documentation is what
matters, not hitting a fixed file count.

Read order for this folder:
1. `CURRENT-TRUTH.json` — refreshed snapshot fields (branch/HEAD/dirty counts as of this pass)
2. `DELTA-SINCE-360d436.md` — everything that changed, commit by commit, plus the nervous_recovery discovery
3. `HANDOFF-MANIFEST.sha256` — hashes of this folder's own files, and of the two untracked reproducibility-defect files at this exact moment

**The single most important thing to know before doing anything else:** in the roughly 70
minutes this delta covers, the live tree gained two full new files (`wave1_closeout.py`,
`wave1_verifier.py` under `_ops/nervous_recovery/`) *between two consecutive read-only checks
in this same pass* — i.e. mid-session, while this delta was being written. This branch is being
actively developed by at least one other concurrent process right now. Do not trust any
snapshot, including this one, without re-running `git status`/`git log -3` as your very first
action.

No Telegram token was available to this pass either. No live send, webhook, restart, paid call,
or code change was made. `poll_lease.py` and `transport_subprocess.py` remain untouched and
still untracked — same reproducibility defect the original package already flagged.
