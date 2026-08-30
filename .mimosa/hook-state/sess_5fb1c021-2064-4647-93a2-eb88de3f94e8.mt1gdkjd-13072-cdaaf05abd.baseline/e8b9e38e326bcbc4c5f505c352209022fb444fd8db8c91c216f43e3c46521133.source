# C4 — ONE EVENT SPINE / ARCHITECTURAL CONSOLIDATION — REPORT (2026-07-23)

> Goal: remove duplicate truth; every bus/store is SoT | substrate | projection | cache | archive-candidate.
> Method: evidence-first (read-only cartographer, file:line) → shadow/compat-flag consolidation → parity → propose-only archive.
> Base: C2 complete. Commit: `b557984`.

## 1–3. Producer/consumer graph + per-channel verdict (evidence)

| channel | artifact | producers | flag | **verdict** | strongest evidence |
|---|---|---|---|---|---|
| EventSpine | spine.db (2 rows) | verdict_recorder, wiring, spine_adapters, boot_certificate, self_knowledge, ziman | WIRE_SPINE=1 | **projection / cross-domain index** | `event_spine.py:7` "sits beside the real ledgers, filled by dual_write" |
| outcomes | outcomes.db | verdict/lead/proposal recorders | VERDICT_OUTCOME | **substrate (SoT decisions)** | `outcome_store.py:3` durable+replayable; metrics rebuilt from rows |
| genome ledger | ledger.jsonl | ~20 via opslib.ledger_note | core | **substrate (SoT $/genome)** | `ledger.py:3` "ONLY shared memory… never mutated… hash chain" |
| chrono | chrono.db | pacemaker/effector | core | **cache** | `unified_bus.py:40` "chrono = runtime cache (reconstructable)" |
| unified_bus | ledger+chrono | live_loop, watchdog, tracer | WIRE_UNIFIED=off | **substrate (dormant)** | writer to ledger+checkpoint; flag off → None |
| events.py | events.jsonl (495 KB) | ~15 (cortex/heart/…) | none | **projection (independent)** | busiest stream; dashboard read-model |
| approvals | approvals.json | center | none | **SoT (UI state)** | single-writer invariant |
| review_bus | reviews/ (frozen) | 0 live callers | none | **archive-candidate (writer)** | `submit_review` 0 non-test callers |
| chord/ | (never created) | doctor (flag off) | CHORD_SHADOW=off | **archive-candidate** | no ledger file → never ran live |
| memory | memory.db (absent) | wiring (flag off) | MEMORY_GATE=off | **dormant** (C3 will arm) | no db on disk |
| durable_journal | run-journal.jsonl | doctor + recovery (C2-D) | none | **substrate (thin)** | now 2 live callers (orphan cured) |

## 4–5. One producer surface (the "single write path")
- **`spine_adapters.emit_event`** is now the single generic spine producer (validates via `publish`, sanitizes, fail-soft, idempotent). The 2 direct `event_spine.dual_write` bypasses (`verdict_recorder.py`, `wiring.py`) route through it behind **`OCTOPUS_SPINE_VIA_ADAPTER`** (default `0` = unchanged behavior; `1` = single surface). Old path untouched until soak (mission rule). Independent parallel emit is now **compat-quarantined**.

## 6. Refuted with evidence (mission step 6 NOT executed — correctly)
- events.py/review_bus → spine projection is **impossible**: `event_spine.py:61-74` sanitizer strips exactly their free-text (`summary`, `next_action`, `verdict_note`, full review `payload`). A projection → blind dashboard. They **stay independent projections** (decision D-O4). This is the honest-grounding call: I did not execute a plan the evidence invalidates.

## 7. Parity (byte-identical)
- `test_spine_single_surface::t_parity_direct_vs_adapter`: same input → identical row across all columns except the two wall-clock timestamps (both default to now), incl. **same `event_id` and `idempotency_key`** → replay/dedup identical. 5/5 C4 tests pass.

## 8. Compat quench (staged, not yet)
- The compat flag is the quench switch. It stays `0` until a soak window on the single surface confirms parity live; then flip to `1` (and eventually remove the old branch). Rollback = flip back to `0`.

## 9–10. Schema contract + provenance
- `validate_row` pins the 10-field envelope (event_id, idempotency_key, event_type, domain, occurred_at, recorded_at, producer, correlation_id, trust, schema_version) + valid event_type/trust. `publish` defaults `producer→'unknown'` → **provenance never null**. HLC/occurred_at, correlation_id, source(producer), schema_version all enforced.

## OVERLAP fixes
- **OVERLAP-0** (watchdog either/or): alerts now **always** written to `events.jsonl` (+ unified_bus if present) → never vanish when the bus arms.
- **OVERLAP-A/B/C** (spine shadow-copies outcomes/ledger): reframed by D-O3 — spine is an *index*, not a competing SoT; the single-surface + compat flag is the mechanism to converge it without a big-bang rewrite.

## 11–12. Ownerless files + Archive Packet
- [ARCHIVE-PACKET-C4.md](ARCHIVE-PACKET-C4.md): propose-only (`git mv`, never `rm`). Archive-candidates (0 live callers): `chord/`, `vault_updater.py` + `_apply.py` (+ `_gate.py` iff both go), stale `reviews/` **writer** (files kept — live reader). Root cruft: empty `2026-07-21`, stray `F:backup` dir, `state/_wtest.py`, `_probe_write_test.txt`. **Nothing deleted; awaits owner.**
- Honesty fix applied: `durable_journal.py` stale "ORPHAN" docstring corrected (now wired).

## 13. Tests
- 5/5 new (`test_spine_single_surface.py`); spine/verdict/lead/paper regress green; **full sandbox suite 269/269** (one cardiac-allometry timing flake, confirmed 3/3 green standalone, unrelated to spine).

## 14. Decision Log
- D-O3…D-O8 in [DECISION-LOG-SOT.md](DECISION-LOG-SOT.md).

## VERDICT: C4 CONSOLIDATION DONE (governance + single-surface + parity + archive-proposal)
one SoT per knowledge type (roles disambiguated) · zero ownerless producers (durable_journal cured) · independent parallel emit compat-quarantined · replay deterministic (parity) · UI = independent projections (evidence) · rollback = flip `OCTOPUS_SPINE_VIA_ADAPTER=0`.

## Owner decisions
1. **Archive Packet** — approve moving group A (dead vault_updater*/chord) + group C (root cruft) to `_archive/`? (propose-only until yes)
2. **Compat flip schedule** — when to soak `OCTOPUS_SPINE_VIA_ADAPTER=1` and then retire the old dual_write branch.
