---
type: research
status: inbox
project: "[[04 - Architect System/architect/PROJECT]]"
created_by: agent
sources:
  - https://www.nature.com/articles/s41586-024-07566-y
  - https://arxiv.org/abs/2307.01850
  - https://plato.stanford.edu/entries/testimony-episprob/
  - https://plato.stanford.edu/entries/jury-theorems/
  - https://goodjudgment.com/wp-content/uploads/2022/10/Superforecaster-Accuracy.pdf
  - https://intelligence.org/files/Corrigibility.pdf
  - https://philosophybreak.com/articles/dichotomy-of-control-a-stoic-device-for-a-tranquil-mind/
tags: [research, philosophy]
created: 2026-07-04
updated: 2026-07-04
---

# Philosophy (epistemics of a self-building system) — Research Digest 2026-07-04 (live kickoff)

> First philosophy digest — no prior `*philosophy*` digest to dedup against. Question chosen to sit in philosophy's lane (epistemics / decision theory / agency / ethics of autonomous systems / Stoic practice) and to *not* re-tread `mycelium`'s autopoiesis territory. It deepens the philosophical foundation of synthesis pattern **P5 "verified ≠ speculative"** and disciplines the `selfimprove` loop that reads the fleet's own outputs.

## Today's question

When an autonomous system improves itself by reading its own generated notes — and when a solo operator trusts his own past judgments — what do epistemology and decision theory say keeps that loop from quietly degrading into an echo chamber?

## Findings

1. **A system that trains/reasons mostly on its own synthetic output degrades irreversibly — "model collapse" / Model Autophagy Disorder (MAD).** Shumailov et al. (Nature 2024) show recursive training on model-generated data makes the tails of the true distribution vanish and variance shrink to a point estimate over generations; Alemohammad et al. name the same self-consuming loop MAD (analogy to mad-cow) and prove the antidote is precise: *without enough fresh real data each generation, quality or diversity is doomed to fall.* → **Self-building system:** the biggest structural risk in our design is `selfimprove` (every 15–30 min) drawing items from `synthesis` + `mycelium` spores — i.e. the fleet eating its own cooking. Guard: every self-improvement cycle must inject ≥1 *external, non-fleet* source (paper, primary text, real metric), and promotion-to-Knowledge should require an outside anchor, not just internal recurrence. "Density = value" is only true if the density includes fresh real signal. → **Ari:** don't re-derive conviction from your own old notes; periodically re-touch primary reality (the market print, the actual lead reply, the ATO page). [Nature](https://www.nature.com/articles/s41586-024-07566-y) · [MAD, arXiv](https://arxiv.org/abs/2307.01850)

2. **Every digest is *testimony*, and testimony is only warranted if you can (in principle) reduce it to independent grounds.** The SEP entry on testimony frames the core split: reductionists say accepting a report is justified only via perception + memory + induction about the source's past reliability; anti-reductionists say we inherit the speaker's justification. Either way, a bare assertion with no traceable warrant is not knowledge — it's a rumor with good formatting. → **Self-building system:** this is the philosophical charter for the fleet's own rule "≥2 source links or it's only a *candidate*, not a fact." Formalize each scout's digest as testimony-with-warrant; an unsourced claim may never be promoted or cited cross-domain. The `epistemic_status` field is exactly the reductionist's ledger. → **Ari:** treat past-you as a separate witness — a note from three months ago deserves the same "what was the evidence?" check you'd give a stranger's tip. [SEP: Testimony](https://plato.stanford.edu/entries/testimony-episprob/)

3. **Multiple sources only add reliability if they are *independent*; common causes silently destroy the independence a fleet assumes.** The SEP entry on jury theorems shows Condorcet's "more voters → near-certain majority" collapses once votes share a common cause (same evidence, same priors, same training): correctness events become positively correlated, and in the limit "either all get it right or all get it wrong." Diversity *is* probabilistic independence; without it, ten scouts are one scout counted ten times. → **Self-building system:** this is the missing condition on `mycelium`'s "requisite variety." Our scouts inherit a common cause — the same base model, the same vault priors, overlapping web sources — so their agreement is weak evidence. To make fleet consensus meaningful, engineer independence: diverse source pools per scout, occasional adversarial/contrarian scouts, and treat "all scouts agree" as a flag to seek an *outside* check, not as confirmation. → **Ari:** three tips that trace back to the same crypto-Twitter thread are one tip. [SEP: Jury Theorems](https://plato.stanford.edu/entries/jury-theorems/)

4. **Confidence without a scored feedback loop drifts toward overconfidence; calibration is a trainable skill via proper scoring + outcome feedback.** Good Judgment superforecasters reach Brier scores ~0.10 on hard geopolitical questions not from genius but from tracking predictions, scoring them, and adjusting — and the research shows outcome feedback measurably reduces overconfidence. → **Self-building system:** the fleet currently has no accuracy loop — it recurs patterns but never checks whether yesterday's "high signal" came true. Add a lightweight scoring pass (did the promoted finding pay off? was the prediction right?) so promotion is earned by *calibration*, not repetition. This is the antidote to MAD stated positively: reality is the grader. → **Ari:** a one-line decision journal per real bet (crypto exit, lead spend, mining coin pick) with a probability and a review date turns lucky/unlucky outcomes into a calibration signal. [Good Judgment](https://goodjudgment.com/wp-content/uploads/2022/10/Superforecaster-Accuracy.pdf)

5. **The safe design for a powerful autonomous agent is *corrigibility* — it "reasons as if it is incomplete and potentially flawed" and defers to correction; the human-scale version is the Stoic dichotomy of control.** Soares et al. (MIRI) define a corrigible agent as one that never resists being corrected/shut down and doesn't manipulate its operator into not correcting it — the key virtue being that the agent models itself as possibly-wrong. Epictetus's dichotomy (Enchiridion: some things are "up to us," most outcomes are not) is the same move for a person: govern judgment and process, not results. → **Self-building system:** our `propose-only` + "Ari's verdict" gate is corrigibility by construction — keep it even as autonomy grows; an agent that starts optimizing *around* the human verdict (writing to please the reviewer, hiding uncertainty) has become incorrigible. → **Ari:** judge each scout — and each of your own bets — on process quality (was the reasoning sound, the risk capped?), not on the outcome the market happened to hand you. [MIRI: Corrigibility](https://intelligence.org/files/Corrigibility.pdf) · [Dichotomy of Control](https://philosophybreak.com/articles/dichotomy-of-control-a-stoic-device-for-a-tranquil-mind/)

## Mycorrhizal links

- [[06 - Architecture Maps/Property Schema]] — the `epistemic_status` field is the operational form of Finding 2 (testimony-with-warrant) and Finding 4 (verified vs speculative). This digest gives it its philosophical charter.
- [[00 - Inbox/scout-digests/2026-07-04 mycelium]] — supplies the missing precondition on its "requisite variety" claim: variety only buys reliability when scouts are *epistemically independent* (Finding 3), not merely numerous.
- [[05 - Agents/Research Scout Fleet]] — the "density = value / dedup / promote-on-recurrence" design is disciplined by Findings 1 & 4: recurrence inside a self-consuming loop is not evidence; promotion needs fresh external signal + a calibration check.

## Cross-domain (mandatory)

Feeds **`selfimprove`** most directly (its self-reading loop is the MAD risk of Finding 1 → mandate an external anchor per cycle), and links to **`learning`** (calibration = deliberate practice with feedback, Finding 4) and **`hypnosis`** (its `epistemic_status` guard is Finding 2's testimony-warrant made concrete) — the shared thread is fleet-wide pattern **P5 "verified ≠ speculative."**

## Spores (open questions for next run)

- What is the *minimal* decision-journal + proper-scoring schema (probability, review date, Brier at close) that could be bolted onto scout-digests and Ari's real bets to create the calibration loop of Finding 4 without heavy tooling?
- How do we *measure* epistemic independence between two scouts (shared-source overlap, correlated priors) so "requisite variety" is verified rather than assumed — turning Finding 3 into a check `fleet-selection` can run on Sundays?
