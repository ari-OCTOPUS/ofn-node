# A02 Runtime Investigator — Executive Summary (CONSOLIDATED)

**Run:** 2026-08-16-wave-01 · **Mode:** READ_ONLY (both observers) · **Window:** 2026-08-16T23:44–23:59 +10:00
**Repo HEAD:** `028fe81` (branch `equip/g10-cognition-20260816`, dirty tree ≈220 files — mostly runtime state, expected for a live organism)
**Note:** two independent read-only A02 observers converged on this directory (windows 23:48–23:54 and 23:44–23:59). This is the merged deliverable: findings R-001…R-020 (parallel observer) + F-01…F-30 (primary observer), cross-reconciled. Full detail: `02_FINDINGS.md`; machine digest: `09_MACHINE_SUMMARY.json`.

## What is actually running (T0)

OCTOPUS is **live right now**, not a documentation artifact. Six Python services run from `F:\backup\_ops` on system Python 3.13.7 (no venv):

- `organism.py` (PID 29028, since 12:53; ports 8771 status + 8777 lead-boundary) — main loop; beat advances monotonically (38507→38509→38511→38513→38516 observed across both windows; cadence varies ~65–128 s — the arbiter's `effective_period_s≈125` describes the heart consensus, not the beat loop).
- `cortex\cortex.py` (8772), `live\server.py` (8773), `telegram_center\center.py` (8776), `miniapp_gateway.py` (8774), `board_cp\server.py` (TLS on **0.0.0.0:8801**).
- `cloudflared` named tunnel publishes the MiniApp at `https://app.master-painting.com` → 127.0.0.1:8774 (since 06:58).
- Local `ollama serve` (11434) + `llama-server` (1495, `--offline`).
- 12 scheduled tasks sustain the stack (watchdogs every 5–10 min; observatory hourly — **one executes from the Desktop, outside the repo**).

**Heartbeats are genuinely live** (both observers independently): beat, arbiter snapshot and `identity_health` recompute every cycle; `chrono.db` (heartbeat table ≈38.5k rows, per-beat `ledger_hash`) updates in real time; hourly `organism=ok` line fires on a 3600 s wall-clock gate.

## Headline claim verdicts (merged)

| Claim | Verdict |
|---|---|
| "Brains are 4d_system and NBB-CP" | **CONTRADICTED at runtime** — no 4d_system process; live brains are the organism loop + cortex; brain_core SHADOW matched=0 (R-003) |
| "Governance is mutual veto" | **PRESENT_NOT_WIRED** — dual_brain.py complete, `OCTOPUS_WIRE_DUAL_VETO` off in live flags (F-16) |
| "Actions are propose-only" | **Structurally true today, but it's absence-of-paths, not a gate** — executor allows only A0/A1; A2/A4/A5→BLOCK; `propose_only:True` is a reporting label. Caution: autonomy flags `AUTONOMY_FREE/GRANT/CODE_AUTOAPPLY_LOWRISK/LEAD_OUTBOUND` are armed (R-007, R-009, F-12) |
| "A2 bounded automatic; A4 owner approval" | **CONTRADICTED — currently safer than claimed**: A2→BLOCK (VQ-SELFGOAL-002), A4/A5→BLOCK, A6→REJECT; only A0/A1 executable, A1 defaults dry_run (R-009) |
| "Money locked, destructive disabled" | **Effectively true**: money_gate fail-closed (AU$20 threshold, NotWiredStub deny-all, month spend AU$0.74); no payment call sites; outbound HTTPS NOT_WIRED. BUT the octopus-v3 HARD_NO_GO overlay is `WIRED=False` — dormant code, not enforcement (R-008, F-13, F-15). Temporary spend-cap window expired 2026-08-13 (F-14) |
| "Policy Gate runtime-enforced" | **OVERSTATED** — ADR-033 gate is fail-closed but has exactly ONE live call site (protective halt); overlay unwired; adr-033 event stream silent since 08-13 (R-010, F-17) |
| "Viability Loop runtime-enforced" | **NOT_FOUND** — no code anywhere (F-18) |
| "Sensorium active" | **NOT_FOUND** — no code anywhere (F-10) |
| "Ledger live and bitemporal" | Live: **VERIFIED** (per-beat writes + ledger_hash). Bitemporal: **NOT FOUND in schema**; `gated_effect` table has 0 rows ever (R-006; A03 scope) |
| "identity_health = 0.572" | **STALE** — live value 0.542, recomputed per math-control tick (R-005, F-07) |
| runtime_state / readiness_state / bus_state / acquisition_state / safety_state | **NOT_FOUND** as fields; closest live analogues: `wiring`, `halted/frozen/protective_skip`, `epoch_mode` (F-09) |
| Disabled modules emit OFF heartbeats | Mechanism wired; **zero dormant modules exist today** (all module flags on) so nothing emits — vacuously true, untestable live (F-20) |
| Kill switches | Per-loop checks in all four processes + launcher boot guards; `OCTOPUS_WIRE_KILL_SEAM=1` (F-19); rejection not exercised (read-only) |

## The five things the owner should read first

1. **Safety today is structural, not gated (HIGH).** Nothing enforces propose-only as a chokepoint: it holds because the executor simply has no A2+ code paths and money/outbound stubs are unwired. Any new effector added without a gate silently inherits "allowed" (R-007, R-010, F-15/F-16/F-18).
2. **Autonomy flags vs narrative (MEDIUM).** `OCTOPUS_AUTONOMY_FREE=1`, `OCTOPUS_AUTONOMY_GRANT=1`, `OCTOPUS_CODE_AUTOAPPLY_LOWRISK=1`, `OCTOPUS_LEAD_OUTBOUND=1` are live; A2 remains blocked only by a classifier vote (VQ-SELFGOAL-002). Reconcile flags with the propose-only story (F-12, R-009).
3. **Exposure (MEDIUM):** public tunnel to 8774 and 0.0.0.0:8801 (TLS+Bearer, fail-closed pull/ack only) — carried to A04. `.env.bak-20260810` (stale credential copy) sits at repo root (R-016).
4. **Runtime ≠ code (MEDIUM):** processes booted 12:53–16:43 while `organism.py`/`wiring.py` were edited 23:01 and committed 23:27; no boot-hash is recorded, so the exact running revision is unknowable post-hoc (F-23). CURRENT-TRUTH's HEAD field does match git (R-020).
5. **Clock hygiene (MEDIUM):** no `time.monotonic` anywhere; `math-control-latest.json` writes **local time with a `Z` suffix** (10 h mislabel) (F-24); `frozen:true` while beats continue — semantics undocumented (R-015).

## Special question — enforced vs present

Runtime observation proves **presence and activity** (process, listener, per-beat writes, values changing). It **cannot by itself prove enforcement**: enforcement is only demonstrable by observing a violating action being *rejected* (which a read-only agent must not trigger) or by executed tests (T1). This wave went further in the negative direction: runtime evidence affirmatively proves **absence of wiring** for two claimed enforcers (dual-brain veto, HARD_NO_GO overlay) and shows propose-only resting on structural absence rather than a gate.

## Verdict

**READY_FOR_NEXT_WAVE**

Runtime reality is observable, non-regressing, and — for action classes — materially *safer* than several documented claims suggest. No critical safety block originates from the runtime layer itself. Next-wave dependencies: A03 to adjudicate the parallel approval ledgers (`_octopus/approvals.json` still active today vs adr-033 vs cortex cards) and ledger bitemporality; A04 for the exposure surfaces; owner decisions on F-12/F-15/F-16 (autonomy flags; wiring or formally deferring the governance overlay).
