# MEMORY_READ_WRITE_ASYMMETRY — A03 (2026-08-16)

OCTOPUS has **two disjoint memory systems** with different admission discipline. Reads are
broad; disciplined writes exist only on the `_ops` side.

---

## 1. Write paths (who may write what)

### `_ops` side — gated
| Writer | Gate | Store | Evidence |
|---|---|---|---|
| `memory/gate.py::MemoryGate.submit` | FSM classify→scrub(guard)→dedupe→grade→TTL→commit; model/agent can only **propose** procedural/owner_fact; self_knowledge always ADVISORY; raw secret/PII regex-rejected; behind `OCTOPUS_WIRE_MEMORY_GATE=1` (default off = no-op) | MemoryStore (SQLite+FTS5) | `_ops/memory/gate.py:1-50,167` |
| `goal_action_bridge.consolidate_new_verdicts` | MemoryGate + idempotent cycle marker; source=deterministic; outcome-bound episodic rows | MemoryStore | `_ops/goal_action_bridge.py:565-637` |
| `self_loop_ingest` | JSONL trail (separate store) | `_ops/memory/self_loop_ingest.py` |

### `4d_system` side — ungated
| Writer | Gate | Store | Evidence |
|---|---|---|---|
| `brain/tools.py::generate_hypothesis` | **none** — raw LLM reply persisted verbatim | 4d SQLite experiments db | `4d_system/brain/tools.py:149-154` |
| `brain/automation.py` (hypotheses/experiments/reflections) | dedupe-only (read-before-write patch) | 4d SQLite db | `4d_system/brain/automation.py:436-456` |
| `brain/autoloop.py` patterns | dedup check then save | research_store SQLite | `4d_system/brain/autoloop.py:279` |
| `memory/vectorstore.py` | rebuild scripts | ChromaDB vault index | `4d_system/memory/vectorstore.py` |

**Asymmetry:** the _ops store enforces admission (trust classes, TTL, owner-only commits);
the 4d store accepts anything its own loops write, including raw model output (BP-08).

## 2. Read paths (who reads what)

| Reader | Store read | Decision impact | Evidence |
|---|---|---|---|
| `retrieval_router.route` (flag ON) | MemoryStore exact/episodic/procedural/semantic + vault_bridge | **veto-only** over missions; evidence attached to `input_refs` | `_ops/memory/retrieval_router.py:42-103`; `_ops/goal_action_bridge.py:434-445` |
| `goal_action_bridge._recall_for_goal` (flag ON) | MemoryStore FTS (episodic/semantic) | observability only — recorded in journal, plan byte-identical with/without it (invariant `t_memory_is_never_authority_over_the_plan`) | `_ops/goal_action_bridge.py:280-335,395-399` |
| LangGraph brain nodes/graph | ChromaDB vault + 4d experiments | verbatim into LLM prompts (truncated 400/200/800 chars) | `4d_system/brain/nodes.py:41,48,85-90,143-154,218-232`; `graph.py:214-221` |
| `meta_research` | 4d experiments | past metrics into LLM synthesis prompt | `4d_system/brain/meta_research.py:447-469` |
| `automation` dedup patch | pending hypotheses | **write/skip control flow** (Jaccard+SequenceMatcher ≥0.90 = duplicate) | `4d_system/brain/automation.py:436-441`; `memory_read_patch.py:192` |
| `owner_recall` | MemoryStore episodic/self-loop/consolidation | cite-only facts into owner-facing LLM context; `may_authorize` always False | `_ops/memory/owner_recall.py:23-30` |
| `unified_context.assemble` | owner_recall + pulse/equations/shadow | context bus for collaborator | `_ops/memory/unified_context.py:91-92,185` |

## 3. Read/write ratio observations
- `MemoryStore.get`/`search` retrieval is invoked by decision-time, owner-facing, and seed paths — reads are genuinely wired into autonomous loops (mission pipeline + LangGraph brain), not dead helpers.
- Rank/freshness: `MemoryStore.search` filters `admission_state='ADMITTED'` AND `valid_to` expiry (bitemporal-style validity) and ranks bm25−salience. ChromaDB `search_vault`, `owner_recall`, and `research_store` have **no freshness filter**; the only staleness logic anywhere is `memory_read_patch.split_stale` (14-day cutoff, 4d side only).
- Evidence citation: `_ops` reads return `memory_id`/`source_path` citations (mission rows carry `memory:<id>` refs — observed live in `missions.jsonl` `input_refs`). 4d prompt injection truncates but does cite `[i] title (relevance)`.

## 4. Net verdict
Write discipline is asymmetric (gated in _ops, ungated in 4d). Read usage is real and
audited; memory authority is explicitly veto-only by construction on the execution path.
