# 04 Contradictions — A02 Runtime Investigator (CONSOLIDATED)

## C-1 — Brain identity (MEDIUM)
- **Claim:** "Brains are 4d_system and NBB-CP (mutual veto 50/50)."
- **Observed:** No 4d_system process. Live: organism.py loop + cortex.py. brain_core SHADOW matched=0. "NBB" is code naming (`control_plane/dual_brain.py`, `octopus_v3/`), not a running brain. CURRENT-TRUTH.md itself says 4d is not connected. (F-02: the only NBB-adjacent runtime is an hourly observatory script running from the Desktop.)
- **Resolution owner:** A09 (Dual-Brain Governance). Runtime inventory must be the baseline.

## C-2 — Policy Gate enforcement scope (MEDIUM)
- **Claim:** "Policy Gate is runtime-enforced."
- **Observed:** Two gates exist: ADR-033 policy_gate.py (live but ONE call site — protective halt only) and octopus_v3 P0 overlay (WIRED=False, dormant). Neither is a universal chokepoint today. adr-033 events silent since 2026-08-13 (F-17).
- **Note:** commit 028fe81 message is honest ("WIRED=False") — the overstatement lives in higher-level claims, not the commit.

## C-3 — propose_only label vs mechanism (MEDIUM)
- **Claim:** "Actions are propose-only" (implying an enforced property).
- **Observed:** `propose_only: True` is a hardcoded reporting field per leg; actual safety is structural (no executor paths for A2+, NOT_WIRED money stubs, wired() telegram guard). Functionally true today; architecturally a label. Compounding: autonomy arming flags are live (F-12) — the safety story rests on the executor staying empty.

## C-4 — Dashboard liveness (LOW)
- **Claim:** channel-status.json `panel_8790: true`.
- **Observed:** No 8790 listener (nor 8770) on the host. Snapshot channels are not refreshed (file's own writer_note admits it).

## C-5 — "effected" proposals vs gated_effect ledger (LOW)
- **Claim:** proposal_metrics effected=42.
- **Observed:** chrono.db `gated_effect` table has 0 rows ever. The 42 "effects" are internal state transitions, not gate-transacted external effects. Also `proposals_fake_delivered=10` is self-labeled in state.

## C-6 — A2/A4 semantics (LOW, safer than claimed)
- **Claim:** "A2 bounded automatic; A4 requires owner approval."
- **Observed:** A2→BLOCK (VQ-SELFGOAL-002 governance vote), A4→BLOCK, A5→BLOCK, A6→REJECT. Only A0/A1 executable. The system is currently more locked than the claim describes. Tension with C-7-adjacent F-12: free-tier autonomy flags are armed, so *if* the classifier vote ever flips, automation is pre-armed.

## C-7 — Arbiter period vs beat cadence (INFO)
- state `arbiter.effective_period_s≈124.7` vs observed beat every ≈65 s (parallel window) and ≈128 s (primary window). Different clocks for different subsystems; naming invites misreading.

## C-8 — "Sensorium is active" (MEDIUM) [primary]
- **Claim:** Sensorium is an active subsystem.
- **Observed:** NOT_FOUND — zero occurrences of "sensorium" in any live code path (`_ops`, `4d_system`). Documentation-only concept (F-10).

## C-9 — "Viability Loop is runtime-enforced" (MEDIUM) [primary]
- **Claim:** Viability Loop enforced at runtime.
- **Observed:** NOT_FOUND — no code anywhere in `_ops/4d_system/OCTOPUS/03-GATES/04-SYSTEMS` (F-18).

## C-10 — "Governance is mutual veto" (HIGH) [primary]
- **Claim:** Mutual-veto governance between the two brains is in force.
- **Observed:** `dual_brain.py` implements it fully, but `OCTOPUS_WIRE_DUAL_VETO` is absent from the live boot flags → disabled; its own code defers execution enforcement to an unbuilt "phase 8e" (F-16, R-003).

## C-11 — Timestamp self-inconsistency (MEDIUM) [primary]
- `pulse/math-control-latest.json` writes local (+10:00) time with a UTC `Z` suffix — 10 h mislabel — while sibling artifacts (board-status +10:00, state_guard true-UTC, miniapp-url true-UTC) are correct (F-24). Internal contradiction independent of any external claim.

## C-12 — "Flags default off" narrative vs all-on reality (LOW) [primary]
- Code and older docs describe most `OCTOPUS_WIRE_*` gates as default-off; the live boot loads ~200 of them set to '1' from `OCTOPUS-flags.cmd` (335 flags, shortfall 0). Not a code bug — but any doc asserting defaults describes a machine that isn't this one (F-22).

## C-13 — Dual approval ledgers (MEDIUM) [primary]
- `_octopus/approvals.json` + `audit.log` still receive approvals (today 12:35) while adr-033 proposals/replay and cortex decision cards also exist; `gated_effect` shows 0 rows. Which ledger is authoritative is undecidable from runtime alone (F-28; A03).

## C-14 — Spend-cap window expiry (LOW) [primary]
- Docs/narrative may assume the AU$200/day temporary cap; its `UNTIL=2026-08-13` has lapsed. Permanent money gates remain, but the "capped at 200" story is expired (F-14).

## Cross-checks that did NOT contradict
- CURRENT-TRUTH HEAD == git HEAD (R-020); ORGANISM-STATE.started == PID 29028 creation time; beat count == heartbeat table rows (±2 in-flight); money lock, kill-switch files, HALT semantics consistent between code and state; tunnel URL-file pid == live cloudflared pid (F-03); tg-center/miniapp pid fields == live PIDs (F-25).
