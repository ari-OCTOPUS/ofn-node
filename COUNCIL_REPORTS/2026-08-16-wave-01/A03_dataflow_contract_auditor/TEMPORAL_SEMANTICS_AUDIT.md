# TEMPORAL_SEMANTICS_AUDIT — A03 (2026-08-16)

Audit of `occurred_at`, `recorded_at`, `decided_at`/`decision_time`, `valid_from`,
`valid_to`, and the documented "live bitemporal ledger" claim.

## 1. Verdict on the bitemporal claim

**DOCUMENTED_NOT_IMPLEMENTED (as stated).** No ledger that is actually live implements
event-time vs record-time duality:

- **Genome ledger** (`07 - Knowledge/genome-system/ledger/ledger.jsonl`) — the artifact most
  often called "the ledger" — writes exactly one timestamp field `ts` (UTC ISO, set to now
  at append: `ledger/ledger.py:226,233-236`). Hash-chained (`prev`, `hash`), append-only,
  fsync'd — but **not bitemporal** (record-time only).
- **Structurally bitemporal stores exist but collapse in practice.** Four SQLite stores
  carry both `occurred_at` and `recorded_at` columns — `spine/event_spine.py:31,95,118`
  (state/spine/spine.db), `outcomes/outcome_store.py:33,98`, `outcomes/funnel_store.py:154,176`,
  `legs/consent_store.py:107-108,174` — but every current caller either omits `occurred_at`
  (publish falls back to `_utc_now_iso()` for both: event_spine.py:118) or sets it at event
  creation, so **the two columns are always equal**. Infrastructure yes, exercised no.
- The only in-repo mention of "bitemporal" outside code is a research note
  (`07 - Knowledge/_doctor-research/active-mutation-ledger.md:153`) citing the TOKI paper as
  a design aspiration.
- `decision_time`: zero hits. `effective_from`: zero hits. `decided_at` exists in several
  schemas (control_contracts.py:130,156; seed/evolution_gate.py:76+; 4d self_code.py:396).

## 2. Valid-time (closest real implementation)
`_ops/memory/memory_store.py` implements a genuine valid-time window: `valid_from`
(defaults to now, line 140), `valid_to` (TTL per namespace: self_knowledge 30d, semantic
90d, episodic 30d; procedural/owner_fact no expiry — gate.py `_TTL_DAYS`), supersede/retract
sets `valid_to=now` and `admission_state='RETRACTED'` (line 169); records never physically
deleted. Reads filter `valid_to` (search, line 199). This is bitemporal *validity*, not
event-vs-record time.

## 3. Temporal field inventory (selected)

| Field | Where | Producer semantics |
|---|---|---|
| `ts` (single) | genome ledger; chord-ledger; octopus_v3 IntentLedger; durable_journal (epoch float); agi2027_runtime ledgers; intervention-ledger | append time only |
| `timestamp`+`ts` | `_ops/state/events.jsonl` | same instant, duplicated |
| `occurred_at`+`recorded_at` | spine, outcomes, funnel, consent stores | always equal in practice (see §1) |
| `valid_from`/`valid_to` | memory_store | TTL validity window — real |
| `started_at`/`finished_at` | action-receipt.v1 (contracts.py:179-199) | local time `strftime` **without timezone** (goal_action_bridge.py:532) |
| `created_ts`/`transition_ts` | missions.jsonl (epoch floats) | creation vs state-transition times — distinct, good |
| `ts`+`evaluated_at_cycle` | cycle_verdict.v1 | verdict recorded in a *later* cycle than the one evaluated — correct delayed-evaluation semantics (observed live: cycle 2026-08-15#1 evaluated at 2026-08-16#1) |
| `decided_at` | control_contracts (checked against `proposal.created_at` — staleness enforcement), evolution_gate, self_code | decision time captured |
| `expires_at`/`expires_epoch`/TTL | owner_gate approvals (24h), approval_store jobs, memory TTL | expiry discipline present |
| `observed_at` | audit/generate_aeb, organism_manifest, world_discovery Freshness | observation stamps |
| `ingested_at` | legs/raw_store.py:142 | ingest time |
| none at all | `state/c6/research-ledger.jsonl` | **no temporal field** |

## 4. Risk findings

- **T-1 Ambiguous time (naive local timestamps).** action receipts use
  `time.strftime(...,time.localtime(now))` without offset (goal_action_bridge.py:532);
  4d `Event.timestamp`/`EventEnvelope` use naive `datetime.now().isoformat()`
  (events.py:137; control_plane/contracts.py:23). Mixed with UTC ISO (`+00:00`) fields
  elsewhere (genome `ts`) and epoch floats (missions). Cross-store joins must guess zones.
- **T-2 Future-use:** prereg rows carry `deadline_cycles` and verdicts are evaluated in a
  later cycle — sound. Memory `valid_from` defaults to write time; no scheduled-future
  facts found (no future-use violation observed).
- **T-3 Stale-use:** owner-gate approvals expire (24h) and `control_contracts` checks
  `decided_at` against `proposal.created_at`; the lead effector staleness gate refuses
  releasable effects older than 24h (default) with hard ceiling 72h and refuses on missing
  `release_ts` (effector_gate_bridge.py). Weak spot: ChromaDB/owner_recall/research_store
  reads have no freshness filter (see MEMORY_READ_WRITE_ASYMMETRY).
- **T-4 Causality inversion:** none observed — mission transitions are monotonic
  (`created_ts` ≤ `transition_ts`), verdict evaluation lags its cycle by design, and
  `get_summary` in 4d events.py parses ISO strings defensively (tz/DST comment, line 213-224).
- **T-5 Mutation of time-series "ledgers":** `state_guard._atomic_rewrite` rewrites
  unchained JSONL state files (quarantine sidecar exists for `reach/ledger.jsonl`,
  2026-08-08) — record-time history is editable for REPAIR_TARGETS files
  (BP-06). Hash-chained ledgers (genome/chord/IntentLedger) are not targeted.

## 5. Comparison with documentation
Docs/dashboards referring to "the live bitemporal ledger" should be read as: *live,
append-only, hash-chained (genome) + valid-time memory (MemoryStore)*. Event-time vs
record-time duality is schema-present (4 SQLite stores) but produces identical values
today. Any doc claiming bitemporality *in operation* is STALE/overstated.
