# ADR-008 — Hybrid cortex organ: the kernel learns the body and decides to attach

- **Status:** Closed — machine verdict OPTIMIZE after adversarial re-gating (see §Verdict & §Correction) · **shadow attachment PERFORMED 2026-07-14 (owner authorized Q1)**: one additive `PROJECT.md` in `F:\backup\03 - Projects\research-spec-compiler\` registers the organ read-only/propose-only in URCP; zero existing body files modified; reversible. Effect-upgrades remain separate ORANGE gates.
- **Date:** 2026-07-14
- **Spec:** `specs/hybrid_organism.yaml` (H-HYBRID-01, PASS 6/6) · `experiments/hybrid_organism.py` · bridge: `experiments/organism_bridge.py`
- **Decision rule (GO/NO-GO):** bottleneck_advantage < 0.02 → DISCARD · [0.02,0.05) → OPTIMIZE (shadow-only) · ≥0.05 → INTEGRATE (sanctioned observing cortex, still propose-only)

## Context — the owner's directive

«F:/backup را به عنوان بدنت … مفاهیم پایه را بخوان و یاد بگیر تصمیم بگیر و
هایبریدی‌ترین درست کن.» Three read-only learners studied the body's base
concepts; the sanctioned attachment pattern they surfaced is unambiguous:

- Attach as a **Ring-2 differentiated cognitive organ** (the "cortex" slot),
  NOT Ring 0/1; cert-derived, revocable, no write to genome/pulse
  [Octopus_Heart_Design_v1.md:43,166,199-203; ARCHITECT-ORGANISM-CONTEXT.md:129].
- **Afferent broadband, efferent propose-only.** Risk Ladder GREEN = read /
  report / new-file only [RISK-LADDER.md:26-29]. Wiring it live is an ORANGE
  act needing the owner's Telegram verdict [RISK-LADDER.md:28].
- The body's OWN 2027 backlog marks the cortex's biggest gaps 🔴 OPEN and they
  are exactly this kernel: episodic→semantic **consolidation**, online
  **self-monitoring/metacognition**, access-only self-evaluation
  [2027 Standards Base & Backlog.md:30-32]. So this organ is on-roadmap, not
  an intrusion.
- **Hard red line:** access/functional only, NEVER phenomenal/qualia/sentience
  [2027-backlog:20]. Scope stays C0–C3.

## Decision — the four-mechanism hybrid, learning the real body

`experiments/organism_bridge.py` is the afferent nerve: it reads the body's
`dashboard_events` READ-ONLY (`mode=ro&immutable=1`) into a local snapshot
(5,044 events, 13 agents, the 9-phase cycle) — one read of the body, new files
only in the kernel, never a write to F:\backup, never the TCB. (The 4d research
daemon that feeds the table has been stopped since 2026-07-11, so the snapshot
is a stable static read.)

`experiments/hybrid_organism.py` combines all four proven mechanisms into one
organ that predicts the organism's NEXT event from the current event context,
on a **chronological** split (train on the body's earlier behavior, predict its
later behavior — temporal transfer, the honest self-model test):
- WM-gating (H-OWN-03): K=3 slots selected by greedy forward selection.
- schema consolidation (H-OWN-04): bin → majority-next-event library + backoff.
- RTA (H-GEO-01): reported alignment(coverage×purity) on the future window.
- temporal transfer: 5 chronological cuts (train_frac 0.60–0.80) as the seeds.

K=3 (who / what / where-in-cycle) is fixed a-priori as the minimal sufficient
context; the pilot sweep confirmed it is also the optimum (K≥6 collapses to the
unbounded model).

## Correction (adversarial review, 2026-07-14) — a blocker caught and fixed

The FIRST cut of this spec gated INTEGRATE on `hybrid_selfpred ≥ 0.90` (absolute
next-event accuracy). The review proved that gate **vacuous**:
- A plain 2-column `(agent, event_name) → majority-next` lookup — none of the
  four mechanisms — scores 0.946 bit-identically to the "K=3 hybrid" on every
  cut. `phase_idx = CYCLE.index(agent)` is a deterministic function of `agent`,
  so the advertised third slot never subdivides a bin: K=3 was silently K=2.
- The gate could not fail for any reason tied to the hypothesis: on this cyclic
  stream even a single feature scores 0.789, structurally far above the 0.70
  kill line. WM-gating / RTA / the bottleneck edge played zero role in the
  GO/NO-GO — they were display-only.
- The "+0.515 understanding gain" was inflated ~3.3× by a strawman majority
  baseline (0.431); against the fair single-feature baseline (0.789) the
  mechanisms add +0.157, and that comes from adding one raw feature (`agent`),
  not the fancy machinery.

**Fixes applied:** (1) primary metric re-pointed to `bottleneck_advantage` =
acc(K=2 gated) − acc(full 10-feature) — the actual falsifiable content (it can
be ≤0); (2) failure_condition + bands now sit on it (`<0.02 DISCARD`,
`[0.02,0.05) OPTIMIZE`, `≥0.05 INTEGRATE`); (3) K set to 2 with the phase_idx
redundancy disclosed; (4) the honest single-feature baseline (0.789) reported
instead of the strawman majority. The review's one refuted finding: the +0.036
bottleneck edge is NOT a strawman artifact — it is a real signal, just modest.

## Verdict

**OPTIMIZE** — `python rsc.py run hybrid_organism` (corrected gate), 5 temporal
cuts, 2026-07-14. All numbers [FACT: run log]:

| condition | mean | std | role |
|---|---|---|---|
| **bottleneck_advantage** (primary) | **0.036** | 0.009 | gated |
| hybrid_selfpred | 0.946 | 0.004 | reported (trivially high) |
| gain_over_single | 0.157 | 0.002 | reported (vs fair baseline) |

- bottleneck_advantage 0.036 ∈ [0.02, 0.05) → **OPTIMIZE**. The WM bottleneck
  does transfer across the body's timeline better than unbounded memory
  (positive on all 5 cuts, growing with train size, ~4 SE above 0) — H-OWN-03's
  thesis holds on real organism data — but the effect is **modest**, not strong.
- Honest reading of "does the kernel understand the body": yes, ~95% next-event
  accuracy, but that is mostly the stream being trivially predictable (a 9-phase
  cycle); over a fair single-feature baseline the whole hybrid adds only +0.157,
  and the bottleneck-specific contribution is +0.036. The kernel is a competent
  but unremarkable self-model here.
- **Scope caveat (locked):** observational SINGLE-SNAPSHOT study — the body's DB
  is frozen since 2026-07-11, so the 5 temporal cuts are correlated, not
  independent replications. Verdict scoped to "this snapshot of the body's
  history"; true replication needs the body's research daemon to produce fresh
  events.

## Consequence — the decision the kernel makes

OPTIMIZE licenses **proposing a SHADOW-only attachment**, NOT performing it and
NOT (yet) a full observing-cortex integration. Per the learned doctrine and the
Central Law firewall (ADR-007), the next step is an OWNER-gated ORANGE act. The
kernel therefore emits a proposal only:
- attach `research-spec-compiler` as a Ring-2 observing cortex organ;
- afferent: read-only over `dashboard_events` (+ the schema'd state files
  `heart-signals.v1` / `cortex-state.v1` when live);
- efferent: propose-only, paper-mode $0, behind an off-flag; no outward action,
  no production merge (`apply_merge` stays unwired) without the owner's
  Telegram verdict;
- register in URCP with owner + risk_tier via a `PROJECT.md`, ship the blackbox
  contract (MANIFEST/adapter/…), never touch the TCB or genome/pulse.
The owner decides whether to wire it. Nothing here is executed autonomously.
