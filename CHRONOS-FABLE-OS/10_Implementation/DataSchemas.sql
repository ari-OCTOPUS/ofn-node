-- CHRONOS-FABLE OS — L0/L4 Data Schemas (SQLite/WAL, single-process, Orange-Pi class)
-- Provenance: VERBATIM from DOC-B primary `01_SourceMap/_primaries/OCTOPUS_CHRONO_ARCHITECTURE.md` §8.
-- Evidence: [SOLID] — this is the design-locked substrate spec, now present in-repo (MER-1 closed 2026-07-08).
-- Rule: chrono/heartbeat tables only. Business logic (Gate/Queue/Channel) is untouched (DOC-B §0).
-- NOTE: the `langar_ledger` columns EXTEND the existing Brushline audit hash-chain — add columns to it,
--       do not create a rival table (DOC-B §8 comment).

-- ── Heartbeat: one row per pacemaker tick. beat_seq = the "pulse number". ──
CREATE TABLE heartbeat (
  beat_seq      INTEGER PRIMARY KEY,          -- strictly monotonic
  wall_ts       INTEGER NOT NULL,             -- ms UTC (human/debug only; never read by legs — TINV-5)
  hlc_phys      INTEGER NOT NULL,             -- "shared now" = max physical HLC across legs
  hlc_logical   INTEGER NOT NULL,
  present_legs  TEXT NOT NULL,                -- JSON: legs that ack'd
  absent_legs   TEXT NOT NULL,                -- JSON: suspected/failed
  workspace_ref TEXT,                         -- ref to the broadcast GWT event
  ts            INTEGER NOT NULL
);
CREATE INDEX idx_heartbeat_ts ON heartbeat(ts);

-- ── Per-leg clock (HLC) + liveness + experience rate. One row per leg, UPDATEd. ──
CREATE TABLE leg_clock (
  leg_id          TEXT PRIMARY KEY,           -- 'A'..'F'
  hlc_phys        INTEGER NOT NULL,
  hlc_logical     INTEGER NOT NULL,
  last_ack_beat   INTEGER NOT NULL,           -- last beat_seq acked
  vitality_phi    REAL NOT NULL DEFAULT 0.0,  -- phi-accrual: higher = more suspect
  experience_rate REAL NOT NULL DEFAULT 0.0,  -- events / pacemaker-second
  state           TEXT NOT NULL DEFAULT 'alive'
                  CHECK (state IN ('alive','suspected','failed')),
  updated_at      INTEGER NOT NULL
);

-- ── Heart: the LANGAR ledger. Single total order (TINV-2). age_tick = mortal arrow (TINV-3). ──
CREATE TABLE langar_ledger (
  entry_seq     INTEGER PRIMARY KEY,          -- single total order (TINV-2)
  prev_hash     TEXT NOT NULL,
  hash          TEXT NOT NULL,                -- sha256(prev_hash || payload || age_tick)
  hlc_phys      INTEGER NOT NULL,             -- event HLC
  hlc_logical   INTEGER NOT NULL,
  age_tick      INTEGER NOT NULL,             -- mortal arrow; +1 ONLY on human-append (TINV-3)
  is_human      INTEGER NOT NULL DEFAULT 0,   -- 1 = human judgment; the ONLY thing that moves age  (OQ-2 = is_human)
  actor_leg     TEXT,                         -- which leg produced the event
  payload_ref   TEXT NOT NULL,
  ts            INTEGER NOT NULL
);
CREATE INDEX idx_langar_hlc ON langar_ledger(hlc_phys, hlc_logical);

-- ── Experience meter (rate ∝ load) — per leg per beat. Feeds metabolic aging (TINV-6). ──
CREATE TABLE experience_meter (
  leg_id        TEXT NOT NULL,
  beat_seq      INTEGER NOT NULL,
  events_count  INTEGER NOT NULL,             -- distinguishable events this beat
  dt_wall_ms    INTEGER NOT NULL,
  rate          REAL NOT NULL,                -- events_count / (dt_wall_ms/1000)
  PRIMARY KEY (leg_id, beat_seq)
);

-- ── Duration sense (feature 1): anchors for "how long since X". ──
CREATE TABLE duration_marker (
  event_id    TEXT PRIMARY KEY,
  hlc_phys    INTEGER NOT NULL,
  hlc_logical INTEGER NOT NULL,
  wall_ts     INTEGER NOT NULL,
  label       TEXT
);

-- ── Anticipation / future (feature 4): scheduled work keyed by BEAT, not wall-clock (TINV-5). ──
CREATE TABLE anticipation_queue (
  id           INTEGER PRIMARY KEY,
  leg_id       TEXT,
  due_beat     INTEGER,                       -- due date in pulses, NOT wall-clock
  kind         TEXT NOT NULL,                 -- 'wait' | 'schedule' | 'followup'
  task_ref     TEXT NOT NULL,
  created_beat INTEGER NOT NULL
);
CREATE INDEX idx_anticipation_due ON anticipation_queue(due_beat);

-- =====================================================================================
-- HYBRID / higher-layer shapes below are [EST] (reconciled from Master Handoff §6 to the
-- DOC-B ledger above). Confirm the L4 vault field set against the Survival-Stack primary
-- (DOC-A, MER-2) before persisting. DDL sketch only.
-- =====================================================================================

-- L4 authoritative Vault (A). Confirmed subset {tag,confidence,falsifier,valid_until} = [SOLID];
-- id/content/source_ref/superseded_by = [EST]; full field set BLOCKED on DOC-A (MER-2).
CREATE TABLE memory_vault_item (
  id            TEXT PRIMARY KEY,
  content       TEXT NOT NULL,
  tag           TEXT NOT NULL,                -- [E/S/P/M/I/R/C/G]
  confidence    INTEGER NOT NULL CHECK (confidence BETWEEN 0 AND 100),
  falsifier     TEXT,                         -- kill-condition for this belief
  valid_until   INTEGER,                      -- stale after this (validity window)
  source_ref    TEXT,                         -- [EST]
  superseded_by TEXT                          -- additive versioning (INV-12); never DELETE
);

-- L4 evictable semantic cache (C). NON-authoritative; reconstructable from ledger (INV-06).
CREATE TABLE semantic_cache_item (
  id                TEXT PRIMARY KEY,
  summary           TEXT NOT NULL,
  derived_from_events TEXT NOT NULL,          -- JSON array of langar entry_seq
  authoritative     INTEGER NOT NULL DEFAULT 0 CHECK (authoritative = 0)
);

-- L13 checkpoint: per-beat snapshot carrying a ledger hash for replay integrity.
CREATE TABLE checkpoint (
  beat_id       INTEGER PRIMARY KEY,
  logical_clock TEXT NOT NULL,                -- HLC snapshot
  ledger_hash   TEXT NOT NULL,                -- hash of langar_ledger head at this beat
  snapshot_ref  TEXT NOT NULL,               -- ref to per-leg state blob (few KB)
  metrics       TEXT                          -- JSON: cost/latency/error
);

-- L9 project registry: money_link gate. No money_link ⇒ status forced 'incubating' (INV-14). [EST]
CREATE TABLE project (
  id             TEXT PRIMARY KEY,
  status         TEXT NOT NULL CHECK (status IN ('incubating','active','parked','killed','done')),
  money_link     TEXT,                        -- NULL ⇒ must stay 'incubating'
  priority_score REAL                         -- (money×prob×speed×leverage)/(risk×energy) — see AtomicObjects AKO-021
);

-- L8 guard decision log (audit of every gate verdict). [EST]
CREATE TABLE guard_decision (
  event_id             TEXT NOT NULL,
  guard_id             TEXT NOT NULL,         -- Truth|Money|State|Autonomy|Evolution|Worker|NonDestruct
  verdict              TEXT NOT NULL CHECK (verdict IN ('allow','deny','cooldown')),
  active_mode          TEXT NOT NULL,         -- Normal|LowEnergy|Offline|HighEnergyGuard|Recovery
  requires_human_append INTEGER NOT NULL DEFAULT 0,
  ts                   INTEGER NOT NULL,
  PRIMARY KEY (event_id, guard_id)
);
