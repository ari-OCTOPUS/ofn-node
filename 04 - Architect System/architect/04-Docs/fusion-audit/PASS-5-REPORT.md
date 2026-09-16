---
type: reference
status: done
tags: [fusion-audit]
created: 2026-07-03
updated: 2026-07-03
---

# PASS 5 — Memory Architect: State & Memory Architecture

Role: describe the actual memory/state architecture (schema, context passing, persisted vs
reconstructed); compare to episodic/semantic stores, compaction, retrieval-before-generation; find
where state can silently diverge from the source of truth.

## Actual architecture (evidence)
There is **no database**. All persistent state is flat files:

| Store | File | Integrity model | Lifetime |
|---|---|---|---|
| Main audit | `logs/audit.jsonl` | SHA-256 hash chain, **unkeyed**, 16-hex truncated (`src/tracing.py:53-55`) | persisted, append |
| Kernel audit | `logs/igk_state/audit.jsonl` | **HMAC-SHA256** keyed (`igk/kernel.py:62-84`) | persisted, append |
| Prompt store | `prompts.json` | none (JSON, active-pointer + version list, `src/prompt_store.py`) | persisted |
| Grounding anchor | `igk/held_out.json` **and** `logs/igk_state/held_out.json` | none | persisted (duplicated) |
| Budget ledger | in-memory `BudgetLedger` (`src/budget.py:26-66`) | none | per-run only |
| Nonce set / chain heads | in-memory `Kernel._used_nonces`, `_seq`, `_prev` (`igk/kernel.py:38-39`) | none | per-run only |

Context passing between agents is **by function argument only** — `findings: str` →
`analysis: str` (`src/agents.py:56-69`, `src/orchestrator.py:87-100`). There is **no** episodic or
semantic memory, **no** retrieval-before-generation, **no** context compaction, and **no** shared
working memory. Each run is stateless apart from append-only logging and prompt versioning. This is
appropriate for the MVP scale; the point is only that the "memory system" the task asks about is a
log, not a store. [Certain]

## Findings

### P5-01 [Medium] Two audit logs form two disjoint chains with different integrity guarantees
The signed kernel chain (`logs/igk_state/audit.jsonl`) and the unsigned main chain
(`logs/audit.jsonl`) share **no** cross-reference — no common sequence, no hash linking one to the
other. Reconstructing a single run timeline requires merging the two by wall-clock timestamp, which
is unauthenticated. Events that matter most (human verdict vs. actuation) live in *different* logs
with *different* trust levels. The "source of truth" for what happened is therefore split and only
partially signed. [Certain]

### P5-02 [Medium] Single-writer assumption on the audit chain is undocumented and violable
`AuditLog` caches `_prev_hash` in memory at construction (`src/tracing.py:24,33-42`) and appends.
Two `AuditLog` instances writing the same file interleave and break the chain: `run.py` /
orchestrator create one instance, while `self_update.py` creates its own (`self_update.py:64`,
`AuditLog()`), both defaulting to `logs/audit.jsonl` (`config.py:52`). Concurrent (or even
interleaved-in-time) runs corrupt `verify_chain()`. The same in-memory-head pattern exists in the
kernel (`igk/kernel.py:39`). No lock, no single-writer guard, no note. [Probable]

### P5-03 [Medium] The grounding anchor is duplicated — two sources of truth that can diverge
`igk/held_out.json` and `logs/igk_state/held_out.json` currently hold identical content, but the
kernel reads from the state dir (`igk/kernel.py:56-60`) while several tests copy `igk/held_out.json`
(`igk/test_redteam.py:18-20`, `test_failures.py:28-29`). Editing one and not the other silently
changes what "grounded" means depending on which entry point runs. There is no canonical loader.
[Certain]

### P5-04 [Low/Medium] Per-run in-memory state cannot be reconciled against the logs after a crash
Budget totals and used-nonces exist only in memory. If a run is killed mid-flight, the persisted
audit shows partial events but the authoritative budget/nonce state is gone; a restart begins with
`_used_nonces = {}` (`igk/kernel.py:38`). Replay protection is bounded only by the 30s permit expiry
(`igk/kernel.py:112`) across restarts. No divergence within a run; the gap is cross-run
reconstruction. [Certain]

### P5-05 [Low] Prompt-store rollback has no floor validation
`PromptStore.rollback` merely decrements the active pointer (`src/prompt_store.py:74-81`) with no
check that the reverted version is safe/valid; and `self_update` can auto-keep a "provisional" new
version in MOCK (`src/evals.py:122-141`, `self_update.py:97-108`). Divergence between "active prompt"
and "best-verified prompt" is possible but low-impact (guarded by the allow-list on write). [Certain]

## Comparison to target patterns
- Episodic/semantic stores: absent. For a research assistant that could benefit from
  retrieval-before-generation, findings are neither stored nor retrieved across runs. [Certain]
- Compaction: absent (no long context maintained). [Certain]
- Single-source-of-truth discipline: **violated** at three points (P5-01 dual logs, P5-03 dual
  anchor, plus mutable `config` globals from Pass 1 P1-07). [Certain]

## Gaps I could not verify
- Behavior under real concurrency (not exercised by the test suite; all tests are single-threaded).
