# 02 Findings — A02 Runtime Investigator (CONSOLIDATED)

Legend: status ∈ VERIFIED_LIVE / VERIFIED_CODE_ONLY / VERIFIED_TEST_ONLY / DOCUMENTED_NOT_IMPLEMENTED / STALE / CONTRADICTED / NOT_FOUND / UNKNOWN (plus compound statuses where honest). Tier per truth hierarchy. Confidence 0.0–1.0.
Two observers: **R-*** = parallel observer (window 23:48–23:54+10:00), **F-*** = primary observer (window 23:44–23:59+10:00). Machine-readable versions (all fields incl. commands) in `03_EVIDENCE.jsonl`.

## Reconciliation notes (read first)

- **Beat cadence**: R-002 measured ~65 s/beat (23:49–23:53); F-05 measured ~128 s (23:53–23:57). Both are real — tick cadence is variable. The arbiter's `effective_period_s≈125` describes the heart-consensus period, **not** the beat loop (naming trap, C-7).
- **Propose-only**: R-007/R-009 (structural: executor EXECUTABLE={A0,A1}, A2/A4/A5→BLOCK; `propose_only` is a reporting label) + F-12 (autonomy arming flags live: AUTONOMY_FREE/GRANT/CODE_AUTOAPPLY_LOWRISK/LEAD_OUTBOUND=1, boot log "code-apply armed but active()=False"). Merged verdict: **structurally propose-only today; enforcement is absence-of-paths, not a gate; flag arming is a latent widening risk**.
- **Git/runtime**: R-020 (CURRENT-TRUTH HEAD == git HEAD; truth-sync live) + F-23 (running processes predate the 23:01 edits and 23:27 commit). Both true: docs are current, the running bytecode is not.
- **Overlap map**: R-001≈F-01, R-002≈F-05, R-004≈F-30, R-005≈F-07, R-008≈F-13, R-010≈F-15/F-17, R-011⊂F-24, R-014≈F-03/F-04, R-016≈F-22, R-018⊂F-13.

---

## Section A — Parallel observer findings (R-001…R-020)

### R-001 — OCTOPUS organism is live
- **Claim:** OCTOPUS runs locally as a live python organism.
- **Status:** VERIFIED_LIVE · **Tier:** T0 · **Confidence:** 1.0 · **Severity:** INFO
- **Evidence:** PID 29028 `python -X utf8 organism.py` started 2026-08-16 12:53:10; matches `ORGANISM-STATE.json.started=2026-08-16T12:53:10`. Plus 5 further python processes (cortex, live, telegram center, miniapp gateway, board_cp) + ollama + cloudflared.
- **Source:** `raw/PROCESS_SNAPSHOT.md`, command `Get-CimInstance Win32_Process`.
- **Contradiction:** none. **Next:** none needed.

### R-002 — Heartbeat advances monotonically over ≥3 cycles
- **Claim:** Beat loop is alive and non-regressing.
- **Status:** VERIFIED_LIVE · **Tier:** T0 · **Confidence:** 0.95 · **Severity:** INFO
- **Evidence:** beat 38507 @23:49:11 → 38509 @23:51:18 → 38511 @23:53:31 (≈65 s/beat). chrono.db `heartbeat` table 38,509 rows; `checkpoint` 38,508 rows with per-beat `ledger_hash`. WAL file mtime advanced during session.
- **Source:** `raw/HEARTBEAT_TRANSCRIPT.jsonl`; sqlite read-only.
- **Contradiction:** none observed in window. **Next:** longer soak if required by A15.

### R-003 — "Brains are 4d_system and NBB-CP"
- **Claim:** The two reasoning brains are 4d_system and NBB-CP.
- **Status:** CONTRADICTED (runtime) / VERIFIED_CODE_ONLY (naming only) · **Tier:** T0+T2 · **Confidence:** 0.85 · **Severity:** MEDIUM
- **Evidence:** No process runs from `4d_system/`. Live brain processes: `organism.py` loop + `cortex\cortex.py` (8772). `brain_core` runs SHADOW-LIVE with counters `matched=0, missing_old=4167`. CURRENT-TRUTH.md itself states 4d/Super-Governor not connected. "NBB" appears in code (`control_plane/dual_brain.py`, `goal_action_bridge.py`, `octopus_v3/`) but not as a running process. (Primary observer adds: 4d artifacts processed via 6-hourly schtasks; NBB observatory runs hourly **from the Desktop** — F-02.)
- **Contradiction:** with project claim; see C-1. **Next:** A09 should define the canonical brain inventory from live processes.

### R-004 — Telegram cockpit surface live
- **Claim:** Telegram is a cockpit surface.
- **Status:** VERIFIED_LIVE · **Tier:** T0 · **Confidence:** 0.95 · **Severity:** INFO
- **Evidence:** PID 11724 `telegram_center\center.py`; `channel-status.json` telegram `live: true, mode: long-poll(T-8)` (ts 23:51:09, refreshed live); `.env` names `TELEGRAM_BOT_TOKEN`, `TG_CENTER_BOT_TOKEN`, `TG_ZIMAN_STUDIO_BOT_TOKEN` (values unread); miniapp gateway + cloudflared tunnel `octopus-miniapp` → 127.0.0.1:8774 (public HTTPS via Cloudflare).
- **Note:** telegram channel `allowlist: false, owner_set: true` — interpretation deferred to A04.
- **Contradiction:** none. **Next:** A04 audits the gateway auth wall.

### R-005 — identity_health
- **Claim:** identity_health reported 0.572.
- **Status:** STALE · **Tier:** T0+T2 · **Confidence:** 0.95 · **Severity:** LOW
- **Evidence:** Live value 0.542, constant across ≥4 beats, refreshed per math-control tick. Code: `_ops/math_control/spine.py:157-181` recomputes via `identity_equations.evaluate()` — mean of learner/earner/guardian/creator/organism identity values; with `money_confirmed=0` the score is driven by draft_rate (0.25) and budget_frac (0.15) terms (`_ops/identity_equations.py:73,381,400`).
- **Verdict:** live-computed, not cached; the 0.572 figure is outdated lore.
- **Contradiction:** with claim. **Next:** regenerate docs from state.

### R-006 — Ledger live; bitemporality unproven
- **Claim:** The ledger is live and bitemporal.
- **Status:** VERIFIED_LIVE (liveness) / NOT_FOUND (bitemporality) · **Tier:** T0 · **Confidence:** 0.9 / 0.7 · **Severity:** LOW
- **Evidence:** `chrono.db` tables: heartbeat(38,509), checkpoint(38,508, ledger_hash), leg_clock(1), experience_meter(38,074), duration_marker(106), metabolic_age(2), **gated_effect(0)**. Heartbeat columns: beat_seq, wall_ts, hlc_phys, hlc_logical, present_legs, absent_legs, workspace_ref, ts — **no valid-from/valid-to/supersedes**.
- **Contradiction:** "bitemporal" documented vs schema absent. **Next:** A03/A12 to implement/verify the contract.

### R-007 — Propose-only / outward execution
- **Claim:** External actions are propose-only.
- **Status:** VERIFIED_CODE_ONLY (structural) — with caveat · **Tier:** T2 · **Confidence:** 0.85 · **Severity:** MEDIUM
- **Evidence:** `propose_only: True / outward_execution: False` are hardcoded labels in each leg beat's return dict (`_ops/wiring.py:454,594,677,1105,3386,3742,4040`) — reporting, not a central gate. Actual blocking: `action_bridge/executor.py:35 EXECUTABLE = frozenset({"A0","A1"})` — no execution functions exist for A2+; telegram sends all pass `tg_api.py:509 wired()`; outbound_https returns NOT_WIRED. Legs observed emitting `proposals_emitted: 0` this beat.
- **Contradiction:** label-vs-mechanism (C-3). **Next:** A05 to convert to an enforced gate.

### R-008 — Money locked
- **Claim:** Money is locked.
- **Status:** VERIFIED_CODE_ONLY · **Tier:** T2 · **Confidence:** 0.9 · **Severity:** INFO
- **Evidence:** `_ops/budget/money_gate.py:48` default channel `NotWiredStub` (deny >AU$20); `_ops/integrations/outbound_https.py:176` returns NOT_WIRED without disk/network; no payment API call sites found; `baseline.py:159-175` fails on money-code fingerprint change. State shows `money_link: active` labels but `proposal_value_aud: 0.0`, `confirmed_revenue_aud: null`.
- **Contradiction:** none. Runtime negative-proof impossible by design (correct). **Next:** none.

### R-009 — Action classes A2/A4
- **Claim:** A2 bounded automatic; A4 owner-approved.
- **Status:** CONTRADICTED (today) — safer than claimed · **Tier:** T2+T0 · **Confidence:** 0.9 · **Severity:** LOW
- **Evidence:** `_ops/action_bridge/classifier.py:176-184` DECISION_BY_CLASS: A0/A1→ALLOW, **A2→BLOCK** (VQ-SELFGOAL-002), A3→OWNER_GATE, **A4→BLOCK, A5→BLOCK**, A6→REJECT. Executor has no A2+ paths (`executor.py:9-12,35`); A1 defaults dry_run. Bridge flag ON (`OCTOPUS-flags.cmd:827 OCTOPUS_WIRE_ACTION_BRIDGE=1`).
- **Contradiction:** claim says A2 automatic — code blocks it (C-6). **Next:** governance decision whether A2 stays blocked.

### R-010 — Policy Gate runtime enforcement
- **Claim:** Policy Gate is runtime-enforced.
- **Status:** DOCUMENTED_NOT_IMPLEMENTED (as universal chokepoint) / VERIFIED_CODE_ONLY (narrow) · **Tier:** T2 · **Confidence:** 0.9 · **Severity:** MEDIUM
- **Evidence:** Live ADR-033 `_ops/policy/policy_gate.py` is fail-closed (any exception → DENY; unknown action → DENY) but its **only** live call site is `wiring.py:2057-2094 request_protective_halt()`. The octopus-v3 P0 overlay (P0ExecutionGate, INTENT ledger, taint latch, capability lease, HARD_NO_GO) is `_ops/octopus_v3/__init__.py:12 WIRED = False` — not imported by organism/wiring; commit 028fe81 itself labels it WIRED=False. (Primary observer adds: adr-033 event stream silent since 2026-08-13 — F-17.)
- **Contradiction:** C-2. **Next:** A05 design; wave-2 prototype.

### R-011 — Clock source
- **Claim:** (implicit) system clock basis.
- **Status:** VERIFIED_LIVE · **Tier:** T0+T2 · **Confidence:** 0.9 · **Severity:** INFO
- **Evidence:** state `ts` local wall clock (+10:00); `chrono.hlc` epoch-ms physical + logical counter; `epoch_mode: allostatic` (pressure-driven); host `date` consistent with state ts within seconds.
- **Contradiction:** none. See F-24 for the deeper audit (no monotonic; Z-mislabel bug).

### R-012 — Coherence/arbiter values are live-generated
- **Claim:** coherence 0.859, arbiter GREEN.
- **Status:** VERIFIED_LIVE (values refresh) · **Tier:** T0 · **Confidence:** 0.85 · **Severity:** INFO
- **Evidence:** CURRENT-TRUTH.md auto-block regenerated at 2026-08-16T13:41:27Z (7 min before session read); writer = `cortex/cortex.py:559-623 truth_sync_tick()` gated by `OCTOPUS_WIRE_TRUTH_SYNC=1`, 30-min cooldown, via `intel_spine/obsidian_sync.py:70-75`. Arbiter in live state: GREEN, consensus driver, wire_open. (Primary observer: arbiter recomputed per beat, advisory_only=true — F-06.)
- **Contradiction:** none. **Note:** 30-min cooldown means CURRENT-TRUTH can lag runtime by up to 30 min.

### R-013 — Stale dashboard claims
- **Claim:** panel 8790 live (channel-status.json).
- **Status:** STALE · **Tier:** T0 · **Confidence:** 0.9 · **Severity:** LOW
- **Evidence:** netstat shows no 8790 listener; `live/server.py:34` references dashboard=8770 (also not listening). channel-status.json itself notes only the telegram entry is refreshed live; others are snapshots.
- **Contradiction:** C-4.

### R-014 — Public exposure surfaces active
- **Claim:** (risk observation)
- **Status:** VERIFIED_LIVE · **Tier:** T0 · **Confidence:** 0.95 · **Severity:** MEDIUM (carried to A04)
- **Evidence:** cloudflared `octopus-miniapp` tunnel → 127.0.0.1:8774 (running since 06:58); board_cp TLS on 0.0.0.0:8801 (Bearer + self-signed cert pinning per code).
- **Contradiction:** none.

### R-015 — frozen≠stopped semantics
- **Claim:** (observation) `frozen: true` while beats continue.
- **Status:** VERIFIED_LIVE · **Tier:** T0+T2 · **Confidence:** 0.8 · **Severity:** LOW
- **Evidence:** state top-level `frozen: true`, `halted: null`, `stop_organism: false`, beat advancing. `opslib.frozen()` checks a FREEZE_FLAG file; beat_scheduler blocks ACT/LEARN only under HALT. Freeze semantics undocumented at runtime → operator-confusion risk.
- **Contradiction:** none (naming hazard).

### R-016 — Config provenance
- **Claim:** (observation)
- **Status:** VERIFIED_LIVE · **Tier:** T0+T2 · **Confidence:** 0.9 · **Severity:** LOW
- **Evidence:** precedence chain: process env > `F:\backup\.env` (root, 17 key names incl. 5 provider keys, 3 Telegram tokens, GMAIL_APP_PASSWORD, POCKETSMITH_API_KEY, OCTOPUS_CB_SECRET — values unread) > `_ops/OCTOPUS.env` + `_ops/OCTOPUS-flags.cmd` loaded `setdefault` by services (`board_cp/server.py:36-56`). `OCTOPUS-flags.cmd:1114 OCTOPUS_WIRE_ACTUATOR=1`, `:827 OCTOPUS_WIRE_ACTION_BRIDGE=1`.
- **Note:** `.env.bak-20260810` also present at root (older copy of secrets) — hygiene risk. Primary observer adds the full 5-layer precedence proof and the 335-flag boot snapshot — F-22.

### R-017 — brain_core SHADOW never matched
- **Claim:** (observation) brain_core SHADOW-LIVE, matched=0.
- **Status:** VERIFIED_LIVE · **Tier:** T0 · **Confidence:** 0.9 · **Severity:** LOW
- **Evidence:** state counters compared=4167, matched=0, missing_old=4167 over 348,826 s soak; CURRENT-TRUTH: "SHADOW matched=0 → promote نکن". New comparator produced no old-side samples — parity unproven.
- **Contradiction:** none (matches its own doc).

### R-018 — Budgets live
- **Claim:** (observation) life-currency budgets active.
- **Status:** VERIFIED_LIVE · **Tier:** T0 · **Confidence:** 0.9 · **Severity:** INFO
- **Evidence:** cardiac budget spent 538 / daily_cap 2000, remaining 1462, depleted=false (date 2026-08-16); `cardiac-budget.json` mtime advanced during session. (Primary observer saw 540 a few beats later — both fresh reads; units µUSD-scale, consistent with month AU$0.74 — F-13.)

### R-019 — Proposal metrics vs gated_effect
- **Claim:** (observation) proposals_effected=42 while gated_effect=0 rows.
- **Status:** CONTRADICTED (internal bookkeeping vs gated schema) · **Tier:** T0 · **Confidence:** 0.8 · **Severity:** LOW
- **Evidence:** state proposal_metrics lifecycle delivered=105, effected=42, `proposals_fake_delivered: 10` (self-labeled); chrono.db gated_effect 0 rows. Effects are internal state writes, not gate-transacted external effects.
- **Contradiction:** C-5.

### R-020 — Git/runtime consistency (HEAD fields)
- **Claim:** (observation)
- **Status:** VERIFIED_LIVE · **Tier:** T0 · **Confidence:** 0.9 · **Severity:** INFO
- **Evidence:** CURRENT-TRUTH auto-block HEAD `028fe81` == `git rev-parse HEAD`. 220 dirty files ≈ runtime state + today's notes. (Pairs with F-23: the *processes* still run pre-23:01 code — docs current, bytecode older.)

---

## Section B — Primary observer findings (F-01…F-30)

Full field set (claim/status/tier/source/lines/command/timestamp/confidence/severity/contradiction/action) in `03_EVIDENCE.jsonl`; detail artefacts: `LIVE_PROCESS_MAP.md`, `RUNTIME_CONFIG_PROVENANCE.md`, `CLOCK_AND_TIMESTAMP_AUDIT.md`, `SERVICE_LIVENESS_VS_READINESS.md`, `CLAIM_VS_RUNTIME_MATRIX.csv`.

| ID | Finding (claim) | Status | Tier | Conf | Sev | Key evidence |
|----|-----------------|--------|------|------|-----|--------------|
| F-01 | Six OCTOPUS python services live | VERIFIED_LIVE | T0 | 0.99 | INFO | process snapshot + netstat (≈R-001) |
| F-02 | 12 schtasks sustain stack; one runs from Desktop OUTSIDE repo | VERIFIED_LIVE | T0 | 0.97 | MEDIUM | `Get-ScheduledTask` (`OCTOPUS Observatory Hourly` → `C:\Users\Armin\Desktop\OCTOPUS-NBB-CP-WORKING\...`) |
| F-03 | Named tunnel publishes miniapp publicly (app.master-painting.com→8774); URL-file pid == live pid | VERIFIED_LIVE | T0 | 0.97 | MEDIUM | miniapp-url.json + process 17332 (≈R-014) |
| F-04 | board_cp binds 0.0.0.0:8801; TLS+Bearer, only pull/ack, fail-closed 503 | VERIFIED_LIVE | T0 | 0.90 | MEDIUM | netstat + `board_cp/server.py:1-40` |
| F-05 | beat computed live; 38511→38513→38516 observed, zero observer writes | VERIFIED_LIVE | T0+T2 | 0.97 | INFO | sampler; `chrono.py:1241,1273,1419-1422` (≈R-002; cadence variable) |
| F-06 | arbiter computed live per beat; advisory_only=true; 3-heart consensus (42/490/83 s votes) | VERIFIED_LIVE | T0+T2 | 0.96 | INFO | `pulse/arbiter-latest.json` fresh each beat; `pulse_arbiter.py:405-468` |
| F-07 | identity_health computed live (0.542; may_authorize=false; identities breakdown) | VERIFIED_LIVE | T0+T2 | 0.93 | INFO | `math-control-latest.json` per-beat; `spine.py:157-181` (≈R-005) |
| F-08 | coherence computed on demand behind WIRE_COHERENCE=1; no standalone surfaced value | VERIFIED_CODE_ONLY | T2 | 0.70 | LOW | `identity_equations.py:337-353,393-401` + boot flags |
| F-09 | runtime_state/readiness_state/bus_state/acquisition_state/safety_state: no such fields | NOT_FOUND | T2 | 0.95 | INFO | repo-wide grep; closest analogues listed |
| F-10 | Sensorium: no implementation anywhere | NOT_FOUND | T2 | 0.95 | MEDIUM | `grep -ri sensorium` (_ops, 4d_system) → 0 |
| F-11 | Physical legs: no hardware path; software legs propose-only; HANDLERS registry empty | VERIFIED_CODE_ONLY | T2 | 0.90 | INFO | `wiring.py:637-677,1144-1159`; `approval_actuator.py:46-48` |
| F-12 | Autonomy arming flags live (AUTONOMY_FREE/GRANT=1, CODE_AUTOAPPLY_LOWRISK=1, LEAD_OUTBOUND=1 cap 100/d); boot: code-apply armed but active()=False | VERIFIED_LIVE | T0 | 0.95 | MEDIUM | `flags-loaded-organism.json`; HEARTBEAT 12:52:47 (reconciled with R-007/R-009) |
| F-13 | Money locked live: AU$20 threshold + NotWiredStub; month AU$0.74; budget 540/2000; MONEY_FSM=1 | VERIFIED_LIVE | T0+T2 | 0.90 | INFO | `money_gate.py:35-55` + live state (≈R-008/R-018) |
| F-14 | Temporary spend-cap window EXPIRED (UNTIL=2026-08-13); permanent gates remain | VERIFIED_LIVE | T0 | 0.85 | LOW | boot flags snapshot |
| F-15 | octopus-v3 HARD_NO_GO/INTENT/lease overlay WIRED=False, never imported | DOCUMENTED_NOT_IMPLEMENTED | T2+T3 | 0.97 | HIGH | `octopus_v3/__init__.py:7-12`; grep imports → 0 (≈R-010) |
| F-16 | Mutual veto: dual_brain.py complete; OCTOPUS_WIRE_DUAL_VETO ABSENT from live flags | PRESENT_NOT_WIRED | T0+T2 | 0.95 | HIGH | flags snapshot (DUAL_VETO → False); `dual_brain.py:110-117` |
| F-17 | Policy gate fail-closed + wired, but adr-033 events silent since 08-13 | VERIFIED_CODE_ONLY | T2+T3 | 0.85 | MEDIUM | `policy_gate.py:102-140`; adr-033/events mtimes |
| F-18 | Viability Loop: no code anywhere | NOT_FOUND | T2 | 0.95 | MEDIUM | grep -r viability → 0 |
| F-19 | Kill switches checked per-loop in all 4 processes + launcher boot guards; KILL_SEAM=1 | VERIFIED_CODE_ONLY | T0+T2 | 0.90 | INFO | `organism.py:532`; `cortex.py:842`; `center.py:592-606`; `opslib.py:355-407` |
| F-20 | OFF-heartbeat mechanism wired; ZERO dormant modules today (all module flags on) → nothing emits; events.jsonl last write 23:11 | VERIFIED_CODE_ONLY | T2+T0 | 0.90 | LOW | `off_heartbeat.py:23-56`; `organism.py:549-557`; events tail (0 module.heartbeat) |
| F-21 | Event bus is file/in-process; no broker; stream sparse (45+ min silent while healthy) | VERIFIED_LIVE | T0 | 0.90 | LOW | events.jsonl mtime/tail; no broker process |
| F-22 | Config precedence live-proven: flags.cmd env > env > .env (fills-empty) > auto-knobs (fills-empty, bounded) > defaults; 335 flags, shortfall 0, secrets auto-redacted | VERIFIED_LIVE | T0+T2 | 0.95 | INFO | `flags-loaded-organism.json`; `env_loader.py:33-56`; `auto_approve.py:395-408` (extends R-016) |
| F-23 | Version drift: processes booted 12:53–16:43; organism.py/wiring.py edited 23:01; HEAD 23:27; no boot-hash recorded | VERIFIED_LIVE | T0 | 0.95 | MEDIUM | CreationDates vs mtimes vs `git show -s` |
| F-24 | Clock: no time.monotonic anywhere; math-control writes LOCAL time with 'Z' (10 h mislabel); mixed conventions; board-status +10:00 and state_guard UTC correct | VERIFIED_LIVE | T0+T2 | 0.95 | MEDIUM | grep monotonic → 0; ts cross-comparison (extends R-011) |
| F-25 | No zombies / duplicate listeners / stale PID files; launchers self-guard; pid fields match live PIDs | VERIFIED_LIVE | T0 | 0.95 | INFO | genealogy analysis; 52-listener dedup; find *.pid → 0 |
| F-26 | System Python 3.13.7, no venv for any service; stdlib http.server | VERIFIED_LIVE | T0 | 0.97 | LOW | ExecutablePaths; `python --version` |
| F-27 | Local brain backend live (ollama 11434 + llama-server 1495 --offline since 23:41); external provider keys present, unused by audit | VERIFIED_LIVE | T0 | 0.95 | INFO | process snapshot |
| F-28 | `_octopus` legacy control-plane mostly stale since 07-18 BUT approvals still landing today (12:35:57, risk=medium) | VERIFIED_LIVE | T0 | 0.90 | MEDIUM | `_octopus/logs/audit.log` tail; approvals.json mtime |
| F-29 | Three independent beat counters coexist (chrono 38511; heart-card 4163; board 601 @22:57) | VERIFIED_LIVE | T0 | 0.95 | LOW | ORGANISM-STATE.json; beat-state.json; board-status.txt |
| F-30 | Telegram channel live (long-poll T-8); notification sends NOT per-message approval-gated (audit-logged, STOP-gated) | VERIFIED_LIVE | T0+T2 | 0.88 | LOW | channel-status 23:51; `tg_api.py:489-534` (≈R-004) |
