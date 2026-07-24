# C6 — CYCLE 3: In-Loop Prediction Pre-Registration Gate (2026-07-24)

> Third governed mission. Target chosen by **two independent adversarial verdicts** (cycles
> 1–2, governance-honesty lens both times): the research loop trusts caller-supplied
> predictions — peeking is structurally undetectable — and I personally hit the same hole
> (fabricated `registered_at`, run-1 prediction file postdating results). Cycle 3 = the
> immune system hardening its own immune system. Proposal-only; owner-gated.

## The mechanism

**Patch (`proposed_c3.patch`, +123/−2, additive & opt-in, legacy byte-compatible):**
- `preregister_prediction(state_dir, contract, capability, predicted, experiment_index)` —
  journals the prediction's sha256 **before** the experiment runs. The append-only journal
  writes its own timestamps; **line order is the only precedence evidence** — no
  caller-supplied clock strings (the exact failure mode from cycle 2).
- `verify_preregistration(...)` — re-derives (never trusts): recomputes the sha from the
  *claimed* prediction and demands, among preregister rows **of this experiment_index**,
  **exactly one distinct sha**, equal to the claimed one, at a line **before** the first
  `experiment/start` row of the same index. Fail-closed.
- `record_calibration(..., preregistration=)` — unverified ⇒ uncertainty=1.0.
- `run_experiment(..., preregistration={capability, predicted})` — **the loop itself**
  re-derives verification at acceptance time; calibration uncertainty can only *raise* the
  caller's uncertainty (max), and an unverified prediction ⇒ **quarantined**.

## Attack matrix (measured; single-shot clean state)

| scenario | baseline (live loop) | patched |
|---|---|---|
| **H** honest (preregistered 0.40, measured 0.42) | accepted, U=0.30 | accepted, **U=0.30 — byte-invariant** |
| **P** peeked (no registration; claims predicted=measured, unc=0) | **accepted** (undetected) | **quarantined** |
| **T** tampered (registered 0.10; later claims 0.42) | **accepted** (undetected) | **quarantined** |
| **S** sprayed (registered 5 predictions; claims the matching one) | **accepted** (undetected) | **quarantined** |
| **R** legit recalibration (new prediction at higher experiment_index — cycle-2 style) | accepted | **accepted** (binding does not break honest recalibration) |

**Baseline detection 0/3 → patched 3/3.** The spray class was found by my own pre-launch
red-teaming and pre-registered (`PREDICTION-C3b.json`, file-first) before being built/fixed.

## Pre-registration discipline — practiced on itself
Both predictions for this cycle were registered **file-first with no clock strings**
(`PREDICTION-C3.json`, `PREDICTION-C3b.json`; mtime = the timestamp — the cycle-2 lesson):
predicted detection 1.0 → measured 1.0; calibration error **0.0**.

## Governed verdict (judge = the live, un-patched loop)
- **`accepted` — U = 1.0 − 0.05 − 0.10 − 0.0 = 0.85**, the largest margin of any cycle —
  earned by an exact pre-registered prediction, not by optimism.
- `benchmark_gain` is defined in the contract as attack-detection-rate improvement (0→1.0).
- Held-out: **real decision-time re-run** of the full 10-scenario matrix under an unseen
  state tag — passed. Receipt `dr_4160c9d95102cbcc`; memory `mem_4e2eec61e7f9e918` via
  learning_gate; `merge_or_deploy` → permitted: False.

## Honest limits (disclosed)
1. **External pre-measurement**: if the measurement happens entirely outside
   `run_experiment` before the loop ever runs, journal ordering cannot see it. The gate
   binds the loop's own world; real C6 missions should run experiments inside the loop,
   where the ordering proof is airtight. Driver-style flows still gain tamper- and
   spray-evidence plus procedural ordering.
2. **Journal file tampering**: an attacker with filesystem write access to the journal can
   rewrite history; out of scope (filesystem trust), partially mitigated by C7's HMAC'd
   experiment artifacts.
3. This patch modifies the research loop itself ⇒ apply routes through the
   **owner-governed maintenance lane** (constitution: loop never edits its own criteria
   autonomously). It is strengthening-only: adds a quarantine path, removes nothing;
   legacy call-sites are byte-compatible.

## Verification status
- Full suite on live code (`67f1a71`) + patch: _pending → recorded below when complete._
- Independent adversarial lenses: _pending → recorded below._
