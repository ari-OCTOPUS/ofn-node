# 02 FINDINGS — A01 Repository Cartographer (2026-08-16)

Status vocabulary: VERIFIED_LIVE / VERIFIED_CODE_ONLY / VERIFIED_TEST_ONLY /
DOCUMENTED_NOT_IMPLEMENTED / STALE / CONTRADICTED / NOT_FOUND / UNKNOWN.

---

## F-001 — Main organism runtime is live and identifiable
- **Claim**: OCTOPUS has a running main organism.
- **Status**: VERIFIED_LIVE
- **Evidence tier**: T0
- **Source**: Win32_Process query; `_ops/state/ORGANISM-STATE.json`
- **Detail**: `python -X utf8 organism.py`, PID 29028, started 2026-08-16T12:53:10; state file ts
  2026-08-16T23:49:11, beat 38507, started field matches PID creation. Port 8771.
- **Command**: `Get-CimInstance Win32_Process -Filter "name like '%python%'"`
- **Confidence**: 0.97 · **Severity**: INFO · **Contradiction**: none
- **Next**: A02 to sample `/api/organism` and observe tick progression.

## F-002 — Companion processes: cortex, live room, telegram center, board queue, miniapp gateway
- **Claim**: layered services run alongside the organism.
- **Status**: VERIFIED_LIVE (5 PIDs: 11144 cortex :8772, 7852 live :8773, 11724 tg-center, 23464
  board_cp, 19076 miniapp_gateway)
- **Tier**: T0 · **Source**: Win32_Process · **Confidence**: 0.95 · **Severity**: INFO
- **Contradiction**: none. **Next**: A02 verify each port answers.

## F-003 — Ten Windows scheduled tasks keep the organism supervised
- **Claim**: OS-level scheduling exists.
- **Status**: VERIFIED_LIVE — `OCTOPUS-Cortex-Watchdog`, `OCTOPUS-Live-Watchdog`, `OCTOPUS-MiniApp-Watchdog`,
  `OCTOPUS-TG-Center-Watchdog`, `OCTOPUS-Cockpit-Brain`, `OCTOPUS-Observatory`, `OCTOPUS Observatory Hourly`,
  `OCTOPUS-doctor-day`, `OCTOPUS 4d Consolidation Tick`, `OCTOPUS 4d Poisoning Watch` — all "Ready".
- **Tier**: T0 (`schtasks /query`) · **Confidence**: 0.95 · **Severity**: INFO · **Next**: A02 read task
  actions/paths to confirm they launch the watchdog ps1 scripts found on disk.

## F-004 — LIVE INCIDENT: organism running under budget FREEZE since 20:09
- **Claim**: (new finding) budget settle failure froze grants.
- **Status**: VERIFIED_LIVE
- **Tier**: T0 · **Source**: `_ops/budget/FREEZE.flag` content: "2026-08-16T20:09:05 settle failed for
  ARCHITECT_SYS: [Errno 22] Invalid argument: 'F:\backup\_ops\budget\budget-state.json'";
  live state shows `frozen: true`.
- **Command**: `cat _ops/budget/FREEZE.flag` · **Confidence**: 0.93
- **Severity**: HIGH — fail-closed behavior worked as designed, but the organism has been operating
  frozen for ~4h; the Errno 22 indicates a Windows file-handle/locking fault in settle path, not a
  governance decision.
- **Contradiction**: contradicts any claim of "budget settle healthy".
- **Next**: A02/A03 reproduce write contention on budget-state.json read-only (e.g., inspect locks);
  owner decision needed to clear freeze after root cause.

## F-005 — Claim "OCTOPUS has layers L0–L8"
- **Status**: CONTRADICTED (as stated) — the architecture SoT defines 7 layers (0–6 + S safety);
  no L0–L8 scheme exists in code or current docs.
- **Tier**: T2/T5 · **Source**: `_ops/ARCHITECTURE-LAYERS-2026-07-27.md` (incl. ERRATA 2026-08-12);
  repo-wide grep for L0–L8 found only one old fix-log mention.
- **Confidence**: 0.9 · **Severity**: MEDIUM (brief/lore mismatch) · **Next**: council adopts the
  7-layer vocabulary or owner redefines.

## F-006 — Claim "Brains are 4d_system and NBB-CP"
- **Status**: PARTIALLY VERIFIED — VERIFIED_CODE_ONLY for the *governance identity*:
  `_ops/control_plane/dual_brain.py` defines `BrainID.FOURD="fourd_system"` and `BrainID.NBB="nbb_cp"`.
  But at runtime tonight **neither runs as a brain process**: 4d_system has no process and is only an
  opt-in observed member of cortex (`OCTOPUS_OBSERVE_4D`, marked DEPRECATED-disconnected);
  NBB-CP exists only as code (3 copies). The live "think" lane is the cortex local 3-model router
  (ollama :11434).
- **Tier**: T2 + T0 · **Confidence**: 0.85 · **Severity**: MEDIUM · **Contradiction**: partial —
  claim names real governance brains but implies running brains.
- **Next**: A02 confirm whether any dual-brain evaluate() fires in live events.jsonl.

## F-007 — Claim "Governance is mutual veto"
- **Status**: VERIFIED_TEST_ONLY — `evaluate_veto()` logic (approve/approve→APPROVED; any veto→
  OWNER_DECISION; pending otherwise; consensus halt only) is implemented and proven by
  `_ops/tests/test_dual_brain_veto.py` (dated 2026-08-16 phase 6). Runtime side effects are gated
  behind `OCTOPUS_WIRE_DUAL_VETO`, which is **not set** in `.env` or `OCTOPUS-flags.cmd`.
  Verdicts are function parameters — no live caller observed producing them.
- **Tier**: T1/T2 · **Confidence**: 0.88 · **Severity**: MEDIUM · **Next**: owner decision — arm flag or
  document as dormant.

## F-008 — Claim "Actions are propose-only"
- **Status**: VERIFIED_LIVE for business legs — live state: lead `propose_only: true`,
  ziman `propose_only: true, outward_execution: false`, cartographer `read_only: true`,
  `proposals_emitted: 0`. Telegram center charter: only `propose_action` writes `_octopus/queue/pending`.
- **Tier**: T0 · **Confidence**: 0.9 · **Severity**: INFO · **Next**: A04 to try to find any
  non-propose effector path.

## F-009 — Claim "Money is locked and destructive actions disabled"
- **Status**: VERIFIED_LIVE (practice) + VERIFIED_CODE_ONLY (mechanism). `money_gate.py` is fail-closed:
  ≤AU$20 auto (hard floor locked by owner verdict 2026-07-07), above requires a valid approval from
  ApprovalChannel whose default implementation is `NotWiredStub` ⇒ deny-all above threshold.
  Live month spend: AU$0.74 / US$0.49. Destructive ladder: A6 FORBIDDEN always-REJECT;
  A2 currently BLOCK (VQ-SELFGOAL-002); A4/A5 "structurally pathless" per `action_bridge/integration.py:42`.
- **Tier**: T0+T2 · **Confidence**: 0.92 · **Severity**: INFO (positive control confirmed)
- **Next**: A04 adversarial check for spend paths that bypass money_gate.

## F-010 — Claim "A2 = bounded automatic; A4 = owner approval"
- **Status**: CONTRADICTED (semantics) — real ladder A0–A6 (`action_bridge/contracts.py`):
  A0 observe, A1 sandbox artifact, A2 internal-reversible **currently unlicensed/blocked**,
  A3 = owner-action vote cards, A4 = external effect (fail-closed, pathless now), A5 = money/contract,
  A6 forbidden.
- **Tier**: T2 · **Confidence**: 0.9 · **Severity**: LOW · **Next**: restate brief with A0–A6.

## F-011 — Claim "Policy Gate is runtime-enforced"
- **Status**: SPLIT — (a) `_ops/policy/policy_gate.py` ADR-033: executable, fail-closed, imported by
  live `wiring.py` and used by `talk_gate` ⇒ VERIFIED_CODE_ONLY (wired; live enforcement event not
  observed). (b) `4d_system/control_plane/policy.py`: pure data ladder, self-declared non-enforcing
  (v1) ⇒ DOCUMENTED_NOT_IMPLEMENTED as a gate. (c) `_ops/octopus_v3` P0 gate: complete, **WIRED=False**.
- **Tier**: T2 · **Confidence**: 0.87 · **Severity**: MEDIUM (three "policy" things; wrong one could be
  cited) · **Next**: A03/A04 name which policy_gate serves which surface.

## F-012 — Claim "Viability Loop is runtime-enforced"
- **Status**: NOT_FOUND as named. No `viability` symbol in any organism Python. Closest live analogues:
  allostatic heart (`heart/control_law.py`, `pulse_arbiter.py`), telemetry FREEZE-on-conflict (I3),
  `identity_health` in math_control. A `homeostasis.py` exists only inside unrelated
  `03 - Projects/research-spec-compiler/experiments/`.
- **Tier**: T2 (exhaustive grep) · **Confidence**: 0.85 · **Severity**: MEDIUM · **Next**: owner to
  rename claim or point to intended module.

## F-013 — Claim "ledger is live and bitemporal"
- **Status**: SPLIT — LIVE: VERIFIED_LIVE (11,444 records; last append 2026-08-16T13:44:24Z ≈ 23:44
  local; SHA-256 chained; cross-process append lock; torn-line tolerance). BITEMPORAL: CONTRADICTED —
  schema is append-only event log with single `ts` + monotonic `age_tick`/`is_human` (heart rule);
  no valid-time/system-time axes.
- **Tier**: T0+T2 · **Source**: ledger.py header v0.4.5/v0.4.6; ledger.jsonl tail · **Confidence**: 0.9
- **Severity**: LOW · **Next**: if bitemporality matters, it is a design gap, not a wiring gap.

## F-014 — Claim "Sensorium is active; legs are unauthorized"
- **Status**: NOT_FOUND for Sensorium (zero code matches; the sensing layer that exists is telemetry,
  C6 probes, afferent/, web research — Layer 1 "senses"). "Legs are unauthorized": the only "legs"
  on disk are **business venture legs** (lead/ziman/mining/crypto/cartographer + accounting modules);
  no physical-hardware leg control code found; mining/crypto legs are skeletons; so as phrased —
  NOT_FOUND/misframed.
- **Tier**: T2 · **Confidence**: 0.85 · **Severity**: MEDIUM (brief vocabulary drift)
- **Next**: owner clarify Sensorium referent.

## F-015 — Claim "Memory affects reasoning"
- **Status**: PARTIAL / VERIFIED_CODE_ONLY with known weakness — neural memory (hebbian/bcm/
  consolidation/latent_space) is wired and live state shows equations touching (#1 bcm, #2 hebbian);
  the architecture SoT itself calls Layer-2 the weakest layer ("mostly write-only" until recent
  read-back fixes). Deep-think now reads last 3 same-topic sessions.
- **Tier**: T2/T5/T0 · **Confidence**: 0.7 · **Severity**: MEDIUM · **Next**: A02 to trace one live
  recall path (recall_reach present in state: median 21 events).

## F-016 — Claim "identity_health is calculated live"
- **Status**: VERIFIED_LIVE — `math_control.identity_health = 0.542` in live ORGANISM-STATE
  (ts 23:49:11), with knob deltas and effects (`improve_rank_bias`, `schedule_bias_hint`).
- **Tier**: T0 · **Confidence**: 0.95 · **Severity**: INFO

## F-017 — Repository plurality & anomalies
- **Status**: VERIFIED_LIVE/CODE — enumerated: root repo (dirty 219); nested repo genome-system
  (own .git; files also tracked by root ⇒ repo-in-repo anomaly; 220 dirty); Desktop
  OCTOPUS-NBB-CP-WORKING (separate repo, active today, remote=bundle file in vault); 5 Claude
  worktrees; 2 orphaned archived worktrees; ~12 Desktop checkouts frozen at a3000f0.
- **Tier**: T0/T2 · **Confidence**: 0.95 · **Severity**: MEDIUM (operational risk, not a bug)
- **Next**: owner decision on canonical homes; see DUPLICATE_CANDIDATES.csv DUP-001/011.

## F-018 — NBB-CP triple fork divergence
- **Status**: VERIFIED_CODE_ONLY — three `nbb_cp` trees differ materially: vault copy has
  `adapters/legs` + `api/owner_gate.py`; 4d_system copy has `llm/fugu.py` + `adapters/vault`;
  Desktop copy has `adapters/observatory` (today's work). api/http.py & app/* differ in all three.
- **Tier**: T2 (`diff -rq`) · **Confidence**: 0.95 · **Severity**: HIGH for governance claims about
  "the" NBB brain — which fork is authoritative?
- **Next**: owner decision; A03 should test only the canonical fork.

## F-019 — octopus_v3 P0 overlay present but unwired
- **Status**: VERIFIED_CODE_ONLY — `WIRED=False` in `__init__.py`; gate.py docstring: "not wired into
  organism.py". Committed tonight (HEAD commit message).
- **Tier**: T2 · **Confidence**: 0.95 · **Severity**: INFO · **Next**: keep until owner vote.

## F-020 — Startup import surface
- **Status**: VERIFIED_CODE_ONLY — organism.py imports budget/* + wiring.py (4,347 lines) which lazily
  imports ~60 subsystems; cortex runs its own imports. 4d_system/nbb_cp/octopus_v3/genome-system code
  are NOT on the organism startup path.
- **Tier**: T2 · **Confidence**: 0.9 · **Severity**: INFO

## F-021 — Stale lore & broken launchers inside live tree
- **Status**: STALE — organism.py docstring references brain `app.py:8768` (no app.py on disk);
  `4d_system/start.bat` targets non-existent Desktop path; nbb-cp-kre README install path points to
  `F:\kre-out\…` while package lives in `4d_system/`.
- **Tier**: T2 · **Confidence**: 0.92 · **Severity**: LOW · **Next**: one-line fixes by a wired lane.

## F-022 — Prior test-execution evidence with recorded failures
- **Status**: VERIFIED_TEST_ONLY (cache artifacts, possibly stale) — `_ops/.pytest_cache` lastfailed:
  1 test (test_context_assembler fail-soft); root `.pytest_cache` lastfailed: 5 tests; caches dated
  Aug 5–6 (root cache dir touched 23:45 tonight). Not a fresh run.
- **Tier**: T1 · **Confidence**: 0.6 (staleness unknown) · **Severity**: MEDIUM · **Next**: fresh
  `pytest` run by a sanctioned lane (07_TEST_PLAN).

## F-023 — Static viz + extraction layer is decoupled from runtime
- **Status**: VERIFIED_CODE_ONLY — `OCTOPUS/` is static HTML (3D dashboards, 10 worlds,
  admin-telegram panels); `nervous-system/` extract_*.py feeds it; no runtime coupling to `_ops`.
- **Tier**: T2 · **Confidence**: 0.9 · **Severity**: INFO (naming confusion risk)

## F-024 — Board control-plane queue semantics
- **Status**: VERIFIED_CODE_ONLY — `board_cp/service.py`: tasks always land `RECEIVED` (owner_required);
  non-task kinds become `AUTHORIZED` only if armed.
- **Tier**: T2 · **Confidence**: 0.85 · **Severity**: INFO · **Next**: A04 verify `config.is_armed()`.

## F-025 — Cartographer leg's own map is stale
- **Status**: VERIFIED_LIVE (self-reported) — `map_age_days: 18, drift_files: 1143,
  refresh_recommended: true, mood 🔴`. (This agent's map supersedes it for tonight's council.)
- **Tier**: T0 · **Confidence**: 0.9 · **Severity**: LOW
