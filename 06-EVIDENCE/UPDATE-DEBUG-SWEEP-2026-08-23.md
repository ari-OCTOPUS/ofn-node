---
type: report
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
tags: [octopus, debug, memory, scheduler, lease, halt]
created: 2026-08-23
updated: 2026-08-23
created_by: agent
sources:
  - "[[OCTOPUS/CURRENT-TRUTH]]"
  - "[[01-TRUTH/CONTRADICTIONS]]"
  - "[[06-EVIDENCE/UPDATE-DEBUG-SWEEP-2026-08-16]]"
---

# OCTOPUS Full Update & Debug Sweep — 2026-08-23

Verdict: **PASS_WITH_FINDINGS**. Defects with safe, reversible fixes were repaired. No
consequential feature was armed, no live Telegram message was sent, and no live
halt drill was executed.

## Live stamp

- `OCTOPUS/CURRENT-TRUTH.md` auto block: generated
  `2026-08-22T23:44:51Z`, HEAD `ad788b6`, beat `46265`, coherence `0.981`,
  `halted=False`.
- `_ops/state/ORGANISM-STATE.json`: `2026-08-23T09:44:54+10`, beat `46266`,
  started `08:02:27`, frozen false, germline lag `0.11h`, recall events `91`,
  median reach `21.0`.
- The auto-block's `members_present=11` is still an awareness-member count, not
  an OS-process count.
- Corrected manifest snapshot: all five declared limbs observed, `board_cp`
  separated as persistent auxiliary, audit/tool processes separated as
  transient, unknown command-line members `0`.

## T1 — stale sync

**Fixed: memory acceptance metrics silently forgot archived history.**

`telemetry_metrics()` read only `dashboard_events`; housekeeping moves old rows
to `events_archive`. The apparent long-window ratios therefore changed with
retention. Commit `ad788b6` now unions both tables while preserving `after_id`.

Current archive-aware live measurement:

- read-before-decision: `2965/4213 = 0.703774` versus target `0.95`;
- readback success: `618/629 = 0.982512` versus target `0.99`.

The system therefore does **not** meet either all-history phase-zero target,
despite recent windows reaching 1.0. Regression:
`test_memory_metrics_archive_20260823.py` PASS.

**Fixed: manifest probes counted themselves as organism members.**

Classification now uses the exact entry file, distinguishes persistent
auxiliaries from transient audit/test/tool processes, and reports both
`members_observed` and `observed_processes_total`. Regression:
`test_organism_manifest_filter_20260823.py` PASS.

**Truth retained, not cosmetically rewritten:**

- canonical live consolidation is `_ops/neural/consolidation.py`, called from
  `organism.py → wiring.consolidation_beat`;
- its history currently ends at persisted cycle `639` with folded logical
  `last_cycle=657`;
- `4d_system/brain/consolidation.py` is explicitly RETIRED and remains unwired;
- strongest current Hebbian edge is `errors_high × rhythm_amber`, strength
  `0.990025`, `29` co-occurrences;
- `afferent_starved × errors_high` has more historical co-occurrences (`37`) but
  is stale;
- circuit target `orchestr` is **open**, last success
  `2026-08-12T07:52:59`, with a 20-failure recent window. It must not be called
  recovered. Target `reason` is closed with recent successful outcomes.

## T2 — launcher-class defect

The two affected scheduled actions now use the full
`C:\Program Files\Python313\python.exe` path rather than bare `py`.

- `OCTOPUS 4d Poisoning Watch`: enabled/Ready, last run
  `2026-08-23T04:08:10+10`, result `0`.
- `OCTOPUS 4d Consolidation Tick`: disabled, last run
  `2026-08-23T05:49:01+10`, result `0`.

The consolidation task was not left enabled merely because its launcher was
repaired: its script still imports the retired 4d consolidation implementation.

## T3 — R18 scheduler decision

Decision: **disable the legacy sidecar task; do not create a replacement task.**

Reason: the live organism already calls the canonical `_ops/neural`
consolidation. Scheduling `_ops/audit/consolidation_4d_tick.py` would revive a
retired duplicate and create two incompatible consolidation histories. A future
4d-specific revival requires a new owner decision and removal of the RETIRED
contract first.

## T4 — Telegram lease path

A real, owner-gated, default-off enforcement seam now exists at both outbound
boundaries:

- `telegram_center.tg_api.TgClient._call_post`;
- `budget.approval_channel._url_json_post`.

The seam reuses `octopus_v3.lease.CapabilityLease` and enforces:

- HMAC integrity;
- exact action and canonical-parameter binding;
- maximum 30-second TTL;
- single-use atomic consumption and replay rejection;
- local revocation and a dedicated lease kill flag;
- fail-closed behavior on missing lease, missing key, evaluation/import errors,
  hash drift, expiry, revocation, or kill.

Runtime post-fix evidence showed no-lease deny before transport, one valid allow,
then replay/hash/expiry/revoke/kill denials, plus the same deny/allow behavior at
the approval-channel boundary. The durable regression reports
`PASS telegram real lease seam 6/6`.

Boundary: enforcement remains **OFF by default** and there is no production
caller of `issue_real_lease()` yet. Only the API and choke points exist. This is
intentional: arming the flag or adding an owner issuer is a consequential owner
decision.

## T5 — live halt-drill readiness

The static/integration readiness floor passed for:

- master halt;
- outbound halt;
- halt coverage;
- provider-effect halt;
- launcher halt;
- halt integration.

No live TCB mutation or process halt was performed. The live drill remains an
owner-window operation using `04-SYSTEMS/HALT-DRILL-RUNBOOK-2026-08-16.md`.

## T6 — contradiction ledger true-up

No agent-only closure was promoted to owner truth.

- C-047 is documented elsewhere as closed-with-fix.
- C-048 through C-053 remain explicitly **candidates**, not registered
  contradictions.
- The safe next unallocated identifier is therefore **C-054**, while preserving
  the candidate reservations.
- C-018 and C-021 remain owner-review items; this sweep does not silently close
  them.

## T7 — regression floor

Targeted checks are green:

- memory archive KPI regression: PASS;
- manifest filter regression: PASS;
- hypothesis compatibility suite after UTF-8 setup: PASS;
- Telegram lease seam: 6/6 PASS;
- six halt suites: PASS.

The repository-wide `run_all.py` floor is **RED / INCOMPLETE**, not green. The
run surfaced existing branch failures across heart-fuel wiring, approval
single-consumer ownership, LLM inventory, spine replay, lead memory wiring,
flags line endings, self-knowledge, verdict feedback, runner scoring, and router
snapshots, then timed out after 300 seconds in `test_bounded_read.py`. No new
targeted regression failed, but this dirty shared branch cannot claim a global
green floor.

## T8 — secret and egress hygiene

- gitleaks `8.30.1`: no leaks in `_ops/budget`, `_ops/telegram_center`,
  `_ops/audit`, `_ops/hypothesis_engine`, `4d_system/brain`, either new
  regression file, or commit `ad788b6`.
- Scanning all `_ops/tests` still reports `316` historical fixture findings;
  this is existing test-fixture debt, not a clean-directory result.
- Tests used injected transports; no live Telegram HTTP send occurred.
- General egress enforcement and Telegram lease enforcement are separate:
  current flags report `OCTOPUS_EGRESS_ENFORCE=1`, while
  `OCTOPUS_TG_PEP_ENFORCE` remains absent/default-off.

## Remaining owner decisions

1. Choose a controlled window for the live halt drill.
2. Decide whether to create and arm a production Telegram lease issuer.
3. Review C-018/C-021 and candidate C-048..C-053 before ledger promotion.
4. Triage the repository-wide regression floor separately; do not attribute its
   existing failures to this narrow sweep without individual reproductions.

## Vault validation

Both mandatory validators completed and failed on accumulated vault debt:

- frontmatter: `823` notes checked, `450` errors, exit `1`;
- links: `3733` notes checked, `19` curated-layer broken links plus `28`
  operational/package warnings, exit `1`.

Neither validator named this sweep's new report or its new handoff links. The
session therefore does not claim a globally valid vault, and the validators
were not weakened to manufacture green.

## Change and checkpoint boundary

- Committed: archive-aware memory metrics and regression (`ad788b6`).
- Implemented but still uncommitted in the shared dirty tree: manifest
  classification, hypothesis API compatibility, Telegram lease seam, and their
  regressions.
- No push was performed.
