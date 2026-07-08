---
type: proposal
project: "[[07 - Knowledge/Time-Architecture/PROJECT]]"
status: draft-for-verdict
created_by: agent
relates_to: "[[07 - Knowledge/Time-Architecture/MAP]] (da/dt=−L(G)a) · [[04 - Architect System/DOCTOR-BOX-OF-AGENTS-SPEC]] (agent_state, φ) · [[_ops/ORGANISM-SPEC]]"
tags: [octopus, school-memory, curriculum, awareness, geometric, spec, propose-only]
created: 2026-07-08
updated: 2026-07-08
---

# SCHOOL MEMORY — default curriculum + awareness field (spec, no code)

> Shared read-only knowledge substrate every agent/leg mounts at init. A geometric, layered graph of ~200 topics (humans → societies → evolution of consciousness), with an awareness field that diffuses via the graph Laplacian `−L(G)` — the **same operator** as Time-Architecture and the Doctor's spectral-sense. Architecture only.
> **Honesty line:** "awareness / consciousness" here are **field metrics**, not sentience claims. Every node carries an epistemic tag. No PII enters the curriculum.

## 1. Entities (reconciled with the real Octopus)
1. **Octopus Core** — holds the *canonical* Curriculum Graph (ledger-versioned), assigns lessons/projects, aggregates insight. Canonical edits are **human-append** (genome-like), never silent.
2. **Legs** — the real legs are business subsystems (Lead-نقاشی, Ziman, Crypto, Accounting, Mining, Project-F). They **consult** the school; they do **not** become curriculum classes. `[honesty]`
3. **School Memory** — `07 - Knowledge/school-memory/` : the graph + per-agent study state. Read-only mount; propose-only writes.
4. **Research Classes / Consultation Rooms** — 6 bounded knowledge-rooms (one per layer A–F), each a capped set of Box-of-Agents instances focused on a topic subset, sharing the common core. Propose-only, sandboxed, budget-capped (reuse the Box 2% discipline). Distinct from money-legs.

## 2. Geometric curriculum (the math)
1. **Nodes/layers:** `V = {v_i | i=1..200} = V_A∪V_B∪V_C∪V_D∪V_E∪V_F`, ~33/layer.
   - L1 **A** Individual & micro-awareness · L2 **B** Small groups & networks · L3 **C** Institutions & macro-society · L4 **D** Culture & meaning · L5 **E** Technology & digital mind · L6 **F** Long-term evolution & crises.
2. **Edges:** directed, labeled, weighted `e=(v_i→v_j, label∈{depends-on, influences, similar-to, part-of}, w∈[0,1])`. `G=(V,E)`.
3. **Embedding:** each `v_i → x_i ∈ R^6`, interpretable axes: (1) micro↔macro, (2) concrete↔abstract, (3) short↔long time-scale, (4) culture, (5) technology, (6) consciousness-depth. `d(i,j)=‖x_i−x_j‖`; small ⇒ related.
4. **Awareness field:** `a(t) ∈ [0,1]^200`; diffusion `ȧ = −L(G)·a + input(t)`, `L=D−W`. Studying `v_k` raises `a_k`, which then flows to neighbors. **Same `L(G)` the Doctor's `spectral_mine` reads** ⇒ insight-detection is shared machinery.

## 3. Agent School State schema (extends Box `agent_state` Part 10)
```
school_state(agent α):
  studied_topics: set<topic_id>
  mastery:   map<topic_id, float[0..1]>   # m_i^α
  interest:  map<topic_id, float[0..1]>   # I_i^α
  awareness: vector<float>[200]            # a^α(t)
  subjective_time: float                   # τ^α  (= ∫ γ(z) dt, from ChronoUnit)
  open_questions: list<string>             # Q_α
  simulations_run: list<run_ref>           # R_α (ledger-linked)
  class_membership: set<class_id>          # C_α ⊆ {Class_A..Class_F}
```
`τ^α` couples to the psych-state `z` (novelty/load/intensity dilate learning-time) — reuses the ChronoUnit `γ`.

## 4. Research-Class templates (6, one per layer)
| class | focus | methods (sim styles · metrics) | interaction protocol |
|---|---|---|---|
| **A** Individual & attention | attention, emotion, habit, identity | agent-based micro-sim · mastery, `I(a;x)` | publishes micro→meso links |
| **B** Networks & norms | trust, teams, families, contagion | network/percolation sim · σ (criticality) | consumes A, feeds C |
| **C** Institutions & power | law, economy, inequality | system-dynamics · flow/constructal metrics | macro anchors for B/D |
| **D** Culture & meaning | narrative, art, religion, media | memetic diffusion · `−L(G)` spread | cross-links E |
| **E** Technology & digital mind | platforms, AI, privacy, addiction | feedback-loop sim · stability `ρ(J)` | bridges A↔F |
| **F** Long-term evolution & crisis | cycles, climate, pandemics, futures | scenario/branching · scale-exponents | integrates all shells |
Shared across classes: one insight registry, one vocabulary, explicit micro↔macro links.

## 5. Awareness dynamics (pseudocode)
```
each tick dt:
  input = study_signals + observation_signals          # topic-localized
  a ← clip(a + dt·(−L·a + input), 0, 1)                 # graph diffusion
  for each studied v_k: m_k ← m_k + lr·(1−m_k)          # mastery gain
  τ ← τ + γ(z)·dt                                       # subjective time
insight events (propose-only):
  (i)  a_i crosses θ_high            → "topic ignited"
  (ii) Δ(spectral gap of L) large    → "structural shift"  (shared w/ spectral_mine)
  (iii) persistent co-activation     → PROPOSE new edge (curriculum change = human-gated)
```
Multi-scale: radial coordinate = shell {micro⊂meso⊂macro⊂mega}; `a_global` = shell-aggregated mean of `a^α`.

## 6. Local → global, one worked example
1. **Observe:** a Lead-نقاشی chat arrives (no PII).
2. **Map:** classifier places it on topics {A: attention, B: trust} at embedding `x`.
3. **Local update:** the Perception leg's agent bumps `a_A, a_B`, updates `mastery`, appends an `open_question`.
4. **Diffuse:** `−L(G)` spreads awareness to neighbors (e.g. C: pricing-norms).
5. **Aggregate:** Core rolls `a^α` → `a_global`; a persistent cluster forms.
6. **Insight:** spectral-gap shift fires → an **insight token** (propose-only). If it implies a *new edge*, it's queued as a **human-append curriculum change** — never auto-applied.

## 7. Octopus Core integration
- **Canonical curriculum** = one ledger-versioned artifact (extend-don't-rival, one truth). Agents **mount read-only**; edits go through human-append.
- **Lesson assignment:** Core issues `lesson = (topic, task, budget)`; agent studies → returns propose-only insight.
- **Rooms as exploration legs:** Research Classes run on Box infra under the 2% cap; kill-switch + λ_persist-negative apply (no "study forever" reward).
- **Curriculum evolves** only as the world changes AND a human approves (new topics/edges = genome-like change).

## 8. Safety & honesty (bounded, faithful)
- Awareness/consciousness = **metrics, not sentience**; every node epistemic-tagged (Established…Speculative) per Time-Architecture discipline.
- **No PII** in curriculum; observations carry topic labels, not raw personal data (Accounting/Project-F rules hold).
- Bounded: ~200 nodes, capped edges, rate-limited insight-proposals ⇒ anti-rabbit-hole (this area is `priority:low, RABBIT_HOLE_RISK` — Security Gate + verdict gate any real data use).
- Propose-only; no effector; Research Classes cannot move money or publish.

## 9. The ~200 topics — generative structure (not hand-enumerated)
Full enumeration is a **fill-table**, not prose. ID scheme `⟨A..F⟩⟨01..~33⟩`; each row: `id · category · title · short_desc · coord x∈R^6 · edges[{to,label,w}] · epistemic_tag · valid_until · sources`. Representative seeds (≈8/layer) to anchor the table:
- **A:** attention, working-memory, habit-loop, emotion-regulation, identity, self-narrative, motivation, perception-bias.
- **B:** trust, reciprocity, small-team dynamics, family systems, homophily, social contagion, status, cooperation.
- **C:** law, markets, inequality, bureaucracy, power, collective action, institutions, governance.
- **D:** narrative, myth/religion, art, media ecology, values, ritual, meaning-making, taboo.
- **E:** platforms, recommender loops, AI agency, interface/attention economy, privacy, addiction, digital identity, automation.
- **F:** historical cycles, demographic transition, climate, pandemics, technological phase-shifts, existential risk, long-termism, civilizational resilience.
> Verdict needed: auto-generate the full 200-row table (I can draft it as a CSV under `school-memory/curriculum.csv`, propose-only) — or keep it seed-only until you curate.

## 10. Roadmap (each sandbox · propose-only · tested · $0 offline first)
- **SM-B0:** curriculum graph loader + `L(G)` + awareness diffusion + insight-events (offline).
- **SM-B1:** agent school-state + study/mastery/τ (reuse Box agent_state).
- **SM-B2:** 6 Research Classes as bounded rooms on Box infra (2% cap).
- **SM-B3:** Core integration — lesson assignment + `a_global` aggregation (read-only mount).
- **SM-B4:** insight → propose new edge/topic → human-append curriculum evolution.

## Sources
[[07 - Knowledge/Time-Architecture/MAP]] (`da/dt=−L(G)a`, embedding, layers) · [[04 - Architect System/DOCTOR-BOX-OF-AGENTS-SPEC]] (agent_state, φ, 2% cap, ρ(J)) · [[07 - Knowledge/Time-Architecture/fusion-doctor-spectral-sense]] (shared `L(G)` spectral machinery) · user brief (session 36)
