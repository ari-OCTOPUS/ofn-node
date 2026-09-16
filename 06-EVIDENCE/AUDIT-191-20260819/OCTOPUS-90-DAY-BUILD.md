# OCTOPUS-90-DAY-BUILD — capability path from audit evidence (2026-08-19 → 2026-11-17)

Rules: every phase has a **measurable capability**, an explicit **gate**, test, rollback, owner-decision requirement and stop condition. No agent/board/token expansion before evidence justifies it. Standing boundaries (boards no-contact, scheduler unchanged, shell disarmed, PROPOSE_ONLY, budget 30/24/1) hold throughout unless a phase's owner decision explicitly changes one.

## Phase 0 — Unblock Primary Scoring (Day 0–3)

**Capability**: first counted primary pair under a frozen protocol.
- Work: D-B judge contract to real 4/4 (strict JSON/single-char + one re-ask) · E2E fixture gate assertions · FX re-pin (owner, before each expiry) · V2 protocol freeze ratification (owner) · reservation re-arm as needed.
- Gate: E2E 4/4 with `judge_unreadable=0, baseline_failure=0` asserted by test; protocol label VERIFIED with non-null hash.
- Owner decisions: FX pin, freeze ratification, (optional) different-family judge.
- Stop condition: if 3 more E2E attempts fail 4/4 → escalate judge-provider decision to owner instead of iterating prompts.
- Rollback: fg_runner/harness revert; no TCB touched.

## Phase 1 — Complete the Primary + Confirmatory Sample (Day 3–14)

**Capability**: LIVE-4 primary verdict (pass or fail — both are success of the method).
- Work: run batches 1–2 (2×15) foreground in reservation windows; then batches 3–4 confirmatory if primary passed; publish the full report contract (valid_pairs, VOID reasons, provider availability, costs per pair/win, limitations).
- Gate: 30 valid pairs or documented exhaustion with VOID accounting; evaluator run for Brier/coverage; label transitions in registry.
- Owner decisions: none beyond FX pins (recurring ~daily until an owner-approved FX workflow exists).
- Stop: hard stop 24 AUD or 3 expired-FX days in a row → owner packet.

## Phase 2 — Honest-Receipts & Memory-Spine Completion (Day 5–21, parallel-safe)

**Capability**: every paid-path promise machine-enforced.
- Work: RCPT-1 (budget_before bug), RCPT-2 (paid_blocked read), FALLBACK-RCPT, RADAR wiring (or label downgrade), F3, `evidence_ref` column, deterministic writers populating confidence_source/method, hash-chain label-history.
- Gate: zero negative budget_after across ≥50 new receipts; a QUARANTINED-on-contradiction example in production; 0 new incomplete-metadata rows.
- Rollback: per-patch diffs + INC1-style rollback artifacts under 06-EVIDENCE.
- Owner decisions: none (all CORE-AUTO-DEBUG scope).

## Phase 3 — Close the Daemon Learning Loop (Day 14–35)

**Capability**: the 4d brain itself writes predictions that get scored.
- Work: wire hypothesis/prediction recording from daemon ticks into predictions.db (non-TCB); dedup-novelty gate stays; daemon predictions enter the same evaluator as Live runs (separate namespace); retire-or-wire decision executed for ConsolidationCycle 4d twin and the 18 orphan modules per owner votes.
- Gate: ≥ 20 daemon predictions with outcomes in 7 days; Brier computed per namespace.
- Owner decisions: wire-or-retire votes (Deep-Seams VOTE 1 pattern); math-TCB guard ceremony (VOTE A/B).
- Stop: if daemon predictions are 100% duplicates after wiring → hypothesis engine redesign packet, not force.

## Phase 4 — Reliability & World-Model Semantics (Day 30–55)

**Capability**: contradiction handling and expiry semantics live in the world model.
- Work: radar active on all writers; expired-label auto-downgrade verified end-to-end; TCB-launch wrapper discipline (relaunch daemon via OCTOPUS-flags.cmd wrapper, enforcement verified in live env); Windows-task launcher fixes (absolute python.exe); http.server 8765 disposition; INC-2 router-level fix.
- Gate: a live contradiction → QUARANTINE demo; daemon env shows OCTOPUS_TCB_MANIFEST_ENFORCE=1; zero FILE_NOT_FOUND tasks.
- Owner decisions: kill/adopt 8765; any TCB-adjacent change.

## Phase 5 — Sensorium Groundwork (Day 50–80) — PAPER ONLY until owner funds it

**Capability**: verified hardware inventory exists (nothing powered beyond current state).
- Work: physical inventory scheme (device ID/MAC/firmware/location/power/role/owner/risk/last-seen) filled for what exists; MQTT-vs-NATS decision memo with justification; 5–10 ESP32 sensor-only pilot contract drafted (telemetry contract, allowed commands, rollback); Orange Pi live-verification plan (SSH probes as owner-executed scripts, results into registry).
- Gate: inventory file with ≥1 verified entry beyond the laptop; pilot contract reviewed.
- Owner decisions: ALL hardware actions (contact, purchase, pilot start). None inferred.
- Stop: no board contact without explicit decision — hard rule.

## Phase 6 — Scale Only What Earned It (Day 75–90)

**Capability**: capacity follows demonstrated learning.
- Work: only if Phase 1 passed and Phase 3 produces scored daemon predictions — expand reservation caps, consider actuator pilot (Phase-5 contract), consider second provider family for judge independence.
- Gate: LEARNING_VERIFIED or a falsified claim with preserved evidence (both acceptable outcomes; the method is the asset).
- Owner decisions: budget raise, actuator pilot, any external effect.

## Cross-phase invariants (checked every phase)

Labels/NOW.md in sync (`render_now.py --check` green) · every promotion has diff+test+rollback+manifest · append-only history preserved · two agents agreeing never makes VERIFIED · VOID never becomes win/loss · spend ≤ caps with complete receipts · no scheduler/shell/board/external effects without explicit owner decision.

## Resourcing honesty

Total all-time LLM spend is $0.45 USD; a full Live-4 completion costs < $0.50 AUD at current unit costs. **Money is not the bottleneck.** The bottlenecks are: judge readability (technical), protocol freeze + FX pin (owner, minutes each), and wiring promises into code (engineering discipline).
