# 🧬 OCTOPUS — Research-Synthesis Mega-Prompt: Memory Persistence + Self-Improvement Architecture Upgrade

> **Purpose:** This document contains (1) state-of-the-art research on multi-agent memory persistence and self-improvement from major companies (2023-2026), (2) deep gap analysis of the Octopus project's current architecture, and (3) a concrete, phased plan for upgrading Octopus's memory, learning, and self-improvement systems. Claude 5 should read this entirely and execute autonomously within safety constraints.

> **Created:** 2026-07-10
> **Security:** Telegram bot token in `_ops/OCTOPUS.env` — NEVER log or expose.
> **Live gate:** Locked until 2026-07-21. All work is shadow/paper ($0).

---

# PART A: INDUSTRY RESEARCH — How Top Companies Solve Memory + Self-Improvement

## A.1 Memory Architecture Taxonomy (2023-2026 State of the Art)

### Pattern 1: OS-Style Virtual Memory Paging — **MemGPT/Letta** (UC Berkeley)
**Paper:** [MemGPT: Towards LLMs as Operating Systems](https://arxiv.org/pdf/2310.08560)
**Company:** Letta (formerly MemGPT), UC Berkeley Sky Computing Lab

**Core Idea:** Treat the LLM context window like RAM and external storage like disk. Use OS-style virtual memory paging.

| Memory Tier | Analogy | Role |
|---|---|---|
| **Main Context** | RAM | Current working memory (limited tokens) |
| **Recall Memory** | SSD | Recent conversation history, fast retrieval |
| **Archival Memory** | HDD | Long-term storage, slow but vast |

**Key Mechanism:** When the LLM needs info not in context, it issues a function call (like a page fault) to search/insert from archival or recall storage. The LLM itself decides what to page in/out.

**2025 Updates:** Adaptive retention and context summarization for more efficient semantic memory management.

**Relevance to Octopus:** Octopus has a similar tiered structure (consolidation → latent space → JSONL history) but **lacks the LLM-directed paging mechanism**. Octopus's consolidation is rule-based, not LLM-directed.

---

### Pattern 2: Graph-Based Memory with Conflict Resolution — **Mem0** (mem0.ai)
**Paper:** [Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory](https://arxiv.org/html/2504.19413v1)
**Company:** mem0.ai

**Core Pipeline:**
```
Raw Input → Extraction → Deduplication → Consolidation → Scoped Retrieval
```

**Key Features:**
- **ADD-only architecture:** Memories accumulate; nothing is overwritten (append-only like Octopus's ledger)
- **Deduplication:** Semantic deduplication during consolidation (folding similar memories)
- **Conflict resolution:** LLM-driven contradiction resolution (when two memories contradict, older is archived with `valid_until`)
- **Graph extension (Mem0-Graph):** Entities as nodes, relationships as edges (knowledge graph)
- **Hybrid search:** Dense + sparse retrieval

**Known Gap:** The ADD-only architecture doesn't fully implement conflict resolution in open-source v2 — active area of development.

**Relevance to Octopus:** Octopus's consolidation has **no deduplication, no conflict resolution, no structured fact extraction**. Mem0's pipeline directly maps to what's missing.

---

### Pattern 3: Temporal Knowledge Graph — **Zep** (Zep AI)
**Paper:** [Zep: A Temporal Knowledge Graph Architecture for Agent Memory](https://arxiv.org/html/2501.13956v1)
**Company:** Zep AI

**Core Idea:** Every fact/edge in the knowledge graph carries temporal metadata.

| Memory Subgraph | Content | Temporal Behavior |
|---|---|---|
| **Episodic** | Specific events tied to time/place | Strong temporal decay |
| **Semantic** | Generalized knowledge | Slow decay |
| **Community** | Shared/social knowledge | Aggregate over time |

**Key Mechanism:** Every edge has `valid_from` and `valid_until` timestamps. Stale facts naturally decay in retrieval relevance. Fact extraction from conversations → structured triples (subject, predicate, object) with temporal metadata.

**Benchmark:** Outperforms MemGPT in Deep Memory Retrieval (DMR) benchmark.

**Relevance to Octopus:** Octopus's `latent_space.py` stores `ts` but **never uses it in retrieval or ranking**. No temporal decay, no episodic/semantic split. Zep's approach directly addresses this.

---

### Pattern 4: Episodic Memory + Reflection — **Stanford Generative Agents**
**Paper:** [Generative Agents: Interactive Simulacra of Human Behavior](https://arxiv.org/abs/2304.03442)
**Authors:** Joon Sung Park et al. (Stanford / Google)

**Architecture:**
```
Observation → Memory Stream (append) → Retrieval (relevance + recency + importance)
                                          ↓
                                    Reflection (periodic synthesis into higher-level insights)
                                          ↓
                                    Planning (decompose goals into sub-goals)
```

**Key Mechanism:**
- **Memory Stream:** Natural language records of experiences (like Octopus's consolidation.jsonl)
- **3-Factor Retrieval:** `score = α·recency + β·relevance + γ·importance` — surfaces right memories for current context
- **Reflection:** Periodically synthesizes higher-level insights from accumulated memories (e.g., "X tends to happen after Y")
- **Planning:** Decomposes goals into actionable sub-goals for future behavior

**Relevance to Octopus:** Octopus has **no reflection step** — `run_cycle()` ends immediately after submit with no retrospective. The 3-factor retrieval is missing entirely.

---

### Pattern 5: MAP-Elites + LLM Mutation — **AlphaEvolve / FunSearch** (Google DeepMind)
**Paper:** [AlphaEvolve: A coding agent for scientific and algorithmic discovery](https://msu.dvaoblaka.ru/media/2025/05/68271bf34ef55_AlphaEvolve.pdf)
**Company:** Google DeepMind

**Core Loop:**
```
Elite Archive (MAP-Elites cells) → Sample elite → LLM Mutation → Execute → Evaluate → Insert if better
```

**Key Features:**
- **MAP-Elites Archive:** Maintains best solution per behavior descriptor cell (multi-dimensional, not just score)
- **LLM as Mutation Operator:** Gemini generates code variants from elite solutions
- **Real Sandbox Execution:** Programs are actually run and tested (not severity heuristics)
- **Recursive Self-Improvement:** AlphaEvolve discovered improvements to Gemini's own training pipeline

**Difference from FunSearch:** Combines MAP-Elites illumination with LLM mutations for broader search coverage.

**Relevance to Octopus:** Octopus's `evolution.py` has MAP-Elites structure but **mutations are string stubs, not code changes**. Evaluation is severity-lookup, not sandbox execution. Missing the LLM-as-mutator pattern.

---

### Pattern 6: Hierarchical Memory Persistence — **LangGraph** (LangChain)
**Docs:** [LangGraph Persistence](https://docs.langchain.com/oss/python/langgraph/persistence)
**Company:** LangChain

**Two-Layer Persistence:**
| Layer | Mechanism | Scope |
|---|---|---|
| **Short-term** | Checkpointers (save graph state between steps) | Per-thread / within-session |
| **Long-term** | Store API (`store.put`/`store.get`) | Cross-thread / cross-session |

**Key Insight:** Checkpoints reset per thread, but Store survives thread boundaries. Production uses Redis/Postgres/SQLite backends.

**Relevance to Octopus:** Octopus has chrono.db checkpoints + JSONL append-only, but **no cross-session knowledge persistence** (each restart starts from state files, not from accumulated knowledge graph).

---

### Pattern 7: Self-Evolving Graph Memory — **GraphMem** (2025)
**Paper:** [GraphMem: Self-Evolving Graph-Based Memory for Production AI Agents](https://www.researchgate.net/publication/398203328_GraphMem_Self-Evolving_Graph-Based_Memory_for_Production_AI_Agents)

**Core Innovation:**
- **LLM-powered knowledge extraction** → structured graph
- **Conflict Resolution during `evolve()`:** Contradicting facts detected → older fact ARCHIVED with `valid_until` timestamp
- **Self-evolution:** Memory graph changes over time based on new information, not just append

**Relevance to Octopus:** Octopus has **no knowledge graph, no conflict resolution, no self-evolving memory structure**.

---

### Pattern 8: Orchestrator-Worker Multi-Agent — **Anthropic Claude**
**Source:** [How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system)
**Company:** Anthropic

**Architecture:** Claude Opus 4 as lead orchestrator + Claude Sonnet 4 subagents (parallel workers). Outperforms single-agent Claude Opus 4.

**Memory:** Claude Managed Agents now support persistent memory (public beta) with immutable versioning — every memory change creates an immutable version for audit trail.

**Relevance to Octopus:** Octopus has a single organism loop, not an orchestrator-worker pattern. Could benefit from parallel subagent execution for research/debate tasks.

---

### Pattern 9: Meta-Programming Multi-Agent — **MetaGPT** (ICLR 2024)
**Paper:** [MetaGPT: Meta Programming for Multi-Agent Collaborative Framework](https://arxiv.org/abs/2308.00352)

**Architecture:** Software company simulation with specialized roles (PM, Architect, Engineer, QA). Uses SOPs (Standardized Operating Procedures) as prompts encoding human workflows.

**Memory:** Centralized knowledge sharing + personalized role-based memory caches. Reduces conflicts between agents through structured workflow.

**Relevance to Octopus:** Octopus has organ specialization but **no structured inter-organ knowledge sharing protocol** (no blackboard, no pub/sub, no shared context).

---

### Pattern 10: Conversational Actor Model — **Microsoft AutoGen / AG2**
**Source:** [LangGraph vs CrewAI vs AutoGen comparison](https://dev.to/pockit_tools/langgraph-vs-crewai-vs-autogen-the-complete-multi-agent-ai-orchestration-guide-for-2026-2d63)
**Company:** Microsoft

**Architecture:** Agents exchange asynchronous messages via event-driven runtime (actor model v0.4+). Multi-turn conversations with shared memory across agents.

**Relevance to Octopus:** Octopus organs communicate through `wiring.py` function calls, not through a message-passing system. No async inter-organ messaging.

---

## A.2 Research Summary Matrix

| System | Memory Type | Temporal Decay | Conflict Resolution | Fact Extraction | Self-Improvement | Graph Structure |
|---|---|---|---|---|---|---|
| **MemGPT/Letta** | Tiered (RAM/SSD/HDD) | Via paging | No | No | No | No |
| **Mem0** | ADD-only + Graph | No (open issue) | LLM-driven (v3) | Entity extraction | No | Mem0-Graph |
| **Zep** | Temporal KG | Yes (edge timestamps) | Yes (archive old) | Yes (triple extraction) | No | Yes (episodic+semantic+community) |
| **Stanford Generative** | Episodic stream | Recency weighting | No | No | Reflection loop | No |
| **AlphaEvolve** | MAP-Elites archive | No | No | No | Yes (LLM mutation) | No (cell grid) |
| **LangGraph** | Checkpoint + Store | No | No | No | No | No |
| **GraphMem** | Self-evolving graph | Yes (valid_until) | Yes (archive + supersede) | Yes (LLM extraction) | Yes (evolve) | Yes |
| **Anthropic Claude** | Immutable versions | Via versioning | Via versioning | No | Orchestrator-worker | No |
| **MetaGPT** | Role-based caches | No | Via SOP workflow | No | No | No |
| **AutoGen** | Conversation memory | No | No | No | No | No |

---

# PART B: OCTOPUS GAP ANALYSIS — What's Missing vs. Industry

## B.1 Critical Gaps (HIGH Priority)

### GAP-1: Consolidation Has No Temporal Decay or Conflict Resolution
**File:** `_ops/neural/consolidation.py:92-111`
**Problem:** The `_history` list grows without bound. Every entry treated equally. No `recency` weighting. When multiple sources contradict, both are concatenated silently.
**Industry Fix:** Zep-style temporal decay (`decay = exp(-λ * age)`) + GraphMem-style conflict resolution (detect contradictions → archive older fact with `valid_until`).

### GAP-2: Latent Space Has No Deduplication, No TTL, Temporal Metadata Unused
**File:** `_ops/neural/latent_space.py:42-54, 60-84, 122-142`
**Problem:** `ts` is stored but never used in retrieval. No near-duplicate detection on insert. No LRU eviction or TTL. Vectors accumulate indefinitely.
**Industry Fix:** Mem0-style dedup on insert (check similarity before adding) + Redis-style TTL/eviction + use `ts` in retrieval scoring.

### GAP-3: Doctor Evolution Mutations Are String Stubs, Not Code Changes
**File:** `_ops/doctor/evolution.py:100-111`
**Problem:** `mutate()` appends generic strings like "+ guard اضافه" to fix text. No actual code diff generation, no AST transformation, no structured change proposal.
**Industry Fix:** AlphaEvolve pattern: LLM as mutation operator that generates actual program variants. `measured_lift` should execute code in sandbox, not lookup severity scores.

### GAP-4: School Memory Has No Prediction Error, No Spaced Repetition
**File:** `07 - Knowledge/school-memory/curriculum.py:27-36, 147-167`
**Problem:** No per-node learning progress. No generative model to predict what should be known. No spaced repetition scheduling. Activation diffusion spreads but never decays.
**Industry Fix:** SuperMemo SM-2 algorithm (ease_factor, interval, repetitions) + Predictive Coding (Friston): predict awareness → compute error → drive attention.

### GAP-5: No Structured Knowledge Representation (No Knowledge Graph)
**Project-wide gap**
**Problem:** All knowledge is stored as either flat strings in `consolidation.jsonl` or dense vectors in `latent_space.py`. No triples, no entities, no relationships, no ontological grounding.
**Industry Fix:** Zep/GraphMem pattern: extract (subject, predicate, object) triples with temporal metadata. Build a temporal knowledge graph.

## B.2 Medium Gaps (MEDIUM Priority)

### GAP-6: No Reflection / Self-Evaluation Step in Doctor Cycle
**File:** `_ops/doctor/doctor.py:618-625`
**Problem:** `run_cycle()` ends immediately after `submit_for_approval()`. No retrospective, no meta-cognition, no strategy update based on outcomes.
**Industry Fix:** Stanford Generative Agents reflection pattern: periodically synthesize higher-level insights from accumulated experiences.

### GAP-7: BCM and Sparse Filter Are Independent, No Feedback Loop
**File:** `_ops/wiring.py:904-928`
**Problem:** BCM pruning and sparse filtering run as independent decorations with no data flowing between them. BCM should inform sparse about what's already well-known.
**Industry Fix:** BCM homeostatic plasticity feedback: theta (saturation threshold) should feed into sparse filter's threshold — well-known concepts get higher sparsity threshold.

### GAP-8: No Episodic vs Semantic Memory Separation
**Project-wide gap**
**Problem:** `ConsolidatedInsight` has a single `insights: list[str]` field. No distinction between "what happened at time T" (episodic) and "general truth learned" (semantic).
**Industry Fix:** Zep's episodic/semantic/community subgraph separation. CLS theory (McClelland et al., 1995): hippocampus stores fast episodic → slow consolidation into semantic neocortex.

### GAP-9: Verdicts Are Fire-and-Forget, No Lesson Extraction
**File:** `_ops/doctor/doctor.py:534-547`
**Problem:** When RFCs are rejected, the reason is recorded in calibration but no lesson is extracted. No "why was this rejected?" analysis feeds back into mining strategy.
**Industry Fix:** Prioritized Experience Replay (Schaul et al., 2015): store failed attempts with priority, revisit and learn from mistakes.

### GAP-10: No Cross-Session Knowledge Persistence
**Project-wide gap**
**Problem:** Each restart loads from state JSON files but accumulated knowledge (474 consolidation cycles) is in `consolidation.jsonl` — not in a structured, queryable knowledge store that persists across sessions.
**Industry Fix:** LangGraph's Store API pattern: cross-session persistent memory that survives thread/process restarts.

## B.3 Low Gaps (LOW Priority)

### GAP-11: Chrono Missing Per-Event Timers and Temporal Windowing
**File:** `_ops/chrono.py:80-160`
**Problem:** No "schedule callback after N beats" or "events within last N beats" query. HLC and phi-accrual are well-implemented.
**Industry Fix:** Flink/Spark temporal windowing (tumbling, sliding, session windows).

### GAP-12: Latent Space Uses Brute-Force Similarity (No ANN Index)
**File:** `_ops/neural/latent_space.py:60-84`
**Problem:** Builds full matrix on every query. Acceptable at 32-dim small scale, won't scale.
**Industry Fix:** HNSW index (Malkov & Yashunin, 2018) for approximate nearest neighbor.

---

# PART C: PROPOSED ARCHITECTURE UPGRADE — Phased Plan

## C.1 Phase Overview

| Phase | Goal | Industry Pattern | Risk | Pre-registered Metric |
|---|---|---|---|---|
| **UP-1** | Structured Knowledge Extraction | Zep/GraphMem fact extraction | Low | `fact_count > 0`, `triple_extraction_rate` |
| **UP-2** | Temporal Knowledge Graph | Zep temporal KG + GraphMem conflict | Medium | `temporal_decay_active`, `conflicts_resolved_count` |
| **UP-3** | 3-Factor Retrieval | Stanford Generative Agents | Medium | `retrieval_relevance_score`, `recency_weight_active` |
| **UP-4** | Reflection Loop | Stanford + CLS consolidation | Medium | `reflection_insights_generated`, `reflection_cycle_count` |
| **UP-5** | BCM↔Sparse Feedback | BCM homeostatic plasticity | Low | `bcm_theta_feeds_sparse`, `wellknown_filter_rate` |
| **UP-6** | LLM-Assisted Mutation | AlphaEvolve pattern | 🔴 HIGH | `code_mutation_count`, `sandbox_mutation_pass_rate` |
| **UP-7** | Spaced Repetition in School | SuperMemo SM-2 | Low | `topic_mastery_tracking`, `review_interval_accuracy` |

## C.2 Phase Details

### UP-1: Structured Knowledge Extraction (from Strings to Triples)

**Goal:** Transform consolidation output from flat strings to structured triples `(subject, predicate, object)` with temporal metadata.

**What to build:**
- `_ops/neural/fact_extractor.py` — Rule-based fact extraction from consolidation insights
  - Pattern: "بهترین محتوا: X (score=Y)" → triple `(acquisition, best_content, X, score=Y)`
  - Pattern: "تعداد فیکس تأییدشده: N" → triple `(doctor, fixes_approved, N)`
  - Pattern: "میانگین آگاهی: A" → triple `(school, mean_awareness, A)`
- Add `facts: list[Fact]` to `ConsolidatedInsight` (backward-compatible, `None` by default)
- Persist facts in `_ops/state/knowledge-graph.jsonl` (append-only per I1)

**Industry Pattern:** Zep's fact extraction + OpenIE triple format

**Safety:** Read-only extraction from existing data. No LLM calls. $0.
**Tests:** `test_fact_extractor.py` — 10+ tests
**Pre-registered:** `fact_count > 0` for any consolidation cycle with data.

---

### UP-2: Temporal Knowledge Graph (Time-Aware Memory)

**Goal:** Build a temporal knowledge graph where every fact carries `valid_from` and `valid_until`, enabling temporal decay and conflict resolution.

**What to build:**
- `_ops/neural/knowledge_graph.py` — TemporalKG class
  - `add_fact(subject, predicate, object, source, ts)` → fact with `valid_from=ts, valid_until=None`
  - `query(subject=None, predicate=None, object=None, as_of_ts=None)` → time-aware retrieval
  - `retract_fact(fact_id, reason)` → set `valid_until=current_ts` (not delete — I1)
  - `detect_conflicts()` → find facts where newer contradicts older → auto-archive older
  - `decay_factor(fact, current_ts) → float` — `exp(-λ * age_hours)` scoring
- Persist in `_ops/state/knowledge-graph.json` (JSON or JSONL)
- Wire into consolidation: after fact extraction → add to KG → detect conflicts

**Industry Pattern:** Zep temporal KG + GraphMem conflict resolution (archive older, not delete)

**Safety:** Append-only. No deletion. Conflict resolution = archive (set valid_until). $0.
**Tests:** `test_knowledge_graph.py` — 15+ tests
**Pre-registered:** `temporal_decay_active=True`, `conflicts_resolved_count >= 0`.

---

### UP-3: 3-Factor Retrieval (Relevance + Recency + Importance)

**Goal:** Replace brute-force cosine similarity in `latent_space.similar()` with 3-factor scoring: relevance (cosine similarity) + recency (temporal decay) + importance (access count or BCM weight).

**What to build:**
- Add `access_count` and `last_access_ts` to `SharedLatentSpace` metadata
- Add `recency_weight`, `importance_weight` parameters to `similar()`
- New scoring: `score = α·cosine_sim + β·recency_decay + γ·importance`
- Wire retrieval into consolidation: when looking for similar past cycles, use 3-factor scoring

**Industry Pattern:** Stanford Generative Agents: `score = α·recency + β·relevance + γ·importance`

**Safety:** Retrieval-only change. No new writes. No money. $0.
**Tests:** `test_retrieval_3factor.py` — 12+ tests
**Pre-registered:** `retrieval_relevance_score` correlates with manual relevance judgments. `recency_weight > 0`.

---

### UP-4: Reflection Loop (Meta-Cognition)

**Goal:** Add a reflection step to the doctor's `run_cycle()` — after submitting an RFC, synthesize what was learned from the cycle into a higher-level insight.

**What to build:**
- `_ops/doctor/reflection.py` — `ReflectionEngine`
  - `reflect(cycle_summary, recent_verdicts, history)` → `ReflectionInsight`
  - Patterns: "Last 3 RFCs about X were all rejected → avoid X bottleneck"
  - "Approval rate for organ Y is high → increase exploration of Y"
  - Store reflections in `_ops/state/reflections.jsonl` (append-only)
- Wire into `doctor.py:run_cycle()` after submit step
- Wire reflections back into mining strategy (inform `should_skip_bottleneck`)

**Industry Pattern:** Stanford Generative Agents reflection + CLS slow consolidation

**Safety:** Reflections are advisory only. No auto-merge from reflections. $0.
**Tests:** `test_reflection.py` — 10+ tests
**Pre-registered:** `reflection_insights_generated >= 0`. Reflections never trigger auto-action.

---

### UP-5: BCM↔Sparse Feedback Loop

**Goal:** Connect BCM saturation threshold (θ) to sparse filter — well-known concepts should have higher sparsity threshold (filter more aggressively).

**What to build:**
- Modify `SparseInputFilter` to accept external saturation signal from BCM
- BCM's `theta_mean` (average saturation) feeds into sparse's threshold: `effective_threshold = base_threshold * (1 + k * theta_mean)`
- Well-known topics (high theta) → higher filter → only truly novel signals pass
- Wire in `wiring.py:consolidation_beat()`: BCM step → theta → sparse threshold

**Industry Pattern:** BCM homeostatic plasticity feedback loop (Bienenstock, Cooper, Munro, 1982)

**Safety:** Filter-only change. Cannot add data, only filter. $0.
**Tests:** `test_bcm_sparse_feedback.py` — 8+ tests
**Pre-registered:** `bcm_theta_feeds_sparse=True`. Higher theta → higher effective threshold.

---

### UP-6: LLM-Assisted Mutation (🔴 HIGH RISK — VERDICT REQUIRED)

**Goal:** Replace string-stub mutations in `evolution.py` with actual code change proposals generated by an LLM (when LLM is available).

**What to build:**
- New mutation strategy in `evolution.py`: `llm_mutation(rfc, sandbox_result)`
  - Takes RFC + sandbox outcome → generates structured code change proposal
  - Change proposal: `{file, line_range, old_code, new_code, rationale}`
  - Validated by sandbox before submission
- Requires `DEEPSEEK_API_KEY` or similar (only active in paper-full profile)
- **NEVER auto-merge.** Human verdict always required.
- **🔒 RED label** — only activates with explicit owner verdict + ACTIVATION flag

**Industry Pattern:** AlphaEvolve's LLM-as-mutation-operator

**Safety:** EXTREME CAUTION. Propose-only. Sandbox-isolated. Human-gated. No auto-merge.
**Tests:** `test_llm_mutation.py` — 15+ tests (all offline, mock LLM)
**Pre-registered:** `code_mutation_count >= 0`. `sandbox_mutation_pass_rate`. ZERO auto-merge.
**⚠️ Gate:** Explicit owner verdict required. RED label. Not in PAPER_FULL_FLAGS.

---

### UP-7: Spaced Repetition in School Memory

**Goal:** Add learning progress tracking and spaced repetition scheduling to School Memory's `TopicNode`.

**What to build:**
- Add `LearningProgress` dataclass to `TopicNode`: `{ease_factor, interval, repetitions, last_review_ts, next_review_ts}`
- Implement SM-2 algorithm: after successful study → `interval = 6 * ease_factor^repetitions`; after failure → reset
- Add `spaced_review_schedule()` to `AwarenessField`: returns topics due for review
- Wire into consolidation: topics due for review get boosted activation

**Industry Pattern:** SuperMemo SM-2 (P. Wozniak, 1987) + Anki-style Leitner system

**Safety:** Read-only scheduling. No writes to knowledge base. $0.
**Tests:** `test_spaced_repetition.py` — 12+ tests
**Pre-registered:** `topic_mastery_tracking=True`. `review_interval` follows SM-2 formula.

---

## C.3 Execution Order and Dependencies

```
UP-1 (Fact Extraction) ──→ UP-2 (Temporal KG) ──→ UP-3 (3-Factor Retrieval)
                                       │
                                       └──→ UP-5 (BCM↔Sparse Feedback)

UP-4 (Reflection Loop) ──→ independent, can run in parallel with UP-1/2/3

UP-6 (LLM Mutation) ──→ 🔴 independent, requires explicit verdict

UP-7 (Spaced Repetition) ──→ independent, can run in parallel
```

**Recommended order:** UP-1 → UP-2 → UP-3 → UP-4 → UP-5 → UP-7 → (UP-6 only with verdict)

---

# PART D: CURRENT PROJECT STATE (Quick Reference)

## D.1 Test Suite: 77/77 Green

| Component | File | Tests |
|---|---|---|
| Blueprint Phase 3 (BCM) | `test_bcm_forgetting.py` | 15 |
| Blueprint Phase 4 (Sparse) | `test_sparse_filter.py` | 15 |
| Blueprint Phase 5 (Chamber T) | `test_chamber_temperature.py` | 25 |
| Blueprint Phase 6 (Fisher) | `test_fisher.py` | 13 |
| W-3 Telegram RFC Router | `test_telegram_rfc_router.py` | 19 |
| Phase 0-2 (existing) | 69 files | ~90 |
| **Total** | **77 files** | **~177** |

## D.2 Key Files (Absolute Paths)

```
F:\backup\_ops\                          # Main code
F:\backup\_ops\neural\consolidation.py   # Consolidation engine
F:\backup\_ops\neural\bcm.py             # BCM forgetting (Phase 3)
F:\backup\_ops\neural\sparse_filter.py   # Sparse filter (Phase 4)
F:\backup\_ops\neural\latent_space.py     # R^32 latent space (Phase 2)
F:\backup\_ops\neural\encoders.py        # 5 deterministic encoders
F:\backup\_ops\doctor\doctor.py          # Doctor main loop
F:\backup\_ops\doctor\evolution.py       # MAP-Elites evolution
F:\backup\_ops\doctor\temperature.py      # Chamber temperature (Phase 5)
F:\backup\_ops\doctor\calibration.py      # Feedback/calibration
F:\backup\_ops\doctor\chamber.py         # Inner chamber
F:\backup\_ops\budget\fisher.py           # Fisher metric (Phase 6)
F:\backup\_ops\budget\approval_channel.py # Telegram approval (51KB)
F:\backup\_ops\wiring.py                  # Master wiring (1077 lines)
F:\backup\_ops\chrono.py                  # Pacemaker + HLC + phi
F:\backup\_ops\organism.py               # Main loop
F:\backup\07 - Knowledge\school-memory\curriculum.py  # School memory
F:\backup\_ops\state\                    # State files
F:\backup\_ops\tests\run_all.py           # Test runner (77 files)
```

## D.3 Environment Constraints

| Constraint | Value |
|---|---|
| Dependencies | stdlib + numpy only |
| Budget | $0 (shadow) |
| Auto-merge | NEVER |
| Live gate | Locked until 2026-07-21 |
| Max cells | 6 |
| σ must be | ≤ 1.0 |
| Platform | Windows (Git Bash) |

---

# PART E: RESEARCH SOURCES

## Memory Architecture
- [MemGPT: Towards LLMs as Operating Systems (arXiv)](https://arxiv.org/pdf/2310.08560)
- [Mem0: Production-Ready AI Agents with Scalable Long-Term Memory (arXiv)](https://arxiv.org/html/2504.19413v1)
- [Zep: Temporal Knowledge Graph Architecture for Agent Memory (arXiv)](https://arxiv.org/html/2501.13956v1)
- [GraphMem: Self-Evolving Graph-Based Memory (ResearchGate)](https://www.researchgate.net/publication/398203328_GraphMem_Self-Evolving_Graph-Based_Memory_for_Production_AI_Agents)
- [SAGE: Self-Evolving Agentic Graph-Memory Engine (arXiv)](https://arxiv.org/html/2605.12061v1)
- [Multi-Agent Memory from a Computer Architecture Perspective (arXiv)](https://arxiv.org/html/2603.10062v1)
- [Mem0 Multi-Agent Memory Systems Blog](https://mem0.ai/blog/multi-agent-memory-systems)
- [AI Agent Memory Architectures 2026 (Zylos.ai)](https://zylos.ai/research/2026-04-05-ai-agent-memory-architectures-persistent-knowledge/)
- [Agent Memory Paper List (GitHub)](https://github.com/Shichun-Liu/Agent-Memory-Paper-List)
- [Agent Memory Layer Architecture Guide 2026 (Datapace)](https://datapace.ai/blog/ai-agent-memory-layer-architecture-guide-2026)

## Self-Improvement / Evolution
- [AlphaEvolve (Google DeepMind Blog)](https://deepmind.google/blog/alphaevolve-a-gemini-powered-coding-agent-for-designing-advanced-algorithms/)
- [AlphaEvolve Full Paper (PDF)](https://msu.dvaoblaka.ru/media/2025/05/68271bf34ef55_AlphaEvolve.pdf)
- [Self-Evolving Agents Cookbook (OpenAI)](https://developers.openai.com/cookbook/examples/partners/self_evolving_agents/autonomous_agent_retraining)
- [A Self-Improving Coding Agent (OpenReview)](https://openreview.net/pdf?id=rShJCyLsOr)
- [OpenAI Harness Engineering](https://openai.com/index/harness-engineering/)

## Multi-Agent Frameworks
- [Anthropic Multi-Agent Research System](https://www.anthropic.com/engineering/multi-agent-research-system)
- [Claude Managed Agent Memory Docs](https://platform.claude.com/docs/en/managed-agents/memory)
- [LangGraph Persistence Docs](https://docs.langchain.com/oss/python/langgraph/persistence)
- [LangGraph Long-Term Memory Guide (2026)](https://hindsight.vectorize.io/blog/2026/03/24/langgraph-longterm-memory)
- [LangGraph vs CrewAI vs AutoGen Comparison](https://dev.to/pockit_tools/langgraph-vs-crewai-vs-autogen-the-complete-multi-agent-ai-orchestration-guide-for-2026-2d63)
- [CrewAI Multi-Agent Framework](https://crewai.com/multi-agent-ai-framework-for-task-automation)
- [Microsoft AutoGen (AG2)](https://gurusup.com/blog/best-multi-agent-frameworks-2026)
- [MetaGPT (arXiv, ICLR 2024)](https://arxiv.org/abs/2308.00352)

## Foundational Cognitive Architectures
- [Stanford Generative Agents (arXiv)](https://arxiv.org/abs/2304.03442)
- [Complementary Learning Systems (McClelland et al., 1995)] — hippocampus→neocortex consolidation
- [BCM Theory (Bienenstock, Cooper, Munro, 1982)] — homeostatic plasticity
- [Predictive Coding (Friston, 2005)] — free energy minimization
- [MAP-Elites (Mouret & Clune, 2015)] — illumination of search space
- [Prioritized Experience Replay (Schaul et al., 2015)] — replay with TD-error priority
- [SuperMemo SM-2 (Wozniak, 1987)] — spaced repetition algorithm

---

> **END OF RESEARCH-SYNTHESIS MEGA-PROMPT**
>
> Claude 5: You now have the full picture of how the industry solves memory persistence and self-improvement, exactly where Octopus's gaps are (with file:line references), and a concrete 7-phase upgrade plan. Execute UP-1 through UP-5 + UP-7 autonomously (all safe, $0). UP-6 (LLM Mutation) requires explicit owner verdict.
>
> **برو.** (Go.)
