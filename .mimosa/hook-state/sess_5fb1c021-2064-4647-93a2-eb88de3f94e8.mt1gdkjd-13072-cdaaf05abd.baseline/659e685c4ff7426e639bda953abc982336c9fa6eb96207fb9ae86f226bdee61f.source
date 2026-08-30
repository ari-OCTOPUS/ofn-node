# C6 — FIRST IGNITION: Governed Self-Improvement Run (2026-07-23→24)

> Mission: first REAL research mission through the C6 governed harness. Sense a real
> bottleneck → sandbox an experiment → grade it through the governed loop → produce an
> **owner-gated proposal**. Proposal-only. Zero merge / deploy / external effect.
> Branch `claude/c6-self-improvement-ignition-c73186` · all work under `_sandbox/evolution_v1/` (untracked).

Label note: the owner's kickoff header said "C8"; the body, harness, and prior commits call
this **C6**. This is the C6 harness's first live mission run (its report's "Honest status"
said the harness was proven but had never run a real mission — that gap is now closed).

---

## Phase 1 — SENSE & DIAGNOSE (empirical, not eyeballed)

**Vitals (live tree, read-only):** `STOP-METABOLIC`, `HALT-ALL`, `STOP-ORGANISM`, `FREEZE`, architect `STOP` — all **absent**. Organism not in metabolic death or panic. FTS5 **available** (sqlite 3.50.4, py 3.13.7) → the real search path is exercised.

**Target — an N+1 query in the recall hot path.** `MemoryStore.search()` (`_ops/memory/memory_store.py:138-179`) gets candidate ids from FTS5, then **issues a separate SQL round-trip per candidate** to hydrate each row (`for mid, score in ids:` at :163). Every recall = `1 + max(k*4,20)` queries.

**Decomposed profile (`profile_search.py`):** the N+1 hydration is a ~constant ~0.19 ms (20 point-lookups) regardless of corpus size; batching those into one query is 2.5× faster on that sub-step. **Hypothesis:** batch the per-candidate hydration into one `IN(...)` query → faster recall, **byte-identical results**.

---

## Phase 2 — THE DREAM STATE (sandbox A/B)

Candidate = final minimal patch `proposed_final.patch` (**+15/−3 lines, `search()` only**, comments preserved, applies with `git apply`): replace the N+1 loop with one batched `IN(...)` query, then keep the original FTS candidate order for ranking/tie-breaks → **byte-identical**.

**Correctness (hard gate).** One corpus DB opened by BOTH baseline and candidate → identical rows/ids; any difference is purely the algorithm.
- Governed evidence (`result.json`): main n=5000 + held-out n=3000 → **1,440 checks, 0 mismatches**.
- Additional edge/patch batteries (`verify_edges.py` 1,920 + `make_patch.py` 1,800): FTS **and** LIKE-fallback, k∈{1,5,20,300}, empty/whitespace/no-match/special-char/Persian-unicode/stopword, all filters → **0 mismatches**.
- Adversarial lens built a hand-crafted corpus (duplicate FTS ids, expiry boundary, salience=None, forced ties) → still **0 mismatches**.
- **Grand total ≈ 5,160 checks, 0 mismatches** (1,440 fed to the governed loop; the rest separate verification).

**Mechanism (exact, hardware-independent):** instrumented `execute()` per single search: **baseline 21 → opt 2** (1 FTS + 20 point-queries → 1 FTS + 1 batched) = **10.5× fewer SQL round-trips**. This is the durable claim; latency % is its hardware-dependent consequence.

**Latency — measured honestly, corrected twice.** This was noisy sub-ms timing and the number was wrong before every confound was controlled:

| measurement | n=5000 | why it was wrong |
|---|---|---|
| naive A/B (baseline-first) | 25.9% | inflated — 2nd-run warm cache |
| paired, opt always 2nd | 9.7% | deflated — GC pauses hit opt's timing |
| GC-off single-stream | 33.6% | **still inflated** — timed base/opt on *disjoint* unequal-cost query subsets (caught by adversarial verify) |
| **symmetric paired (authoritative)** | **~24%** | same query both variants, lead alternated, GC off; median≈mean |

Authoritative corrected (`measure_paired.py`): **n=1000 → ~39%, n=3000 → ~29%, n=5000 → ~24%** (median across sizes **~29%**, speedup 1.31×–1.63×). Gain shrinks as corpus grows (FTS cost grows; N+1 saving ~constant) — physically sensible.

**Honest headline:** **~24% faster recall at a 5,000-memory store (~29% median, up to ~39% smaller), never slower, byte-identical**, anchored by the exact **10.5× round-trip reduction**.

---

## Phase 3 — DURABLE LEARNING (governed loop)

`governed_run.py` drove `research_loop.run_experiment` on the corrected `result.json`, fully sandboxed (`_sandbox/evolution_v1/governed_state_final`, never live state).

- **Verdict: `accepted`** — `verified + held-out + U=0.0103`.
- benchmark_gain **0.235** (conservative n=5000 floor); risk 0.05; cost **0.0** ($0 offline); maintenance_debt 0.05.
- **Self-calibration:** predicted 0.11 (Phase-1 lower bound) vs measured 0.235 → error 0.125, **not overconfident** (under-prediction), uncertainty 0.125 → `U = 0.235 − 0.05 − 0.05 − 0.125 = 0.0103`. Honest, thin margin; overconfidence would have quarantined it.
- DecisionReceipt `dr_438828d0…`; research ledger (1 accepted entry); durable `research-journal.jsonl`; memory `mem_3bc32aa7…` admitted **only via the C3 learning_gate**.
- **No auto-apply, proven:** `propose_only_apply_guard("merge_or_deploy") → permitted:False`.

---

## Adversarial verification — 5 independent skeptic lenses

| lens | verdict | outcome |
|---|---|---|
| correctness-completeness | ✅ confirmed (low) | byte-identical even on adversarial hand-crafted corpus; caveats: IN() 999-param limit on SQLite<3.32 (not this engine), single clock-snapshot (arguably *more* correct) |
| **measurement-validity** | ❌ **refuted (medium)** | caught the disjoint-subset artifact; forced the latency correction 33.6% → **~24%** (n=5000). Mechanism + correctness untouched. |
| isolation-safety | ✅ confirmed (low) | re-ran governed_run; live genome-ledger leak_hits still 0; only `_sandbox/` touched; the live-state files advancing are the *concurrently running organism* (governor/debate), provably not this experiment |
| patch-fidelity | ✅ confirmed (low) | patch == benchmarked code (600-check A/B); caveats fixed → final patch preserves comments + LF (`git apply` clean) |
| governance-honesty | ✅ confirmed (low) | U=0.01 not gamed — discretionary inputs chosen *against* self-interest; honest under-prediction nearly quarantined it |

The one refutation improved the result: the inflated 33.6% never reached the owner as a headline — the anti-self-deception pass corrected it to the honest ~24% first.

**Known limitations (disclosed, not hidden):**
1. Latency % is hardware-specific (owner's Windows box, sub-ms regime); the 10.5× round-trip reduction and byte-identical correctness are not.
2. Acceptance margin is thin (U=0.01, just above the quarantine cliff) — appropriate for a modest optimization, not a strong mandate.
3. The governed loop trusts the caller-injected verifier/held-out dicts; here they were honest, but the loop does not re-derive them (design note for future hardening).
4. IN()-batching adds a latent 999-param ceiling on SQLite<3.32 — irrelevant to this engine (32766) and the k=5 workload (21 params); the patch documents it.

---

## Safety ledger
- Live tree untouched: worktree `git status` = only `_sandbox/` (untracked). No writes to `F:/backup/_ops/state`; live genome-ledger leak_hits = 0 (independently re-checked).
- Budget: **offline, $0 cortex** (no LLM calls) — under the $0.10 cap.
- Metabolic: `STOP-METABOLIC` absent before and after.
- Rollback: delete `_sandbox/evolution_v1/` — nothing else changed.

## VERDICT
First genuine C6 mission complete. Bottleneck found → sandboxed → measured honestly (with a self-caught correction) → governed-accepted at ~24% recall speedup / 10.5× fewer SQL round-trips / byte-identical → **owner-gated proposal only**. Applying `proposed_final.patch` is the owner's decision and would still route through the human-append merge lane.
