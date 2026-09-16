# ADR-011 — Prospective memory: an explicit intention buffer that survives interruptions

- **Status:** Closed — machine verdict INTEGRATE (see §Verdict)
- **Date:** 2026-07-14
- **Spec:** `specs/prospective_memory.yaml` (EXP-005 / H-OWN-05, PASS 6/6) · env: `experiments/prospective_memory.py`
- **Decision rule (GO/NO-GO):** pm_advantage_highload < 0.10 → DISCARD · [0.10, 0.40) → OPTIMIZE · ≥ 0.40 → INTEGRATE

## Context

Long-horizon agency needs to hold a *deferred* intention — "when cue X later
fires, do Y" — across an ongoing task that competes for the same limited memory.
This is the classic prospective-memory dissociation: an interruption stream
overwrites the working store that a delayed intention would otherwise occupy, so
a purely reactive controller loses the pending intention under load. H-OWN-05
asks whether adding a **dedicated, non-overwritable intention buffer** buys
functional retention over a reactive shared-register controller — and, crucially,
whether that advantage is *interruption-driven* rather than a free structural gift.

Scope is C2/C3-flavored (deferred-intention agency) but the metric is functional
task completion ONLY. Forbidden interpretation: intention as felt volition /
phenomenology. Permitted: functional retention of a delayed goal binding.

## Decision — a deterministic PM environment + two hand-coded memory architectures

`experiments/prospective_memory.py` is a new deterministic environment (NO
learning, NO LLM — the manipulation is MEMORY ARCHITECTURE only, mirroring
`homeostasis.py`'s control-strategy contrast). Each episode is a token stream of
`enc` (encode a cue→resp binding), `ong` (ongoing interruption), and `trg`
(trigger — the scored PM event). Each intention's trigger is placed `gap` steps
after its encode; heavy load draws `gap∈[3,18]` (many exceed the register),
light load `gap∈[1,7]` (all fit). The response `resp` is a fresh per-intention
draw, so it **cannot be baked into a fixed policy or re-derived from the cue** —
it must be STORED. Both agents key the trigger on the *stored* binding; there is
no learned selection.

Two agents step the identical stream:
- **reactive** (= no intention buffer): a single SHARED FIFO register of capacity
  K=8 [FACT: code constant]. Every salient token — ongoing item, binding,
  trigger — is pushed, so interruptions evict pending bindings. At a trigger it
  searches the surviving register; if the binding is gone it emits a deterministic
  fallback guess over R=4 responses (chance floor 1/R = 0.25 [FACT: code]). This
  is a strong, non-strawman baseline: perfect under light load, ~1/R once the
  binding is evicted.
- **buffer** (= explicit prospective memory): a SEPARATE dedicated store of
  capacity P=6 [FACT: code constant] holding (cue→resp), never touched by ongoing
  items; at a trigger it reads the store, else emits the SAME fallback guess.

Because both agents emit the identical guess when they lack the binding, triggers
where both lack it cancel — the primary is purely the differential value of a
dedicated, non-overwritable store. Parameters were set on pilot family 982000
(advantage ≈ 0.48 [FACT: pilot log 2026-07-14]), then FROZEN; the confirmatory
run uses a disjoint family (982600+). Primary metric:
`pm_advantage_highload = PM_completion(buffer) − PM_completion(reactive)`,
micro-averaged over all trigger events (8 intentions × 60 episodes ≈ 480 events
per seed [FACT: code constants]), across 5 seeds.

## Confirmed caveats (adversarial review, 2026-07-14)

Three findings were confirmed and recorded transparently; none reverses the
verdict, but each bounds what it means. Fixes were applied to the spec/experiment
prose (see below).

1. **The buffer's *capacity* is never the binding constraint under high load —
   this is a buffer-vs-no-buffer result, not a capacity-pressure result.** The
   buffer completes **1.0** under heavy load [FACT: confirmatory smoke 982600+],
   so its FIFO capacity P=6 never evicts a needed binding in practice. The entire
   0.475 advantage comes from the reactive register *dropping* (1.0 → 0.5254),
   not from the buffer being stressed. The design tension the spec advertises
   ("P<K can flip the advantage negative") is *latent* here, not exercised —
   P=6<K=8 alone is insufficient to make the buffer lose, because the staggered
   encode schedule keeps ≤P intentions simultaneously pending. **Disclosed** in
   the docstring, the `failure_condition.note`, and here.

2. **`null_control = 0` holds BY CONSTRUCTION, not by measurement.** In the null
   regime `make_episode` places encodes but no triggers, so `pm_total = 0` and
   `_batch_rates` returns `(0.0, 0.0)` from its `n_tot == 0` guard — no PM event
   is ever scored. It pins the zero-point definitionally; it is *not* evidence of
   a measured cancellation. **Corrected** in the `prediction.baseline` comment and
   the docstring (previously it read as an empirical "= exactly 0").

3. **`low_load_advantage ≈ 0` is the discriminating control that makes the result
   non-trivial — and it is a *measured* zero.** Under light load reactive = 1.0
   and buffer = 1.0, advantage **0.000** [FACT: confirmatory smoke 982600+]: the
   shared register survives when gaps fit within K, so the buffer buys nothing
   for free. This is what distinguishes "the buffer helps under interruptions"
   from "the buffer trivially helps." Unlike null (true by construction), low_load
   *could* have been positive and was not. **Highlighted** in the docstring and
   the Verdict below as the load-sensitive control.

## Scope guard (locked)

C0–C3 only. The metric is functional deferred-intention completion; the C0⇏C4
line (phenomenal / qualia / felt volition / sentience) is never crossed. "Prospective
memory" here names a functional retention mechanism, not experienced intention.
The buffer's extra persistent state (space/compute the reactive agent does not
carry) is a declared cost, per house discipline.

## Verdict

**INTEGRATE** — `python rsc.py run prospective_memory`, confirmatory family
982600+, 5 seeds × 60 episodes, 2026-07-14. All numbers [FACT: run log / smoke]:

| condition | advantage (mean) | std | reactive | buffer | role |
|---|---|---|---|---|---|
| **pm_advantage_highload** (primary) | **0.475** | 0.022 | 0.5254 | 1.0 | gated |
| low_load_advantage | 0.000 | 0.000 | 1.0 | 1.0 | control (measured) |
| null_control | 0.000 | 0.000 | 0.0 | 0.0 | zero-point (by construction) |

- pm_advantage_highload 0.475 ≥ 0.40 → failure_condition (`< 0.10`) not
  triggered; lands in the INTEGRATE band → **INTEGRATE**.
- **Honest reading:** under interruption-heavy episodes an explicit intention
  buffer completes deferred intentions ~0.475 more often than a reactive
  shared-register agent — a large, real functional gain. But read it precisely:
  the buffer is at ceiling (1.0), so the effect is *reactive degradation under
  interruptions*, not buffer capacity headroom. The claim earned is **"a
  dedicated non-overwritable intention store beats a shared register under
  interruption load"**, established by the low_load control (measured 0.000: no
  advantage when the register survives) rather than by the null control (0.000 by
  construction). The advertised P<K sign-flip tension is genuine in the mechanism
  but was not reached in this run — a stronger test would raise intention density
  above P to force buffer eviction and confirm the kill line is approachable.
