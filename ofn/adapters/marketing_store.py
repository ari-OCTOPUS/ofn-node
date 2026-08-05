"""Persisted marketing state for the studio leg.

This is the adapter half of the marketing scout's memory and the weekly
cycle's record. The kernel's `marketing_scout.Memory` is a pure, in-RAM
ratchet; without persistence a rejected idea is forgotten on the next
restart and the model re-proposes it next week — the exact loop the scout
exists to break. This store loads that memory at the start of a cycle and
writes every disposition back, so the ratchet survives reboots.

It also holds the weekly cycle's own record: which week is open, what was
observed, what was routed, what the partner felt, and what the platforms
reported. Every table is tenant-scoped from the first migration — the
kernel's tenancy rule is that no state crosses a tenant boundary, and
"marketing is new" is not a reason to forget it.

The marketing tables live in their own sqlite file (`marketing.sqlite`),
not inside `studio.sqlite`. The reason is operational, not architectural:
studio.sqlite is backed up and restored as a unit, and mixing a fast-
changing marketing log into it would inflate every nightly snapshot. A
separate file is backed up alongside it and costs nothing extra.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Iterable, Mapping

from ..kernel.marketing_scout import (
    Candidate, Disposition, Memory, Note, TrendObservation,
)
from .sqlite_base import Pool, apply_schema


SCHEMA = (
    """
    CREATE TABLE IF NOT EXISTS marketing_weeks (
        week_id      TEXT    PRIMARY KEY,
        tenant_id    TEXT    NOT NULL,
        starts_at    INTEGER NOT NULL,
        style_id     TEXT    NOT NULL,
        focus_text   TEXT,
        status       TEXT    NOT NULL DEFAULT 'open'
                        CHECK (status IN ('open', 'closed')),
        created_at   INTEGER NOT NULL
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_marketing_weeks_tenant "
    "ON marketing_weeks (tenant_id, starts_at)",
    """
    CREATE TABLE IF NOT EXISTS trend_observations (
        observation_id  TEXT    PRIMARY KEY,
        tenant_id       TEXT    NOT NULL,
        week_id         TEXT,
        source_id       TEXT    NOT NULL,
        term            TEXT    NOT NULL,
        observed_at     INTEGER NOT NULL,
        region          TEXT,
        count_value     REAL,
        rank_value      INTEGER,
        source_url      TEXT,
        raw_ref         TEXT,
        created_at      INTEGER NOT NULL,
        -- An observation without a count or rank is an assertion, not
        -- evidence. Enforced in the kernel too; restated here so a row
        -- written by any path is honest.
        CHECK (count_value IS NOT NULL OR rank_value IS NOT NULL)
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_trend_week "
    "ON trend_observations (tenant_id, week_id, observed_at)",
    """
    CREATE TABLE IF NOT EXISTS rejected_marketing_ideas (
        reject_id    TEXT    PRIMARY KEY,
        tenant_id    TEXT    NOT NULL,
        idea_hash    TEXT    NOT NULL,
        -- The candidate's stable key, stored beside the hash so the
        -- re-proposal check can match on either.
        idea_key     TEXT    NOT NULL,
        title        TEXT    NOT NULL,
        disposition  TEXT    NOT NULL
                        CHECK (disposition IN ('proposed', 'accepted',
                                               'rejected_soft',
                                               'rejected_hard',
                                               'tried_failed')),
        reason       TEXT    NOT NULL,
        rejected_by  TEXT    NOT NULL,
        at_epoch_s   INTEGER NOT NULL,
        created_at   INTEGER NOT NULL,
        UNIQUE (tenant_id, idea_hash)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS routed_variants (
        variant_id          TEXT    PRIMARY KEY,
        tenant_id           TEXT    NOT NULL,
        draft_id            TEXT    NOT NULL,
        platform            TEXT    NOT NULL,
        caption             TEXT    NOT NULL,
        hashtags_json       TEXT    NOT NULL DEFAULT '[]',
        framing             TEXT    NOT NULL,
        adult_label         INTEGER NOT NULL DEFAULT 0,
        screen_ok           INTEGER NOT NULL,
        screen_rule         TEXT    NOT NULL,
        screen_reasons_json TEXT    NOT NULL DEFAULT '[]',
        risk_color          TEXT    NOT NULL,
        idempotency_key     TEXT    NOT NULL,
        created_at          INTEGER NOT NULL,
        UNIQUE (tenant_id, idempotency_key)
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_variants_draft "
    "ON routed_variants (tenant_id, draft_id, platform)",
    """
    CREATE TABLE IF NOT EXISTS felt_right_signals (
        signal_id            TEXT    PRIMARY KEY,
        tenant_id            TEXT    NOT NULL,
        draft_id             TEXT    NOT NULL,
        asked_at             INTEGER NOT NULL,
        value                INTEGER NOT NULL
                        CHECK (value BETWEEN 1 AND 5),
        asked_before_metrics INTEGER NOT NULL
                        CHECK (asked_before_metrics IN (0, 1)),
        created_at           INTEGER NOT NULL
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_felt_draft "
    "ON felt_right_signals (tenant_id, draft_id)",
    """
    CREATE TABLE IF NOT EXISTS platform_metrics (
        metric_id      TEXT    PRIMARY KEY,
        tenant_id      TEXT    NOT NULL,
        variant_id     TEXT,
        platform       TEXT    NOT NULL,
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
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_metrics_variant "
    "ON platform_metrics (tenant_id, variant_id, captured_at)",
    """
    CREATE TABLE IF NOT EXISTS release_switch_events (
        event_id    TEXT    PRIMARY KEY,
        tenant_id   TEXT    NOT NULL,
        event_type  TEXT    NOT NULL
                        CHECK (event_type IN ('armed', 'disarmed',
                                              'kill_switch_on',
                                              'kill_switch_off')),
        owner_id    TEXT    NOT NULL,
        session_id  TEXT    NOT NULL,
        reason      TEXT    NOT NULL,
        expires_at  INTEGER,
        created_at  INTEGER NOT NULL
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_release_tenant "
    "ON release_switch_events (tenant_id, created_at)",
)


# Maps the kernel's Disposition enum *value* to the column's CHECK values.
# Matching on `.value` rather than enum identity is deliberate: in some test
# runs the marketing_scout module can be imported twice, producing two
# Distinct-but-equal Disposition classes whose members are equal by value
# but not by identity. A dict keyed by the enum object would then miss;
# keyed by the string value it cannot.
_DISPOSITION_TO_COL = {
    Disposition.UNSEEN.value: None,             # never written
    Disposition.PROPOSED.value: "proposed",
    Disposition.ACCEPTED.value: "accepted",
    Disposition.REJECTED_SOFT.value: "rejected_soft",
    Disposition.REJECTED_HARD.value: "rejected_hard",
    Disposition.TRIED_FAILED.value: "tried_failed",
}
_COL_TO_DISPOSITION = {col: Disposition(val) for val, col in
                       _DISPOSITION_TO_COL.items() if col}


class MarketingStore:
    """Persisted marketing state, tenant-scoped."""

    def __init__(self, path: str) -> None:
        self._pool = Pool(path)
        apply_schema(self._conn, SCHEMA, ())

    def close(self) -> None:
        self._pool.close()

    @property
    def _conn(self):
        return self._pool.conn

    # ── scout memory: the ratchet, persisted ──────────────────────────

    def load_memory(self, tenant: str) -> Memory:
        """Rebuild the scout's in-RAM memory from the stored dispositions.

        Every note ever recorded for this tenant comes back, in insertion
        order, and is fed to `Memory.record`. The ratchet's rule — a hard
        rejection is never softened — is enforced by `Memory.record`
        itself, so loading is safe even if rows arrive out of order.
        """
        mem = Memory()
        rows = self._conn.execute(
            "SELECT idea_key, idea_hash, disposition, reason, at_epoch_s "
            "FROM rejected_marketing_ideas WHERE tenant_id = ? "
            "ORDER BY created_at, at_epoch_s",
            (tenant,),
        ).fetchall()
        for r in rows:
            disp = _COL_TO_DISPOSITION.get(r["disposition"])
            if disp is None:
                continue
            mem.record(Note(
                key=r["idea_key"], disposition=disp,
                reason=r["reason"], at_epoch_s=r["at_epoch_s"],
            ))
        return mem

    def remember(self, tenant: str, candidate: Candidate, note: Note, *,
                 rejected_by: str, now_epoch_s: int) -> None:
        """Persist one disposition. Idempotent on (tenant, idea_hash).

        A re-record with the same hash is a no-op for the unique row; the
        kernel's ratchet already prevents a hard rejection from softening,
        so a stale write from a retried cycle cannot corrupt the memory.
        """
        col = _DISPOSITION_TO_COL.get(note.disposition.value)
        if col is None:
            return  # UNSEEN is not a thing to persist.
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            self._conn.execute(
                "INSERT OR IGNORE INTO rejected_marketing_ideas "
                "(reject_id, tenant_id, idea_hash, idea_key, title, "
                " disposition, reason, rejected_by, at_epoch_s, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (f"{tenant}:{candidate.idea_hash if hasattr(candidate, 'idea_hash') else candidate.key}",
                 tenant, getattr(candidate, "idea_hash", candidate.key),
                 candidate.key, candidate.title, col, note.reason,
                 rejected_by, note.at_epoch_s, now_epoch_s),
            )
            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK")
            raise

    # ── weekly cycle ──────────────────────────────────────────────────

    def open_week(self, tenant: str, week_id: str, *, starts_at: int,
                  style_id: str, focus_text: str | None,
                  now_epoch_s: int) -> None:
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            self._conn.execute(
                "INSERT OR REPLACE INTO marketing_weeks "
                "(week_id, tenant_id, starts_at, style_id, focus_text, "
                " status, created_at) VALUES (?, ?, ?, ?, ?, 'open', ?)",
                (week_id, tenant, starts_at, style_id, focus_text, now_epoch_s),
            )
            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK")
            raise

    def close_week(self, tenant: str, week_id: str) -> None:
        self._conn.execute(
            "UPDATE marketing_weeks SET status = 'closed' "
            "WHERE tenant_id = ? AND week_id = ?",
            (tenant, week_id),
        )

    def current_week(self, tenant: str) -> Mapping | None:
        row = self._conn.execute(
            "SELECT week_id, starts_at, style_id, focus_text, status "
            "FROM marketing_weeks WHERE tenant_id = ? AND status = 'open' "
            "ORDER BY starts_at DESC LIMIT 1",
            (tenant,),
        ).fetchone()
        return dict(row) if row else None

    def record_observations(self, tenant: str, week_id: str,
                            observations: Iterable[TrendObservation],
                            *, now_epoch_s: int) -> None:
        rows = []
        for i, obs in enumerate(observations):
            rows.append((
                f"{tenant}:{week_id}:{obs.source_id}:{obs.term}:{i}",
                tenant, week_id, obs.source_id, obs.term, obs.observed_at,
                obs.region, obs.count_value, obs.rank_value,
                obs.source_url, None, now_epoch_s,
            ))
        if not rows:
            return
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            self._conn.executemany(
                "INSERT OR REPLACE INTO trend_observations "
                "(observation_id, tenant_id, week_id, source_id, term, "
                " observed_at, region, count_value, rank_value, source_url, "
                " raw_ref, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                rows,
            )
            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK")
            raise

    def observations_for_week(self, tenant: str, week_id: str) -> list[Mapping]:
        rows = self._conn.execute(
            "SELECT source_id, term, observed_at, region, count_value, "
            "rank_value, source_url FROM trend_observations "
            "WHERE tenant_id = ? AND week_id = ? ORDER BY observed_at",
            (tenant, week_id),
        ).fetchall()
        return [dict(r) for r in rows]

    # ── routed variants ───────────────────────────────────────────────

    def record_variant(self, tenant: str, *, draft_id: str, platform: str,
                       caption: str, hashtags: tuple[str, ...], framing: str,
                       adult_label: bool, screen_ok: bool, screen_rule: str,
                       screen_reasons: tuple[str, ...], risk_color: str,
                       idempotency_key: str, variant_id: str,
                       now_epoch_s: int) -> None:
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            self._conn.execute(
                "INSERT OR IGNORE INTO routed_variants "
                "(variant_id, tenant_id, draft_id, platform, caption, "
                " hashtags_json, framing, adult_label, screen_ok, "
                " screen_rule, screen_reasons_json, risk_color, "
                " idempotency_key, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (variant_id, tenant, draft_id, platform, caption,
                 json.dumps(list(hashtags)), framing, 1 if adult_label else 0,
                 1 if screen_ok else 0, screen_rule,
                 json.dumps(list(screen_reasons)), risk_color,
                 idempotency_key, now_epoch_s),
            )
            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK")
            raise

    # ── felt_right ────────────────────────────────────────────────────

    def record_felt_right(self, tenant: str, *, draft_id: str, value: int,
                          asked_at: int, asked_before_metrics: bool,
                          signal_id: str, now_epoch_s: int) -> None:
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            self._conn.execute(
                "INSERT OR REPLACE INTO felt_right_signals "
                "(signal_id, tenant_id, draft_id, asked_at, value, "
                " asked_before_metrics, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (signal_id, tenant, draft_id, asked_at, value,
                 1 if asked_before_metrics else 0, now_epoch_s),
            )
            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK")
            raise

    # ── summary for the dashboard ─────────────────────────────────────

    def summary(self, tenant: str) -> dict:
        """A compact, safe (no secrets) view of this tenant's marketing."""
        week = self.current_week(tenant)
        obs_count = self._conn.execute(
            "SELECT COUNT(*) AS n FROM trend_observations WHERE tenant_id = ?",
            (tenant,)).fetchone()["n"]
        rejected = self._conn.execute(
            "SELECT COUNT(*) AS n FROM rejected_marketing_ideas "
            "WHERE tenant_id = ?", (tenant,)).fetchone()["n"]
        variants = self._conn.execute(
            "SELECT COUNT(*) AS n FROM routed_variants WHERE tenant_id = ?",
            (tenant,)).fetchone()["n"]
        return {
            "current_week": dict(week) if week else None,
            "trend_observations": obs_count,
            "rejected_ideas_in_memory": rejected,
            "routed_variants": variants,
        }
