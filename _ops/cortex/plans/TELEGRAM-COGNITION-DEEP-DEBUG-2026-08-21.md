---
type: architecture-debug-plan
scope: telegram-cognition-full-loop
owner: Ari
date: 2026-08-21
baseline_head: c713d26c9460e184347c82d13b0f96cb809975dd
branch: equip/g10-cognition-20260816
execution_authorized: true
live_send_authorized: false
webhook_authorized: false
paid_calls_authorized: false
wave1_unlocked: false
independent_verification_pending: true
---

# TELEGRAM-COGNITION-DEEP-DEBUG — 2026-08-21

Builder session. Terminal status target: `IMPLEMENTATION_COMPLETE_VERIFICATION_PENDING`.
Does not overwrite `_ops/cortex/plans/TELEGRAM-DEEP-DEBUG-IMPLEMENTATION-2026-08-21.md`.

## 1. Owner constraints

- Execute local/fixture/shadow repairs. No live Telegram send, webhook, paid model call, Wave 1 flip, force-push, history rewrite, or secret display.
- Preserve all uncommitted owner/live-tree work (organism observe-only watchdog hook; improve calibration consume). Never `git add -A`.
- `center.py` remains WORKLOCK: no drive-by edits; dispatch timestamp hooked from `durable_loop.commit_result`.
- `run_all.py` WORKLOCK: new tests are created and **named for registration**, not appended by this builder.
- Builder ≠ independent verifier. No `SECURITY_SHADOW_PASS` / `TELEGRAM_LOOP_BASELINE` / `LIVE_READY` self-declaration.

## 2. Git reality

| field | value |
|---|---|
| repository root | `F:/backup` |
| branch | `equip/g10-cognition-20260816` |
| HEAD (full) | `c713d26c9460e184347c82d13b0f96cb809975dd` |
| upstream | **none** configured |
| remotes (names only) | `germline` |
| working tree | dirty: live organism state + prior uncommitted slices (improve calibration, organism orphan observe). Do not revert. |
| staged | empty at session start |
| local-only | entire branch vs `germline/equip/g10-cognition-20260816` (no `@{u}`) |

Resolved short SHAs (all CONFIRMED locally):

| short | full | subject |
|---|---|---|
| 9bc506f | `9bc506ffb34763731aedd4653fc26019963a303e` | WAVE0_PASS; wave1 locked |
| 8fd8eae | `8fd8eaefb2f8deed674a53f6156618a9be1833af` | C1–C4 failing baseline |
| 2325ffce | `2325ffce7b8408cb0c007c6089a4b7fe1f717b5a` | C1–C4 fixture patches |
| eb86de7 | `eb86de7d0b0717eaa50ae59b8d6e747e1365ead1` | C1–C4 evidence; verifier_independent=false |
| fa38d16 | `fa38d16cca944a80396ae1e1a16c547ab3122f78` | loop wiring; 163/163 builder |
| d301339 | `d3013390d52aab2e61bd2578613aff7077f68742` | evidence at fa38d16 |
| bcbc3dd | `bcbc3dd270f758b53eb11b7608ca6080a7da7fc7` | config read hang |
| a8f2e1a | `a8f2e1ad4555e625acce2f1a08f36822be454637` | DNS getaddrinfo hang |
| 396b1d0 | `396b1d064d78df5034ca757960f5f3dd620a8346` | stall-class evidence |
| f314cb0 | `f314cb0ed600e47a00c280fcb0de015668e33ecb` | bounded_io |
| c50327c | `c50327c67120cdb31c01423486bc02ff991a0691` | OWNER_SIGNATURE_BUNDLE_V1 |
| cc267048 | `cc267048075b0f64bd56c8ac59074d8a43233ae2` | organs package on repair branch |
| c713d26 | `c713d26c9460e184347c82d13b0f96cb809975dd` | W7 telegram deep-debug evidence (this HEAD) |

Prior-session plan claimed HEAD `c50327c` — **STALE**. Current HEAD is W7 child `c713d26`.

## 3. Runtime topology (measured 2026-08-21 ~19:13–19:18 +10)

| process | PID | PPID | started | port | commit |
|---|---|---|---|---|---|
| `telegram_center/center.py` | 2080 | 30764 | 19:12:56 local / `2026-08-21T09:12:58Z` | 8776 | `c713d26` (process-identity) |
| `miniapp_gateway.py` | 12220 | 25980 | 16:18:04 | 8774 | NOT_MEASURED (no identity file) |
| `cortex/cortex.py` | 24760 | 25216 | 16:19:05 | 8772 | NOT_MEASURED |
| `organism.py` | 19444 | 3660 | 16:22:04 | 8771+8777 | NOT_MEASURED |
| unknown listener | 6024 | — | — | 8773 | NOT_MEASURED (likely live-watchdog sibling) |

- Scheduled: `OCTOPUS-TG-Center-Watchdog` Ready (plus MiniApp/Live/Cortex/organism watchdogs).
- Mode: polling only. Webhook: absent (owner gate). SenderBridge: not imported by center (default-off) CONFIRMED by grep.
- One Center PID. Duplicate poller: NOT_MEASURED beyond single matching `center.py` CIM instance.
- poll-health after ~3 min: started=16 completed=16 empty=16, workers=0, threads=4.
- Pulse `tg-center.json` pid=2080; timestamps naive local vs process-identity UTC — clock-label inconsistency PARTIAL.
- Paid-path counters: not opened this session (forbidden).
- Token: boolean present via env of Center process only; bytes never read.

W7 STATUS said live restart was not performed. Runtime now shows Center **did** boot `c713d26` at 09:12:58Z. Classification: **PARTIAL** (restart happened; 60-minute soak NOT_MEASURED; builder of W7 did not claim TELEGRAM_LOOP_BASELINE).

## 4. Component inventory

See `_ops/state/debug/component-map.json`. Headline: Telegram W0–W7 modules exist on HEAD; cognition consume-path was telemetry-only.

## 5. Canonical state ownership

See `_ops/state/debug/state-ownership.json`. No second database introduced. MemoryContext artifacts live under `state/pulse/` (same owner as memory-read telemetry).

## 6. Blocking-I/O inventory

| site | status | notes |
|---|---|---|
| `center-config.json` Path.read_text | CONFIRMED mitigated | ConfigManager + bounded_io (W2/bcbc3dd) |
| `socket.getaddrinfo` | PARTIAL | thread pool + optional subprocess (W3); subprocess default-off |
| `poll-health.json` read+write every round | CONFIRMED live | 16/16 counters; mtime age ~8s; this session eliminates **re-read** after boot, keeps durable write (existing `test_tg_poll_health` contract) |
| `bounded_io` daemon threads | CONFIRMED residual | uncancellable; capped at 4; live active_transport_workers=0 |
| mission/rfcs Path.read_text | CONFIRMED mitigated | bounded_json_read (W2) |
| watchdog pulse file | CONFIRMED | `tg-center.json` every iteration; PS1 does **not** call `watchdog_truth()` |

## 7. Loop closure matrix

See `_ops/state/debug/loop-closure-matrix.json`.

Open (pre-this-session, runtime-proved):

- Memory read → decision consume (H3): `memory-read-latest` OK, 3 reads/cycle, `executable=false`; newest event id **not** present in cortex-state/actuation/outcomes.
- `last_dispatch_completed_at` absent from poll-health.
- Watchdog T5 taxonomy not implemented in PS1 (pulse-age only).
- Sender live attach default-off (intentional).
- Independent verifier pending.

## 8. Black-box register

- AV byte-range locks (environmental).
- Live DNS resolver quality.
- MiniApp tunnel stderr.
- Cortex/organism boot IDs (no process-identity files).
- Whether watchdog has restarted Center since 09:12:58Z (log not fully tailed this session).

## 9. Confirmed failures / gaps

1. **Memory telemetry ≠ cognition.** `tick_from_spine` maps spine rows and writes pulse; `improve.gather_signals` / planner never receive a typed MemoryContext. Runtime: `newest_id_consumed_by_cortex_artifacts=false`.
2. **poll-health hot read.** `_load()` before every `_save()`.
3. **Dispatch timestamp missing** from health schema.
4. **Watchdog does not consume `watchdog_truth()`.** T5 states not classified.
5. **163/163 and 202/202** are builder-run at historical HEADs; `verifier_independent=false` CONFIRMED in commits. Independent verification still pending.

## 10. Unproven hypotheses

| id | claim | falsifier |
|---|---|---|
| H1 | Every poll round reads poll-health.json from disk | After patch, second `record_poll` in one process does not call `_bounded_read` / Path.read_text |
| H2 | bounded_io DNS workers accumulate without bound | After 100 stalls, `active_worker_count()==0` and thread delta bounded (already claimed W6; re-verify if regressions) |
| H3 | Memory reads never change a later decision | Cycle-2 fixture: prior failed experiment → `hold_and_revise` referencing `context_id` |
| H4 | Empty long poll is treated as hang by watchdog | PS1 kill on pulse age only; empty polls still pulse — likely REFUTED for current watchdog, NOT_MEASURED for `watchdog_truth` unused path |
| H5 | last_dispatch_completed_at never recorded | After patch, `commit_result` sets the field in HealthState |

Lead claims from the megaprompt (verified):

| lead | verdict |
|---|---|
| workspace near `equip/g10-cognition-20260816` | CONFIRMED |
| C1–C4 freshness/nonce/retry_after/queue/sender default-off | CONFIRMED in git log 2325ffce–fa38d16 |
| 163/163 frozen + independent verification pending | PARTIAL (builder green; independent=false) |
| Center blocked on config read and getaddrinfo | CONFIRMED historically (bcbc3dd, a8f2e1a); live Center currently completing empty polls |
| thread wrappers don't kill file/DNS workers | CONFIRMED residual (docstring + design); live workers=0 |
| poll-health hot-loop I/O | CONFIRMED |
| modules exist but connections incomplete | CONFIRMED for memory consume; PARTIAL for telegram W0–W7 |
| memory write-only / half-blind self-model | PARTIAL: reads occur (3/cycle) but are not decision inputs |
| Wave 1 lock.json true vs megaprompt forbidden | CONFIRMED conflict; this session does **not** touch Wave 1 |

## 11. Existing patch lineage

Telegram W0–W7 already on this branch (`f7dbebc`…`c713d26`). This plan is **cognition + residual health**, not a rewrite of those waves.

Uncommitted preserved: `organism.py` orphan_watchdog observe-only; `improve.py` calibration consume (S-A03).

## 12. Patch conflicts and overlaps

- Do not revert W1–W6 tests. HealthState must keep `test_tg_poll_health` file-mark contract (write after record).
- Do not edit `run_all.py` / `center.py` / `wiring.py`.
- `memory_read_loop` header still says unwired; organism **does** call it — comment STALE; behavior stays fail-soft.

## 13. Proposed minimal architecture

```
HealthState (in-memory, load-once per path)
  → write-through snapshot (durability for existing tests)
  → incident jsonl on failure
  → last_dispatch_completed_at from durable_loop.commit_result

MemoryReadLoop (existing 3 queries)
  → retrieve_similar_failures + retrieve_owner_decisions
  → MemoryContext (typed)
  → decide_from_context (explore | continue | hold_and_revise)
  → pulse/memory-context-latest.json
  → improve.gather_signals consume (propose-only)

typed_agent.AgentContract (seams only; no free-form chat; critic ≠ builder)
```

## 14. Implementation waves (this session)

- W0b: this plan + four JSON maps
- W8: MemoryContext + cycle-2 test + organism/improve consume (fail-soft)
- W1b: HealthState no re-read + last_dispatch + classify() (no PS1 kill-policy change — TCB-adjacent)
- W9: typed agent contract seams + test

## 15. Acceptance tests per wave

- W8: `test_memory_cycle_context.py` — cycle1 explore, cycle2 hold_and_revise, context_id binding, isolated store
- W1b: second record_poll does not disk-read; `last_dispatch_completed_at` set; existing `test_health_truth_20260821` + `test_tg_poll_health` still pass
- W9: critic cannot share builder tool lease; required fields present

## 16. Rollback per wave

`git revert <wave SHA>` of files listed in the commit. No migrations. HealthState is backward-compatible JSON.

## 17. Evidence classification

| class | this session |
|---|---|
| git object | HEAD `c713d26…` |
| runtime process | Center PID 2080 |
| pulse/file | poll-health, memory-read-latest, process-identity |
| fixture test | W8/W1b/W9 |
| builder ≠ verifier | independent_verification_pending=true |

## 18. Independent verification plan

Verifier session at declared HEAD after these commits, separate process, `verifier_independent=true` only if that session reproduces fixtures without this working tree. SIG-IV remains owner-gated.

## 19. Live canary gates

All blocked: G-CANARY-IN/OUT, G-WEBHOOK, G-PAID, G-WAVE1, G-PUSH, G-TCB (watchdog kill policy / auth roots).

## 20. Owner decisions required

1. Controlled no-send Center reload after W1b if HealthState should apply to PID 2080 (currently still old module).
2. Independent verifier session.
3. Any live canary.

## 21. Explicit non-goals

Live send, webhook, paid calls, Wave 1 mutation, SenderBridge attach, transport-subprocess default-on, 60-minute soak claim, AGI/self-healed language, rewriting HANDOFF history pins, touching `_Archive`.
