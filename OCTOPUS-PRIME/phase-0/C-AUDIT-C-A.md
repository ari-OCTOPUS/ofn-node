# C-AUDIT-C-A

## summary
Candidate _ops/chrono.py holds gated_effect at schema v1: 7 columns (effect_id, kind, payload_ref, created_beat, created_ts, release_ref, status) defined in the _DDL string at lines 205-214, with a status CHECK limited to ('pending','releasable','settled','refused'). The only schema-version mechanism is `PRAGMA user_version = 1` at line 227, embedded in _DDL and executed UNCONDITIONALLY on every ChronoDB construction; there is no meta table. ChronoDB.__init__ (lines 232-239) runs NO migration — it connects, sets WAL, and calls executescript(_DDL); every CREATE is `IF NOT EXISTS`, so editing _DDL alone can never add columns to an existing DB. All 10 SQL statements touching gated_effect live inside chrono.py (request/release/settle/sweep/status). The proven prototype's v2 adds 10 binding columns via table-recreate and bumps user_version to 2, guarded by `if ver >= 2: return`. Two hard blockers for the port: (1) the unconditional `PRAGMA user_version = 1` at line 227 will reset the version to 1 on every ChronoDB() after any migrate_up bumps it to 2, defeating the version guard and re-triggering migration; (2) because __init__ has no migration call and _DDL uses IF NOT EXISTS, the port must add an explicit migrate_up invocation — editing the DDL string is insufficient. Of the 15 v2-target columns named in the brief, ZERO exist today; only 10 of them are actually implemented in the proven prototype (content_hash, action_kind, target_ref, idempotency_key, proposal_id, mission_id, approval_id, approved_by, approved_at, expires_at). The remaining 5 (effect_class, settled_at, external_receipt_ref, failure_reason, schema_version) have NO proven design in chrono_migration_prototype.py; note also the prototype tracks version via PRAGMA user_version, not a schema_version COLUMN, so a schema_version column conflicts with the proven mechanism. External callers only read the `status` column (COUNT/GROUP BY), so a binding-column-additive table-recreate is caller-safe provided the 7 v1 columns are preserved.

## findings
- **[info]** Current gated_effect DDL defines exactly 7 columns (effect_id, kind, payload_ref, created_beat, created_ts, release_ref, status) with a status CHECK of ('pending','releasable','settled','refused'). All 15 v2-target columns from the brief are MISSING.
  - ev: `_ops/chrono.py:205-214`
  - port: Add the v2 binding columns via table-recreate (SQLite cannot ALTER a CHECK), preserving all 7 v1 columns so existing callers/rows survive.
- **[info]** The only schema-version mechanism is `PRAGMA user_version = 1` embedded in the _DDL string; there is no meta/version table anywhere in the DDL.
  - ev: `_ops/chrono.py:227`
  - port: Adopt the prototype's PRAGMA user_version discipline (migrate_up guards on `if ver >= 2: return` and sets user_version=2). Do NOT introduce a separate schema_version column — it conflicts with the proven user_version mechanism.
- **[critical]** BLOCKER: `PRAGMA user_version = 1` sits inside _DDL and executescript(_DDL) runs on EVERY ChronoDB.__init__. After a migrate_up bumps user_version to 2, the next ChronoDB() construction re-runs _DDL and resets user_version back to 1, defeating the prototype's `if ver >= 2: return` guard and re-triggering migration on every open.
  - ev: `_ops/chrono.py:227`
  - port: Remove the `PRAGMA user_version = 1` line from _DDL (or make version-setting happen only inside a conditional migration runner) before wiring migrate_up, so the version is never clobbered back to 1.
- **[critical]** BLOCKER: ChronoDB.__init__ runs no migration — it only calls executescript(_DDL), and every table uses `CREATE TABLE IF NOT EXISTS`. On an existing v1 chrono.db, IF NOT EXISTS is a no-op, so adding columns to the _DDL string alone will NEVER alter the live table.
  - ev: `_ops/chrono.py:238`
  - port: Add an explicit migrate_up(self._con) call inside __init__ after executescript (mirroring prototype migrate_up at chrono_migration_prototype.py:48-67). Editing the _DDL string is insufficient for existing DBs.
- **[high]** INSERT path (EffectorGate.request) writes only the 7 v1 columns; it does not populate content_hash/action_kind/target_ref/idempotency_key/proposal_id/mission_id.
  - ev: `_ops/chrono.py:384-386`
  - port: Extend request() signature and this INSERT to populate v2 binding columns (compute content_hash, accept action_kind/target_ref/idempotency_key/proposal_id/mission_id), matching prototype request_effect at chrono_migration_prototype.py:70-85.
- **[high]** Batch release (release_gated_effects) sets status='releasable' for any pending row whose kind is in the money allowlist, with no content_hash/action_kind/target_ref binding check — the exact per-effect authorization weakness the prototype closes.
  - ev: `_ops/chrono.py:402-404`
  - port: Port the prototype's release_effect binding verification (chrono_migration_prototype.py:93-111): match content_hash/action_kind/target_ref against the approval before releasing, and record approval_id/approved_by/approved_at.
- **[medium]** release_one already does an id-bound single-row release but writes only release_ref; it records none of the v2 approval-provenance columns (approval_id, approved_by, approved_at).
  - ev: `_ops/chrono.py:418-419`
  - port: Extend this UPDATE to also set approval_id/approved_by/approved_at from the approval entry once those columns exist.
- **[medium]** settle() reads (status, release_ref) and transitions releasable->settled; it does not record settled_at, external_receipt_ref, or failure_reason (three of the brief's target columns).
  - ev: `_ops/chrono.py:443-452`
  - port: These 3 columns are NOT in the proven prototype (prototype v2 adds only 10 binding columns, none for settlement). Flag to the single writer: no proven design exists — do not invent settlement columns from this port; keep settle() as-is unless a separate ratified design is supplied.
- **[info]** Full gated_effect SQL inventory in chrono.py (all reads/writes, no external file issues direct DML): INSERT request()=384-386; UPDATE batch release=402-404; UPDATE release_one=418-419; SELECT status_of=431-432; UPDATE refused(kill)=439-440; SELECT status,release_ref settle=443-444; UPDATE settled=449-450; SELECT sweep=461-463; UPDATE refused(sweep)=466; SELECT COUNT status()=751-752.
  - ev: `_ops/chrono.py:384-752`
  - port: Treat chrono.py as the exclusive owner of gated_effect DML (confirmed by test_effector_gate_bridge.py:148). Any migration only needs to keep these 10 statements valid; the widened status CHECK must still admit the 4 existing statuses used here.
- **[medium]** External callers read gated_effect ONLY via the status column (COUNT/GROUP BY status) or the gate API — none SELECT v2 columns — so an additive table-recreate that preserves the 7 v1 columns will not break callers.
  - ev: `_ops/export_status.py:105`
  - port: Safe to recreate the table. But note: widening the status CHECK to include NEEDS_OWNER_REVIEW/LEGACY_UNBOUND (prototype line 42) makes new buckets appear in GROUP BY status readers (export_status.py:105, cockpit_readmodel.py:337); verify those dashboards tolerate unknown status values.
- **[high]** Of the 15 brief-target columns, only 10 are implemented in the proven 13/13 prototype (V2_COLUMNS). The 5 extras — effect_class, settled_at, external_receipt_ref, failure_reason, schema_version — appear nowhere in chrono_migration_prototype.py's v2 table.
  - ev: `OCTOPUS-PRIME/phase-0/test-authority/chrono_migration_prototype.py:38-45`
  - port: Port ONLY the 10 proven columns. Escalate the 5 unproven columns (esp. schema_version, which duplicates PRAGMA user_version) to the writer/owner for a ratified design before adding — porting them from this task would be ungrounded.
