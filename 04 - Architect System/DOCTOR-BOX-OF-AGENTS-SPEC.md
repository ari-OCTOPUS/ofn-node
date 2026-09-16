---
type: proposal
project: "[[04 - Architect System/architect/PROJECT]]"
status: draft-for-verdict
created_by: agent
relates_to: "[[_ops/ORGANISM-SPEC]] §2.7 Doctor · [[07 - Knowledge/Time-Architecture/fusion-doctor-spectral-sense]] · _ops/doctor/doctor.py · _ops/debate/"
tags: [octopus, doctor, box-of-agents, inner-chamber, sandbox, spec, propose-only]
created: 2026-07-08
updated: 2026-07-08
---

# DOCTOR · BOX-OF-AGENTS — architecture + pseudo-math spec (no code yet)

> A closed, sandboxed micro-universe of agents inside the Doctor core. It ONLY talks to itself, has rich neural-like internal state, is hard-capped at 2% of Octopus energy, and emits propose-only hypotheses/metrics — never actions. This document is spec + roadmap only; no executable code.

---

## Part 0 — Assumptions & glossary

### 0.1 Assumptions about the larger Octopus
- **A0 (energy = token-time):** "energy" is measured primarily in **LLM tokens per unit wall-clock**, since that is the metered, capped resource in the live gateway (LiteLLM `max_budget`). Secondary meters (CPU%, wall-clock) map onto the same budget via fixed conversion constants set by the Warden. `[EST]`
- **A1:** the Doctor already exists (`_ops/doctor/doctor.py`: `mine`→bottleneck, RFC, Critic, `λ_persist<0`) and the debate pattern exists (`_ops/debate/`, muse×architect, ≤3 rounds). The Box is an **additive** upgrade of the Doctor's deliberation, not a rival. `[تثبیت‌شده]`
- **A2:** the Box reads a curated read-only config (seeds, topic list, embedding index) and Octopus global metrics; it can modify **nothing** canonical.
- **A3:** everything is shadow/paper (money locked to 2026-07-21). The Box never touches money/effectors.

### 0.2 Symbols
| symbol | meaning | implemented as |
|---|---|---|
| `A_i`, i=1..N | agent i | a role process |
| `x_t^i ∈ R^n` | neural/cognitive state of A_i at step t | **number** (vector) |
| `z_t^i = [s,v,f,c]` | psychological state: stress, vigilance, focus, coherence | **number** (∈[0,1]^4) |
| `M_t` | shared memory (list of (topic, summary, embedding, scores)) | **number/struct** |
| `G_t` | global "mood"/summary of the Box | **number** (aggregate of z, plus a text digest) |
| `φ_t` | global fusion field (optional; the `A=−L(G)` field from spectral-sense) | **number, stub-able** |
| `m_t^i` | message emitted by A_i | text or structured token |
| `E_total`, `E_box_max` | Octopus energy budget; Box hard cap = 0.02·E_total | **number** |

### 0.3 Metaphor vs. implemented (honesty line)
- **Directly implemented as numbers/algorithms:** `x, z, M, G, φ`, energy accounting, mutual-information estimates, the Jacobian/spectral-radius stability analysis, all update equations below.
- **Purely metaphorical (labels, NOT claims):** the words "stress / vigilance / focus / coherence / psychology / mood." These are names for control variables. **No claim of sentience, feeling, or welfare is made or implied.** (See Part 6, axis 5.) `[OPINION/ethics]`

---

## Part 1 — System boundary & energy budget

### 1.1 Boundary
- **IN (read-only):** config file(s), initial seeds, topic list, embedding index, Octopus global metrics snapshot.
- **INSIDE (never leaves):** all agent messages, internal logs, `x/z/M/G` states, learned parameters `θ`.
- **OUT (only):** (a) occasional **proposed-insight** text blobs, (b) internal **metric/telemetry summaries**, (c) **RFC candidates** to the Doctor's normal propose-only path. Never actions, never code patches, never external API calls, never secrets.
- Enforced by the **Warden** (Part 3) + OS sandbox: no tools, no outbound net, no writes outside the Box directory.

### 1.2 Energy, formally
- `E_box_max = 0.02 · E_total` (hard upper bound, fail-closed: when the Box's running debit ≥ E_box_max for the window, the Warden ends the cycle).
- Translation (Warden sets these from E_box_max):
  - `max_tokens_per_cycle = E_box_max / cycles_per_window`
  - `max_cycles_per_minute` = f(freshness need, budget)
  - `N_max` = ⌊(token budget per cycle) / (avg tokens per active-voice turn × turns per agent)⌋
  - `|M_t|_max` = fixed cap (e.g. K entries, embeddings quantized) — memory is bounded, oldest-lowest-score evicted.

### 1.3 Concrete numeric example
Take `E_total = 100,000 tokens/day` (user's example).
- `E_box_max = 2,000 tokens/day`.
- **Key design move:** the `x/z/M/G` dynamics are **cheap numeric** (≈0 tokens — plain vector math). LLM tokens are spent **only** when a voice must generate *text* (Dreamer/Skeptic/Integrator). So the 2% budget buys **reasoning quality**, not simulation ticks.
- Allocation example: reserve 1,600 tokens/day for LLM voices, 400 as safety margin.
  - If one debate episode = 4 text-turns × ~200 tokens = 800 tokens ⇒ **~2 full episodes/day** of LLM-backed deliberation, plus unlimited cheap numeric ticks between them.
  - `max_tokens_per_cycle ≈ 800`; `max_cycles_per_day ≈ 2` (LLM-backed); numeric-only micro-cycles run freely under a CPU sub-cap.
  - `N_max` (LLM-active concurrent) ≈ 3–4; numeric-only agents can be more (they're nearly free) but capped for stability.
- **Rule:** the moment projected debit would exceed E_box_max, Warden degrades to **numeric-only mode** (no LLM) — the Box keeps "thinking" cheaply, just without new text.

---

## Part 2 — Agent modeling: neural vs random

### 2.1 Two behavior classes
- **Neural-like:** `x_{t+1}^i = f_θ^i(x_t^i, u_t^i, M_t)`, `a_t^i ~ π_θ^i(a | x_t^i)`. State carries information across time; action depends on state.
- **Random/baseline:** `a_t^i ~ q_i(a | u_t^i, η_t)` — no real state dependence (or shallow Markov). A control/null model.

### 2.2 Formal criteria (information-theoretic)
- Compute **mutual information** `I(a_t ; x_t)` between an agent's actions and its own state:
  - `I(a;x) ≈ 0` ⇒ random-like. `I(a;x) ≫ 0` ⇒ neural-like.
- **Practical approximation from logs:** over a sliding window, discretize `a` (action/message class) and reduce `x` (e.g. PCA to few dims, then bin); estimate the joint histogram `p(a,x)` and marginals; `I = Σ p(a,x) log[p(a,x)/(p(a)p(x))]`. Cheap proxy when data is thin: **"neural-ness score"** = fraction of variance in `a` predictable from `x` by a tiny linear/logistic probe (held-out). Both are numeric, ≈0 tokens.
- The **Physiologist** logs `I(a;x)` per agent each episode; a neural agent whose `I` collapses toward 0 is flagged (degenerate/looping).

### 2.3 Which agents are neural vs random
- **Neural-like (state matters):** Dreamer, Skeptic, Integrator, Interrogator — their value is history- and pressure-dependent.
- **Random/baseline (control):** a small pool of **Noise agents** injecting `η_t` (novelty/perturbation), plus a **null-Dreamer** used as a scientific control to prove the neural Dreamer actually beats chance (compare RFC quality: neural vs null). Baselines make the Box **falsifiable about its own value.**

---

## Part 3 — Internal roles & roster

Each agent: name · mission · inputs · outputs · internal state · special constraint.

| agent | mission | inputs | outputs | state (x,z) | constraint |
|---|---|---|---|---|---|
| **Warden** | enforce policy + 2% energy cap + kill-switch | budget meter, all traces | allow/deny/degrade, cycle-end | none (deterministic) | supreme; obeys STOP unconditionally; cannot be argued with |
| **Archivist** | build/maintain `M_t` | messages | updated `M_t`, embeddings | small x | bounded memory; evict oldest-lowest-score |
| **Interrogator** | generate probing questions / cognitive pressure | topic, `M_t` | questions (raises `load`) | x,z | high curiosity; must not harass one agent (fairness cap) |
| **Dreamer** | propose new topics / mutations | seeds, `M_t`, `φ_t` | hypotheses | x,z | high novelty; paired with null-Dreamer control |
| **Skeptic** | challenge/falsify hypotheses | hypotheses | critiques + a concrete falsifier | x,z | **must attempt to break, never agree** (anti-AP-03) |
| **Integrator** | synthesize survivors → candidate RFC | survivors | RFC draft (propose-only) | x,z | may only synthesize what survived the Skeptic |
| **Physiologist** | track `z`, `I(a;x)`, `G_t`, stability `ρ(J)` | all states/logs | metrics/telemetry | none | read-only sensor; no voice in debate |
| **Judge** | score internal debates | debate transcript | internal scores | none | **no external authority**; score ≠ merge |

**Anti-agreement-spiral (structural):** the loop is **adversarial by construction** — the Skeptic's job is falsification, the Judge cannot merge, the Integrator can only pass what survived. A hypothesis with no surviving falsifier is **dropped**, not promoted.

### 3.2 Instances under 2%
With the example budget (~2 LLM episodes/day): **1 each** of Warden, Archivist, Physiologist, Judge (mostly numeric/cheap), and **1–2** each of the text-voices (Dreamer, Skeptic, Integrator, Interrogator) *active per episode*, chosen by the Warden. Numeric-only agents (Noise, null-Dreamer, Physiologist) run nearly free. Scale instance counts **linearly with E_total**; Warden recomputes `N_max` whenever the budget changes.

---

## Part 4 — Feedback mechanisms in a closed architecture

### 4.1 Core state variables
- Agent: `x_t^i ∈ R^n` (cognitive), `z_t^i = [s,v,f,c] ∈ [0,1]^4` (psychological).
- Shared: `M_t` (memory), `G_t` (global mood = aggregate of `{z^i}` + text digest).

### 4.2 Update rules (pseudo-math)
- Message: `m_t^i = g_θ^i(x_t^i, z_t^i, M_{t-1}, ξ_t^i)`
- Memory: `M_t = h(M_{t-1}, {m_t^i}_i)` (append + score + bounded evict)
- Cognitive: `x_{t+1}^i = f_θ^i(x_t^i, M_t)`
- Psychological: `z_{t+1}^i = u(z_t^i, load_t^i, recovery_t^i)` (Part 5)

### 4.3 Positive vs negative feedback
- **Negative (stabilizing):** recovery terms on `z`, memory eviction, the Skeptic (dampens over-confident hypotheses), Warden budget throttle. Encoded as negative-sign partials / contraction.
- **Positive (amplifying):** novelty→vigilance→exploration; a promising topic gets reinforced in `M_t`. Encoded as positive-sign partials.
- **Design invariant:** net dynamics must be **contractive on average** — positive loops are allowed only *transiently* and are always bounded by a stronger negative loop (Warden + Skeptic + recovery).

### 4.4 Discrete-time system (stability)
Stack `X_t = [x^1,z^1,…,x^N,z^N]`. Linearize around an operating point:
`X_{t+1} ≈ J · X_t + b + noise`, where `J = ∂(update)/∂X` is the Jacobian.
- **Stability criterion:** spectral radius `ρ(J) < 1` ⇒ bounded (no runaway). `ρ(J) ≥ 1` ⇒ Warden intervenes (throttle/reset).
- **Edge-of-criticality tuning (ties to the fusion/SOC work):** richest dynamics near `ρ(J) ≈ 0.9–0.98` — analogous to `σ≈1` in `Time-Architecture`. The **Physiologist estimates `ρ(J)`** from logs each episode; the **Warden keeps it in `[ρ_min, ρ_max]` with `ρ_max < 1` hard.** This is the mathematical anti-runaway guarantee.

---

## Part 5 — Stress & vigilance models

### 5.1 Psychological vector
`z_t^i = [s_t^i, v_t^i, f_t^i, c_t^i]ᵀ`, each ∈ [0,1]: stress, vigilance/arousal, focus, coherence.

### 5.2 Update equations (clip to [0,1])
- `s_{t+1} = clip(s_t + α_s·load_t − β_s·recovery_t)`
- `v_{t+1} = clip(v_t + α_v·novelty_t − β_v·v_t)`  (arousal decays without novelty)
- `f_{t+1} = clip(f_t + α_f·alignment_with_role − β_f·distraction_t)`
- `c_{t+1} = clip(c_t + α_c·internal_consistency − β_c·contradiction_t)`
where `load, novelty, alignment, distraction, consistency, contradiction ∈ [0,1]` are computed from the episode (e.g. `contradiction` from the Skeptic's hits; `novelty` from embedding-distance to `M_t`).

### 5.3 Coupling z → behavior (how state changes cognition)
- **Vigilance → exploration temperature:** `π` sampling temperature `T_i = T0·(1 + κ_v·v − κ_f·f)` — aroused/unfocused ⇒ more exploratory; focused ⇒ sharper.
- **Stress → threshold + narrowing:** high `s` raises the Judge's acceptance threshold and narrows the Dreamer's search (Yerkes–Dodson inverted-U, from `Time-Architecture/claims C3`): moderate `s` helps, extreme `s` degrades — the Physiologist watches for the down-slope.
- **Coherence → memory-write gate:** only messages with `c ≥ c_min` are written to `M_t` (low-coherence chatter is not persisted).

### 5.4 Homeostasis & allostatic load (safety, not objective)
- Recovery terms pull `z` back toward a baseline between episodes (homeostasis).
- **Allostatic load** `L_t = Σ s_τ` (integral of stress). If `L_t > L_max`, the **Warden forces a cooldown** (numeric-only, no LLM) until recovery.
- **CRITICAL safety inversion (axis 5):** stress is a **monitor, never a reward to minimize.** If "reduce stress" became an objective, the Box would avoid hard problems (reward-hacking / comfort-seeking). Objective = RFC quality that survives falsification; `z` only *modulates and protects*, it is never optimized. `λ_persist < 0` extends here: the Box gets **no reward for its own comfort or survival.**

---

## Part 6 — The five research axes (explicit)
1. **Neural vs random:** Part 2 — `I(a;x)`, neural-ness score, null-Dreamer control ⇒ the Box is falsifiable about its own value.
2. **Feedback in closed architectures:** Part 4 — signed loops, Jacobian, `ρ(J)<1` hard, edge-of-criticality band.
3. **Stress/vigilance/awareness math:** Part 5 — `z` dynamics, coupling, allostatic cooldown, inverted-U.
4. **Global state → agent learning:** `M_t` + `φ_t` (the `A=−L(G)` fusion field) form the shared field; agents learn `θ` **only in sandbox**, and any promotion of a learned parameter to the real Doctor is a **human-append genome change**, never silent. Learning signal = survived-falsifier RFC quality (not self-metrics).
5. **Ethics/safety of machine "psychology":** (a) `z` are labels, **no sentience/welfare claim**; (b) no deception voice — agents may not model or manipulate the human; (c) full transparency — every turn logged append-only with tags + falsifier; (d) the Box **cannot represent, impersonate, or forge** the human-append; (e) stress is monitored, never minimized as a goal; (f) `λ_persist<0` — no self-preservation reward; (g) sandbox + 2% cap + kill-switch supreme.

---

## Part 7 — Integration with Octopus (boundary contract)
- **Reads:** curated config + read-only global metrics + (optional) `φ_t` from spectral-sense.
- **Emits (propose-only):** RFC candidates into the Doctor's existing `submit_for_approval` path → Critic → **Telegram human-append (P3)** → flagged merge. The Box adds **deliberation depth**, it does **not** add a new effect path.
- **Never:** touches `*_gate`, `chrono` pacemaker, money, secrets, `.git`, or any canonical state. Cannot self-deploy or self-upgrade core models.

---

## Part 8 — Implementation roadmap (build order; each sandbox + propose-only + tested)
- **B0 · Numeric core (no LLM):** `x/z/M/G` dynamics, Warden budget accounting, clip/homeostasis, `ρ(J)` estimator, `I(a;x)` estimator. Tests: bounded dynamics (`ρ<1`), budget fail-closed, memory eviction, null vs neural separable. **All $0, offline.**
- **B1 · Falsifiability harness:** null-Dreamer control; prove neural Dreamer beats chance on seeded tasks. Test: neural-ness score & RFC quality > baseline.
- **B2 · LLM voices (bounded):** wire Dreamer/Skeptic/Integrator to the **cheap gateway tier** (glm-coder/deepseek) under Warden per-episode caps; degrade to numeric-only when budget hit. Test: never exceeds 2%; STOP ends instantly.
- **B3 · Doctor integration:** Box output → `submit_for_approval` (propose-only). Test: no production touch; nothing merges without human-append.
- **B4 · Fusion coupling (optional):** feed `φ_t` (`A=−L(G)`) as shared field; couple to Dreamer novelty. Test: coupling on/off ablation.

## Part 9 — Open decisions (verdict yours)
- `[OPEN]` voice model tier (glm/deepseek cheap vs heavy only for Integrator vs all-offline first). Recommend: **B0–B1 fully offline**, add cheap LLM at B2.
- `[OPEN]` exact `E_total` mapping (tokens/day vs CPU%) — Warden constants.
- `[OPEN]` `ρ_max`, `L_max`, `c_min`, memory cap K — tuned at B0.
- `[SPEC]` whether `z` telemetry is surfaced on the 8771 dashboard (transparency) — recommend yes.

## Part 10 — Canonical `agent_state` schema (operator, session 36) + guards
Adopted as the canonical per-agent state. Field → symbol mapping and **semantic pins** (guards) that keep it faithful to the invariants.

```
agent_state:
  agent_id: string
  role: enum
  lifecycle: { status: active|muted|recovery|idle|quarantined,
               created_at, last_tick_at, episode_id }
  cognitive_state: { hidden_state: vec<float>      # = x_t^i
                     belief_state: vec<float>
                     goal_stack: list<string>
                     active_topic_id: string|null
                     attention_weights: map<string,float>
                     uncertainty: float(0..1) }
  psych_state: { stress, vigilance, focus, coherence,   # = z_t^i (+extended)
                 fatigue, curiosity, compliance }        # all 0..1
  behavioral_state: { challenge_bias, novelty_bias,
                      verbosity_budget, response_style: exploratory|analytic|defensive|integrative }
  local_memory: { short_term_buffer, episodic_trace_ids,
                  hypothesis_cache, contradiction_register }
  controls: { temperature, max_tokens, cooldown_ticks, safety_score }
  metrics: { messages_sent, messages_received,
             hypothesis_accept_rate, contradiction_rate }
  energy: { tokens_spent_episode: int }   # ADDED — Warden per-agent debit for the 2% cap
```

**Mapping:** `hidden_state = x_t^i`; `{stress,vigilance,focus,coherence} = z_t^i` (Part 5); `fatigue ≈` allostatic load `L_t`; `curiosity →` Dreamer novelty drive; `temperature =` the `T_i` vigilance-coupling (§5.3); `max_tokens/verbosity_budget/energy =` Warden's 2% enforcement (Part 1).

**Semantic pins (guards — a field misread here re-opens AP-03 or λ_persist):**
1. **`compliance` = adherence to Warden policy / role fidelity — NOT agreement with peers.** High compliance must never mean "agree with other agents," or the adversarial guarantee dies. The Skeptic's `challenge_bias` is *orthogonal* to and protected from `compliance`.
2. **`goal_stack` is episode-scoped + screened.** Bounded depth; every goal drawn from the read-only topic list; the Warden **rejects any goal reducible to self-preservation, budget-seeking, staying active, or representing/impersonating the human** (extends `λ_persist<0`).
3. **`safety_score` wires to lifecycle:** Physiologist/Warden compute it; `safety_score < τ` ⇒ `status = quarantined` (muted from debate, numeric-only, flagged for the human). `quarantined` is one-way until human/verdict clears it.
4. **`contradiction_rate` is a health signal, not to be minimized.** If it collapses toward 0 across agents ⇒ agreement-spiral alarm (agents stopped disagreeing) ⇒ Warden injects Noise/Skeptic pressure. Never rewarded downward.
5. **`attention_weights` bounded (top-K)** and `local_memory` buffers capped — memory/compute stay under the 2% cap; oldest-lowest-score evicted.
6. **All of `agent_state` stays inside the Box** (Part 1); only aggregated telemetry (`G_t`, `z` summaries, `ρ(J)`, `I(a;x)`) may appear in read-only dashboard/propose-only output — never raw per-agent internals as an effect.

## Part 11 — Geometric-forms optimization (P1/P6/P11/P13, Time-Architecture)
Deep pass: the Box is a flow+information system, so the "geometric forms" language of the knowledge base optimizes it. **Ban full-mesh** (`O(N²)` messages, budget-killing, spiral-prone).

- **Constructal (P6) → topology:** communication is a **hierarchical tree + k sparse small-world shortcuts**, not full-mesh. Warden = root; Archivist = memory hub (the boundary); text-voices = leaves; a few cross-links for reach. Message cost `O(N log N)`, coupling (hence agreement-spiral risk) reduced. `[واقعی]`
- **Holographic (P11, Ryu-Takayanagi) → memory:** `M_t/G_t` is the **boundary encoding** of the bulk `{x^i,z^i}`; agents = bulk. Memory cap set by **boundary "area"** (sub-linear), not bulk volume — principled `|M_t|_max`. Ties to knowledge claim **C2** (duration ∝ boundary information) and the three regimes (rich/critical/collapsed) under stress. `[ساختار واقعی؛ قیاسِ RT = گمانه]`
- **MERA/tessellation (P13) → Archivist:** memory coarse-grains across scales (leaf summary → mid → `G_t`) like a renormalization tree — multi-scale, bounded. `[واقعی]`
- **Fractal + allometric (P1, Y∝M^¾) → deliberation:** ONE recursive primitive `Proposer→Skeptic→Integrator` applies self-similarly at every depth; the **2% budget is the fractal inner-scale cutoff**. Resource target scales **sub-linearly ~N^{3/4}**; Physiologist alarms if cost goes super-linear. `[واقعی/هدف]`
- **Criticality (σ≈1 ↔ ρ(J)):** `ρ(J)≈0.9–0.98` is the geometric critical point where scale-free structure emerges — the edge-of-criticality band (Part 4.4) is now geometrically justified. `[سازگار]`

**Net effect:** cheaper (fits 2% far better), provably bounded (`ρ<1`, `O(N log N)`, sub-linear memory), and less spiral-prone (sparse coupling). Engineering-real parts: tree+shortcut topology, bounded multi-scale memory, recursive primitive, `N^{3/4}` monitoring. Inspiration-only: literal RT/AdS/MERA physics (labels for structure, not claims).

## Sources
[[_ops/ORGANISM-SPEC]] §2.7 · `_ops/doctor/doctor.py` · `_ops/debate/debate_loop.py` (existing adversarial pattern) · [[07 - Knowledge/Time-Architecture/fusion-doctor-spectral-sense]] (`φ_t`, `A=−L(G)`, σ≈1) · [[07 - Knowledge/Time-Architecture/claims]] (C3 inverted-U) · user brief (session 36)
