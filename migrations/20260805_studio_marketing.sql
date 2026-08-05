-- ═══════════════════════════════════════════════════════════════════
-- Marketing tables for the studio leg — v0.3
-- date: 2026-08-05
--
-- IMPORTANT — what this migration is NOT:
--   It does NOT create collections / drafts / draft_media / subjects /
--   releases / draft_subjects / outbox / ledger. Those already exist:
--     - studio core (collections, drafts, draft_media, ...) lives in
--       ofn/adapters/studio_store.py and is already in production with
--       tenant_id columns this migration must not clobber.
--     - the outbox lives in ofn/adapters/outbox.py.
--     - the ledger lives in ofn/adapters/ledger.py.
--   The v0.3 architect pack proposed re-creating them; that would
--   collide with the stronger, tenant-scoped versions already running.
--   This migration adds ONLY the new marketing tables and references
--   the existing drafts table by id (loose reference, no FK, so it works
--   whether drafts live in studio.sqlite or a sibling db).
--
-- All marketing tables are tenant-scoped from day one: tenant_id is on
-- every row, because the kernel's tenancy rule is that no state crosses
-- a tenant boundary, and "marketing is new" is not a reason to forget it.
-- ═══════════════════════════════════════════════════════════════════

PRAGMA journal_mode = WAL;
PRAGMA synchronous = FULL;
PRAGMA foreign_keys = ON;

-- One marketing week. The unit of the weekly cycle: a style is chosen,
-- a focus derived, ideas proposed, some acted on.
CREATE TABLE IF NOT EXISTS marketing_weeks (
  week_id      TEXT PRIMARY KEY,
  tenant_id    TEXT NOT NULL,
  starts_at    INTEGER NOT NULL,
  style_id     TEXT NOT NULL,
  focus_text   TEXT,
  status       TEXT NOT NULL DEFAULT 'open',   -- open | closed
  created_at   INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_marketing_weeks_tenant
  ON marketing_weeks(tenant_id, starts_at);

-- Raw trend evidence. Each row is one observation from one source at one
-- time. The CHECK enforces the scout's hard rule: an observation without
-- a count or rank is an assertion, not evidence.
CREATE TABLE IF NOT EXISTS trend_observations (
  observation_id  TEXT PRIMARY KEY,
  tenant_id       TEXT NOT NULL,
  week_id         TEXT,
  source_id       TEXT NOT NULL,
  term            TEXT NOT NULL,
  observed_at     INTEGER NOT NULL,
  region          TEXT,
  count_value     REAL,
  rank_value      INTEGER,
  source_url      TEXT,
  raw_ref         TEXT,
  created_at      INTEGER NOT NULL,
  CHECK(count_value IS NOT NULL OR rank_value IS NOT NULL)
);
CREATE INDEX IF NOT EXISTS idx_trend_week
  ON trend_observations(tenant_id, week_id, observed_at);

-- The scout's rejection memory, persisted. idea_hash is the same stable
-- slug the kernel's Candidate.key produces, so a re-proposal collides.
CREATE TABLE IF NOT EXISTS rejected_marketing_ideas (
  reject_id    TEXT PRIMARY KEY,
  tenant_id    TEXT NOT NULL,
  idea_hash    TEXT NOT NULL,
  disposition  TEXT NOT NULL,   -- rejected_hard | rejected_soft | tried_failed
  reason       TEXT NOT NULL,
  rejected_by  TEXT NOT NULL,
  rejected_at  INTEGER NOT NULL,
  UNIQUE(tenant_id, idea_hash)
);

-- A draft routed for one platform. Loose ref to drafts (no FK) so this
-- works regardless of where drafts physically live. screen_ok=false rows
-- are kept on purpose: the owner needs to see what was refused and why.
CREATE TABLE IF NOT EXISTS routed_variants (
  variant_id          TEXT PRIMARY KEY,
  tenant_id           TEXT NOT NULL,
  draft_id            TEXT NOT NULL,
  platform            TEXT NOT NULL,
  caption             TEXT NOT NULL,
  hashtags_json       TEXT NOT NULL DEFAULT '[]',
  framing             TEXT NOT NULL,
  adult_label         INTEGER NOT NULL DEFAULT 0,
  screen_ok           INTEGER NOT NULL,
  screen_rule         TEXT NOT NULL,
  screen_reasons_json TEXT NOT NULL DEFAULT '[]',
  risk_color          TEXT NOT NULL,
  idempotency_key     TEXT NOT NULL,
  created_at          INTEGER NOT NULL,
  UNIQUE(tenant_id, idempotency_key)
);
CREATE INDEX IF NOT EXISTS idx_variants_draft
  ON routed_variants(tenant_id, draft_id, platform);

-- felt_right: the partner's gut feeling, captured BEFORE she sees the
-- numbers. asked_before_metrics is a hard column, not a convention: once
-- metrics are visible the answer is a reflection of the number, not a
-- signal independent of it, and that independence is the whole point.
CREATE TABLE IF NOT EXISTS felt_right_signals (
  signal_id            TEXT PRIMARY KEY,
  tenant_id            TEXT NOT NULL,
  draft_id             TEXT NOT NULL,
  asked_at             INTEGER NOT NULL,
  value                INTEGER NOT NULL CHECK(value BETWEEN 1 AND 5),
  asked_before_metrics INTEGER NOT NULL CHECK(asked_before_metrics IN (0,1)),
  created_at           INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_felt_draft
  ON felt_right_signals(tenant_id, draft_id);

-- Platform metrics, captured over time. revenue_cents in integer cents
-- to avoid float money. NULLs allowed: a platform may not expose every
-- metric.
CREATE TABLE IF NOT EXISTS platform_metrics (
  metric_id      TEXT PRIMARY KEY,
  tenant_id      TEXT NOT NULL,
  variant_id     TEXT,
  platform       TEXT NOT NULL,
  captured_at    INTEGER NOT NULL,
  impressions    INTEGER,
  likes          INTEGER,
  comments       INTEGER,
  shares         INTEGER,
  saves          INTEGER,
  clicks         INTEGER,
  revenue_cents  INTEGER,
  raw_ref        TEXT,
  created_at     INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_metrics_variant
  ON platform_metrics(tenant_id, variant_id, captured_at);

-- The owner release switch audit trail. Every arm/disarm is a row; the
-- current state is the latest row for a tenant. expires_at makes a
-- release self-revoking — a switch that stays on because someone forgot
-- to turn it off is exactly the failure mode this is built against.
CREATE TABLE IF NOT EXISTS release_switch_events (
  event_id    TEXT PRIMARY KEY,
  tenant_id   TEXT NOT NULL,
  event_type  TEXT NOT NULL,    -- armed | disarmed | kill_switch_on | kill_switch_off
  owner_id    TEXT NOT NULL,
  session_id  TEXT NOT NULL,
  reason      TEXT NOT NULL,
  expires_at  INTEGER,
  created_at  INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_release_tenant
  ON release_switch_events(tenant_id, created_at);
