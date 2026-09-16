---
type: plan
status: read-complete
tags: [telegram, g0, reconciliation, loop-closure, 2026-08-21]
created: 2026-08-21
updated: 2026-08-21
authority: G0 owner approval (chat, this session, 2026-08-21) — read-only reconciliation, not an implementation order
as_of_head: 53e527aef95c9bb30a3822e3ac278df59590e1d4
implementation_authorized_by_this_document: false
live_send_authorized: false
webhook_authorized: false
paid_calls_authorized: false
restart_authorized: false
supersedes: none
does_not_supersede:
  - "_ops/cortex/plans/TELEGRAM-DEEP-DEBUG-IMPLEMENTATION-2026-08-21.md"
  - "_ops/cortex/plans/TELEGRAM-COGNITION-DEEP-DEBUG-2026-08-21.md"
  - "_ops/cortex/plans/OCTOPUS-MILESTONE-CORRECTION-2026-08-21.md"
---

# OCTOPUS-LOOP-CLOSURE-TELEGRAM — G0 Reconciliation — 2026-08-21

## 0. What this document is and is not

This is **not** a fourth independent plan for the Telegram loop-closure problem. It is a
read-only reconciliation, requested by the owner in chat, sitting on top of three plan
documents already in `_ops/cortex/plans/` plus the live `_ops/state/debug/*.json` maps —
checking what has actually landed on current HEAD against what an external multi-model
analysis (pasted into this session) proposed to build, and against what the vault's own
`loop-closure-matrix.json` says is still open. It authorizes **no code, no commit, no
restart, no webhook, no live send, no paid call.** The only writes made during this pass
are this file and two new evidence JSON files (`_ops/state/debug/tree-divergence.json`,
`_ops/state/debug/capability-matrix.json`), both additive, neither touching a WORKLOCK'd
file (`center.py`, `run_all.py`, `wiring.py` remain untouched).

Full source data: [[../state/debug/tree-divergence.json|tree-divergence.json]] ·
[[../state/debug/capability-matrix.json|capability-matrix.json]].

## 1. Headline finding

**Most of what the pasted external plan (`OCTOPUS-MILESTONE-CORRECTION-2026-08-21.md`)
proposes to build already exists on current HEAD**, built by two earlier same-day plan
documents (`TELEGRAM-DEEP-DEBUG-IMPLEMENTATION-2026-08-21.md`'s Waves A–F and
`TELEGRAM-COGNITION-DEEP-DEBUG-2026-08-21.md`'s W0b/W8/W1b/W9), landing in commits
`fc3ef66`..`c713d26`..`bac5097` between 16:45 and 19:38 local on 2026-08-21. The external
plan's own audit was scoped to commit `d301339` — a point roughly 13 commits behind
current HEAD on this exact path — and it explicitly and correctly refused to project later
bytes backward onto that frozen evidence. That discipline is sound; the practical
consequence is that its "target architecture" (§7) and "sequential implementation plan"
(§10, Waves W1–W7) largely describe work that is already done, in progress, or
deliberately still gated, not a green-field build. Detail: `tree-divergence.json →
plan_lineage_divergence`.

This does **not** mean the external plan was wrong about anything it measured. Where it
made a claim about d301339's actual bytes, it appears accurate. It means: before anyone
acts on that plan's Wave sequence, they should re-read it against current HEAD, not
against d301339.

## 2. What's already built, tested, and live (selected — full list in capability-matrix.json)

| capability | state | evidence |
|---|---|---|
| Typed per-bot circuit breaker + bounded transport | LIVE_UNVERIFIED (thread path proven; subprocess path default-off + untracked) | `transport_pool.py`, commit `036ef32`, 7/7 + 16-scenario battery |
| Immutable config snapshot + last-known-good | OPERATIONAL_VERIFIED | `config_manager.py`, commit `b78d1b6`, 8/8 |
| Health truth (last-completed-poll, not last-update, is the signal) | OPERATIONAL_VERIFIED (function); consumer gap open | `health_metrics.watchdog_truth()`, commit `fc3ef66` |
| One-poller-per-token SQLite TTL lease | LIVE_UNVERIFIED — untracked in git | `poll_lease.py` — see reproducibility defect §3 |
| 163-registered / 39-wave / 202-total green suite | reconciled | note 79 + commit `6249741` + note 80 §4 (see `tree-divergence.json → test_count_reconciliation`) |
| Controlled live restart with byte-exact offset preservation | OPERATIONAL_VERIFIED, one real trial | note 80 §5, PID 27884→2080, offset `223883352` preserved |
| Typed memory context / decide_from_context | LIVE_UNVERIFIED — fixture-closed, live-open | `cycle_context.py`, commit `bac5097`, 3/3 fixture |

## 3. The one finding that should gate everything else: reproducibility

`tg_api.py` (tracked, part of HEAD) imports `poll_lease` (untracked, working-tree-only).
`test_poller_lease_20260821.py` (tracked) imports it too. **A clean checkout of current
HEAD does not run.** This was found independently twice — once by this scan reading live
files directly, once by the external `OCTOPUS-MILESTONE-CORRECTION-2026-08-21.md` reading
git blobs — via two unrelated methods, which is why it's reported here with high
confidence rather than as a maybe.

Practical consequence: **any independent verifier (SIG-IV) that tries to reproduce from a
clean checkout of `53e527a` today will fail before it even gets to test the interesting
questions**, not because the lease logic is wrong, but because the file implementing it
was never committed. The same applies to `transport_subprocess.py`. Whoever runs SIG-IV
next needs `git add` + commit of exactly these two files (and nothing else from the ~7
other dirty paths currently sitting in the working tree) before reproduction is even
possible. This document does not do that commit — it only names the blocker.

## 4. What's genuinely still open (from `loop-closure-matrix.json`, cross-checked)

Ranked by how directly each blocks the owner's original ask ("ببین توی تلگرام واقعاً اعمال
شدن"):

1. **Reproducibility of `poll_lease.py`/`transport_subprocess.py`** (§3 above) — blocks
   SIG-IV from even starting cleanly.
2. **Independent verification (SIG-IV) itself** — every one of the three prior plan
   documents agrees this is the actual next gate; none of them, including this one, can
   self-declare it. `OWNER-ORDER-WAVE1-2026-08-21.md`'s own current-blocker line still
   reads `verifier_independent=false`.
3. **T5 supervision taxonomy is built but not consumed** — `health_metrics.watchdog_truth()`
   exists and is tested, but `tg-center-watchdog.ps1` still decides "hung" from pulse-file
   age alone and never calls it. The taxonomy that would tell the watchdog "this is an
   empty long-poll, not a hang" is sitting unused one file away from the component that
   needs it most.
4. **Memory-read → decision consume, live** — `memory_read_loop.py` produces real
   telemetry every beat; `cycle_context.py`'s typed consume path is fixture-proven
   (3/3) but `loop-closure-matrix.json` still marks the live organism's `consume_tick`
   as "explore-only without outcomes." This is the live-code counterpart of what one of
   the three external model analyses flagged as the single most important missing loop
   (credit assignment / L3 learning) — independently corroborated here by the vault's own
   debug state, not just by that external analysis.
5. **60-minute polling-only soak** — required by every version of this plan's acceptance
   criteria; not run anywhere yet.
6. **Mini App live re-measure** — initData TTL constant (300s claimed vs. a different
   value once seen in code per note 77) was not re-extracted in this pass either; still
   open from the prior architecture scan (note 81).
7. **`tg.rate_queue` / `tg.sender_bridge` remain unattached to the live Center** — by
   design, owner-gated. Not a gap to close silently; a decision the owner has not yet
   made to make.

## 5. Explicit non-findings

This pass did not re-verify: the exact numeric TTL/skew constants in `miniapp_gateway.py`,
whether `tg-center-watchdog.ps1` has restarted Center since the 09:12:58Z boot recorded in
`TELEGRAM-COGNITION-DEEP-DEBUG-2026-08-21.md`, or the provenance of `OCTOPUS/admin-telegram/`.
All three are carried forward as open items rather than guessed at.

## 6. Recommendation

Do not open a new implementation wave. The owner's own executive order
(`OWNER-ORDER-WAVE1-2026-08-21.md`) already fixes the sequence: **مگاپرامپت ۱ (independent
verification) → PASS → مگاپرامپت ۲ (single-message canary) → ۳ (loop closure) → ۴
(post-canary expansion)**. Nothing found in this reconciliation changes that order or
skips ahead of it. The one actionable addition this pass contributes: whoever runs
مگاپرامپت ۱ next should be told, before they start, that the working tree currently has a
reproducibility gap (§3) that will fail a clean-checkout reproduction attempt for reasons
unrelated to the lease logic itself — so that failure isn't mistaken for a real defect in
`poll_lease.py`.

## 7. Terminal state

```
G0_READ_COMPLETE
CAPABILITY_MATRIX_WRITTEN
TREE_DIVERGENCE_WRITTEN
IMPLEMENTATION_NOT_STARTED
NO_COMMIT_MADE
NEXT_GATE = SIG-IV (independent verifier, per OWNER-ORDER-WAVE1-2026-08-21.md — unchanged by this document)
```

This note, `tree-divergence.json`, and `capability-matrix.json` are the only files created
by this G0 pass.
