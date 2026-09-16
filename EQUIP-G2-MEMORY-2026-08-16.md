---
schema: equip-evidence.v1
group: G2
wave: A1
title: EQUIP G2 — Trusted Read-Write Memory Loop
date: 2026-08-16
verdict: CONDITIONAL PASS
implementer: agent-1-wave-A1
branch: equip/g2-memory-20260816
---

# EQUIP G2 — Trusted Read-Write Memory Loop — Evidence Report

## Executive Verdict: CONDITIONAL PASS

The vertical slice closes the Trusted Read-Write Memory Loop gap with three new
modules and a comprehensive test suite. All 49 new tests pass. No regressions in
existing tests. The acceptance scenario (save -> restart -> retrieve -> conclude ->
verify) is verified.

**Conditional** because: the modules are bridging/wrapping layers that wire into
existing infrastructure but are not yet called from the live `automation.py` loop
(that wiring requires owner approval since it changes the production brain path).

## Discovered Architecture (Memory System Topology)

### Source of Truth Map

| Memory Type | Store | Path | Write Gate | Read Path |
|---|---|---|---|---|
| Short-term (session) | In-process dict + JSONL | `_ops/memory/session_memory.py` | N/A (temp) | `recent()` / `as_context_block()` |
| Episodic (graded) | MemoryStore (SQLite + FTS5) | `_ops/memory/memory_store.py` | `_ops/memory/gate.py` (MemoryGate) | `retrieval_router.py` → `store.search()` |
| Semantic (graded) | MemoryStore (SQLite + FTS5) | `_ops/memory/memory_store.py` | `_ops/memory/gate.py` | `retrieval_router.py` → `vault_bridge.py` (ChromaDB) |
| Procedural (graded) | MemoryStore (SQLite + FTS5) | `_ops/memory/memory_store.py` | `_ops/memory/gate.py` | `retrieval_router.py` → `store.get()` |
| Owner Fact (graded) | MemoryStore (SQLite + FTS5) | `_ops/memory/memory_store.py` | `_ops/memory/gate.py` (owner_only) | `retrieval_router.py` → exact veto |
| Self Knowledge (graded) | MemoryStore (SQLite + FTS5) | `_ops/memory/memory_store.py` | `_ops/memory/gate.py` (ADVISORY) | `unified_context.py` |
| Hypothesis (4d brain) | SQLite experiments DB | `4d_system/memory/store.py` | `hypothesis_policy.py` (R16) | `memory_read_patch.py` |
| Vault (canonical) | Obsidian Markdown | `F:\backup\4D-Vault\` | N/A (write via Obsidian) | `vault_bridge.py` → ChromaDB |

### Key Finding: Two Separate Memory Stores

The vault has TWO independent SQLite-backed memory systems that were previously
disconnected:

1. **MemoryStore** (`_ops/memory/memory_store.py`) — graded, trust-stamped, has
   MemoryGate (gate.py), FTS5/BM25 retrieval, admission states, TTL, supersede.
   This is the "decision-time memory" used by the OCTOPUS organism layer.

2. **Experiments DB** (`4d_system/memory/store.py`) — the 4d brain's hypothesis
   and experiment store. Has R16 hypothesis_policy (family dedup, daily cap,
   dormancy). NO gate enforcement. This is the "creative/research memory."

**Gap closed by this EQUIP wave:** The Write Gate Enforcer now provides a
gate-like enforcement layer that can be applied to ANY write path, including
the 4d brain's hypothesis writes that previously bypassed all gating.

## Implemented Capabilities

### 1. Write Gate Enforcer (`_ops/memory/write_gate_enforcer.py`)

- Content hash (SHA-256) computation on every write
- Source classification: trusted (owner, deterministic, tg_center) vs untrusted
  (llm, tool, web, model:auto) — unknown defaults to untrusted (fail-closed)
- Provenance stamping: schema_version, source, source_class, writer_agent,
  model, evidence_ref, timestamp
- Quarantine: untrusted writes are quarantined (admission_state=QUARANTINED),
  not directly committed
- Secret/PII detection: same regex as gate.py for consistency
- Append-only audit trail (JSONL) for every evaluation (commit/quarantine/reject)
- Kill-switch compatible: no side effects beyond audit file
- Contradiction checker injection point for pipeline integration

### 2. Contradiction Radar (`_ops/memory/contradiction_radar.py`)

- Detects contradictions between new memory and existing memories
- Hybrid retrieval: works with MemoryStore (FTS5/BM25) and raw memory lists
- Multilingual negation detection (English + Persian patterns)
- Agreement pattern suppression (reduces false positives)
- Keyword overlap analysis (Jaccard similarity threshold)
- Confidence calibration (0.6 minimum, max 0.95)
- **Never auto-deletes or auto-resolves** — flags only, per spec
- Deduplication by contradicting_memory_id

### 3. Evidence Chain (`_ops/memory/evidence_chain.py`)

- Tracks SHA-256 content hash through lifecycle: write -> readback -> conclude
- SQLite-backed (WAL mode) for persistence across process restarts
- Full chain verification: all hashes must be identical
- Tamper detection: any divergence in hashes is immediately detected
- Static verification method for inline checks without DB
- Multiple hypothesis chains are independent

## Changed Files (this branch only)

| File | Action | Lines |
|---|---|---|
| `_ops/memory/write_gate_enforcer.py` | NEW | ~260 |
| `_ops/memory/contradiction_radar.py` | NEW | ~250 |
| `_ops/memory/evidence_chain.py` | NEW | ~220 |
| `_ops/tests/test_g2_trusted_memory_loop.py` | NEW | ~700 |

**No existing files were modified.** No migrations. No new dependencies.

## Tests + Exact Results

### New Tests: 49/49 PASS

```
test_g2_trusted_memory_loop: 49/49 passed (0 failures, 0 errors)
```

Breakdown:
- **Section A — Write Gate Enforcer:** 16/16 pass
  (trusted/untrusted/reject/audit/hash/idempotent/provenance/readback)
- **Section B — Contradiction Radar:** 8/8 pass
  (negation/Persian/agreement/FTS5/unified/serialization/empty)
- **Section C — Evidence Chain:** 11/11 pass
  (write/readback/conclude/verify/tamper/restart/static/multi-hypothesis)
- **Section D — Integration:** 5/5 pass
  (full loop/ungated audit/MemoryStore/contradiction+store/restart)
- **Section E — Security:** 9/9 pass
  (secrets/impersonation/forged provenance/unicode/tamper/audit resilience)

### Existing Tests: No Regressions

| Test Suite | Result | Count |
|---|---|---|
| `test_memory_gate.py` | OK | 10/10 |
| `test_memory_read_seam.py` | OK | 5/5 |
| `test_octopus_mcp_search.py` | OK | 4/4 |
| `test_memory_loop_c012.py` (pytest) | OK | 13/13 |

**Note on baseline:** The launcher mentioned `test_octopus_mcp_search.py` as having a
pre-existing failure in `t_empty_query_is_handled`. This test now passes (4/4),
suggesting the fix was applied in working-tree edits by the owner before this wave.

## Security Scan Findings

| Severity | Finding | Status |
|---|---|---|
| LOW | `_SECRET_RX` pattern definition references "SECRET", "TOKEN" — these are detector patterns, not actual secrets | SAFE — expected |
| LOW | Test fixture strings contain sample secret patterns — these are test data for verifying detection | SAFE — expected |
| — | No eval/exec/subprocess/os.system/pickle/yaml.load found | CLEAN |
| — | No hardcoded credentials or PII in production code | CLEAN |
| — | All SQLite connections use timeout parameter | CLEAN |
| — | stdlib-only, no network, $0 cost | CLEAN |

### Memory-Specific Security Checks

| Check | Result |
|---|---|
| Write-only memory (unreachable retrieval) | N/A — retrieval exists for both stores |
| Memory poisoning | Mitigated: untrusted writes quarantined, content hash verified |
| Forged provenance | Mitigated: source_class based on source field, not writer_agent claim |
| Cross-user leakage | N/A — single-tenant personal vault |
| Duplicate records | Mitigated: content_hash + dedup in both gate and enforcer |
| Schema drift | Mitigated: schema_version field in all records |
| Vector/metadata inconsistency | N/A — no vector DB introduced |
| Deletion/revocation failure | Mitigated: append-only, RETRACTED state, no physical delete |

## Unresolved Risks

1. **Not yet wired to production brain path**: The Write Gate Enforcer is a bridge
   module. To enforce it in the live `automation.py` loop, `_job_create()` would
   need to call `stamp_hypothesis_with_gate()` after `save_hypothesis()`. This
   requires owner approval since it changes the production decision path.

2. **Contradiction radar is pattern-based only**: The current implementation uses
   regex negation detection + keyword Jaccard. It does not use semantic
   embeddings for contradiction detection. This is intentional (no new vector DB
   per DO NOT instructions) but means some semantic contradictions may be missed.

3. **Evidence chain DB is separate from hypotheses DB**: The evidence chain uses
   its own SQLite database. Integration with the existing 4d_experiments.db would
   require schema migration (not done in this wave to avoid touching live state).

4. **No quarantine resolution workflow**: Quarantined writes are flagged but there
   is no automated or manual workflow to promote them. This is by design (owner
   must approve) but means quarantined writes will accumulate.

## Rollback Plan

All changes are additive (new files only). No existing files were modified.
Rollback = delete the 4 new files and revert the 2 commits on this branch.

```bash
git checkout equip/g2-memory-20260816
git revert f236648 ca8be9a  # or: git reset --hard 8b7e6e8
```

No migrations, no dependency changes, no database schema changes.

## Reproduce Commands

```bash
# Create branch (already done)
git checkout -b equip/g2-memory-20260816

# Run new tests
cd F:\backup
PYTHONIOENCODING=utf-8 python -X utf8 _ops/tests/test_g2_trusted_memory_loop.py

# Run existing memory tests (regression check)
PYTHONIOENCODING=utf-8 python -X utf8 _ops/tests/test_memory_gate.py
PYTHONIOENCODING=utf-8 python -X utf8 _ops/tests/test_memory_read_seam.py

# Run 4d memory loop tests (pytest required)
cd 4d_system && python -m pytest tests/test_memory_loop_c012.py -v

# Smoke test individual modules
python -X utf8 _ops/memory/write_gate_enforcer.py
python -X utf8 _ops/memory/contradiction_radar.py
python -X utf8 _ops/memory/evidence_chain.py
```

## Evidence Paths

- New modules: `_ops/memory/write_gate_enforcer.py`, `contradiction_radar.py`, `evidence_chain.py`
- Test suite: `_ops/tests/test_g2_trusted_memory_loop.py`
- This evidence: `06-EVIDENCE/EQUIP-G2-MEMORY-2026-08-16.md`
- Branch: `equip/g2-memory-20260816`

## Recommended Next Step

1. Owner reviews this evidence and the conditional pass rationale.
2. If approved, wire `stamp_hypothesis_with_gate()` into `automation.py::_job_create()`
   (owner decision required — touches production brain path).
3. Pass to Group 6 (Observability) per the EQUIP sequence: 2 -> 6 -> 7 -> 8 -> 1 -> 3 -> 4 -> 5 -> 9 -> 10.
