# 04 CONTRADICTIONS — A01 Repository Cartographer (2026-08-16)

Contradictions between the project-brief hypotheses and observed reality. Each entry: claim → evidence → resolution status.

## C-01 · "OCTOPUS has layers L0–L8"
- **Observed**: The architecture SoT (`_ops/ARCHITECTURE-LAYERS-2026-07-27.md`, with 2026-08-12 ERRATA) defines **7 layers: 0 Body, 1 Senses, 2 Memory, 3 Understanding, 4 Decision, 5 Action, 6 Interface, plus S Safety**. No code or current doc uses "L0–L8". The only "L0–L8" text found is in an old fix-run log (`_ops/OCTOPUS-FIX-START-CODEX-20260804-200015/*`).
- **Likely origin of claim**: conflation with the NBB-CP pytest tier markers `l0/l1/l2` (kernel/adapter/replay) and the 8-phase worker-agent directive notes in the knowledge base (`07 - Knowledge/شناسایی-اختاپوس/…62…`).
- **Verdict**: CONTRADICTED — vocabulary mismatch; council should adopt the 7-layer (0–6 + S) scheme.

## C-02 · "The ledger is live and bitemporal"
- **Observed**: Live = TRUE (11,444 records; last append 2026-08-16T13:44:24Z; SHA-256 hash chain; cross-process append lock; `age_tick` heart rule; `is_human`; torn-line tolerance). Bitemporal = FALSE under the standard meaning (valid-time vs system-time axes). The schema carries a single event `ts` plus a monotonic `age_tick` counter — two clocks, but no valid-time axis.
- **Verdict**: SPLIT — live confirmed; "bitemporal" CONTRADICTED unless the owner redefines it as "event-time + age counter". If true bitemporality is required (e.g., for retroactive corrections), it is a design gap.

## C-03 · "A2 actions are bounded automatic; A4 requires owner approval"
- **Observed**: Real ladder (`_ops/action_bridge/contracts.py`) is A0–A6: A0 observe-only; A1 sandbox artifact; A2 internal-reversible **currently unlicensed/BLOCKED** (VQ-SELFGOAL-002, `integration.py:42`); A3 = owner vote cards; A4 external effect, fail-closed but **"structurally pathless"**; A5 money/contract fail-closed; A6 always REJECTED.
- **Verdict**: CONTRADICTED as phrased — A2 is not running (it is blocked), and A4 does not "require approval" in the sense of an operational path; it has **no path at all** today. Only A3 produces owner-vote cards; A5 is the money gate (fail-closed via NotWiredStub).

## C-04 · "Brains are 4d_system and NBB-CP"
- **Observed**: `dual_brain.py` does name exactly these two as governance brains (BrainID.FOURD / BrainID.NBB) — but **neither runs tonight**. 4d_system has no process; cortex registry lists it as opt-in observer (`OCTOPUS_OBSERVE_4D`) marked DEPRECATED/disconnected. NBB-CP exists as code in three divergent copies, no process. The live cognitive lane is cortex's local 3-model router (ollama :11434).
- **Verdict**: PARTIAL CONTRADICTION — the governance *identity* is real; the runtime *presence* is not. Any claim that "the brains are actively reasoning today" is not supported.

## C-05 · "Governance is mutual veto"
- **Observed**: Logic implemented + tested (`test_dual_brain_veto.py`, 2026-08-16): both-approve → APPROVED; any veto → OWNER_DECISION; mixed-pending → PENDING; consensus required for halt. Side-effectful wiring is behind `OCTOPUS_WIRE_DUAL_VETO` which is **unset** in `.env` and `OCTOPUS-flags.cmd`. Verdicts are parameters — no live producer found.
- **Verdict**: VERIFIED_TEST_ONLY, runtime-dormant. Not a contradiction of code, but of any "live governance" reading.

## C-06 · "Sensorium is active"
- **Observed**: Zero Python matches for "sensorium" repo-wide. The sensing surface that exists is Layer-1: telemetry, C6 probes (12), afferent/, web research, inboxes — none named Sensorium.
- **Verdict**: NOT_FOUND — claim refers to something that does not exist under that name (or is documentary only).

## C-07 · "Viability Loop is runtime-enforced"
- **Observed**: Zero "viability" matches in organism Python. Closest real mechanisms: allostatic `heart/` (control_law, pulse_arbiter, work_pump), FREEZE-on-conflict (I3), `identity_health` math. A `homeostasis.py` exists only in the unrelated research-spec-compiler project.
- **Verdict**: DOCUMENTED_NOT_IMPLEMENTED (as named) — the function exists in spirit (homeostasis), not as a module/lane called "viability loop".

## C-08 · "Money is locked and destructive actions disabled"
- **Observed**: Consistent with the claim, but via different mechanisms than often described: money_gate fail-closed ≤AU$20 hard floor + NotWiredStub ⇒ above-threshold always denied; A6 forbidden; A2 blocked; live spend AU$0.74 this month; FREEZE incident further locks grants. **Caveat**: freeze is an *incident*, not a governance posture.
- **Verdict**: CONFIRMED with corrected mechanism — but the ongoing FREEZE (F-004) must not be cited as intentional lockdown.

## C-09 · "Memory affects reasoning"
- **Observed**: Memory writes are abundant; **read-back into reasoning is the documented weak point** (ARCHITECTURE-LAYERS Layer-2: "weakest layer, mostly write-only"; consolidation append-only without dedup/retract; recent read-back fixes for deep-think). Live `recall_reach` exists (90 events, median 21).
- **Verdict**: PARTIAL — code exists and is wired; actual influence on reasoning tonight is UNVERIFIED. Treat "memory affects reasoning" as a goal, not a proven property.

## C-10 · "Legs are unauthorized"
- **Observed**: The word "legs" maps to **business venture legs** (lead, ziman, mining, crypto, cartographer, accounting). Live state: lead/ziman propose-only with zero outward execution; mining/crypto skeletons; cartographer read-only. No physical-hardware leg controller found.
- **Verdict**: MISFRAMED rather than contradicted — "legs" exist and are effectively unauthorized (propose-only), but they are business legs, not actuators.

## C-11 · Policy Gate: "runtime-enforced"
- **Observed**: Three different things share the name: (a) `_ops/policy/policy_gate.py` (ADR-033) — executable, fail-closed, imported by live wiring.py and talk_gate (wired); (b) `4d_system/control_plane/policy.py` — pure data, self-declared non-enforcing; (c) `_ops/octopus_v3` P0 gate — complete but WIRED=False. Live enforcement of (a) was not observed as an event tonight (denial logs exist; see organ-gate-log.jsonl — not inspected for content).
- **Verdict**: PARTIAL — one of the three is wired; naming collision is itself a hazard.

## C-12 · "identity_health is calculated live"
- **Observed**: `identity_health = 0.542` in live ORGANISM-STATE (23:49:11) with equations touching #1-#17 and knob effects.
- **Verdict**: CONFIRMED (VERIFIED_LIVE) — no contradiction.
