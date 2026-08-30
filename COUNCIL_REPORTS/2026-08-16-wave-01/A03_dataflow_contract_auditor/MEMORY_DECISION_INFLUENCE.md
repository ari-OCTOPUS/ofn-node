# MEMORY_DECISION_INFLUENCE — A03 (2026-08-16)

Question: is retrieved memory evidence-cited, ranked, freshness-checked, and capable of
influencing decisions — and can it ever *authorize* anything?

## 1. Where memory influences decisions (confirmed call sites)

### D-1 Mission veto (execution decision) — LIVE
`goal_action_bridge.run_for_cycle` step 2.5 (`_ops/goal_action_bridge.py:432-445`) calls
`retrieval_router.route` (flag `OCTOPUS_WIRE_MEMORY_DECISION=1`, armed 2026-07-31).
- `veto=true` → mission transitioned to `blocked`, ledger row appended, pipeline returns
  `MEMORY_VETO`. **Memory can close, never open** (`veto فقط می‌تواند ببندد` — line 265).
- Router error or absence = fail-soft continue ("memory is not authority; its absence is
  not a permit").
- Evidence-cited: yes — `memories_used` ids land in mission `input_refs` as `memory:<id>`
  (observed live: `missions.jsonl` 2026-08-16 rows carry six `memory:` refs).

### D-2 Advisory recall (no plan influence) — LIVE
`_recall_for_goal` (`goal_action_bridge.py:280-335`) runs **before** `prepare_records` so
the plan/receipt stay byte-identical with or without retrieval (documented invariant
`t_memory_is_never_authority_over_the_plan`, lines 395-399). Output = ids/trust/freshness
metadata only, journal-recorded. Decision impact: **none by design**.

### D-3 Write/skip control flow (4d) — CODE
`automation.py:436-441` + `memory_read_patch.py:192`: pending hypotheses are read and
compared (Jaccard + SequenceMatcher, threshold 0.90); a duplicate hypothesis write is
**skipped**. Memory content determines a write decision deterministically.

### D-4 Prompt influence (4d brain) — CODE
`nodes.py:41,48,85-90`, `graph.py:214-221`, `meta_research.py:447-469`: vault RAG text and
past experiment metrics are injected verbatim (truncated) into LLM prompts. Influence is
epistemic only — the 4d brain's only actuators are `outputs/` writes behind
`guardrails.assert_safe_write` and LangChain tools that are read/compute-only
(`4d_system/brain/tools.py::ALL_TOOLS`).

### D-5 Owner-facing citations — CODE
`owner_recall.recall_for_owner_ask` returns cite-only facts with `source_path`/`mkey`;
`may_authorize` hard-coded False (`_ops/memory/owner_recall.py:23-30`). Injected into
collaborator LLM context (`collab_model_adapter.py:213-216`) and appended to owner replies
with citation paths (`collaborator.py:398-414`).

## 2. Ranking / freshness / citation per store

| Store | Ranked | Freshness | Evidence-cited |
|---|---|---|---|
| _ops MemoryStore.search | bm25 + salience composite | `valid_to` expiry + ADMITTED filter | memory_id + trust class |
| retrieval_router | cascading exact>episodic>procedural | inherited | as_memories_used() refs |
| vault_bridge (flag default off in bridge; store flag on) | relevance sort | **none** | memory_id/source/relevance |
| 4d vectorstore.search_vault | relevance sort | **none** | title+relevance in tool output |
| owner_recall | probe-order | **none** | source_path per fact |
| research_store | plain SQL | **none** | n/a |

Only freshness machinery on the 4d side is `memory_read_patch.split_stale` (14-day cutoff).

## 3. Authority boundaries (verified in code)
- MemoryGate: model/agent output can never commit `procedural`/`owner_fact`; `self_knowledge`
  is permanently ADVISORY (`_ops/memory/gate.py` docstring + COMMIT_RULES).
- Mission pipeline: memory veto only narrows; plan deterministic without it.
- Owner recall: cite-only, never authorizing.
- Weakest link: BP-08 — ungated LLM→hypothesis writes on the 4d side can poison future
  prompts (epistemic loop), though they cannot reach execution authority.

**Conclusion:** memory demonstrably influences decisions (veto, dedup, prompts) and is
citation-bearing; it is structurally barred from granting authority on every gated path
audited. Two patch points (`patch_introspect`, `patch_conclude` in
`4d_system/brain/memory_read_patch.py:130,154`) still use only the **count** of retrieved
rows — content does not yet flow there (partial wiring).
